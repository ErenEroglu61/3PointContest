ADVANCE_COUNT = 3

def advancing_players(scores: dict[str,int]) -> list[str]:
    ranked = sorted(scores, key=lambda p: scores[p], reverse=True)
    return ranked[:ADVANCE_COUNT]

def needs_advancement_tiebreaker(scores: dict[str,int]) -> bool:
    values = sorted(scores.values(),reverse=True)
    return values[ADVANCE_COUNT - 1] == values[ADVANCE_COUNT]

def championship_order(scores: dict[str,int], advancers: list[str]) -> list[str]:
    return sorted(advancers,key=lambda p:scores[p])
