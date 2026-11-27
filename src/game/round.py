"""Bir oyuncunun 70 saniyelik turu: süre, güç barı, istasyon geçişleri ve havadaki toplar.

Grafikten bağımsızdır; renderer yalnızca bu nesnenin durumunu okur.
"""
import math
import random
from dataclasses import dataclass
from enum import Enum

import numpy as np

from src.contest.balls import BallType
from src.contest.rack import ShotSequence
from src.contest.scoring import ShotResult, ShotStatus
from src.contest.timer import ROUND_SECONDS, ContestTimer
from src.game import layout
from src.physics.ball_physics import BallBody, PhysicsWorld
from src.physics.shot import PowerMeter, shot_velocity

MOVE_TIME = 0.9          # rack'ten rack'e yürüme süresi (sn)
PEDESTAL_MOVE_TIME = 1.1
RELOAD_TIME = 0.6        # rack'ten yeni top alma süresi
MAX_BALL_AGE = 7.0       # yerde kalan topların sahneden kaldırılma süresi
MISS_TIMEOUT = 6.0


class RoundPhase(Enum):
    COUNTDOWN = "countdown"
    LIVE = "live"
    WAITING = "waiting"   # süre bitti / top kalmadı, havadaki toplar bekleniyor
    DONE = "done"


@dataclass
class FlyingBall:
    body: BallBody
    result: ShotResult
    ball_type: BallType
    age: float = 0.0
    resolved: bool = False


