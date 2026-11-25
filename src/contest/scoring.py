from src.contest.balls import BallType, POINTS

def score_for_made_shot(ball: BallType, made: bool = True) -> int:
    if not made:
        return 0
    return POINTS[ball]