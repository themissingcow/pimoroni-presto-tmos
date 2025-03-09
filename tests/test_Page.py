# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for Pages in the UI layer
"""

import time
import weakref

from unittest import mock

from tmos import OS, Region
from tmos_ui import Page, WindowManager

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name, redefined-outer-name


class Test_Page_init:

    def test_default_execution_frequency_is_none(self):
        p = Page()
        assert p.execution_frequency is None

    def test_controls_initialised_to_unique_list(self):

        p1 = Page()
        p2 = Page()

        assert p1._controls is not p2._controls
        p1._controls.append(mock.Mock())
        assert p1._controls != p2._controls


class Test_Page:

    def test_when_base_setup_called_then_noop(self):
        Page().setup(Region(0, 0, 1, 1), mock.Mock())

    def test_when_base_will_show_called_then_noop(self):
        Page().will_show()

    def test_when_base_will_hide_called_then_noop(self):
        Page().will_hide()

    def test_when_base__draw_called_then_noop(self):
        Page()._draw(mock.Mock(), mock.Mock(), mock.Mock())

    def test_when_base__update_called_then_noop(self):
        Page()._update(mock.Mock())

    def test_when_teardown_called_then_controls_deleted(self):

        # pylint: disable=protected-access

        p = Page()
        p._controls.append(mock.Mock())
        control_ref = weakref.ref(p._controls[0])
        p.teardown()
        assert len(p._controls) == 0
        assert control_ref() is None

    def test_when_base_tick_called_then_controls_processed_around__update_and__draw_call(self):

        # pylint: disable=protected-access

        class MyPage(Page):
            pass

        a_region = Region(0, 0, 1, 2)
        a_control = mock.Mock()
        os_instance = OS()
        a_wm = WindowManager(os_instance)
        a_page = MyPage()

        # Shim the update/draw method to be a mock method on the control. This
        # makes it easier to then check the order of operations.
        # Total fudge, but it saves a lot of faffing.
        a_page._update = a_control.proxy_page__update
        a_page._draw = a_control.proxy_page__draw

        a_page._controls.append(a_control)
        a_page.tick(a_region, a_wm)

        assert a_control.mock_calls == [
            mock.call.process_touch_state(os_instance.touch),
            mock.call.proxy_page__update(a_wm.os),
            mock.call.proxy_page__draw(a_wm.display, a_region, a_wm.theme),
            mock.call.draw(a_wm.display, a_wm.theme),
        ]
