> [!NOTE]
> This project is entirely independent of the lovely folks at Pimoroni.
> With their permission, the brand is in the repo name to help make it
> easier to find, it does not imply any official endorsement.

# TmOS

A basic single-tasking "OS" for the [Pimoroni Presto](https://shop.pimoroni.com/products/presto).

It hopes to simplify writing simple interactive applications based
around paged displays of information.

It (currently) consists of a couple of single-file modules, to make deployment
to devices easier. That is starting to get a bit unmaintainable though
so it will be packaged up into `mip` at some point

## Features

- [x] RTC clock sync (requires WiFI)
- [x] Glow LED setup
- [x] Message handers
- [x] Task execution with adjustable update frequency
  - [x] Touches cause immediate updates (optional)
  - [x] `async` tasks
- [x] Timeout based display backlight / Glow LED dimming and sleep
- [ ] Page-based window manager
  - [x] Programmatic page navigation
  - [x] Basic buttons with event callbacks
  - [x] Tabbed UI for page switching
  - [x] Themes with vector font support
  - [ ] Brightness controls
  - [x] Clock
  - [x] Modal pop-over pages
- [x] App switcher
- [ ] `mip` package

## Getting started

> [!CAUTION]
> This project is in its early days and is subject to breaking changes.

1. Upload [tmos.py](src/tmos.py) to your Presto
   - Include [tmos_ui.py](src/tmos_ui.py) if you want the window
     manager/themes.
   - Include [tmos_apps.py](src/tmos_apps.py) if you want the app manager
2. If you want to use WiFI, configure
   [`secrets.py`](https://github.com/pimoroni/pimoroni-pico/blob/main/micropython/examples/pico_wireless/secrets.py) accordingly.
3. Create an instance of `tmos.OS`.
4. Configure as desired, and register one or more tasks to run.
5. `boot` the OS with `run=True`.

### The low-level tasks API

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

### The high-level `App` and `Page` API

This example shows how to use the `AppManager` to switch between
multiple apps, each with their own set of pages:

```python
from tmos import OS
from tmos_ui import StaticPage, WindowManager, to_screen
from tmos_apps import App, AppManager

os = OS(layers=1)
wm = WindowManager(os, systray_visible=True)
apps = AppManager(wm)


class SimplePage(StaticPage):
    """
    A simple page with a message and an optional custom color.
    """

    def __init__(self, title: str, text: str, bg=None):
        super().__init__()
        self.title = title
        self.text = text
        self.bg = bg

    def _draw(self, display: "PicoGraphics", region: "Region", theme: "Theme"):
        display.set_pen(self.bg if self.bg else theme.background_pen)
        display.rectangle(*region)
        display.set_pen(theme.foreground_pen)
        theme.text(display, self.text, *to_screen(region, theme.padding, theme.padding))


class ColorsApp(App):

    YELLOW = wm.display.create_pen(255, 255, 100)
    RED = wm.display.create_pen(255, 100, 100)

    name = "Colors"

    def pages(self):
        return [
            SimplePage("Yellow", "Like a lemon", self.YELLOW),
            SimplePage("Red", "Like a thing that is red", self.RED),
        ]


class AnimalsApp(App):

    name = "Animals"

    def pages(self):
        return [
            SimplePage("Cat", "Cats are why the internet exists."),
            SimplePage("Mouse", "Mice are small."),
            SimplePage("Duck", "quaaaack."),
        ]


apps.add_app(ColorsApp(), make_current=True)
apps.add_app(AnimalsApp())

os.boot(run=True)
```

See the [examples](examples) for more.
