# SPDX-License-Identifier: MIT
"""
A minimal example of using the OS class to set up the hardware and run a
task in a continuous loop. It takes advantage of the OS's update
frequency for tasks, to only redraw the clock once every second.
"""

import time

import tmos


os = tmos.OS()

# Use a short timeout for the display to demonstrate screen dimming, set
# the timeout to 0 to disable.
os.backlight_manager.display_timeouts.dim = 5
os.backlight_manager.display_timeouts.sleep = 20

WHITE = os.presto.display.create_pen(255, 255, 255)
BLACK = os.presto.display.create_pen(0, 0, 0)

os.presto.display.set_font("bitmap8")


def clock():
    """
    Draws the current date/time in the top-left.
    """

    os.backlight_manager.set_glow_leds(255, 255, 255)

    display = os.presto.display

    display.set_pen(WHITE)
    display.clear()
    display.set_pen(BLACK)

    year, month, day, hours, mins, secs, _, __ = time.localtime()
    display.text(
        f"{day:02d}/{month:02d}/{year} {hours:02d}:{mins:02d}:{secs:02d}", 10, 10
    )

    # Show the update time, so its easier to see the effect of
    # execution_frequency when the task is registered.
    display.text(f"Update @ {time.ticks_ms()}", 10, 30)

    os.presto.update()


# Add out function to display the time as a task, so it will be called
# each time the run loop runs. We specify an execution_frequency of 1 so
# it will only be invoked every second, to save unnecessary updates.
os.add_task(clock, execution_frequency=1)

# Enable WiFI and NTP so we have the correct time, start the run loop as
# everything else is configured.
os.boot(wifi=True, use_ntp=True, glow_leds=True, run=True)
