# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for controls in the UI layer
"""

import time

from unittest import mock

from tmos import Region
from tmos_ui import Control

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name


class Test_Control:

    def test_default_process_touch_state_implementation_is_a_noop(self):

        c = Control()
        touch_state = mock.Mock()
        c.process_touch_state(touch_state)
        touch_state.assert_not_called()

    def test_draw_implementation_is_a_noop(self):

        c = Control()
        display = mock.Mock()
        theme = mock.Mock()
        c.draw(display, theme)
        display.assert_not_called()
        theme.assert_not_called()

    def test__event_called_then_named_attr_invoked_with_forwarded_args(self):

        c = Control()
        c.on_a = mock.Mock()
        # pylint: disable=protected-access
        c._event("on_a", 1, 2, three=3, four=4)
        c.on_a.assert_called_with(1, 2, three=3, four=4)
