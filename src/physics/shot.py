"""Atış hesabı: güç barı ve hedefe giden atış hızının çözümü."""
import math
import random

import numpy as np

from src.physics.ball_physics import GRAVITY

LAUNCH_ANGLE_DEG = 52.0
SWEET_SPOT = 0.80           # güç barında ideal bırakma noktası
POWER_SENSITIVITY = 0.09    # bar hatası -> hız çarpanı
AIM_SENSITIVITY_DEG = 3.0   # bar hatası -> yanal sapma
RANDOM_AIM_SD_DEG = 0.25    # her atışta küçük rastgele sapma
AIM_DEPTH = 0.07            # çember merkezinin bu kadar arkasına nişan al (ön çembere çarpmasın)


def launch_velocity(start, target, angle_deg: float = LAUNCH_ANGLE_DEG) -> np.ndarray:
    """``start`` noktasından ``angle_deg`` açıyla atılan topun ``target``'tan geçmesi
    için gereken hız vektörü (hava direnci ihmal edilir).

    v² = g d² / (2 cos²θ (d tanθ - h))
    """
    start = np.asarray(start, dtype=float)
    target = np.asarray(target, dtype=float)
    delta = target - start
    horizontal = np.array([delta[0], 0.0, delta[2]])
    d = float(np.linalg.norm(horizontal))
    if d < 1e-6:
        raise ValueError("hedef tam üstte")
    h = float(delta[1])
    theta = math.radians(angle_deg)
    denom = 2.0 * math.cos(theta) ** 2 * (d * math.tan(theta) - h)
    if denom <= 0:
        raise ValueError("bu açıyla hedefe ulaşılamaz")
    speed = math.sqrt(GRAVITY * d * d / denom)
    direction = horizontal / d
    return direction * speed * math.cos(theta) + np.array([0.0, speed * math.sin(theta), 0.0])


def rotate_y(v: np.ndarray, angle_rad: float) -> np.ndarray:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([c * v[0] + s * v[2], v[1], -s * v[0] + c * v[2]])


def shot_velocity(start, target, meter_value: float, rng: random.Random | None = None) -> np.ndarray:
    """Güç barı değerine göre hatalı/isabetli atış hızı üretir."""
    start = np.asarray(start, dtype=float)
    target = np.asarray(target, dtype=float)
    horizontal = np.array([target[0] - start[0], 0.0, target[2] - start[2]])
    target = target + horizontal / (np.linalg.norm(horizontal) or 1.0) * AIM_DEPTH
    base = launch_velocity(start, target)
    error = meter_value - SWEET_SPOT
    speed_scale = 1.0 + error * POWER_SENSITIVITY
    aim = math.radians(error * AIM_SENSITIVITY_DEG)
    if rng is not None:
        aim += math.radians(rng.gauss(0.0, RANDOM_AIM_SD_DEG))
    return rotate_y(base * speed_scale, aim)


class PowerMeter:
    """Basılı tutuldukça 0→1→0 gidip gelen güç barı."""

    def __init__(self, period: float = 2.0):
        self.period = period
        self.charging = False
        self.phase = 0.0

    def start(self) -> None:
        self.charging = True
        self.phase = 0.0

    def cancel(self) -> None:
        self.charging = False
        self.phase = 0.0

    def update(self, dt: float) -> None:
        if self.charging:
            self.phase = (self.phase + dt / self.period) % 1.0

    @property
    def value(self) -> float:
        if not self.charging:
            return 0.0
        return 1.0 - abs(1.0 - 2.0 * self.phase)

    def release(self) -> float:
        v = self.value
        self.charging = False
        self.phase = 0.0
        return v
