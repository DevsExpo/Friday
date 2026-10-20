# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

"""Shared help-menu builders.

The bot plugin (``Main/plugins/bot/help.py``) owns the inline/callback handlers,
but the menu *builders* are also needed by the internals layer
(``Main/internals/get_session.py``).  Keeping the builders in a neutral module
means the internals never have to import a plugin, so there is no
internals -> plugins dependency edge (and no chance of the plugin being
executed twice).
"""

import telethon
from platform import python_version
from telethon import custom

from Main import Friday
from Main.core.decorators import log_errors
from Main.utils.ui_tokens import ADMIN, NAV, STATUS

help_text = f"""<b><u>Friday Help Menu</u></b>
<b>Userbot version:</b> <code>V{Friday.__version__}</code>
<b>Telethon version:</b> <code>V{telethon.__version__}</code>
<b>Python version:</b> <code>V{python_version()}</code>"""


@log_errors
async def get_help_menu(category: str = "all", page: int = 0):
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

    ikb = [
        custom.Button.inline(
            f"{ADMIN.PACKAGE if Friday.get_plugin_category(p) == 'main' else ADMIN.PLUGIN} {p.replace('_', ' ').title()}",
            f"help#{p}?cat={category}&page={page}".encode("utf-8"),
        )
        for p in target_plugins
    ]

    rows = getattr(Friday.config, "HELP_MENU_ROWS", 6) or 6
    columns = getattr(Friday.config, "HELP_MENU_COLUMNS", 3) or 3
    chunked = [ikb[i : i + columns] for i in range(0, len(ikb), columns)]
    pages = [chunked[i : i + rows] for i in range(0, len(chunked), rows)]

    if not pages:
        pages = [[]]

    page = max(0, min(page, len(pages) - 1))
    current_grid = list(pages[page])

    # Insert category switcher as the first row
    current_grid.insert(0, cat_tabs)

    # Append pagination if multiple pages
    if len(pages) > 1:
        page_buttons = [
            custom.Button.inline(
                f"> {i + 1} <" if i + 1 == page else str(i + 1),
                f"help#_page?cat={category}&page={i}".encode("utf-8"),
            )
            for i in range(len(pages))
        ]
        if len(page_buttons) > 6:
            start_idx = max(0, min(page - 2, len(page_buttons) - 5))
            page_buttons = page_buttons[start_idx : start_idx + 5]
        current_grid.append(page_buttons)

    # Append Control buttons & Close
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
        f"<b>Help for</b> <code>{p_name}</code>  <i>[{badge}]</i>\n\n"
        f"{Friday._command_help_message_data[p_name].strip()}"
    )
    buttons = [
        [
            custom.Button.inline(NAV.BACK, f"help#_page?cat={category}&page={page}".encode("utf-8")),
            custom.Button.inline(f"{NAV.HOME_ICON} Main Menu", b"bot_start_menu"),
        ]
    ]
    return text, buttons
