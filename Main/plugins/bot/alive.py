# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

import time
import platform
from platform import python_version

import telethon
from telethon import custom

from Main import Friday
from Main.core.decorators import log_errors, iuser_check
from Main.utils.custom_filters import filters
from Main.utils.essentials import Essentials
from Main.utils.inline_helper import is_authorized_cb, is_owner_cb
from Main.utils.ui_tokens import ADMIN, NAV, STATUS


def _make_alive_content():
    """Build the alive-status message text and inline buttons."""
    uptime = Essentials.get_readable_time(time.time() - Friday.start_time)
    text = (
        f"{STATUS.PROCESSING} <b>Friday Userbot is Alive &amp; Operational!</b>\n\n"
        f"• <b>Version:</b> <code>v{Friday.__version__}</code>\n"
        f"• <b>Uptime:</b> <code>{uptime}</code>\n"
        f"• <b>Telethon:</b> <code>v{telethon.__version__}</code>\n"
        f"• <b>Python:</b> <code>v{python_version()}</code>\n"
        f"• <b>Active Sessions:</b> <code>{len(getattr(Friday, 'clients', [])) or 1}</code>\n"
        f"• <b>Loaded Plugins:</b> <code>{len(getattr(Friday, '_command_help_message_data', {}))}</code>\n"
    )
    buttons = [
        [
            custom.Button.inline(f"{STATUS.PING} Ping", b"alive_ping"),
            custom.Button.inline(f"{ADMIN.PACKAGE} FPM Plugins", b"fpm_list"),
        ],
        [
            custom.Button.inline(f"{STATUS.DOCTOR} Diagnostics", b"alive_diag"),
            custom.Button.inline(NAV.REFRESH, b"alive_refresh"),
        ],
        [custom.Button.inline(NAV.CLOSE, b"alive_close")],
    ]
    return text, buttons


@Friday.bot.on_inline_query(filters.regex(r"^alive$"))
@log_errors
@iuser_check
async def alive_inline_query_handler(c, iq):
    text, buttons = _make_alive_content()
    res = iq.builder.article(
        title=f"{STATUS.PROCESSING} Friday Alive Status",
        description="View live system uptime, active sessions, and core stats.",
        text=text,
        buttons=buttons,
        parse_mode="html",
    )
    await iq.answer([res], cache_time=0)


@Friday.bot.on_callback_query(filters.regex(r"^alive_"))
@log_errors
@iuser_check
async def alive_callback_handler(c, cb):
    if not is_authorized_cb(cb):
        return await cb.answer(
            f"{STATUS.DENIED} Access denied: You are not authorized to interact with this control.",
            alert=True,
        )

    data = cb.data.decode("utf-8") if isinstance(cb.data, bytes) else str(cb.data)

    if data == "alive_ping":
        start = time.perf_counter()
        await c.get_me()
        ms = round((time.perf_counter() - start) * 1000, 2)
        return await cb.answer(f"{STATUS.PING} Pong! Latency: {ms} ms", alert=True)

    if data == "alive_diag":
        active_clients = len(getattr(Friday, "clients", []))
        diag_text = (
            f"{STATUS.DOCTOR} Friday Diagnostics:\n"
            f"• OS: {platform.system()} {platform.release()}\n"
            f"• Engine: Telethon {telethon.__version__}\n"
            f"• Active Clients: {active_clients}\n"
            f"• DB Connection: {'Online' if Friday.db else 'Local Memory'}"
        )
        return await cb.answer(diag_text, alert=True)

    if data == "alive_refresh":
        text, buttons = _make_alive_content()
        await cb.answer(f"{ADMIN.RELOAD} Status refreshed!")
        import contextlib

        with contextlib.suppress(Exception):
            await cb.edit(text, buttons=buttons, parse_mode="html")
        return

    if data == "alive_close":
        if not is_owner_cb(cb):
            return await cb.answer(f"{STATUS.DENIED} Only the bot owner can close this widget.", alert=True)
        import contextlib

        with contextlib.suppress(Exception):
            await cb.delete()
            return
        with contextlib.suppress(Exception):
            await cb.edit("<i>Alive status panel closed.</i>", buttons=None, parse_mode="html")
