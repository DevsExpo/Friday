# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

import os
import re
import uuid
import base64
import psutil
import socket
import platform
from Main import Friday
from Main.utils.suppress import suppress_error
from os import remove as rmv
from mimetypes import guess_type
from Main.utils.paste import Paste
from Main.core.types import Message, FridayTelegramClient
from Main.utils.essentials import Essentials
from Main.utils.ui_tokens import STATUS
from Main.utils.inline_helper import is_owner



def verify_owner(m: Message) -> bool:
    sender_id = getattr(m, "sender_id", None)
    if sender_id is None and hasattr(m, "from_user") and m.from_user:
        sender_id = getattr(m.from_user, "id", None)
    if is_owner(sender_id):
        return True
    if getattr(m, "is_self", False):
        return True
    return False


def fileToBase64(file_path: str) -> str:
    """
    File to Base64
        takes a file as input and encodes it to base 64
    """
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read())


@Friday.run_in_exc
def get_info(value=False) -> tuple:
    """
    Get Info
        fetches information about your system
        hides MAC and IP until explicitly referenced
        incompatible with termux due to problem with ethtool.h file .so objects
    """
    splatform = platform.system()
    platform_release = platform.release()
    platform_version = platform.version()
    architecture = platform.machine()
    hostname = socket.gethostname()
    ip_address = "Unable to fetch"
    mac_address = "Unable to fetch"
    with suppress_error(msg="Fetching host ip"):
        ip_address = socket.gethostbyname(socket.gethostname())
    with suppress_error(msg="Fetching mac address"):
        mac_address = ":".join(re.findall("..", "%012x" % uuid.getnode()))
    processor = platform.processor()
    ram = Essentials.humanbytes(round(psutil.virtual_memory().total))
    cpu_freq = psutil.cpu_freq().current
    if cpu_freq >= 1000:
        cpu_freq = f"{round(cpu_freq / 1000, 2)}GHz"
    else:
        cpu_freq = f"{round(cpu_freq, 2)}MHz"
    du = psutil.disk_usage(os.getcwd())
    psutil.disk_io_counters()
    disk = f"{Essentials.humanbytes(du.used)}/{Essentials.humanbytes(du.total)}({du.percent}%)"
    cpu_len = len(psutil.Process().cpu_affinity())
    return (
        splatform,
        platform_release,
        platform_version,
        architecture,
        hostname,
        ip_address if value else None,
        mac_address if value else None,
        processor,
        ram,
        cpu_len,
        cpu_freq,
        disk,
    )


@Friday.register_on_cmd(
    ["ubstat", "stat"],
    cmd_help={
        "help": "Get info about your machine.",
        "example": "ubstat",
        "user_args": [
            {
                "arg": "a",
                "help": "Reveal all info - IP and MAC.",
                "requires_input": False,
            },
        ],
    },
)
async def sTATS(c: FridayTelegramClient, m: Message):
    if not verify_owner(m):
            return await m.handle_message(
            f"{STATUS.ERROR} <b>Security Violation:</b> <code>Only the userbot owner retrieve this info.</code>"
        )
    msg = await m.handle_message("PROCESSING")
    value = m.user_args and m.user_args.a
    ub_stat = await get_info(value)
    database_ = await Friday.db._db_name.command("dbstats")
    s = tuple(ub_stat) + (
        Essentials.humanbytes(database_["dataSize"]),
        Essentials.humanbytes(database_.get("storageSize")),
    )
    await msg.edit_msg("UBSTAT", string_args=s)


# Unstable


@Friday.register_on_cmd(
    ["base64", "b64"],
    cmd_help={
        "help": "Encodes given file to an url",
        "example": "base64 <reply_to_file>",
    },
    requires_reply=True,
)
async def file_to_b64(c: FridayTelegramClient, m: Message):
    msg = await m.handle_message("PROCESSING")
    reply = await m.get_reply_message()
    if not reply or not reply.media:
        return await msg.edit("Reply to media...")
    temp_dir = os.path.abspath("./temp")
    os.makedirs(temp_dir, exist_ok=True)
    file = await reply.download_media(file=temp_dir)
    try:
        base = fileToBase64(file)
        type_ = guess_type(file)[0]
        name, link = await Paste(f"data:{type_};base64,{str(base)[2:][:-1]}").paste()
        await msg.edit(
            Friday.get_string("PASTE_TEXT").format(link, name),
            link_preview=False,
        )
    finally:
        if file and os.path.exists(file):
            rmv(file)

