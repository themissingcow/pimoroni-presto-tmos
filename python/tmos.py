# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
The Missing "OS"

A basic single-tasking OS for the wonderful Pimoroni Presto, that aims
to simplify making simple 'page' based apps.

It allows tasks to be scheduled, and run at varying frequencies to avoid
redundant updates.

This is kept as a single-file module for ease of deployment.
"""

import ntptime
import time

from plasma import WS2812
from presto import Presto, Buzzer


__all__ = [
    "OS",
]


class OS:
    """
    A minimal, single-tasking os, that takes care of basic hardware
    initialisation and management, along with the main run loop.
    """

    MSG_DEBUG = 0
    MSG_INFO = 1
    MSG_WARNING = 2
    MSG_FATAL = 3

    MSG_SEVERITY_NAMES = ("DEBUG", "INFO", "WARNING", "FATAL")

    #
    # Hardware access
    #

    presto: Presto
    buzzer: Buzzer
    glow_leds: WS2812

    #
    # Platform hardware config
    #

    __BUZZER_PIN = 43
    __GLOW_LED_PIN = 33
    __GLOW_LED_COUNT = 7

    class Task:
        """
        Represents a task in the task list. Tracks last run, and the
        requested run interval.
        """

        def __init__(self, fn, run_interval_us: int) -> None:
            self.fn = fn
            self.run_interval_us = run_interval_us
            # Use None, to avoid and edge cases when values wrap, etc.
            self.last_run_us = None

    #
    # Internal state
    #
    __message_handlers: []
    __tasks: []
    __running = False

    __tasks_min_intervals_us = []
    __tasks_last_run_us = []

    def __init__(self, *args, **kwarg) -> None:
        """
        Sets up the base Presto instance. At this point, none of the
        additional hardware is configured. The Presto instance in the
        presto attribute can be used for pen creation etc.

        Any args/kwargs are forwarded to the Presto constructor.
        """
        self.__message_handlers = []
        self.__tasks = []
        self.presto = Presto(*args, **kwarg)

    def boot(
        self,
        wifi: bool = False,
        use_ntp: bool = False,
        glow_leds: bool = False,
        glow_fps: int | None = None,
        run: bool = False,
    ):
        """
        Sets up the hardware to be ready for use, and optionally starts
        the run loop (@see run)

        Exceptions during boot will be logged to any registered message
        handlers (@see add_message_handler).

        :param wifi: When True, attempts to connect using secrets.py
        :param use_ntp: When True syncs the RTC to the current time
          using NTP (requires wifi).
        :param glow_leds: WHen True, creates a plasma instance to manage
          the glow LEDs, and starts it running.
        :param glow_fps: Specifies the update frequency for the Glow
          LEDs, if omitted, the plasma defaults for start are used.
        :param run: When True, the run loop will be started (@see run)
        :raises RuntimeError: If use_ntp is requested without wifi.
        """
        try:
            self.post_message("Initialising Buzzer")
            self.buzzer = Buzzer(self.__BUZZER_PIN)

            if glow_leds:
                self.post_message("Initialising Glow LEDs")
                self.glow_leds = WS2812(
                    self.__GLOW_LED_COUNT, 0, 0, self.__GLOW_LED_PIN
                )
                self.glow_leds.start(glow_fps)
            else:
                self.glow_leds = None

            if wifi:
                self.__setup_network(use_ntp)
            elif use_ntp:
                raise RuntimeError("use_ntp set without wifi")

        except Exception as ex:  # pylint: disable=broad-except
            self.post_message(str(ex), self.MSG_FATAL)
            raise ex

        if run:
            self.run()

    def run(self):
        """
        Starts the main run loop, executing registered tasks.
        This runs in the main MicroPython thread, and so is a blocking
        call. The runloop can be stopped by calling stop from another
        thread or within a task.

        Exceptions thrown by any task will halt execution and also be
        logged to the registered message handlers.
        """
        self.post_message("Starting tasks")
        try:
            self.__running = True
            while self.__running:
                self.__tick()
        except Exception as ex:  # pylint: disable=broad-except
            self.post_message(str(ex), self.MSG_FATAL)
            raise ex
        self.post_message("System stopped")

    def stop(self):
        """
        Stops the runloop, the run function will then return.
        """
        self.__running = False

    def add_message_handler(self, handler):
        """
        Adds a handler that will be called with any OS messages.
        Handlers are called in the order of registration. Exceptions
        raised in a handler will be silently suppressed to ensure other
        handlers continue to run.

        No checks are made to ensure the handler hasn't already been
        registered.

        :param handler: A callable that will be invoked for each message.
        :type handler: Callable[[str, int], None]
        """
        self.post_message(f"Adding message handler: {handler}", self.MSG_DEBUG)
        self.__message_handlers.append(handler)

    def remove_message_handler(self, handler):
        """
        Remove a previously registered message handler.

        :param handler: A previously registered handler.
        :type handler: Callable[[str, int], None]
        """
        self.__message_handlers.remove(handler)
        self.post_message(f"Removed message handler: {handler}", self.MSG_DEBUG)

    def post_message(self, msg: str, severity: int = MSG_INFO):
        """
        Post a message to any registered handlers.

        :param msg: A text message, may contain multiple lines.
        :param severity: One of the OS.MSG_* severity constants.
        """
        for handler in self.__message_handlers:
            # As we report fatal errors via the messaging system, we
            # don't want a faulty handler to interrupt the reporting of
            # the message.
            try:
                handler(msg, severity)
            except Exception:  # pylint: disable=broad-except
                pass

    def add_task(self, fn, index: int = -1, update_frequency: int | None = None):
        """
        Adds a task to be run during each cycle of the run loop.

        No checks are made to determine if the task is already in the
        list, and subsequent additions will cause the task to be run
        multiple times.

        :param fn: A callable to be invoked in the run loop.
        :type fn: Callable[[], None]
        :param index: The index in the list of tasks to insert the task.
        :param update_frequency: The preferred update rate (Hz) for the
          task. If omitted, it will be called each tick, otherwise it
          will be called at the requested frequency (or slower).
        """
        if update_frequency is not None and update_frequency <= 0:
            raise ValueError(f"update_frequency must be > 0 ({update_frequency})")

        run_interval_us = int(1e6 // update_frequency) if update_frequency else -1
        task = OS.Task(fn, run_interval_us)

        if index < 0:
            self.__tasks.append(task)
        else:
            self.__tasks.insert(index, task)

        self.post_message(
            f"Added task: {fn} (index {index}, interval: {run_interval_us})",
            self.MSG_DEBUG,
        )

    def remove_task(self, fn):
        """
        Removes a previously registered task from the run loop.

        An exception will be raised if the task is not in the task list.

        :param fn: A previously registered task callable.
        :type fn: Callable[[], None]
        """
        self.__tasks = [t for t in self.__tasks if t.fn is not fn]
        self.post_message(f"Removed task: {fn}", self.MSG_DEBUG)

    def tasks(self) -> [Task]:
        """
        Returns the current task list, task properties can be modified,
        but add_task or remove_task should be used to modify the list
        itself.

        :returns: A list of tasks as OS.Task instances.
        """
        return tuple(self.__tasks)

    def __setup_network(self, use_ntp: bool):
        """
        Initialises the network, and optionally updates the RTC using
        NTP.
        """
        self.post_message("Connecting to WiFI")
        try:
            self.presto.connect()
            if use_ntp:
                self.post_message("Setting time")
                ntptime.settime()
        except Exception as ex:  # pylint: disable=broad-except
            self.post_message(str(ex), self.MSG_FATAL)
            raise ex

    def __tick(self):
        """
        The main run loop function. Called indefinitely from run, whilst
        self.__running is True. Call stop to, well, stop.

        It will attempt to run tasks at their requested frequency, if
        load is high, they may be late, but they will never be scheduled
        faster than the indicated rate.

        This is responsible for executing all tasks, and any other
        housekeeping required by the OS.
        """

        self.presto.touch.poll()

        time_now_us = time.ticks_us()
        for task in self.__tasks:
            if not self.__task_should_run(task, time_now_us):
                continue
            task.last_run_us = time_now_us
            task.fn()

    @staticmethod
    def __task_should_run(task: Task, time_now_us: int) -> bool:
        """
        Determines if the task should run based on the current time and
        its last invocation.
        """
        if task.last_run_us is None:
            return True
        return time.ticks_diff(time_now_us, task.last_run_us) >= task.run_interval_us
