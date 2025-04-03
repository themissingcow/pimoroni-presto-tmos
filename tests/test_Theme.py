# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for Theme logic
"""
from unittest import mock

import pytest

from tmos import OS, Region
from tmos_ui import DefaultTheme, Theme, WindowManager

from picographics import PicoGraphics

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


class Test_Theme_dpi_scale_factor:

    def test_when_theme_constructed_then_is_not_set(self):

        a_theme = DefaultTheme()
        assert a_theme.dpi_scale_factor is None

    def test_when_setup_then_value_propagated(self):

        a_theme = DefaultTheme()
        expected = 3
        a_theme.setup(mock.Mock(), expected)
        assert a_theme.dpi_scale_factor == expected

    def test_when_set_then_AttributeError_raised(self):

        a_theme = DefaultTheme()
        with pytest.raises(AttributeError):
            a_theme.dpi_scale_factor = 4


class Test_Theme_setup:

    def test_when_setup_with_pen_color_tuples_then_converted_to_pens(self):

        pens = [
            ("foreground_pen", (1, 2, 3)),
            ("background_pen", (4, 5, 6)),
            ("secondary_background_pen", (7, 8, 9)),
            ("error_pen", (10, 11, 12)),
        ]
        assert [p[0] for p in pens] == list(DefaultTheme._pens)

        mock_picographics = PicoGraphics()

        class MockPen:
            def __init__(self, *args):
                self.args = args

        mock_picographics.create_pen.side_effect = MockPen

        a_theme = DefaultTheme()
        for pen, vals in pens:
            setattr(a_theme, pen, vals)

        a_theme.setup(mock_picographics, 1)

        for pen, vals in pens:
            assert getattr(a_theme, pen).args == vals

    def test_when_setup_then_scaled_attributes_updated(self):

        scaled = [
            ("padding", 1),
            ("base_font_scale", 3),
            ("base_text_height", 5),
            ("base_line_height", 7),
            ("control_height", 9),
            ("systray_height", 11),
        ]

        dpi_scale_factor = 2

        mock_picographics = PicoGraphics()
        a_theme = DefaultTheme()
        for prop, val in scaled:
            setattr(a_theme, prop, val)

        a_theme.setup(mock_picographics, dpi_scale_factor)

        for prop, val in scaled:
            assert getattr(a_theme, prop) == (val * dpi_scale_factor)

    def test_when_called_twice_then_noop(self):

        dpi_scale_factor = 2
        base_font_scale = 11
        expected_base_font_scale = base_font_scale * dpi_scale_factor

        mock_picographics = PicoGraphics()
        a_theme = DefaultTheme()
        a_theme.base_font_scale = base_font_scale
        a_theme.setup(mock_picographics, dpi_scale_factor)
        assert a_theme.base_font_scale == expected_base_font_scale
        a_theme.setup(mock_picographics, dpi_scale_factor)
        assert a_theme.base_font_scale == expected_base_font_scale
