"""Yapay zekâ rakipler: bir turu, isabet yüzdesine ve hızına göre anında simüle eder."""
import random
from dataclasses import dataclass

from src.contest.balls import BallType
from src.contest.locations import MAIN_LOCATIONS
from src.contest.rack import ShotSequence
from src.contest.tournament import Player


@dataclass(frozen=True)
class ShooterProfile:
    accuracy: float              # NBA topu isabet olasılığı
    money_accuracy: float        # money topu (aynı mesafe, biraz baskı)
    logo_accuracy: float         # mavi money (logo mesafesi)
    shot_time: float = 1.05      # bir topu alıp atma süresi (sn)
    move_time: float = 1.4       # bir istasyondan diğerine geçiş (sn)
    favorite_rack: str | None = None
    skips_logo: bool = False     # logo atışlarını atlayıp zaman kazanır

    def chance(self, ball: BallType) -> float:
        if ball is BallType.BLUE_MONEY:
            return self.logo_accuracy
        if ball is BallType.MONEY:
            return self.money_accuracy
        return self.accuracy


def simulate_round(
    profile: ShooterProfile,
    duration: float,
    rng: random.Random,
    money_rack: str | None = None,
) -> ShotSequence:
    """Bir turu baştan sona simüle eder ve atış kaydını döndürür."""
    if money_rack is None:
        money_rack = profile.favorite_rack or rng.choice(MAIN_LOCATIONS).name
    seq = ShotSequence(money_rack)
    clock = 0.0
    station_idx = 0

    while True:
        # Oyuncunun bulunduğu istasyon bittiyse bir sonrakine yürü
        while station_idx < len(seq.stations) and seq.stations[station_idx].exhausted:
            station_idx += 1
            clock += profile.move_time
        if station_idx >= len(seq.stations):
            break
        station = seq.stations[station_idx]
        if station.is_pedestal and profile.skips_logo and station_idx + 1 < len(seq.stations):
            station_idx += 1
            clock += profile.move_time * 0.6
            continue
        clock += profile.shot_time
        if clock > duration:
            break
        ball_idx = station.next_ball_index()
        made = rng.random() < profile.chance(station.balls[ball_idx].type)
        seq.attempt(station_idx, ball_idx, made)
    return seq


# Kurgusal rakipler (gerçek oyunculara dayanmaz)
AI_ROSTER: list[tuple[str, ShooterProfile]] = [
    ("KAAN DEMIR", ShooterProfile(0.62, 0.58, 0.40, 0.98, 1.30, "corner_right")),
    ("ARDA KAYA", ShooterProfile(0.57, 0.55, 0.36, 1.02, 1.35, "wing_left")),
    ("MERT YILDIZ", ShooterProfile(0.54, 0.50, 0.30, 1.00, 1.40, "center")),
    ("CAN AKSOY", ShooterProfile(0.60, 0.52, 0.22, 0.95, 1.25, "corner_left", skips_logo=True)),
    ("BARIS OZ", ShooterProfile(0.50, 0.48, 0.34, 1.10, 1.45, "wing_right")),
    ("ONUR CELIK", ShooterProfile(0.56, 0.56, 0.38, 1.05, 1.35, "corner_right")),
    ("EGE TUNC", ShooterProfile(0.52, 0.47, 0.33, 1.00, 1.40, None)),
    ("SINAN KOC", ShooterProfile(0.58, 0.54, 0.35, 1.08, 1.30, "corner_left")),
]


def ai_players(count: int, rng: random.Random | None = None) -> dict[Player, ShooterProfile]:
    """``count`` adet yapay zekâ oyuncusu; birini rastgele savunan şampiyon yapar."""
    rng = rng or random.Random()
    if not 0 <= count <= len(AI_ROSTER):
        raise ValueError(f"en fazla {len(AI_ROSTER)} yapay zekâ oyuncusu var")
    picked = rng.sample(AI_ROSTER, count)
    champion_idx = rng.randrange(count) if count else -1
    return {
        Player(name, defending_champion=(i == champion_idx)): profile
        for i, (name, profile) in enumerate(picked)
    }
