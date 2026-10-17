# Copyright (C) 2021-present by StarkGang@Github, < https://github.com/StarkGang >.
#
# This file is part of < https://github.com/StarkGang/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/StarkGang/Friday/blob/main/LICENSE >
#
# All rights reserved.

import re
from telethon import custom
from Main import Friday
from Main.core.decorators import log_errors
from Main.utils.custom_filters import filters
from Main.utils.inline_helper import is_owner_cb, is_owner


def _make_main_menu():
    text = (
        "📦 <b>Friday Package Manager (FPM v3)</b>\n\n"
        "Modular external plugin management system with zero-latency pre-flight dependency checking and hot isolation.\n\n"
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
        [
            custom.Button.inline("🏠 Main Menu", b"bot_start_menu"),
        ],
    ]
    return text, buttons


@Friday.bot.on_inline_query(filters.regex(r"^fpm$"))
@log_errors
async def fpm_inline_query_handler(c, iq):
    sender_id = getattr(iq, "sender_id", None)
    if not is_owner(sender_id):
        return await iq.answer(
            [],
            switch_pm="⛔ Access denied: Only bot owner can use FPM.",
            switch_pm_param="unauth",
        )

    builder = iq.builder
    text, buttons = _make_main_menu()
    res = builder.article(
        title="📦 FPM Control Center",
        description="Manage, diagnose, and update installed external plugins.",
        text=text,
        buttons=buttons,
        parse_mode="html",
    )
    await iq.answer([res])


