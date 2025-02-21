# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for the MomentaryButton in the UI layer
"""

from unittest import mock

import pytest

from tmos import Region
from tmos_ui import _Button, MomentaryButton

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name, redefined-outer-name


class Test_MomentaryButton_init:

    def test_inherits__Button(self):
        assert issubclass(MomentaryButton, _Button)


class Test_MomentaryButton_process_touch_state:

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
        a_test_button.set_is_down(True)
        a_test_button.reset_mock()
        a_test_button.process_touch_state(a_touch_inside)
        assert a_test_button.is_down is True
        a_test_button.assert_events_called(down=False, up=False, cancel=False)

    def test_when_down_and_touch_false_then_button_is_up_and_up_event_triggered(
        self, a_test_button, a_touch_inside
    ):
        a_test_button.set_is_down(True)
        a_test_button.reset_mock()
        a_touch_inside.state = False
        a_test_button.process_touch_state(a_touch_inside)
        assert a_test_button.is_down is False
        a_test_button.assert_events_called(down=False, up=True, cancel=False)

    def test_when_down_and_touch_true_outside_then_button_is_up_and_cancel_event_triggered(
        self, a_test_button, a_touch_outside
    ):
        a_test_button.set_is_down(True)
        a_test_button.reset_mock()
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

    class TestButton(MomentaryButton):
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


@pytest.fixture
def a_touch_outside(a_test_button, mock_touch_factory):
    mock_touch = mock_touch_factory()
    mock_touch.state = True
    mock_touch.x = a_test_button.region.x - 1
    mock_touch.y = a_test_button.region.y - 1
    return mock_touch


@pytest.fixture
def a_touch_inside(a_test_button, mock_touch_factory):
    mock_touch = mock_touch_factory()
    mock_touch.state = True
    mock_touch.x = a_test_button.region.x + 1
    mock_touch.y = a_test_button.region.y + 1
    return mock_touch
