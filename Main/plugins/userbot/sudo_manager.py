# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

"""
A-Z for sudo users!
"""

from Main import Friday
import re
from style import bullets
from Main.core.types.client import FridayTelegramClient as Client
from Main.core.types.message import Message
from Main.utils.ui_tokens import STATUS, ADMIN
from Main.utils.inline_helper import send_inline_widget
from Main.plugins.bot.sudo_inline import _render_sudo_menu


b4 = bullets.get("bullet4", "•")
b5 = bullets.get("bullet5", "├")
b6 = bullets.get("bullet6", "│")
b7 = bullets.get("bullet7", "└")


def bulletify(u_):
    out = "<b>Sudo Users :</b> \n"
    len_ = len(u_)
    if len_ == 1:
        mention = getattr(u_[0], "mention", str(u_[0].id))
        return f"{out}\n{b6}{b4} {mention}"
    if len_ == 2:
        m0 = getattr(u_[0], "mention", str(u_[0].id))
        m1 = getattr(u_[1], "mention", str(u_[1].id))
        return f"{out}\n{b5}{b4} {m0}\n{b7}{b4} {m1}"
    for i in enumerate(u_):
        m_curr = getattr(i[1], "mention", str(i[1].id))
        if i[0] == 0:
            out += f"\n{b5}{b4} {m_curr}"
        elif i[0] == len_ - 1:
            out += f"\n{b7}{b4} {m_curr}"
        else:
            out += f"\n{b6}{b4} {m_curr}"
    return out


@Friday.register_on_cmd(
    "dpfs",
    cmd_help={
        "help": "Disabled cmds for sudo users!",
        "example": [
            "dpfs eval",
            "dpfs exec, sh",
        ],
    },
    requires_input=True,
    owner_only=True,
)
async def disabled_ps_func(c: Client, m: Message):
    msg = await m.handle_message("PROCESSING")
    input_ = m.user_input.strip()
    if "," in input_:
        input_ = [x.strip() for x in input_.split(",") if x.strip()]
    else:
        input_ = [input_]
    await Friday.config.sync_env_to_db("DISABLED_SUDO_CMD_LIST", input_, push_=True)
    current = getattr(Friday, "disabled_sudo_plugin_list", [])
    Friday.disabled_sudo_plugin_list = list(dict.fromkeys([*current, *[x.lower() for x in input_]]))
    Friday.prepare_help()
    await msg.edit_msg("DISABLED_SUDO_CMD", string_args=(str(input_),))


@Friday.register_on_cmd(
    "rmdfs",
    cmd_help={"help": "Disabled cmds from sudo users", "example": "rmdfs eval"},
    requires_input=True,
    owner_only=True
)
async def remove_disabled_ps_func(c: Client, m: Message):
    msg = await m.handle_message("PROCESSING")
    input_ = m.user_input.strip()
    if "," in input_:
        input_ = [x.strip() for x in input_.split(",") if x.strip()]
    else:
        input_ = [input_]
    Friday.disabled_sudo_plugin_list = await Friday.config.unsync_env_to_db("DISABLED_SUDO_CMD_LIST", input_)
    Friday.disabled_sudo_plugin_list = [str(item).strip().lower() for item in Friday.disabled_sudo_plugin_list]
    Friday.prepare_help()
    await msg.edit_msg("UNDISABLED_SUDO_CMD", string_args=(str(input_),))


@Friday.register_on_cmd(
    "addsudo",
    cmd_help={
        "help": "Add a user to sudo list",
        "example": [
            "addsudo @username",
            "addsudo 123456789",
        ],
    },
    owner_only=True
)
async def add_sudo_func(c: Client, m: Message):
    msg = await m.handle_message("PROCESSING")
    user, _, is_channel = m.get_user
    if not user or is_channel:
        return await msg.edit_msg("INVALID_USER")
    target_id = None
    mention_str = None
    try:
        user_ent = await c.get_users(user)
        target_id = user_ent.id
        mention_str = getattr(user_ent, "mention", str(target_id))
    except Exception:
        if isinstance(user, int):
            target_id = user
            mention_str = str(user)
        else:
            return await msg.edit_msg("INVALID_USER")

    sudo_list = await Friday.config.get_sudo()
    if target_id in sudo_list:
        return await msg.edit_msg("ALREADY_IN_SUDO")
    await Friday.config.add_sudo(target_id)
    await msg.edit_msg("ADDED_SUDO", string_args=(mention_str,))


