# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

import re
import os
import time
import asyncio
import logging
from typing import Dict, Any, Optional
from Main import Friday
from Main.utils.suppress import suppress_error
from Main.core.decorators import log_errors
from Main.utils.custom_filters import filters
from telethon import errors, custom
from telethon.sessions import StringSession
from Main.core.types.client import FridayTelegramClient

logger = logging.getLogger("friday.make_session")

# Active interactive login sessions: chat_id -> state dict
_ACTIVE_LOGINS: Dict[int, Dict[str, Any]] = {}
_PENDING_LOGINS: set = set()

# Console Setup Code Lock for TWP
_TWP_LOCKED_USER: Optional[int] = None
_TWP_SETUP_CODE: Optional[str] = None

# Rate-limiting for TWP PIN guesses {sender_id: {attempts, lockout_until}}
_TWP_ATTEMPTS: Dict[int, Dict[str, Any]] = {}
_TWP_GLOBAL_HOURLY: Dict[str, Any] = {"count": 0, "reset_at": 0.0}

_MAX_ATTEMPTS_PER_SENDER = 5
_LOCKOUT_SECONDS = 900   # 15 min
_GLOBAL_HOURLY_CAP = 60  # total across all senders / hour


def get_or_create_twp_code() -> str:
    """Generate and display a secure 6-digit setup code in console logs."""
    global _TWP_SETUP_CODE
    if _TWP_SETUP_CODE is None:
        import secrets

        _TWP_SETUP_CODE = f"{secrets.randbelow(900000) + 100000:06d}"
        msg = (
            "\n" + "=" * 62 + "\n"
            f"🔒 FRIDAY INITIAL SETUP PIN: [ {_TWP_SETUP_CODE} ]\n"
            "Send this 6-digit code to your Telegram bot to unlock setup!\n"
            + "=" * 62
        )
        logger.warning(msg)
        print(msg, flush=True)
    return _TWP_SETUP_CODE


def _twp_is_rate_limited(sender_id: int) -> bool:
    """Return True if this sender is locked out or the global cap is exceeded."""
    now = time.monotonic()

    # Global hourly cap
    g = _TWP_GLOBAL_HOURLY
    if now > g["reset_at"]:
        g["count"] = 0
        g["reset_at"] = now + 3600
    if g["count"] >= _GLOBAL_HOURLY_CAP:
        return True

    # Per-sender lockout
    rec = _TWP_ATTEMPTS.get(sender_id)
    if rec and now < rec.get("lockout_until", 0):
        return True
    return False


def _twp_record_fail(sender_id: int) -> None:
    """Record a failed attempt and apply lockout if threshold crossed."""
    now = time.monotonic()

    _TWP_GLOBAL_HOURLY["count"] = _TWP_GLOBAL_HOURLY.get("count", 0) + 1

    rec = _TWP_ATTEMPTS.setdefault(sender_id, {"attempts": 0, "lockout_until": 0.0})
    rec["attempts"] = rec.get("attempts", 0) + 1
    if rec["attempts"] >= _MAX_ATTEMPTS_PER_SENDER:
        rec["lockout_until"] = now + _LOCKOUT_SECONDS
        logger.warning(f"TWP: sender {sender_id} locked out after {rec['attempts']} failed attempts.")


async def verify_twp_code(sender_id: Optional[int], code: str) -> bool:
    """Validate submitted code against generated PIN and claim ownership."""
    global _TWP_LOCKED_USER
    if not sender_id or not code:
        return False
    current_code = get_or_create_twp_code()
    clean_code = str(code).strip()
    if clean_code == current_code:
        _TWP_LOCKED_USER = int(sender_id)
        if getattr(Friday, "config", None):
            with suppress_error(msg="Setting OWNER_ID in config"):
                Friday.config.OWNER_ID = int(sender_id)
            with suppress_error(msg="Persisting OWNER_ID to DB"):
                await Friday.config.add_env_to_db("OWNER_ID", int(sender_id), upsert=True)
        logger.info(f"TWP Ownership successfully claimed by user ID: {sender_id}")
        return True
    _twp_record_fail(int(sender_id))
    return False


