# SPDX-License-Identifier: MIT
"""
A minimal example of using the OS class to set up the hardware and run a
task in a continuous loop.
"""

import time

import tmos


os = tmos.OS()

WHITE = os.presto.display.create_pen(255, 255, 255)
BLACK = os.presto.display.create_pen(0, 0, 0)


os.presto.display.set_font("bitmap8")


def clock():
    """
    Draws the current date/time in the top-left.
    """

    year, month, day, hours, mins, secs, _, __ = time.localtime()

    display = os.presto.display
    display.set_pen(WHITE)
    display.clear()
    display.set_pen(BLACK)
    display.text(
        f"{day:02d}/{month:02d}/{year} {hours:02d}:{mins:02d}:{secs:o2d}", 10, 10
    )
    os.presto.update()


# Add out function to display the time as a task, so it will be called
# each time the run loop runs.
os.add_task(clock)

# Enable WiFI and NTP so we have the correct time, start the run loop as
# everything else is configured.
os.boot(wifi=True, use_ntp=True, run=True)
