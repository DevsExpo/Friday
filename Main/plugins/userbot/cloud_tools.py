# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

from os.path import isdir, isfile
from os import stat, listdir as ls

from Main import Friday
from Main.core.types import FridayTelegramClient as Client
from Main.core.types.message import Message
from Main.utils.essentials import Essentials
from Main.utils.ui_tokens import STATUS

try:
    from style import bullets
except ImportError:
    bullets = {}

from pathlib import Path

# Set this to your actual project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_safe_path(user_input: str = "") -> Path | None:
    try:
        requested = Path(user_input) if user_input else Path(".")
        if requested.is_absolute():
            resolved = requested.resolve(strict=True)
        else:
            resolved = (PROJECT_ROOT / requested).resolve(strict=True)
        if not resolved.is_relative_to(PROJECT_ROOT):
            return None
        return resolved
    except (OSError, ValueError, RuntimeError):
        return None

b1 = bullets.get("bullet1", ">")
b2 = bullets.get("bullet2", "•")
b3 = bullets.get("bullet3", "⋟")


def readable(data):
    return Essentials.humanbytes(data)


@Friday.register_on_cmd(
    ["listdir", "list", "ls", "ld"],
    cmd_help={
        "help": "Lists given directory given as input.",
        "example": "ls Main/plugins/userbot",
    },
    owner_only=True
)
async def listdir_cmd_handler(c: Client, m: Message):
    msg = await m.handle_message("PROCESSING")
    input_ = (m.raw_user_input or "").strip()
    target_dir = get_safe_path(input_)

    if target_dir is None:
        return await msg.edit(
            f"<b>Invalid directory or access denied:</b> <code>{input_ or '.'}</code>"
        )

    if not target_dir.is_dir():
        return await msg.edit(
            f"<code>{input_ or '.'}</code> <b>is not a directory.</b>"
        )
    if not target_dir:
        return await msg.edit(f"<code>{input_}</code> <b>is an invalid directory.</b>")
    files = []
    folders = []
    lists = sorted(ls(target_dir))
    length = len(lists)
    if length == 0:
        return await msg.edit(f"<code>{target_dir}</code> <b>is an empty folder.</b>")
    for i in lists:
        j = f"{target_dir}/{i}"
        if isdir(j):
            folders.append(f"<code>  {b1} {i}</code>")
        if isfile(j):
            files.append(f"<code>  {b2} {i} ({readable(stat(j).st_size)})</code>")
    disp_name = input_ or "current directory"
    output_ = f"<b>Files and Folders in</b> <code>{disp_name}</code> (<code>{length}</code>) <b>are :</b> \n\n"
    output_ += f"<code>{b3}</code> <i><b>Folders</b></i> (<code>{len(folders)}</code>):\n"
    output_ += ("\n").join(folders)
    output_ += "\n\n"
    output_ += f"<code>{b3}</code> <i><b>Files</b></i> (<code>{len(files)}</code>):\n"
    output_ += ("\n").join(files)
    del (files, folders)
    if input_ and input_.startswith("/"):
        output_ += f"\n\n<b>Note:</b> <code>{input_}</code> <b>is a parent directory.</b>"
    await msg.edit_msg(f"{output_}")



@Friday.register_on_cmd(
    ["remove", "rm"],
    cmd_help={
        "help": "Removes files or directories inside the project.",
        "example": "rm -a |*.log",
        "user_args": [
            {
                "arg": "d",
                "help": "to remove an empty directory.",
                "requires_input": False,
            },
            {
                "arg": "a",
                "help": "to remove files of the same type from a directory.",
                "requires_input": False,
            },
        ],
    },
    requires_input=True,
    owner_only=True
)
async def remove_cmd_handler(c: Client, m: Message):
    msg = await m.handle_message("PROCESSING")
    input_ = (m.raw_user_input or "").strip()
    u_input = (m.user_input or "").strip()
    user_args = m.user_args or []

    if "d" in user_args:
        target = get_safe_path(u_input)

        if target is None:
            return await msg.edit(
                f"{STATUS.ERROR} <b>Invalid path or access denied.</b>"
            )

        if target == PROJECT_ROOT:
            return await msg.edit(
                f"{STATUS.ERROR} <b>Cannot delete project root.</b>"
            )

        if not target.is_dir():
            return await msg.edit(
                f"<code>{u_input}</code> <b>is not a directory.</b>"
            )

        try:
            target.rmdir()
            return await msg.edit(
                f"<b>Folder,</b> <code>{u_input}</code> "
                "<b>has been removed successfully.</b>"
            )
        except OSError as error:
            return await msg.edit(
                f"<b>Unable to delete</b> <code>{u_input}</code>.\n\n"
                f"<code>{error}</code>"
            )

    elif "a" in user_args:
        if "|*." not in u_input:
            return await msg.edit_msg("INVALID_INPUT")

        directory_part, extension = u_input.split("*", 1)
        directory_input = directory_part.removesuffix("|").strip()
        extension = extension.strip()

        if (
            not directory_input
            or not extension.startswith(".")
            or extension in (".", "..")
            or any(char in extension for char in ("/", "\\", "*", "|"))
        ):
            return await msg.edit_msg("INVALID_INPUT")

        target_dir = get_safe_path(directory_input)

        if target_dir is None:
            return await msg.edit(
                f"{STATUS.ERROR} <b>Invalid directory or access denied.</b>"
            )

        if not target_dir.is_dir():
            return await msg.edit(
                f"<code>{directory_input}</code> "
                "<b>is a file, not a directory.</b>"
            )

        count = 0

        try:
            for entry in target_dir.iterdir():
                if entry.is_symlink() or not entry.is_file():
                    continue

                if not entry.name.endswith(extension):
                    continue

                safe_entry = get_safe_path(
                    str(entry.relative_to(PROJECT_ROOT))
                )

                if safe_entry is None or safe_entry != entry:
                    continue

                safe_entry.unlink()
                count += 1

        except OSError as error:
            return await msg.edit(
                f"<b>Unable to delete files.</b>\n\n"
                f"<code>{error}</code>\n"
                f"<b>Files removed:</b> <code>{count}</code>"
            )

        return await msg.edit(
            f"<b>Removed all files ending with</b> "
            f"<code>{extension}</code> <b>in</b> "
            f"<code>{directory_input}</code> "
            f"(<code>{count}</code>)."
        )

    else:
        target = get_safe_path(input_)

        if target is None:
            return await msg.edit(
                f"{STATUS.ERROR} <b>Invalid path or access denied.</b>"
            )

        if target.is_dir():
            return await msg.edit(
                f"<code>{input_}</code> "
                "<b>is a directory, not a file.</b>"
            )

        try:
            target.unlink()
            return await msg.edit(
                f"<b>File,</b> <code>{input_}</code> "
                "<b>has been removed successfully.</b>"
            )
        except OSError as error:
            return await msg.edit(
                f"<b>Unable to delete</b> <code>{input_}</code>.\n\n"
                f"<code>{error}</code>"
            )
