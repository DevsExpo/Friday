# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

import time
import asyncio
from Main import Friday
from Main.utils.suppress import suppress_error
from Main.core.types.client import FridayTelegramClient as Client
from Main.core.types.message import Message
from Main.utils.essentials import Essentials
from Main.utils.custom_filters import create, Filter


MENTIONED = []
afk_sanity_check: dict = {}


@Friday.register_on_cmd(
    "afk",
    bot_mode_unsupported=True,
    cmd_help={
        "help": "Set AFK.",
        "example": [
            "afk",
            "afk Busy studying, will reply later",
            "afk -hls Working on project",
            "afk -dlm Traveling today",
        ],
        "user_args": [
            {"arg": "hls", "help": "Hides last seen in afk.", "requires_input": False},
            {
                "arg": "dlm",
                "help": "Doesn't log mentioned messages.",
                "requires_input": False,
            },
        ],
    },
)
async def afk(c: Client, m: Message):
    afk_sanity_check.clear()
    user_args = m.user_args
    afk_time = int(time.time())
    reason = m.user_input
    my_id = getattr(c.myself, "id", 0) if getattr(c, "myself", None) else 0

    await Friday.db.settings_col.update_one(
        {"_id": "AFK", "client_id": my_id},
        {
            "$set": {
                "afk_time": afk_time,
                "reason": reason,
                "dlm": "dlm" in user_args,
                "hls": "hls" in user_args,
            }
        },
        upsert=True,
    )
    await m.handle_message("GOING_AFK", del_in=7)


async def user_afk(c: Client, m: Message) -> bool:
    my_id = getattr(c.myself, "id", 0) if getattr(c, "myself", None) else 0
    afk_record = await Friday.db.settings_col.find_one({"_id": "AFK", "client_id": my_id})
    return bool(afk_record)


def afk_trigger_filter(c: Client, m: Message) -> bool:
    cmd_pfx = getattr(Friday, "user_command_handler", ".") or "."
    txt = (m.text or "").strip()
    if txt.startswith(f"{cmd_pfx}afk") or txt.startswith(f"{cmd_pfx}test"):
        return False
    if getattr(m, "out", False) and not getattr(Friday, "self_test_mode", False):
        return False
    # Trigger on private messages (DM)
    if m.is_private:
        return True
    # Trigger on mention in group
    if getattr(m, "mentioned", False):
        return True
    my_uname = getattr(c.myself, "username", "") if getattr(c, "myself", None) else ""
    if my_uname and txt and f"@{my_uname.lower()}" in txt.lower():
        return True
    # Trigger on reply to user's message in group
    my_id = getattr(c.myself, "id", 0) if getattr(c, "myself", None) else 0
    if m.reply_to_message and getattr(m.reply_to_message, "sender_id", None) == my_id:
        return True
    if getattr(Friday, "self_test_mode", False):
        return True
    return False


@Friday.on_message(
    create(user_afk) & Filter(afk_trigger_filter),
    bot_mode_unsupported=True,
)
async def afk_mentioned(c: Client, m: Message):
    user = m.from_user
    user_id = getattr(user, "id", 0) if user else m.sender_id
    if user_id and not getattr(Friday, "self_test_mode", False):
        afk_sanity_check[user_id] = afk_sanity_check.get(user_id, 0) + 1
        if afk_sanity_check[user_id] > 3:
            return

    my_id = getattr(c.myself, "id", 0) if getattr(c, "myself", None) else 0
    result = await Friday.db.settings_col.find_one({"_id": "AFK", "client_id": my_id})
    if not result:
        return

    afk_time = result.get("afk_time", int(time.time()))
    hls = result.get("hls", False)
    dlm = result.get("dlm", False)

    afk_since = Friday.get_string("AFK_SINCE") if hls else Essentials.get_readable_time(time.time() - afk_time)
    if reason := result.get("reason"):
        await m.reply_msg("USER_AFK", string_args=(afk_since, reason))
    else:
        await m.reply_msg("USER_AFK_NO_REASON", string_args=(afk_since,))

    if not dlm:
        chat = m.chat
        chat_id = str(getattr(chat, "id", ""))
        MENTIONED.append(
            {
                "user": getattr(user, "first_name", "User") if user else "User",
                "chat": getattr(chat, "title", "Chat") if chat else "Chat",
                "chat_id": chat_id,
                "id": m.id,
            }
        )


def outgoing_filter(c: Client, m: Message) -> bool:
    if not getattr(m, "out", False):
        return False
    cmd_pfx = getattr(Friday, "user_command_handler", ".") or "."
    txt = (m.text or "").strip()
    if txt.startswith(f"{cmd_pfx}afk") or txt.startswith(f"{cmd_pfx}test"):
        return False
    return True


@Friday.on_message(
    create(user_afk) & Filter(outgoing_filter),
    bot_mode_unsupported=True,
)
async def set_unafk(c: Client, m: Message):
    global MENTIONED
    my_id = getattr(c.myself, "id", 0) if getattr(c, "myself", None) else 0
    rec = await Friday.db.settings_col.find_one({"_id": "AFK", "client_id": my_id})
    if not rec:
        return

    # Grace period: if set within the last 5 seconds, do not un-afk immediately
    if time.time() - rec.get("afk_time", 0) < 5:
        return

    await Friday.db.settings_col.delete_one({"_id": "AFK", "client_id": my_id})

    msg_template = Friday.get_string("NO_AFK") or "I am no longer AFK!"
    with suppress_error(msg="Sending unafk notification"):
        chat_target = m.chat_id or (getattr(m.chat, "id", None))
        _m_ = await c.send_message(chat_target, msg_template)
        if _m_:
            await asyncio.sleep(4)
            with suppress_error(msg="Deleting unafk notification"):
                await c.delete_messages(chat_target, _m_.id)

    if MENTIONED and Friday.log_chat:
        text = f"<b>Mentions while you were AFK ({len(MENTIONED)}):</b>\n"
        for item in MENTIONED:
            text += f"• {item['user']} in {item['chat']} (Message: {item['id']})\n"
        await c.send_message(Friday.log_chat, text, parse_mode="html")
        MENTIONED = []
    afk_sanity_check.clear()
