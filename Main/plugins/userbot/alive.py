# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

import os
import glob
import time
from Main import Friday
from Main.core.types.client import FridayTelegramClient as Client
from Main.core.types.message import Message
from Main.utils.essentials import Essentials


@Friday.register_on_cmd(
    "alive",
    cmd_help={
        "help": "Checks Alive status of UB",
        "example": [
            "alive",
            "alive -basic",
        ],
        "user_args": [
            {
                "arg": "basic",
                "help": "Force text/media output without inline buttons widget.",
                "requires_input": False,
            }
        ],
    },
)
async def alive(c: Client, m: Message):
    is_bot = (getattr(c, "myself", None) and getattr(c.myself, "bot", None) is True) or (
        getattr(Friday, "bot_info", None)
        and getattr(c, "myself", None)
        and getattr(Friday.bot_info, "id", None) is not None
        and getattr(c.myself, "id", None) == Friday.bot_info.id
    )
    if is_bot:
        from Main.plugins.bot.alive import _make_alive_content

        text, buttons = _make_alive_content()
        return await m.reply(text, buttons=buttons, parse_mode="html")

    if "-basic" not in m.user_args and "-text" not in m.user_args:
        try:
            from Main.utils.inline_helper import send_inline_widget

            if await send_inline_widget(c, m, "alive"):
                return
        except Exception:
            pass

    version = Friday.__version__
    uptime = Essentials.get_readable_time(time.time() - Friday.start_time)
    path_ = "./cache/alive.*"
    files = glob.glob(path_)
    file = files[0] if files else ""
    template = (
        Friday.get_string("ALIVE_TEXT")
        or "<b>Friday Userbot (Telethon) is Alive!</b>\nVersion: <code>{0}</code>\nUptime: <code>{1}</code>"
    )
    text = template.format(version, uptime)
    if os.path.exists(file):
        await m.reply_file(file, caption=text)
        return await m.delete_if_self()
    await m.handle_message(text)
