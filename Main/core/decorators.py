# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

from __future__ import annotations

import logging
import traceback
import contextlib
from functools import wraps
from typing import Any, Callable, List, Union

from telethon import errors, events
from telethon.events import StopPropagation

logger = logging.getLogger("friday.decorators")


def inline_check(func: Callable) -> Callable:
    """Auto-enable inline mode in BotFather if it's disabled, then retry."""

    @wraps(func)
    async def wrapper(c: Any, m: Any, *args, **kwargs) -> Any:
        if getattr(wrapper, "_retried", False):
            # Already retried once this invocation — run unconditionally to avoid loops.
            return await func(c, m, *args, **kwargs)
        try:
            return await func(c, m, *args, **kwargs)
        except (errors.ChatSendInlineForbiddenError, errors.BotInlineDisabledError):
            from Main.internals.set_inline import set_inline_in_botfather

            status = await m.handle_message("INLINE_DISABLED")
            await set_inline_in_botfather(c)
            if status:
                with contextlib.suppress(Exception):
                    await status.delete()
            wrapper._retried = True
            result = await func(c, m, *args, **kwargs)
            wrapper._retried = False
            return result

    wrapper._retried = False
    return wrapper


def check_perm(perm_type: Union[str, List[str]], return_perm: bool = False) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(client: Any, m: Any, *args, **kwargs) -> Any:
            chat_type = getattr(m.chat, "type", "")
            if chat_type in {"private", "bot"}:
                return await func(client, m, *args, **kwargs)

            if isinstance(perm_type, list):
                perms_map = {}
                for p in perm_type:
                    has_perm, _ = await client.check_my_perm(m, p)
                    perms_map[p] = has_perm
                if all(val for val in perms_map.values()):
                    return await func(client, m, *args, **kwargs)
                failed_perms = " ".join([p for p, ok in perms_map.items() if not ok])
                return await m.handle_message("ADMIN_ACTION_FAILED", string_args=(failed_perms,))
            else:
                has_perm, perm_dict = await client.check_my_perm(m, perm_type)
                if has_perm:
                    if return_perm:
                        return await func(client, m, perm_dict, *args, **kwargs)
                    return await func(client, m, *args, **kwargs)
                return await m.handle_message("ADMIN_ACTION_FAILED", string_args=(perm_type,))

        return wrapper

    return decorator


def iuser_check(func: Callable) -> Callable:
    """Allow only authorized users to execute callback or inline query."""

    @wraps(func)
    async def wrapper(client: Any, update: Any, *args, **kwargs) -> Any:
        # Lazy import avoids circular-import issues while keeping the reference
        # cheap after the first call (module is cached in sys.modules).
        import Main as _main_module

        users = _main_module.Friday.auth_users
        sender_id = getattr(update, "sender_id", None)
        if sender_id is None and hasattr(update, "from_user") and update.from_user:
            sender_id = getattr(update.from_user, "id", None)

        if sender_id in users:
            try:
                return await func(client, update, *args, **kwargs)
            except errors.MessageNotModifiedError:
                if hasattr(update, "answer"):
                    await update.answer("🤔🧐😳🙄😬")
        elif isinstance(update, events.CallbackQuery.Event) or hasattr(update, "data"):
            if hasattr(update, "answer"):
                await update.answer(
                    "You are not authorized to use me.",
                    alert=True,
                )
        elif isinstance(update, events.InlineQuery.Event) or hasattr(update, "builder"):
            if hasattr(update, "answer"):
                await update.answer(
                    [],
                    cache_time=0,
                    private=True,
                    switch_pm="You are not authorized to use me.",
                    switch_pm_param="auth",
                )

    return wrapper


def log_errors(func: Callable) -> Callable:
    """Log exceptions and report to log chat or owner."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except StopPropagation:
            raise
        except (
            errors.MessageNotModifiedError,
            errors.MessageIdInvalidError,
            errors.UserNotParticipantError,
            errors.MessageEmptyError,
        ):
            pass
        except Exception as exc:
            import Main

            friday = Main.Friday
            tb = traceback.format_exc()
            logger.error(f"Error in {func.__name__}: {exc}\n{tb}")
            target_chat = friday.log_chat or getattr(friday.config, "OWNER_ID", None)
            if target_chat and hasattr(friday, "bot") and friday.bot:
                try:
                    await friday.bot.send_message(
                        target_chat,
                        f"<b>AN ERROR OCCURRED:</b>\n"
                        f"Exception: <i>{exc}</i>\n"
                        f"Occurred in: <code>{func.__name__}</code>\n\n"
                        f"<pre>{tb}</pre>",
                        parse_mode="html",
                    )
                except Exception:
                    pass

    return wrapper
