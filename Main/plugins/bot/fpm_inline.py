# Copyright (C) 2021-present by StarkGang@Github, < https://github.com/StarkGang >.
#
# This file is part of < https://github.com/StarkGang/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/StarkGang/Friday/blob/main/LICENSE >
#
# All rights reserved.

import contextlib
from telethon import custom

from Main import Friday
from Main.core.decorators import log_errors
from Main.utils.custom_filters import filters
from Main.utils.inline_helper import is_owner_cb, is_owner


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_main_menu():
    text = (
        "📦 <b>Friday Package Manager (FPM v3)</b>\n\n"
        "Modular external plugin management with zero-latency dependency "
        "checking and hot plugin isolation.\n\n"
        "<i>Select an action below to manage plugins:</i>"
    )
    buttons = [
        [
            custom.Button.inline("📦 Installed Plugins", b"fpm_list"),
            custom.Button.inline("🩺 Doctor & Health", b"fpm_doc"),
        ],
        [
            custom.Button.inline("🔄 Update All", b"fpm_up_all"),
            custom.Button.inline("🔧 Batch Repair", b"fpm_rep"),
        ],
        [custom.Button.inline("🏠 Main Menu", b"bot_start_menu")],
    ]
    return text, buttons


_BACK_ROW = [
    custom.Button.inline("🔙 Back", b"fpm_menu"),
    custom.Button.inline("🏠 Main Menu", b"bot_start_menu"),
]


async def _safe_edit(cq, text: str, buttons: list) -> None:
    """Edit a callback query message, suppressing MessageNotModifiedError."""
    with contextlib.suppress(Exception):
        await cq.edit(text, buttons=buttons, parse_mode="html")


# ─── Inline Query ─────────────────────────────────────────────────────────────

@Friday.bot.on_inline_query(filters.regex(r"^fpm$"))
@log_errors
async def fpm_inline_query_handler(c, iq):
    if not is_owner(getattr(iq, "sender_id", None)):
        return await iq.answer(
            [],
            switch_pm="⛔ Access denied: Only bot owner can use FPM.",
            switch_pm_param="unauth",
        )
    text, buttons = _make_main_menu()
    res = iq.builder.article(
        title="📦 FPM Control Center",
        description="Manage, diagnose, and update installed external plugins.",
        text=text,
        buttons=buttons,
        parse_mode="html",
    )
    await iq.answer([res])


# ─── Callback Handler ─────────────────────────────────────────────────────────

