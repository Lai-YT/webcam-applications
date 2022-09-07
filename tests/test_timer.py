from datetime import datetime, timedelta

import pytest
import pytz
from freezegun import freeze_time

import util.time
from util.time import Timer


INITIAL_REF_TIME = datetime(2022, 9, 17, 10, 10, 0)


class TestTimer:
    @pytest.fixture(autouse=True)
    def setUp(self) -> None:
        self._timer = Timer()

    @pytest.fixture
    def frozen_time(self):
        with freeze_time(INITIAL_REF_TIME) as _frozen_time:
            yield _frozen_time

    def test_unstart_have_time_0(self) -> None:
        assert self._timer.time() == 0

    def test_time_when_started(self, frozen_time) -> None:
        frozen_time.tick(timedelta(seconds=250))
        self._timer.start()
        frozen_time.tick(timedelta(seconds=250))

        assert self._timer.time() == 500 - 250

    def test_time_when_paused(self, frozen_time) -> None:
        self._timer.start()
        frozen_time.tick(timedelta(seconds=250))
        self._timer.pause()
        frozen_time.tick(timedelta(seconds=250))

        assert self._timer.time() == 500 - 250

    def test_time_after_paused(self, frozen_time) -> None:
        self._timer.start()
        frozen_time.tick(timedelta(seconds=250))
        self._timer.pause()
        frozen_time.tick(timedelta(seconds=250))
        self._timer.start()
        frozen_time.tick(timedelta(seconds=250))

        assert self._timer.time() == 750 - 250

    def test_wont_be_paused_before_started(self) -> None:
        self._timer.pause()
        assert not self._timer.is_paused()

    def test_reset(self, frozen_time) -> None:
        self._timer.start()
        frozen_time.tick(timedelta(seconds=250))
        self._timer.reset()

        assert self._timer.time() == 0
        assert not self._timer.is_paused()

    def test_is_paused(self) -> None:
        self._timer.start()
        assert not self._timer.is_paused()
        self._timer.pause()
        assert self._timer.is_paused()

    class TestSpecialCase:
        @pytest.fixture(autouse=True)
        def setUp(self) -> None:
            self._timer = Timer()

        def test_duplicate_pause(self, frozen_time) -> None:
            self._timer.start()
            frozen_time.tick(timedelta(seconds=250))
            self._timer.pause()
            frozen_time.tick(timedelta(seconds=250))
            self._timer.pause()
            frozen_time.tick(timedelta(seconds=250))
            self._timer.start()
            frozen_time.tick(timedelta(seconds=250))

            assert self._timer.time() == 1000 - 250 * 2

        def test_duplicate_start(self, frozen_time) -> None:
            self._timer.start()
            frozen_time.tick(timedelta(seconds=250))
            self._timer.start()
            frozen_time.tick(timedelta(seconds=250))
            self._timer.pause()
            frozen_time.tick(timedelta(seconds=250))
            self._timer.start()
            frozen_time.tick(timedelta(seconds=250))

            assert self._timer.time() == 1000 - 250

        def test_time_pause_before_start(self, frozen_time) -> None:
            self._timer.pause()
            frozen_time.tick(timedelta(seconds=250))
            self._timer.start()
            frozen_time.tick(timedelta(seconds=250))

            assert self._timer.time() == 500 - 250


def test_epoch_to_date_time() -> None:
    date_time: str = util.time.to_date_time(0, timezone=pytz.utc)
    assert date_time == "1970-01-01 00:00:00"

    assert (
        util.time.to_date_time(
            int(
                datetime.strptime(
                    "2022-09-07 08:25:13 +0000", "%Y-%m-%d %H:%M:%S %z"
                ).timestamp()
            ),
            timezone=pytz.utc,
        )
        == "2022-09-07 08:25:13"
    )


def test_min_to_sec() -> None:
    assert util.time.min_to_sec(0) == 0
    assert util.time.min_to_sec(1) == 60
    assert util.time.min_to_sec(100) == 6000


def test_negative_min_to_sec() -> None:
    assert util.time.min_to_sec(-1) == -60
    assert util.time.min_to_sec(-100) == -6000
