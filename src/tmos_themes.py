# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Additional themes for The missing OS.
"""

from picographics import PicoGraphics
from picovector import Polygon

from tmos import Region
from tmos_ui import Theme, inset_region


def lerp_color(a: tuple(int), b: tuple(int), position: float) -> tuple[int]:
    """
    Blends between color a and color b.
    """
    diff = (a[0] - b[0], a[1] - b[1], a[2] - b[2])
    tint = (int(diff[0] * position), int(diff[1] * position), int(diff[2] * position))
    return (a[0] - tint[0], a[1] - tint[1], a[2] - tint[2])

def corner_radii(free_radius: int, adjoined: int) -> tuple(int):
    """
    Determines a corner tuple for a rect adjoined on the specified
    sides.
    """
    return (
        0 if (adjoined & Theme.EDGE_L or adjoined & Theme.EDGE_T) else free_radius,
        0 if (adjoined & Theme.EDGE_T or adjoined & Theme.EDGE_R) else free_radius,
        0 if (adjoined & Theme.EDGE_R or adjoined & Theme.EDGE_B) else free_radius,
        0 if (adjoined & Theme.EDGE_B or adjoined & Theme.EDGE_L) else free_radius,
    )

class ClassicTheme(Theme):
    """
    A simple black/white/grey theme with rounded corners.
    """

    padding = 5
    font = "bitmap8"
    base_font_scale = 1
    base_text_height = 8
    base_line_height = 10
    systray_height = 30
    control_height = 30

    foreground_pen = (0, 0, 0)
    background_pen = (255, 255, 255)
    secondary_background_pen = (200, 200, 200)
    error_pen = (200, 0, 0)

    button_corner_radius = 8

    _dpi_scaled_sizes = Theme._dpi_scaled_sizes + ("button_corner_radius",)

    def setup(self, display: PicoGraphics, dpi_scale_factor: int):

        if not self._setup_done:
            tint_factor = 0.1
            mid_fg = lerp_color(self.foreground_pen, self.background_pen, tint_factor)
            mid_bg = lerp_color(self.foreground_pen, self.background_pen, 1.0 - tint_factor)
            self._mid_foreground_pen = display.create_pen(*mid_fg)
            self._mid_background_pen = display.create_pen(*mid_bg)

        super().setup(display, dpi_scale_factor)

    def draw_button_frame(
        self,
        display: PicoGraphics,
        region: Region,
        is_pressed: bool,
        adjoined: int,
        bevel: bool = True,
    ):

        radius = self.button_corner_radius

        corners = corner_radii(radius, adjoined)

        shape = Polygon()

        display.set_pen(self.foreground_pen)
        shape.rectangle(*region, corners=corners)
        self._vector.draw(shape)

        if adjoined & self.EDGE_L and not is_pressed:
            display.set_pen(self._mid_background_pen if bevel else self.background_pen)
            display.rectangle(
                region.x,
                region.y + self.dpi_scale_factor,
                self.dpi_scale_factor,
                region.height - self.dpi_scale_factor - self.dpi_scale_factor,
            )

        if not is_pressed:

            inner_radius = radius - self.dpi_scale_factor
            inner_corners = corner_radii(inner_radius, adjoined)

            display.set_pen(self._mid_background_pen if bevel else self.background_pen)
            inner_shape = Polygon()
            inner_shape.rectangle(
                *inset_region(region, self.dpi_scale_factor), corners=inner_corners
            )
            self._vector.draw(inner_shape)

    def draw_button_title(
        self,
        display: PicoGraphics,
        region: Region,
        is_pressed: bool,
        title: str,
        title_rel_scale: int,
        adjoined: int,
    ):
        display.set_pen(self.background_pen if is_pressed else self.foreground_pen)
        self.centered_text(display, region, title, rel_scale=title_rel_scale)

    def draw_systray(self, display: PicoGraphics, region: Region, adjoined: int):
        display.set_pen(self.secondary_background_pen)
        display.rectangle(*region)
        display.set_pen(self.foreground_pen)
        if adjoined & self.EDGE_T:
            display.rectangle(region.x, region.y, region.width, self.dpi_scale_factor)
        else:
            display.rectangle(
                region.x,
                region.y + region.height - self.dpi_scale_factor,
                region.width,
                self.dpi_scale_factor,
            )

    def draw_systray_page_button_frame(
        self, display: PicoGraphics, region: Region, is_pressed: bool, adjoined: int
    ):
        line_thk = self.dpi_scale_factor
        tab_region = self._tab_region(region, adjoined)

        v_adjoined = adjoined & (self.EDGE_B + self.EDGE_T)
        h_adjoined = adjoined & (self.EDGE_L + self.EDGE_R)

        # Before we draw the normal frame, draw the extension of
        # adjacent buttons as needed for the chosen page
        if is_pressed:
            adjoined = v_adjoined
        #    if h_adjoined & self.EDGE_L:
        #        display.set_pen(self.foreground_pen)
        #        display.rectangle(
        #            tab_region.x, tab_region.y, self.button_corner_radius, tab_region.height
        #        )
        #    if h_adjoined & self.EDGE_R:
        #        display.set_pen(self.foreground_pen)
        #        display.rectangle(
        #            tab_region.x + tab_region.width - self.button_corner_radius,
        #            tab_region.y,
        #            self.button_corner_radius,
        #            tab_region.height,
        #        )

        if is_pressed:
            self.draw_button_frame(display, tab_region, not is_pressed, adjoined, bevel=False)

            display.set_pen(self.background_pen)
            display.rectangle(
                tab_region.x + line_thk,
                (
                    tab_region.y
                    if adjoined & self.EDGE_T
                    else tab_region.y + tab_region.height - line_thk
                ),
                tab_region.width - line_thk - line_thk,
                line_thk,
            )

    def draw_systray_page_button_title(
        self,
        display: PicoGraphics,
        region: Region,
        is_pressed: bool,
        title: str,
        title_rel_scale: int,
        adjoined: int,
    ):
        tab_region = self._tab_region(region, adjoined)
        display.set_pen(self.foreground_pen if is_pressed else self._mid_foreground_pen)
        self.centered_text(display, tab_region, title, rel_scale=title_rel_scale)

    def _tab_region(self, region: Region, adjoined: int) -> Region:

        inset = 2 * self.dpi_scale_factor
        x, y, w, h = region
        v_adjoined = adjoined & (self.EDGE_B + self.EDGE_T)
        if (v_adjoined & self.EDGE_T or v_adjoined & self.EDGE_B) and (
            v_adjoined != (self.EDGE_T + self.EDGE_B)
        ):
            h -= inset
            if adjoined & self.EDGE_B:
                y += inset
        h_adjoined = adjoined & (self.EDGE_L + self.EDGE_R)
        if (h_adjoined & self.EDGE_L or h_adjoined & self.EDGE_R) and (
            h_adjoined != (self.EDGE_L + self.EDGE_R)
        ):
            w -= inset
            if adjoined & self.EDGE_R:
                x += inset

        return Region(x, y, w, h)
