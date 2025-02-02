# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
The Missing "OS"

A basic single-tasking OS for the wonderful Pimoroni Presto, that aims
to simplify making simple 'page' based apps.

It allows tasks to be scheduled, and run at varying frequencies to avoid
redundant updates.

The full frequency run loop implements auto-dimming for the display and
glow LEDs. Configured through the backlight_manager property.

This is kept as a single-file module for ease of deployment.

The main orchestrator of the runtime is the 'OS' class. This manages
hardware initialisation, and coordinates task evaluation. It composes
functionality from other classes to add additional functionality:

- BacklightManager: Timeout-based backlight / glow LED dimming/sleep.

These are added in explicit order in the main run loop (__see tick),
around user specified tasks to ensure consistent order of operations and
state management.
"""

import ntptime
import time

from plasma import WS2812
import plasma
from presto import Presto, Buzzer
from picographics import PicoGraphics
from touch import FT6236


__all__ = [
    "BacklightManager",
    "OS",
    "MSG_DEBUG",
    "MSG_INFO",
    "MSG_WARNING",
    "MSG_FATAL",
    "MSG_SEVERITY_NAMES",
]

MSG_DEBUG = 0
MSG_INFO = 1
MSG_WARNING = 2
MSG_FATAL = 3

MSG_SEVERITY_NAMES = ("DEBUG", "INFO", "WARNING", "FATAL")


class BacklightManager:
    """
    A helper class that manages display/glow LED brightness based on
    a timeout since the last touch interaction with the device.

    It defines three distinct display "phases". Each phase has an
    associated timeout, and brightness values for the display and LEDs.

    LED control can be disabled if required, usually when a user process
    is directly controlling the LEDs. The LEDs on the presto don't
    support an independent brightness, and so the only way to implement
    this is by modifying the requested color. Consequently, there isn't
    a way to insert ourselves into any plasma updates implemented in
    user code.

    By default, the backlight manager consumes any touches that cause a
    display phase transition, this can be disabled by setting
    display_wake_consumes_touch to False.
    """

    presto: Presto = None
    glow_leds: WS2812 = None
    num_leds: int = 7

    DISPLAY_ON = "on"
    DISPLAY_DIM = "dim"
    DISPLAY_SLEEP = "sleep"

    class DisplayPhaseSetting:
        """Allows programmatic retrieval of values"""

        def for_phase(self, phase: str) -> float | int:
            """:returns: the value for the specified phase"""
            return getattr(self, phase)

    class BrightnessSettings(DisplayPhaseSetting):
        """Holds brightness settings for each display phase"""

        on = 1.0
        dim = 0.3
        sleep = 0

    class TimeoutSettings(DisplayPhaseSetting):
        """
        Holds timeout settings for each display phase, set to 0 to
        disable this phase. Dim should always be less than sleep.
        """

        dim = 30
        sleep = 600

    display_phase: str | None = None
    display_wake_consumes_touch = True
    display_phase_controls_glow_leds = True
    display_timeouts: TimeoutSettings
    display_brightnesses: BrightnessSettings
    glow_led_brighnesses: BrightnessSettings

    __requested_glow_led_rgb: tuple | None = None
    __last_interaction_us: int | None = None

    def __init__(self):
        """
        Sets the default brightneeses and timeouts, changes made to
        these will take effect at the next display update.
        """

        self.display_timeouts = self.TimeoutSettings()
        self.display_brightnesses = self.BrightnessSettings()
        self.glow_led_brighnesses = self.BrightnessSettings()

    def set_glow_leds(self, r, g, b):
        """
        Updates the Glow LEDS to the specified color. This method only
        allows simple uniform coloring. If you need anything more
        specific, or to use the auto ambient feature, then be sure to
        disable display_phase_controls_glow_leds.

        The Presto hardware doesn't support an independent brightness
        for the LEDs, so we simulate one by taking the requested
        brightness for the display phase, and multiplying the requested
        LED color.
        """
        if not self.glow_leds:
            return

        rgb = (r, g, b)

        self.__requested_glow_led_rgb = rgb

        if self.display_phase and self.display_phase_controls_glow_leds:
            brightness = self.glow_led_brighnesses.for_phase(self.display_phase)
            rgb = [int(v * brightness) for v in rgb]

        for i in range(self.num_leds):
            self.glow_leds.set_rgb(i, *rgb)

    def tick(self, time_now_us: int):

        if not self.presto:
            return

        if self.__last_interaction_us is None or self.presto.touch.state:
            self.__last_interaction_us = time_now_us

        changed = self.update_display_phase(time_now_us, self.__last_interaction_us)
        if changed and self.display_wake_consumes_touch:
            # Wait for the touch to end so that the current page won't
            # see it when its tick is called.
            while self.presto.touch.state:
                time.sleep_ms(5)
                self.presto.touch.poll()

    def update_display_phase(self, time_now_us: int, last_interaction_us: int) -> bool:
        """
        Updates the display phase based on the current time the last
        interaction time.

        The display backlight and/or glow LEDs will be updated if the
        presto/glow_leds have been suitably configured.

        :param time_now_us: The current time in microseconds.
        :param last_interaction_us: The last user interaction time in
          microseconds.
        :return: Whether the display phase changed.
        """

        in_initial_update = self.display_phase is None

        new_phase = self.__next_display_state(
            time_now_us, last_interaction_us, self.display_timeouts
        )

        if new_phase == self.display_phase:
            # Avoid redundant hardware updates as this always runs in
            # the high-frequency loop.
            return False

        self.display_phase = new_phase

        # Update the hardware state

        if self.presto:
            new_backlight_brightness = self.display_brightnesses.for_phase(new_phase)
            self.presto.set_backlight(new_backlight_brightness)

        if self.display_phase_controls_glow_leds and self.__requested_glow_led_rgb:
            self.set_glow_leds(*self.__requested_glow_led_rgb)

        # Ensure initial updates don't count as a state change
        # pylint: disable=simplifiable-if-expression
        return False if in_initial_update else True

    @staticmethod
    def __next_display_state(
        time_now_us: int, last_interaction_us: int, timeouts: TimeoutSettings
    ):
        """
        Calculates the updated display sate phase There are three
        states, on, dimmed and off. Triggered by a timeout since last
        touch. By default, touches that transition from a dimmed/off
        state are consumed. This can be turned off if required.
        """
        new_display_phase = BacklightManager.DISPLAY_ON

        delta_s = time.ticks_diff(time_now_us, last_interaction_us) // int(1e6)

        for phase in (BacklightManager.DISPLAY_SLEEP, BacklightManager.DISPLAY_DIM):

            timeout_s = timeouts.for_phase(phase)

            # If the timeout is 0, it means this mode is disabled
            if not timeout_s:
                continue

            if delta_s > timeout_s:
                new_display_phase = phase
                break

        return new_display_phase


class OS:
    """
    A minimal, single-tasking os, that takes care of basic hardware
    initialisation and management, along with the main run loop.
    """

    #
    # Hardware access
    #

    presto: Presto
    display: PicoGraphics
    touch: FT6236
    buzzer: Buzzer
    glow_leds: WS2812

    #
    # Backlight / Glow LED management
    #

    backlight_manager: BacklightManager

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

        Once constructed, you can configure the backlight_manager and
        other settings before booting. Backlight settings updated after
        boot will take effect at the next display phase transition.
        Timeout settings will take immediate effect.

        Any args/kwargs are forwarded to the Presto constructor.
        """
        self.__message_handlers = []
        self.__tasks = []

        self.presto = Presto(*args, **kwarg)

        self.backlight_manager = BacklightManager()
        self.backlight_manager.presto = self.presto

        # The auto ambient light subsystem will override anything we do
        # so disable glow led control if it has been requested.
        if kwarg.get("ambient_light", False):
            self.post_message(
                "Disabling display_phase_controls_glow_leds as ambient_light is set",
                MSG_DEBUG,
            )
            self.backlight_manager.display_phase_controls_glow_leds = False

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
                if glow_fps:
                    self.glow_leds.start(glow_fps)
                else:
                    self.glow_leds.start()
                self.backlight_manager.glow_leds = self.glow_leds
                self.backlight_manager.num_leds = self.__GLOW_LED_COUNT
            else:
                self.glow_leds = None

            if wifi:
                self.__setup_network(use_ntp)
            elif use_ntp:
                raise RuntimeError("use_ntp set without wifi")

        except Exception as ex:  # pylint: disable=broad-except
            self.post_message(str(ex), MSG_FATAL)
            raise ex

        if run:
            self.run()

    def run(self):
        """
        Starts the main run loop, executing registered tasks.
        This runs in the main MicroPython thread, and so is a blocking
        call. The run loop can be stopped by calling stop from another
        thread or within a task.

        Exceptions thrown by any task will halt execution and also be
        logged to the registered message handlers.

        The touch system will be polled at the start of each time around
        the run loop.
        """
        self.post_message("Starting tasks")
        try:
            self.__running = True
            while self.__running:
                self.__tick()
        except Exception as ex:  # pylint: disable=broad-except
            self.post_message(str(ex), MSG_FATAL)
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
        self.post_message(f"Adding message handler: {handler}", MSG_DEBUG)
        self.__message_handlers.append(handler)

    def remove_message_handler(self, handler):
        """
        Remove a previously registered message handler.

        :param handler: A previously registered handler.
        :type handler: Callable[[str, int], None]
        """
        self.__message_handlers.remove(handler)
        self.post_message(f"Removed message handler: {handler}", MSG_DEBUG)

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
            MSG_DEBUG,
        )

    def remove_task(self, fn):
        """
        Removes a previously registered task from the run loop.

        An exception will be raised if the task is not in the task list.

        :param fn: A previously registered task callable.
        :type fn: Callable[[], None]
        """
        self.__tasks = [t for t in self.__tasks if t.fn is not fn]
        self.post_message(f"Removed task: {fn}", MSG_DEBUG)

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
                # We seem to get timeouts frequently
                ntptime.timeout = 10
                ntptime.settime()
        except Exception as ex:  # pylint: disable=broad-except
            self.post_message(str(ex), MSG_FATAL)
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

        # Update the display before anything else, so we can consume the
        # touch event if we need to.
        self.backlight_manager.tick(time_now_us)

        # Run the users tasks
        self.__run_tasks(time_now_us)

    def __run_tasks(self, time_now_us: int):
        """
        Runs any tasks that are pending, based on their update
        frequency.
        """
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
