"""Basketbol topu fiziği (hava direnci ihmal edilir): yerçekimi, çember/panya/zemin çarpışmaları ve sayı tespiti.

Grafikten bağımsızdır; yalnızca NumPy kullanır.
"""
import math
from dataclasses import dataclass, field

import numpy as np

from src.game import layout

GRAVITY = 9.81
SUBSTEP = 1.0 / 600.0           # pota çevresinde alt adım (sn): hızlı top çemberi kaçırmasın
COARSE_STEP = 1.0 / 120.0       # serbest uçuş ve zeminde alt adım
ROLLING_FRICTION = 3.0          # yerde yuvarlanma sönümü (1/sn)
RIM_RESTITUTION = 0.55
BOARD_RESTITUTION = 0.65
FLOOR_RESTITUTION = 0.72


@dataclass
class Hoop:
    center: np.ndarray = field(default_factory=lambda: np.array([0.0, layout.RIM_HEIGHT, 0.0]))
    rim_radius: float = layout.RIM_RADIUS
    tube_radius: float = layout.RIM_TUBE
    board_front_z: float = layout.BACKBOARD_FRONT_Z
    board_half_width: float = layout.BACKBOARD_HALF_WIDTH
    board_bottom: float = layout.BACKBOARD_BOTTOM
    board_top: float = layout.BACKBOARD_TOP
    board_thickness: float = layout.BACKBOARD_THICKNESS


@dataclass
class BallBody:
    position: np.ndarray
    velocity: np.ndarray
    radius: float = layout.BALL_RADIUS
    made: bool = False            # çemberin içinden aşağı geçti
    touched_rim: bool = False
    touched_floor: bool = False
    resting: bool = False
    in_net_time: float = 0.0      # file içindeki süre (animasyon için)
    spin_angle: float = 0.0       # görsel geri dönüş (backspin) açısı
    spin_axis: np.ndarray = field(default_factory=lambda: np.array([1.0, 0.0, 0.0]))

    def __post_init__(self):
        self.position = np.asarray(self.position, dtype=float).copy()
        self.velocity = np.asarray(self.velocity, dtype=float).copy()
        horizontal = np.array([self.velocity[0], 0.0, self.velocity[2]])
        n = np.linalg.norm(horizontal)
        if n > 1e-6:
            # Geri dönüş ekseni: uçuş yönüne dik, yatay
            d = horizontal / n
            self.spin_axis = np.array([d[2], 0.0, -d[0]])


