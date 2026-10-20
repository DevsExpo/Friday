# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

import logging
from traceback import format_exc
from Main import Friday
from Main.core.types.message import Message
from Main.utils.ui_tokens import ADMIN, INDICATOR, STATUS
from Main.utils.inline_helper import send_inline_widget

packages_list = Friday.db.make_collection("packages") if Friday.db else None


@Friday.register_on_cmd(
    ["fpm", "fpmpanel"],
    cmd_help={
        "help": "Open the interactive FPM Control Center or install packages.",
        "example": [
            "fpm",
            "fpmpanel",
        ],
    },
    owner_only=True
)
async def fpm_hub_cmd(c, m: Message):
    if not m.user_input:
        sent = await send_inline_widget(c, m, "fpm")
        if sent:
            return
        return await list_packages(c, m)
    return await install_pack(c, m)


@Friday.register_on_cmd(
    ["fpm_install", "fpminstall"],
    cmd_help={
        "example": [
            "fpm_install vc",
            "fpm_install DevsExpo/VCPlugin",
            "fpm_install https://github.com/username/XtraPlugins -sub media",
        ],
        "help": "Install external plugins with optional subcategory segregation and fast dependency resolution. Supports shortcuts like 'vc' for DevsExpo/VCPlugin.",
        "user_args": [
            {
                "arg": "sub",
                "help": "Specify comma-separated subcategories to install (e.g. -sub media,lifestyle).",
                "requires_input": True,
            },
            {
                "arg": "ios",
                "help": "Persist and install package on startup.",
                "requires_input": False,
            },
        ],
    },
    requires_input=True,
    owner_only=True
)
async def install_pack(c, m: Message):
    msg = await m.handle_message("PROCESSING")
    raw = m.user_input.strip()
    subcategories = None
    if "-sub " in raw:
        parts = raw.split("-sub ")
        raw = parts[0].strip()
        sub_arg = parts[1].strip().split()[0]
        subcategories = [s.strip() for s in sub_arg.split(",") if s.strip()]

    source = raw.strip()
    if source.lower() in ("vc", "vcplugin"):
        source = "DevsExpo/VCPlugin"
    elif source.lower() in ("xtra", "xtraplugins"):
        source = "DevsExpo/XtraPlugins"

    # Priority 1: Use modern PluginManager (FPM v3)
    if Friday.plugin_manager is not None:
        try:
            provider = "github"
            if source.startswith(("http://", "https://")) and "github.com" not in source:
                provider = "url"

            manifest = await Friday.plugin_manager.install(
                source, provider=provider, subcategories=subcategories, msg=msg
            )
            if manifest:
                name = manifest.name
                author = manifest.author or "Unknown"
                version = manifest.version or "1.0.0"
                active_subs = manifest.active_subcategories

                subs_text = ""
                if active_subs:
                    subs_list = ", ".join([f"<code>{s}</code>" for s in active_subs])
                    subs_text = f"\n• <b>Active Subcategories:</b> {subs_list}"

                await msg.edit_msg(
                    f"{STATUS.SUCCESS} <b>Successfully installed plugin:</b> <code>{name}</code>\n"
                    f"• <b>Author:</b> {author}\n"
                    f"• <b>Version:</b> <code>{version}</code>"
                    f"{subs_text}"
                )

                if "ios" in m.user_args and packages_list:
                    if await packages_list.find_one({"_id": "FPM"}):
                        await packages_list.update_one({"_id": "FPM"}, {"$addToSet": {"installed_packages": source}})
                    else:
                        await packages_list.insert_one({"_id": "FPM", "installed_packages": [source]})
                return
        except ValueError as e:
            return await msg.edit_msg(f"{STATUS.WARNING} {e}")
        except Exception as e:
            logging.error(format_exc())
            if source.startswith(("http://", "https://", "git@")) or "/" in source:
                return await msg.edit_msg(f"{STATUS.ERROR} <b>Installation Failed:</b> <code>{e}</code>")

    return await msg.edit_msg(
        f"{STATUS.ERROR} <b>Package not found:</b> <code>{source}</code>. Please provide a valid GitHub repository (e.g. <code>username/repo</code>) or shortcut."
    )


@Friday.register_on_cmd(
    ["fpm_list", "fpmlist", "plugins"],
    cmd_help={
        "help": "List all installed external plugins with version and active segregated subcategories.",
        "example": [
            "fpm_list",
            "plugins",
        ],
    },
)
async def list_packages(c, m: Message):
    if not Friday.plugin_manager:
        return await m.handle_message(f"{STATUS.ERROR} Plugin Manager not initialized.")

    installed = await Friday.plugin_manager.list_installed()
    if not installed:
        return await m.handle_message(
            f"{ADMIN.PACKAGE} <b>No external plugins currently installed.</b>\nInstall one via <code>.fpm_install &lt;repo&gt;</code>."
        )

    lines = []
    for idx, p in enumerate(installed, 1):
        subs = p.active_subcategories
        subs_badge = f" [<code>{', '.join(subs)}</code>]" if subs else ""
        quarantine_badge = f" {STATUS.WARNING} <i>(Quarantined)</i>" if p.quarantined else ""
        lines.append(
            f"<b>{idx}.</b> <code>{p.name}</code> (v{p.version}) by <i>{p.author}</i>{quarantine_badge}\n"
            f"   • Source: <code>{p.source}</code>{subs_badge}"
        )

    report = (
        f"{ADMIN.PACKAGE} <b>Installed Friday External Plugins ({len(installed)}):</b>\n\n"
        + "\n\n".join(lines)
        + "\n\n<i>Manage subcategories via <code>.fpm_sub &lt;plugin&gt;</code></i>"
    )
    await m.handle_message(report)


