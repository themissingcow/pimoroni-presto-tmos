# SPDX-License-Identifier: MIT
"""
An example of simple custom themes.
"""
from presto import PicoGraphics

from tmos import OS, Region
from tmos_ui import (
    ClockAccessory,
    DefaultTheme,
    LatchingButton,
    MomentaryButton,
    RadioButton,
    StaticPage,
    Theme,
    WindowManager,
)

from tmos_themes import ClassicTheme

# Theme properties can be customised before they are used.
#
# The theme's setup method is called once they are added to the
# WindowManager, this initialises pens etc... and so as long as we
# customise them before passing to the theme= constructor kwarg, or the
# set_theme method, then any changes you make will take effect.

# The default theme is light
LIGHT_THEME = DefaultTheme()

# Swap the fg/bg around and adjust some of the other colors.
DARK_THEME = DefaultTheme()
DARK_THEME.foreground_pen = LIGHT_THEME.background_pen
DARK_THEME.background_pen = LIGHT_THEME.foreground_pen
DARK_THEME.secondary_background_pen = (30, 30, 30)

CLASSIC_THEME = ClassicTheme()

# And make a totally ridiculous one. This demonstrates vector font
# support too.
NEON_THEME = DefaultTheme()
NEON_THEME.foreground_pen = (255, 255, 0)
NEON_THEME.background_pen = (255, 0, 255)
NEON_THEME.secondary_background_pen = (180, 0, 180)
NEON_THEME.font = "cherry-hq.af"
NEON_THEME.base_font_scale = 20
NEON_THEME.base_text_height = 14
NEON_THEME.base_line_height = 16
NEON_THEME.systray_height = 50
NEON_THEME.control_height = 20
NEON_THEME.systray_text_rel_scale = 2

# If more comprehensive customisation is needed, you can subclass
# Theme and override it's drawing methods.

os = OS(layers=1, full_res=False)

# We'll pick the light theme by default. If not specified, then the
# WindowManager makes its own instance of the DefaultTheme.
wm = WindowManager(os, theme=LIGHT_THEME, systray_visible=True)
wm.add_systray_accessory(ClockAccessory(show_seconds=False), ClockAccessory.POSITION_TRAILING)


class ThemePage(StaticPage):

    title = "Themes"

    def setup(self, region: Region, window_manager: WindowManager):
        """
        Create a radio button at the bottom, that switches the current
        theme.
        """

        # Note, as themes can change the size of UI elements, setup will
        # be called when the theme changes.

        p = window_manager.theme.padding
        control_height = window_manager.theme.control_height
        available_width = region.width - p - p
        half_Width = (available_width - p) // 2
        y = region.y + p

        momentary_region = Region(region.x + p, y, half_Width, control_height)
        momentary_button = MomentaryButton(momentary_region, "Momentary Button")

        latching_region = Region(region.x + p + half_Width + p, y, half_Width, control_height)
        latching_button = LatchingButton(latching_region, "Latching Button")

        options = ["Light", "Dark", "Classic", "Unpleasant"]
        themes = [LIGHT_THEME, DARK_THEME, CLASSIC_THEME, NEON_THEME]

        radio_region = Region(
            region.x + p, region.height - p - control_height, available_width, control_height
        )
        radio_button = RadioButton(
            radio_region, options, current_index=themes.index(window_manager.theme)
        )

        def theme_changed(new_index: int):
            window_manager.set_theme(themes[new_index])

        radio_button.on_current_index_changed = theme_changed

        self._controls = [momentary_button, latching_button, radio_button]

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):
        theme.clear_display(display, region)
        p = theme.padding
        x = region.x + p
        y = region.y + p + theme.control_height + p
        theme.text(display, "Text with rel_scale 2", x, y, rel_scale=2)
        y += theme.line_spacing(rel_scale=2) + p
        theme.text(display, "Text with rel_scale 1", x, y, rel_scale=1)
        y += theme.line_spacing(rel_scale=1) + p
        theme.text(
            display,
            "Separated by theme padding, this line is long to demonstrate word wraping spacing",
            x,
            y,
            rel_scale=1,
            wordwrap=region.width - p - p,
        )


class ControlPage(StaticPage):

    title = "Controls"

    def setup(self, region: Region, window_manager: "WindowManager"):

        # Create a radio button that chooses where the systray appears.

        t = window_manager.theme
        p = window_manager.theme.padding
        x = region.x + p
        y = region.y + t.line_spacing() + p
        w = region.width - p - p

        positions = ["bottom", "top"]
        current_position = positions.index(window_manager.systray_position)

        def update_position(new_index):
            new_pos = positions[new_index]
            window_manager.set_systray_position(new_pos)

        position_selector = RadioButton(
            Region(x, y, w, t.control_height),
            positions,
            current_index=current_position,
        )
        position_selector.on_current_index_changed = update_position
        self._controls = [position_selector]

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):

        theme.clear_display(display, region)
        theme.text(display, "Systray position", region.x + theme.padding, region.y + theme.padding)


class EmptyPage(StaticPage):
    title = "Empty"

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):
        theme.clear_display(display, region)


wm.add_page(ThemePage(), make_current=True)
wm.add_page(ControlPage())
wm.add_page(EmptyPage())

os.boot(run=True)
