from src.contest.balls import BallType
from src.contest.scoring import score_for_made_shot

def test_made_nba_ball_scores_one_point():
    assert score_for_made_shot(BallType.NBA) == 1

def test_made_money_ball_scores_two_points():
    assert score_for_made_shot(BallType.MONEY) == 2

def test_made_blue_money_ball_scores_three_points():
    assert score_for_made_shot(BallType.BLUE_MONEY) == 3

def test_missed_shot_nba_scores_zero():
    assert score_for_made_shot(BallType.NBA, made=False) == 0

def test_missed_shot_money_scores_zero():
    assert score_for_made_shot(BallType.MONEY,made=False) == 0

def test_missed_shot_blue_money_scores_zero():
    assert score_for_made_shot(BallType.BLUE_MONEY,made=False) == 0