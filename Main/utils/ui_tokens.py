# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
#
# Centralized UI & Emoji Tokens for Core (Main) Friday Components.
# Keeps Main styling consistent, customizable, and segregated from external plugins.

from types import SimpleNamespace

# Core Status & Feedback Tokens
STATUS = SimpleNamespace(
    SUCCESS="✅",
    ERROR="❌",
    WARNING="⚠️",
    INFO="ℹ️",
    PROCESSING="⚡",
    PING="🏓",
    GEAR="⚙️",
    LOCK="🔒",
    KEY="🔐",
    SHIELD="🛡️",
    DENIED="⛔",
    BULLET="•",
    ARROW="➔",
    STAR="🌟",
    CHECK="✓",
    CROSS="✖",
    FIRE="🔥",
    HEART="❤️",
    THUMB_UP="👍",
    WAIT="⏳",
    CLEAN="🧹",
    DOCTOR="🩺",
    LINK="🔗",
    PIN="📌",
    FORBIDDEN="🚫",
    GRIN="😁",
)

# Visual Indicators (Badges & Toggles)
INDICATOR = SimpleNamespace(
    GREEN="🟢",
    RED="🔴",
    YELLOW="🟡",
    WHITE="⚪",
    OFF="⚫",
)

# Core Management, Administration & Asset Tokens
ADMIN = SimpleNamespace(
    OWNER="👑",
    SUDO="⚡",
    USER="👤",
    USERS="👥",
    BOT="🤖",
    PACKAGE="📦",
    RELOAD="🔄",
    METRICS="📊",
    SEARCH="🔍",
    TRASH="🗑️",
    WRENCH="🔧",
    FOLDER="🗂️",
    DRAWER="🗄️",
    DOC="📄",
    CONTACT="📇",
    NOTE="📝",
    MAIL="📬",
    CHAT="💬",
    BROADCAST="📢",
    DOOR="🚪",
    BELL="🔔",
    BELL_OFF="🔕",
    NSFW="🔞",
    BIRTHDAY="🎂",
    NUMBER="🔢",
    PLUGIN="🧩",
    WEB="🌐",
    BOOK="📖",
    LAMP="💡",
    HOME="🏠",
    PLUS="➕",
)

# Button & Navigation Controls
NAV = SimpleNamespace(
    PREV="◀ Prev",
    NEXT="Next ▶",
    BACK="🔙 Back",
    CLOSE="❌ Close",
    REFRESH="🔄 Refresh",
    HOME="🏠 Home",
    ADD="➕ Add",
    BACK_ICON="🔙",
    CLOSE_ICON="✖",
    REFRESH_ICON="🔄",
    HOME_ICON="🏠",
    ADD_ICON="➕",
)

# Seamlessly respect root style.py overrides if customized by user
try:
    import style

    if hasattr(style, "ping_format") and isinstance(style.ping_format, dict):
        STATUS.PING = style.ping_format.get("ping_emoji1", STATUS.PING)
        STATUS.GEAR = style.ping_format.get("ping_emoji2", STATUS.GEAR)
    if hasattr(style, "bullets") and isinstance(style.bullets, dict):
        STATUS.BULLET = style.bullets.get("bullet2", STATUS.BULLET)
except Exception:
    pass
