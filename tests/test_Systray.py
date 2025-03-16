# SPDX-License-Identifier: MIT
# Copyright 2025 Tom Cowland

"""
Tests for the WindowManager Systray implementation. Designed to run
off-platform, they focus on the specifics of the business logic and
advertised functionality.
"""

from unittest import mock

from picographics import PicoGraphics
import pytest

from tmos import OS, Region
from tmos_ui import DefaultTheme, Region, Size, Page, Theme, WindowManager, Systray

# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=invalid-name, redefined-outer-name
# pylint: disable=attribute-defined-outside-init
# pylint: disable=too-few-public-methods


class Test_Systray_Accessory:

    def test_default_size_implementation_raises_NotImplementedError(self):
        accessory = Systray.Accessory()
        with pytest.raises(NotImplementedError):
            accessory.size(mock.Mock(), mock.Mock())


class Test_Systray:

    def test_positions_are_leading_and_trailing(self):
        assert Systray.accessory_positions == (
            Systray.Accessory.POSITION_LEADING,
            Systray.Accessory.POSITION_TRAILING,
        )
        assert Systray.Accessory.POSITION_LEADING == "leading"
        assert Systray.Accessory.POSITION_TRAILING == "trailing"


class Test_Systray_Accessories:

    def test_when_adding_accessory_with_leading_position_then_is_leading(
        self, an_accessory_factory
    ):
        a = an_accessory_factory()
        s = Systray()
        s.add_accessory(a, a.POSITION_LEADING)
        assert s.accessories() == ((a,), ())

    def test_when_adding_accessory_with_trailing_position_then_is_trailing(
        self, an_accessory_factory
    ):
        a = an_accessory_factory()
        s = Systray()
        s.add_accessory(a, a.POSITION_TRAILING)
        assert s.accessories() == ((), (a,))

    def test_when_adding_accessory_without_index_then_is_last(self, an_accessory_factory):
        a = an_accessory_factory()
        b = an_accessory_factory()
        s = Systray()
        s.add_accessory(a, a.POSITION_LEADING)
        s.add_accessory(b, a.POSITION_LEADING)
        assert s.accessories() == ((a, b), ())

    def test_when_adding_accessory_with_index_then_inserted_at_index(self, an_accessory_factory):
        a = an_accessory_factory()
        b = an_accessory_factory()
        s = Systray()
        s.add_accessory(a, a.POSITION_LEADING)
        s.add_accessory(b, a.POSITION_LEADING, index=0)
        assert s.accessories() == ((b, a), ())

    def test_when_adding_accessory_with_invalid_position_then_ValueError_raised(
        self, an_accessory_factory
    ):
        s = Systray()
        with pytest.raises(ValueError):
            s.add_accessory(an_accessory_factory(), "cat")

    def test_when_non_accessory_added_then_ValueError_raised(self):
        s = Systray()
        with pytest.raises(ValueError):
            s.add_accessory(Page(), Systray.Accessory.POSITION_LEADING)

    def test_when_removing_accessory_then_removed(self, an_accessory_factory):
        a = an_accessory_factory()
        b = an_accessory_factory()
        s = Systray()
        s.add_accessory(a, Systray.Accessory.POSITION_LEADING)
        s.add_accessory(b, Systray.Accessory.POSITION_LEADING)
        s.remove_accessory(a)
        assert s.accessories() == ((b,), ())

    def test_when_removing_accessory_then_teardown_is_called(self, mock_accessory_factory):

        a = mock_accessory_factory()
        s = Systray()
        s.add_accessory(a, Systray.Accessory.POSITION_LEADING)
        a.teardown.assert_not_called()
        s.remove_accessory(a)
        a.teardown.assert_called_once()

    def test_when_removing_unknown_accessory_then_ValueError_raised(self, an_accessory_factory):
        s = Systray()
        with pytest.raises(ValueError):
            s.remove_accessory(an_accessory_factory())

    def test_when_accessories_called_then_immutable_lists_returned(
        self, a_systray_with_accessories
    ):
        leading, trailing = a_systray_with_accessories.accessories()
        assert isinstance(leading, tuple)
        assert isinstance(trailing, tuple)


class Test_Systray_Region_setup_positional_accessories:

    def test_when_laying_out_leading_accesories_then_left_aligned_with_reduced_pager_region(
        self, mock_accessory_factory, a_mock_wm
    ):

        outer_region = Region(10, 20, 100, 30)
        a1 = mock_accessory_factory()
        a1.size.side_effect = None
        a1.size.return_value = Size(10, 20)
        a2 = mock_accessory_factory()
        a2.size.side_effect = None
        a2.size.return_value = Size(20, 30)

        s = Systray()
        s.add_accessory(a1, Systray.Accessory.POSITION_LEADING)
        s.add_accessory(a2, Systray.Accessory.POSITION_LEADING)
        s.setup(outer_region, a_mock_wm)

        a1.size.assert_called_with(Size(100, 30), a_mock_wm)
        a2.size.assert_called_with(Size(90, 30), a_mock_wm)
        a1.setup.assert_called_with(Region(10, 20, 10, 20), a_mock_wm)
        a2.setup.assert_called_with(Region(20, 20, 20, 30), a_mock_wm)
        assert s._Systray__page_radio_button.region == Region(40, 20, 70, 30)

    def test_when_laying_out_trailing_accesories_then_right_aligned_with_reduced_pager_region(
        self, mock_accessory_factory, a_mock_wm
    ):
        outer_region = Region(10, 20, 100, 30)
        a1 = mock_accessory_factory()
        a1.size.side_effect = None
        a1.size.return_value = Size(10, 20)
        a2 = mock_accessory_factory()
        a2.size.side_effect = None
        a2.size.return_value = Size(20, 30)

        s = Systray()
        s.add_accessory(a1, Systray.Accessory.POSITION_TRAILING)
        s.add_accessory(a2, Systray.Accessory.POSITION_TRAILING)
        s.setup(outer_region, a_mock_wm)

        a1.size.assert_called_with(Size(100, 30), a_mock_wm)
        a2.size.assert_called_with(Size(90, 30), a_mock_wm)
        a1.setup.assert_called_with(Region(100, 20, 10, 20), a_mock_wm)
        a2.setup.assert_called_with(Region(80, 20, 20, 30), a_mock_wm)
        assert s._Systray__page_radio_button.region == Region(10, 20, 70, 30)


