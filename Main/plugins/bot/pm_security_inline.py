# Copyright (C) 2021-present by StarkGang@Github, < https://github.com/StarkGang >.
#
# This file is part of < https://github.com/StarkGang/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/StarkGang/Friday/blob/main/LICENSE >
#
# All rights reserved.

"""
PM Security inline control panel for the Friday assistant bot.

The `pm_permit_warning_cache` is imported once at module level with a graceful
fallback so all handlers can share it without repeated try/except import blocks.
"""

import re
import html
import contextlib
from typing import Dict, Any

from telethon import custom, functions

from Main import Friday
from Main.core.decorators import log_errors, iuser_check
from Main.utils.custom_filters import filters
from Main.utils.inline_helper import is_owner_cb, is_owner

# ─── Lazy module-level cache reference ────────────────────────────────────────
# Imported once; falls back to an empty local dict if the PM_Security plugin
# hasn't been loaded yet (e.g. when running in bot-only / TWP mode).
try:
    from Main.plugins.userbot.PM_Security import pm_permit_warning_cache  # type: ignore[import]
except Exception:
    pm_permit_warning_cache: Dict[int, Any] = {}  # type: ignore[assignment]


# ─── Panel Renderers ──────────────────────────────────────────────────────────

async def _render_pmpermit_panel():
    is_enabled = await Friday.config.get_pm_sts()
    limit = await Friday.config.get_pm_warn_limit()
    allow_contacts = await Friday.config.get_pm_allow_contacts()
    custom_msg = await Friday.config.get_pm_custom_msg()
    pending_count = len(pm_permit_warning_cache)

    status_badge = "🟢 <b>ACTIVE &amp; SCREENING</b>" if is_enabled else "🔴 <b>DISABLED</b>"
    contacts_badge = "✅ <b>ALLOWED (Bypass)</b>" if allow_contacts else "🛡️ <b>SCREENED</b>"
    msg_badge = "📝 <i>Customized</i>" if custom_msg else "📄 <i>Default Template</i>"

    text = (
        "🛡️ <b>Friday PM Security Control Panel</b>\n\n"
        f"• <b>Status:</b> {status_badge}\n"
        f"• <b>Spam Warning Limit:</b> <code>{limit} Warnings</code> (Blocks on #{limit + 1})\n"
        f"• <b>Allow Contacts:</b> {contacts_badge}\n"
        f"• <b>Warning Message:</b> {msg_badge}\n"
        f"• <b>Pending In Queue:</b> <code>{pending_count} user(s)</code>\n\n"
        "<i>Tap buttons below to change policies, adjust limits (1-20), or mass approve:</i>"
    )
    buttons = [
        [custom.Button.inline(
            "🔴 Turn OFF PM Permit" if is_enabled else "🟢 Turn ON PM Permit",
            b"pmsec_toggle",
        )],
        [
            custom.Button.inline(
                "📇 Contacts: ALLOWED" if allow_contacts else "📇 Contacts: SCREENED",
                b"pmsec_contacts",
            ),
            custom.Button.inline(f"🔢 Set Limit ({limit})", b"pmsec_open_limits"),
        ],
        [
            custom.Button.inline("💬 View Message", b"pmsec_view_msg"),
            custom.Button.inline(f"✅ Mass Approve ({pending_count})", b"pmsec_mass_appr"),
        ],
        [
            custom.Button.inline("🧹 Reset Warnings", b"pmsec_reset"),
            custom.Button.inline("⚙️ Settings Panel", b"panel_refresh"),
        ],
        [
            custom.Button.inline("🏠 Main Menu", b"bot_start_menu"),
            custom.Button.inline("✖ Close", b"pmsec_close"),
        ],
    ]
    return text, buttons


async def _render_limits_panel():
    limit = await Friday.config.get_pm_warn_limit()
    text = (
        "🔢 <b>Select PM Security Warning Limit</b>\n\n"
        "Choose how many warning messages a user receives before being automatically blocked.\n\n"
        f"• Current Active Limit: <b>{limit} Warnings</b>\n\n"
        "<i>Tap any number (1 - 20) below to set the limit:</i>"
    )
    buttons = [
        [
            custom.Button.inline(
                f"✅ {r * 5 + c}" if (r * 5 + c) == limit else str(r * 5 + c),
                f"pmsec_set_limit_{r * 5 + c}".encode(),
            )
            for c in range(1, 6)
        ]
        for r in range(4)
    ]
    buttons.append([
        custom.Button.inline("🔙 Back to PM Security", b"pmsec_main_panel"),
        custom.Button.inline("🏠 Main Menu", b"bot_start_menu"),
    ])
    return text, buttons


