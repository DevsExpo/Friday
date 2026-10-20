# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

import re
import html
from Main import Friday
from Main.utils.custom_filters import filters
from Main.core.decorators import log_errors, iuser_check
from telethon import custom
from Main.utils.ui_tokens import NAV, STATUS
from Main.utils.help_menu import get_help_header, get_help_menu, get_plugin_data


@Friday.bot.on_callback_query(filters.regex("close_help"))
@log_errors
@iuser_check
async def close_help(c, cq):
    await cq.edit(
        f"<b>Help Menu Closed {STATUS.KEY}</b>",
        buttons=[
            [
                custom.Button.inline("Re-Open", b"re_open"),
                custom.Button.inline(f"{NAV.HOME_ICON} Main Menu", b"bot_start_menu"),
            ]
        ],
        parse_mode="html",
    )


@Friday.bot.on_inline_query(filters.regex(r"^change_lang", flags=re.IGNORECASE))
@log_errors
@iuser_check
async def reload_language(c, iq):
    bttns = [
        [
            custom.Button.inline(
                Friday.all_lang_strings[lang].get("def", lang).title(),
                f"reload_lang_{lang}".encode("utf-8"),
            )
        ]
        for lang in Friday.all_lang_strings.keys()
    ]
    builder = iq.builder
    result = builder.article(
        title="Change Friday default language",
        text="<b>Friday Language Setup Wizard</b>\n<b>Click a language available below to change Friday's default language</b>",
        parse_mode="html",
        buttons=bttns,
    )
    await iq.answer([result])


@Friday.bot.on_callback_query(filters.regex(r"^reload_lang_(.*)"))
@log_errors
@iuser_check
async def change_lang(c, cb):
    data_str = cb.data.decode("utf-8") if isinstance(cb.data, bytes) else str(cb.data)
    match = re.search(r"^reload_lang_(.*)", data_str)
    if not match:
        return
    lang = match.group(1)
    if lang not in Friday.all_lang_strings.keys():
        return await cb.answer(Friday.get_string("INVALID_LANG_SELECTED") or "Invalid language", alert=True)
    if lang == Friday.selected_lang:
        return await cb.answer(Friday.get_string("LANG_IN_USE") or "Language already in use")
    Friday.selected_lang = lang
    await Friday.config.add_env_to_db("UB_LANG", lang)
    return await cb.answer(Friday.get_string("LANG_SELECTED") or "Language selected!")


@Friday.bot.on_inline_query(filters.regex(r"^help ?(.+)?", flags=re.IGNORECASE))
@log_errors
@iuser_check
async def help_inline(c, iq):
    text = iq.text or ""
    parts = text.split(None, 1)
    plugin = parts[1].strip() if len(parts) > 1 else None
    builder = iq.builder

    if not plugin:
        buttons = await get_help_menu(category="all", page=0)
        result = builder.article(
            title="Help Menu",
            text=await get_help_header(category="all", page=0),
            parse_mode="html",
            buttons=buttons,
        )
        await iq.answer([result])
    elif plugin.lower() in Friday._command_help_message_data:
        p_text, p_buttons = await get_plugin_data(plugin.lower(), page=0, category="all")
        result = builder.article(
            title=f"Help Module for {plugin}",
            text=p_text,
            parse_mode="html",
            buttons=[[custom.Button.inline("Go to help menu", b"re_open")]],
        )
        await iq.answer([result])
    else:
        result = builder.article(
            title="Plugin not found!",
            text=f"Help for {plugin} was not found!",
        )
        await iq.answer([result])


@Friday.bot.on_callback_query(filters.regex(r"^re_open"))
@log_errors
@iuser_check
async def re_help(c, cq):
    buttons = await get_help_menu(category="all", page=0)
    await cq.edit(await get_help_header(category="all", page=0), buttons=buttons, parse_mode="html")


@Friday.bot.on_callback_query(filters.regex(r"^help(?:#([a-zA-Z0-9_]+)(?:\?(.*))?)?$"))
@log_errors
@iuser_check
async def help_callback(c, cq):
    data_str = cq.data.decode("utf-8") if isinstance(cq.data, bytes) else str(cq.data)
    match = re.search(r"^help(?:#([a-zA-Z0-9_]+)(?:\?(.*))?)?$", data_str)
    if not match or not match.group(1):
        buttons = await get_help_menu(category="all", page=0)
        return await cq.edit(
            await get_help_header(category="all", page=0), buttons=buttons, parse_mode="html"
        )

    text = match.group(1)
    query_str = match.group(2) or ""
    params = dict(item.split("=", 1) for item in query_str.split("&") if "=" in item)
    category = params.get("cat", "all")
    page = int(params.get("page", 0)) if params.get("page", "").isdigit() else 0

    if text in ("_page", "_cat"):
        buttons = await get_help_menu(category=category, page=page)
        return await cq.edit(
            await get_help_header(category=category, page=page), buttons=buttons, parse_mode="html"
        )

    if text.lower() not in Friday._command_help_message_data:
        return await cq.answer(Friday.get_string("PLUGIN_404") or "Plugin not found")

    p_text, p_buttons = await get_plugin_data(text, page=page, category=category)
    await cq.edit(p_text, buttons=p_buttons, parse_mode="html")


@Friday.bot.on_message(filters.command(["help"], prefixes="/"))
@log_errors
async def bot_help_message_handler(c, m):
    sender_id = getattr(m, "sender_id", None)
    if not sender_id or sender_id not in Friday.auth_users:
        if getattr(m, "is_private", False):
            return await m.reply(f"{STATUS.WARNING} <i>You are not authorized to use this bot.</i>", parse_mode="html")
        return

    raw_text = getattr(m, "text", "") or getattr(m, "raw_text", "") or ""
    parts = raw_text.split(None, 1)
    plugin = parts[1].strip().lower() if len(parts) > 1 else None

    if not plugin:
        buttons = await get_help_menu(category="all", page=0)
        await m.reply(await get_help_header(category="all", page=0), buttons=buttons, parse_mode="html")
    elif plugin in Friday._command_help_message_data:
        p_text, p_buttons = await get_plugin_data(plugin, page=0, category="all")
        await m.reply(p_text, buttons=p_buttons, parse_mode="html")
    else:
        await m.reply(f"<i>Help for</i> <code>{html.escape(plugin)}</code> <i>was not found!</i>", parse_mode="html")
