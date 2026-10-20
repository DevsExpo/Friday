# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
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

from telethon import custom, functions

from Main import Friday
from Main.core.decorators import log_errors, iuser_check
from Main.utils.custom_filters import filters
from Main.utils.inline_helper import is_owner_cb, is_owner
from Main.utils.ui_tokens import ADMIN, STATUS
from Main.utils.pm_panel import (
    pm_permit_warning_cache,
    render_limits_panel,
    render_msg_panel,
    render_pmpermit_panel,
)


async def _safe_edit(cq, text: str, buttons: list) -> None:
    with contextlib.suppress(Exception):
        await cq.edit(text, buttons=buttons, parse_mode="html")


@Friday.bot.on_inline_query(filters.regex(r"^pmpermit$"))
@log_errors
@iuser_check
async def pmpermit_inline_query_handler(c, iq):
    if not is_owner(iq.sender_id):
        return await iq.answer(
            [], switch_pm=f"{STATUS.DENIED} Access denied: PM Security is owner only.", switch_pm_param="auth"
        )
    text, buttons = await render_pmpermit_panel()
    res = iq.builder.article(
        title=f"{STATUS.SHIELD} PM Security Panel",
        description="Toggle PM security, set limits (1-20), custom message, and mass approve.",
        text=text,
        buttons=buttons,
        parse_mode="html",
    )
    await iq.answer([res], cache_time=0)


@Friday.bot.on_callback_query(filters.regex(r"^pmsec_"))
@log_errors
async def pmsec_callback_handler(c, cb):
    if not is_owner_cb(cb):
        return await cb.answer(
            f"{STATUS.DENIED} Access denied: Only the account owner can manage PM Security.", alert=True
        )

    data = cb.data.decode("utf-8") if isinstance(cb.data, bytes) else str(cb.data)

    # Navigation
    if data == "pmsec_main_panel":
        return await _safe_edit(cb, *(await render_pmpermit_panel()))

    if data == "pmsec_open_limits":
        return await _safe_edit(cb, *(await render_limits_panel()))

    if data.startswith("pmsec_set_limit_"):
        new_limit = int(data.rsplit("_", 1)[-1])
        await Friday.config.sync_env_to_db("PM_PERMIT_LIMIT", new_limit)
        await cb.answer(f"{ADMIN.NUMBER} PM Warning limit set to {new_limit} warnings!")
        return await _safe_edit(cb, *(await render_limits_panel()))

    if data == "pmsec_view_msg":
        return await _safe_edit(cb, *(await render_msg_panel()))

    if data == "pmsec_reset_msg":
        await Friday.config.del_env_from_db("PM_PERMIT_CUSTOM_MSG")
        await cb.answer(f"{ADMIN.RELOAD} Custom warning message reset to default!", alert=True)
        return await _safe_edit(cb, *(await render_msg_panel()))

    # Toggle / contacts
    if data == "pmsec_toggle":
        new_val = not await Friday.config.get_pm_sts()
        await Friday.config.sync_env_to_db("PM_PERMIT", new_val)
        await cb.answer(f"{STATUS.SHIELD} PM Security {'Enabled' if new_val else 'Disabled'}!")

    elif data == "pmsec_contacts":
        new_val = not await Friday.config.get_pm_allow_contacts()
        await Friday.config.sync_env_to_db("PM_PERMIT_ALLOW_CONTACTS", new_val)
        await cb.answer(f"{ADMIN.CONTACT} Saved Contacts: {'Allowed (Bypass)' if new_val else 'Screened'}!")

    elif data == "pmsec_mass_appr":
        pending_ids = list(pm_permit_warning_cache.keys())
        if not pending_ids:
            return await cb.answer(f"{STATUS.INFO} No pending users waiting in warning queue.", alert=True)
        if Friday.db is not None:
            col = Friday.db.make_collection("pm_permit")
            for uid in pending_ids:
                await col.update_one({"user_id": uid}, {"$set": {"approved": True}}, upsert=True)
        pm_permit_warning_cache.clear()
        await cb.answer(f"{STATUS.SUCCESS} Successfully approved {len(pending_ids)} pending user(s)!", alert=True)

    elif data == "pmsec_reset":
        count = len(pm_permit_warning_cache)
        pm_permit_warning_cache.clear()
        await cb.answer(f"{STATUS.CLEAN} Cleared warning count cache ({count} users reset)!", alert=True)

    elif data == "pmsec_close":
        with contextlib.suppress(Exception):
            await cb.delete()
            return
        with contextlib.suppress(Exception):
            await cb.edit("<i>PM Security panel closed.</i>", buttons=None, parse_mode="html")
        return

    # Refresh panel after any state change
    await _safe_edit(cb, *(await render_pmpermit_panel()))


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

    body = (
        html.escape(custom_msg)
        if custom_msg
        else (
            "<i>Hello there! I am currently away or busy.</i>\n"
            "Please state your reason for contacting in <b>one message</b> and wait for approval."
        )
    )
    warn_str = f"{STATUS.WARNING} <b>Warning: {warn_num} of {limit}</b>"
    if warn_num >= limit:
        warn_str += " <i>(FINAL WARNING before automatic block)</i>"

    text = (
        f"{ADMIN.BOT} <b>Friday PM Security Protection</b>\n\n"
        f"{body}\n\n{warn_str}\n"
        "<i>Repeated messages will result in an automatic block.</i>"
    )
    buttons = [
        [
            custom.Button.inline(f"{STATUS.SHIELD} Owner: Approve", f"pm_appr:{target_id}".encode()),
            custom.Button.inline(f"{STATUS.FORBIDDEN} Owner: Block", f"pm_block:{target_id}".encode()),
        ]
    ]
    res = iq.builder.article(
        title=f"{STATUS.WARNING} PM Warning ({warn_num}/{limit})",
        description=f"Warning {warn_num} of {limit} before auto-block.",
        text=text,
        buttons=buttons,
        parse_mode="html",
    )
    await iq.answer([res], cache_time=0)


@Friday.bot.on_callback_query(filters.regex(r"^pm_(appr|block):(\d+)"))
@log_errors
async def pm_action_callback_handler(c, cb):
    if not is_owner(cb.sender_id):
        return await cb.answer(
            f"{STATUS.DENIED} Nice try! Only the account owner can approve or block contacts.", alert=True
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
        await cb.answer(f"{STATUS.SUCCESS} User has been approved!", alert=True)
        await cb.edit(
            f"{STATUS.SUCCESS} <b>Contact Approved</b>\n\nUser <code>{target_id}</code> is now permitted to send direct messages.",
            parse_mode="html",
        )
    else:
        # Block the user via Telethon
        with contextlib.suppress(Exception):
            for client in getattr(Friday, "clients", []):
                peer = await client.get_input_entity(target_id)
                await client(functions.contacts.BlockRequest(id=peer))
                break
        await cb.answer(f"{STATUS.FORBIDDEN} Contact blocked.", alert=True)
        await cb.edit(
            f"{STATUS.FORBIDDEN} <b>Contact Blocked</b>\n\nUser <code>{target_id}</code> has been blocked.",
            parse_mode="html",
        )
