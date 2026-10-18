# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

import contextlib
from telethon import custom

from Main import Friday
from Main.core.decorators import log_errors
from Main.utils.custom_filters import filters
from Main.utils.inline_helper import is_owner_cb, is_owner
from Main.utils.ui_tokens import ADMIN, INDICATOR, NAV, STATUS


def _make_main_menu():
    text = (
        f"{ADMIN.PACKAGE} <b>Friday Package Manager (FPM v3)</b>\n\n"
        "Modular external plugin management with zero-latency dependency "
        "checking and hot plugin isolation.\n\n"
        "<i>Select an action below to manage plugins:</i>"
    )
    buttons = [
        [
            custom.Button.inline(f"{ADMIN.PACKAGE} Installed Plugins", b"fpm_list"),
            custom.Button.inline(f"{STATUS.DOCTOR} Doctor & Health", b"fpm_doc"),
        ],
        [
            custom.Button.inline(f"{ADMIN.RELOAD} Update All", b"fpm_up_all"),
            custom.Button.inline(f"{ADMIN.WRENCH} Batch Repair", b"fpm_rep"),
        ],
        [custom.Button.inline(f"{NAV.HOME_ICON} Main Menu", b"bot_start_menu")],
    ]
    return text, buttons


_BACK_ROW = [
    custom.Button.inline(NAV.BACK, b"fpm_menu"),
    custom.Button.inline(f"{NAV.HOME_ICON} Main Menu", b"bot_start_menu"),
]


async def _safe_edit(cq, text: str, buttons: list) -> None:
    """Edit a callback query message, suppressing MessageNotModifiedError."""
    with contextlib.suppress(Exception):
        await cq.edit(text, buttons=buttons, parse_mode="html")


