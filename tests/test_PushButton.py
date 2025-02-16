# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for controls in the UI layer
"""

from unittest import mock

import pytest

from tmos import Region
from tmos_ui import Control, PushButton

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name, redefined-outer-name


class Test_PushButton_init:

    def test_inherits_Control(self):
        assert issubclass(PushButton, Control)

    def test_when_constructed_then_properties_updates(self, a_region):

        a_title = "Button Moon"
        a_title_rel_scale = 12

        b = PushButton(a_region, a_title, a_title_rel_scale)
        assert b.region is a_region
        assert b.title is a_title
        assert b.title_rel_scale is a_title_rel_scale

    def test_when_no_title_supplied_then_defaults_to_empty_string(self, a_region):

        b = PushButton(a_region)
        assert b.title == ""

    def test_when_no_title_rel_scale_supplied_then_defaults_to_one(self, a_region):

        b = PushButton(a_region)
        assert b.title_rel_scale == 1


class Test_PushButton_process_touch_state:

    def test_when_up_and_touch_true_outside_then_button_is_not_down_and_no_events_triggered(
        self, a_test_button, a_touch_outside
    ):
        assert a_test_button.is_down is False
        a_test_button.process_touch_state(a_touch_outside)
        assert a_test_button.is_down is False
        a_test_button.assert_events_called(down=False, up=False, cancel=False)

    def test_when_up_and_touch_true_inside_then_button_is_down_and_down_event_triggered(
        self, a_test_button, a_touch_inside
    ):
        assert a_test_button.is_down is False
        a_test_button.process_touch_state(a_touch_inside)
        assert a_test_button.is_down is True
        a_test_button.assert_events_called(down=True, up=False, cancel=False)

    def test_when_down_and_touch_true_inside_then_button_is_down_and_down_event_not_retriggered(
        self, a_test_button, a_touch_inside
    ):
        a_test_button.is_down = True
        a_test_button.process_touch_state(a_touch_inside)
        assert a_test_button.is_down is True
        a_test_button.assert_events_called(down=False, up=False, cancel=False)

    def test_when_down_and_touch_false_then_button_is_up_and_up_event_triggered(
        self, a_test_button, a_touch_inside
    ):
        a_test_button.is_down = True
        a_touch_inside.state = False
        a_test_button.process_touch_state(a_touch_inside)
        assert a_test_button.is_down is False
        a_test_button.assert_events_called(down=False, up=True, cancel=False)

    def test_when_down_and_touch_true_outside_then_button_is_up_and_cancel_event_triggered(
        self, a_test_button, a_touch_outside
    ):
        a_test_button.is_down = True
        a_test_button.process_touch_state(a_touch_outside)
        assert a_test_button.is_down is False
        a_test_button.assert_events_called(down=False, up=False, cancel=True)


@pytest.fixture
def a_region():
    return Region(10, 20, 100, 200)


@pytest.fixture
def a_test_button(a_region):
    """
    A button with mocked even callbacks.
    """

    class TestButton(PushButton):
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
    return b


@pytest.fixture
def mock_touch():
    """
    Provides a mock touch data structure
    """

    class State:
        state = False
        x = 0
        y = 0
        state2 = False
        x2 = 0
        y2 = 0

    return State()


@pytest.fixture
def a_touch_outside(a_test_button, mock_touch):
    mock_touch.state = True
    mock_touch.x = a_test_button.region.x - 1
    mock_touch.y = a_test_button.region.y - 1
    return mock_touch


@pytest.fixture
def a_touch_inside(a_test_button, mock_touch):
    mock_touch.state = True
    mock_touch.x = a_test_button.region.x + 1
    mock_touch.y = a_test_button.region.y + 1
    return mock_touch
