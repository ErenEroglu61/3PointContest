from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from src.contest.balls import BallType, POINTS


def score_for_made_shot(ball: BallType, made: bool = True) -> int:
    if not made:
        return 0
    return POINTS[ball]


class ShotStatus(Enum):
    PENDING = "pending"                       # top havada, sonuç bekleniyor
    MADE = "made"
    MISSED = "missed"
    VOID_OUT_OF_SEQUENCE = "void_sequence"    # sıra dışı atış (money/mavi money erken atıldı)
    VOID_ELIMINATED = "void_eliminated"       # atlanmış, elenmiş mavi money topu
    VOID_LINE_VIOLATION = "void_line"         # çizgiye basarak atış

    @property
    def is_void(self) -> bool:
        return self in (
            ShotStatus.VOID_OUT_OF_SEQUENCE,
            ShotStatus.VOID_ELIMINATED,
            ShotStatus.VOID_LINE_VIOLATION,
        )


@dataclass
class ShotResult:
    station: str
    ball_index: int
    ball: BallType
    status: ShotStatus
    points: int = 0


def total_score(results: Iterable[ShotResult]) -> int:
    return sum(r.points for r in results)
