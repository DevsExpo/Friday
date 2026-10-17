# Copyright (C) 2021-present by FridaySoftware@Github, < https://github.com/FridaySoftware >.
#
# This file is part of < https://github.com/FridaySoftware/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/FridaySoftware/Friday/blob/main/LICENSE >
#
# All rights reserved.

from Main import Friday
from Main.utils.custom_filters import filters
from Main.core.decorators import log_errors
from telethon import custom


@Friday.bot.on_message(filters.command("add", "/"))
@log_errors
async def add_session_command_handler(_, m):
    sender_id = getattr(m, "sender_id", None)
    if sender_id not in Friday.auth_users:
        return await m.reply("Hey, I'm just a bot. Powered by @FridayUB.")

    buttons = [
        [
            custom.Button.inline("Yes", b"session_yes"),
            custom.Button.inline("No", b"session_no"),
        ]
    ]
    await m.reply(
        "Do you have the Telethon string session already generated?",
        buttons=buttons,
    )