@Friday.bot.on_callback_query(filters.regex(r"^fpm_"))
@log_errors
async def fpm_callback_handler(c, cq):
    if not is_owner_cb(cq):
        return await cq.answer("⛔ Access denied: Only the owner can manage plugins.", alert=True)

    data = cq.data.decode("utf-8") if isinstance(cq.data, bytes) else str(cq.data)
    action = data.replace("fpm_", "fpm_")
    pm = Friday.plugin_manager

    if not pm:
        return await cq.answer("❌ Plugin Manager is not initialized.", alert=True)

    # 1. Main Menu
    if action == "fpm_menu":
        text, buttons = _make_main_menu()
        return await cq.edit(text, buttons=buttons, parse_mode="html")

    # 2. List Installed
    if action == "fpm_list":
        installed = await pm.list_installed()
        if not installed:
            text = "📦 <b>Installed Plugins</b>\n\n<i>No external plugins currently installed.</i>"
            buttons = [
                [custom.Button.inline("🔙 Back to Main Menu", b"fpm_menu")],
                [custom.Button.inline("🏠 Main Menu", b"bot_start_menu")],
            ]
            return await cq.edit(text, buttons=buttons, parse_mode="html")

        lines = ["📦 <b>Installed External Plugins:</b>\n"]
        btn_rows = []
        for idx, p in enumerate(installed, 1):
            subs_count = len(p.active_subcategories)
            subs_str = f" ({subs_count} subs)" if subs_count else ""
            lines.append(f"<b>{idx}.</b> <code>{p.name}</code> (v{p.version}) - <i>{p.author}</i>{subs_str}")
            btn_rows.append([
                custom.Button.inline(f"⚙️ {p.name}", f"fpm_p_{p.name}".encode("utf-8"))
            ])

        btn_rows.append([
            custom.Button.inline("🔙 Back to Main Menu", b"fpm_menu"),
            custom.Button.inline("🏠 Main Menu", b"bot_start_menu"),
        ])
        report = "\n".join(lines) + "\n\n<i>Tap a plugin below to inspect or manage:</i>"
        return await cq.edit(report, buttons=btn_rows, parse_mode="html")

    # 3. Inspect Specific Plugin
    if action.startswith("fpm_p_"):
        pname = action.replace("fpm_p_", "")
        manifest = pm._installed.get(pname)
        if not manifest:
            return await cq.answer(f"Plugin {pname} not found.", alert=True)

        subs = manifest.active_subcategories
        subs_text = ", ".join(subs) if subs else "Monolithic (None)"
        deps = manifest.dependencies
        deps_text = ", ".join(deps) if deps else "None"

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
                custom.Button.inline("🔄 Update", f"fpm_up_{pname}".encode("utf-8")),
                custom.Button.inline("🗑 Uninstall", f"fpm_rm_{pname}".encode("utf-8")),
            ],
            [
                custom.Button.inline("🔙 Back to List", b"fpm_list"),
                custom.Button.inline("🏠 Main Menu", b"bot_start_menu"),
            ],
        ]
        return await cq.edit(text, buttons=buttons, parse_mode="html")

    # 4. Doctor Check
    if action == "fpm_doc":
        await cq.answer("🩺 Running health scan...")
        doc = await pm.doctor()
        total = doc["total_plugins"]
        healthy = len(doc["healthy"])
        issues = doc["issues"]
        status_icon = "🟢 Healthy" if not issues else "⚠️ Issues Found"

        issue_lines = [f"• {iss}" for iss in issues] if issues else ["No missing packages detected."]
        report = (
            f"🩺 <b>FPM Diagnostic Health Report</b>\n\n"
            f"• <b>Status:</b> {status_icon}\n"
            f"• <b>Plugins Checked:</b> <code>{total}</code>\n"
            f"• <b>Satisfied:</b> <code>{healthy}/{total}</code>\n\n"
            f"<b>Details:</b>\n" + "\n".join(issue_lines)
        )
        buttons = [
            [custom.Button.inline("🔧 Auto-Repair Missing", b"fpm_rep")],
            [
                custom.Button.inline("🔙 Back", b"fpm_menu"),
                custom.Button.inline("🏠 Main Menu", b"bot_start_menu"),
            ],
        ]
        return await cq.edit(report, buttons=buttons, parse_mode="html")

    # 5. Repair
    if action == "fpm_rep":
        await cq.answer("🔧 Initiating auto-repair...")
        repaired, failed = await pm.repair()
        if repaired == 0 and failed == 0:
            res_msg = "✅ All dependencies are already satisfied."
        else:
            res_msg = f"✅ Repaired {repaired} package(s). ({failed} failed)"
        await cq.answer(res_msg, alert=True)
        text, buttons = _make_main_menu()
        return await cq.edit(f"{res_msg}\n\n{text}", buttons=buttons, parse_mode="html")

    # 6. Update Single Plugin
    if action.startswith("fpm_up_") and action != "fpm_up_all":
        pname = action.replace("fpm_up_", "")
        await cq.answer(f"Updating {pname}...")
        try:
            m = await pm.update(pname)
            msg_str = f"✅ Updated {pname} to v{m.version}" if m else f"❌ Update failed for {pname}"
            await cq.answer(msg_str, alert=True)
        except Exception as e:
            await cq.answer(f"Error: {e}", alert=True)

    # 7. Uninstall Single Plugin
    if action.startswith("fpm_rm_"):
        pname = action.replace("fpm_rm_", "")
        await cq.answer(f"Uninstalling {pname}...")
        try:
            ok = await pm.uninstall(pname)
            if ok:
                await cq.answer(f"🗑 {pname} uninstalled.", alert=True)
                installed = await pm.list_installed()
                text, buttons = _make_main_menu()
                return await cq.edit(text, buttons=buttons, parse_mode="html")
        except Exception as e:
            await cq.answer(f"Error: {e}", alert=True)

    # 8. Update All
    if action == "fpm_up_all":
        await cq.answer("🔄 Checking remote updates...")
        installed = await pm.list_installed()
        updated_count = 0
        for p in installed:
            try:
                up_res = await pm.update(p.name)
                if up_res:
                    updated_count += 1
            except Exception:
                pass
        await cq.answer(f"🔄 Scanned {len(installed)} plugins. Updated {updated_count}.", alert=True)
