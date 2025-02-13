# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for misc items in the tmos_ui module.
"""

import time

from tmos import Region
from tmos_ui import to_screen

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name


class Test_to_screen:

    def test_when_region_origing_non_zero_the_xy_offset(self):

        offset_x = 23
        offset_y = 45
        a_region = Region(offset_x, offset_y, 100, 100)

        x = 12
        y = 34
        expected_x = x + offset_x
        expected_y = y + offset_y

        assert to_screen(a_region, x, y) == (expected_x, expected_y)
