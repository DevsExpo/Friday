# Copyright (C) 2021-present by StarkGang@Github, < https://github.com/StarkGang >.
#
# This file is part of < https://github.com/StarkGang/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/StarkGang/Friday/blob/main/LICENSE >
#
# All rights reserved.

import time
from Main import Friday
from style import ping_format as pf
from Main.core.types.client import FridayTelegramClient as Client
from Main.core.types.message import Message
from Main.utils.essentials import Essentials
from Main.core.decorators import inline_check


@Friday.register_on_cmd(
    ["ping", "pong"],
    bot_mode_unsupported=True,
    cmd_help={
        "help": "Ping userbot",
        "example": [
            "ping",
            "ping -c",
        ],
        "user_args": [
            {
                "arg": "c",
                "help": "show the ping output as a regular text edit.",
                "requires_input": False,
            },
        ],
    },
)
async def ping_ub_cmd(c: Client, m: Message):
    user_args = m.user_args
    if "c" not in user_args and "-basic" not in user_args and "-text" not in user_args:
        try:
            from Main.utils.inline_helper import send_inline_widget
            if await send_inline_widget(c, m, "ping"):
                return
        except Exception:
            pass

    start = time.perf_counter()
    await c.get_me()
    uptime = Essentials.get_readable_time(time.time() - Friday.start_time)
    end = time.perf_counter()
    ms = round((end - start) * 1000, 2)
    template = Friday.get_string("PING_TEXT") or "{0} Pong! {1} ms | {2} Uptime: {3}"
    await m.handle_message(
        template.format(pf["ping_emoji1"], ms, pf["ping_emoji2"], uptime)
    )