async def _render_msg_panel():
    custom_msg = await Friday.config.get_pm_custom_msg()
    status_text = (
        f"<blockquote>{html.escape(custom_msg)}</blockquote>"
        if custom_msg
        else "<i>(Currently using default template)</i>"
    )
    text = (
        "💬 <b>PM Security Warning Message</b>\n\n"
        f"<b>Current Active Message:</b>\n{status_text}\n\n"
        "<i>To change your message, send:</i>\n"
        f"<code>{Friday.user_command_handler}setpmmsg &lt;your custom message&gt;</code>"
    )
    buttons = [
        [custom.Button.inline("🔄 Reset to Default Template", b"pmsec_reset_msg")],
        [
            custom.Button.inline("🔙 Back to PM Security", b"pmsec_main_panel"),
            custom.Button.inline("🏠 Main Menu", b"bot_start_menu"),
        ],
    ]
    return text, buttons


async def _safe_edit(cq, text: str, buttons: list) -> None:
    with contextlib.suppress(Exception):
        await cq.edit(text, buttons=buttons, parse_mode="html")


# ─── Inline Query ─────────────────────────────────────────────────────────────

@Friday.bot.on_inline_query(filters.regex(r"^pmpermit$"))
@log_errors
@iuser_check
async def pmpermit_inline_query_handler(c, iq):
    if not is_owner(iq.sender_id):
        return await iq.answer(
            [], switch_pm="⛔ Access denied: PM Security is owner only.", switch_pm_param="auth"
        )
    text, buttons = await _render_pmpermit_panel()
    res = iq.builder.article(
        title="🛡️ PM Security Panel",
        description="Toggle PM security, set limits (1-20), custom message, and mass approve.",
        text=text,
        buttons=buttons,
        parse_mode="html",
    )
    await iq.answer([res], cache_time=0)


# ─── PM Security Settings Callback ────────────────────────────────────────────

@Friday.bot.on_callback_query(filters.regex(r"^pmsec_"))
@log_errors
async def pmsec_callback_handler(c, cb):
    if not is_owner_cb(cb):
        return await cb.answer(
            "⛔ Access denied: Only the account owner can manage PM Security.", alert=True
        )

    data = cb.data.decode("utf-8") if isinstance(cb.data, bytes) else str(cb.data)

    # Navigation
    if data == "pmsec_main_panel":
        return await _safe_edit(cb, *(await _render_pmpermit_panel()))

    if data == "pmsec_open_limits":
        return await _safe_edit(cb, *(await _render_limits_panel()))

    if data.startswith("pmsec_set_limit_"):
        new_limit = int(data.rsplit("_", 1)[-1])
        await Friday.config.sync_env_to_db("PM_PERMIT_LIMIT", new_limit)
        await cb.answer(f"🔢 PM Warning limit set to {new_limit} warnings!")
        return await _safe_edit(cb, *(await _render_limits_panel()))

    if data == "pmsec_view_msg":
        return await _safe_edit(cb, *(await _render_msg_panel()))

    if data == "pmsec_reset_msg":
        await Friday.config.del_env_from_db("PM_PERMIT_CUSTOM_MSG")
        await cb.answer("🔄 Custom warning message reset to default!", alert=True)
        return await _safe_edit(cb, *(await _render_msg_panel()))

    # Toggle / contacts
    if data == "pmsec_toggle":
        new_val = not await Friday.config.get_pm_sts()
        await Friday.config.sync_env_to_db("PM_PERMIT", new_val)
        await cb.answer(f"🛡️ PM Security {'Enabled' if new_val else 'Disabled'}!")

    elif data == "pmsec_contacts":
        new_val = not await Friday.config.get_pm_allow_contacts()
        await Friday.config.sync_env_to_db("PM_PERMIT_ALLOW_CONTACTS", new_val)
        await cb.answer(f"📇 Saved Contacts: {'Allowed (Bypass)' if new_val else 'Screened'}!")

    elif data == "pmsec_mass_appr":
        pending_ids = list(pm_permit_warning_cache.keys())
        if not pending_ids:
            return await cb.answer("ℹ️ No pending users waiting in warning queue.", alert=True)
        if Friday.db is not None:
            col = Friday.db.make_collection("pm_permit")
            for uid in pending_ids:
                await col.update_one({"user_id": uid}, {"$set": {"approved": True}}, upsert=True)
        pm_permit_warning_cache.clear()
        await cb.answer(f"✅ Successfully approved {len(pending_ids)} pending user(s)!", alert=True)

    elif data == "pmsec_reset":
        count = len(pm_permit_warning_cache)
        pm_permit_warning_cache.clear()
        await cb.answer(f"🧹 Cleared warning count cache ({count} users reset)!", alert=True)

    elif data == "pmsec_close":
        with contextlib.suppress(Exception):
            await cb.delete()
            return
        with contextlib.suppress(Exception):
            await cb.edit("<i>PM Security panel closed.</i>", buttons=None, parse_mode="html")
        return

    # Refresh panel after any state change
    await _safe_edit(cb, *(await _render_pmpermit_panel()))