@Friday.bot.on_inline_query(filters.regex(r"^fpm$"))
@log_errors
async def fpm_inline_query_handler(c, iq):
    if not is_owner(getattr(iq, "sender_id", None)):
        return await iq.answer(
            [],
            switch_pm=f"{STATUS.DENIED} Access denied: Only bot owner can use FPM.",
            switch_pm_param="unauth",
        )
    text, buttons = _make_main_menu()
    res = iq.builder.article(
        title=f"{ADMIN.PACKAGE} FPM Control Center",
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
        return await cq.answer(f"{STATUS.DENIED} Access denied: Only the owner can manage plugins.", alert=True)

    data = cq.data.decode("utf-8") if isinstance(cq.data, bytes) else str(cq.data)
    pm = Friday.plugin_manager

    if not pm:
        return await cq.answer(f"{STATUS.ERROR} Plugin Manager is not initialized.", alert=True)

    if data == "fpm_menu":
        text, buttons = _make_main_menu()
        return await _safe_edit(cq, text, buttons)

    if data == "fpm_list":
        installed = await pm.list_installed()
        if not installed:
            return await _safe_edit(
                cq,
                f"{ADMIN.PACKAGE} <b>Installed Plugins</b>\n\n<i>No external plugins currently installed.</i>",
                [[custom.Button.inline(NAV.BACK, b"fpm_menu")]],
            )
        lines = [f"{ADMIN.PACKAGE} <b>Installed External Plugins:</b>\n"]
        btn_rows = []
        for idx, p in enumerate(installed, 1):
            subs = f" ({len(p.active_subcategories)} subs)" if p.active_subcategories else ""
            lines.append(f"<b>{idx}.</b> <code>{p.name}</code> (v{p.version}) — <i>{p.author}</i>{subs}")
            btn_rows.append([custom.Button.inline(f"{STATUS.GEAR} {p.name}", f"fpm_p_{p.name}".encode())])
        btn_rows.append(_BACK_ROW)
        report = "\n".join(lines) + "\n\n<i>Tap a plugin to inspect or manage:</i>"
        return await _safe_edit(cq, report, btn_rows)

    if data.startswith("fpm_p_"):
        pname = data[len("fpm_p_") :]
        manifest = pm._installed.get(pname)
        if not manifest:
            return await cq.answer(f"Plugin '{pname}' not found.", alert=True)
        subs_text = ", ".join(manifest.active_subcategories) if manifest.active_subcategories else "None"
        deps_text = ", ".join(manifest.dependencies) if manifest.dependencies else "None"
        text = (
            f"{ADMIN.PLUGIN} <b>Plugin:</b> <code>{manifest.name}</code>\n"
            f"• <b>Version:</b> <code>{manifest.version}</code>\n"
            f"• <b>Author:</b> <i>{manifest.author}</i>\n"
            f"• <b>Provider:</b> <code>{manifest.provider}</code>\n"
            f"• <b>Source:</b> <code>{manifest.source}</code>\n"
            f"• <b>Active Subcategories:</b> <code>{subs_text}</code>\n"
            f"• <b>Dependencies:</b> <code>{deps_text}</code>\n"
        )
        buttons = [
            [
                custom.Button.inline(f"{ADMIN.RELOAD} Update", f"fpm_up_{pname}".encode()),
                custom.Button.inline(f"{ADMIN.TRASH} Uninstall", f"fpm_rm_{pname}".encode()),
            ],
            [
                custom.Button.inline(f"{NAV.BACK_ICON} Back to List", b"fpm_list"),
                custom.Button.inline(f"{NAV.HOME_ICON} Main Menu", b"bot_start_menu"),
            ],
        ]
        return await _safe_edit(cq, text, buttons)

    if data == "fpm_doc":
        await cq.answer(f"{STATUS.DOCTOR} Running health scan...")
        doc = await pm.doctor()
        total = doc["total_plugins"]
        healthy = len(doc["healthy"])
        issues = doc["issues"]
        status_icon = f"{INDICATOR.GREEN} Healthy" if not issues else f"{STATUS.WARNING} Issues Found"
        issue_lines = [f"• {iss}" for iss in issues] or ["No missing packages detected."]
        report = (
            f"{STATUS.DOCTOR} <b>FPM Diagnostic Health Report</b>\n\n"
            f"• <b>Status:</b> {status_icon}\n"
            f"• <b>Plugins Checked:</b> <code>{total}</code>\n"
            f"• <b>Satisfied:</b> <code>{healthy}/{total}</code>\n\n"
            "<b>Details:</b>\n" + "\n".join(issue_lines)
        )
        return await _safe_edit(
            cq,
            report,
            [
                [custom.Button.inline(f"{ADMIN.WRENCH} Auto-Repair Missing", b"fpm_rep")],
                _BACK_ROW,
            ],
        )

    if data == "fpm_rep":
        await cq.answer(f"{ADMIN.WRENCH} Initiating auto-repair...")
        repaired, failed = await pm.repair()
        res_msg = (
            f"{STATUS.SUCCESS} All dependencies are already satisfied."
            if repaired == 0 and failed == 0
            else f"{STATUS.SUCCESS} Repaired {repaired} package(s). ({failed} failed)"
        )
        await cq.answer(res_msg, alert=True)
        text, buttons = _make_main_menu()
        return await _safe_edit(cq, f"{res_msg}\n\n{text}", buttons)

    if data.startswith("fpm_up_") and data != "fpm_up_all":
        pname = data[len("fpm_up_") :]
        await cq.answer(f"Updating {pname}...")
        with contextlib.suppress(Exception):
            manifest = await pm.update(pname)
            msg_str = (
                f"{STATUS.SUCCESS} Updated {pname} to v{manifest.version}"
                if manifest
                else f"{STATUS.ERROR} Update failed for {pname}"
            )
            await cq.answer(msg_str, alert=True)
        return

    if data.startswith("fpm_rm_"):
        pname = data[len("fpm_rm_") :]
        await cq.answer(f"Uninstalling {pname}...")
        with contextlib.suppress(Exception):
            ok = await pm.uninstall(pname)
            if ok:
                await cq.answer(f"{ADMIN.TRASH} {pname} uninstalled.", alert=True)
                text, buttons = _make_main_menu()
                return await _safe_edit(cq, text, buttons)
        return

    if data == "fpm_up_all":
        await cq.answer(f"{ADMIN.RELOAD} Checking remote updates...")
        installed = await pm.list_installed()
        updated_count = 0
        for p in installed:
            with contextlib.suppress(Exception):
                if await pm.update(p.name):
                    updated_count += 1
        await cq.answer(f"{ADMIN.RELOAD} Scanned {len(installed)} plugins. Updated {updated_count}.", alert=True)
