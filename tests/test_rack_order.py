import pytest
from src.contest.balls import BallType
from src.contest.rack import Rack

def test_money_ball_before_nba_scores_zero():
    rack = Rack.standard()
    assert rack.shoot(BallType.MONEY, made=True) == 0

def test_money_ball_after_four_nba_balls_scores_two():
    rack = Rack.standard()
    for _ in range(4):
        rack.shoot(BallType.NBA,made=True)
    assert rack.shoot(BallType.MONEY,made=True) == 2

def test_shooting_from_empty_rack_raises():
    rack = Rack.all_money()
    for _ in range(5):
        rack.shoot(BallType.MONEY,made=True)
    with pytest.raises(ValueError):
        rack.shoot(BallType.MONEY,made=True)