"""
Common test helpers, mostly to aid testing on non-Presto hardware.
"""

import sys
import time

from unittest import mock

import pytest

# Stub the Presto platform imports so we can test business logic on
# desktop hardware

# pylint: disable=no-member

mock_presto = type(sys)("presto")
mock_presto.Presto = mock.Mock()
mock_presto.Presto.return_value.connect = mock.Mock()
mock_presto.Presto.return_value.touch.poll = mock.Mock()
# Ensure that the state property isn't a Mock, which would evaluate
# touch True, and make code thing there was perpetually a touch in
# progress.
mock_presto.Presto.return_value.touch.state = False
mock_presto.Presto.return_value.touch.state2 = False
mock_presto.Presto.return_value.display.get_bounds.return_value = (240, 240)
mock_presto.Buzzer = mock.Mock()
sys.modules["presto"] = mock_presto

mock_plasma = type(sys)("plasma")
mock_plasma.WS2812 = mock.create_autospec(object, instance=False)
mock_plasma.WS2812.return_value.start = mock.Mock()
sys.modules["plasma"] = mock_plasma

mock_ntptime = type(sys)("ntptime")
mock_ntptime.settime = mock.Mock()
sys.modules["ntptime"] = mock_ntptime

mock_picographics = type(sys)("picographics")
mock_picographics.PicoGraphics = mock.create_autospec(object, instance=False)
sys.modules["picographics"] = mock_picographics

# Needed for typing, note this is _not_ the object within a presto
# instance, as that is a generic recursive mock from the Presto
# definition above.
mock_touch = type(sys)("touch")
mock_touch.FT6236 = mock.create_autospec(object, instance=False)
sys.modules["touch"] = mock_touch

time.ticks_us = lambda: time.monotonic_ns() // 1000
time.ticks_diff = lambda a, b: a - b
time.sleep_ms = lambda s: time.sleep(s / 1000)

sys.print_exception = mock.Mock()


@pytest.fixture
def mock_presto_module():
    """
    Supplies the mock/stub used for the "presto" module to allow
    asserts. The mock will be reset for each test.
    """
    mock_presto.Presto.reset_mock()
    mock_presto.Buzzer.reset_mock()
    return mock_presto


@pytest.fixture
def mock_plasma_module():
    """
    Supplies the mock/stub used for the "plasma" module to allow
    asserts. The mock will be reset for each test.
    """
    mock_plasma.WS2812.reset_mock()
    return mock_plasma


@pytest.fixture
def mock_ntptime_module():
    """
    Supplies the mock/stub used for the "ntptime" module to allow
    asserts. The mock will be reset for each test.
    """
    mock_ntptime.settime.reset_mock()
    return mock_ntptime

@pytest.fixture
def mock_touch_factory():
    """
    Provides a mock touch data structure
    """

    class State:
        state = False
        x = 0
        y = 0
        state2 = False
        x2 = 0
        y2 = 0

    return State

