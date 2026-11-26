from dataclasses import dataclass

from src.contest.balls import BallType
from src.contest.scoring import score_for_made_shot

@dataclass
class Rack:
    nba_remaining: int
    money_remaining: int

    @classmethod
    def standard(cls) -> "Rack":
        return cls(nba_remaining=4,money_remaining=1)

    @classmethod
    def all_money(cls) -> "Rack":
        return cls(nba_remaining=0,money_remaining=5)

    def is_empty(self) -> bool:
        return self.nba_remaining == 0 and self.money_remaining == 0

    def shoot(self,ball:BallType,made: bool = True) -> int:
        if self.is_empty():
            raise ValueError("Rack boş, atış yapılamaz")

        if ball is BallType.NBA:
            if self.nba_remaining == 0:
                raise ValueError("Rack'te top kalmadı")
            self.nba_remaining -= 1
            return score_for_made_shot(ball,made)

        if ball is BallType.MONEY:
            if self.money_remaining == 0:
                raise ValueError("Rack'te money topu kalmadı")
            self.money_remaining -= 1
            if self.nba_remaining > 0:
                return 0
            return score_for_made_shot(ball,made)

        raise ValueError(f"Bu rack {ball} içermez")