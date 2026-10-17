# Copyright (C) 2021-present by FridaySoftware@Github, < https://github.com/FridaySoftware >.
#
# This file is part of < https://github.com/FridaySoftware/Friday > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/FridaySoftware/Friday/blob/main/LICENSE >
#
# All rights reserved.

import unittest
from Main import Friday
from Main.utils.progress import render_progress_bar, human_bytes, format_eta


class TestProgress(unittest.IsolatedAsyncioTestCase):
    def test_progress_bar_rendering(self):
        self.assertEqual(render_progress_bar(0.0), "[░░░░░░░░░░░░] 0.0%")
        self.assertEqual(render_progress_bar(50.0), "[██████░░░░░░] 50.0%")
        self.assertEqual(render_progress_bar(100.0), "[████████████] 100.0%")
        self.assertEqual(human_bytes(1024 * 1024 * 5), "5.0 MB")
        self.assertEqual(format_eta(90), "1m 30s")
        self.assertEqual(format_eta(3665), "1h 1m")

    async def test_progress_bar_setting_default_disabled(self):
        await Friday.config.set_progress_bar_sts(False)
        self.assertFalse(await Friday.config.get_progress_bar_sts())

        await Friday.config.set_progress_bar_sts(True)
        self.assertTrue(await Friday.config.get_progress_bar_sts())

        await Friday.config.set_progress_bar_sts(False)
        self.assertFalse(await Friday.config.get_progress_bar_sts())


if __name__ == "__main__":
    unittest.main()
