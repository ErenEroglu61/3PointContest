import random

from src.contest.ai import AI_ROSTER, ShooterProfile, ai_players, simulate_round
from src.contest.records import HighScores, ScoreRecord


def test_perfect_fast_shooter_scores_40():
    p = ShooterProfile(1.0, 1.0, 1.0, shot_time=0.5, move_time=0.5)
    assert simulate_round(p, 70, random.Random(0)).score == 40


def test_zero_accuracy_scores_zero():
    p = ShooterProfile(0.0, 0.0, 0.0)
    assert simulate_round(p, 70, random.Random(0)).score == 0


def test_time_limit_caps_shots():
    slow = ShooterProfile(1.0, 1.0, 1.0, shot_time=5.0, move_time=1.0)
    seq = simulate_round(slow, 30, random.Random(0))
    assert len(seq.results) < 27


def test_simulation_is_deterministic_with_seed():
    _, profile = AI_ROSTER[0]
    a = simulate_round(profile, 70, random.Random(42)).score
    b = simulate_round(profile, 70, random.Random(42)).score
    assert a == b


def test_logo_skipper_never_scores_blue_money():
    p = ShooterProfile(1.0, 1.0, 1.0, shot_time=0.5, move_time=0.5, skips_logo=True)
    seq = simulate_round(p, 70, random.Random(0))
    assert seq.score == 34


def test_ai_players_have_one_defending_champion():
    players = ai_players(7, random.Random(1))
    assert len(players) == 7
    assert sum(p.defending_champion for p in players) == 1


def test_highscores_sorted_and_ranked(tmp_path):
    hs = HighScores(tmp_path / "s.json", limit=3)
    assert hs.add(ScoreRecord("A", 10)) == 1
    assert hs.add(ScoreRecord("B", 20)) == 1
    assert hs.add(ScoreRecord("C", 15)) == 2
    assert hs.add(ScoreRecord("D", 5)) is None      # tabloya giremedi
    assert [r.name for r in hs.top()] == ["B", "C", "A"]


def test_highscores_roundtrip(tmp_path):
    path = tmp_path / "data" / "s.json"
    hs = HighScores(path)
    hs.add(ScoreRecord("EMRE", 31, "tournament"))
    hs.save()
    again = HighScores(path)
    assert again.top(1)[0].name == "EMRE"
    assert again.top(1)[0].mode == "tournament"


def test_corrupt_highscore_file_is_ignored(tmp_path):
    path = tmp_path / "s.json"
    path.write_text("{bozuk", encoding="utf-8")
    assert HighScores(path).records == []
