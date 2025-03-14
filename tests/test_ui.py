# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for misc items in the tmos_ui module.
"""

import time

from tmos import Region
from tmos_ui import inset_region, to_screen

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


class Test_inset_region:

    def test_when_x_and_y_supplied_then_inset_to_smaller_region(self):
        r = Region(10, 20, 30, 40)
        assert inset_region(r, 2, 3) == Region(12, 23, 26, 34)

    def test_when_negative_x_and_y_supplied_then_inset_to_larger_region(self):
        r = Region(10, 20, 30, 40)
        assert inset_region(r, -2, -3) == Region(8, 17, 34, 46)

    def test_when_only_x_supplied_then_used_to_inset_y(self):
        r = Region(10, 20, 30, 40)
        assert inset_region(r, 2) == Region(12, 22, 26, 36)
