# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

import time
import contextlib
from telethon import custom

from Main import Friday
from style import ping_format as pf
from Main.utils.custom_filters import filters
from Main.utils.essentials import Essentials
from Main.core.decorators import log_errors, iuser_check


def _build_ping_text(ms: float) -> str:
    """Render a ping response string with uptime from the shared template."""
    uptime = Essentials.get_readable_time(time.time() - Friday.start_time)
    template = Friday.get_string("PING_TEXT") or "{0} Pong! {1} ms | {2} Uptime: {3}"
    return template.format(pf["ping_emoji1"], ms, pf["ping_emoji2"], uptime)


def _ping_buttons() -> list:
    return [[custom.Button.inline(f"{pf['ping_emoji1']} Ping", b"ping")]]


async def _measure_latency(c) -> float:
    """Return round-trip latency in milliseconds for a get_me() call."""
    start = time.perf_counter()
    await c.get_me()
    return round((time.perf_counter() - start) * 1000, 2)


@Friday.bot.on_message(filters.command("ping", "/"))
@log_errors
async def ping_command_handler(c, m):
    if m.sender_id != Friday.config.OWNER_ID:
        return
    ms = await _measure_latency(c)
    text = _build_ping_text(ms)
    await m.reply(text, buttons=_ping_buttons(), parse_mode="html")


@Friday.bot.on_callback_query(filters.regex(r"^ping"))
@log_errors
@iuser_check
async def ping_cb_handler(c, cb):
    ms = await _measure_latency(c)
    text = _build_ping_text(ms)
    await cb.answer(Essentials.clean_html(text), alert=True)
    with contextlib.suppress(Exception):
        await cb.edit(text, buttons=_ping_buttons(), parse_mode="html")


@Friday.bot.on_inline_query(filters.regex(r"^ping"))
@log_errors
@iuser_check
async def ping_inline_handler(c, iq):
    ms = await _measure_latency(c)
    uptime = Essentials.get_readable_time(time.time() - Friday.start_time)
    result = iq.builder.article(
        title=f"{pf['ping_emoji1']} Pong!",
        description=f"{ms} ms\n{uptime}",
        text=(
            f"<b>{pf['ping_emoji1']} Pong!</b>\n"
            f"<code>{ms} ms</code>\n"
            f"<b>{pf['ping_emoji2']} Uptime:</b> <code>{uptime}</code>"
        ),
        parse_mode="html",
        buttons=_ping_buttons(),
    )
    await iq.answer([result])
