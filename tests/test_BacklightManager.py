# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for the OS implementation. Designed to run off-platform, they
focus on the specifics of the business logic and advertised
functionality.
"""

from unittest import mock

import pytest

from tmos import BacklightManager

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name


class Test_BacklightManager_init:

    def test_when_created_then_settings_dont_share_an_instance(self):
        """
        As this is a class, its easily to accidentally create a class
        var, which would share an instance of the settings. Cough.
        """

        bm_1 = BacklightManager()
        bm_2 = BacklightManager()

        bm_2.display_timeouts.dim = 70
        bm_2.display_brightnesses.dim = 0.0
        bm_2.glow_led_brighnesses.dim = 1.0

        assert bm_2.display_timeouts.dim != bm_1.display_timeouts.dim
        assert bm_2.display_brightnesses.dim != bm_1.display_brightnesses.dim
        assert bm_2.glow_led_brighnesses.dim != bm_1.glow_led_brighnesses.dim


class Test_BacklightManager_set_glow_leds:

    def test_when_no_presto_instance_then_no_exception_raised(self):

        bm = BacklightManager()
        assert bm.presto is None
        bm.set_glow_leds(255, 255, 255)

    def test_when_called_with_leds_then_set_values_reflect_display_phase(self):

        bm = BacklightManager()
        assert bm.display_phase_controls_glow_leds

        mock_set = mock.Mock()
        bm.presto = mock.Mock()
        bm.presto.set_led_rgb = mock_set

        rgb = (200, 100, 10)

        for phase, brightness in (
            (bm.DISPLAY_ON, 0.9),
            (bm.DISPLAY_DIM, 0.5),
            (bm.DISPLAY_SLEEP, 0.3),
        ):

            mock_set.reset_mock()

            expected_values = [int(c * brightness) for c in rgb]
            expected_calls = [
                mock.call(i, *expected_values) for i in range(bm.num_leds)
            ]

            setattr(bm.glow_led_brighnesses, phase, brightness)
            bm.display_phase = phase

            bm.set_glow_leds(*rgb)
            mock_set.assert_has_calls(expected_calls)

    def test_when_control_disabled_then_set_values_ignore_display_phase(self):

        bm = BacklightManager()
        bm.display_phase_controls_glow_leds = False

        mock_set = mock.Mock()
        bm.presto = mock.Mock()
        bm.presto.set_led_rgb = mock_set

        rgb = (200, 100, 10)

        for phase, brightness in (
            (bm.DISPLAY_ON, 0.9),
            (bm.DISPLAY_DIM, 0.5),
            (bm.DISPLAY_SLEEP, 0.3),
        ):

            mock_set.reset_mock()

            expected_calls = [mock.call(i, *rgb) for i in range(bm.num_leds)]

            setattr(bm.glow_led_brighnesses, phase, brightness)
            bm.display_phase = phase

            bm.set_glow_leds(*rgb)
            mock_set.assert_has_calls(expected_calls)


class Test_BacklightManager_update_display_phase:

    def test_when_initialised_then_display_is_none(self):

        bm = BacklightManager()
        assert bm.display_phase is None

    def test_when_updated_then_phase_refelcted_time_interval(self, mock_presto_module):

        bm = BacklightManager()
        bm.presto = mock_presto_module.Presto()
        bm.display_timeouts.dim = 10
        bm.display_timeouts.sleep = 20
        bm.display_brightnesses.on = 0.9
        bm.display_brightnesses.dim = 0.5
        bm.display_brightnesses.sleep = 0.1

        now_s = 1234
        for interval, expected_phase in (
            (4, bm.DISPLAY_ON),
            (14, bm.DISPLAY_DIM),
            (24, bm.DISPLAY_SLEEP),
        ):

            bm.presto.set_backlight.reset_mock()

            last_interaction_s = now_s - interval
            bm.update_display_phase(now_s, last_interaction_s)
            assert bm.display_phase == expected_phase

            bm.presto.set_backlight.assert_called_with(
                bm.display_brightnesses.for_phase(expected_phase)
            )

    def test_when_dim_timeout_zero_then_phase_inactive(self):

        bm = BacklightManager()

        now_s = 1234
        for dim_timeout, sleep_timeout, interval, expected_phase in (
            (0, 10, 4, bm.DISPLAY_ON),
            (0, 10, 14, bm.DISPLAY_SLEEP),
            (10, 0, 4, bm.DISPLAY_ON),
            (10, 0, 14, bm.DISPLAY_DIM),
        ):
            bm.display_timeouts.dim = dim_timeout
            bm.display_timeouts.sleep = sleep_timeout

            last_interaction_s = now_s - interval
            bm.update_display_phase(now_s, last_interaction_s)
            assert bm.display_phase == expected_phase

    def test_when_glow_led_control_enabled_then_leds_updated(self):

        bm = BacklightManager()
        bm.presto = mock.Mock()
        bm.presto.set_led_rgb = mock.Mock()
        bm.display_phase_controls_glow_leds = True
        bm.display_timeouts.dim = 10
        bm.display_timeouts.sleep = 20
        bm.glow_led_brighnesses.on = 0.9
        bm.glow_led_brighnesses.dim = 0.5
        bm.glow_led_brighnesses.sleep = 0.1

        rgb = (100, 100, 100)
        bm.set_glow_leds(*rgb)

        now_s = 1234
        for interval, expected_phase in (
            (4, bm.DISPLAY_ON),
            (14, bm.DISPLAY_DIM),
            (24, bm.DISPLAY_SLEEP),
        ):

            bm.presto.set_led_rgb.reset_mock()

            last_interaction_s = now_s - interval
            bm.update_display_phase(now_s, last_interaction_s)
            assert bm.display_phase == expected_phase

            phase_brightness = bm.glow_led_brighnesses.for_phase(expected_phase)
            expected_rgb = [int(v * phase_brightness) for v in rgb]
            bm.presto.set_led_rgb.assert_called_with(6, *expected_rgb)

    def test_when_glow_led_control_disabled_then_leds_not_updated(self):

        bm = BacklightManager()
        bm.presto = mock.Mock()
        bm.presto.set_led_rgb = mock.Mock()
        bm.display_phase_controls_glow_leds = False
        bm.display_timeouts.dim = 10
        bm.display_timeouts.sleep = 20

        rgb = (100, 100, 100)
        bm.set_glow_leds(*rgb)

        now_s = 1234
        for interval, expected_phase in (
            (4, bm.DISPLAY_ON),
            (14, bm.DISPLAY_DIM),
            (24, bm.DISPLAY_SLEEP),
        ):

            bm.presto.set_led_rgb.reset_mock()

            last_interaction_s = now_s - interval
            bm.update_display_phase(now_s, last_interaction_s)
            assert bm.display_phase == expected_phase
            bm.presto.set_led_rgb.assert_not_called()


class Test_BacklightManager_tick:

    def test_when_wake_consumes_touch_then_state_false_after_update(
        self, mock_presto_module, monkeypatch
    ):
        self.__test_touch_handling(True, mock_presto_module, monkeypatch)

    def test_when_wake_doesnt_consumes_touch_then_state_true_after_update(
        self, mock_presto_module, monkeypatch
    ):
        self.__test_touch_handling(False, mock_presto_module, monkeypatch)


    def __test_touch_handling(self, should_consume, mock_presto_module, monkeypatch):

        bm = BacklightManager()
        bm.display_wake_consumes_touch = should_consume

        bm.presto = mock_presto_module.Presto()

        # Mock the effect of poll to simulate the touch ending

        def reset_touch():
            bm.presto.touch.state = False

        monkeypatch.setattr(
            bm.presto.touch.poll,
            "side_effect",
            reset_touch,
        )

        dim_timeout = 5
        time_now = 1234 * 1e6

        bm.display_timeouts.dim = dim_timeout
        bm.display_timeouts.sleep = 0

        # Call tick with a touch (ensure last time and initial state)
        bm.presto.touch.state = True
        bm.tick(time_now)
        assert bm.display_phase is bm.DISPLAY_ON

        # Call within the timeout and make sure it's not consumed as no
        # change has occurred.

        bm.presto.touch.poll.reset_mock()

        bm.presto.touch.state = True
        time_now += (dim_timeout - 1) * 1e6
        bm.tick(time_now)
        assert bm.display_phase is bm.DISPLAY_ON
        assert bm.presto.touch.state is True
        bm.presto.touch.poll.assert_not_called()

        # Call without a touch to allow the phase to change to dim

        bm.presto.touch.state = False
        time_now += (dim_timeout + 1) * 1e6
        bm.tick(time_now)
        assert bm.display_phase is bm.DISPLAY_DIM
        bm.presto.touch.poll.assert_not_called()

        # Call again later, with a touch to wake and check if it was
        # consumed and the state changed.

        bm.presto.touch.state = True
        time_now += 1 * 1e6
        bm.tick(time_now)
        assert bm.display_phase is bm.DISPLAY_ON
        if should_consume:
            bm.presto.touch.poll.assert_called_once()
            assert bm.presto.touch.state is False
        else:
            bm.presto.touch.poll.assert_not_called()
            assert bm.presto.touch.state is True
