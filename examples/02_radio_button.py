# SPDX-License-Identifier: MIT
""" 
An example that uses the RadioButton control to change the page
background.
"""
from presto import PicoGraphics

from tmos import MSG_DEBUG, OS, Region
from tmos_ui import RadioButton, Page, Theme, WindowManager

os = OS(layers=1)
wm = WindowManager(os)


class ColorPage(Page):

    title = "Colors"
    execution_frequency = 1

    pen = None

    def setup(self, region: Region, window_manager: WindowManager):
        """
        Create a radio button at the bottom, that switches the current
        pen.
        """
        p = window_manager.theme.padding

        options = ["Red", "Green", "Blue"]
        pens = [
            window_manager.display.create_pen(255, 0, 0),
            window_manager.display.create_pen(0, 255, 0),
            window_manager.display.create_pen(0, 0, 255),
        ]

        self.pen = pens[0]

        radio_region = Region(region.x + p, region.height - p - 30, region.width - p - p, 30)
        radio_button = RadioButton(radio_region, options, current_index=0)

        # This callback will be run when the user changes the active
        # radio button option.
        def option_changed(new_index: int):
            self.pen = pens[new_index]

        radio_button.on_current_index_changed = option_changed

        # Add the control so it will be checked/drawn for us
        self._controls.append(radio_button)

    def _draw(self, display: PicoGraphics, region: Region, _: Theme):
        """
        Super simple implementation that fills the region with the
        chosen color.
        """
        display.set_pen(self.pen)
        display.rectangle(*region)


wm.add_page(ColorPage(), make_current=True)

os.boot(run=True)
