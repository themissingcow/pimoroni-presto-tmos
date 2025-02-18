> [!NOTE]
> This project is entirely independent of the lovely folks at Pimoroni.
> With their permission, the brand is in the repo name to help make it
> easier to find, it does not imply any official endorsement.

# TmOS

A basic single-tasking "OS" for the [Pimoroni Presto](https://shop.pimoroni.com/products/presto).

It hopes to simplify writing simple interactive applications based
around paged displays of information.

## Features

- [x] RTC clock sync (requires WiFI)
- [x] Glow LED setup
- [x] Message handers
- [x] Task execution with adjustable update frequency
  - [x] Touches cause immediate updates (optional)
- [x] Timeout based display backlight / Glow LED dimming and sleep
- [ ] Page-based window manager
  - [x] Programmatic page navigation
  - [x] Basic buttons with event callbacks
  - [ ] Tabbed UI for page switching
  - [ ] Brightness controls
  - [ ] Clock

## Getting started

> [!CAUTION]
> This project is in its early days and is subject to breaking changes.

1. Upload [tmos.py](src/tmos.py) to your Presto (and
   [tmos_ui.py](src/tmos_ui.py) if you want the window manager/themes).
2. If you want to use WiFI, configure
   [`secrets.py`](https://github.com/pimoroni/pimoroni-pico/blob/main/micropython/examples/pico_wireless/secrets.py) accordingly.
3. Create an instance of `tmos.OS`.
4. Configure as desired, and register one or more tasks to run.
5. `boot` the with `run=True`.

The following example shows how to setup the Presto with  Wifi, sync the
RTC clock using NTP, and update the display every second with the
current time. The display backlight will dim after a while, and sleep
some time later. Touching the screen wakes the display.

```python
import time
from tmos import OS

os = OS()

WHITE = os.presto.display.create_pen(255, 255, 255)
BLACK = os.presto.display.create_pen(0, 0, 0)

os.presto.display.set_font("bitmap8")

def clock():
    """
    Draw the current time at the top left.
    """
    display = os.presto.display

    display.set_pen(WHITE)
    display.clear()
    display.set_pen(BLACK)

    year, month, day, hours, mins, secs, _, __ = time.localtime()
    display.text(
        f"{day:02d}/{month:02d}/{year} {hours:02d}:{mins:02d}:{secs:02d}", 10, 10
    )

    os.presto.update()

os.add_task(clock, execution_frequency=1)
os.boot(wifi=True, use_ntp=True, run=True)
```

See the [examples](examples) more.
