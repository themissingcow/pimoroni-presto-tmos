# SPDX-License-Identifier: MIT
"""
An demonstration of modal pages.
"""

from presto import PicoGraphics

from tmos import OS, Region
from tmos_ui import (
    ClockAccessory,
    MomentaryButton,
    StaticPage,
    Systray,
    WindowManager,
    Theme,
    to_screen,
)

os = OS(layers=1)
# Show the systray by default to make the modality more obvious.
wm = WindowManager(os, systray_visible=True)

YELLOW = wm.display.create_pen(255, 255, 100)
RED = wm.display.create_pen(255, 100, 100)


class ModalPage(StaticPage):
    """
    A simple page with a message and a close button.
    """

    ## No need for a title as they cover the systray (unless you want
    ## one for debugging)

    def __init__(self, text: str, bg) -> None:
        super().__init__()
        self.text = text
        self.bg = bg

    def setup(self, region: Region, window_manager: "WindowManager"):
        """
        Add a button top right to close the current modal page.
        """
        p = window_manager.theme.padding
        close_button_region = Region(region.x + region.width - p - 75, p, 75, 25)
        close_button = MomentaryButton(close_button_region, "Close")
        # As there is only ever one, modal pages are easy to close
        close_button.on_button_up = window_manager.clear_modal_page
        self._controls.append(close_button)

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):
        display.set_pen(self.bg)
        display.rectangle(*region)
        display.set_pen(theme.foreground_pen)
        theme.text(
            display,
            self.text,
            *to_screen(region, theme.padding, region.y + region.height // 2),
            rel_scale=2,
        )


class ControlsPage(StaticPage):
    """
    A page with buttons to show modal pages.
    """

    title = "Controls"

    def setup(self, region: Region, window_manager: WindowManager):

        p = window_manager.theme.padding

        def add_modal_page_button(title: str, bg, text: str, y: int) -> int:
            """
            Adds a button that displays a modal page with the supplied text.
            """
            page = ModalPage(text, bg)
            height = window_manager.theme.control_height
            button_region = Region(region.x + p, region.y + y, region.width - p - p, height)
            show_button = MomentaryButton(button_region, title, title_rel_scale=2)
            # Ask the window manager to show the page modally
            show_button.on_button_up = lambda: window_manager.show_modal_page(page)
            self._controls.append(show_button)
            return y + height + p

        next_y = add_modal_page_button(
            "Show A Modal Page",
            YELLOW,
            "Hello!\nPress the button\nto close",
            p
        )
        add_modal_page_button(
            "Show Another",
            RED,
            "Page-tastic",
            next_y
        )

    def _draw(self, display: PicoGraphics, _: Region, theme: Theme):
        theme.clear_display(display)


wm.add_systray_accessory(ClockAccessory(), Systray.Accessory.POSITION_TRAILING)
wm.add_page(ControlsPage(), make_current=True)

os.boot(run=True, wifi=True, use_ntp=True)