@Friday.register_on_cmd(
    "rmsudo",
    cmd_help={
        "help": "Remove sudo from sudo list",
        "example": [
            "rmsudo @username",
            "rmsudo 123456789",
            "rmsudo -a",
        ],
        "user_args": [
            {
                "arg": "a",
                "help": "Removes all sudos from the db.",
                "requires_input": False,
            },
        ],
    },
    owner_only=True
)
async def rm_sudo_func(c: Client, m: Message):
    msg = await m.handle_message("PROCESSING")
    user, _, is_channel = m.get_user
    acg = await Friday.config.get_sudo()
    user_args = m.user_args
    if "a" in user_args:
        count = 0
        lacg = len(acg)
        for i in acg:
            try:
                await Friday.config.del_sudo(i)
                count += 1
            except Exception:
                pass
        return await msg.edit_msg("DEL_SUDO_A", string_args=(count, lacg))

    if not user or is_channel:
        return await msg.edit_msg("INVALID_USER")

    target_id = None
    mention_str = None
    try:
        user_ent = await c.get_users(user)
        target_id = user_ent.id
        mention_str = getattr(user_ent, "mention", str(target_id))
    except Exception:
        if isinstance(user, int):
            target_id = user
            mention_str = str(user)
        else:
            return await msg.edit_msg("INVALID_USER")

    if target_id not in acg:
        return await msg.edit_msg("NOT_IN_SUDO")
    await Friday.config.del_sudo(target_id)
    await msg.edit_msg("DEL_SUDO", string_args=(mention_str,))


@Friday.register_on_cmd(
    "listsudo",
    cmd_help={
        "help": "list all sudo users!",
        "example": [
            "listsudo",
            "listsudo -basic",
        ],
        "user_args": [
            {
                "arg": "basic",
                "help": "Force text-based list without inline buttons widget.",
                "requires_input": False,
            }
        ],
    },
    owner_only=True
)
async def list_sudo_func(c: Client, m: Message):
    is_bot = (getattr(c, "myself", None) and getattr(c.myself, "bot", False)) or (
        getattr(Friday, "bot_info", None) and getattr(c, "myself", None) and c.myself.id == Friday.bot_info.id
    )
    if is_bot:
        text, buttons = await _render_sudo_menu(c)
        return await m.reply(text, buttons=buttons, parse_mode="html")

    if "-basic" not in m.user_args and "-text" not in m.user_args:
        try:
            if await send_inline_widget(c, m, "listsudo"):
                return
        except Exception:
            pass

    msg = await m.handle_message("PROCESSING")
    users_ = await Friday.config.get_sudo()
    if not users_:
        return await msg.edit_msg("NO_SUDO_LIST")
    user_ = []
    for i in users_:
        try:
            user_.append(await c.get_users(int(i)))
        except Exception:
            user_.append(type("DummyUser", (), {"id": int(i), "mention": f"<code>{i}</code>"}))
    if not user_:
        return await msg.edit_msg("NO_SUDO_LIST")

    await msg.edit_msg(bulletify(user_))
 
 
