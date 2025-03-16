# SPDX-License-Identifier: MIT
"""
An example that shows pages that only update on request/touch.
"""
import asyncio
import time

from picographics import PicoGraphics

from tmos import OS, Region
from tmos_ui import StaticPage, MomentaryButton, Theme, WindowManager, to_screen

os = OS(layers=1)
wm = WindowManager(os)


class UpdatePage(StaticPage):
    """
    A basic page that shows when it was updated (ie tick -> _draw is
    called).
    """

    def setup(self, region: Region, window_manager: "WindowManager"):
        """
        Adds a button to request a page update.
        """

        p = window_manager.theme.padding
        update_region = Region(p, region.height - p - 50, region.width - p - p, 50)

        update_btn = MomentaryButton(update_region, "Update in 1s", title_rel_scale=2)

        async def request_update():
            # The touch to press the button will cause an update, which
            # masks the fact that we requested one, so request one 1s
            # later to let the touch updates finish.
            asyncio.sleep(1.0)
            self.needs_update = True

        update_btn.on_button_up = request_update
        self._controls.append(update_btn)

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):
        p = theme.padding
        theme.clear_display(display, region)
        theme.text(
            display,
            f"Update @ {time.ticks_ms()}",
            *to_screen(region, p, p),
            rel_scale=2,
        )


wm.add_page(UpdatePage(), make_current=True)

os.boot(run=True)