class Test_Systray_Accessory_forwarding:

    def test_when_will_show_called_then_forwarded_to_accessories(
        self, a_systray_with_mock_accessories
    ):
        l, t = a_systray_with_mock_accessories.accessories()
        a_systray_with_mock_accessories.will_show()
        for a in (*l, *t):
            a.will_show.assert_called_once()

    def test_when_will_hide_called_then_forwarded_to_accessories(
        self, a_systray_with_mock_accessories
    ):
        l, t = a_systray_with_mock_accessories.accessories()
        a_systray_with_mock_accessories.will_hide()
        for a in (*l, *t):
            a.will_hide.assert_called_once()

    def test_when_teardown_called_then_forwarded_to_accessories(
        self, a_systray_with_mock_accessories
    ):
        l, t = a_systray_with_mock_accessories.accessories()
        a_systray_with_mock_accessories.teardown()
        for a in (*l, *t):
            a.teardown.assert_called_once()

    def test_when__tick_called_then_forwarded_to_accessories_with_relevant_region(
        self, a_systray_with_mock_accessories, a_mock_wm
    ):
        region = Region(0, 0, 100, 30)
        l, t = a_systray_with_mock_accessories.accessories()
        a_systray_with_mock_accessories.setup(region, a_mock_wm)
        a_systray_with_mock_accessories._tick(region, a_mock_wm)
        l[0]._tick.assert_called_once_with(Region(0, 0, 10, 30), a_mock_wm)
        l[1]._tick.assert_called_once_with(Region(10, 0, 10, 30), a_mock_wm)
        l[2]._tick.assert_called_once_with(Region(20, 0, 10, 30), a_mock_wm)
        t[0]._tick.assert_called_once_with(Region(90, 0, 10, 30), a_mock_wm)
        t[1]._tick.assert_called_once_with(Region(80, 0, 10, 30), a_mock_wm)


@pytest.fixture
def an_accessory_factory():
    class AnAccessory(Systray.Accessory):
        title = "AnAccessory"

    return AnAccessory


@pytest.fixture
def mock_accessory_factory():
    def make_mock():
        m = mock.create_autospec(Systray.Accessory, instance=True)

        def size_stub(max_size, wm):
            return Size(10, max_size.height)

        m.size.side_effect = size_stub
        return m

    return make_mock


@pytest.fixture
def a_mock_wm():

    p1 = Page()
    p1.title = "One"
    p2 = Page()
    p2.title = "Teo"
    m = mock.create_autospec(WindowManager, instance=True)
    m.os = OS()
    m.display = PicoGraphics()
    m.theme = DefaultTheme()
    m.theme.setup(m.display)
    m.pages.return_value = (p1, p2)
    m.current_page = p1
    return m


@pytest.fixture
def a_systray_with_accessories(an_accessory_factory, a_mock_wm):
    s = Systray()
    s.setup(Region(0, 0, 240, 30), a_mock_wm)
    s.add_accessory(an_accessory_factory(), position=Systray.Accessory.POSITION_LEADING)
    s.add_accessory(an_accessory_factory(), position=Systray.Accessory.POSITION_LEADING)
    s.add_accessory(an_accessory_factory(), position=Systray.Accessory.POSITION_LEADING)
    s.add_accessory(an_accessory_factory(), position=Systray.Accessory.POSITION_TRAILING)
    s.add_accessory(an_accessory_factory(), position=Systray.Accessory.POSITION_TRAILING)
    return s


@pytest.fixture
def a_systray_with_mock_accessories(mock_accessory_factory, a_mock_wm):
    s = Systray()
    s.setup(Region(0, 0, 240, 30), a_mock_wm)
    s.add_accessory(mock_accessory_factory(), position=Systray.Accessory.POSITION_LEADING)
    s.add_accessory(mock_accessory_factory(), position=Systray.Accessory.POSITION_LEADING)
    s.add_accessory(mock_accessory_factory(), position=Systray.Accessory.POSITION_LEADING)
    s.add_accessory(mock_accessory_factory(), position=Systray.Accessory.POSITION_TRAILING)
    s.add_accessory(mock_accessory_factory(), position=Systray.Accessory.POSITION_TRAILING)
    return s