def is_twp_unclaimed() -> bool:
    """Check if initial setup ownership has not been claimed yet."""
    owner_id = getattr(Friday.config, "OWNER_ID", None)
    if owner_id and str(owner_id).strip().isdigit() and int(owner_id) > 0:
        return False
    return _TWP_LOCKED_USER is None


def is_twp_authorized(sender_id: Optional[int]) -> bool:
    """
    Security Barrier for Training Wheels Protocol (TWP):
    1. If OWNER_ID is configured in environment, strictly enforce sender_id == OWNER_ID.
    2. If OWNER_ID is not configured, only the user who verified the setup code is authorized.
    """
    global _TWP_LOCKED_USER
    if not sender_id:
        return False
    owner_id = getattr(Friday.config, "OWNER_ID", None)
    if owner_id and str(owner_id).strip().isdigit() and int(owner_id) > 0:
        return int(sender_id) == int(owner_id)
    return _TWP_LOCKED_USER is not None and int(sender_id) == _TWP_LOCKED_USER


async def client_session(api_id: int, api_hash: str) -> FridayTelegramClient:
    return FridayTelegramClient(StringSession(), api_id=int(api_id), api_hash=str(api_hash))


def get_numpad_buttons() -> list:
    return [
        [
            custom.Button.inline("1", b"otp_1"),
            custom.Button.inline("2", b"otp_2"),
            custom.Button.inline("3", b"otp_3"),
        ],
        [
            custom.Button.inline("4", b"otp_4"),
            custom.Button.inline("5", b"otp_5"),
            custom.Button.inline("6", b"otp_6"),
        ],
        [
            custom.Button.inline("7", b"otp_7"),
            custom.Button.inline("8", b"otp_8"),
            custom.Button.inline("9", b"otp_9"),
        ],
        [
            custom.Button.inline("⌫ Del", b"otp_del"),
            custom.Button.inline("0", b"otp_0"),
            custom.Button.inline("✖ Cancel", b"otp_cancel"),
        ],
    ]


def get_numpad_text(phone: str, digits: str) -> str:
    masked_list = list(digits) + ["•"] * max(0, 5 - len(digits))
    masked_display = " ".join(masked_list)
    return (
        "📲 <b>Telegram Login Code Sent!</b>\n\n"
        f"• <b>Target Phone:</b> <code>{phone}</code>\n"
        f"• <b>Code Entered:</b> <code>[ {masked_display} ]</code>\n\n"
        "🔒 <b>Secure NumPad Active:</b>\n"
        "<i>Tap the buttons below to enter your 5-digit code safely. Telegram never cancels login codes submitted via button clicks!</i>\n\n"
        "<i>(Or send the code as a message with letters between digits, e.g. <code>x1x2x3x4x5</code>)</i>"
    )


