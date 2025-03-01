# SPDX-License-Identifier: MIT
"""
An example that uses the RadioButton control to change the page
background.
"""
import asyncio
import time

from presto import PicoGraphics

from tmos import OS, Region
from tmos_ui import MomentaryButton, Page, Theme, WindowManager

os = OS(layers=1)
wm = WindowManager(os)

class APage(Page):

    title = "Async Events"

    def setup(self, region: Region, window_manager: WindowManager):
        """
        Create buttons with sync and async event callbacks.
        """
        p = window_manager.theme.padding
        y = 50

        def sync_buzz():
            """
            Buzzes for 1 second synchronously.
            """
            os.buzzer.set_tone(100)
            time.sleep(1)
            os.buzzer.set_tone(400)
            time.sleep_ms(10)
            os.buzzer.set_tone(-1)

        sync_region = Region(region.x + p, y, region.width - p - p, 30)
        sync_button = MomentaryButton(sync_region, "Sync")
        sync_button.on_button_up = sync_buzz
        self._controls.append(sync_button)

        y += 30 + p

        async def async_buzz():
            """
            Buzzes for 1 second asynchronously.
            """
            os.buzzer.set_tone(100)
            await asyncio.sleep(1)
            os.buzzer.set_tone(400)
            await asyncio.sleep_ms(10)
            os.buzzer.set_tone(-1)

        async_region = Region(region.x + p, y, region.width - p - p, 30)
        async_button = MomentaryButton(async_region, "Async")
        async_button.on_button_up = async_buzz
        self._controls.append(async_button)

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):
        """
        Draw the update tick so we can spot blocking events
        """
        theme.clear_display(display, region)
        display.set_pen(theme.foreground_pen)
        theme.text(display, f"Update @ {time.ticks_ms()}", 10, 10)


wm.add_page(APage(), make_current=True)

os.boot(run=True)
