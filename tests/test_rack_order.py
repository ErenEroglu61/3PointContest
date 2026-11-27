import pytest

from src.contest.balls import BallType
from src.contest.locations import COMPETITION_ORDER
from src.contest.rack import TOTAL_BALLS, ShotSequence, build_stations
from src.contest.scoring import ShotStatus


def idx(seq, name):
    return seq.station_index(name)


def test_competition_order_puts_logo_between_center_and_wings():
    names = [s.name for s in COMPETITION_ORDER]
    assert names == ["corner_left", "wing_left", "logo_left", "center", "logo_right", "wing_right", "corner_right"]


def test_stations_hold_27_balls():
    stations = build_stations("center")
    assert sum(len(s.balls) for s in stations) == TOTAL_BALLS == 27


def test_standard_rack_is_four_nba_then_money():
    rack = build_stations("center")[0]
    assert [b.type for b in rack.balls] == [BallType.NBA] * 4 + [BallType.MONEY]


def test_all_money_rack_is_placed_where_player_chooses():
    stations = {s.name: s for s in build_stations("wing_right")}
    assert stations["wing_right"].all_money
    assert all(b.type is BallType.MONEY for b in stations["wing_right"].balls)
    assert sum(s.all_money for s in stations.values()) == 1


def test_pedestals_hold_one_blue_money_ball():
    stations = {s.name: s for s in build_stations("center")}
    for name in ("logo_left", "logo_right"):
        assert [b.type for b in stations[name].balls] == [BallType.BLUE_MONEY]


def test_money_rack_cannot_be_on_pedestal():
    with pytest.raises(ValueError):
        build_stations("logo_left")


def test_perfect_round_scores_40():
    seq = ShotSequence("corner_right")
    while (shot := seq.next_shot()) is not None:
        seq.attempt(*shot, made=True)
    # 4 rack x (4x1 + 2) + all money 5x2 + 2 x 3
    assert seq.score == 40
    assert seq.finished


def test_missed_round_scores_zero():
    seq = ShotSequence("center")
    while (shot := seq.next_shot()) is not None:
        assert seq.attempt(*shot, made=False).status is ShotStatus.MISSED
    assert seq.score == 0


def test_money_ball_before_nba_balls_is_void():
    seq = ShotSequence("center")
    result = seq.attempt(0, 4, made=True)  # corner_left money topu, NBA topları atılmadan
    assert result.status is ShotStatus.VOID_OUT_OF_SEQUENCE
    assert result.points == 0


def test_money_ball_after_nba_balls_counts_two():
    seq = ShotSequence("center")
    for b in range(4):
        seq.attempt(0, b, made=True)
    assert seq.attempt(0, 4, made=True).points == 2


def test_all_money_rack_has_no_order_restriction():
    seq = ShotSequence("corner_left")
    assert seq.attempt(0, 3, made=True).points == 2


def test_blue_money_shot_out_of_sequence_is_void():
    seq = ShotSequence("center")
    result = seq.attempt(idx(seq, "logo_left"), 0, made=True)
    assert result.status is ShotStatus.VOID_OUT_OF_SEQUENCE


def _finish_station(seq, name, made=True):
    si = idx(seq, name)
    for bi in seq.stations[si].remaining:
        seq.attempt(si, bi, made)


def test_blue_money_counts_three_in_sequence():
    seq = ShotSequence("center")
    _finish_station(seq, "corner_left")
    _finish_station(seq, "wing_left")
    assert seq.attempt(idx(seq, "logo_left"), 0, made=True).points == 3


def test_skipping_blue_money_eliminates_it():
    seq = ShotSequence("center")
    _finish_station(seq, "corner_left")
    _finish_station(seq, "wing_left")
    center = idx(seq, "center")
    assert seq.attempt(center, 0, made=True).status is ShotStatus.MADE
    logo = seq.stations[idx(seq, "logo_left")]
    assert logo.balls[0].eliminated
    late = seq.attempt(idx(seq, "logo_left"), 0, made=True)
    assert late.status is ShotStatus.VOID_ELIMINATED
    assert late.points == 0


def test_skipping_a_rack_makes_shot_void():
    seq = ShotSequence("center")
    result = seq.attempt(idx(seq, "wing_left"), 0, made=True)
    assert result.status is ShotStatus.VOID_OUT_OF_SEQUENCE
    assert not seq.stations[idx(seq, "logo_left")].balls[0].eliminated


def test_line_violation_does_not_count():
    seq = ShotSequence("center")
    result = seq.attempt(0, 0, made=True, line_violation=True)
    assert result.status is ShotStatus.VOID_LINE_VIOLATION
    assert seq.score == 0


def test_ball_cannot_be_shot_twice():
    seq = ShotSequence("center")
    seq.attempt(0, 0, made=True)
    with pytest.raises(ValueError):
        seq.attempt(0, 0, made=True)


def test_release_then_resolve_two_phase():
    seq = ShotSequence("center")
    result = seq.release(0, 0)
    assert result.status is ShotStatus.PENDING
    assert seq.score == 0
    seq.resolve(result, made=True)
    assert seq.score == 1


def test_void_result_stays_void_after_resolve():
    seq = ShotSequence("center")
    result = seq.release(0, 4)
    seq.resolve(result, made=True)
    assert result.status is ShotStatus.VOID_OUT_OF_SEQUENCE
    assert seq.score == 0