@Friday.bot.on_callback_query(filters.regex(r"^fpm_"))
@log_errors
async def fpm_callback_handler(c, cq):
    if not is_owner_cb(cq):
        return await cq.answer("⛔ Access denied: Only the owner can manage plugins.", alert=True)

    data = cq.data.decode("utf-8") if isinstance(cq.data, bytes) else str(cq.data)
    pm = Friday.plugin_manager

    if not pm:
        return await cq.answer("❌ Plugin Manager is not initialized.", alert=True)

    # ── Main Menu ──────────────────────────────────────────────────────────────
    if data == "fpm_menu":
        text, buttons = _make_main_menu()
        return await _safe_edit(cq, text, buttons)

    # ── List Installed ─────────────────────────────────────────────────────────
    if data == "fpm_list":
        installed = await pm.list_installed()
        if not installed:
            return await _safe_edit(
                cq,
                "📦 <b>Installed Plugins</b>\n\n<i>No external plugins currently installed.</i>",
                [[custom.Button.inline("🔙 Back", b"fpm_menu")]],
            )
        lines = ["📦 <b>Installed External Plugins:</b>\n"]
        btn_rows = []
        for idx, p in enumerate(installed, 1):
            subs = f" ({len(p.active_subcategories)} subs)" if p.active_subcategories else ""
            lines.append(f"<b>{idx}.</b> <code>{p.name}</code> (v{p.version}) — <i>{p.author}</i>{subs}")
            btn_rows.append([custom.Button.inline(f"⚙️ {p.name}", f"fpm_p_{p.name}".encode())])
        btn_rows.append(_BACK_ROW)
        report = "\n".join(lines) + "\n\n<i>Tap a plugin to inspect or manage:</i>"
        return await _safe_edit(cq, report, btn_rows)

    # ── Inspect Plugin ─────────────────────────────────────────────────────────
    if data.startswith("fpm_p_"):
        pname = data[len("fpm_p_"):]
        manifest = pm._installed.get(pname)
        if not manifest:
            return await cq.answer(f"Plugin '{pname}' not found.", alert=True)
        subs_text = ", ".join(manifest.active_subcategories) if manifest.active_subcategories else "None"
        deps_text = ", ".join(manifest.dependencies) if manifest.dependencies else "None"
        text = (
            f"🧩 <b>Plugin:</b> <code>{manifest.name}</code>\n"
            f"• <b>Version:</b> <code>{manifest.version}</code>\n"
            f"• <b>Author:</b> <i>{manifest.author}</i>\n"
            f"• <b>Provider:</b> <code>{manifest.provider}</code>\n"
            f"• <b>Source:</b> <code>{manifest.source}</code>\n"
            f"• <b>Active Subcategories:</b> <code>{subs_text}</code>\n"
            f"• <b>Dependencies:</b> <code>{deps_text}</code>\n"
        )
        buttons = [
            [
                custom.Button.inline("🔄 Update", f"fpm_up_{pname}".encode()),
                custom.Button.inline("🗑 Uninstall", f"fpm_rm_{pname}".encode()),
            ],
            [
                custom.Button.inline("🔙 Back to List", b"fpm_list"),
                custom.Button.inline("🏠 Main Menu", b"bot_start_menu"),
            ],
        ]
        return await _safe_edit(cq, text, buttons)

    # ── Doctor ─────────────────────────────────────────────────────────────────
    if data == "fpm_doc":
        await cq.answer("🩺 Running health scan...")
        doc = await pm.doctor()
        total = doc["total_plugins"]
        healthy = len(doc["healthy"])
        issues = doc["issues"]
        status_icon = "🟢 Healthy" if not issues else "⚠️ Issues Found"
        issue_lines = [f"• {iss}" for iss in issues] or ["No missing packages detected."]
        report = (
            f"🩺 <b>FPM Diagnostic Health Report</b>\n\n"
            f"• <b>Status:</b> {status_icon}\n"
            f"• <b>Plugins Checked:</b> <code>{total}</code>\n"
            f"• <b>Satisfied:</b> <code>{healthy}/{total}</code>\n\n"
            "<b>Details:</b>\n" + "\n".join(issue_lines)
        )
        return await _safe_edit(
            cq,
            report,
            [
                [custom.Button.inline("🔧 Auto-Repair Missing", b"fpm_rep")],
                _BACK_ROW,
            ],
        )

    # ── Repair ─────────────────────────────────────────────────────────────────
    if data == "fpm_rep":
        await cq.answer("🔧 Initiating auto-repair...")
        repaired, failed = await pm.repair()
        res_msg = (
            "✅ All dependencies are already satisfied."
            if repaired == 0 and failed == 0
            else f"✅ Repaired {repaired} package(s). ({failed} failed)"
        )
        await cq.answer(res_msg, alert=True)
        text, buttons = _make_main_menu()
        return await _safe_edit(cq, f"{res_msg}\n\n{text}", buttons)

    # ── Update Single ──────────────────────────────────────────────────────────
    if data.startswith("fpm_up_") and data != "fpm_up_all":
        pname = data[len("fpm_up_"):]
        await cq.answer(f"Updating {pname}...")
        with contextlib.suppress(Exception):
            manifest = await pm.update(pname)
            msg_str = (
                f"✅ Updated {pname} to v{manifest.version}"
                if manifest
                else f"❌ Update failed for {pname}"
            )
            await cq.answer(msg_str, alert=True)
        return

    # ── Uninstall ──────────────────────────────────────────────────────────────
    if data.startswith("fpm_rm_"):
        pname = data[len("fpm_rm_"):]
        await cq.answer(f"Uninstalling {pname}...")
        with contextlib.suppress(Exception):
            ok = await pm.uninstall(pname)
            if ok:
                await cq.answer(f"🗑 {pname} uninstalled.", alert=True)
                text, buttons = _make_main_menu()
                return await _safe_edit(cq, text, buttons)
        return

    # ── Update All ─────────────────────────────────────────────────────────────
    if data == "fpm_up_all":
        await cq.answer("🔄 Checking remote updates...")
        installed = await pm.list_installed()
        updated_count = sum(
            1
            for p in installed
            if not contextlib.suppress(Exception)
            and await pm.update(p.name) is not None
        )
        # Use a simple sequential count (suppress errors per-plugin)
        updated_count = 0
        for p in installed:
            with contextlib.suppress(Exception):
                if await pm.update(p.name):
                    updated_count += 1
        await cq.answer(f"🔄 Scanned {len(installed)} plugins. Updated {updated_count}.", alert=True)
