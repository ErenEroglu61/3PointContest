"""Rack durumu, atış sırası kontrolü ve mavi money eliminasyonu.

Kurallar (2026 State Farm 3-Point Contest):
- 4 standart rack: 4 NBA topu + 1 money topu. Money topu, 4 NBA topu atılmadan
  atılırsa atış geçersizdir (void).
- 1 "all money" rack: 5 money topu, yeri oyuncu tarafından seçilir.
- 2 "From the Logo" pedestalı: her birinde 1 mavi money topu (3 puan).
- Rack'ler ve pedestallar yarışma sırasıyla bitirilmelidir. Sırası gelmeden
  atılan mavi money topu void olur. Mavi money atlanıp sonraki rack'ten top
  atılırsa mavi money elenir; sonradan atılıp girse bile sayılmaz.
"""
from dataclasses import dataclass

from src.contest.balls import BallType
from src.contest.locations import COMPETITION_ORDER, MAIN_LOCATIONS, Spot, SpotKind
from src.contest.scoring import ShotResult, ShotStatus, score_for_made_shot, total_score

BALLS_PER_RACK = 5
TOTAL_BALLS = 27


@dataclass
class RackBall:
    type: BallType
    shot: bool = False
    eliminated: bool = False

    @property
    def available(self) -> bool:
        return not self.shot and not self.eliminated


@dataclass
class Station:
    spot: Spot
    balls: list[RackBall]
    all_money: bool = False

    @property
    def name(self) -> str:
        return self.spot.name

    @property
    def is_pedestal(self) -> bool:
        return self.spot.kind is SpotKind.PEDESTAL

    @property
    def remaining(self) -> list[int]:
        return [i for i, b in enumerate(self.balls) if b.available]

    @property
    def exhausted(self) -> bool:
        return not self.remaining

    def next_ball_index(self) -> int | None:
        remaining = self.remaining
        return remaining[0] if remaining else None


def build_stations(money_rack: str) -> list[Station]:
    """Yarışma sırasındaki 7 istasyonu (5 rack + 2 pedestal) oluşturur."""
    rack_names = [s.name for s in MAIN_LOCATIONS]
    if money_rack not in rack_names:
        raise ValueError(f"all money rack bir ana lokasyonda olmalı: {rack_names}")

    stations: list[Station] = []
    for spot in COMPETITION_ORDER:
        if spot.kind is SpotKind.PEDESTAL:
            stations.append(Station(spot, [RackBall(BallType.BLUE_MONEY)]))
        elif spot.name == money_rack:
            balls = [RackBall(BallType.MONEY) for _ in range(BALLS_PER_RACK)]
            stations.append(Station(spot, balls, all_money=True))
        else:
            balls = [RackBall(BallType.NBA) for _ in range(BALLS_PER_RACK - 1)]
            balls.append(RackBall(BallType.MONEY))
            stations.append(Station(spot, balls))
    return stations


class ShotSequence:
    """Bir oyuncunun 27 topluk turundaki tüm atışları takip eder.

    İki aşamalı kullanım (oyun için): ``release`` topun elden çıktığı anı,
    ``resolve`` topun girip girmediğinin belli olduğu anı kaydeder.
    Testler için tek adımlı ``attempt`` da vardır.
    """

    def __init__(self, money_rack: str):
        self.money_rack = money_rack
        self.stations = build_stations(money_rack)
        self.results: list[ShotResult] = []

    # --- durum sorguları -------------------------------------------------
    @property
    def current_index(self) -> int | None:
        """Hâlâ atılabilir topu olan ilk istasyonun sırası."""
        for i, station in enumerate(self.stations):
            if not station.exhausted:
                return i
        return None

    def station_index(self, name: str) -> int:
        for i, station in enumerate(self.stations):
            if station.name == name:
                return i
        raise KeyError(name)

    def next_shot(self) -> tuple[int, int] | None:
        """Kurallara uygun bir sonraki atış: (istasyon, top)."""
        si = self.current_index
        if si is None:
            return None
        return si, self.stations[si].next_ball_index()

    @property
    def balls_left(self) -> int:
        return sum(len(s.remaining) for s in self.stations)

    @property
    def score(self) -> int:
        return total_score(self.results)

    @property
    def finished(self) -> bool:
        return self.current_index is None

    # --- atışlar ---------------------------------------------------------
    def release(self, station_idx: int, ball_idx: int, line_violation: bool = False) -> ShotResult:
        station = self.stations[station_idx]
        ball = station.balls[ball_idx]
        if ball.shot:
            raise ValueError(f"{station.name}[{ball_idx}] zaten atıldı")

        def record(status: ShotStatus) -> ShotResult:
            ball.shot = True
            result = ShotResult(station.name, ball_idx, ball.type, status)
            self.results.append(result)
            return result

        if ball.eliminated:
            return record(ShotStatus.VOID_ELIMINATED)

        current = self.current_index
        if current is not None and station_idx > current:
            skipped = self.stations[current:station_idx]
            rack_left_behind = any(not s.is_pedestal and not s.exhausted for s in skipped)
            if station.is_pedestal or rack_left_behind:
                return record(ShotStatus.VOID_OUT_OF_SEQUENCE)
            # Yalnızca pedestal(lar) atlandı: mavi money topları elenir.
            for s in skipped:
                for b in s.balls:
                    if b.available:
                        b.eliminated = True

        if (
            not station.all_money
            and ball.type is BallType.MONEY
            and any(b.type is BallType.NBA and not b.shot for b in station.balls)
        ):
            return record(ShotStatus.VOID_OUT_OF_SEQUENCE)

        if line_violation:
            return record(ShotStatus.VOID_LINE_VIOLATION)

        return record(ShotStatus.PENDING)

    def resolve(self, result: ShotResult, made: bool) -> ShotResult:
        if result.status is not ShotStatus.PENDING:
            return result  # void atışlar sonradan değişmez
        result.status = ShotStatus.MADE if made else ShotStatus.MISSED
        result.points = score_for_made_shot(result.ball, made)
        return result

    def attempt(self, station_idx: int, ball_idx: int, made: bool, line_violation: bool = False) -> ShotResult:
        return self.resolve(self.release(station_idx, ball_idx, line_violation), made)
