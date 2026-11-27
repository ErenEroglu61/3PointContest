"""Turnuva akışı: ilk tur, ilk tur tiebreaker'ı, şampiyonluk turu ve final tiebreaker'ı.

- 8 oyuncu, ilk tur sırası kura ile; geçen yılın şampiyonu (katılıyorsa) en son atar.
- İlk turdan en yüksek skorlu 3 oyuncu finale çıkar. Kesme çizgisindeki
  eşitlik 30 saniyelik tiebreaker ile, eşitlik bozulana kadar tekrarlanarak çözülür.
- Finalde sıra, ilk tur skorlarının tersidir (en düşük skorlu ilk atar).
- Şampiyonluk eşitliği 70 saniyelik tiebreaker ile, bozulana kadar çözülür.
"""
import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

from src.contest.timer import (
    CHAMPIONSHIP_TIEBREAKER_SECONDS,
    FIRST_ROUND_TIEBREAKER_SECONDS,
    ROUND_SECONDS,
)

PLAYERS_IN_CONTEST = 8
FINALISTS = 3


@dataclass(frozen=True)
class Player:
    name: str
    defending_champion: bool = False
    human: bool = False


class Phase(Enum):
    FIRST_ROUND = "first_round"
    FIRST_ROUND_TIEBREAKER = "first_round_tiebreaker"
    CHAMPIONSHIP = "championship"
    CHAMPIONSHIP_TIEBREAKER = "championship_tiebreaker"
    FINISHED = "finished"


PHASE_LABELS = {
    Phase.FIRST_ROUND: "ILK TUR",
    Phase.FIRST_ROUND_TIEBREAKER: "ILK TUR TIEBREAKER",
    Phase.CHAMPIONSHIP: "SAMPIYONLUK TURU",
    Phase.CHAMPIONSHIP_TIEBREAKER: "FINAL TIEBREAKER",
    Phase.FINISHED: "TURNUVA BITTI",
}


@dataclass(frozen=True)
class Turn:
    player: Player
    phase: Phase
    duration: float


def first_round_order(players: list[Player], rng: random.Random | None = None) -> list[Player]:
    """Kura ile sıra; savunan şampiyon en sona."""
    rng = rng or random.Random()
    champions = [p for p in players if p.defending_champion]
    others = [p for p in players if not p.defending_champion]
    rng.shuffle(others)
    return others + champions


def resolve_cut(scores: dict[Player, int], slots: int) -> tuple[list[Player], list[Player], int]:
    """Skorlara göre ``slots`` kişilik kontenjanı dağıtır.

    Dönüş: (kesin geçenler, kesme çizgisinde eşit kalanlar, eşitler için kalan kontenjan).
    Eşitlik yoksa ikinci eleman boş listedir.
    """
    ranked = sorted(scores, key=lambda p: scores[p], reverse=True)
    if slots <= 0:
        return [], [], 0
    if len(ranked) <= slots:
        return ranked, [], 0
    cutoff = scores[ranked[slots - 1]]
    above = [p for p in ranked if scores[p] > cutoff]
    at_cutoff = [p for p in ranked if scores[p] == cutoff]
    if len(above) + len(at_cutoff) == slots:
        return above + at_cutoff, [], 0
    return above, at_cutoff, slots - len(above)


@dataclass
class TiebreakerRecord:
    phase: Phase
    scores: dict[Player, int] = field(default_factory=dict)


class Tournament:
    def __init__(self, players: list[Player], rng: random.Random | None = None):
        if len(players) < FINALISTS:
            raise ValueError(f"en az {FINALISTS} oyuncu gerekli")
        if len({p.name for p in players}) != len(players):
            raise ValueError("oyuncu isimleri benzersiz olmalı")
        self.players = list(players)
        self.rng = rng or random.Random()
        self.phase = Phase.FIRST_ROUND
        self.first_round_scores: dict[Player, int] = {}
        self.championship_scores: dict[Player, int] = {}
        self.tiebreakers: list[TiebreakerRecord] = []
        self.finalists: list[Player] = []
        self.champion: Player | None = None
        self._slots_left = FINALISTS
        self.order = first_round_order(self.players, self.rng)
        self._queue: deque[Turn] = deque(Turn(p, Phase.FIRST_ROUND, ROUND_SECONDS) for p in self.order)

    # ------------------------------------------------------------------
    @property
    def current_turn(self) -> Turn | None:
        return self._queue[0] if self._queue else None

    @property
    def upcoming(self) -> list[Turn]:
        return list(self._queue)

    @property
    def finished(self) -> bool:
        return self.phase is Phase.FINISHED

    def submit_score(self, score: int) -> Turn:
        if not self._queue:
            raise RuntimeError("sırada atış yok")
        if score < 0:
            raise ValueError("skor negatif olamaz")
        turn = self._queue.popleft()
        if turn.phase is Phase.FIRST_ROUND:
            self.first_round_scores[turn.player] = score
        elif turn.phase is Phase.CHAMPIONSHIP:
            self.championship_scores[turn.player] = score
        else:
            self.tiebreakers[-1].scores[turn.player] = score
        if not self._queue:
            self._advance_phase()
        return turn

    # ------------------------------------------------------------------
    def _advance_phase(self) -> None:
        if self.phase is Phase.FIRST_ROUND:
            self._apply_cut(self.first_round_scores)
        elif self.phase is Phase.FIRST_ROUND_TIEBREAKER:
            self._apply_cut(self.tiebreakers[-1].scores)
        elif self.phase is Phase.CHAMPIONSHIP:
            self._decide_champion(self.championship_scores)
        elif self.phase is Phase.CHAMPIONSHIP_TIEBREAKER:
            self._decide_champion(self.tiebreakers[-1].scores)

    def _apply_cut(self, scores: dict[Player, int]) -> None:
        sure, tied, slots = resolve_cut(scores, self._slots_left)
        self.finalists.extend(sure)
        self._slots_left -= len(sure)
        if tied:
            self._start_tiebreaker(Phase.FIRST_ROUND_TIEBREAKER, tied, FIRST_ROUND_TIEBREAKER_SECONDS)
        else:
            self._start_championship()

    def _start_tiebreaker(self, phase: Phase, players: list[Player], duration: float) -> None:
        self.phase = phase
        self.tiebreakers.append(TiebreakerRecord(phase))
        # Tiebreaker'da ilk turdaki atış sırası korunur.
        order = {p: i for i, p in enumerate(self.order)}
        for p in sorted(players, key=lambda p: order[p]):
            self._queue.append(Turn(p, phase, duration))

    def _start_championship(self) -> None:
        self.phase = Phase.CHAMPIONSHIP
        # Ters sıra: ilk turda en düşük skoru alan ilk atar.
        order = sorted(self.finalists, key=lambda p: self.first_round_scores[p])
        for p in order:
            self._queue.append(Turn(p, Phase.CHAMPIONSHIP, ROUND_SECONDS))

    def _decide_champion(self, scores: dict[Player, int]) -> None:
        sure, tied, _ = resolve_cut(scores, 1)
        if sure:
            self.champion = sure[0]
            self.phase = Phase.FINISHED
        else:
            self._start_tiebreaker(Phase.CHAMPIONSHIP_TIEBREAKER, tied, CHAMPIONSHIP_TIEBREAKER_SECONDS)
