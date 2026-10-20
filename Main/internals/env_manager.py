# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

from Main import Friday
from Main.core.types.message import Message
from Main.utils.ui_tokens import STATUS


@Friday.register_on_cmd(
    "addenv",
    cmd_help={
        "help": "Adds Env to database! In public chats, value is hidden for privacy.",
        "example": "addenv env_varname env_value",
    },
    requires_input=True,
    owner_only=True,
)
async def add_env_cmd_handler(c, m: Message):
    ms = await m.handle_message("PROCESSING")
    input_ = m.user_input
    if not input_ or " " not in input_:
        return await ms.edit_msg("PROPER_INPUT_REQ")
    env_key, value = input_.split(" ", maxsplit=1)
    await Friday.config.sync_env_to_db(env_key, value)

    is_private = getattr(m, "is_private", False) or getattr(m.chat, "type", "") == "private"
    if is_private:
        await ms.edit_msg("ENV_ADDED", string_args=(env_key, value))
    else:
        await ms.edit_msg("ENV_ADDED", string_args=(env_key, "•••••••• [HIDDEN IN PUBLIC CHAT]"))


@Friday.register_on_cmd(
    "delenv",
    cmd_help={
        "help": "Deletes env from database!",
        "example": "delenv env_varname",
    },
    requires_input=True,
    owner_only=True,
)
async def del_env_cmd_handler(c, m: Message):
    ms = await m.handle_message("PROCESSING")
    input_ = m.user_input.strip()
    if not await Friday.config.get_env(input_):
        return await ms.edit_msg("NO_ENV_FOUND", string_args=(input_,))
    await Friday.config.del_env_from_db(input_)
    await ms.edit_msg("ENV_DELETED", string_args=(input_,))


@Friday.register_on_cmd(
    "getenv",
    cmd_help={
        "help": "Gets env from database! In public chats, use -f / -force to display.",
        "example": [
            "getenv env_varname",
            "getenv env_varname -f",
            "getenv env_varname -force",
        ],
        "user_args": [
            {
                "arg": "f",
                "help": "Force display in public chat despite security risks.",
                "requires_input": False,
            },
            {
                "arg": "force",
                "help": "Force display in public chat despite security risks.",
                "requires_input": False,
            },
        ],
    },
    requires_input=True,
    owner_only=True,
)
async def get_env_cmd_handler(c, m: Message):
    ms = await m.handle_message("PROCESSING")
    input_ = (m.user_input or "").strip()
    if not input_:
        return await ms.edit_msg("PROPER_INPUT_REQ")

    is_forced = bool(
        m.user_args
        and (
            "force" in m.user_args
            or "f" in m.user_args
            or "-force" in m.user_args
            or "-f" in m.user_args
        )
    )

    is_private = getattr(m, "is_private", False) or getattr(m.chat, "type", "") == "private"
    if not is_private and not is_forced:
        prefix = getattr(Friday, "user_command_handler", ".") or "."
        return await ms.edit_msg(
            f"{STATUS.WARNING} <b>Security Warning:</b> Viewing sensitive environment variables in a public/group chat is not wise!\n\n"
            f"If you really want to view it here, use:\n<code>{prefix}getenv {input_} -f</code> (or <code>-force</code>)\n\n"
            "💡 <i>Tip: Run this command in Saved Messages / PM instead.</i>"
        )

    value = await Friday.config.get_env(input_)
    if not value:
        return await ms.edit_msg("NO_ENV_FOUND", string_args=(input_,))
    await ms.edit_msg("ENV_VALUE", string_args=(input_, value))