@Friday.register_on_cmd(
    ["fpm_sub", "fpmsub", "subcategories"],
    cmd_help={
        "help": "Inspect segregated subcategories of an installed plugin and their enabled status.",
        "example": [
            "fpm_sub XtraPlugins",
            "fpmsub VCPlugin",
        ],
    },
    requires_input=True,
    owner_only=True,
)
async def list_plugin_subcategories(c, m: Message):
    if not Friday.plugin_manager:
        return await m.handle_message(f"{STATUS.ERROR} Plugin Manager not initialized.")

    pname = m.user_input.strip()
    manifest = Friday.plugin_manager._installed.get(pname)
    if not manifest:
        return await m.handle_message(f"{STATUS.ERROR} Plugin <code>{pname}</code> is not installed.")

    subs = manifest.subcategories
    if not subs:
        return await m.handle_message(
            f"{STATUS.INFO} Plugin <code>{pname}</code> is monolithic and has no segregated subcategories."
        )

    lines = []
    for sname, sdata in subs.items():
        is_active = sname in manifest.active_subcategories
        status_icon = f"{INDICATOR.GREEN} Active" if is_active else f"{INDICATOR.WHITE} Disabled"
        deps = sdata.get("dependencies", [])
        deps_str = f" | Deps: {', '.join(deps)}" if deps else " | Zero Deps"
        lines.append(
            f"• <b>{sdata.get('name', sname)}</b> (<code>{sname}</code>) - {status_icon}\n"
            f"  {sdata.get('file_count', 0)} files{deps_str}"
        )

    report = (
        f"{ADMIN.FOLDER} <b>Subcategories for {manifest.name}:</b>\n\n" + "\n\n".join(lines) + "\n\n<b>Commands:</b>\n"
        f"• <code>.fpm_enable {pname} &lt;category&gt;</code>\n"
        f"• <code>.fpm_disable {pname} &lt;category&gt;</code>"
    )
    await m.handle_message(report)


@Friday.register_on_cmd(
    ["fpm_enable", "fpmenable"],
    cmd_help={
        "help": "Enable and hot-load a segregated subcategory in an installed plugin.",
        "example": [
            "fpm_enable XtraPlugins media",
            "fpmenable XtraPlugins games",
        ],
    },
    requires_input=True,
    owner_only=True
)
async def enable_subcategory_cmd(c, m: Message):
    if not Friday.plugin_manager:
        return await m.handle_message(f"{STATUS.ERROR} Plugin Manager not initialized.")

    tokens = m.user_input.strip().split()
    if len(tokens) < 2:
        return await m.handle_message(
            f"{STATUS.WARNING} <b>Usage:</b> <code>.fpm_enable &lt;plugin_name&gt; &lt;subcategory&gt;</code>"
        )

    pname, sub = tokens[0], tokens[1].lower()
    success = await Friday.plugin_manager.enable_subcategory(pname, sub)
    if success:
        await m.handle_message(f"{STATUS.SUCCESS} Subcategory <code>{sub}</code> in <b>{pname}</b> enabled and loaded!")
    else:
        await m.handle_message(
            f"{STATUS.ERROR} Failed to enable subcategory <code>{sub}</code>. Check plugin name and subcategories."
        )


@Friday.register_on_cmd(
    ["fpm_disable", "fpmdisable"],
    cmd_help={
        "help": "Disable a segregated subcategory in an installed plugin without deleting files.",
        "example": [
            "fpm_disable XtraPlugins lifestyle",
            "fpmdisable XtraPlugins system",
        ],
    },
    requires_input=True,
    owner_only=True
)
async def disable_subcategory_cmd(c, m: Message):
    if not Friday.plugin_manager:
        return await m.handle_message(f"{STATUS.ERROR} Plugin Manager not initialized.")
    tokens = m.user_input.strip().split()
    if len(tokens) < 2:
        return await m.handle_message(
            f"{STATUS.WARNING} <b>Usage:</b> <code>.fpm_disable &lt;plugin_name&gt; &lt;subcategory&gt;</code>"
        )

    pname, sub = tokens[0], tokens[1].lower()
    success = await Friday.plugin_manager.disable_subcategory(pname, sub)
    if success:
        await m.handle_message(
            f"{INDICATOR.WHITE} Subcategory <code>{sub}</code> in <b>{pname}</b> disabled. Restart Friday to unload active handlers."
        )
    else:
        await m.handle_message(f"{STATUS.ERROR} Failed to disable subcategory <code>{sub}</code>.")


