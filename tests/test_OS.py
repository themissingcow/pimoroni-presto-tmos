# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for the OS implementation. Designed to run off-platform, they
focus on the specifics of the business logic and advertised
functionality.
"""

import asyncio

import time

from unittest import mock

import pytest

from tmos import OS, Region, MSG_FATAL, MSG_WARNING, MSG_INFO, MSG_DEBUG

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name


class Test_OS_init:

    def test_when_constructed_then_presto_is_initialised(self, mock_presto_module):
        os_instance = OS()
        assert os_instance.presto is mock_presto_module.Presto.return_value
        mock_presto_module.Presto.assert_called_once()

    def test_when_called_with_args_then_presto_is_initialised_with_args(self, mock_presto_module):
        expected_args = (1, 2, "a", "b")
        expected_kwargs = {"d": 1, "e": "2"}
        OS(*expected_args, **expected_kwargs)
        mock_presto_module.Presto.assert_called_once_with(*expected_args, **expected_kwargs)

    def test_when_ambient_light_not_in_kwarg_then_glow_led_control_enabled(self):

        os_instance = OS()
        assert os_instance.backlight_manager.display_phase_controls_glow_leds is True

    def test_when_ambient_light_false_in_kwarg_then_glow_led_control_enabled(self):

        os_instance = OS(ambient_light=False)
        assert os_instance.backlight_manager.display_phase_controls_glow_leds is True

    def test_when_ambient_light_true_in_kwarg_then_glow_led_control_disabled(self):

        os_instance = OS(ambient_light=True)
        assert os_instance.backlight_manager.display_phase_controls_glow_leds is False


class Test_OS_boot:

    def test_when_called_with_default_args_then_only_buzzer_initialized(
        self, mock_presto_module, mock_ntptime_module
    ):
        os_instance = OS()
        os_instance.boot()
        assert os_instance.buzzer is mock_presto_module.Buzzer.return_value
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

    def test_when_called_with_run_then_run_loop_started(self):

        os_instance = OS()

        mock_task = mock.MagicMock()
        mock_task.side_effect = os_instance.stop

        os_instance.add_task(mock_task)
        os_instance.boot(run=True)

        mock_task.assert_called_once()

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

        mock_handler.assert_called_with(str(test_exception), MSG_FATAL)


class Test_OS_messageHandlers:

    def test_when_hander_added_then_called_with_severity_and_msg(self):

        os_instance = OS()

        mock_handler = mock.MagicMock()
        os_instance.add_message_handler(mock_handler)

        assert mock_handler in os_instance.message_handlers()

        expected_messages = (
            ("I'm a debug message with 🐟 unicode", MSG_DEBUG),
            ("I'm an info message with 🐟 unicode", MSG_INFO),
            ("I'm a warning message with 🐟 unicode", MSG_WARNING),
            ("I'm a fatal message with 🐟 unicode", MSG_FATAL),
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
        assert mock_handler not in os_instance.message_handlers()

        os_instance.post_message("msg2")
        mock_handler.assert_called_once()

    def test_when_multiple_handers_added_then_called_in_order_added(self):

        os_instance = OS()

        calls = []

        # Ignore debug messages as the OS logs message handler manipulation

        def handler_one(_, severity):
            if severity > MSG_DEBUG:
                calls.append(1)

        def handler_two(_, severity):
            if severity > MSG_DEBUG:
                calls.append(2)

        expected_handlers = (*os_instance.message_handlers(), handler_one, handler_two)

        os_instance.add_message_handler(handler_one)
        os_instance.add_message_handler(handler_two)
        os_instance.post_message("msg", MSG_INFO)

        assert os_instance.message_handlers() == expected_handlers
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
        os_instance.post_message("msg", MSG_INFO)

        assert calls == [2]

    def test_when_no_severity_supplied_to_post_message_then_info_is_used(self):

        os_instance = OS()

        mock_handler = mock.MagicMock()
        os_instance.add_message_handler(mock_handler)

        os_instance.post_message("msg")

        mock_handler.assert_called_once_with("msg", MSG_INFO)


class Test_OS_run:

    def test_when_runloop_ticks_then_touch_poll_is_called(self):

        os_instance = OS()

        touch_poll = mock.Mock()
        os_instance.presto.touch.poll = touch_poll

        num_calls = 10
        calls = []

        def task():
            calls.append(time.ticks_us())
            if len(calls) == num_calls:
                os_instance.stop()

        os_instance.add_task(task)
        os_instance.run()

        assert len(touch_poll.mock_calls) == num_calls

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

    def test_when_task_not_active_then_not_called(self):

        os_instance = OS()

        calls = []

        def task_one():
            calls.append(1)

        def task_two():
            calls.append(2)
            os_instance.stop()

        t1 = os_instance.add_task(task_one)
        os_instance.add_task(task_two)
        t1.active = False

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

        mock_hander.assert_called_with(str(expected_exception), MSG_FATAL)

    def test_when_stop_called_run_loop_terminates(self):

        os_instance = OS()

        mock_task = mock.MagicMock()
        mock_task.side_effect = os_instance.stop

        os_instance.add_task(mock_task)
        os_instance.run()

        mock_task.assert_called_once()


class Test_OS_run_async:

    def test_is_awaitable(self):
        os_instance = OS()
        os_instance.add_task(os_instance.stop)
        asyncio.new_event_loop().run_until_complete(os_instance.run_async())


class Test_OS_active:

    def test_when_task_made_active_then_last_execution_time_reset(self):

        expected_fn = mock.Mock()
        os_instance = OS()
        task = os_instance.add_task(expected_fn)
        task.last_execution_us = 1
        task.active = True
        assert task.last_execution_us is None


class Test_OS_tasks:

    def test_when_task_added_then_task_object_returned_referencing_fn(self):

        expected_fn = mock.Mock()
        os_instance = OS()
        task = os_instance.add_task(expected_fn)
        assert isinstance(task, OS.Task)
        assert task.fn is expected_fn

    def test_when_task_added_then_in_task_list(self):

        os_instance = OS()
        task = os_instance.add_task(mock.Mock())
        assert os_instance.tasks() == (task,)

    def test_when_task_removed_with_fn_then_removed_from_task_list(self):

        task_fn = mock.Mock()
        os_instance = OS()
        task = os_instance.add_task(task_fn)
        assert os_instance.tasks() == (task,)
        os_instance.remove_task(task_fn)
        assert os_instance.tasks() == tuple()

    def test_when_task_removed_with_task_instance_then_removed_from_task_list(self):

        os_instance = OS()
        task = os_instance.add_task(mock.Mock())
        assert os_instance.tasks() == (task,)
        os_instance.remove_task(task)
        assert os_instance.tasks() == tuple()

    def test_when_returned_task_modified_then_task_updated(self):

        os_instance = OS()
        os_instance.add_task(mock.Mock())

        tasks = os_instance.tasks()
        assert tasks[0].execution_interval_us == -1

        new_interval = 1e6 / 10
        tasks[0].execution_interval_us = new_interval
        assert os_instance.tasks()[0].execution_interval_us == new_interval


class Test_OS_run_execution_frequency:

    def test_when_task_added_with_no_execution_frequency_then_interval_is_minus_one(
        self,
    ):

        os_instance = OS()

        mock_task = mock.Mock()
        task = os_instance.add_task(mock_task)

        assert task.fn is mock_task
        assert task.last_execution_us is None
        assert task.execution_interval_us == -1

    def test_when_task_added_with_valid_execution_frequency_then_interval_calculated(
        self,
    ):

        frequency = 4
        expected_interval_us = 1e6 // 4

        os_instance = OS()
        mock_task = mock.Mock()
        task = os_instance.add_task(mock_task, execution_frequency=frequency)

        assert task.execution_interval_us == expected_interval_us

    def test_when_task_added_with_execution_frequency_zero_then_interval_is_none(self):

        os_instance = OS()
        mock_task = mock.Mock()
        task = os_instance.add_task(mock_task, execution_frequency=0)

        assert task.execution_interval_us is None

    def test_when_task_added_with_invalid_execution_frequence_then_ValueError_raised(
        self,
    ):

        os_instance = OS()

        for invalid_hz in (-12.4, -1):
            with pytest.raises(ValueError):
                os_instance.add_task(mock.Mock(), execution_frequency=invalid_hz)

    def test_when_task_has_execution_frequency_and_ignores_touch_then_run_respects_interval(
        self,
    ):

        frequency = 5
        expected_interval_us = int(1e6 // frequency)
        num_calls = 3

        call_times = []

        def task():
            call_times.append(time.ticks_us())
            if len(call_times) == num_calls:
                os_instance.stop()

        os_instance = OS()

        # simulate a touch
        os_instance.presto.touch.state = True

        task = os_instance.add_task(
            task, execution_frequency=frequency, touch_forces_execution=False
        )
        assert task.execution_interval_us == expected_interval_us
        assert task.touch_forces_execution is False

        os_instance.run()

        # Check the last run entry is close enough to the call time we logged
        assert abs(task.last_execution_us - call_times[-1]) < 100
        # Check call intervals are close enough
        self.__check_intervals(call_times, expected_interval_us, 0.1)

        os_instance.presto.touch.state = False

    def test_when_task_has_execution_frequency_zero_and_ignores_touch_then_run_once(
        self,
    ):

        num_calls = 3

        call_times = []
        control_call_times = []

        def task_fn():
            call_times.append(time.ticks_us())

        def control_task_fn():
            control_call_times.append(time.ticks_us())
            if len(control_call_times) == num_calls:
                os_instance.stop()

        os_instance = OS()

        # simulate a touch
        os_instance.presto.touch.state = True

        task = os_instance.add_task(task_fn, execution_frequency=0, touch_forces_execution=False)
        control_task = os_instance.add_task(
            control_task_fn, execution_frequency=10, touch_forces_execution=False
        )
        assert task.execution_interval_us == None
        assert task.touch_forces_execution is False

        os_instance.run()

        assert len(call_times) == 1
        assert len(control_call_times) == num_calls

        os_instance.presto.touch.state = False

    def test_when_task_executes_on_touch_then_touch_affects_interval(self):

        frequency = 5
        expected_interval_us = int(1e6 // frequency)
        max_expected_touch_interval_us = 1e6 // (5 * frequency)
        num_calls = 7
        num_calls_in_touch = 3

        call_times = []

        os_instance = OS()

        def task():
            call_times.append(time.ticks_us())
            if len(call_times) == num_calls_in_touch:
                os_instance.presto.touch.state = False
            if len(call_times) == num_calls:
                os_instance.stop()

        task = os_instance.add_task(
            task, execution_frequency=frequency, touch_forces_execution=True
        )

        assert task.execution_interval_us == expected_interval_us
        assert task.touch_forces_execution

        # Simulate a touch
        os_instance.presto.touch.state = True

        os_instance.run()

        # Check the last run entry is close enough to the call time we logged
        assert abs(task.last_execution_us - call_times[-1]) < 100

        # Note: there is an additional call immediately after touch is
        # false ,to allow UIs to update. As such there will be
        # num_calls_in_touch + 1 at a high frequency.

        # Check touch intervals are suitably short
        with_touch = call_times[: num_calls_in_touch + 1]
        self.__check_intervals(with_touch, max_expected_touch_interval_us)

        # Check non-touch intervals are as expected from frequency
        without_touch = call_times[num_calls_in_touch:]
        self.__check_intervals(without_touch, expected_interval_us, 0.2)

    def test_when_task_execution_frequency_zero_and_executes_on_touch_then_touch_forces_execution(
        self,
    ):

        max_expected_touch_interval_us = 1e6 // 25
        num_calls = 7
        num_calls_in_touch = 3

        call_times = []
        control_call_times = []

        os_instance = OS()

        def task_fn():
            call_times.append(time.ticks_us())

        def control_task_fn():
            control_call_times.append(time.ticks_us())
            if len(control_call_times) == num_calls_in_touch:
                os_instance.presto.touch.state = False
            if len(control_call_times) == num_calls:
                os_instance.stop()

        task = os_instance.add_task(task_fn, execution_frequency=0, touch_forces_execution=True)
        os_instance.add_task(control_task_fn, execution_frequency=5, touch_forces_execution=True)

        assert task.execution_interval_us is None
        assert task.touch_forces_execution

        # Simulate a touch
        os_instance.presto.touch.state = True

        os_instance.run()

        # Note: there is an additional call immediately after touch is
        # false ,to allow UIs to update. As such there will be
        # num_calls_in_touch + 1 at a high frequency.

        assert len(call_times) == num_calls_in_touch + 1

        self.__check_intervals(call_times, max_expected_touch_interval_us)

    def test_when_touch_forces_execution_then_additional_high_freq_invocation_after_touch_up(self):

        os_instance = OS()

        execution_frequency = 5
        expected_interval = 1e6 // execution_frequency
        call_touch_states = []
        call_times = []
        num_calls = 3

        def task():
            call_touch_states.append(os_instance.touch.state)
            call_times.append(time.ticks_us())
            if os_instance.touch.state:
                os_instance.touch.state = False
            if len(call_times) == num_calls:
                os_instance.stop()

        os_instance.add_task(
            task, execution_frequency=execution_frequency, touch_forces_execution=True
        )
        os_instance.touch.state = True
        os_instance.run()

        intervals = self.__intervals(call_times)
        # Check we were called with the expected touch states
        assert call_touch_states == [True, False, False]
        # Check the initial interval was short (ie the first two calls
        # with True/False), less thank half the expected interval shows
        # that the scheduling was effectively immediate.
        assert intervals[0] < expected_interval // 2
        assert intervals[1] > expected_interval // 2

    def test_when_task_enqueued_then_runs_immediately(self):

        frequency = 5
        expected_interval_us = int(1e6 // frequency)
        num_calls = 3

        call_times = []

        os_instance = OS()

        task = None

        def task_fn():
            task.enqueue()
            call_times.append(time.ticks_us())
            if len(call_times) == num_calls:
                os_instance.stop()

        task = os_instance.add_task(task_fn, execution_frequency=frequency)

        os_instance.run()

        # Check intervals are suitably short
        self.__check_intervals(call_times, expected_interval_us // 2)

    @staticmethod
    def __intervals(call_times: [int]) -> [int]:
        return [b - a for a, b in zip(call_times[:-1], call_times[1:])]

    def __check_intervals(
        self, call_times: [int], expected_interval: int, tolerance: float = None
    ):
        """
        Checks the intervals between call_times are less than the
        expected_interval, or if a tolerance supplied (% as 0-1), then
        within that range.
        """
        intervals = self.__intervals(call_times)
        average_interval = sum(intervals) // (len(call_times) - 1)
        if tolerance is not None:
            difference = abs(1 - (average_interval / expected_interval))
            assert difference < tolerance
        else:
            assert average_interval < expected_interval


class Test_async_tasks:

    def test_when_async_function_registered_then_is_run(self):

        os_instance = OS()

        async def stop():
            os_instance.stop()

        os_instance.add_task(stop)
        # This would hang if it wasn't called
        os_instance.run()

    def test_when_async_task_executed_before_sync_task_then_does_not_block(self):

        os_instance = OS()

        calls = []

        def capture_tick():
            calls.append(True)

        async def stop_later():
            await asyncio.sleep(0.05)
            os_instance.stop()

        os_instance.add_task(stop_later)
        os_instance.add_task(capture_tick)
        os_instance.run()
        # If stop_later ran blocking the subsequent task, then we'd have
        # exactly one invocation of the capture task as stop would have
        # been called.
        assert len(calls) > 1


class Test_OS_update_display:

    def test_when_called_without_region_then_update_called(self):

        os_instance = OS()
        os_instance.presto.touch.state = True
        os_instance.update_display()
        os_instance.presto.presto.update.assert_called_with(os_instance.presto.display)
        assert os_instance.presto.touch.state
        os_instance.presto.touch.state = False

    def test_when_called_with_region_then_partial_update_called(self):

        expected_region = Region(1, 2, 3, 4)

        os_instance = OS()
        os_instance.presto.touch.state = True
        os_instance.update_display(expected_region)
        os_instance.presto.presto.partial_update.assert_called_once_with(
            os_instance.presto.display, *expected_region
        )

        assert os_instance.presto.touch.state
        os_instance.presto.touch.state = False
