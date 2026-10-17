# Copyright (C) 2021-present by StarkGang@Github, < https://github.com/StarkGang >.
#
# This file is part of < https://github.com/StarkGang/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/StarkGang/Friday/blob/main/LICENSE >
#
# All rights reserved.

from Main import Friday
from Main.utils._updater import *
from Main.core.types.message import Message


@Friday.register_on_cmd(
    "update",
    cmd_help={
        "help": "Updates your userbot bot.",
        "example": "update",
        "user_args": [
            {
                "arg": "changelog",
                "help": "Generate and shows changelog.",
                "requires_input": False,
            }
        ],
    },
)
async def update(client, message: Message):
    msg = await message.handle_message("PROCESSING")
    updater_ = Updater(
        repo=Friday.config.REPO, branch="main", app_url=Friday.app_url_
    )
    await msg.edit_msg("UPDATING")
    repo = await updater_.init_repo()
    if message.user_args.changelog:
        repo = await updater_.init_repo()
        if cl := await updater_.gen_changelog(repo, message, Friday.config.REPO):
            cl = f"<b>Change-log for Friday <i>v{Friday.__version__}</i></b> \n{cl}"
        else:
            cl = "NO_CHANGES"
        await msg.edit_msg(cl)
    uprem = await updater_.create_remote_and_fetch(repo)
    if Friday.app_url_:
        await updater_.update_remotely_heroku(uprem, repo, msg)
    else:
        await updater_.update_locally(uprem, repo, msg)
    return await msg.edit_msg("UPDATER_SUCCESS", string_args=(Friday.__version__))
