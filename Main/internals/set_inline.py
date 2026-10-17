# Copyright (C) 2021-present by FridaySoftware@Github, < https://github.com/FridaySoftware >.
#
# This file is part of < https://github.com/FridaySoftware/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/FridaySoftware/Friday/blob/main/LICENSE >
#
# All rights reserved.


# ====================================
# **REQUIRES MULTICLIENT FORMATTING **
# ====================================

import asyncio
from Main import Friday
from Main.core.types import FridayTelegramClient


async def set_inline_in_botfather(Client: FridayTelegramClient):
    await Client.send_message("botfather", "/cancel")
    await asyncio.sleep(1)
    message = await Client.send_message("botfather", "/setinline")
    await asyncio.sleep(1)
    await message.reply(f"@{Friday.bot_info.username}")
    await asyncio.sleep(1)
    await message.reply("Powered by Friday")
    await asyncio.sleep(1)
