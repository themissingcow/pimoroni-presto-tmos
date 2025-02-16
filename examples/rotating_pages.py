# SPDX-License-Identifier: MIT
"""
An example that shows how to use the WindowManager to rotate through
multiple pages, each with their own redraw rate.
"""
import time

from picographics import PicoGraphics

from tmos import OS, Region
from tmos_ui import Page, PushButton, Theme, WindowManager, to_screen

# layers=1 is so we can use partial_update, see:
#   https://github.com/pimoroni/presto/issues/56
os = OS(layers=1)
wm = WindowManager(os)


class PageWithTime(Page):
    """
    A basic page that displays its own title along with the cpu time.

    It includes buttons to switch between adjacent pages.
    """

    def setup(self, region: Region, window_manager: "WindowManager"):
        """
        This method is called before the page is first displayed, or if
        the region the page occupies changes.

        It is an opportunity to create controls and or work out any
        static data pertaining to the geometry of the display.
        """

        # Figure out a few constants
        padding = window_manager.theme.padding
        btn_height = 50
        btn_width = (region.width - (padding * 3)) // 2
        btn_y = region.height - btn_height - padding

        # Make a button on the bottom left to change to the prev page
        prev_region = Region(region.x + padding, btn_y, btn_width, btn_height)
        prev_btn = PushButton(prev_region, "Prev")
        # Buttons events can call functions when activated via touch.
        # This is handled by the os, so we don't have to check button
        # state ourselves. By default, regardless of the update
        # frequency we specify, we're always called immediately if there
        # is touch interaction.
        prev_btn.on_button_up = window_manager.prev_page
        # Adding the button to our control list will cause it to be
        # checked for touches, and drawn on screen after our _draw call
        # is done. Re-implement Page.tick if you don't want this
        # behaviour.
        self._controls.append(prev_btn)

        # Make a button on the bottom right to change to the next page
        next_btn_x = region.x + padding + btn_width + padding
        next_region = Region(next_btn_x, btn_y, btn_width, btn_height)
        next_tn = PushButton(next_region, "Next")
        next_tn.on_button_up = window_manager.next_page
        self._controls.append(next_tn)

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):
        """
        Clear the screen and draw the title as text, using theme colors
        and fonts.

        This method is called by the OS after processing touches, and
        before the controls are drawn on top.

        We don't need to update the display here as this will be done
        once controls are drawn.
        """
        p = theme.padding

        theme.clear_display(display, region)
        # Make sure we draw within the specified region, which might not
        # be the whole screen, or have an origin at 0, 0.
        theme.text(display, self.title, *to_screen(region, p, p))
        theme.text(
            display, f" @ {time.ticks_ms()}", *to_screen(region, p, p + theme.line_spacing())
        )


page_one = PageWithTime()
page_one.title = "Fast"

page_two = PageWithTime()
page_two.title = "Medium"
page_two.execution_frequency = 10

page_three = PageWithTime()
page_three.title = "Slow"
page_three.execution_frequency = 1

# We don't need to make any page current, the task added below will call
# next_page when the os starts for us.
wm.add_page(page_one)
wm.add_page(page_two)
wm.add_page(page_three)

# Rotate the page every 10s, don't run on touch as that would be dizzying.
os.add_task(wm.next_page, execution_frequency=0.1, touch_forces_execution=False)

os.boot(run=True)