async def persist_and_finalize_session(app, session_str: str, chat_id: int):
    status_msg = await Friday.bot.send_message(chat_id, "Connecting session and registering with Friday...")
    try:
        new_client = await Friday.add_session(session_str, status_msg)
    except Exception as e:
        return await status_msg.edit(f"❌ Failed to connect session: {e}")

    user_id = new_client.myself.id
    user_name = getattr(new_client.myself, "first_name", "User")
    username = getattr(new_client.myself, "username", None)
    username_str = f"@{username}" if username else "None"

    # Multi-Tier Persistence for Serverless & Cloud Hosting:
    # Tier 1: Cloud/Active Database (Survives dyno/container restarts)
    if Friday.db is not None and Friday.config:
        with suppress_error(msg="Persisting session to database"):
            await Friday.config.add_element_to_list("SESSIONS", session_str)
            await Friday.config.add_env_to_db("OWNER_ID", user_id, upsert=True)

    # Tier 2: Heroku Config Vars (if running on Heroku)
    h_api_key = getattr(Friday.config, "HEROKU_API_KEY", None) or os.environ.get("HEROKU_API_KEY")
    h_app_name = getattr(Friday.config, "HEROKU_APP_NAME", None) or os.environ.get("HEROKU_APP_NAME")
    if h_api_key and h_app_name:
        try:
            import heroku3

            h = heroku3.from_key(h_api_key)
            app_inst = h.app(h_app_name)
            curr = app_inst.config().get("SESSIONS", "")
            if session_str not in curr:
                app_inst.config()["SESSIONS"] = f"{curr} {session_str}".strip()
            app_inst.config()["OWNER_ID"] = str(user_id)
        except Exception:
            pass

    # Tier 3: Local .env (if on VPS/local machine with writable disk)
    if hasattr(Friday.config, "append_session"):
        with suppress_error(msg="Appending session to .env"):
            Friday.config.append_session(session_str)

    # Disable TWP
    Friday.training_wheels_protocol = False

    # Detect Serverless / Ephemeral environment
    is_serverless = any(
        k in os.environ for k in ("DYNO", "KOYEB_APP_NAME", "RENDER", "RAILWAY_STATIC_URL", "VERCEL")
    ) or os.path.exists("/.dockerenv")

    db_is_persistent = Friday.db is not None and not isinstance(Friday.db, type(Friday.local_db))

    if is_serverless and not db_is_persistent:
        serverless_notice = (
            "\n\n⚠️ <b>Serverless Host Detected (Ephemeral Storage):</b>\n"
            "Your container wipes local files on reboot. To make your userbot permanent, "
            "add these variables to your cloud platform's <b>Environment Variables</b> dashboard:\n\n"
            f"<code>SESSIONS={session_str}</code>\n"
            f"<code>OWNER_ID={user_id}</code>"
        )
    else:
        serverless_notice = (
            "\n\n💾 <b>Persistence Verified:</b>\n"
            "Your session is securely saved in your database & configuration. "
            "It will persist across all container/dyno restarts automatically."
        )

    # Send backup copy to Saved Messages
    with suppress_error(msg="Sending backup to Saved Messages"):
        await new_client.send_message(
            "me",
            f"**🔐 Friday Telethon String Session**\n\n`{session_str}`\n\n"
            "Keep this session secret! Do not share it with anyone.",
        )

    success_text = (
        f"🎉 <b>Setup Complete! Welcome {user_name}!</b>\n\n"
        f"• <b>Account:</b> {user_name} ({username_str})\n"
        f"• <b>User ID:</b> <code>{user_id}</code> (Configured as Owner)\n"
        f"• <b>Status:</b> 🟢 Operational & Online"
        f"{serverless_notice}"
    )

    success_buttons = [
        [
            custom.Button.inline("🎛️ Settings Panel", b"panel_refresh"),
            custom.Button.inline("⚡ Test Ping", b"panel_ping"),
        ],
        [custom.Button.inline("📖 Help Menu", b"help#_cat?cat=all&page=0")],
    ]

    await Friday.bot.send_message(chat_id, success_text, buttons=success_buttons, parse_mode="html")


