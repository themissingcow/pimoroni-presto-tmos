# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for Theme logic
"""
from unittest import mock

import pytest

from picographics import PicoGraphics

from tmos import OS
from tmos_ui import DefaultTheme, Page, WindowManager
from tmos_apps import App, AppManager

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name, redefined-outer-name


class Test_App:

    def test_default_app_as_name_and_description(self):

        an_app = App()
        assert isinstance(an_app.name, str)
        assert an_app.description == ""

    def test_default_pages_method_raises_NotImplementedError(self):

        an_app = App()
        with pytest.raises(NotImplementedError):
            an_app.pages()


class Test_AppManager_apps:

    def test_when_constucted_then_apps_empty(self, a_wm):

        am = AppManager(a_wm)
        assert am.apps() is ()

    def test_when_constucted_then_wm_pages_unchanged(self, a_wm):

        expected_pages = a_wm.pages()
        expected_current = a_wm.current_page
        AppManager(a_wm)
        assert a_wm.pages() == expected_pages
        assert a_wm.current_page == expected_current

    def test_when_app_added_then_in_apps_list(self, an_app_manager, an_app_factory):

        app_a = an_app_factory()
        app_b = an_app_factory()
        an_app_manager.add_app(app_a)
        assert an_app_manager.apps() == (app_a,)
        an_app_manager.add_app(app_b)
        assert an_app_manager.apps() == (app_a, app_b)

    def test_when_added_with_make_current_not_specified_then_app_is_not_made_current(
        self, an_app_manager, an_app
    ):

        an_app_manager.add_app(an_app)
        assert an_app_manager.current_app is None

    def test_when_added_with_make_current_false_then_app_is_not_made_current(
        self, an_app_manager, an_app
    ):

        an_app_manager.add_app(an_app, make_current=False)
        assert an_app_manager.current_app is None

    def test_when_added_with_make_current_true_then_app_is_made_current(
        self, an_app_manager, an_app
    ):

        an_app_manager.add_app(an_app, make_current=True)
        assert an_app_manager.current_app is an_app

    def test_when_app_made_curent_then_current_app_updatred(self, an_app_manager, an_app):

        an_app_manager.add_app(an_app, make_current=False)
        an_app_manager.set_current_app(an_app)
        assert an_app_manager.current_app is an_app

    def test_when_unregistered_app_made_current_then_ValueError_raised(
        self, an_app_manager, an_app
    ):

        with pytest.raises(ValueError):
            an_app_manager.set_current_app(an_app)

    def test_when_app_added_without_make_current_then_wm_pages_unchanged(
        self, a_wm, an_app_factory
    ):

        expected_pages = a_wm.pages()
        expected_current = a_wm.current_page
        am = AppManager(a_wm)
        am.add_app(an_app_factory())
        assert a_wm.pages() == expected_pages
        assert a_wm.current_page == expected_current

    def test_when_app_added_with_make_current_true_then_wm_pages_updated_and_first_made_current(
        self, a_wm, an_app_factory
    ):

        an_app = an_app_factory()
        app_pages = an_app.pages()
        am = AppManager(a_wm)
        am.add_app(an_app, make_current=True)
        assert a_wm.pages() == app_pages
        assert a_wm.current_page == app_pages[0]

    def test_when_app_made_current_then_wm_pages_updated_and_first_made_current(
        self, a_wm, an_app_factory
    ):

        app_a = an_app_factory()
        app_b = an_app_factory()
        am = AppManager(a_wm)
        am.add_app(app_a, make_current=True)
        am.add_app(app_b)
        assert a_wm.pages() == app_a.pages()
        assert a_wm.current_page == app_a.pages()[0]
        am.set_current_app(app_b)
        assert a_wm.pages() == app_b.pages()
        assert a_wm.current_page == app_b.pages()[0]

    def test_when_current_app_is_made_current_then_is_noop(self, an_app):

        mock_wm = mock.create_autospec(WindowManager, instance=True)
        mock_wm.os = OS()
        am = AppManager(mock_wm)
        am.add_app(an_app, make_current=True)
        mock_wm.remove_all_pages.assert_called_once()
        mock_wm.reset_mock()
        assert am.current_app is an_app
        am.set_current_app(an_app)
        mock_wm.remove_all_pages.assert_not_called()


@pytest.fixture
def a_wm():
    return WindowManager(OS())


@pytest.fixture
def an_app_factory():
    """
    A factory to make mock apps with 2 pages
    """

    def make():
        p1 = Page()
        p1.title = "One"
        p2 = Page()
        p2.title = "Teo"
        app = mock.create_autospec(App, instance=True)
        app.name = "Some app"
        app.description = "A desc"
        app.pages.return_value = (p1, p2)
        return app

    return make


@pytest.fixture
def an_app(an_app_factory):
    return an_app_factory()


@pytest.fixture
def an_app_manager(a_wm):
    return AppManager(a_wm)
