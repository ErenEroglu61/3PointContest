from dataclasses import dataclass

from src.contest.locations import MAIN_LOCATIONS,Spot

@dataclass(frozen=True)
class PlayerTurn:
    all_money_spot: Spot

    def __post_init__(self):
        if self.all_money_spot not in MAIN_LOCATIONS:
            raise ValueError("All money rack sadece ana lokasyonda var")