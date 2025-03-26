# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
The Missing "OS": App Switcher

The app switch builds on the base OS/WindowManager to allow easy
switching of smaller, independent apps. Each app has its own set of
pages. A single app is current at any one time.

The AppManager class manages the page list of a particular WindowManager
instance.
"""

from picographics import PicoGraphics

from tmos import Region, Size
from tmos_ui import MomentaryButton, Page, StaticPage, Systray, Theme, WindowManager, inset_region


class App:

    name: str = "Unnamed Application"
    description: str = ""

    def pages(self) -> [Page]:
        """
        Retrieve a list of pages for the application.

        :return: The apps pages, the implementation can reuse a single
          set of initialised pages across multiple calls to this method.
        """
        raise NotImplementedError("App classes must implement the pages method")


class AppManagerAccessory(Systray.Accessory):

    on_open_switcher = None

    class AppSwitcherButton(MomentaryButton):

        def __init__(self, region: Region) -> None:
            super().__init__(region, "")

        def draw(self, display: PicoGraphics, theme: Theme):
            theme.draw_app_switcher_button(display, self.region, self.is_down)

    def size(self, max_size: Size, window_manager: "WindowManager") -> Size:
        return Size(max_size.height, max_size.height)

    def setup(self, region: Region, window_manager: "WindowManager"):

        button_region = inset_region(region, 2, 2)
        button = self.AppSwitcherButton(button_region)
        button.on_button_up = self.on_open_switcher
        self._controls = [button]


class AppSwitcher(StaticPage):
    """
    A page that presents a list of applications, and switches the active
    application.
    """

    title = "App Switcher"

    on_app_changed = None

    def __init__(self, apps: [App]) -> None:
        super().__init__()
        self.__apps = apps

    def setup(self, region: Region, window_manager: WindowManager):

        self._controls = []

        p = window_manager.theme.padding
        button_height = window_manager.theme.control_height

        def add_app_button(app: App, y: int) -> int:
            button_region = Region(region.x + p, region.y + y, region.width - p - p, button_height)
            show_button = MomentaryButton(button_region, app.name, title_rel_scale=2)
            # pylint: disable=not-callable
            show_button.on_button_up = lambda: self.on_app_changed(app)
            self._controls.append(show_button)
            return y + button_height + p

        max_y = region.height - button_height - p - p

        y = p
        for app in self.__apps:
            y = add_app_button(app, y)
            if y > max_y:
                break

    def _draw(self, display: PicoGraphics, region: Region, theme: Theme):
        theme.clear_display(display)


class AppManager:
    """
    A layer on top of the WindowManager that allows multiple
    applications to registered and switched between.

    Each app (see: App) has its own set of pages. A single app can be
    made active at once.

    The AppManger provides a themeable systray accessory that can be
    used to show a modal app switcher. Lets not kid ourselves, its
    pretty basic though.
    """

    __apps: [App]
    __current_app: App | None = None
    __window_manager: WindowManager

    def __init__(self, window_manager: WindowManager) -> None:
        """
        Constructs a new instance that will manage the page list of the
        supplied window manager.

        :param window_manager: The window manager whose pages will be
          managed.
        """
        self.__apps = []
        self.__current_app = None
        self.__window_manager = window_manager

    def systray_accessory(self) -> Systray.Accessory:
        """
        Returns a systray accessory button that can be used to open
        a basic modal app switcher UI.

        :return: The systray accessory, see:
            WindowManager.add_systray_accessory
        """
        accessory = AppManagerAccessory()
        accessory.on_open_switcher = self.open_switcher
        return accessory

    def add_app(self, app: App, make_current: bool = False):
        """
        Adds an app to the AppManger's list of apps.

        :param  The app to add.
        :param make_current: Whether the window manager's page list
          should be immediately updated to those of this app (see:
          set_current_app)
        """
        self.__apps.append(app)
        if make_current:
            self.set_current_app(app)
        self.__window_manager.os.post_message(
            f"Added app '{app.name}' (make_current: {make_current})"
        )

    def apps(self) -> [App]:
        """
        Returns the apps currently registered with the manager.

        :return: An immutable list of apps.
        """
        return tuple(self.__apps)

    @property
    def current_app(self) -> App | None:
        """
        The currently active app or None.
        """
        return self.__current_app

    def set_current_app(self, app: App | None):
        """
        Updates the active app, replacing the window manager's pages
        with those of the app. The first page of the app will be made
        the current page.

        :param app: The app to make current, if this app is already
          current then it is a no-op.
        :raises ValueError: If the supplied app is not registered with
          the app manager.
        :raises RuntimeError: If the app provides no pages.
        """
        if app not in self.__apps:
            raise ValueError(f"{app.name} is not a registered app")
        if app is self.__current_app:
            return
        self.__current_app = app

        self.__window_manager.remove_all_pages()
        app_pages = app.pages()
        if not app_pages:
            raise RuntimeError(f"{app.name} provided no pages")
        for page in app_pages:
            self.__window_manager.add_page(page)
        self.__window_manager.set_current_page(app_pages[0])

    def open_switcher(self):
        """
        Opens a simple modal app switcher, that auto-closes when an app
        is selected.
        """

        def select_app(app: App):
            self.__window_manager.clear_modal_page()
            self.set_current_app(app)

        swithcher = AppSwitcher(self.apps())
        swithcher.on_app_changed = select_app
        self.__window_manager.show_modal_page(swithcher)
