# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
The Missing "OS": UI Layer
"""
import math

from picographics import PicoGraphics

from tmos import OS, Region, MSG_INFO, MSG_FATAL, MSG_SEVERITY_NAMES


__all__ = [
    "Control",
    "DefaultTheme",
    "Page",
    "PushButton",
    "Theme",
    "WindowManager",
    "is_within",
    "to_screen",
]


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


class Theme:
    """
    The encapsulation of a color scheme and presentation of UI elements.

    A theme can be used for it's palette, and to draw on-screen graphics
    consistently.

    Themes are responsible for drawing well-known WindowManager controls and UI elements. If
    extending these, use the drawing mechanisms exposed by the theme if you want them to match
    other elements.

    Use the base picographcs APIs if full flexibility is
    required.
    """

    foreground_pen: int
    """
    The preferred pen to use for text and other primary content.
    """

    background_pen: int
    """
    The preferred pen to use for empty areas.
    """

    error_pen: int
    """
    The preferred pen to use for highlighting errors or other
    failure-related information.
    """

    font: str
    """
    A PicoGraphics.set_font compatible font name (af fonts are not
    currently supported).
    """

    default_font_scale: int
    """
    The default font scale to use for drawing text.
    """

    line_height: int
    """
    The height of a line (in pixels) for a font-scale of 1.

    Eg, for "bitmap8", set a value near 10, regardless of the value of
    default_font_scale.
    """

    padding: int = 10
    """
    The preffered padding value to add around UI elements.
    """

    def setup(self, display: PicoGraphics):
        """
        Configures the theme for the supplied display.

        This will be called by the WindowManager, and does not need to
        be called in user code in most common use cases.

        This should be implemented by a theme to  initialise pens,
        fonts, and other properties appropriately for the supplied
        display.
        """
        raise NotImplementedError("Theme must implement setup")

    def line_spacing(self, scale: int | None = None) -> int:
        """
        Determines the line height of the themes text. This can be used to ensure multiple draw
        calls are spaced appropriately.

        This factors in the themes default_font_scale if a custom scale
        is not specified.

        :param scale: The scale of text to be drawn, overriding the
          themes default_font_scale.
        :return: The preferred line height in pixels, including spacing.
        """
        return self.line_height * (scale or self.default_font_scale)

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

    def text(self, display: PicoGraphics, text: str, *args, scale: int | None = None, **kwargs):
        """
        Draws text, additional args as pre PicoGraphics.text.

        NOTE: If the wordwrap arg is provided, as this is handled by
        PicoGraphics, rendering will not respect the themes line_height.

        :param display: The display on which to draw the text.
        :param scale: Overrides the themes default_font_scale.
        :param text:  The string to render.
        """
        display.text(text, *args, scale=self._text_scale(scale), **kwargs)

    def centered_text(
        self,
        display: PicoGraphics,
        region: Region,
        text: str,
        *args,
        scale: int | None = None,
        **kwargs,
    ):
        """
        Draws single line text approximately centered within the region.

        See @text for other args.
        """
        scale = self._text_scale(scale)
        height = self.line_spacing(scale)
        text_width = display.measure_text(text, scale)

        cx = region.x + (region.width // 2)
        cy = region.y + (region.height // 2)

        x = cx - (text_width // 2)
        y = cy - (height // 2)

        self.text(display, text, x, y, *args, scale=scale, **kwargs)

    def draw_strings(
        self, display: PicoGraphics, messages: [str], region: Region, scale: int | None = None
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
        scale = self._text_scale(scale)

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
                scale=scale,
            )
            # Work out how many lines we consumed, measure_text only
            # gives a width.
            # TODO: The +1 is for a fudge for the fact that
            # we're calculating character wrap not word wrap
            # It's super inaccurate though.
            text_width = display.measure_text(message, scale)
            num_lines = math.ceil(text_width / wrap_width)
            if num_lines > 1:
                num_lines += 1
            offset += self.line_spacing(scale) * num_lines
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

    #pylint: disable=too-many-arguments
    def draw_button_title(
        self, display: PicoGraphics, region: Region, is_pressed: bool, title: str, title_scale: int
    ):
        """
        Draws the frame/background for an on-screen "button"

        :param display: The display to draw the messages on.
        :param region: The bounds of the button.
        :param is_pressed: Whether the button is currently pressed.
        :param title: The button title.
        :param title_scale: The font scale to draw the title with.
        """
        display.set_pen(self.foreground_pen if is_pressed else self.background_pen)
        self.centered_text(display, region, title, scale=title_scale)

    def _text_scale(self, scale: int | None = None) -> int:
        """
        A helper to determine text scale to draw, taking an optional
        override.

        :param scale: A custom scale that overrides the themes default.
        :return: The text scale to use.
        """
        return scale or self.default_font_scale


class DefaultTheme(Theme):
    """
    A simple black-and-white theme.
    """

    def setup(self, display: PicoGraphics):

        w, h = display.get_bounds()

        self.foreground_pen = display.create_pen(0, 0, 0)
        self.background_pen = display.create_pen(255, 255, 255)
        self.error_pen = display.create_pen(200, 0, 0)
        self.font = "bitmap8"
        self.line_height = 8

        self.default_font_scale = 4 if w > 240 else 2


class Control:
    """
    A base for interactive elements.

    We don't make use of the stock Presto Button, etc as they manage
    global state. This isn't compatible with the multi-page model, where
    only one of many pages will be visible at any given time.

    We also introduce a more html style even model to controls.
    """

    def process_touch_state(self, touch):
        pass

    def tick(self, display: PicoGraphics, theme: Theme):
        pass

    def _event(self, event_name: str, *args, **kwargs):
        fn = getattr(self, event_name)
        if fn:
            fn(*args, **kwargs)


class PushButton(Control):

    title: str
    title_rel_scale: float
    region: Region

    is_down: bool = False

    on_button_down = None
    on_button_up = None
    on_button_cancel = None

    def __init__(self, region: Region, title: str = "", title_rel_scale=1) -> None:
        self.region = region
        self.title = title
        self.title_rel_scale = title_rel_scale

    def process_touch_state(self, touch):

        touch_active = touch.state
        touch_is_inside = touch_active and is_within(self.region, touch.x, touch.y)

        if touch_is_inside:
            if not self.is_down:
                self._event("on_button_down")
        else:
            if not touch_active:
                # Touch ended within our region
                if self.is_down:
                    self._event("on_button_up")
            elif self.is_down:
                # The touch has moved out side our area, we don't count
                # this as a button up as its a common way to 'cancel' a
                # press.
                self._event("on_button_cancel")

        self.is_down = touch_is_inside

    def draw(self, display: PicoGraphics, theme: Theme):

        scale = round(theme.default_font_scale * self.title_rel_scale)

        theme.draw_button_frame(display, self.region, self.is_down)
        if self.title:
            theme.draw_button_title(display, self.region, self.is_down, self.title, scale)


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

    _controls: [Control]

    def __init__(self) -> None:
        self._controls = []

    def setup(self, region: Region, window_manager: "WindowManager"):
        pass

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
        display = window_manager.display
        touch = window_manager.os.touch
        theme = window_manager.theme

        for control in self._controls:
            control.process_touch_state(touch)

        self._draw(display, region, theme)

        for control in self._controls:
            control.draw(display, theme)

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

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):
        """
        The default implementation of tick will call this method to draw
        non-interactive page content.

        There is no need to update the display, this will be done for
        the content region after controls have been done.
        """


class WindowManager:

    display: PicoGraphics
    theme: Theme

    system_message_level = MSG_INFO

    os: OS

    __pages: []
    __page_tasks: {Page, OS.Task}
    __current_page: Page = None
    __last_page: Page = None
    __pages_need_setup: bool = True

    __messages: []

    def __init__(self, os_: OS, theme: Theme = None, display_system_messages=True):

        self.__pages = []
        self.__page_tasks = {}

        self.os = os_
        self.display = os_.display
        self.theme = theme or DefaultTheme()
        self.theme.setup(self.display)

        self.__set_content_region(Region(0, 0, *os_.display.get_bounds()))

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
        self.__pages_need_setup

    def tick(self):
        """
        The main window manage tick callback, executed from the OS
        runloop.
        """
        self.__upadate_pages()

    def update_display(self, *args, **kwargs):
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
        self.theme.draw_strings(self.display, display_messages, full_screen, scale=1)
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
            self.__pages_need_setup = False

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
