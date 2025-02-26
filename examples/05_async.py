# SPDX-License-Identifier: MIT
"""
An example of registering an async task with the OS.
"""

import asyncio

import time

import tmos


os = tmos.OS()

WHITE = os.presto.display.create_pen(255, 255, 255)
BLACK = os.presto.display.create_pen(0, 0, 0)

os.presto.display.set_font("bitmap8")

times_slept = 0


def display_draw_time():
    """ """
    display = os.presto.display

    display.set_pen(WHITE)
    display.clear()
    display.set_pen(BLACK)

    # Show the update time, so its easier to see the effect of blocking
    # tasks.
    display.text(f"Update @ {time.ticks_ms()}", 10, 10)
    display.text(f"Times slept: {times_slept}", 10, 30)

    os.presto.update()


async def sleeepy():
    # Simulate doing something await-able that would otherwise block
    # updates or touch handling.
    await asyncio.sleep(0.5)
    global times_slept
    times_slept += 1


os.add_task(display_draw_time, execution_frequency=10)

# async functions can be added as normal, and will be scheduled as
# a task on the main run loop. The OS yields between each task
# invocation. Beware, this is cooperative multitasking, you need to
# ensure your async task awaits something, otherwise it will block just
# like a normal synchronous function.
os.add_task(sleeepy, execution_frequency=0.5)

os.boot(run=True)

## or:
# os.boot()
# asyncio.run(os.run_async())
