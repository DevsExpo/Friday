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
from Main.core.decorators import log_errors, iuser_check
from Main.utils.custom_filters import filters
from Main.utils.inline_helper import is_owner_cb, is_owner
from Main.utils.ui_tokens import ADMIN, NAV, STATUS


async def _render_sudo_menu(c):
    """Build the sudo users panel text and inline buttons."""
    sudos = await Friday.config.get_sudo() or []
    if not sudos:
        return (
            f"{ADMIN.OWNER} <b>Sudo Users Management</b>\n\n"
            "<i>No sudo users currently authorized.</i>\n\n"
            "To grant sudo access, use:\n"
            "<code>.addsudo @username</code>"
        ), [
            [custom.Button.inline(NAV.REFRESH, b"sudo_refresh")],
            [custom.Button.inline(NAV.CLOSE, b"sudo_close")],
        ]

    lines = [
        f"{ADMIN.OWNER} <b>Sudo Users Management Panel</b>\n",
        f"<b>Authorized Users ({len(sudos)}):</b>\n",
    ]
    buttons = []
    for uid in sudos:
        with contextlib.suppress(Exception):
            user_ent = await c.get_entity(int(uid))
            name = getattr(user_ent, "first_name", "") or str(uid)
            uname = f"@{user_ent.username}" if getattr(user_ent, "username", None) else f"ID: {uid}"
            lines.append(f"• <b>{name}</b> (<code>{uname}</code>)")
            buttons.append([custom.Button.inline(f"{STATUS.ERROR} Revoke {name[:14]}", f"sudo_rm:{uid}".encode())])
            continue
        lines.append(f"• User ID: <code>{uid}</code>")
        buttons.append([custom.Button.inline(f"{STATUS.ERROR} Revoke {uid}", f"sudo_rm:{uid}".encode())])

    lines.append(f"\n<i>{ADMIN.LAMP} Tap any revoke button below to remove sudo privileges instantly:</i>")
    buttons.append(
        [
            custom.Button.inline(NAV.REFRESH, b"sudo_refresh"),
            custom.Button.inline(NAV.CLOSE, b"sudo_close"),
        ]
    )
    return "\n".join(lines), buttons


@Friday.bot.on_inline_query(filters.regex(r"^listsudo$"))
@log_errors
@iuser_check
async def listsudo_inline_query_handler(c, iq):
    if not is_owner(iq.sender_id):
        return await iq.answer(
            [], switch_pm=f"{STATUS.DENIED} Access denied: Sudo management is owner only.", switch_pm_param="auth"
        )
    text, buttons = await _render_sudo_menu(c)
    res = iq.builder.article(
        title=f"{ADMIN.OWNER} Sudo Users Management",
        description="View and revoke authorized sudo users with one tap.",
        text=text,
        buttons=buttons,
        parse_mode="html",
    )
    await iq.answer([res], cache_time=0)


@Friday.bot.on_callback_query(filters.regex(r"^sudo_"))
@log_errors
async def sudo_callback_handler(c, cb):
    if not is_owner_cb(cb):
        return await cb.answer(
            f"{STATUS.DENIED} Access denied: Only primary bot owner can manage sudo users.", alert=True
        )

    data = cb.data.decode("utf-8") if isinstance(cb.data, bytes) else str(cb.data)

    if data.startswith("sudo_rm:"):
        target_uid = int(data.split(":", 1)[1])
        await Friday.config.del_sudo(target_uid)
        await cb.answer(f"{STATUS.ERROR} Revoked sudo privileges for {target_uid}!", alert=True)

    elif data == "sudo_refresh":
        await cb.answer(f"{ADMIN.RELOAD} Sudo list refreshed!")

    elif data == "sudo_close":
        with contextlib.suppress(Exception):
            await cb.delete()
            return
        with contextlib.suppress(Exception):
            await cb.edit("<i>Sudo management panel closed.</i>", buttons=None, parse_mode="html")
        return

    with contextlib.suppress(Exception):
        text, buttons = await _render_sudo_menu(c)
        await cb.edit(text, buttons=buttons, parse_mode="html")
