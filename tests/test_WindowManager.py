# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for the WindowManager implementation. Designed to run
off-platform, they focus on the specifics of the business logic and
advertised functionality.
"""

from unittest import mock

import pytest

from tmos import OS, Region
from tmos_ui import DefaultTheme, Page, Theme, WindowManager

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name, redefined-outer-name
# pylint: disable=attribute-defined-outside-init
# pylint: disable=too-few-public-methods


class Test_WindowManager_init:

    def test_when_theme_not_supplied_then_DefaultTheme_is_used(self):

        os_instance = OS()
        wm = WindowManager(os_instance)
        assert isinstance(wm.theme, DefaultTheme)

    def test_when_theme_supplied_then_setup_is_called_with_display_and_dpi(self):

        mock_theme = mock.create_autospec(Theme, instance=True)

        os_instance = OS()
        os_instance.display.get_bounds.return_value = (240, 240)
        wm = WindowManager(os_instance, theme=mock_theme)
        mock_theme.setup.assert_called_once_with(wm.display, 1)
        mock_theme.reset_mock()
        os_instance.display.get_bounds.return_value = (480, 480)
        wm = WindowManager(os_instance, theme=mock_theme)
        mock_theme.setup.assert_called_once_with(wm.display, 2)

    def test_when_created_then_content_region_matches_display_size(self):

        os_instance = OS()
        wm = WindowManager(os_instance)
        expected_region = Region(0, 0, *os_instance.display.get_bounds())
        assert wm.content_region == expected_region

    def test_exposes_os_instance(self):

        os_instance = OS()
        wm = WindowManager(os_instance)
        assert wm.os is os_instance

    def test_exposes_os_display(self):

        os_instance = OS()
        wm = WindowManager(os_instance)
        assert wm.display is os_instance.display

    def test_exposes_theme(self):

        mock_theme = mock.create_autospec(Theme, instance=True)
        wm = WindowManager(OS(), theme=mock_theme)
        assert wm.theme is mock_theme

    def test_inserts_tick_at_start_of_task_list(self):

        os_instance = OS()
        os_instance.add_task(mock.Mock())
        os_instance.add_task(mock.Mock())
        mock_task_fns = [t.fn for t in os_instance.tasks()]

        wm = WindowManager(os_instance)
        expected_task_fns = [wm.tick, *mock_task_fns]
        task_fns = [t.fn for t in os_instance.tasks()]
        # There may be other tasks (eg: systray tick) that we don't care
        # about in this specific test.
        assert task_fns[: len(mock_task_fns) + 1] == expected_task_fns


class Test_WindowManager_pages:

    def test_when_page_added_then_in_page_list(self, a_wm, a_page):

        a_wm.add_page(a_page)
        assert a_wm.pages() == (a_page,)

    def test_when_page_removed_then_removed_from_page_list(self, a_wm, a_page):

        a_wm.add_page(a_page)
        assert a_wm.pages() == (a_page,)
        a_wm.remove_page(a_page)
        assert a_wm.pages() == ()

    def test_when_last_page_removed_then_current_page_is_none(self, a_wm, a_page):

        a_wm.add_page(a_page)
        a_wm.os.add_task(a_wm.os.stop)
        a_wm.os.run()
        a_wm.remove_page(a_page)
        a_wm.os.run()
        assert a_wm.current_page is None

    def test_when_added_with_make_current_not_specified_then_page_is_not_made_current(
        self, a_wm, a_page
    ):

        a_wm.add_page(a_page)
        assert a_wm.current_page is None

    def test_when_added_with_make_current_false_then_page_is_not_made_current(self, a_wm, a_page):

        a_wm.add_page(a_page, make_current=False)
        assert a_wm.current_page is None

    def test_when_added_with_make_current_true_then_page_is_made_current(self, a_wm, a_page):

        a_wm.add_page(a_page, make_current=True)
        assert a_wm.current_page is a_page

    def test_when_added_with_no_execution_frequency_specified_then_task_interval_is_minus_one(
        self, a_wm, a_page
    ):
        a_page.execution_frequency = None
        prev_tasks = a_wm.os.tasks()
        a_wm.add_page(a_page)
        page_task = next(filter(lambda t: t not in prev_tasks, a_wm.os.tasks()))
        assert page_task.execution_interval_us == -1

    def test_when_added_with_execution_frequency_specified_then_task_has_expected_interval(
        self, a_wm, a_page
    ):
        a_page.execution_frequency = 5
        expected_interval = 1e6 // a_page.execution_frequency
        prev_tasks = a_wm.os.tasks()
        a_wm.add_page(a_page)
        page_task = next(filter(lambda t: t not in prev_tasks, a_wm.os.tasks()))
        assert page_task.execution_interval_us == expected_interval

    def test_when_page_needs_update_then_called_in_next_run_loop(self, a_wm, a_mock_page):
        pytest.skip("Need to figure out a nice way to test this")

    def test_when_run_then_page_setup_called_before_will_show(self, a_wm, a_mock_page):

        a_wm.add_page(a_mock_page, make_current=True)
        a_wm.os.add_task(a_wm.os.stop)
        a_wm.os.run()

        expected_calls = [
            mock.call.setup(a_wm.content_region, a_wm),
            mock.ANY,
            mock.ANY,
            mock.call.will_show(),
        ]

        # For some reason assert_has_calls really doesn't like this arrangement...
        calls = a_mock_page.mock_calls
        first_idx = calls.index(expected_calls[0])
        assert calls[first_idx : first_idx + len(expected_calls)] == expected_calls

    def test_when_current_page_changes_then_will_hide_called_on_previous_page(
        self, a_wm, a_page, a_mock_page
    ):

        # Run with our mock page to make sure it's active
        a_wm.add_page(a_mock_page, make_current=True)
        a_wm.os.add_task(a_wm.os.stop)
        a_wm.os.run()

        # Run with a new page
        a_wm.add_page(a_page, make_current=True)
        a_wm.os.run()
        a_mock_page.will_hide.assert_called_once()

    def test_when_no_page_made_current_then_no_page_ticks(self, a_wm):

        class TestPage(Page):
            pass

        page_a = TestPage()
        page_a.tick = mock.Mock()
        page_b = TestPage()
        page_b.tick = mock.Mock()
        a_wm.add_page(page_a)
        a_wm.add_page(page_b)
        a_wm.os.add_task(a_wm.os.stop)
        a_wm.os.run()

        page_a.tick.assert_not_called()

    def test_when_no_page_set_current_then_no_page_ticks(self, a_wm, a_mock_page_factory):

        page_a = a_mock_page_factory()
        page_b = a_mock_page_factory()
        a_wm.add_page(page_a)
        a_wm.add_page(page_b, make_current=True)
        a_wm.os.add_task(a_wm.os.stop)
        a_wm.os.run()
        page_a.tick.assert_not_called()
        page_b.tick.assert_called_once()
        page_b.reset_mock()
        a_wm.set_current_page(None)
        a_wm.os.run()
        page_a.tick.assert_not_called()
        page_b.tick.assert_not_called()

    def test_when_page_made_current_then_page_ticks(self, a_wm):

        class TestPage(Page):
            pass

        page_a = TestPage()
        page_a.tick = mock.Mock()
        page_b = TestPage()
        page_b.tick = mock.Mock()
        a_wm.add_page(page_a, make_current=True)
        a_wm.add_page(page_b)
        a_wm.os.add_task(a_wm.os.stop)
        a_wm.os.run()

        page_a.tick.assert_called_once()
        page_b.tick.assert_not_called()

        page_a.tick.reset_mock()
        page_b.tick.reset_mock()
        a_wm.set_current_page(page_b)
        a_wm.os.run()

        page_a.tick.assert_not_called()
        page_b.tick.assert_called_once()

    def test_when_next_page_called_then_current_page_updated_to_next_and_wraps(
        self, a_wm, some_pages
    ):

        for p in some_pages:
            a_wm.add_page(p)

        last_idx = len(some_pages) - 1

        for curr_page, expected_next in ((0, 1), (last_idx, 0)):
            a_wm.set_current_page(some_pages[curr_page])
            a_wm.next_page()
            assert a_wm.current_page is some_pages[expected_next]

    def test_when_next_page_called_with_no_pages_then_noop(self, a_wm):

        a_wm.next_page()

    def test_when_next_page_called_with_no_current_page_then_picks_first(self, a_wm, some_pages):

        for p in some_pages:
            a_wm.add_page(p, make_current=False)

        a_wm.next_page()
        assert a_wm.current_page is some_pages[0]

    def test_when_prev_page_called_then_current_page_updated_to_next_and_wraps(
        self, a_wm, some_pages
    ):

        for p in some_pages:
            a_wm.add_page(p)

        last_idx = len(some_pages) - 1

        for curr_page, expected_prev in ((0, last_idx), (1, 0)):
            a_wm.set_current_page(some_pages[curr_page])
            a_wm.prev_page()
            assert a_wm.current_page is some_pages[expected_prev]

    def test_when_prev_page_called_with_no_pages_then_noop(self, a_wm):

        a_wm.prev_page()

    def test_when_prev_page_called_with_no_current_page_then_picks_last(self, a_wm, some_pages):

        for p in some_pages:
            a_wm.add_page(p, make_current=False)
        a_wm.prev_page()
        assert a_wm.current_page is some_pages[-1]

    def test_when_remove_all_pages_called_with_no_pages_then_is_noop(self, a_wm):

        a_wm.remove_all_pages()

    def test_when_remove_all_pages_called_with_pages_then_pages_torn_down_and_current_page_is_none(
        self, a_wm, a_mock_page_factory
    ):
        pages = [a_mock_page_factory(), a_mock_page_factory()]
        for p in pages:
            a_wm.add_page(p)
        a_wm.prev_page()
        a_wm.os.add_task(a_wm.os.stop)
        a_wm.os.run()
        a_wm.remove_all_pages()
        a_wm.os.run()
        assert a_wm.current_page is None
        for p in pages:
            p.teardown.assert_called_once()


class Test_WindowManager_update_display:

    def test_when_called_then_args_forwarded_to_os_update_display(self, a_wm, monkeypatch):

        mock_update = mock.Mock()
        monkeypatch.setattr(a_wm.os, "update_display", mock_update)

        args = (1, 2, "a", "b")
        kwargs = {"c": "d"}

        a_wm.update_display(*args, **kwargs)
        mock_update.assert_called_with(*args, **kwargs)


class Test_WindowManager_display_system_messages:

    def test_when_not_specified_then_handler_registered(self):

        os_instance = OS()
        wm = WindowManager(os_instance)
        assert wm.os_msg in os_instance.message_handlers()

    def test_when_set_to_true_then_handler_registered(self):

        os_instance = OS()
        wm = WindowManager(os_instance, display_system_messages=True)
        assert wm.os_msg in os_instance.message_handlers()

    def test_when_set_to_false_then_handler_not_registered(self):

        os_instance = OS()
        wm = WindowManager(os_instance, display_system_messages=False)
        assert wm.os_msg not in os_instance.message_handlers()


class Test_WindowManager_modal_pages:

    def test_when_modal_page_shown_then_uses_whole_screen(self, a_wm, a_mock_page):

        a_wm.show_modal_page(a_mock_page)
        a_wm.os.add_task(a_wm.os.stop)
        a_wm.os.run()

        w, h = a_wm.display.get_bounds()
        expected_region = Region(0, 0, w, h)
        a_mock_page.setup.assert_called_once_with(expected_region, a_wm)
        a_mock_page.will_show.assert_called_once()
        a_mock_page.tick.assert_called_once()

    def test_when_modal_page_shown_then_other_pages_dont_update(
        self, a_wm, a_mock_page, some_pages
    ):
        # Tenuous, but worth a check for now as it was a bug at one point!
        a_wm.set_systray_visible(True)
        systray_task = a_wm.os.tasks()[-1]
        a_wm.add_page(a_mock_page, make_current=True)
        a_wm.show_modal_page(some_pages[0])
        a_wm.os.add_task(a_wm.os.stop)
        a_wm.os.run()
        assert systray_task.active is False
        a_mock_page.tick.assert_not_called()

    def test_when_second_modal_page_shown_over_first_then_previous_is_cleared_and_doesnt_update(
        self, a_wm, a_mock_page_factory
    ):
        modal_a = a_mock_page_factory()
        modal_b = a_mock_page_factory()
        a_wm.os.add_task(a_wm.os.stop)
        a_wm.show_modal_page(modal_a)
        a_wm.os.run()
        modal_a.tick.assert_called_once()
        modal_a.reset_mock()
        a_wm.show_modal_page(modal_b)
        a_wm.os.run()
        modal_a.tick.assert_not_called()
        modal_a.will_hide.assert_called_once()
        modal_a.teardown.assert_called_once()
        modal_b.setup.assert_called_once()
        modal_b.will_show.assert_called_once()
        modal_b.tick.assert_called_once()

    def test_when_modal_page_cleared_then_current_page_updates(
        self, a_wm, a_mock_page, some_pages
    ):

        a_wm.set_systray_visible(True)
        systray_task = a_wm.os.tasks()[-1]
        # Ensure the current page is drawn once, so it will have
        # will_show called, so we can test that it isn't called later...
        a_wm.add_page(a_mock_page, make_current=True)
        a_wm.os.add_task(a_wm.os.stop)
        a_wm.os.run()
        a_mock_page.reset_mock()
        a_wm.show_modal_page(some_pages[0])
        a_wm.os.run()
        assert systray_task.active is False
        a_mock_page.will_hide.assert_not_called()
        a_mock_page.tick.assert_not_called()
        a_mock_page.reset_mock()
        a_wm.clear_modal_page()
        a_wm.os.run()
        a_mock_page.will_show.assert_not_called()
        a_mock_page.tick.assert_called_once()
        assert systray_task.active is True

    def test_when_modal_page_cleared_then_modal_page_torn_down_and_not_updated(
        self, a_wm, a_mock_page, some_pages
    ):

        a_wm.add_page(some_pages[0], make_current=True)
        a_wm.show_modal_page(a_mock_page)
        a_wm.os.add_task(a_wm.os.stop)
        a_wm.os.run()
        a_mock_page.tick.assert_called_once()
        a_mock_page.reset_mock()
        a_wm.clear_modal_page()
        a_wm.os.run()
        a_mock_page.tick.assert_not_called()
        a_mock_page.will_hide.assert_called_once()
        a_mock_page.teardown.assert_called_once()

    def test_when_no_modal_page_then_clear_is_a_noop(self, a_wm, a_mock_page):
        a_wm.clear_modal_page()


class Test_WindowManager_set_theme:

    def test_when_theme_set_then_setup_is_called_with_display_and_dpi_scale_factor(self):

        mock_theme = mock.create_autospec(Theme, instance=True)

        os_instance = OS()
        os_instance.display.get_bounds.return_value = (240, 240)
        wm = WindowManager(os_instance)
        os_instance.display.get_bounds.return_value = (480, 480)
        wm = WindowManager(os_instance, theme=mock_theme)
        mock_theme.setup.assert_called_once_with(wm.display, 2)


@pytest.fixture
def a_wm():
    os_instance = OS()
    return WindowManager(os_instance)


@pytest.fixture
def a_page():
    class TestPage(Page):
        pass

    return TestPage()


@pytest.fixture
def a_mock_page_factory():
    def make():
        mock_page = mock.create_autospec(Page)
        mock_page.execution_frequency = None
        mock_page.title = "Mock Page"
        mock_page.needs_update = False
        return mock_page

    return make


@pytest.fixture
def a_mock_page(a_mock_page_factory):
    return a_mock_page_factory()


@pytest.fixture
def some_pages():
    class TestPage(Page):
        pass

    return [TestPage() for i in range(3)]