class PhysicsWorld:
    """Not: iç döngü saf Python float'larıyla yazıldı; 3 elemanlı NumPy dizilerinde
    işlem başına maliyet, hesabın kendisinden çok daha yüksektir."""

    def __init__(self, hoop: Hoop | None = None):
        self.hoop = hoop or Hoop()

    def step(self, ball: BallBody, dt: float) -> list[str]:
        """Topu ``dt`` saniye ilerletir. Olaylar: 'rim', 'board', 'floor', 'made'."""
        events: list[str] = []
        if ball.resting or dt <= 0:
            return events
        s = _State(ball)
        remaining = dt
        while remaining > 1e-12 and not s.resting:
            # Pota çevresinde ince, diğer yerlerde kaba adım
            near = (s.y > self.hoop.center[1] - 0.9
                    and abs(s.x - self.hoop.center[0]) < 1.4 and abs(s.z - self.hoop.center[2]) < 1.4)
            h = min(remaining, SUBSTEP if near else COARSE_STEP)
            self._substep(s, h, events)
            remaining -= h
        s.write_back(ball)
        ball.spin_angle -= 9.0 * dt * (0.2 if ball.touched_floor else 1.0)
        return events

    # ------------------------------------------------------------------
    def _substep(self, s: "_State", h: float, events: list[str]) -> None:
        hoop = self.hoop
        cx, cy, cz = hoop.center
        prev_y = s.y

        s.vy -= GRAVITY * h
        s.x += s.vx * h
        s.y += s.vy * h
        s.z += s.vz * h

        self._collide_rim(s, events)
        self._collide_board(s, events)

        rx, rz = s.x - cx, s.z - cz
        if (not s.made and not s.touched_floor and s.vy < 0 and prev_y >= cy > s.y
                and math.hypot(rx, rz) < hoop.rim_radius - 0.25 * s.r):
            s.made = True
            events.append("made")

        # File: içinden geçen topu yavaşlatıp merkeze çeker
        if s.made and cy - 0.45 < s.y < cy:
            s.in_net_time += h
            s.vx -= rx * 25.0 * h
            s.vz -= rz * 25.0 * h
            damp = 1.0 - 3.0 * h
            s.vx *= damp
            s.vy *= damp
            s.vz *= damp

        self._collide_floor(s, h, events)

    def _collide_rim(self, s: "_State", events: list[str]) -> None:
        hoop = self.hoop
        cx, cy, cz = hoop.center
        rx, rz = s.x - cx, s.z - cz
        hl = math.hypot(rx, rz)
        if hl < 1e-9:
            return  # tam merkezde: çembere uzak
        qx, qy, qz = cx + rx / hl * hoop.rim_radius, cy, cz + rz / hl * hoop.rim_radius
        nx, ny, nz = s.x - qx, s.y - qy, s.z - qz
        dist = math.sqrt(nx * nx + ny * ny + nz * nz)
        limit = s.r + hoop.tube_radius
        if dist >= limit or dist < 1e-9:
            return
        nx, ny, nz = nx / dist, ny / dist, nz / dist
        s.x, s.y, s.z = qx + nx * limit, qy + ny * limit, qz + nz * limit
        vn = s.vx * nx + s.vy * ny + s.vz * nz
        if vn < 0:
            # teğet bileşen biraz sürtünür, normal bileşen sekme katsayısıyla yansır
            tx, ty, tz = s.vx - vn * nx, s.vy - vn * ny, s.vz - vn * nz
            k = -RIM_RESTITUTION * vn
            s.vx, s.vy, s.vz = tx * 0.85 + k * nx, ty * 0.85 + k * ny, tz * 0.85 + k * nz
            if not s.touched_rim or abs(vn) > 0.6:
                events.append("rim")
            s.touched_rim = True

    def _collide_board(self, s: "_State", events: list[str]) -> None:
        hoop = self.hoop
        if not (abs(s.x - hoop.center[0]) <= hoop.board_half_width and hoop.board_bottom <= s.y <= hoop.board_top):
            return
        front = hoop.board_front_z
        back = front - hoop.board_thickness
        if s.z - s.r < front and s.z > back:
            s.z = front + s.r
            if s.vz < 0:
                s.vz = -s.vz * BOARD_RESTITUTION
                s.vx *= 0.9
                s.vy *= 0.9
                events.append("board")

    def _collide_floor(self, s: "_State", h: float, events: list[str]) -> None:
        if s.y - s.r >= 0.0:
            return
        s.y = s.r
        if s.vy < 0:
            impact = -s.vy
            s.vy = impact * FLOOR_RESTITUTION
            s.vx *= 0.92
            s.vz *= 0.92
            if impact > 0.8:
                events.append("floor")
            s.touched_floor = True
            if s.vy < 0.35:
                s.vy = 0.0
        if s.vy == 0.0:
            roll = math.exp(-ROLLING_FRICTION * h)
            s.vx *= roll
            s.vz *= roll
            if math.hypot(s.vx, s.vz) < 0.05:
                s.resting = True
                s.vx = s.vy = s.vz = 0.0


class _State:
    """BallBody'nin adım boyunca float olarak tutulan kopyası."""
    __slots__ = ("x", "y", "z", "vx", "vy", "vz", "r", "made", "touched_rim", "touched_floor",
                 "resting", "in_net_time")

    def __init__(self, b: BallBody):
        self.x, self.y, self.z = (float(c) for c in b.position)
        self.vx, self.vy, self.vz = (float(c) for c in b.velocity)
        self.r = b.radius
        self.made, self.touched_rim = b.made, b.touched_rim
        self.touched_floor, self.resting = b.touched_floor, b.resting
        self.in_net_time = b.in_net_time

    def write_back(self, b: BallBody) -> None:
        b.position[:] = (self.x, self.y, self.z)
        b.velocity[:] = (self.vx, self.vy, self.vz)
        b.made, b.touched_rim = self.made, self.touched_rim
        b.touched_floor, b.resting = self.touched_floor, self.resting
        b.in_net_time = self.in_net_time
