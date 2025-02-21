# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for the RadioButton control in the UI layer
"""

import time

import pytest

from tmos import Region
from tmos_ui import Control, LatchingButton, RadioButton

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name, redefined-outer-name, protected-access


class Test_RadioButton:

    def test_inherits_Control(self):
        assert issubclass(RadioButton, Control)

    def test_when_options_empty_then_ValueError_raised(self):
        with pytest.raises(ValueError):
            RadioButton(a_region, [])

    def test_when_custom_control_class_supplied_then_used(self, a_region):

        class Custom(LatchingButton):
            pass

        a_radio = RadioButton(a_region, ["a", "b"], control_class=Custom)
        for c in a_radio._controls:
            assert isinstance(c, Custom)

    def test_when_no_current_index_supplied_then_index_zero_is_current(self, a_radio):
        assert a_radio.current_index == 0

    def test_when_current_index_supplied_then_reflected_and_corresponding_control_down(
        self, a_region
    ):
        options = ["a", "b", "c"]
        expected_index = 1
        a_radio = RadioButton(a_region, options, current_index=expected_index)
        self.__assert_current_index(a_radio, expected_index)

    def test_when_current_index_set_then_reflected_and_corresponding_control_down(self, a_radio):
        for i in range(len(a_radio.options)):
            a_radio.set_current_index(i)
            self.__assert_current_index(a_radio, i)

    def test_when_touch_up_over_control_then_current_index_updated(
        self, a_radio, mock_touch_factory
    ):

        assert a_radio.current_index == 0

        for i in range(len(a_radio.options)):
            t = self.__a_touch_over(a_radio, i, mock_touch_factory)
            a_radio.process_touch_state(t)
            # The control updates on touch end
            t.state = False
            a_radio.process_touch_state(t)
            assert a_radio.current_index == i

    def __a_touch_over(self, a_radio, index, mock_touch_factory):
        """
        Creates a fake touch over a specific index in the radio control.
        """
        touch = mock_touch_factory()
        control_width = a_radio.region.width // len(a_radio.options)
        touch.x = (control_width // 2) + (index * control_width)
        touch.y = a_radio.region.y + 1
        touch.state = True
        return touch

    def __assert_current_index(self, a_radio, index):
        """
        Checks the current index and controls reflect this.
        """
        assert a_radio.current_index == index
        for i, ctl in enumerate(a_radio._controls):
            expected_down = i == index
            assert ctl.is_down is expected_down


@pytest.fixture
def a_region():
    return Region(10, 20, 100, 200)


@pytest.fixture
def a_radio(a_region):
    options = ["a", "b", "c"]
    return RadioButton(a_region, options)