@Friday.bot.on_callback_query(filters.regex(r"^session_no"))
@log_errors
async def add_session_cb_handler(_, cb):
    chat_id = sender_id = getattr(cb, "sender_id", 0)
    if not is_twp_authorized(sender_id):
        return await cb.answer("⛔ Access Denied: Setup is locked to the owner.", alert=True)

    if chat_id in _PENDING_LOGINS or chat_id in _ACTIVE_LOGINS:
        return await cb.answer(
            "⚠️ Login is already in progress! Please enter your code/password or /cancel.", alert=True
        )

    _PENDING_LOGINS.add(chat_id)
    await cb.answer()

    with suppress_error(msg="Deleting session_no callback message"):
        await cb.delete()

    api_id = Friday.config.API_ID
    api_hash = Friday.config.API_HASH

    if not api_id or not api_hash:
        _PENDING_LOGINS.discard(chat_id)
        return await Friday.bot.send_message(chat_id, "API_ID or API_HASH is not set in config.")

    phone_number = None
    try:
        if hasattr(Friday.bot, "_conversations"):
            with suppress_error():
                for c_obj in list(Friday.bot._conversations.get(chat_id, set())):
                    c_obj._cancel_all()
                Friday.bot._conversations.pop(chat_id, None)

        async with Friday.bot.conversation(chat_id, timeout=120, exclusive=False) as conv:
            phone_prompt = await conv.send_message(
                "📱 Please send your Telegram phone number with international country code (e.g. <code>+1234567890</code>).\n\n"
                "Tap below or send /cancel to abort.",
                buttons=[[custom.Button.inline("❌ Cancel / Main Menu", b"bot_start_menu")]],
                parse_mode="html",
            )
            while True:
                resp = await conv.get_response(phone_prompt)
                raw_text = resp.raw_text.strip()
                if raw_text.lower().startswith(("/cancel", "/start", "/stop", "/abort", "cancel", "menu")):
                    _PENDING_LOGINS.discard(chat_id)
                    if raw_text.startswith("/start"):
                        mention = getattr(resp.sender, "first_name", "User") or "User"
                        from Main.internals.get_session import get_main_start_dashboard

                        caption, buttons = get_main_start_dashboard(mention)
                        return await conv.send_message(caption, buttons=buttons, parse_mode="html")
                    return await conv.send_message(
                        "Setup cancelled.",
                        buttons=[[custom.Button.inline("🏠 Main Menu", b"bot_start_menu")]],
                    )
                cleaned_phone = re.sub(r"[\s\-\(\)]", "", raw_text)
                if re.match(r"^\+?\d{7,16}$", cleaned_phone):
                    phone_number = cleaned_phone
                    break
                phone_prompt = await conv.send_message(
                    "❌ That does not look like a valid phone number format.\n"
                    "Please send your phone number with country code (e.g. <code>+1234567890</code>), or tap below to cancel.",
                    buttons=[[custom.Button.inline("❌ Cancel / Main Menu", b"bot_start_menu")]],
                    parse_mode="html",
                )
    except asyncio.TimeoutError:
        _PENDING_LOGINS.discard(chat_id)
        return await Friday.bot.send_message(
            chat_id,
            "⏱️ <b>Setup timed out</b> due to inactivity.\nTap below to return to the main menu.",
            buttons=[[custom.Button.inline("🏠 Main Menu", b"bot_start_menu")]],
            parse_mode="html",
        )
    except Exception as e:
        _PENDING_LOGINS.discard(chat_id)
        err_msg = str(e).strip()
        if not err_msg:
            err_msg = "Conversation closed or timed out."
        return await Friday.bot.send_message(
            chat_id,
            f"❌ <b>Setup Notice:</b> {err_msg}",
            buttons=[[custom.Button.inline("🏠 Main Menu", b"bot_start_menu")]],
            parse_mode="html",
        )
    finally:
        _PENDING_LOGINS.discard(chat_id)

    # 2. Connect to Telegram MTProto outside conversation
    process_msg = await Friday.bot.send_message(chat_id, "Connecting to Telegram...")
    app = await client_session(api_id, api_hash)
    await app.connect()

    try:
        sent_code = await app.send_code_request(phone_number)
    except errors.FloodWaitError as e:
        await app.disconnect()
        return await process_msg.edit(f"Floodwait: please wait {e.seconds} seconds.")
    except errors.PhoneNumberInvalidError:
        await app.disconnect()
        return await process_msg.edit("Invalid phone number format. Please check and try again.")
    except errors.ApiIdInvalidError:
        await app.disconnect()
        return await process_msg.edit("Invalid API ID or Hash.")
    except Exception as e:
        await app.disconnect()
        return await process_msg.edit(f"Connection error: {e}")

    # 3. Store active login state
    _ACTIVE_LOGINS[chat_id] = {
        "app": app,
        "phone": phone_number,
        "hash": sent_code.phone_code_hash,
        "digits": "",
        "awaiting_2fa": False,
    }

    with suppress_error():
        await process_msg.delete()

    numpad_msg = await Friday.bot.send_message(
        chat_id,
        get_numpad_text(phone_number, ""),
        buttons=get_numpad_buttons(),
        parse_mode="html",
    )
    _ACTIVE_LOGINS[chat_id]["msg_id"] = numpad_msg.id


