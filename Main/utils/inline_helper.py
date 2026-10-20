# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

import asyncio
import logging
from contextlib import suppress
from typing import Optional, Any
from telethon import errors, types
from Main import Friday

logger = logging.getLogger("friday.inline")


def is_inline_available() -> bool:
    """Check if the assistant bot is online, configured, and capable of inline queries."""
    if not getattr(Friday, "bot_info", None) or not getattr(Friday, "bot", None):
        return False
    username = getattr(Friday.bot_info, "username", None)
    return bool(username and isinstance(username, str))


async def send_inline_widget(c: Any, m: Any, query: str) -> bool:
    """
    Attempt to send an interactive inline bot widget to the current chat.
    Returns True if successfully sent, False if inline is unavailable or failed.
    """
    if not is_inline_available():
        return False

    bot_username = getattr(Friday.bot_info, "username", None)
    if not bot_username or not isinstance(bot_username, str):
        return False

    chat_id = getattr(m, "chat_id", None) or getattr(getattr(m, "chat", None), "id", None)
    if not chat_id:
        return False

    try:
        results = await c.get_inline_bot_results(bot_username, query)
        if results and isinstance(results, (list, tuple)) and len(results) > 0:
            rm = getattr(m, "reply_to_message", None)
            reply_to = rm.id if rm else m.id
            await results[0].click(chat_id, reply_to=reply_to)
            with suppress(Exception):
                await m.delete_if_self()
            return True
    except errors.BotInlineDisabledError:
        try:
            from Main.internals.set_inline import set_inline_in_botfather

            logger.info(f"Inline mode disabled on @{bot_username}. Attempting auto-enable via @BotFather...")
            await set_inline_in_botfather(c)
            await asyncio.sleep(1)
            results = await c.get_inline_bot_results(bot_username, query)
            if results and isinstance(results, (list, tuple)) and len(results) > 0:
                rm = getattr(m, "reply_to_message", None)
                reply_to = rm.id if rm else m.id
                await results[0].click(chat_id, reply_to=reply_to)
                with suppress(Exception):
                    await m.delete_if_self()
                return True
        except Exception as exc:
            logger.warning(f"Auto-enabling inline on @BotFather failed: {exc}")
            return False
    except Exception as e:
        logger.debug(f"Inline widget invocation for '{query}' failed: {e}")
        return False

    return False


def is_owner(sender_id: Optional[int]) -> bool:
    """Single source of truth: delegates to Friday._resolve_is_owner.

    All callers (control panel, FPM inline, sudo inline, PM-security inline,
    devtools) use this function so the definition stays in one place.
    Friday._resolve_is_owner already suppresses TypeError/ValueError from a
    non-numeric OWNER_ID string, so no extra guard is needed here.
    """
    if not sender_id:
        return False
    resolver = getattr(Friday, "_resolve_is_owner", None)
    if callable(resolver):
        return resolver(sender_id)
    # Fallback during early startup before FridayClient is fully initialised
    owner_id = getattr(getattr(Friday, "config", None), "OWNER_ID", None)
    try:
        if owner_id and int(sender_id) == int(owner_id):
            return True
    except (TypeError, ValueError):
        pass
    for acc in getattr(Friday, "ourselves", []) or []:
        if getattr(acc, "id", None) == sender_id:
            return True
    for cl in getattr(Friday, "clients", []) or []:
        if getattr(getattr(cl, "myself", None), "id", None) == sender_id:
            return True
    return False


def is_sudo(sender_id: Optional[int]) -> bool:
    """Verify if the sender_id belongs to the sudo (trusted user) tier."""
    if not sender_id:
        return False
    sudo_users = getattr(Friday.config, "SUDO_USERS", []) or []
    try:
        return int(sender_id) in {int(u) for u in sudo_users}
    except (TypeError, ValueError):
        return sender_id in sudo_users

def is_owner_cb(cq: Any) -> bool:
    """Verify that the clicking user is strictly the owner (not sudo or stranger)."""
    sender_id = getattr(cq, "sender_id", 0)
    return is_owner(sender_id)


def is_authorized_cb(cq: Any, allowed_user_id: Optional[int] = None) -> bool:
    """Verify that the clicking user has permission to interact with this control widget."""
    sender_id = getattr(cq, "sender_id", 0)
    if allowed_user_id and sender_id == allowed_user_id:
        return True

    if is_owner(sender_id):
        return True

    sudo_users = getattr(Friday.config, "SUDO_USERS", []) or []
    if sender_id in sudo_users:
        return True

    return False


class contextlib_suppress:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return True
