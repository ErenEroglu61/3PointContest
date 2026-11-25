from src.contest.balls import BallType, POINTS

def test_nba_ball_is_worth_one_point():
    assert POINTS[BallType.NBA] == 1

def test_money_ball_is_worth_two_points():
    assert POINTS[BallType.MONEY] == 2

def test_blue_money_ball_is_worth_three_points():
    assert POINTS[BallType.BLUE_MONEY] == 3
