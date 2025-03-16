# SPDX-License-Identifier: MIT
"""
An demonstration of systray accessories.
"""
import asyncio
import time

from presto import PicoGraphics

from tmos import OS, Size, Region
from tmos_ui import (
    LatchingButton,
    RadioButton,
    StaticPage,
    Page,
    Systray,
    WindowManager,
    Theme,
    inset_region,
    to_screen,
)

os = OS(layers=1)
# Show the systray by default
wm = WindowManager(os, systray_visible=True)


class BoopAccessory(Systray.Accessory):
    """
    Adds a button that boops.
    """

    def size(self, max_size: Size, _: WindowManager) -> Size:
        return Size(max_size.height, max_size.height)

    def setup(self, region: Region, _: WindowManager):

        self._controls = []

        boop_button = LatchingButton(inset_region(region, 2, 3), "B")

        async def boop():
            os.buzzer.set_tone(1200)
            os.backlight_manager.set_glow_leds(255, 255, 255)
            await asyncio.sleep_ms(1200)
            os.buzzer.set_tone(2400)
            await asyncio.sleep_ms(50)
            os.backlight_manager.set_glow_leds(0, 0, 0)
            os.buzzer.set_tone(-1)
            boop_button.set_is_down(False)

        boop_button.on_button_down = boop
        self._controls.append(boop_button)


class ClockAccessory(Systray.Accessory):
    """
    A clock.

    Accessories are re-drawn with the systray so can't specify their own
    refresh rate (execution_frequency). The default is 1hz.
    """

    def size(self, max_size: Region, _: WindowManager) -> Size:
        return Size(45, max_size.height)

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):

        # The systray region is already cleared to the systray
        # background, so there is no need to clear our display region
        # ourselves.

        p = theme.padding

        # Make sure we draw within the specified region, which might not
        # be the whole screen, or have an origin at 0, 0.
        _, month, day, hours, mins, secs, __, ___ = time.localtime()
        line_height = theme.line_spacing()
        y = (region.height // 2) - line_height
        display.set_pen(theme.foreground_pen)
        theme.text(display, f"{hours:02d}:{mins:02d}:{secs:02d}", *to_screen(region, p, y))
        theme.text(display, f"{day:02d}/{month:02d}", *to_screen(region, p, y + line_height))


boop_accessory = BoopAccessory()
clock_accessory = ClockAccessory()


def set_accessory_positions(position: str):
    """
    Updates the position of the accessories in the systray.
    """

    # Remove the accessories if they've already been added, so we can
    # re-insert them in our new favoured position.
    l, t = wm.systray_accessories()
    if l or t:
        wm.remove_systray_accessory(boop_accessory)
        wm.remove_systray_accessory(clock_accessory)

    pos_l = Systray.Accessory.POSITION_LEADING
    pos_t = Systray.Accessory.POSITION_TRAILING

    positions = {
        pos_l: (pos_l, pos_l),
        pos_t: (pos_t, pos_t),
        "split": (pos_l, pos_t),
        "none": (None, None),
    }

    pos_boop, pos_clock = positions[position]

    if pos_boop:
        wm.add_systray_accessory(boop_accessory, position=pos_boop)
    if pos_clock:
        wm.add_systray_accessory(clock_accessory, position=pos_clock)


current_pos = "trailing"
set_accessory_positions(current_pos)


class OptionsPage(StaticPage):
    """
    A page to control the accessory positions.
    """

    title = "Options"

    def setup(self, region: Region, window_manager: "WindowManager"):

        options = [
            Systray.Accessory.POSITION_LEADING,
            Systray.Accessory.POSITION_TRAILING,
            "split",
            "none",
        ]

        def option_changed(new_index: int):
            global current_pos
            current_pos = options[new_index]
            set_accessory_positions(current_pos)

        p = window_manager.theme.padding
        radio_region = Region(
            region.x + p,
            region.height - p - 60,
            region.width - p - p,
            window_manager.theme.control_height,
        )
        radio_button = RadioButton(radio_region, options, current_index=options.index(current_pos))
        radio_button.on_current_index_changed = option_changed

        self._controls.append(radio_button)

    def _draw(self, display: PicoGraphics, _: Region, theme: Theme):
        theme.clear_display(display)


INFO_TEXT = """
Accessories can be added to the systray.

They update at the same rate.

They can use all the normal controls
that pages can, but have a restricted
set of life time hooks.

They can be set in a "leading" or
"trailing" position. Multiple accessories
are supported.

(Press the 'B')
"""


class InfoPage(StaticPage):

    title = "Info"

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):
        p = theme.padding
        theme.clear_display(display)
        display.set_pen(theme.foreground_pen)
        theme.text(display, INFO_TEXT, *to_screen(region, p, p))


wm.add_page(InfoPage(), make_current=True)
wm.add_page(OptionsPage())

os.boot(run=True, wifi=True, use_ntp=True)