# ─── PM Warning Inline Query ───────────────────────────────────────────────────

@Friday.bot.on_inline_query(filters.regex(r"^pm_warn:(\d+)(?::(\d+):(\d+))?"))
@log_errors
async def pm_warn_inline_query_handler(c, iq):
    m = re.match(r"^pm_warn:(\d+)(?::(\d+):(\d+))?", iq.text)
    if not m:
        return

    target_id = int(m.group(1))
    warn_num = int(m.group(2)) if m.group(2) else 1
    limit = int(m.group(3)) if m.group(3) else await Friday.config.get_pm_warn_limit()
    custom_msg = await Friday.config.get_pm_custom_msg()

    body = html.escape(custom_msg) if custom_msg else (
        "<i>Hello there! I am currently away or busy.</i>\n"
        "Please state your reason for contacting in <b>one message</b> and wait for approval."
    )
    warn_str = f"⚠️ <b>Warning: {warn_num} of {limit}</b>"
    if warn_num >= limit:
        warn_str += " <i>(FINAL WARNING before automatic block)</i>"

    text = (
        "🤖 <b>Friday PM Security Protection</b>\n\n"
        f"{body}\n\n{warn_str}\n"
        "<i>Repeated messages will result in an automatic block.</i>"
    )
    buttons = [[
        custom.Button.inline("🛡️ Owner: Approve", f"pm_appr:{target_id}".encode()),
        custom.Button.inline("🚫 Owner: Block", f"pm_block:{target_id}".encode()),
    ]]
    res = iq.builder.article(
        title=f"⚠️ PM Warning ({warn_num}/{limit})",
        description=f"Warning {warn_num} of {limit} before auto-block.",
        text=text,
        buttons=buttons,
        parse_mode="html",
    )
    await iq.answer([res], cache_time=0)


# ─── PM Approve / Block Callback ──────────────────────────────────────────────

@Friday.bot.on_callback_query(filters.regex(r"^pm_(appr|block):(\d+)"))
@log_errors
async def pm_action_callback_handler(c, cb):
    if not is_owner(cb.sender_id):
        return await cb.answer(
            "⛔ Nice try! Only the account owner can approve or block contacts.", alert=True
        )

    data = cb.data.decode("utf-8") if isinstance(cb.data, bytes) else str(cb.data)
    m = re.match(r"^pm_(appr|block):(\d+)", data)
    if not m:
        return

    action = m.group(1)
    target_id = int(m.group(2))

    # Update DB record
    if Friday.db is not None:
        col = Friday.db.make_collection("pm_permit")
        await col.update_one(
            {"user_id": target_id},
            {"$set": {"approved": action == "appr"}},
            upsert=True,
        )

    # Remove from in-memory warning cache
    pm_permit_warning_cache.pop(target_id, None)

    if action == "appr":
        await cb.answer("✅ User has been approved!", alert=True)
        await cb.edit(
            f"✅ <b>Contact Approved</b>\n\nUser <code>{target_id}</code> is now permitted to send direct messages.",
            parse_mode="html",
        )
    else:
        # Block the user via Telethon
        with contextlib.suppress(Exception):
            for client in getattr(Friday, "clients", []):
                peer = await client.get_input_entity(target_id)
                await client(functions.contacts.BlockRequest(id=peer))
                break
        await cb.answer("🚫 Contact blocked.", alert=True)
        await cb.edit(
            f"🚫 <b>Contact Blocked</b>\n\nUser <code>{target_id}</code> has been blocked.",
            parse_mode="html",
        )
