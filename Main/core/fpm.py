# Copyright (C) 2021-present by DevsExpo@Github, < https://github.com/DevsExpo >.
#
# This file is part of < https://github.com/DevsExpo/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/Friday/blob/main/LICENSE >
#
# All rights reserved.

"""
Friday Package Manager (FPM)
Pure GitHub/Git based plugin management framework.
"""

from Main.core.plugin_manager import PluginManager, PluginManifest

# Re-export PluginManager as FPM for backward compatibility
FPM = PluginManager

__all__ = ["FPM", "PluginManager", "PluginManifest"]
