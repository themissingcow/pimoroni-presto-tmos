# SPDX-License-Identifier: MIT
"""
An example that shows how to use the WindowManager to rotate through
multiple pages, each with their own redraw rate.
"""
import time

from tmos import OS, Region
from tmos_ui import Page, Theme, WindowManager, to_screen

# layers=1 is so we can use partial_update, see:
#   https://github.com/pimoroni/presto/issues/56
os = OS(layers=1)
wm = WindowManager(os)

# Make the text a little larger in the theme
wm.theme.default_font_scale = 3


class SimplePage(Page):
    """
    A basic page that displays its own title along with the cpu time.
    """

    def tick(self, region: Region, window_manager: WindowManager):
        """
        Clear the screen and draw the title as text, using theme colors
        and fonts.
        """
        display = window_manager.display
        theme = window_manager.theme
        p = theme.padding

        theme.clear_display(display, region)
        # Make sure we draw within the specified region, which might not
        # be the whole screen, or have an origin at 0, 0.
        theme.text(display, self.title, *to_screen(region, p, p))
        theme.text(
            display, f" @ {time.ticks_ms()}", *to_screen(region, p, p + theme.line_spacing())
        )

        window_manager.update_display(region)


page_one = SimplePage()
page_one.title = "Fast"

page_two = SimplePage()
page_two.title = "Medium"
page_two.execution_frequency = 10

page_three = SimplePage()
page_three.title = "Slow"
page_three.execution_frequency = 1

# We don't need to make any page current, the task added below will call
# next_page when the os starts for us.
wm.add_page(page_one)
wm.add_page(page_two)
wm.add_page(page_three)

# Rotate the page every 5s, don't run on touch.
os.add_task(wm.next_page, execution_frequency=0.2, touch_forces_execution=False)

os.boot(run=True)
