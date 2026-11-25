from enum import Enum

class BallType(Enum):
    NBA = "nba"
    MONEY = "money"
    BLUE_MONEY = "blue_money"

POINTS: dict[BallType, int] = {
    BallType.NBA: 1,
    BallType.MONEY: 2,
    BallType.BLUE_MONEY: 3
}