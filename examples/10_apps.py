# SPDX-License-Identifier: MIT
"""
An demonstration of apps
"""

from presto import PicoGraphics

from tmos import OS
from tmos_ui import StaticPage, WindowManager, to_screen
from tmos_apps import App, AppManager

os = OS(layers=1, full_res=False)
# Show the systray by default to make the modality more obvious.
wm = WindowManager(os, systray_visible=True)
apps = AppManager(wm)

class SimplePage(StaticPage):
    """
    A simple page with a message and a custom color.
    """

    def __init__(self, title: str, text: str, bg=None) -> None:
        super().__init__()
        self.title = title
        self.text = text
        self.bg = bg

    def _draw(self, display: PicoGraphics, region: "Region", theme: "Theme"):
        display.set_pen(self.bg if self.bg else theme.background_pen)
        display.rectangle(*region)
        display.set_pen(theme.foreground_pen)
        theme.text(display, self.text, *to_screen(region, theme.padding, theme.padding))


class ColorsApp(App):
    """
    An app with some colorful pages.
    """

    YELLOW = wm.display.create_pen(255, 255, 100)
    RED = wm.display.create_pen(255, 100, 100)

    name = "Colors"

    def pages(self):
        return [
            SimplePage("Yellow", "Like a lemon", self.YELLOW),
            SimplePage("Red", "Like a thing that is red", self.RED),
        ]


class AnimalsApp(App):
    """
    An app with critical animal facts.
    """

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