@Friday.register_on_cmd(
    ["sudomgr", "sudomanager"],
    cmd_help={
        "help": "Manage sudo plugin access permissions (grant all plugins or restrict to selected plugins).",
        "example": [
            "sudomgr",
            "sudomgr all",
            "sudomgr all -confirm",
            "sudomgr ping, whois, help",
            "sudomgr ping, whois, help -confirm",
        ],
        "user_args": [
            {
                "arg": "confirm",
                "help": "Confirm the permission change after security warning.",
                "requires_input": False,
            },
            {
                "arg": "y",
                "help": "Short alias for -confirm.",
                "requires_input": False,
            },
        ],
    },
    owner_only=True,
)
async def sudomgr_func(c: Client, m: Message):
    msg = await m.handle_message("PROCESSING")
    prefix = getattr(Friday, "user_command_handler", ".") or "."
    user_args = m.user_args
    is_confirmed = bool(
        user_args
        and (
            "confirm" in user_args
            or "y" in user_args
            or "f" in user_args
            or "force" in user_args
        )
    )

    raw_input = (m.user_input or "").strip()
    all_plugins = sorted(list({k.lower() for k in Friday.cmd_list.keys()}))

    if not raw_input or raw_input.lower() in ("status", "info"):
        sudo_users = await Friday.config.get_sudo() or []
        disabled = getattr(Friday, "disabled_sudo_plugin_list", []) or []
        mode_text = (
            f"{STATUS.SUCCESS} <b>All Plugins Allowed</b>"
            if not disabled
            else f"{STATUS.WARNING} <b>Restricted</b> ({len(disabled)} plugins blocked)"
        )
        disabled_str = (
            ", ".join(f"<code>{p}</code>" for p in sorted(disabled[:20]))
            if disabled
            else "<i>None (All accessible)</i>"
        )
        if len(disabled) > 20:
            disabled_str += f" <i>...and {len(disabled) - 20} more</i>"

        text = (
            f"{ADMIN.OWNER} <b>Sudo Permissions Manager</b>\n\n"
            f"• <b>Sudo Users:</b> <code>{len(sudo_users)}</code> authorized\n"
            f"• <b>Access Mode:</b> {mode_text}\n"
            f"• <b>Disabled Plugins:</b> {disabled_str}\n\n"
            "<b>Usage Commands:</b>\n"
            f"• <code>{prefix}sudomgr all</code> - Grant access to all plugins (requires confirmation)\n"
            f"• <code>{prefix}sudomgr &lt;p1, p2...&gt;</code> - Restrict sudo to selected plugins only\n"
            f"• <code>{prefix}dpfs &lt;plugin&gt;</code> - Block a specific plugin from sudo\n"
            f"• <code>{prefix}rmdfs &lt;plugin&gt;</code> - Unblock a specific plugin for sudo\n\n"
            f"<i>{STATUS.SHIELD} Owner-only commands always remain strictly protected.</i>"
        )
        return await msg.edit_msg(text)

    # 2. Grant ALL plugins
    if raw_input.lower() in ("all", "--all", "-all"):
        if not is_confirmed:
            return await msg.edit_msg(
                f"{STATUS.WARNING} <b>CRITICAL SECURITY WARNING: Grant All Plugins to Sudo</b>\n\n"
                "You are about to grant sudo users access to <b>ALL PLUGINS</b> on this userbot.\n"
                "This allows sudo users to execute every non-owner command (moderation, cleanup, tools, etc.).\n\n"
                f"<i>({STATUS.SHIELD} Commands marked <code>owner_only</code> will always remain strictly blocked from sudo).</i>\n\n"
                "Are you <b>100% sure</b> you want to proceed?\n"
                "To confirm, re-run with:\n"
                f"<code>{prefix}sudomgr all -confirm</code> (or <code>-y</code>)"
            )

        await Friday.config.sync_env_to_db("DISABLED_SUDO_CMD_LIST", [], upsert=True)
        Friday.disabled_sudo_plugin_list = []
        Friday.prepare_help()
        return await msg.edit_msg(
            f"{STATUS.SHIELD} <b>Sudo Permissions Configured:</b>\n"
            f"{STATUS.SUCCESS} Granted sudo users access to <b>ALL PLUGINS</b>!\n\n"
            f"<i>{STATUS.LOCK} All owner_only commands remain strictly restricted to you.</i>"
        )
    raw = raw_input.lower()
    if raw.startswith("select "):
        raw = raw[7:]
    selected_tokens = [x.strip().lower() for x in re.split(r"[\s,]+", raw) if x.strip()]
    valid_selected = [p for p in selected_tokens if p in all_plugins or any(k in p for k in all_plugins)]
    if not valid_selected:
        available_preview = ", ".join(f"<code>{p}</code>" for p in all_plugins[:15])
        return await msg.edit_msg(
            f"{STATUS.ERROR} <b>Invalid Plugin Selection:</b> None of the specified names matched loaded plugins.\n\n"
            f"<b>Available plugins:</b> {available_preview}..."
        )

    if not is_confirmed:
        blocked_count = max(0, len(all_plugins) - len(valid_selected))
        return await msg.edit_msg(
            f"{STATUS.WARNING} <b>CONFIRMATION: Restrict Sudo to Selected Plugins</b>\n\n"
            f"You are configuring sudo access for <b>{len(valid_selected)} plugins</b>:\n"
            f"• <b>Allowed:</b> <code>{', '.join(valid_selected)}</code>\n"
            f"• <b>Blocked:</b> <code>{blocked_count}</code> other loaded plugins will be disabled for sudo users.\n\n"
            "Are you <b>100% sure</b>?\n"
            "To confirm, re-run with:\n"
            f"<code>{prefix}sudomgr {', '.join(valid_selected)} -confirm</code> (or <code>-y</code>)"
        )

    blocked_plugins = [p for p in all_plugins if p not in valid_selected]
    await Friday.config.sync_env_to_db("DISABLED_SUDO_CMD_LIST", blocked_plugins, upsert=True)
    Friday.disabled_sudo_plugin_list = blocked_plugins
    Friday.prepare_help()

    return await msg.edit_msg(
        f"{STATUS.SHIELD} <b>Sudo Permissions Configured:</b>\n"
        f"{STATUS.SUCCESS} Sudo access restricted to <b>{len(valid_selected)} selected plugins</b>:\n"
        f"<code>{', '.join(valid_selected)}</code>\n\n"
        f"{STATUS.FORBIDDEN} <b>Restricted:</b> <code>{len(blocked_plugins)}</code> other plugins are now blocked for sudo users."
    )
