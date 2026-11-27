"""Topların 3B gösterimi: rack'teki, eldeki ve havadaki topların çizim listesi."""
import math
from dataclasses import dataclass

import numpy as np

from src.contest.balls import BallType
from src.contest.rack import build_stations
from src.game import layout
from src.graphics.utils.hoop import (MAT_BALL, MAT_BLUE_MONEY, MAT_MONEY, ball_slot_position)
from src.graphics.utils.math_utils import rotate_axis, rotate_x, rotate_y

MATERIAL_FOR = {BallType.NBA: MAT_BALL, BallType.MONEY: MAT_MONEY, BallType.BLUE_MONEY: MAT_BLUE_MONEY}


@dataclass
class BallDraw:
    position: np.ndarray
    ball_type: BallType
    rotation: np.ndarray
    dim: bool = False         # elenmiş top (soluk çizilir)


def _rack_rotation(seed: int) -> np.ndarray:
    return rotate_y(seed * 1.7) @ rotate_x(seed * 0.9)


def rack_balls(stations, hidden: tuple[int, int] | None = None) -> list[BallDraw]:
    draws = []
    for si, station in enumerate(stations):
        for bi, ball in enumerate(station.balls):
            if ball.shot or (hidden is not None and hidden == (si, bi)):
                continue
            pos = ball_slot_position(station.name, bi, station.is_pedestal)
            draws.append(BallDraw(pos, ball.type, _rack_rotation(si * 5 + bi), dim=ball.eliminated))
    return draws


def preview_balls(money_rack: str) -> list[BallDraw]:
    """Tur başlamadan (rack seçimi ekranı) gösterilecek dizilim."""
    return rack_balls(build_stations(money_rack))


def round_balls(game_round) -> list[BallDraw]:
    held = game_round.held_ball()
    draws = rack_balls(game_round.stations, hidden=held)
    if held is not None:
        si, bi = held
        ball_type = game_round.stations[si].balls[bi].type
        x, z = game_round.player_position()
        fx, fz = game_round.facing()
        lift = game_round.meter.value if game_round.meter.charging else 0.0
        y = 1.25 + lift * (layout.RELEASE_HEIGHT - 1.25)
        pos = np.array([x + fx * (0.35 - 0.05 * lift), y, z + fz * (0.35 - 0.05 * lift)])
        draws.append(BallDraw(pos, ball_type, rotate_y(math.atan2(fx, fz))))
    for fb in game_round.flying:
        b = fb.body
        draws.append(BallDraw(b.position.copy(), fb.ball_type, rotate_axis(b.spin_axis, b.spin_angle)))
    return draws
