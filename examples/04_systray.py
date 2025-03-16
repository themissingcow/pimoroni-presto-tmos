# SPDX-License-Identifier: MIT
"""
An demonstration of the systray and its programmatic controls.
"""
import time

from presto import PicoGraphics

from tmos import MSG_INFO, OS, Region
from tmos_ui import (
    LatchingButton,
    MomentaryButton,
    Page,
    StaticPage,
    RadioButton,
    WindowManager,
    Theme,
    to_screen,
)

os = OS(layers=1)
# Show the systray by default
wm = WindowManager(os, systray_visible=True)
wm.system_message_level = MSG_INFO


class ClockPage(Page):
    """
    A page with the current date/time.
    """

    title = "Clock"
    execution_frequency = 1

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):

        p = theme.padding

        theme.clear_display(display, region)

        # Make sure we draw within the specified region, which might not
        # be the whole screen, or have an origin at 0, 0.
        year, month, day, hours, mins, secs, _, __ = time.localtime()
        theme.text(
            display,
            f"{day:02d}/{month:02d}/{year} {hours:02d}:{mins:02d}:{secs:02d}",
            *to_screen(region, p, p),
            rel_scale=2,
        )


class TextPage(StaticPage):
    """
    A page with some words...
    """

    title = "Wordage"

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):

        p = theme.padding

        theme.clear_display(display, region)
        theme.text(display, "The\nCat\nsat\non\the\nMat", *to_screen(region, p, p), rel_scale=2)


class SetupPage(StaticPage):
    """
    A page that allows customisation of the systray.
    """

    title = "Setup"

    def setup(self, region: Region, window_manager: "WindowManager"):
        """
        Add controls for systray visibility/position.
        """

        # setup will be called whenever the pages content region
        # changes. As we're manipulating the systray, then this will be
        # called each time we change its visibility or position.
        #
        # Normally, you'd want to re-position any controls etc. In this
        # case though, we deliberately don't use the region - so the
        # controls don't bounce around as we move the systray and the
        # page's region changes (it hurts your eyes/brain).
        #
        # This means we can re-use the controls we made the first time.
        #
        # **Not recommended in normal use.**

        if self._controls:
            return

        t = window_manager.theme
        p = window_manager.theme.padding
        y = 80
        w = region.width - p - p

        # Create a button that toggles the systray visibility

        show_hide = MomentaryButton(
            Region(region.x + p, y, w, t.control_height), title="Toggle Systray"
        )
        show_hide.on_button_up = lambda: window_manager.set_systray_visible(
            not window_manager.systray_visible
        )
        self._controls.append(show_hide)

        # Create a radio button that chooses where the systray appears.

        positions = ["bottom", "top"]
        current_position = positions.index(window_manager.systray_position)

        def update_position(new_index):
            new_pos = positions[new_index]
            window_manager.set_systray_position(new_pos)

        position_selector = RadioButton(
            Region(region.x + p, y + t.control_height + p, w, t.control_height),
            positions,
            current_index=current_position,
        )
        position_selector.on_current_index_changed = update_position
        self._controls.append(position_selector)

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):
        """
        Draw some text at the top/bottom of the page to help illustrate
        how the systray affects the pages region.
        """

        p = theme.padding

        theme.clear_display(display, region)
        theme.text(display, "Systray Setup", *to_screen(region, p, p), rel_scale=2)

        theme.text(
            display,
            "See me adjust my position",
            *to_screen(region, p, region.height - p - theme.base_line_height),
        )


wm.add_page(ClockPage(), make_current=True)
wm.add_page(TextPage())
wm.add_page(SetupPage())

os.boot(run=True, wifi=True, use_ntp=True)
