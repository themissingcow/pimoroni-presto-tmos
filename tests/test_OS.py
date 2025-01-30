# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for the OS implementation. Designed to run off-platform, they
focus on the specifics of the business logic and advertised
functionality.
"""

from unittest import mock

import pytest

from tmos import OS

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name


class Test_OS_init:

    def test_when_constructed_then_presto_is_initialised(self, mock_presto_module):
        os_instance = OS()
        assert os_instance.presto is mock_presto_module.Presto.return_value
        mock_presto_module.Presto.assert_called_once()

    def test_when_called_with_args_then_presto_is_initialised_with_args(
        self, mock_presto_module
    ):
        expected_args = (1, 2, "a", "b")
        expected_kwargs = {"d": 1, "e": "2"}
        OS(*expected_args, **expected_kwargs)
        mock_presto_module.Presto.assert_called_once_with(
            *expected_args, **expected_kwargs
        )


class Test_OS_boot:

    def test_when_called_with_default_args_then_only_buzzer_initialized(
        self, mock_presto_module, mock_plasma_module, mock_ntptime_module
    ):
        os_instance = OS()
        os_instance.boot()
        assert os_instance.buzzer is mock_presto_module.Buzzer.return_value
        # Glow LEDs - no
        assert os_instance.glow_leds is None
        mock_plasma_module.WS2812.assert_not_called()
        # WiFI - no
        mock_presto_module.Presto.return_value.connect.assert_not_called()
        # ntptime - no
        mock_ntptime_module.settime.assert_not_called()

    def test_when_called_with_wifi_true_then_connect_called_and_not_ntp(
        self, mock_presto_module, mock_ntptime_module
    ):
        os_instance = OS()
        os_instance.boot(wifi=True)
        # Wifi - yes
        mock_presto_module.Presto.return_value.connect.assert_called_once()
        # ntptime - no
        mock_ntptime_module.settime.assert_not_called()

    def test_when_called_with_wifi_and_use_ntp_true_then_connect_and_settime_called(
        self, mock_presto_module, mock_ntptime_module
    ):
        os_instance = OS()
        os_instance.boot(wifi=True, use_ntp=True)
        # Wifi - yes
        mock_presto_module.Presto.return_value.connect.assert_called_once()
        # ntptime - yes
        mock_ntptime_module.settime.assert_called_once()

    def test_when_called_with_wifi_fasle_and_use_ntp_true_then_RuntimeError_raised(
        self,
    ):
        os_instance = OS()
        with pytest.raises(RuntimeError):
            os_instance.boot(wifi=False, use_ntp=True)

    def test_when_called_with_glow_leds_then_plasma_configured_and_started_with_no_fps(
        self, mock_plasma_module
    ):
        os_instance = OS()
        os_instance.boot(glow_leds=True)
        assert os_instance.glow_leds is mock_plasma_module.WS2812.return_value
        os_instance.glow_leds.start.assert_called_once_with(None)

    def test_when_called_with_run_then_run_loop_started(self):

        os_instance = OS()

        mock_task = mock.MagicMock()
        mock_task.side_effect = os_instance.stop

        os_instance.add_task(mock_task)
        os_instance.boot(run=True)

        mock_task.assert_called_once()

    def test_when_called_with_glow_leds_then_plasma_configured_and_started_with_requested_fps(
        self, mock_plasma_module
    ):
        expected_num_leds = 7
        expected_led_pin = 33
        expected_fps = 27
        os_instance = OS()
        os_instance.boot(glow_leds=True, glow_fps=expected_fps)
        assert os_instance.glow_leds is mock_plasma_module.WS2812.return_value
        mock_plasma_module.WS2812.assert_called_once_with(
            expected_num_leds, 0, 0, expected_led_pin
        )
        os_instance.glow_leds.start.assert_called_once_with(expected_fps)

    def test_when_exception_raised_during_boot_then_message_hander_called(
        self, mock_presto_module, monkeypatch
    ):
        # Make connect raise an exception when we boot with wifi

        class TestException(AttributeError):
            """Verify it is the specific exception we threw"""

        test_exception = TestException("test")
        monkeypatch.setattr(
            mock_presto_module.Presto.return_value.connect,
            "side_effect",
            test_exception,
        )

        os_instance = OS()

        mock_handler = mock.MagicMock()
        os_instance.add_message_handler(mock_handler)

        with pytest.raises(TestException, match=str(test_exception)):
            os_instance.boot(wifi=True)

        mock_handler.assert_called_with(str(test_exception), OS.MSG_FATAL)


class Test_OS_messageHandlers:

    def test_when_hander_added_then_called_with_severity_and_msg(self):

        os_instance = OS()

        mock_handler = mock.MagicMock()
        os_instance.add_message_handler(mock_handler)

        expected_messages = (
            ("I'm a debug message with 🐟 unicode", OS.MSG_DEBUG),
            ("I'm an info message with 🐟 unicode", OS.MSG_INFO),
            ("I'm a warning message with 🐟 unicode", OS.MSG_WARNING),
            ("I'm a fatal message with 🐟 unicode", OS.MSG_FATAL),
        )

        calls = [mock.call(*a) for a in expected_messages]

        for msg, severity in expected_messages:
            os_instance.post_message(msg, severity)

        mock_handler.assert_has_calls(calls)

    def test_when_hander_removed_then_no_longer_called(self):

        os_instance = OS()

        mock_handler = mock.MagicMock()
        os_instance.add_message_handler(mock_handler)

        os_instance.post_message("msg")
        mock_handler.assert_called_once()

        os_instance.remove_message_handler(mock_handler)
        os_instance.post_message("msg2")
        mock_handler.assert_called_once()

    def test_when_multiple_handers_added_then_called_in_order_added(self):

        os_instance = OS()

        calls = []

        # Ignore debug messages as the OS logs message handler manipulation

        def handler_one(_, severity):
            if severity > OS.MSG_DEBUG:
                calls.append(1)

        def handler_two(_, severity):
            if severity > OS.MSG_DEBUG:
                calls.append(2)

        os_instance.add_message_handler(handler_one)
        os_instance.add_message_handler(handler_two)
        os_instance.post_message("msg", OS.MSG_INFO)

        assert calls == [1, 2]

    def test_when_handler_raises_then_no_exception_and_other_handlers_called(self):

        os_instance = OS()

        calls = []

        def handler_one(_, severity):
            raise RuntimeError()

        def handler_two(_, __):
            calls.append(2)

        os_instance.add_message_handler(handler_one)
        os_instance.add_message_handler(handler_two)
        os_instance.post_message("msg", OS.MSG_INFO)

        assert calls == [2]

    def test_when_no_severity_supplied_to_post_message_then_info_is_used(self):

        os_instance = OS()

        mock_handler = mock.MagicMock()
        os_instance.add_message_handler(mock_handler)

        os_instance.post_message("msg")

        mock_handler.assert_called_once_with("msg", OS.MSG_INFO)


class Test_OS_run:
    def test_when_multiple_tasks_added_with_no_index_then_called_in_order_added(self):

        os_instance = OS()

        calls = []

        def task_one():
            calls.append(1)

        def task_two():
            calls.append(2)
            os_instance.stop()

        os_instance.add_task(task_one)
        os_instance.add_task(task_two)

        os_instance.run()

        assert calls == [1, 2]

    def test_when_tasks_added_with_index_then_call_order_reflects_index(self):

        os_instance = OS()

        calls = []

        def task_one():
            calls.append(1)
            os_instance.stop()

        def task_two():
            calls.append(2)

        os_instance.add_task(task_one)
        os_instance.add_task(task_two, index=0)

        os_instance.run()

        assert calls == [2, 1]

    def test_when_task_removed_then_not_called(self):

        os_instance = OS()

        calls = []

        def task_one():
            calls.append(1)

        def task_two():
            calls.append(2)
            os_instance.stop()

        os_instance.add_task(task_one)
        os_instance.add_task(task_two)
        os_instance.remove_task(task_one)

        os_instance.run()

        assert calls == [2]

    def test_when_task_raises_exception_then_message_posted_and_exception_raised(self):

        os_instance = OS()

        class TestException(RuntimeError):
            """Ensures we catch our specific exception"""

        expected_exception = TestException("test")

        def task():
            raise expected_exception

        os_instance.add_task(task)

        mock_hander = mock.Mock()
        os_instance.add_message_handler(mock_hander)

        with pytest.raises(TestException, match=str(expected_exception)):
            os_instance.run()

        mock_hander.assert_called_with(str(expected_exception), OS.MSG_FATAL)

    def test_when_stop_called_run_loop_terminates(self):

        os_instance = OS()

        mock_task = mock.MagicMock()
        mock_task.side_effect = os_instance.stop

        os_instance.add_task(mock_task)
        os_instance.run()

        mock_task.assert_called_once()
