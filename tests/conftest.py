"""
Common test helpers, mostly to aid testing on non-Presto hardware.
"""

import sys

from unittest import mock

import pytest

# Stub the Presto platform imports so we can test business logic on
# desktop hardware

# pylint: disable=no-member

mock_presto = type(sys)("presto")
mock_presto.Presto = mock.Mock()
mock_presto.Presto.return_value.connect = mock.Mock()
mock_presto.Buzzer = mock.Mock()
sys.modules["presto"] = mock_presto

mock_plasma = type(sys)("plasma")
mock_plasma.WS2812 = mock.create_autospec(object, instance=False)
mock_plasma.WS2812.return_value.start = mock.Mock()
sys.modules["plasma"] = mock_plasma

mock_ntptime = type(sys)("ntptime")
mock_ntptime.settime = mock.Mock()
sys.modules["ntptime"] = mock_ntptime


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
