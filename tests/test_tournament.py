import random

import pytest

from src.contest.timer import (CHAMPIONSHIP_TIEBREAKER_SECONDS, FIRST_ROUND_TIEBREAKER_SECONDS,
                               ROUND_SECONDS)
from src.contest.tournament import Phase, Player, Tournament, first_round_order, resolve_cut


def make_players(n=8, champion_index=None):
    return [Player(f"P{i}", defending_champion=(i == champion_index)) for i in range(n)]


def play(t: Tournament, scores: dict[str, int]):
    """Sıradaki oyuncuya skor verir; ``scores`` isim -> skor."""
    turn = t.current_turn
    return t.submit_score(scores[turn.player.name])


def play_phase(t: Tournament, scores: dict[str, int]):
    """Şu an sırada bekleyen atışları (tek bir tur/tiebreaker) oynatır."""
    for _ in range(len(t.upcoming)):
        play(t, scores)


def test_defending_champion_shoots_last():
    players = make_players(champion_index=2)
    for seed in range(10):
        order = first_round_order(players, random.Random(seed))
        assert order[-1].name == "P2"
        assert sorted(p.name for p in order) == sorted(p.name for p in players)


def test_first_round_order_is_random_draw():
    players = make_players()
    orders = {tuple(p.name for p in first_round_order(players, random.Random(s))) for s in range(20)}
    assert len(orders) > 1


def test_resolve_cut_without_ties():
    a, b, c, d = (Player(n) for n in "abcd")
    sure, tied, slots = resolve_cut({a: 20, b: 25, c: 18, d: 22}, 3)
    assert sure == [b, d, a] and tied == [] and slots == 0


def test_resolve_cut_with_tie_on_the_line():
    a, b, c, d, e = (Player(n) for n in "abcde")
    sure, tied, slots = resolve_cut({a: 25, b: 22, c: 20, d: 20, e: 18}, 3)
    assert sure == [a, b]
    assert set(tied) == {c, d}
    assert slots == 1


def test_resolve_cut_tie_above_line_is_harmless():
    a, b, c, d = (Player(n) for n in "abcd")
    sure, tied, _ = resolve_cut({a: 25, b: 25, c: 20, d: 10}, 3)
    assert set(sure) == {a, b, c} and tied == []


def test_round_durations():
    t = Tournament(make_players(), random.Random(0))
    assert t.current_turn.duration == ROUND_SECONDS == 70


def test_top_three_advance_and_championship_order_is_inverse():
    t = Tournament(make_players(), random.Random(1))
    scores = {f"P{i}": 10 + i for i in range(8)}   # P7 en yüksek
    play_phase(t, scores)
    assert t.phase is Phase.CHAMPIONSHIP
    assert {p.name for p in t.finalists} == {"P5", "P6", "P7"}
    order = [turn.player.name for turn in t.upcoming]
    assert order == ["P5", "P6", "P7"]   # en düşük ilk turu skoru ilk atar


def test_champion_is_highest_final_score():
    t = Tournament(make_players(), random.Random(1))
    play_phase(t, {f"P{i}": 10 + i for i in range(8)})
    play_phase(t, {"P5": 30, "P6": 22, "P7": 25})
    assert t.finished
    assert t.champion.name == "P5"


def test_first_round_tie_triggers_30_second_tiebreaker():
    t = Tournament(make_players(), random.Random(2))
    scores = {"P0": 30, "P1": 28, "P2": 20, "P3": 20, "P4": 20, "P5": 10, "P6": 9, "P7": 8}
    play_phase(t, scores)
    assert t.phase is Phase.FIRST_ROUND_TIEBREAKER
    assert {p.name for p in t.finalists} == {"P0", "P1"}
    turns = t.upcoming
    assert {turn.player.name for turn in turns} == {"P2", "P3", "P4"}
    assert all(turn.duration == FIRST_ROUND_TIEBREAKER_SECONDS == 30 for turn in turns)


def test_tiebreaker_repeats_until_broken():
    t = Tournament(make_players(), random.Random(2))
    play_phase(t, {"P0": 30, "P1": 28, "P2": 20, "P3": 20, "P4": 20, "P5": 10, "P6": 9, "P7": 8})
    play_phase(t, {"P2": 12, "P3": 12, "P4": 5})     # P2 ve P3 hâlâ eşit
    assert t.phase is Phase.FIRST_ROUND_TIEBREAKER
    assert {turn.player.name for turn in t.upcoming} == {"P2", "P3"}
    play_phase(t, {"P2": 9, "P3": 11})
    assert t.phase is Phase.CHAMPIONSHIP
    assert {p.name for p in t.finalists} == {"P0", "P1", "P3"}
    assert len(t.tiebreakers) == 2


def test_championship_tie_triggers_70_second_tiebreaker():
    t = Tournament(make_players(), random.Random(3))
    play_phase(t, {f"P{i}": 10 + i for i in range(8)})
    play_phase(t, {"P5": 25, "P6": 25, "P7": 20})
    assert t.phase is Phase.CHAMPIONSHIP_TIEBREAKER
    turns = t.upcoming
    assert {turn.player.name for turn in turns} == {"P5", "P6"}
    assert all(turn.duration == CHAMPIONSHIP_TIEBREAKER_SECONDS == 70 for turn in turns)
    play_phase(t, {"P5": 18, "P6": 18})          # yine eşit: tekrar
    assert t.phase is Phase.CHAMPIONSHIP_TIEBREAKER
    play_phase(t, {"P5": 15, "P6": 21})
    assert t.champion.name == "P6"


def test_submit_after_finish_raises():
    t = Tournament(make_players(), random.Random(1))
    play_phase(t, {f"P{i}": 10 + i for i in range(8)})
    play_phase(t, {"P5": 30, "P6": 22, "P7": 25})
    with pytest.raises(RuntimeError):
        t.submit_score(10)


def test_duplicate_names_rejected():
    with pytest.raises(ValueError):
        Tournament([Player("A"), Player("A"), Player("B")])