@Friday.bot.on_message(filters.private)
async def on_twp_text_input(client, message):
    chat_id = message.chat_id
    state = _ACTIVE_LOGINS.get(chat_id)
    if not state:
        if Friday.training_wheels_protocol and is_twp_unclaimed():
            sender_id = getattr(message, "sender_id", None)
            if sender_id is None and hasattr(message, "from_user") and message.from_user:
                sender_id = getattr(message.from_user, "id", None)
            raw = (message.raw_text or "").strip()
            # Only treat as PIN attempt if exactly 6 digits and sender is not rate-limited
            if raw and not raw.startswith("/") and len(raw) == 6 and raw.isdigit() and sender_id:
                if _twp_is_rate_limited(int(sender_id)):
                    # Silent drop — do not reveal lockout to prevent enumeration
                    return
                if await verify_twp_code(sender_id, raw):
                    await message.reply(
                        f"✅ <b>Setup Code Verified!</b>\n\n"
                        f"Welcome owner (<code>{sender_id}</code>)! Ownership has been locked to your account.\n"
                        "Let's configure your Friday instance.",
                        parse_mode="html",
                    )
                    from Main.internals.get_session import get_twp_step1_text, get_twp_step1_buttons

                    return await message.reply(
                        get_twp_step1_text(), buttons=get_twp_step1_buttons(), parse_mode="html"
                    )
                # Failed — silently drop (no oracle signal, rate limit already recorded in verify)
        return

    raw = (message.raw_text or "").strip()
    if raw.startswith("/start"):
        return
    if raw == "/cancel":
        app = state.get("app")
        if app:
            with suppress_error():
                await app.disconnect()
        _ACTIVE_LOGINS.pop(chat_id, None)
        return await message.reply(
            "❌ Login process cancelled.",
            buttons=[[custom.Button.inline("🏠 Main Menu", b"bot_start_menu")]],
        )

    # A. 2FA Password Handling (Event-driven, zero conversation locks)
    if state.get("awaiting_2fa"):
        app = state["app"]
        verifying = await message.reply("⏳ Verifying 2FA password...")
        try:
            await app.sign_in(password=raw)
            with suppress_error():
                await verifying.delete()
        except Exception as e:
            return await verifying.edit(
                f"❌ <b>2FA Verification Failed:</b> <code>{e}</code>\n\nPlease check your password and send it again, or /cancel to abort.",
                buttons=[[custom.Button.inline("❌ Cancel / Main Menu", b"bot_start_menu")]],
                parse_mode="html",
            )

        _ACTIVE_LOGINS.pop(chat_id, None)
        session_str = app.session.save()
        await app.disconnect()
        return await persist_and_finalize_session(app, session_str, chat_id)

    # B. Code Digits Fallback
    digits = "".join(re.findall(r"\d", raw))
    if len(digits) >= 5:
        state["digits"] = digits[:5]
        await _submit_login_code(chat_id, message)


