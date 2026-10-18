# Copyright (C) 2021-present by StarkGang@Github, < https://github.com/StarkGang >.
#
# This file is part of < https://github.com/StarkGang/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/StarkGang/Friday/blob/main/LICENSE >
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


def _make_alive_content():
    """Build the alive-status message text and inline buttons."""
    uptime = Essentials.get_readable_time(time.time() - Friday.start_time)
    text = (
        "⚡ <b>Friday Userbot is Alive &amp; Operational!</b>\n\n"
        f"• <b>Version:</b> <code>v{Friday.__version__}</code>\n"
        f"• <b>Uptime:</b> <code>{uptime}</code>\n"
        f"• <b>Telethon:</b> <code>v{telethon.__version__}</code>\n"
        f"• <b>Python:</b> <code>v{python_version()}</code>\n"
        f"• <b>Active Sessions:</b> <code>{len(getattr(Friday, 'clients', [])) or 1}</code>\n"
        f"• <b>Loaded Plugins:</b> <code>{len(getattr(Friday, '_command_help_message_data', {}))}</code>\n"
    )
    buttons = [
        [
            custom.Button.inline("🏓 Ping", b"alive_ping"),
            custom.Button.inline("📦 FPM Plugins", b"fpm_list"),
        ],
        [
            custom.Button.inline("🩺 Diagnostics", b"alive_diag"),
            custom.Button.inline("🔄 Refresh", b"alive_refresh"),
        ],
        [custom.Button.inline("✖ Close", b"alive_close")],
    ]
    return text, buttons


@Friday.bot.on_inline_query(filters.regex(r"^alive$"))
@log_errors
@iuser_check
async def alive_inline_query_handler(c, iq):
    text, buttons = _make_alive_content()
    res = iq.builder.article(
        title="⚡ Friday Alive Status",
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
            "⛔ Access denied: You are not authorized to interact with this control.",
            alert=True,
        )

    data = cb.data.decode("utf-8") if isinstance(cb.data, bytes) else str(cb.data)

    if data == "alive_ping":
        start = time.perf_counter()
        await c.get_me()
        ms = round((time.perf_counter() - start) * 1000, 2)
        return await cb.answer(f"🏓 Pong! Latency: {ms} ms", alert=True)

    if data == "alive_diag":
        active_clients = len(getattr(Friday, "clients", []))
        diag_text = (
            f"🩺 Friday Diagnostics:\n"
            f"• OS: {platform.system()} {platform.release()}\n"
            f"• Engine: Telethon {telethon.__version__}\n"
            f"• Active Clients: {active_clients}\n"
            f"• DB Connection: {'Online' if Friday.db else 'Local Memory'}"
        )
        return await cb.answer(diag_text, alert=True)

    if data == "alive_refresh":
        text, buttons = _make_alive_content()
        await cb.answer("🔄 Status refreshed!")
        import contextlib
        with contextlib.suppress(Exception):
            await cb.edit(text, buttons=buttons, parse_mode="html")
        return

    if data == "alive_close":
        if not is_owner_cb(cb):
            return await cb.answer("⛔ Only the bot owner can close this widget.", alert=True)
        import contextlib
        with contextlib.suppress(Exception):
            await cb.delete()
            return
        with contextlib.suppress(Exception):
            await cb.edit("<i>Alive status panel closed.</i>", buttons=None, parse_mode="html")
