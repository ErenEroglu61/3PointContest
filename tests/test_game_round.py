import random

from src.contest.scoring import ShotStatus
from src.game.round import GameRound, RoundPhase
from src.physics.shot import SWEET_SPOT

DT = 1 / 60


def bot_step(r: GameRound, target=SWEET_SPOT):
    """Güç barını hedef değerde bırakan basit bot."""
    if r.can_shoot and not r.meter.charging:
        r.press()
    if r.meter.charging and r.meter.phase < 0.5 and r.meter.value >= target:
        r.release()
    r.update(DT)


def run(r: GameRound, seconds=120, target=SWEET_SPOT, skip_logos=False):
    t = 0.0
    while not r.done and t < seconds:
        if skip_logos and r.can_skip:
            r.skip()
        bot_step(r, target)
        t += DT
    return t


def test_countdown_blocks_shooting():
    r = GameRound("center", countdown=3.0, rng=random.Random(0))
    assert r.phase is RoundPhase.COUNTDOWN
    assert not r.press()
    for _ in range(int(3.1 / DT)):
        r.update(DT)
    assert r.phase is RoundPhase.LIVE
    assert r.press()


def test_perfect_bot_scores_40_within_70_seconds():
    r = GameRound("corner_right", countdown=0, rng=random.Random(1))
    run(r)
    assert r.done
    assert r.score == 40
    assert r.timer.remaining > 0


def test_bad_bot_scores_nothing():
    r = GameRound("center", countdown=0, rng=random.Random(2))
    run(r, target=0.3)
    assert r.score == 0


def test_buzzer_ends_round():
    r = GameRound("center", duration=5.0, countdown=0, rng=random.Random(3))
    run(r)
    assert r.done
    assert r.timer.expired
    assert r.seq.balls_left > 0


def test_skipping_logos_eliminates_blue_money():
    r = GameRound("center", countdown=0, rng=random.Random(4))
    run(r, skip_logos=True)
    pedestals = [s for s in r.stations if s.is_pedestal]
    assert all(s.balls[0].eliminated for s in pedestals)
    assert r.score == 40 - 6


def test_shots_released_before_buzzer_still_count():
    r = GameRound("center", duration=2.0, countdown=0, rng=random.Random(5))
    while r.phase is RoundPhase.LIVE:
        bot_step(r)
    assert any(res.status is ShotStatus.PENDING for res in r.seq.results)
    while not r.done:
        r.update(DT)
    assert r.score >= 1
    assert all(res.status is not ShotStatus.PENDING for res in r.seq.results)


def test_events_are_emitted():
    r = GameRound("center", countdown=0, rng=random.Random(6))
    kinds = set()
    for _ in range(int(4 / DT)):
        bot_step(r)
        kinds |= {k for k, _ in r.drain_events()}
    assert {"release", "made"} <= kinds