@Friday.register_on_cmd(
    ["fpm_doctor", "fpmdoctor"],
    cmd_help={
        "help": "Diagnose the health of all installed plugins, verify Python imports, and detect missing packages.",
        "example": "fpm_doctor",
    },
    owner_only=True,
)
async def doctor_cmd(c, m: Message):
    if not Friday.plugin_manager:
        return await m.handle_message(f"{STATUS.ERROR} Plugin Manager not initialized.")

    msg = await m.handle_message(
        f"{STATUS.DOCTOR} Running FPM health check across all plugins and Python environment..."
    )
    doc = await Friday.plugin_manager.doctor()

    total = doc["total_plugins"]
    healthy = len(doc["healthy"])
    issues = doc["issues"]

    status_icon = f"{INDICATOR.GREEN} Healthy" if not issues else f"{STATUS.WARNING} Issues Found"

    issue_block = ""
    if issues:
        issue_lines = [f"  • {iss}" for iss in issues]
        issue_block = (
            "\n\n<b>Detected Issues:</b>\n"
            + "\n".join(issue_lines)
            + "\n\n<i>Run <code>.fpm_repair</code> to batch-install missing packages!</i>"
        )

    report = (
        f"{STATUS.DOCTOR} <b>FPM Diagnostic Doctor Report</b>\n\n"
        f"• <b>Status:</b> {status_icon}\n"
        f"• <b>Plugins Inspected:</b> <code>{total}</code>\n"
        f"• <b>Fully Satisfied:</b> <code>{healthy}/{total}</code>"
        f"{issue_block}"
    )
    await msg.edit_msg(report)


@Friday.register_on_cmd(
    ["fpm_repair", "fpmrepair", "fpmfix"],
    cmd_help={
        "help": "Batch-install any missing dependencies across all installed plugins without restarting the bot.",
        "example": "fpm_repair",
    },
    owner_only=True
)
async def repair_cmd(c, m: Message):
    if not Friday.plugin_manager:
        return await m.handle_message(f"{STATUS.ERROR} Plugin Manager not initialized.")

    msg = await m.handle_message(f"{ADMIN.WRENCH} Scanning and resolving missing plugin dependencies...")
    repaired, failed = await Friday.plugin_manager.repair(msg)

    if repaired == 0 and failed == 0:
        return await msg.edit_msg(
            f"{STATUS.SUCCESS} <b>Everything is in order:</b> No missing dependencies detected across any plugins."
        )

    if failed == 0:
        await msg.edit_msg(
            f"{STATUS.SUCCESS} <b>Repair Complete:</b> Successfully installed <code>{repaired}</code> missing package(s)!"
        )
    else:
        await msg.edit_msg(
            f"{STATUS.WARNING} <b>Partial Repair:</b> Installed {repaired} package(s), but {failed} package(s) encountered installation errors."
        )


@Friday.register_on_cmd(
    ["fpm_uninstall", "unfpm"],
    cmd_help={
        "example": "fpm_uninstall my_plugin",
        "help": "Uninstall an external plugin and remove all files.",
    },
    requires_input=True,
    owner_only=True
)
async def uninstall_pack(c, m: Message):
    msg = await m.handle_message("PROCESSING")
    pn = m.user_input.strip()

    if Friday.plugin_manager is not None:
        try:
            success = await Friday.plugin_manager.uninstall(pn, msg=msg)
            if success:
                if packages_list:
                    await packages_list.update_one({"_id": "FPM"}, {"$pull": {"installed_packages": pn}})
                return await msg.edit_msg(f"{ADMIN.TRASH} Plugin <code>{pn}</code> uninstalled successfully.")
            return await msg.edit_msg(f"{STATUS.ERROR} Plugin <code>{pn}</code> is not installed.")
        except Exception as e:
            return await msg.edit_msg(f"{STATUS.ERROR} Uninstall failed: <code>{e}</code>")

    return await msg.edit_msg(f"{STATUS.ERROR} Plugin <code>{pn}</code> is not installed.")


@Friday.register_on_cmd(
    ["fpm_update", "updatefpm"],
    cmd_help={
        "example": "fpm_update my_plugin",
        "help": "Update an installed plugin to its latest version.",
    },
    requires_input=True,
    owner_only=True
)
async def update_pack(c, m: Message):
    msg = await m.handle_message("PROCESSING")
    pn = m.user_input.strip()

    if Friday.plugin_manager is not None:
        try:
            manifest = await Friday.plugin_manager.update(pn, msg=msg)
            if manifest:
                return await msg.edit_msg(
                    f"{STATUS.SUCCESS} Plugin <code>{pn}</code> updated successfully to version <code>{manifest.version}</code>."
                )
            return await msg.edit_msg(f"{STATUS.ERROR} Could not update plugin <code>{pn}</code>.")
        except Exception as e:
            return await msg.edit_msg(f"{STATUS.ERROR} Update error: <code>{e}</code>")

    return await msg.edit_msg(f"{STATUS.ERROR} Could not update plugin <code>{pn}</code>.")
