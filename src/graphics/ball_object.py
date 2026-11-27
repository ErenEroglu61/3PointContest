import math
from dataclasses import dataclass

import moderngl
import numpy as np

from src.graphics.spots import MAIN_POSITIONS, FROM_THE_LOGO_POSITIONS

BALL_RADIUS = 0.12
RACK_BALL_HEIGHT = 1.0
PEDESTAL_HEIGHT = 1.1
RACK_BALL_SPACING = 0.3
SPHERE_STACKS = 12
SPHERE_SLICES = 16

COLORS = {
    "nba": (0.95, 0.45, 0.10),
    "money": (0.20, 0.80, 0.30),
    "blue_money": (0.10, 0.30, 1.00)
}

@dataclass
class BallObject:
    position: np.ndarray
    color: tuple[float,float,float]

def build_sphere_vao(ctx: moderngl.Context, program: moderngl.Program) -> moderngl.VertexArray:
    def point(theta: float, phi: float) -> list[float]:
        return [
            BALL_RADIUS * math.sin(theta) * math.cos(phi),
            BALL_RADIUS * math.cos(theta),
            BALL_RADIUS * math.sin(theta) * math.sin(phi)
        ]

    verts = []
    for i in range(SPHERE_STACKS):
        t0 = math.pi * i / SPHERE_STACKS
        t1 = math.pi * (i + 1) / SPHERE_STACKS
        for j in range(SPHERE_SLICES):
            p0 = 2 * math.pi * j / SPHERE_SLICES
            p1 = 2 * math.pi * (j + 1) / SPHERE_SLICES
            a, b = point(t0, p0), point(t1, p0)
            c, d = point(t1, p1), point(t0,p1)
            verts += [a,b,c,a,c,d]

    vbo = ctx.buffer(np.array(verts, dtype="f4").tobytes())
    return ctx.vertex_array(program,[(vbo,"3f","in_position")])

def _rack(spot_pos: np.ndarray) -> list[BallObject]:
    balls = []
    for k in range(5):
        kind = "nba" if k < 4 else "money"
        offset = np.array([0.0, 0.0, (k - 2) * RACK_BALL_SPACING])
        pos = spot_pos + offset
        pos[1] = RACK_BALL_HEIGHT
        balls.append(BallObject(pos,COLORS[kind]))
    return balls

def _all_money_rack(spot_pos: np.ndarray) -> list[BallObject]:
    balls = []
    for k in range(5):
        pos = spot_pos + np.array([0.0, 0.0, (k - 2) * RACK_BALL_SPACING])
        pos[1] = RACK_BALL_HEIGHT
        balls.append(BallObject(pos, COLORS["money"]))
    return balls

def build_scene(all_money_spot: str = "top") -> list[BallObject]:
    balls: list[BallObject] = []
    for name, pos in MAIN_POSITIONS.items():
        if name == all_money_spot:
            balls += _all_money_rack(pos)
        else:
            balls += _rack(pos)

    for pos in FROM_THE_LOGO_POSITIONS.values():
        p = pos.copy()
        p[1] = PEDESTAL_HEIGHT
        balls.append(BallObject(p, COLORS["blue_money"]))

    return balls