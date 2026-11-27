import pytest

from src.contest.timer import ContestTimer, format_clock


def test_timer_does_not_run_before_start():
    t = ContestTimer(70)
    t.update(5)
    assert t.remaining == 70


def test_timer_counts_down_and_expires_once():
    t = ContestTimer(30)
    t.start()
    assert t.update(29.5) is False
    assert t.update(1.0) is True       # buzzer tam bu adımda
    assert t.expired and t.remaining == 0
    assert t.update(1.0) is False      # ikinci kez buzzer yok


def test_pause_stops_time():
    t = ContestTimer(70)
    t.start()
    t.update(10)
    t.pause()
    t.update(10)
    assert t.remaining == pytest.approx(60)


def test_invalid_duration():
    with pytest.raises(ValueError):
        ContestTimer(0)


@pytest.mark.parametrize("seconds, text", [(70, "1:10"), (69.2, "1:10"), (60, "1:00"), (10.0, "0:10"),
                                           (9.42, "0:09.4"), (0, "0:00.0")])
def test_format_clock(seconds, text):
    assert format_clock(seconds) == text
