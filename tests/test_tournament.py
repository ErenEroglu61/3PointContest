from src.contest.tournament import (
    ADVANCE_COUNT,
    advancing_players,
    championship_order,
    needs_advancement_tiebreaker
)

def test_top_three_advance_to_championships():
    scores= {"a":10,"b":5,"c":8,"d":3,"e":1,"f":0,"g":7,"h":2}
    assert advancing_players(scores) == ["a","c","g"]

def test_advance_count_is_three():
    assert ADVANCE_COUNT == 3

def test_championship_order_is_lowest_first_round_score_first():
    scores = {"a": 10, "b": 5, "c": 8, "d": 3, "e": 1, "f": 0, "g": 7, "h": 2}
    advancers = advancing_players(scores)
    assert championship_order(scores,advancers) == ["g","c","a"]

def test_tie_at_advancement_cutoff_requires_tiebreaker():
    scores = {"a": 10, "b": 8, "c": 6, "d": 6, "e": 2, "f": 1, "g": 0, "h": 0}
    assert needs_advancement_tiebreaker(scores) is True

def test_no_tiebreaker_when_cutoff_is_clear():
    scores =  {"a": 10, "b": 8, "c": 7, "d": 6, "e": 2, "f": 1, "g": 0, "h": 0}
    assert needs_advancement_tiebreaker(scores) is False