# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

"""Shared PM-security panel state and renderers.

Both the assistant-bot inline panel (``Main/plugins/bot/pm_security_inline.py``)
and the userbot PM-permission plugin (``Main/plugins/userbot/PM_Security.py``)
need the same warning cache and the same panel renderers.

Keeping them here -- in a neutral module that neither plugin imports back --
means there is exactly **one** cache object and **no** import cycle between the
two plugins.  Previously the cache lived in the userbot plugin and the bot
panel imported it at module scope, which both re-executed the userbot plugin
and split the cache in two (the panel then always reported "0 pending").
"""

import html
from typing import Any, Dict

from telethon import custom

from Main import Friday
from Main.utils.ui_tokens import ADMIN, INDICATOR, NAV, STATUS

pm_permit_warning_cache: Dict[int, Any] = {}


async def render_pmpermit_panel():
    is_enabled = await Friday.config.get_pm_sts()
    limit = await Friday.config.get_pm_warn_limit()
    allow_contacts = await Friday.config.get_pm_allow_contacts()
    custom_msg = await Friday.config.get_pm_custom_msg()
    pending_count = len(pm_permit_warning_cache)

    status_badge = (
        f"{INDICATOR.GREEN} <b>ACTIVE &amp; SCREENING</b>" if is_enabled else f"{INDICATOR.RED} <b>DISABLED</b>"
    )
    contacts_badge = (
        f"{STATUS.SUCCESS} <b>ALLOWED (Bypass)</b>" if allow_contacts else f"{STATUS.SHIELD} <b>SCREENED</b>"
    )
    msg_badge = f"{ADMIN.NOTE} <i>Customized</i>" if custom_msg else f"{ADMIN.DOC} <i>Default Template</i>"

    text = (
        f"{STATUS.SHIELD} <b>Friday PM Security Control Panel</b>\n\n"
        f"• <b>Status:</b> {status_badge}\n"
        f"• <b>Warning Limit:</b> <code>{limit} Warnings</code> (Blocks on #{limit + 1})\n"
        f"• <b>Allow Contacts:</b> {contacts_badge}\n"
        f"• <b>Warning Message:</b> {msg_badge}\n"
        f"• <b>Pending In Queue:</b> <code>{pending_count} user(s)</code>\n\n"
        "<i>Tap buttons below to change policies, adjust limits (1-20), or mass approve:</i>"
    )
    buttons = [
        [
            custom.Button.inline(
                f"{INDICATOR.RED} Turn OFF PM Permit" if is_enabled else f"{INDICATOR.GREEN} Turn ON PM Permit",
                b"pmsec_toggle",
            )
        ],
        [
            custom.Button.inline(
                f"{ADMIN.CONTACT} Contacts: ALLOWED" if allow_contacts else f"{ADMIN.CONTACT} Contacts: SCREENED",
                b"pmsec_contacts",
            ),
            custom.Button.inline(f"{ADMIN.NUMBER} Set Limit ({limit})", b"pmsec_open_limits"),
        ],
        [
            custom.Button.inline(f"{ADMIN.CHAT} View Message", b"pmsec_view_msg"),
            custom.Button.inline(f"{STATUS.SUCCESS} Mass Approve ({pending_count})", b"pmsec_mass_appr"),
        ],
        [
            custom.Button.inline(f"{STATUS.CLEAN} Reset Warnings", b"pmsec_reset"),
            custom.Button.inline(f"{STATUS.GEAR} Settings Panel", b"panel_refresh"),
        ],
        [
            custom.Button.inline(f"{NAV.HOME_ICON} Main Menu", b"bot_start_menu"),
            custom.Button.inline(f"{NAV.CLOSE_ICON} Close", b"pmsec_close"),
        ],
    ]
    return text, buttons


async def render_limits_panel():
    limit = await Friday.config.get_pm_warn_limit()
    text = (
        f"{ADMIN.NUMBER} <b>Select PM Security Warning Limit</b>\n\n"
        "Choose how many warning messages a user receives before being automatically blocked.\n\n"
        f"• Current Active Limit: <b>{limit} Warnings</b>\n\n"
        "<i>Tap any number (1 - 20) below to set the limit:</i>"
    )
    buttons = [
        [
            custom.Button.inline(
                f"{STATUS.SUCCESS} {r * 5 + c}" if (r * 5 + c) == limit else str(r * 5 + c),
                f"pmsec_set_limit_{r * 5 + c}".encode(),
            )
            for c in range(1, 6)
        ]
        for r in range(4)
    ]
    buttons.append(
        [
            custom.Button.inline(f"{NAV.BACK_ICON} Back to PM Security", b"pmsec_main_panel"),
            custom.Button.inline(f"{NAV.HOME_ICON} Main Menu", b"bot_start_menu"),
        ]
    )
    return text, buttons


async def render_msg_panel():
    custom_msg = await Friday.config.get_pm_custom_msg()
    status_text = (
        f"<blockquote>{html.escape(custom_msg)}</blockquote>"
        if custom_msg
        else "<i>(Currently using default template)</i>"
    )
    text = (
        f"{ADMIN.CHAT} <b>PM Security Warning Message</b>\n\n"
        f"<b>Current Active Message:</b>\n{status_text}\n\n"
        "<i>To change your message, send:</i>\n"
        f"<code>{Friday.user_command_handler}setpmmsg &lt;your custom message&gt;</code>"
    )
    buttons = [
        [custom.Button.inline(f"{ADMIN.RELOAD} Reset to Default Template", b"pmsec_reset_msg")],
        [
            custom.Button.inline(f"{NAV.BACK_ICON} Back to PM Security", b"pmsec_main_panel"),
            custom.Button.inline(f"{NAV.HOME_ICON} Main Menu", b"bot_start_menu"),
        ],
    ]
    return text, buttons
