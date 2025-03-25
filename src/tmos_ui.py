# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
The Missing "OS": UI Layer

TODO: Document the architecture of the UI Layer
"""

# This is a monstrous single-file module to make deployment easier.

import asyncio
import math

from collections import namedtuple

from picographics import PicoGraphics

import picovector
from picovector import PicoVector

from tmos import OS, Region, Size, MSG_WARNING, MSG_SEVERITY_NAMES


__all__ = [
    "Control",
    "DefaultTheme",
    "Page",
    "MomentaryButton",
    "LatchingButton",
    "RadioButton",
    "Theme",
    "WindowManager",
    "is_within",
    "to_screen",
]


# Allows us to detect if a supplied task is a coroutine or not.
# Fallible, as this is 'generator' in micropython, but as we
# don't ever expect function tasks to return anything, then this
# should work fine.
async def __coro():
    pass


COROUTINE_TYPE = type(__coro())


def to_screen(region: Region, x: int, y: int) -> (int, int):
    """
    Offsets a point within region to screen space, without bounds
    checking.

    Eg, x = 10, y = 10, in Region( 100, 200, ... ) returns (110, 120)

    :param region: Target region
    :param x: x coordinate relative to the regions origin.
    :param y: y coordinate relative to the regions origin.
    :return: Sceen space x, y tupple.
    """
    return x + region.x, y + region.y


def is_within(region: Region, x: int, y: int) -> bool:
    """
    Determines if the supplied x/y coordinates are within the region.

    :param region: Region to intersect.
    :param x: The x coordinate to test.
    :param y: The y coordinate to test.
    :return: True if the coordinates are within the region.
    """
    return region.x <= x < (region.x + region.width) and region.y <= y < (region.y + region.height)


def inset_region(region: Region, x_amt: int, y_amt: int = None) -> Region:
    """
    Insets the specified region, to a smaller region.

    NOTE: Not effort is made to ensure the resulting region has positive
    volume.

    :param region: The region to inset.
    :param x_amt: The amount to inset the left and right sides by.
    :param y_amt: The amount to inset the top and bottom, if None,
      then x_amt will be used.
    :return: The inset region.
    """
    if y_amt is None:
        y_amt = x_amt

    return Region(
        region.x + x_amt,
        region.y + y_amt,
        region.width - x_amt - x_amt,
        region.height - y_amt - y_amt,
    )


class Theme:
    """
    The encapsulation of a color scheme and presentation of UI elements.

    A theme can be used for it's palette, and to draw on-screen graphics
    consistently.

    Themes are responsible for drawing well-known WindowManager controls
    and UI elements. If extending these, use the drawing mechanisms
    exposed by the theme if you want them to match other elements.

    Use the base picographcs APIs if full flexibility is required.

    Themes support bitmap and vector fonts. If the font name ends with
    ".af" then it will be rendered using PicoVector.
    """

    foreground_pen: int
    """
    The preferred pen to use for text and other primary content.
    """

    background_pen: int
    """
    The preferred pen to use for empty areas.
    """

    secondary_background_pen: int
    """
    The pen to use for secondary empty areas.
    """

    error_pen: int
    """
    The preferred pen to use for highlighting errors or other
    failure-related information.
    """

    font: str
    """
    A PicoGraphics.set_font compatible font name. If the font name ends
    with "af" then the PicoVector library will be used.
    """

    base_font_scale: int
    """
    The base font scale to use for drawing text. Scales specified to
    draw calls are relative to this size.
    """

    base_line_height: int
    """
    The height of a line (in pixels) for text at the base size/scale.

    Making this larger than the text simulates an increased line height.
    Note: This is not considered when long text is rendered using
    wordwrap.
    """

    padding: int = 10
    """
    The preferred padding value to add around UI elements.
    """

    control_height: int
    """
    The preferred height for a control
    """

    systray_height: int = 30
    """
    The height of the systray, when visible.
    """

    systray_text_rel_scale: int = 1
    """
    The relative scale of text used in the systray.
    """

    _use_vector_font_rendering: bool = False
    _vector: PicoVector = None

    def setup(self, display: PicoGraphics):
        """
        Configures the theme for the supplied display.

        This will be called by the WindowManager, and does not need to
        be called in user code in most common use cases.

        This should be implemented by a theme to  initialise pens,
        fonts, and other properties appropriately for the supplied
        display.

        The base class implementation must be called.
        """
        self._vector = self._create_picovector(display)

        self._use_vector_font_rendering = self.font.endswith(".af")
        if self._use_vector_font_rendering:
            self._vector.set_font(self.font, self.base_font_scale)
        else:
            display.set_font(self.font)

    def _create_picovector(self, display: PicoGraphics) -> PicoVector:
        # https://github.com/pimoroni/presto/issues/61
        # pylint: disable=attribute-defined-outsite-init
        self.__vector_transform = picovector.Transform()
        vector = PicoVector(display)
        vector.set_transform(self.__vector_transform)
        vector.set_antialiasing(picovector.ANTIALIAS_BEST)
        return vector

    def text_scale(self, rel_scale: float = 1) -> int:
        """
        A helper to determine text scale to draw, taking an optional
        scale factor on the base theme font scale.

        The return of this function will never be less than one.

        :param rel_scale: A custom scale that multiplies the themes default.
        :return: The text scale to use, rounded to the nearest integer.
        """
        return int(max(1, round(self.base_font_scale * rel_scale)))

    def line_spacing(self, rel_scale: float = 1) -> int:
        """
        Determines the line height of the themes text. This can be used
        to ensure multiple draw calls are spaced appropriately.

        This factors in the themes base_font_scale and a relative scale
        if specified, using the same rounding logic as text_scale.

        :param rel_scale: The scale of text to be drawn, relative to the
          themes base_font_scale.
        :return: The preferred line height in pixels, including spacing.
        """
        ratio = self.text_scale(rel_scale) / self.base_font_scale
        return int(round(self.base_line_height * ratio))

    def measure_text(self, display: PicoGraphics, text: str, rel_scale: float = 1) -> (int, int):
        """
        Approximates the bounding box for the specified text, at a scale
        relative to the themes base_font_scale.

        Note: for bitmap fonts, height is approximated by the line
        height.

        This method bridges PicoGraphics and PicoVectors measurement
        methods.

        :param text: The text to measure
        :param rel_scale: The scale relative to the themes base_font_scale.
        :return: Approximate width, height of the texts bounds.
        """
        if self._use_vector_font_rendering:
            self._vector.set_font_size(self.text_scale(rel_scale))
            # We ignore the height as its the bbox of the actual text,
            # which consequently changes if you have descenders or not.
            _, __, w, ___ = self._vector.measure_text(text)
            w = int(w)
        else:
            w = display.measure_text(text, self.text_scale(rel_scale))
        h = self.line_spacing(rel_scale)
        return w, h

    def clear_display(self, display: PicoGraphics, region: Region = None, set_fg_pen: bool = True):
        """
        Clears the display using the background_pen, and re-sets
        optionally resets the pen to the foreground_pen.

        :param display: The display instance to clear.
        :param region: An optional region to update.
        :param set_fg_pen: If True, the display's pen will be reset to
          the theme's foreground_pen.
        """

        display.set_pen(self.background_pen)
        if region:
            display.rectangle(*region)
        else:
            display.clear()
        if set_fg_pen:
            display.set_pen(self.foreground_pen)

    def text(
        self,
        display: PicoGraphics,
        text: str,
        x: int,
        y: int,
        *args,
        rel_scale: float = 1.0,
        **kwargs,
    ):
        """
        Draws text, additional args as pre PicoGraphics.text.

        NOTE: If the wordwrap arg is provided, as this is handled by
        PicoGraphics, rendering will not respect the themes line_height.

        :param display: The display on which to draw the text.
        :param rel_scale: Scales the themes base_font_scale by this amount.
        :param text: The string to render.
        """
        if self._use_vector_font_rendering:
            self._vector.set_font_size(self.text_scale(rel_scale))
            # The default line height is a little large
            self._vector.set_font_line_height(int(rel_scale * (self.base_font_scale * 1.3)))
            y += int(self.line_spacing(rel_scale) * 0.75)
            self._vector.text(text, x, y)
        else:
            display.text(text, x, y, *args, scale=self.text_scale(rel_scale), **kwargs)

    def centered_text(
        self,
        display: PicoGraphics,
        region: Region,
        text: str,
        *args,
        rel_scale: float = 1,
        **kwargs,
    ):
        """
        Draws single line text approximately centered within the region.

        See @text for other args.
        """
        text_width, height = self.measure_text(display, text, rel_scale)

        cx = region.x + (region.width // 2)
        cy = region.y + (region.height // 2)

        x = cx - (text_width // 2)
        y = cy - (height // 2)

        self.text(display, text, x, y, *args, rel_scale=rel_scale, **kwargs)

    def draw_strings(
        self, display: PicoGraphics, messages: [str], region: Region, rel_scale: float = 1
    ):
        """
        Draws multiple, multi-line strings in order.

        :param display: The display to draw the messages on.
        :param messages: A list of strings to draw.
        :param region: The region to draw within, lines will be wrapped
          to avoid overflow.
        :param scale: The text scale to use for display.
        """
        self.clear_display(display, region)

        wrap_width = region.width - (2 * self.padding)

        offset = 0

        # TODO: properly manage clipping, need to figure out how not to
        # interfere with any clipping set by the window manager.
        for message in messages:
            self.text(
                display,
                message,
                region.x + self.padding,
                region.y + self.padding + offset,
                wrap_width,
                rel_scale=rel_scale,
            )
            # Work out how many lines we consumed, measure_text only
            # gives a width.
            # TODO: The +1 is for a fudge for the fact that
            # we're calculating character wrap not word wrap
            # It's super inaccurate though.
            text_width, _ = self.measure_text(display, message, rel_scale)
            num_lines = math.ceil(text_width / wrap_width)
            if num_lines > 1:
                num_lines += 1
            offset += self.line_spacing(rel_scale) * num_lines
            # Skip anything that would run off the edge entirely
            if offset > region.height:
                break

    def draw_button_frame(self, display: PicoGraphics, region: Region, is_pressed: bool):
        """
        Draws the frame/background for an on-screen "button"

        :param display: The display to draw the messages on.
        :param region: The bounds of the button.
        :param is_pressed: Whether the button is currently pressed.
        """
        display.set_pen(self.foreground_pen)
        display.rectangle(*region)
        if is_pressed:
            display.set_pen(self.background_pen)
            x, y, w, h = region
            display.rectangle(x + 1, y + 1, w - 2, h - 2)

    # pylint: disable=too-many-arguments
    def draw_button_title(
        self,
        display: PicoGraphics,
        region: Region,
        is_pressed: bool,
        title: str,
        title_rel_scale: int,
    ):
        """
        Draws the frame/background for an on-screen "button"

        :param display: The display to draw the messages on.
        :param region: The bounds of the button.
        :param is_pressed: Whether the button is currently pressed.
        :param title: The button title.
        :param title_rel_scale: The relative font scale to draw the
          title with.
        """
        display.set_pen(self.foreground_pen if is_pressed else self.background_pen)
        self.centered_text(display, region, title, rel_scale=title_rel_scale)

    def draw_systray(self, display: PicoGraphics, region: Region):
        """
        Draws the systray region underneath any other controls.

        :param display: The display to draw on.
        :param region: The bounds of the systray region.
        """
        display.set_pen(self.secondary_background_pen)
        display.rectangle(*region)
        display.set_pen(self.foreground_pen)
        display.line(region.x, region.y, region.x + region.width, region.y)
        display.line(
            region.x,
            region.y + region.height - 1,
            region.x + region.width,
            region.y + region.height - 1,
        )

    def draw_systray_page_button_frame(
        self, display: PicoGraphics, region: Region, is_pressed: bool
    ):
        """
        Draws the button frame for a systray page selector.

        see: draw_button_frame
        """
        self.draw_button_frame(display, region, is_pressed)

    def draw_systray_page_button_title(
        self,
        display: PicoGraphics,
        region: Region,
        is_pressed: bool,
        title: str,
        title_rel_scale: int,
    ):
        """
        Draws the button title for a systray page selector.

        see: draw_button_title
        """
        self.draw_button_title(display, region, is_pressed, title, title_rel_scale=title_rel_scale)


class DefaultTheme(Theme):
    """
    A simple black-and-white theme.
    """

    padding = 5
    font = "bitmap8"
    base_font_scale = 1
    base_line_height = 10
    systray_height = 30

    def setup(self, display: PicoGraphics):

        w, _ = display.get_bounds()

        self.foreground_pen = display.create_pen(0, 0, 0)
        self.background_pen = display.create_pen(255, 255, 255)
        self.secondary_background_pen = display.create_pen(200, 200, 200)
        self.error_pen = display.create_pen(200, 0, 0)
        self.control_height = 3 * self.base_line_height

        if w > 240:
            self.padding *= 2
            self.base_font_scale *= 2
            self.base_line_height *= 2
            self.control_height *= 2
            self.systray_height *= 2

        super().setup(display)


class Control:
    """
    A base for interactive elements.

    We don't make use of the stock Presto Button, etc as they manage
    global state. This isn't compatible with the multi-page model, where
    only one of many pages will be visible at any given time.

    We also introduce a more html style even model to controls.

    Controls usually have one or more on_* attributes, that can be set
    to a callable, that should be invoked upon specific state
    transitions of the control.

    Unless otherwise noted, it is allowed to modify a control's state in
    an event callback.
    """

    def process_touch_state(self, touch):
        """
        Process the touch and update the state of the button, calling
        any event callbacks as relevant.
        """

    def draw(self, display: PicoGraphics, theme: Theme):
        """
        Draw the control within its region, using the supplied theme to
        reflect its current state.
        """

    def _event(self, event_name: str, *args, **kwargs):
        """
        Invoke the registered callable for the named event, if one has
        been set. Otherwise its a noop.
        """
        fn = getattr(self, event_name)
        if fn:
            result = fn(*args, **kwargs)
            if isinstance(result, COROUTINE_TYPE):
                asyncio.create_task(result)


class _Button(Control):
    """
    A base class for buttons, that defines the main 'is_down' state plus
    associated events.
    """

    title: str
    """
    The button text.
    """

    title_rel_scale: float
    """
    The scale of the button's text relative to the theme's default text
    scale.
    """

    region: Region
    """
    The area occupied by the button.
    """

    __is_down: bool = False

    on_button_down = None
    """
    A callable, invoked when the button transitions to a down state.
    """

    on_button_up = None
    """
    A callable, invoked when the button transitions to an up state.
    """

    on_button_cancel = None
    """
    A callable, invoked when a users touch leaves the button when down.
    """

    def __init__(self, region: Region, title: str = "", title_rel_scale=1) -> None:
        self.region = region
        self.title = title
        self.title_rel_scale = title_rel_scale

    @property
    def is_down(self) -> bool:
        """
        :return: Whether the button is currently down.
        """
        return self.__is_down

    def set_is_down(self, is_down: bool, emit: bool = True):
        """
        Programmatically set the buttons state.

        :param is_down: The new state of the button.
        :param emit: When True, event callbacks will be invoked if the
          button changes state as a result of this call.
        """
        if is_down == self.__is_down:
            return

        self.__is_down = is_down
        if emit:
            self._event("on_button_down" if is_down else "on_button_up")

    def draw(self, display: PicoGraphics, theme: Theme):

        theme.draw_button_frame(display, self.region, self.__is_down)
        if self.title:
            theme.draw_button_title(
                display, self.region, self.__is_down, self.title, self.title_rel_scale
            )


class MomentaryButton(_Button):
    """
    A button that only remains pressed whilst a touch is active within
    the buttons region.

    If the touch ends inside, on_button_up is invoked, otherwise if the
    touch exits the button region, on_button_cancel will be invoked.
    """

    def process_touch_state(self, touch):

        touch_active = touch.state
        touch_active_inside = touch_active and is_within(self.region, touch.x, touch.y)

        was_down = self.is_down
        self.set_is_down(touch_active_inside, emit=False)

        if touch_active_inside:
            if not was_down:
                self._event("on_button_down")
        else:
            if not touch_active:
                # Touch ended within our region
                if was_down:
                    self._event("on_button_up")
            elif was_down:
                # The touch has moved out side our area, we don't count
                # this as a button up as its a common way to 'cancel' a
                # press.
                self._event("on_button_cancel")


class LatchingButton(_Button):
    """
    A button that toggles between down and up on successive presses.

    on_button_down/on_button_up will be immediately invoked as soon as
    a touch enters the button region.
    """

    _last_touch_was_active_inside = None

    def process_touch_state(self, touch):

        # This duplicates a lot from MomentaryButton, but parametrising
        # latching/momentary made the code harder to read.

        touch_active = touch.state
        touch_active_inside = touch_active and is_within(self.region, touch.x, touch.y)

        # De-bounce, so we don't toggle every time we process touches
        if touch_active_inside == self._last_touch_was_active_inside:
            return

        touch_was_inside = self._last_touch_was_active_inside
        self._last_touch_was_active_inside = touch_active_inside

        # update after the touch, to allow cancellation
        if touch_was_inside:
            if not touch_active:
                # The touch ended within our bounds
                was_on = self.is_down
                self.set_is_down(not was_on)
            else:
                # The touch ended outside
                self._event("on_button_cancel")


class RadioButton(Control):
    """
    A control consisting of multiple LatchingButtons, that represent
    a list of options. Only one option can be active at any one time.
    Similar to the old radio preset buttons.
    """

    region: Region

    control_class: LatchingButton

    on_current_index_changed = None
    """
    A callable that will be invoked when the currently acrtive index is
    changed.
    """

    _controls: [LatchingButton]
    _options: [str]
    _current_index: int = -1

    def __init__(
        self,
        region: Region,
        options: [str],
        current_index: int = 0,
        title_rel_scale: float = 1.0,
        control_class: LatchingButton = LatchingButton,
    ) -> None:
        """
        Constructs a new RadioButton.

        :param region: The region occupied by the button.
        :param options:  A list of titles for each segment of the control.
        :param current_index: The index of the active option.
        :param title_rel_scale: The scale of the button text relative to
          the themes default size.
        :raises ValueError: If no options are supplied, or current_index
          is our of range.
        """
        self.region = region

        if not options:
            raise ValueError("One or more options must be provided")

        self._options = options
        self._controls = []
        self.control_class = control_class

        option_width = region.width // len(options)
        for i, option in enumerate(options):
            ctl_region = Region(
                region.x + (i * option_width), region.y, option_width, region.height
            )
            control = self._create_option_control(i, ctl_region, option, title_rel_scale)
            self._controls.append(control)

        self.set_current_index(current_index)

    def _create_option_control(self, index: int, region: Region, title: str, *args) -> Control:
        """
        Creates the control for each option of the control.
        """
        button = self.control_class(region, title, *args)
        button.on_button_down = lambda: self.set_current_index(index)

        def disallow_off_if_current():
            """
            The current option can only be turned off by selecting
            another option.
            """
            if index == self.current_index:
                button.set_is_down(True, emit=False)

        button.on_button_up = disallow_off_if_current

        return button

    @property
    def options(self) -> [str]:
        """
        The options represented by the control.
        """
        return self._options

    @property
    def current_index(self) -> int:
        """
        The index of the currently active option.
        """
        return self._current_index

    def set_current_index(self, index: int):
        """
        Programmatically set the currently active index.

        :param index: The newly active index.
        :raises ValueError: If the supplied index is outside of the
          range of the controls options.
        """
        if index == self._current_index:
            return

        if index < 0 or index >= len(self._options):
            raise ValueError(f"Index {index} is out of range (0-{len(self._options)}")

        self._current_index = index
        for i, control in enumerate(self._controls):
            control.set_is_down(i == index, emit=True)

        if fn := self.on_current_index_changed:
            fn(index)  # pylint: disable=not-callable

    def process_touch_state(self, touch):
        for control in self._controls:
            control.process_touch_state(touch)

    def draw(self, display: PicoGraphics, theme: Theme):
        for button in self._controls:
            button.draw(display, theme)


class SystrayPageButton(LatchingButton):
    """
    A LatchingButton with customised presentation for use in the systray
    page selector.
    """

    def draw(self, display: PicoGraphics, theme: Theme):
        theme.draw_systray_page_button_frame(display, self.region, self.is_down)
        if self.title:
            theme.draw_systray_page_button_title(
                display, self.region, self.is_down, self.title, theme.systray_text_rel_scale
            )


class Page:
    """
    The base Page class represents a single screen managed by the
    WindowManager.

    The page will be provided a region in which to draw itself by the
    window manager.

    Subclass a page to implement your drawing code and encapsulate its
    state. You must call the base class initialiser.
    """

    title: str = "Page"
    """
    The title of the page, this will be used by system ui components
    where a reference to the page is needed.
    """

    execution_frequency: int | None = None
    """
    The preferred frequency for page updates. Tick will be called at
    up to this rate, it may be slower if the system is busy.
    """

    needs_update: bool = False
    """
    Set to True if the page needs an update in the next available run
    loop cycle.
    """

    _controls: [Control]

    def __init__(self) -> None:
        self._controls = []

    def setup(self, region: Region, window_manager: "WindowManager"):
        """
        Called whenever the pages content region changes (and when the
        page is first shown).

        This is an opportunity to create any persistent controls, and
        perform any other house keeping. Not that this may be called
        multiple times during the lifetime of the page, should its
        available region change for any reason.

        There is no need to call the base class implementation.
        """

    def will_show(self):
        """
        Prepares the page for display.

        This will be called before tick, when the page transitions to
        being visible.
        """

    def tick(self, region: Region, window_manager: "WindowManager"):
        """
        The update function for a Page.

        Implement this to do any drawing or touch handling you may
        required. It will be called at up to the requested
        execution_frequency, and at maximum rate when any touch
        interactions occur.

        Drawing will be clipped to the supplied region by the window
        manager. The to_screen helper can be used to map coordinates in
        this region to the screen.

        The supplied WindowManager instance provides access to the
        display and streamlined update calls.

        Use the window_manager.theme and its properties to draw content
        where consistency with other pages is required.

        The default implementation ensures controls are processed prior
        to drawing, so their current state is accurately reflects the
        state of user interactivity. _draw is then called, and controls
        are drawn on top.
        """
        self._tick(region, window_manager)
        window_manager.update_display(region)

    def will_hide(self):
        """
        Prepares the page for display.

        This will be called when the page transitions to a no longer
        visible state.
        """

    def teardown(self):
        """
        Called before a page is removed.
        """
        self._controls = []

    def _tick(self, region: Region, window_manager: "WindowManager"):

        display = window_manager.display
        touch = window_manager.os.touch
        theme = window_manager.theme

        for control in self._controls:
            control.process_touch_state(touch)

        self._update(window_manager.os)
        self._draw(display, region, theme)

        for control in self._controls:
            control.draw(display, theme)

    def _update(self, os: OS):
        """
        The default implementation of tick will call this method to
        allow any updates to be performed after touches have been
        processed, before the screen is drawn.

        This is an opportunity to update LEDs or button titles, etc.
        """

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):
        """
        The default implementation of tick will call this method to draw
        non-interactive page content.

        There is no need to update the display, this will be done for
        the content region after controls have been done.
        """


class StaticPage(Page):
    """
    A specialisation of pages that only updates when requested (by
    setting self.needs_update), or through touch interactions.
    """

    @property
    def execution_frequency(self):
        """
        Execution frequency is fixed at 0 for static pages that manually
        request updates.
        """
        return 0


class Systray(Page):
    """
    A (notionally private) page that presents a tabbed page switcher,
    and optional "accessories" that appear before or after the page
    switcher.
    """

    title = "Systray"

    class Accessory(Page):
        """
        A specialisation of Page that can be added to the systray.

        Accessories do not have their own update/draw cycle, and are
        ticked by the systray itself.

        As they appear in the tray for all pages, they can be used for
        things like clocks, or buttons that open additional UI elements
        or controls.
        """

        POSITION_LEADING = "leading"
        POSITION_TRAILING = "trailing"

        def size(self, max_size: Size, window_manager: "WindowManager") -> Size:
            """
            Determines the size of the accessory, this must fit within
            the specified maximum size..

            This must be implemented by accessories and will be used to
            determine the absolute screen region available to the
            accessory for content.

            :param max_size: The total available space for the accessory.
            :param window_manager: The window manager the accessory will
              be drawn by.
            :return: The size of the supplied region used by the accessory.
            """
            raise NotImplementedError("Accessory must implement size to return the used region")

    accessory_positions = (Accessory.POSITION_LEADING, Accessory.POSITION_TRAILING)
    """
    A list of valid accessory positions.
    """

    __os: OS

    __pages: [Page]
    __page_radio_button: RadioButton = None

    __leading_accessories: [Accessory]
    __leading_accessory_regions: [Region]
    __trailing_accessories: [Accessory]
    __trailing_accessory_regions: [Region]

    def __init__(self) -> None:
        super().__init__()
        self.__pages = []
        self.__leading_accessories = []
        self.__leading_accessory_regions = []
        self.__trailing_accessories = []
        self.__trailing_accessory_regions = []

    def setup(self, region: Region, window_manager: "WindowManager"):
        """
        Ensure we have controls for the wm's pages, and they're in the
        right place. Calculates screen regions for any registered
        accessories.
        """

        self._controls = []
        self.__page_radio_button = None
        self.__os = window_manager.os

        pager_region = self.__setup_accessories(region, window_manager)
        self.__setup_page_switcher(pager_region, window_manager)

    def set_current_page(self, page: Page):
        """
        Update which page is considered current.
        """
        if page not in self.__pages:
            return

        page_index = self.__pages.index(page)
        if radio := self.__page_radio_button:
            radio.set_current_index(page_index)

        self.needs_update = True

    def add_accessory(self, accessory: Accessory, position: str, index: int = -1):
        """
        Adds an accessory to the systray. These can be drawn
        before/after the page selector.

        :param accessory: The accessory to add.
        :param position: Where the accessory should be drawn, relative to
          the page switcher. See accessory_positions.
        :param index: Where to insert the accessory relative to other
          accessories in the same position.
        :raises ValueError: If an unknown position is specified.
        """
        if not isinstance(accessory, Systray.Accessory):
            raise ValueError(f"Must be an instance of {Systray.Accessory}")
        if position not in self.accessory_positions:
            raise ValueError(
                f"Unrecognised position '{position}' must be one of {self.accessory_positions}"
            )

        target = (
            self.__leading_accessories
            if position == self.accessory_positions[0]
            else self.__trailing_accessories
        )
        if index < 0:
            target.append(accessory)
        else:
            target.insert(index, accessory)

    def remove_accessory(self, accessory: Accessory):
        """
        Removes an accessory previously registered with add_accessory.

        :param accessory: The accessory to remove.
        :raises ValueError: If the accessory was not registered.
        """
        if accessory in self.__leading_accessories:
            accessory.teardown()
            self.__leading_accessories.remove(accessory)
        elif accessory in self.__trailing_accessories:
            accessory.teardown()
            self.__trailing_accessories.remove(accessory)
        else:
            raise ValueError("Unkown accessory")

    def accessories(self) -> (tuple[Accessory], tuple[Accessory]):
        """
        Lists the accessories currently registered with the systray.

        :return: Lists of leading and trailing accessories.
        """
        return tuple(self.__leading_accessories), tuple(self.__trailing_accessories)

    def will_show(self):
        for accessory in self.__leading_accessories:
            accessory.will_show()
        for accessory in self.__trailing_accessories:
            accessory.will_show()

    def will_hide(self):
        for accessory in self.__leading_accessories:
            accessory.will_hide()
        for accessory in self.__trailing_accessories:
            accessory.will_hide()

    def teardown(self):
        for accessory in self.__leading_accessories:
            accessory.teardown()
        for accessory in self.__trailing_accessories:
            accessory.teardown()

    def _tick(self, region: Region, window_manager: "WindowManager"):
        """
        Re-implements _tick to draw the systray background, and _tick
        the systray accessories.
        """
        display = window_manager.display
        touch = window_manager.os.touch
        theme = window_manager.theme

        for control in self._controls:
            control.process_touch_state(touch)

        theme.draw_systray(display, region)

        for accessory, acc_region in zip(
            self.__leading_accessories, self.__leading_accessory_regions
        ):
            accessory._tick(acc_region, window_manager)
        for accessory, acc_region in zip(
            self.__trailing_accessories, self.__trailing_accessory_regions
        ):
            accessory._tick(acc_region, window_manager)

        for control in self._controls:
            control.draw(display, theme)

    def __setup_accessories(self, region: Region, window_manager: "WindowManager") -> Region:
        """
        Configures accessories, and returns the region available for the
        pager.
        """
        for accessory_list, region_list, trailing in (
            (self.__leading_accessories, self.__leading_accessory_regions, False),
            (self.__trailing_accessories, self.__trailing_accessory_regions, True),
        ):
            region_list.clear()
            if accessory_list:
                region, accessory_regions = self.__setup_positional_accesories(
                    region, accessory_list, window_manager, trailing=trailing
                )
                region_list.extend(accessory_regions)

        return region

    def __setup_positional_accesories(
        self,
        region: Region,
        accessories: [Accessory],
        window_manager: "WindowManager",
        trailing: bool = False,
    ) -> (Region, [Region]):
        """
        Calls size and setup for the supplied accessories, with an
        increasingly constrained region, based on the space used by the
        last accessory.

        Note: This naive version makes no attempts to enforce bounds.
        """
        regions = []
        for accessory in accessories:
            acc_size = accessory.size(Size(region.width, region.height), window_manager)
            remaning_width = region.width - acc_size.width
            acc_region = Region(
                region.x + remaning_width if trailing else region.x,
                region.y,
                acc_size.width,
                acc_size.height,
            )
            accessory.setup(acc_region, window_manager)
            regions.append(acc_region)
            region = Region(
                region.x if trailing else region.x + acc_size.width,
                region.y,
                remaning_width,
                region.height,
            )
        return region, regions

    def __setup_page_switcher(self, region: Region, window_manager: "WindowManager"):

        self.__page_radio_button = None

        self.__pages = window_manager.pages()
        if not self.__pages:
            return

        titles = [p.title for p in self.__pages]

        current_page_index = 0
        if current_page := window_manager.current_page:
            current_page_index = self.__pages.index(current_page)

        def page_index_changed(new_index: int):
            window_manager.set_current_page(self.__pages[new_index])

        self.__page_radio_button = RadioButton(
            region,
            titles,
            current_index=current_page_index,
            control_class=SystrayPageButton,
        )
        self.__page_radio_button.on_current_index_changed = page_index_changed

        self._controls.append(self.__page_radio_button)


class WindowManager:
    """
    Not really a "window" manager, but it fulfills notionally the same
    role as one.

    The WindowManager tracks and manages multiple pages, but only a
    single page is presented to the user a one time. Methods are exposed
    to Programmatically manipulate the current page, as well as an
    optional 'systray' that presents a page switching interface to the
    user.

    In addition, system level messages will be drawn as full screen
    overlay if they are of a severity equal or greater  to
    system_message_level.
    """

    display: PicoGraphics
    theme: Theme

    system_message_level = MSG_WARNING

    os: OS

    __pages: []
    __page_tasks: {Page, OS.Task}
    __current_page: Page = None
    __last_page: Page = None
    __pages_need_setup: bool = True

    __content_region: Region

    __systray_visible: bool = None
    __systray_position: str = "bottom"
    __systray_region: Region

    __systray_page: Systray | None = None
    __systray_task: OS.Task = None
    __systray_needs_setup: bool = True
    __systray_needs_update: bool = True

    __messages: []

    def __init__(
        self,
        os_: OS,
        theme: Theme = None,
        display_system_messages=True,
        systray_visible: bool = False,
    ):

        self.__pages = []
        self.__page_tasks = {}

        self.os = os_
        self.display = os_.display
        self.theme = theme or DefaultTheme()
        self.theme.setup(self.display)

        self.__create_systray()
        self.set_systray_visible(systray_visible)

        # As we use the main os run loop to run pages (with their
        # respective intervals), we need to be first up so we can
        # enable/disable the page specific tasks as needed.
        self.os.add_task(self.tick, index=0)

        self.__messages = []
        if display_system_messages:
            self.os.add_message_handler(self.os_msg)

    @property
    def content_region(self):
        """
        Determines the area of the display that can be used for content.
        """
        return self.__content_region

    def __set_content_region(self, region: Region):
        self.__content_region = region
        self.__pages_need_setup = True

    @property
    def systray_region(self):
        """
        Determines the area of the display that can be used for the systray.
        """
        return self.__systray_region

    def __set_systray_region(self, region: Region):
        self.__systray_region = region
        self.__systray_needs_setup = True

    @property
    def systray_position(self) -> str:
        """
        The current position of the systray when visible.
        """
        return self.__systray_position

    def set_systray_position(self, position: str):
        """
        Sets the position of the systray when visible.

        :param position: The position, either "top" or "bottom".
        :raises ValueError: If an unknown position is specified.
        """
        if position == self.systray_position:
            return
        if position not in ("top", "bottom"):
            raise ValueError(f"Unknown systray position '{position}', must be 'top' or 'bottom'")
        self.__systray_position = position
        self.__update_regions()

    @property
    def systray_visible(self) -> bool:
        """
        Whether the systray is currently visible.
        :return: True if the systray will be drawn at the next tick.
        """
        return self.__systray_visible

    def set_systray_visible(self, is_visible: bool):
        """
        Sets whether the systray is visible after the next tick.
        """
        if is_visible == self.__systray_visible:
            return
        self.__systray_visible = is_visible
        self.__update_regions()

    def add_systray_accessory(self, accessory: Systray.Accessory, position: str, index: int = -1):
        """
        Adds an accessory to the systray. These can be drawn
        before/after the page selector.

        :param accessory: The accessory to add.
        :param position: Where the accessory should be drawn, relative to
          the page switcher. See accessory_positions.
        :param index: Where to insert the accessory relative to other
          accessories in the same position.
        :raises ValueError: If an unknown position is specified.
        """
        self.__systray_page.add_accessory(accessory, position=position, index=index)
        self.__systray_needs_setup = True

    def remove_systray_accessory(self, accessory: Systray.Accessory):
        """
        Removes a previously registered accessory.

        :param accessory: The accessory to remove.
        :raises ValueError: If the accessory was not registered.
        """
        self.__systray_page.remove_accessory(accessory)
        self.__systray_needs_setup = True

    def systray_accessories(self) -> (tuple[Systray.Accessory], tuple[Systray.Accessory]):
        """
        Lists the accessories currently registered with the systray.

        :return: A tuple containing lists of leading and trailing
          accessories.
        """
        return self.__systray_page.accessories()

    def __update_regions(self):
        content_region, systray_region = self.__calculate_regions(
            self.display, self.__systray_visible, self.systray_position, self.theme
        )
        self.__set_content_region(content_region)
        self.__set_systray_region(systray_region)

    def tick(self):
        """
        The main window manage tick callback, executed from the OS
        run loop.
        """
        self.__upadate_pages()
        self.__update_systray()

    def update_display(self, *args, **kwargs):
        """
        Updates the display. See OS.update_display.
        """
        return self.os.update_display(*args, **kwargs)

    def os_msg(self, msg: str, severity: int):
        """
        A handler for OS messages, currently presents them as a
        full-screen overlay.
        """
        self.__messages.append((msg, severity))
        if len(self.__messages) > 10:
            self.__messages = self.__messages[-10:]

        if severity < self.system_message_level:
            return

        # TODO: Don't update the whole display
        display_messages = [
            f"{MSG_SEVERITY_NAMES[s]}: {m}"
            for m, s in self.__messages
            if s >= self.system_message_level
        ]
        full_screen = Region(0, 0, *self.display.get_bounds())
        self.theme.draw_strings(self.display, display_messages, full_screen)
        self.update_display()

    def add_page(self, page: Page, make_current: bool = False):
        """
        Adds a page to the window manager.

        Once added, a page can be made current, or navigated to using
        next_page, and previous_page. Pages are cycled in the order
        added.

        :param page: The page to add.
        :param make_current: Set to True if this page should become the
          current page.
        """
        self.__pages.append(page)
        self.__page_tasks[page] = self.os.add_task(
            lambda: self.__tick_page(page),
            execution_frequency=page.execution_frequency,
            active=False,
        )

        if make_current:
            self.set_current_page(page)

        self.__pages_changed()

        self.os.post_message(f"Added page '{page.title}' (make_current: {make_current})")

    def remove_page(self, page: Page):
        """
        Removes a previously registered page.

        :param page: A previously registered page to remove.
        :raises ValueError: If the page is not in the pages list.
        """
        if page not in self.__pages:
            raise ValueError("Page not known to the window manager")

        self.__pages.remove(page)
        self.os.remove_task(self.__page_tasks[page])
        del self.__page_tasks[page]

        page.teardown()

        if self.__current_page is page:
            self.set_current_page(self.__pages[-1])

        self.__pages_changed()

        self.os.post_message(f"Removed page '{page.title}'")

    def pages(self) -> [Page]:
        """
        :return: The list of pages registered with the WindowManager.
        """
        return tuple(self.__pages)

    def set_current_page(self, page: Page):
        """
        Sets the specified page as current, so it will be updated in the
        run loop.

        :param page: A page that has been previously registered using
          add_page.
        :raises ValueError: If the supplied page has not been registered.
        """
        if page not in self.__pages:
            raise ValueError(f"{page.title} is not a registered page")
        self.__current_page = page
        self.__systray_needs_update = True

    def next_page(self):
        """
        Changes the current page to the next one in the page list,
        wrapping to the start.
        """
        self.__change_page(1, 0)

    def prev_page(self):
        """
        Changes the current page to the previous one in the page list,
        wrapping to the end.
        """
        self.__change_page(-1, -1)

    @property
    def current_page(self) -> Page | None:
        """
        Returns the page being actively updated in the run loop.
        """
        return self.__current_page

    def __change_page(self, offset, fallback):
        """
        Handles navigation backwards/forwards through pages, wrapping
        when navigation reaches the end/beginning of the page list.
        """
        if not self.__pages:
            return
        if self.current_page is None:
            page_index = fallback
        else:
            page_index = self.__pages.index(self.current_page)
            page_index = (page_index + offset) % len(self.__pages)
        self.set_current_page(self.__pages[page_index])

    def __tick_page(self, page):
        """
        Updates a page, ensuring the drawing region is clipped.
        """
        self.display.set_clip(*self.content_region)
        page.tick(self.content_region, self)
        self.display.remove_clip()

    def __pages_changed(self):
        """
        Call whenever the page list changes.
        """
        self.__systray_needs_setup = True

    def __tick_systray(self):
        """
        Updates the systray, ensuring the drawing region is clipped.
        """
        if not self.__systray_visible or not self.__systray_page:
            return

        self.display.set_clip(*self.__systray_region)
        self.__systray_page.tick(self.__systray_region, self)
        self.display.remove_clip()

    def __upadate_pages(self):
        """
        Handles the transition between current pages, calling the
        lifecycle hooks around the transition.

        This page doesn't actually update the page itself, this is
        handled by the run loop, this function instead manages the
        active states of the page tasks in the run loop.
        """

        # Potential flaw here is that this relies on the WM task being
        # first in the list. Shouldn't be a problem in common scenarios,
        # but would be nice to make this stable. Worst case it the new
        # page doesn't update until the next tick...

        if self.__pages_need_setup:
            for page in self.__pages:
                page.setup(self.content_region, self)
                # We could make page set this in setup, but then
                # everyone would need to call the base class method, and
                # they're only going to forget...
                # We could wrap it, but then that's potentially less
                # intuitive too for some... 🤷
                page.needs_update = True
            self.__pages_need_setup = False

        for page in self.__pages:
            if not page.needs_update:
                continue
            page.needs_update = False
            self.__page_tasks[page].enqueue()

        if self.__current_page == self.__last_page:
            return

        if self.__last_page:
            self.__last_page.will_hide()

        if self.__current_page:
            self.__current_page.will_show()

        # Update page task active states so only the current page runs
        for page, task in self.__page_tasks.items():
            task.active = page is self.__current_page

        self.__last_page = self.__current_page

    def __create_systray(self):
        """
        Creates the systray and registers its task.
        """
        self.__systray_page = Systray()
        self.__systray_task = self.os.add_task(
            self.__tick_systray, execution_frequency=1, active=False
        )

    def __update_systray(self):
        """
        Handles setup, configuration and update of systray state.

        TODO: This needs factoring out into Page.needs_setup or similar.
        """
        self.__systray_task.active = self.__systray_visible

        if self.__systray_needs_setup:
            if self.__systray_visible:
                self.__systray_page.setup(self.__systray_region, self)
                self.__systray_page.will_show()
                self.__systray_page.needs_update = True
            else:
                self.__systray_page.will_hide()
                self.__systray_page.teardown()

        elif self.__systray_needs_update and self.__systray_visible:
            self.__systray_page.set_current_page(self.__current_page)

        self.__systray_needs_setup = False
        self.__systray_needs_update = False

        if self.__systray_visible and self.__systray_page.needs_update:
            self.__systray_task.enqueue()
            self.__systray_page.needs_update = False

    @staticmethod
    def __calculate_regions(
        display: PicoGraphics, systray_visible: bool, systray_position: str, theme: Theme
    ) -> (Region, Region):

        display_width, display_height = display.get_bounds()

        if not systray_visible:
            return Region(0, 0, display_width, display_height), Region(0, 0, 0, 0)

        content_height = display_height - theme.systray_height

        if systray_position == "top":
            content_y = theme.systray_height
            systray_y = 0
        else:  # "bottom"
            content_y = 0
            systray_y = display_height - theme.systray_height

        return (
            Region(0, content_y, display_width, content_height),
            Region(0, systray_y, display_width, theme.systray_height),
        )
