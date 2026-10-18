# Copyright (C) 2021-present by StarkGang@Github, < https://github.com/StarkGang >.
#
# This file is part of < https://github.com/StarkGang/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/StarkGang/Friday/blob/main/LICENSE >
#
# All rights reserved.

from Main import Friday
from Main.core.types import FridayTelegramClient as Client, Message
from Main.core.decorators import log_errors


@Friday.register_on_cmd(
    ["sethandler", "setprefix", "setpfx", "setcmdhandler"],
    bot_mode_unsupported=True,
    cmd_help={
        "help": "Set your custom command handler prefix for Friday userbot.",
        "example": [
            "sethandler !",
            "sethandler .",
            "sethandler ,",
        ],
    },
    requires_input=True,
)
@log_errors
async def set_handler_cmd(c: Client, m: Message):
    new_pfx = (m.user_input or "").strip()
    if not new_pfx or len(new_pfx) > 2 or " " in new_pfx:
        return await m.handle_message(
            "❌ <b>Invalid prefix.</b> Choose 1 or 2 characters without spaces (e.g. <code>.</code>, <code>!</code>, <code>,</code>, <code>?</code>)."
        )

    old_pfx = getattr(Friday, "user_command_handler", ".") or "."
    Friday.user_command_handler = new_pfx

    if Friday.config and Friday.db is not None:
        await Friday.config.add_env_to_db("CMD_HANDLER", new_pfx, upsert=True)

    # Rebuild help documentation across all plugins with the updated prefix
    if hasattr(Friday, "prepare_help"):
        Friday.prepare_help()
    elif hasattr(Friday, "_build_command_help_message"):
        Friday._build_command_help_message()

    return await m.handle_message(
        f"✅ <b>Command prefix updated!</b>\n\n"
        f"• <b>Old prefix:</b> <code>{old_pfx}</code>\n"
        f"• <b>New prefix:</b> <code>{new_pfx}</code>\n\n"
        f"<i>All command examples now use:</i> <code>{new_pfx}ping</code>, <code>{new_pfx}help</code>, etc."
    )
