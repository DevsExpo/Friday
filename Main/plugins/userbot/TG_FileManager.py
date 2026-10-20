# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

import os
import time
from pathlib import Path
from Main import Friday
from Main.core.types.message import Message
from Main.utils.essentials import Essentials
from Main.utils.suppress import suppress_error
from Main.utils.ui_tokens import STATUS

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ALLOWED_DIRS = (
    PROJECT_ROOT,
    (PROJECT_ROOT / "temp").resolve(),
    (PROJECT_ROOT / "cache").resolve(),
)

SENSITIVE_FILES = {
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
    "id_dsa",
    "credentials.json",
    "token.pickle",
    "auth.json",
}

SENSITIVE_EXTENSIONS = (
    ".session",
    ".session-journal",
    ".key",
    ".pem",
    ".pfx",
    ".p12",
    ".db",
    ".db-wal",
    ".db-journal",
    ".pkcs12",
    ".env"
)


def is_sensitive_file(path: Path) -> bool:
    name = path.name.lower()
    if name in SENSITIVE_FILES or name.startswith(".env"):
        return True
    if any(name.endswith(ext) for ext in SENSITIVE_EXTENSIONS):
        return True
    for part in path.parts:
        if part.lower() in (".git", "__pycache__"):
            return True
    return False


@Friday.register_on_cmd(
    ["download"],
    cmd_help={
        "help": "Download files from telegram to local storage safely within ./temp/downloads.",
        "example": [
            "download (replying to file)",
            "download custom_name.zip",
            "download -sethumb (replying to photo)",
        ],
        "user_args": [
            {
                "arg": "sethumb",
                "help": "Save replied photo as custom thumbnail.",
                "requires_input": False,
            }
        ],
    },
    requires_reply=True,
)
async def download_files_from_telegram(c, m: Message):
    msg = await m.handle_message("PROCESSING")
    rm = m.reply_to_message or (await m.get_reply_message() if hasattr(m, "get_reply_message") else None)
    if not rm or not rm.file:
        return await msg.edit_msg("REPLY_TO_FILE")

    user_args = m.user_args
    is_sethumb = bool(user_args and ("sethumb" in user_args or "-sethumb" in user_args))
    start_time = time.time()

    base_confinement = (PROJECT_ROOT / "temp").resolve()
    base_confinement.mkdir(parents=True, exist_ok=True)

    if is_sethumb:
        target_path = base_confinement / "thumb.jpg"
    else:
        downloads_dir = (base_confinement / "downloads").resolve()
        downloads_dir.mkdir(parents=True, exist_ok=True)
        raw_name = (m.user_input or "").strip()
        if raw_name:
            clean_name = Path(raw_name.replace("\\", "/")).name
            if not clean_name or clean_name in (".", "..") or clean_name.startswith("."):
                return await msg.edit_msg(
                    f"{STATUS.ERROR} <b>Invalid filename:</b> Directory traversal or hidden files not allowed."
                )
            target_path = downloads_dir / clean_name
        else:
            target_path = downloads_dir

    resolved_target = target_path.resolve()
    if not resolved_target.is_relative_to(base_confinement):
        return await msg.edit_msg(
            f"{STATUS.DENIED} <b>Path Traversal Blocked:</b> Target must remain inside <code>temp/downloads</code>."
        )

    try:
        file_ = await rm.download_media(file=str(target_path))
    except Exception as exc:
        return await msg.edit_msg(f"{STATUS.ERROR} <b>Download Failed:</b> <code>{exc}</code>")

    if file_:
        downloaded_resolved = Path(file_).resolve()
        if not downloaded_resolved.is_relative_to(base_confinement):
            with suppress_error():
                downloaded_resolved.unlink(missing_ok=True)
            return await msg.edit_msg(
                f"{STATUS.DENIED} <b>Path Traversal Blocked:</b> Downloaded file escaped temp directory."
            )

    end_time = round(time.time() - start_time, 2)
    await msg.edit_msg("FILE_DOWNLOADED", string_args=(str(file_), end_time))


