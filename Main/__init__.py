# Copyright (C) 2021-present by FridaySoftware@Github, < https://github.com/FridaySoftware >.
#
# This file is part of < https://github.com/FridaySoftware/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/FridaySoftware/Friday/blob/main/LICENSE >
#
# All rights reserved.

from .core.client import FridayClient
from .utils.suppress import suppress_error, safe_suppress, suppress

Friday = FridayClient()
Altruix = Friday  # Compatibility alias
AltruixClient = FridayClient

__all__ = ["Friday", "FridayClient", "suppress_error", "safe_suppress", "suppress"]
