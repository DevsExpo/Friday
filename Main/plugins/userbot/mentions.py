# Copyright (C) 2021-present by StarkGang@Github, < https://github.com/StarkGang >.
#
# This file is part of < https://github.com/StarkGang/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/StarkGang/Friday/blob/main/LICENSE >
#
# All rights reserved.

from Main import Friday
from Main.core.types.message import Message
from Main.core.types.client import FridayTelegramClient as Client
from Main.utils.custom_filters import filters
from telethon import custom


@Friday.register_on_cmd(
    ["mentions"],
    cmd_help={
        "help": "To toggle notify mentions globally.",
        "example": [
            "mentions on",
            "mentions off",
        ],
    },
    group_only=False,
    requires_input=True,
)
async def mention_settings_handler(c: Client, m: Message):
    msg = await m.handle_message("PROCESSING")
    input_str = m.user_input.lower().strip() if m.user_input else ""
    if input_str in ["on", "yes", "true"]:
        value = True
        await msg.edit_msg("TURNED_ON_MENTIONS_GLOBALLY")
    elif input_str in ["off", "no", "false"]:
        value = False
        await msg.edit_msg("TURNED_OFF_MENTIONS_GLOBALLY")
    else:
        return await msg.edit_msg("INVALID_INPUT")

    if Friday.db is not None:
        await Friday.db.settings_col.update_one(
            {"_id": "MENTION_LOG", "client_id": c.myself.id},
            {"$set": {"value": value}},
            upsert=True,
        )


@Friday.on_message(filters.mentioned & filters.group)
async def send_mention_log_handler(c: Client, m: Message):
    if not Friday.log_chat:
        return
    bot_id = getattr(Friday.bot_info, "id", None)
    if bot_id and m.sender_id == bot_id:
        return

    chat_title = getattr(m.chat, "title", "Group")
    username = getattr(m.chat, "username", None)
    link = f"https://t.me/{username}/{m.id}" if username else ""
    client_name = getattr(c.myself, "first_name", "User")
    msg_text = f"<b>{client_name}</b> was mentioned in <b>{chat_title}</b>"

    buttons = [[custom.Button.url("🔗 Link", link)]] if link else None
    if hasattr(Friday, "bot") and Friday._raw_bot is not None:
        await Friday.bot.send_message(
            Friday.log_chat,
            msg_text,
            buttons=buttons,
            parse_mode="html",
        )
