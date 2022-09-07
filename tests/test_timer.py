# FIXME: some tests are skipped to due the lack of mocking techniques

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

import util.time
from util.time import Timer


class TestTimer:
    @pytest.fixture(autouse=True)
    def setUp(self) -> None:
        self._timer = Timer()

    def test_unstart_have_time_0(self) -> None:
        assert self._timer.time() == 0

    @patch("time.time")
    def test_time_when_started(self, time_mock: MagicMock) -> None:
        start_time = int(datetime(2022, 9, 17, 10, 10, 0).timestamp())
        end_time: int = start_time + 1000

        time_mock.return_value = start_time
        self._timer.start()
        time_mock.return_value = end_time

        assert self._timer.time() == end_time - start_time
        assert time_mock.called

    @patch("time.time")
    def test_time_when_paused(self, time_mock: MagicMock) -> None:
        start_time = int(datetime(2022, 9, 17, 10, 10, 0).timestamp())
        time_when_paused: int = start_time + 1000
        end_time: int = time_when_paused + 500

        time_mock.return_value = start_time
        self._timer.start()
        time_mock.return_value = time_when_paused
        self._timer.pause()
        time_mock.return_value = end_time

        assert self._timer.time() == time_when_paused - start_time
        assert time_mock.called

    @patch("time.time")
    def test_time_after_paused(self, time_mock: MagicMock) -> None:
        start_time = int(datetime(2022, 9, 17, 10, 10, 0).timestamp())
        time_when_paused: int = start_time + 1000
        paused_time_length: int = 500
        time_when_started: int = time_when_paused + paused_time_length
        end_time: int = time_when_started + 250

        time_mock.return_value = start_time
        self._timer.start()
        time_mock.return_value = time_when_paused
        self._timer.pause()
        time_mock.return_value = time_when_started
        self._timer.start()
        time_mock.return_value = end_time

        assert self._timer.time() == end_time - start_time - paused_time_length
        assert time_mock.called

    @patch("time.time")
    def test_reset(self, time_mock: MagicMock) -> None:
        start_time = int(datetime(2022, 9, 17, 10, 10, 0).timestamp())
        end_time: int = start_time + 1000
        time_mock.return_value = start_time
        self._timer.start()
        time_mock.return_value = end_time

        self._timer.reset()

        assert self._timer.time() == 0
        assert not self._timer.is_paused()
        assert time_mock.called

    def test_is_paused(self) -> None:
        assert not self._timer.is_paused()
        self._timer.pause()
        assert self._timer.is_paused()
        self._timer.start()
        assert not self._timer.is_paused()
        self._timer.pause()
        assert self._timer.is_paused()


@patch("time.time")
def test_get_current_time(time_mock: MagicMock) -> None:
    current_datetime = int(datetime(2022, 9, 7, 9, 17).timestamp())
    time_mock.return_value = current_datetime

    current_time: int = util.time.get_current_time()

    assert current_time == current_datetime
    assert time_mock.called


@pytest.mark.skip("depends on time zone")
def test_epoch_to_date_time() -> None:
    date_time: str = util.time.to_date_time(0)
    assert date_time == "1970-01-01 00:00:00"


def test_min_to_sec() -> None:
    assert util.time.min_to_sec(0) == 0
    assert util.time.min_to_sec(1) == 60
    assert util.time.min_to_sec(100) == 6000


def test_negative_min_to_sec() -> None:
    assert util.time.min_to_sec(-1) == -60
    assert util.time.min_to_sec(-100) == -6000
