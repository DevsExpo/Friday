# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Altriux/Friday/blob/main/LICENSE >
#
# All rights reserved.

"""Shared help-menu builders.

The bot plugin (``Main/plugins/bot/help.py``) owns the inline/callback handlers,
but the menu *builders* are also needed by the internals layer
(``Main/internals/get_session.py``).  Keeping the builders in a neutral module
means the internals never have to import a plugin, so there is no
internals -> plugins dependency edge (and no chance of the plugin being
executed twice).

The layout is tuned for narrow phone screens: short labels, a fixed three
column grid, a compact pager that always highlights the *current* page and a
header that states which page is being shown.
"""

import telethon
from platform import python_version
from telethon import custom

from Main import Friday
from Main.core.decorators import log_errors
from Main.utils.ui_tokens import ADMIN, NAV, STATUS

# Longest plugin label rendered on a button – keeps the grid from wrapping.
MAX_LABEL = 16
# How many page numbers are visible at once.
PAGE_WINDOW = 5

help_text = f"""<b>📚 Friday Help Menu</b>
<b>Userbot:</b> <code>V{Friday.__version__}</code> · <b>Telethon:</b> <code>V{telethon.__version__}</code> · <b>Python:</b> <code>V{python_version()}</code>"""


def _truncate_label(text: str, limit: int = MAX_LABEL) -> str:
    """Shorten a button label so it stays readable on narrow screens."""
    clean = " ".join(str(text).split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].strip() + "…"


def _category_plugins(category: str):
    """Return the plugin names that belong to a help category."""
    main_plugins, loaded_plugins = Friday.get_plugins_by_category()
    all_plugins = sorted(list(Friday._command_help_message_data.keys()))

    if category == "main":
        return main_plugins
    if category == "loaded":
        return loaded_plugins
    return all_plugins


def _category_label(category: str) -> str:
    """Human readable name of a help category."""
    if category == "main":
        return "Main Plugins"
    if category == "loaded":
        return "Loaded Plugins"
    return "All Plugins"


@log_errors
async def get_help_page_info(category: str = "all", page: int = 0):
    """Return ``(total_pages, current_page, plugin_count)`` for a category."""
    rows = getattr(Friday.config, "HELP_MENU_ROWS", 6) or 6
    columns = getattr(Friday.config, "HELP_MENU_COLUMNS", 3) or 3
    plugins = _category_plugins(category)

    chunked = [plugins[i : i + columns] for i in range(0, len(plugins), columns)]
    pages = [chunked[i : i + rows] for i in range(0, len(chunked), rows)] or [[]]

    total_pages = len(pages)
    current = max(0, min(page, total_pages - 1))
    return total_pages, current, len(plugins)


@log_errors
async def get_help_header(category: str = "all", page: int = 0) -> str:
    """Build the page aware help header shown above the keyboard."""
    total_pages, current, plugin_count = await get_help_page_info(category, page)
    return (
        f"{help_text}\n"
        f"{'━' * 18}\n"
        f"📄 <b>Page {current + 1}</b> of <b>{total_pages}</b> · "
        f"🌐 <b>{_category_label(category)}</b> · <b>{plugin_count}</b> modules"
    )


@log_errors
async def get_help_menu(category: str = "all", page: int = 0):
    """Build the inline keyboard for the help menu."""
    main_plugins, loaded_plugins = Friday.get_plugins_by_category()
    all_plugins = sorted(list(Friday._command_help_message_data.keys()))

    if category == "main":
        target_plugins = main_plugins
    elif category == "loaded":
        target_plugins = loaded_plugins
    else:
        category = "all"
        target_plugins = all_plugins

    cat_tabs = [
        custom.Button.inline(
            f"• {ADMIN.PACKAGE} Main ({len(main_plugins)}) •"
            if category == "main"
            else f"{ADMIN.PACKAGE} Main ({len(main_plugins)})",
            b"help#_cat?cat=main&page=0",
        ),
        custom.Button.inline(
            f"• {ADMIN.PLUGIN} Loaded ({len(loaded_plugins)}) •"
            if category == "loaded"
            else f"{ADMIN.PLUGIN} Loaded ({len(loaded_plugins)})",
            b"help#_cat?cat=loaded&page=0",
        ),
        custom.Button.inline(
            f"• {ADMIN.WEB} All ({len(all_plugins)}) •" if category == "all" else f"{ADMIN.WEB} All",
            b"help#_cat?cat=all&page=0",
        ),
    ]

    rows = getattr(Friday.config, "HELP_MENU_ROWS", 6) or 6
    columns = getattr(Friday.config, "HELP_MENU_COLUMNS", 3) or 3
    chunked = [target_plugins[i : i + columns] for i in range(0, len(target_plugins), columns)]
    pages = [chunked[i : i + rows] for i in range(0, len(chunked), rows)] or [[]]

    total_pages = len(pages)
    page = max(0, min(page, total_pages - 1))
    current_grid = [
        [
            custom.Button.inline(
                f"{ADMIN.PACKAGE if Friday.get_plugin_category(p) == 'main' else ADMIN.PLUGIN} "
                f"{_truncate_label(p.replace('_', ' ').title())}",
                f"help#{p}?cat={category}&page={page}".encode("utf-8"),
            )
            for p in row
        ]
        for row in pages[page]
    ]

    # Category switcher always sits on top of the grid.
    current_grid.insert(0, cat_tabs)

    # Compact pager – the active page is highlighted with the correct number.
    if total_pages > 1:
        start = max(0, min(page - (PAGE_WINDOW // 2), total_pages - PAGE_WINDOW))
        window = list(range(start, min(start + PAGE_WINDOW, total_pages)))

        page_buttons = []
        if page > 0:
            page_buttons.append(custom.Button.inline("◀", f"help#_page?cat={category}&page={page - 1}".encode("utf-8")))
        for index in window:
            label = f"» {index + 1} «" if index == page else str(index + 1)
            page_buttons.append(custom.Button.inline(label, f"help#_page?cat={category}&page={index}".encode("utf-8")))
        if page < total_pages - 1:
            page_buttons.append(custom.Button.inline("▶", f"help#_page?cat={category}&page={page + 1}".encode("utf-8")))

        current_grid.append(page_buttons)

    # Control buttons & close
    current_grid.append(
        [
            custom.Button.inline(f"{NAV.HOME_ICON} Main Menu", b"bot_start_menu"),
            custom.Button.inline(f"{STATUS.GEAR} Settings", b"panel_refresh"),
            custom.Button.inline(NAV.CLOSE, b"close_help"),
        ]
    )
    return current_grid


@log_errors
async def get_plugin_data(plugin: str, page: int = 0, category: str = "all"):
    p_name = plugin.lower()
    cat = Friday.get_plugin_category(p_name)
    badge = f"{ADMIN.PACKAGE} Core / Main Plugin" if cat == "main" else f"{ADMIN.PLUGIN} Loaded / Extra Plugin"
    text = (
        f"<b>📘 {p_name.replace('_', ' ').title()}</b>  <i>[{badge}]</i>\n"
        f"{'━' * 18}\n"
        f"{Friday._command_help_message_data[p_name].strip()}"
    )
    buttons = [
        [
            custom.Button.inline(NAV.BACK, f"help#_page?cat={category}&page={page}".encode("utf-8")),
            custom.Button.inline(f"{NAV.HOME_ICON} Main Menu", b"bot_start_menu"),
        ]
    ]
    return text, buttons
