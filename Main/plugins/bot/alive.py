# Copyright (C) 2021-present by FridaySoftware@Github, < https://github.com/FridaySoftware >.
#
# This file is part of < https://github.com/FridaySoftware/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/FridaySoftware/Friday/blob/main/LICENSE >
#
# All rights reserved.

import time
import platform
import telethon
from telethon import custom
from platform import python_version

from Main import Friday
from Main.core.decorators import log_errors, iuser_check
from Main.utils.custom_filters import filters
from Main.utils.essentials import Essentials
from Main.utils.inline_helper import is_authorized_cb, is_owner_cb


def _make_alive_content():
    version = Friday.__version__
    telethon_v = telethon.__version__
    py_v = python_version()
    uptime = Essentials.get_readable_time(time.time() - Friday.start_time)
    sessions_count = len(getattr(Friday, "clients", [])) or 1
    plugins_count = len(getattr(Friday, "_command_help_message_data", {}))

    text = (
        "⚡ <b>Friday Userbot is Alive & Operational!</b>\n\n"
        f"• <b>Version:</b> <code>v{version}</code>\n"
        f"• <b>Uptime:</b> <code>{uptime}</code>\n"
        f"• <b>Telethon:</b> <code>v{telethon_v}</code>\n"
        f"• <b>Python:</b> <code>v{py_v}</code>\n"
        f"• <b>Active Sessions:</b> <code>{sessions_count}</code>\n"
        f"• <b>Loaded Plugins:</b> <code>{plugins_count}</code>\n"
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
        [
            custom.Button.inline("✖ Close", b"alive_close"),
        ],
    ]
    return text, buttons


@Friday.bot.on_inline_query(filters.regex(r"^alive$"))
@log_errors
@iuser_check
async def alive_inline_query_handler(c, iq):
    builder = iq.builder
    text, buttons = _make_alive_content()
    res = builder.article(
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
        return await cb.answer("⛔ Access denied: You are not authorized to interact with this control.", alert=True)

    data = cb.data.decode("utf-8") if isinstance(cb.data, bytes) else str(cb.data)

    if data == "alive_ping":
        start = time.perf_counter()
        await c.get_me()
        ms = round((time.perf_counter() - start) * 1000, 2)
        await cb.answer(f"🏓 Pong! Latency: {ms} ms", alert=True)

    elif data == "alive_diag":
        os_info = f"{platform.system()} {platform.release()}"
        active_clients = len(getattr(Friday, "clients", []))
        diag_text = (
            f"🩺 Friday Diagnostics:\n"
            f"• OS: {os_info}\n"
            f"• Engine: Telethon {telethon.__version__}\n"
            f"• Active Clients: {active_clients}\n"
            f"• DB Connection: {'Online' if Friday.db else 'Local Memory'}"
        )
        await cb.answer(diag_text, alert=True)

    elif data == "alive_refresh":
        text, buttons = _make_alive_content()
        await cb.answer("🔄 Status refreshed!")
        try:
            await cb.edit(text, buttons=buttons, parse_mode="html")
        except Exception:
            pass

    elif data == "alive_close":
        if not is_owner_cb(cb):
            return await cb.answer("⛔ Only the bot owner can close this widget.", alert=True)
        try:
            await cb.delete()
        except (TypeError, Exception):
            try:
                await cb.edit("<i>Alive status panel closed.</i>", buttons=None, parse_mode="html")
            except Exception:
                pass
