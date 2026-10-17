# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

import sys
from Main import Friday


def main() -> None:
    try:
        Friday.run()
    except (KeyboardInterrupt, SystemExit):
        Friday.log("Friday process terminated.")
        sys.exit(0)


if __name__ == "__main__":
    main()