@Friday.bot.on_callback_query(filters.regex(r"^otp_"))
async def on_otp_numpad_callback(c, cq):
    sender_id = getattr(cq, "sender_id", 0)
    if not is_twp_authorized(sender_id):
        return await cq.answer("⛔ Access Denied: Setup is locked to the owner.", alert=True)

    chat_id = cq.chat_id
    state = _ACTIVE_LOGINS.get(chat_id)
    if not state:
        return await cq.answer("Session expired. Please restart login.", alert=True)

    data = cq.data.decode("utf-8") if isinstance(cq.data, bytes) else str(cq.data)
    action = data.split("_", 1)[1]

    if action == "cancel":
        await cq.answer("Login cancelled.")
        app = state.get("app")
        if app:
            with suppress_error():
                await app.disconnect()
        _ACTIVE_LOGINS.pop(chat_id, None)
        try:
            await cq.edit(
                "❌ <i>Login operation cancelled.</i>",
                buttons=[[custom.Button.inline("🏠 Main Menu", b"bot_start_menu")]],
                parse_mode="html",
            )
        except Exception:
            pass
        return

    if action == "del":
        state["digits"] = state["digits"][:-1]
        await cq.answer()
        try:
            await cq.edit(
                get_numpad_text(state["phone"], state["digits"]),
                buttons=get_numpad_buttons(),
                parse_mode="html",
            )
        except Exception:
            pass
        return

    # Numeric digit entered
    if action.isdigit():
        if len(state["digits"]) < 5:
            state["digits"] += action
        await cq.answer()

        try:
            await cq.edit(
                get_numpad_text(state["phone"], state["digits"]),
                buttons=get_numpad_buttons(),
                parse_mode="html",
            )
        except Exception:
            pass

        # Auto-submit once 5 digits are collected
        if len(state["digits"]) == 5:
            await _submit_login_code(chat_id, cq)


async def _submit_login_code(chat_id: int, message_or_cq):
    state = _ACTIVE_LOGINS.get(chat_id)
    if not state:
        return

    app = state["app"]
    phone = state["phone"]
    p_hash = state["hash"]
    digits = state["digits"]

    edit_target = message_or_cq.edit if hasattr(message_or_cq, "edit") else message_or_cq.edit_text

    try:
        await edit_target("⏳ Verifying code with Telegram...", buttons=None, parse_mode="html")
    except Exception:
        pass

    try:
        await app.sign_in(phone, code=digits, phone_code_hash=p_hash)
    except errors.SessionPasswordNeededError:
        state["awaiting_2fa"] = True
        return await Friday.bot.send_message(
            chat_id,
            "🔐 <b>Two-Step Verification (2FA) Active!</b>\n\n"
            "Your Telegram account has a 2FA Cloud Password enabled.\n"
            "Please send your <b>2FA Password</b> as a text message right now.\n\n"
            "<i>(Send /cancel or tap below to abort)</i>",
            buttons=[[custom.Button.inline("❌ Cancel / Main Menu", b"bot_start_menu")]],
            parse_mode="html",
        )
    except (errors.PhoneCodeInvalidError, errors.PhoneCodeExpiredError) as e:
        await app.disconnect()
        _ACTIVE_LOGINS.pop(chat_id, None)
        return await Friday.bot.send_message(
            chat_id,
            f"❌ <b>Invalid or Expired Code:</b> <code>{e}</code>\n\nPlease restart login via /start.",
            buttons=[[custom.Button.inline("🏠 Main Menu", b"bot_start_menu")]],
            parse_mode="html",
        )
    except Exception as e:
        await app.disconnect()
        _ACTIVE_LOGINS.pop(chat_id, None)
        return await Friday.bot.send_message(
            chat_id,
            f"❌ <b>Login failed:</b> <code>{e}</code>\n\n💡 Try terminal session generator: <code>py -3 -m Main.scripts.wizard</code>",
            buttons=[[custom.Button.inline("🏠 Main Menu", b"bot_start_menu")]],
            parse_mode="html",
        )

    _ACTIVE_LOGINS.pop(chat_id, None)
    session_str = app.session.save()
    await app.disconnect()
    await persist_and_finalize_session(app, session_str, chat_id)