@Friday.register_on_cmd(
    ["upload"],
    cmd_help={
        "help": "Upload files from host system to telegram safely.",
        "example": [
            "upload Friday.log",
            "upload ./temp/downloads/file.zip",
            "upload ./temp/downloads/file.zip -f",
        ],
        "user_args": [
            {
                "arg": "f",
                "help": "Force upload in public chat despite security warning.",
                "requires_input": False,
            },
            {
                "arg": "force",
                "help": "Force upload in public chat despite security warning.",
                "requires_input": False,
            },
        ],
    },
    requires_input=True,
)
async def upload_files_to_telegram(c, m: Message):
    start_time = time.time()
    msg = await m.handle_message("PROCESSING")
    input_ = (m.user_input or "").strip()
    if not input_:
        return await msg.edit_msg("PROPER_INPUT_REQ")

    rm = m.reply_to_message or (await m.get_reply_message() if hasattr(m, "get_reply_message") else None)
    msg_id = rm.id if rm else m.id

    try:
        raw_path = Path(input_)
        target_path = (raw_path if raw_path.is_absolute() else (PROJECT_ROOT / raw_path)).resolve(strict=True)
    except (OSError, ValueError, RuntimeError, FileNotFoundError):
        return await msg.edit_msg("404_FILE_NOT_FOUND")

    if not target_path.is_file():
        return await msg.edit_msg("404_FILE_NOT_FOUND")

    # 1. Path confinement check: Must be within PROJECT_ROOT, temp, or cache
    if not any(target_path.is_relative_to(root) for root in ALLOWED_DIRS):
        return await msg.edit_msg(
            f"{STATUS.DENIED} <b>Path Traversal Blocked:</b> Access outside the project workspace is strictly forbidden."
        )

    # 2. Sensitive file check: Block credentials, databases, sessions, keys
    if is_sensitive_file(target_path):
        return await msg.edit_msg(
            f"{STATUS.DENIED} <b>Security Block:</b> Uploading sensitive system/credential files "
            f"(<code>{target_path.name}</code>) is strictly prohibited to prevent data leaks."
        )

    # 3. Public chat check: Warn when uploading local host files in public chats
    is_private = getattr(m, "is_private", False) or getattr(m.chat, "type", "") == "private"
    is_forced = bool(
        m.user_args
        and (
            "force" in m.user_args
            or "f" in m.user_args
            or "-force" in m.user_args
            or "-f" in m.user_args
        )
    )

    if not is_private and not is_forced:
        prefix = getattr(Friday, "user_command_handler", ".") or "."
        return await msg.edit_msg(
            f"{STATUS.WARNING} <b>Security Warning:</b> Uploading server files to a public/group chat is visible to all members!\n\n"
            f"If you really want to upload here, use:\n"
            f"<code>{prefix}upload {input_} -f</code> (or <code>-force</code>)\n\n"
            "💡 <i>Tip: Run this command in Saved Messages / PM instead.</i>"
        )

    thumb_temp = (PROJECT_ROOT / "temp" / "thumb.jpg")
    thumb_cache = (PROJECT_ROOT / "cache" / "thumb.jpg")
    thumb = str(thumb_temp) if thumb_temp.exists() else (str(thumb_cache) if thumb_cache.exists() else None)

    chat_target = m.chat_id or (getattr(m.chat, "id", None))
    await c.send_file(
        chat_target,
        str(target_path),
        thumb=thumb,
        reply_to=msg_id,
    )
    time_taken = round(time.time() - start_time, 2)
    file_size = Essentials.humanbytes(os.stat(target_path).st_size)
    rel_display = (
        str(target_path.relative_to(PROJECT_ROOT))
        if target_path.is_relative_to(PROJECT_ROOT)
        else target_path.name
    )
    await msg.edit_msg("FILE_UPLOAD", string_args=(rel_display, file_size, time_taken))
