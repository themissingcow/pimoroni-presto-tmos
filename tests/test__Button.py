# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for the _Button base in the UI layer
"""

from unittest import mock

import pytest

from tmos import Region
from tmos_ui import _Button, Control

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name, redefined-outer-name


class Test__Button_init:

    def test_inherits_Control(self):
        assert issubclass(_Button, Control)

    def test_when_constructed_then_properties_updates(self, a_region):

        a_title = "Button Moon"
        a_title_rel_scale = 12

        b = _Button(a_region, a_title, a_title_rel_scale)
        assert b.region is a_region
        assert b.title is a_title
        assert b.title_rel_scale is a_title_rel_scale

    def test_when_no_title_supplied_then_defaults_to_empty_string(self, a_region):

        b = _Button(a_region)
        assert b.title == ""

    def test_when_no_title_rel_scale_supplied_then_defaults_to_one(self, a_region):

        b = _Button(a_region)
        assert b.title_rel_scale == 1


class Test__Button_set_is_down:

    def test_when_set_is_down_is_called_then_is_down_updated(self, a_test_button):

        a_test_button.set_is_down(True)
        assert a_test_button.is_down
        a_test_button.set_is_down(False)
        assert a_test_button.is_down is False

    def test_when_set_is_down_is_called_then_events_triggered(self, a_test_button):

        a_test_button.set_is_down(True)
        a_test_button.assert_events_called(down=True, up=False, cancel=False)
        a_test_button.reset_mock()
        a_test_button.set_is_down(False)
        a_test_button.assert_events_called(down=False, up=True, cancel=False)

    def test_when_set_is_down_is_called_repeatedly_then_events_triggered_on_first(
        self, a_test_button
    ):

        a_test_button.set_is_down(True)
        a_test_button.assert_events_called(down=True, up=False, cancel=False)
        a_test_button.reset_mock()
        a_test_button.set_is_down(True)
        a_test_button.assert_events_called(down=False, up=False, cancel=False)

        a_test_button.set_is_down(False)
        a_test_button.assert_events_called(down=False, up=True, cancel=False)
        a_test_button.reset_mock()
        a_test_button.set_is_down(False)
        a_test_button.assert_events_called(down=False, up=False, cancel=False)


@pytest.fixture
def a_region():
    return Region(10, 20, 100, 200)


@pytest.fixture
def a_test_button(a_region):
    """
    A button with mocked even callbacks.
    """

    class TestButton(_Button):
        def assert_events_called(self, down=False, up=False, cancel=False):

            def assert_called(fn, was_called):
                if was_called:
                    fn.assert_called_once()
                else:
                    fn.assert_not_called()

            assert_called(self.on_button_down, down)
            assert_called(self.on_button_up, up)
            assert_called(self.on_button_cancel, cancel)

    b = TestButton(a_region)
    b.on_button_down = mock.Mock()
    b.on_button_up = mock.Mock()
    b.on_button_cancel = mock.Mock()

    def reset_mock():
        b.on_button_down.reset_mock()
        b.on_button_up.reset_mock()
        b.on_button_cancel.reset_mock()

    b.reset_mock = reset_mock
    return b
