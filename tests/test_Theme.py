# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for Theme logic
"""

from tmos import OS, Region
from tmos_ui import Theme, WindowManager

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name, redefined-outer-name


class Test_Theme_text_scale:

    def test_when_rel_scale_not_supplied_then_is_base_font_scale(self):
        expected = 123
        a_theme = Theme()
        a_theme.base_font_scale = expected
        scale = a_theme.text_scale()
        assert scale == expected
        assert isinstance(scale, int)

    def test_when_rel_scale_supplied_then_base_font_scale_multiplied_and_rounded_to_int(self):
        a_theme = Theme()
        for base, rel, expected in [
            (2, 0.5, 1),
            (2, 0.48, 1),
            (2, 2.1, 4),
            (2, 2.5, 5),
        ]:
            a_theme.base_font_scale = base
            scale = a_theme.text_scale(rel)
            assert scale == expected
            assert isinstance(scale, int)

    def test_when_rel_scale_reduces_then_scale_always_above_one(self):
        a_theme = Theme()
        for base, rel, expected in [(2, 0.5, 1), (2, 0.2, 1), (2, 0, 1)]:
            a_theme.base_font_scale = base
            scale = a_theme.text_scale(rel)
            assert scale == expected
            assert isinstance(scale, int)


class Test_Theme_line_spacing:

    def test_when_scale_not_supplied_then_is_base_line_height_regardless_of_base_font_scale(self):
        expected = 124
        a_theme = Theme()
        a_theme.base_font_scale = 2
        a_theme.base_line_height = expected
        spacing = a_theme.line_spacing()
        assert spacing == expected
        assert isinstance(spacing, int)

    def test_when_rel_scale_supplied_then_base_line_height_multiplied_by_rel_rounded_and_clamped_text_scale(
        self,
    ):

        line_height = 12

        a_theme = Theme()
        a_theme.base_font_scale = 2
        a_theme.base_line_height = line_height

        # base_line_height is the line height of base_font_scale
        scale_one_line_height = line_height / a_theme.base_font_scale

        for rel, expected in [
            (0.5, scale_one_line_height * a_theme.text_scale(0.5)),
            (0.48, scale_one_line_height * a_theme.text_scale(0.48)),
            (2.1, scale_one_line_height * a_theme.text_scale(2.1)),
            (2.5, scale_one_line_height * a_theme.text_scale(2.5)),
        ]:
            spacing = a_theme.line_spacing(rel)
            assert spacing == expected
            assert isinstance(spacing, int)


class Test_Theme_text_height:

    def test_when_scale_not_supplied_then_is_base_line_height_regardless_of_base_font_scale(self):
        expected = 124
        a_theme = Theme()
        a_theme.base_font_scale = 2
        a_theme.base_text_height = expected
        height = a_theme.text_height()
        assert height == expected
        assert isinstance(height, int)

    def test_when_rel_scale_supplied_then_base_line_height_multiplied_by_rel_rounded_and_clamped_text_scale(
        self,
    ):

        text_height = 10

        a_theme = Theme()
        a_theme.base_font_scale = 2
        a_theme.base_text_height = text_height

        # base_line_height is the line height of base_font_scale
        scale_one_text_height = text_height / a_theme.base_font_scale

        for rel, expected in [
            (0.5, scale_one_text_height * a_theme.text_scale(0.5)),
            (0.48, scale_one_text_height * a_theme.text_scale(0.48)),
            (2.1, scale_one_text_height * a_theme.text_scale(2.1)),
            (2.5, scale_one_text_height * a_theme.text_scale(2.5)),
        ]:
            height = a_theme.text_height(rel)
            assert height == expected
            assert isinstance(height, int)
