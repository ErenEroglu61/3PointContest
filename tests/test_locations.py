from src.contest.locations import MAIN_LOCATIONS, FROM_THE_LOGO, SpotKind

def test_there_are_five_main_loc():
    assert len(MAIN_LOCATIONS) == 5

def test_there_are_two_from_the_logo_pedestals():
    assert len(FROM_THE_LOGO) == 2

def test_all_spot_names_are_unique():
    names = [s.name for s in MAIN_LOCATIONS + FROM_THE_LOGO]
    assert len(names) == len(set(names))

def test_main_locations_are_racks_and_logo_spots_are_pedestals():
    assert all(s.kind is SpotKind.RACK for s in MAIN_LOCATIONS)
    assert all(s.kind is SpotKind.PEDESTAL for s in FROM_THE_LOGO)