def _smoothstep(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class GameRound:
    def __init__(self, money_rack: str, duration: float = ROUND_SECONDS, countdown: float = 3.0,
                 rng: random.Random | None = None):
        self.seq = ShotSequence(money_rack)
        self.timer = ContestTimer(duration)
        self.meter = PowerMeter()
        self.world = PhysicsWorld()
        self.rng = rng or random.Random()
        self._events: list[tuple[str, dict]] = []
        self.countdown = countdown
        self.phase = RoundPhase.COUNTDOWN
        if countdown <= 0:
            self._go()
        self.player_station = 0
        self._move_from: int | None = None
        self._move_t = 0.0
        self._move_duration = MOVE_TIME
        self.reload = 0.0
        self.flying: list[FlyingBall] = []
        self.time = 0.0
        self.last_made_time = -10.0     # file animasyonu için

    # ------------------------------------------------------------------
    # durum
    @property
    def score(self) -> int:
        return self.seq.score

    @property
    def stations(self):
        return self.seq.stations

    @property
    def station(self):
        return self.seq.stations[self.player_station]

    @property
    def moving(self) -> bool:
        return self._move_from is not None

    @property
    def done(self) -> bool:
        return self.phase is RoundPhase.DONE

    @property
    def can_shoot(self) -> bool:
        return (self.phase is RoundPhase.LIVE and not self.moving and self.reload <= 0
                and not self.station.exhausted)

    @property
    def can_skip(self) -> bool:
        return (self.phase is RoundPhase.LIVE and not self.moving and self.station.is_pedestal
                and not self.station.exhausted and self._next_station() is not None)

    def held_ball(self) -> tuple[int, int] | None:
        """Oyuncunun elindeki (rack'ten alınmış) top."""
        if self.phase in (RoundPhase.COUNTDOWN, RoundPhase.LIVE) and not self.moving and self.reload <= 0:
            bi = self.station.next_ball_index()
            if bi is not None:
                return self.player_station, bi
        return None

    def player_position(self) -> tuple[float, float]:
        target = layout.SPOT_POSITIONS[self.station.name]
        if self._move_from is None:
            return target
        start = layout.SPOT_POSITIONS[self.seq.stations[self._move_from].name]
        t = _smoothstep(self._move_t / self._move_duration)
        return (start[0] + (target[0] - start[0]) * t, start[1] + (target[1] - start[1]) * t)

    def facing(self) -> tuple[float, float]:
        """Oyuncudan potaya yatay birim vektör."""
        x, z = self.player_position()
        n = math.hypot(x, z) or 1.0
        return (-x / n, -z / n)

    def release_point(self) -> np.ndarray:
        x, z = self.player_position()
        fx, fz = self.facing()
        return np.array([x + fx * 0.3, layout.RELEASE_HEIGHT, z + fz * 0.3])

    def drain_events(self) -> list[tuple[str, dict]]:
        events, self._events = self._events, []
        return events

    # ------------------------------------------------------------------
    # girdi
    def press(self) -> bool:
        if self.can_shoot and not self.meter.charging:
            self.meter.start()
            return True
        return False

    def release(self) -> FlyingBall | None:
        if not self.meter.charging:
            return None
        value = self.meter.release()
        if not self.can_shoot:
            return None
        si = self.player_station
        bi = self.station.next_ball_index()
        result = self.seq.release(si, bi)
        start = self.release_point()
        velocity = shot_velocity(start, self.world.hoop.center, value, self.rng)
        fb = FlyingBall(BallBody(start, velocity), result, result.ball)
        self.flying.append(fb)
        self.reload = RELOAD_TIME
        self._emit("release", meter=value, ball=result.ball)
        if result.status.is_void:
            self._emit("void", status=result.status, ball=result.ball)
        if self.station.exhausted:
            self._advance_station()
        return fb

    def skip(self) -> bool:
        """Logo pedestalını atlayıp sonraki rack'e geç (mavi money elenir)."""
        if not self.can_skip:
            return False
        self._emit("skip", station=self.station.name)
        self._advance_station()
        return True

    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.time += dt
        if self.phase is RoundPhase.COUNTDOWN:
            before = math.ceil(self.countdown)
            self.countdown -= dt
            if self.countdown <= 0:
                self._go()
            elif math.ceil(self.countdown) != before:
                self._emit("countdown", value=math.ceil(self.countdown))
        elif self.phase is RoundPhase.LIVE:
            if self.timer.update(dt):
                self.meter.cancel()
                self.phase = RoundPhase.WAITING
                self._emit("buzzer")

        self.meter.update(dt)
        self.reload = max(0.0, self.reload - dt)
        if self._move_from is not None:
            self._move_t += dt
            if self._move_t >= self._move_duration:
                self._move_from = None
                self._emit("arrive", station=self.station.name)

        self._update_balls(dt)

        if self.phase is RoundPhase.LIVE and self._no_balls_left():
            self.timer.pause()
            self.phase = RoundPhase.WAITING
            self._emit("all_shot")
        if self.phase is RoundPhase.WAITING and all(fb.resolved for fb in self.flying):
            self.phase = RoundPhase.DONE
            self._emit("done", score=self.score)

    # ------------------------------------------------------------------
    def _go(self) -> None:
        self.phase = RoundPhase.LIVE
        self.timer.start()
        self._emit("go")

    def _emit(self, kind: str, **data) -> None:
        self._events.append((kind, data))

    def _next_station(self) -> int | None:
        for j in range(self.player_station + 1, len(self.seq.stations)):
            if not self.seq.stations[j].exhausted:
                return j
        return None

    def _advance_station(self) -> None:
        nxt = self._next_station()
        if nxt is None:
            return
        self._move_from = self.player_station
        self._move_t = 0.0
        pedestal_involved = self.station.is_pedestal or self.seq.stations[nxt].is_pedestal
        self._move_duration = PEDESTAL_MOVE_TIME if pedestal_involved else MOVE_TIME
        self.player_station = nxt
        self._emit("move", station=self.station.name)

    def _no_balls_left(self) -> bool:
        return all(s.exhausted for s in self.seq.stations[self.player_station:]) and not self.moving

    def _update_balls(self, dt: float) -> None:
        for fb in self.flying:
            fb.age += dt
            for event in self.world.step(fb.body, dt):
                if event == "made" and not fb.resolved:
                    fb.resolved = True
                    self.seq.resolve(fb.result, made=True)
                    self.last_made_time = self.time
                    self._emit("made", points=fb.result.points, ball=fb.ball_type,
                               void=fb.result.status is not ShotStatus.MADE)
                elif event in ("rim", "board", "floor"):
                    self._emit(event)
            if not fb.resolved and (fb.body.touched_floor or fb.age > MISS_TIMEOUT):
                fb.resolved = True
                self.seq.resolve(fb.result, made=False)
                self._emit("miss", ball=fb.ball_type)
        # Yerde duran eski topları kaldır
        self.flying = [fb for fb in self.flying
                       if not (fb.resolved and (fb.age > MAX_BALL_AGE or fb.body.resting and fb.age > 3.0))]
