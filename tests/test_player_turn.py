import pytest

from dataclasses import FrozenInstanceError
from src.contest.locations import MAIN_LOCATIONS
from src.contest.player_turn import PlayerTurn

def test_all_money_rack_can_be_placed_at_any_main_locations():
    for spot in  MAIN_LOCATIONS:
        turn = PlayerTurn(all_money_spot=spot)
        assert turn.all_money_spot == spot

def test_all_money_rack_cannot_be_placed_at_a_pedestal():
    from src.contest.locations import FROM_THE_LOGO
    with pytest.raises(ValueError):
        PlayerTurn(all_money_spot=FROM_THE_LOGO[0])

def test_all_money_spot_is_fixed_for_the_whole_turn():
    spot = MAIN_LOCATIONS[2]
    turn = PlayerTurn(all_money_spot=spot)
    with pytest.raises(FrozenInstanceError):
        turn.all_money_spot = MAIN_LOCATIONS[0]