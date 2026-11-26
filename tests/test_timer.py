from src.contest.timer import Timer,FakeClock

def test_competition_lasts_70_seconds():
    clock = FakeClock()
    timer = Timer(duration=70, clock=clock)
    clock.advance(69.9)
    assert not timer.expired()
    clock.advance(0.1)
    assert timer.expired()

def test_tiebraker_lasts_30_seconds():
    clock=FakeClock()
    timer = Timer(duration=30,clock=clock)
    clock.advance(30)
    assert timer.expired()

