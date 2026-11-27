"""Kamera: view/projection matrisleri ve üç kamera modu (oyuncu, yayın, serbest)."""
import math
from enum import Enum

import numpy as np

from src.game import layout
from src.graphics.utils.math_utils import look_at, normalize, perspective

RIM = np.array([0.0, layout.RIM_HEIGHT, 0.0])


class CameraMode(Enum):
    SHOOTER = "OYUNCU"
    BROADCAST = "YAYIN"
    FREE = "SERBEST"


class Camera:
    def __init__(self, fov: float = 60.0, near: float = 0.05, far: float = 200.0):
        self.eye = np.array([0.0, 6.0, 16.0])
        self.target = RIM.copy()
        self.fov = fov
        self.near = near
        self.far = far

    def view(self) -> np.ndarray:
        return look_at(self.eye, self.target)

    def projection(self, aspect: float) -> np.ndarray:
        return perspective(self.fov, aspect, self.near, self.far)


class CameraRig:
    """Kamerayı seçili moda göre yumuşakça hedef konuma taşır."""

    def __init__(self, camera: Camera | None = None):
        self.camera = camera or Camera()
        self.mode = CameraMode.SHOOTER
        self.yaw = math.pi          # serbest kamera: -z'ye bakış
        self.pitch = -0.15
        self.free_eye = np.array([0.0, 4.0, 14.0])
        self.smoothing = 6.0

    def cycle(self) -> CameraMode:
        modes = list(CameraMode)
        self.mode = modes[(modes.index(self.mode) + 1) % len(modes)]
        if self.mode is CameraMode.FREE:
            self.free_eye = self.camera.eye.copy()
            d = normalize(self.camera.target - self.camera.eye)
            self.yaw = math.atan2(d[0], d[2])
            self.pitch = math.asin(max(-1.0, min(1.0, d[1])))
        return self.mode

    # --- serbest kamera kontrolü ----------------------------------------
    def free_forward(self) -> np.ndarray:
        cp = math.cos(self.pitch)
        return np.array([math.sin(self.yaw) * cp, math.sin(self.pitch), math.cos(self.yaw) * cp])

    def rotate(self, dx: float, dy: float) -> None:
        self.yaw -= dx * 0.004
        self.pitch = max(-1.4, min(1.4, self.pitch - dy * 0.004))

    def move(self, forward: float, right: float, up: float, dt: float, speed: float = 8.0) -> None:
        f = self.free_forward()
        r = normalize(np.cross(f, [0.0, 1.0, 0.0]))
        self.free_eye += (f * forward + r * right + np.array([0.0, up, 0.0])) * speed * dt
        self.free_eye[1] = max(0.3, self.free_eye[1])

    def zoom(self, amount: float) -> None:
        self.camera.fov = max(25.0, min(90.0, self.camera.fov - amount * 3.0))

    # ------------------------------------------------------------------
    def desired(self, player_xz: tuple[float, float], focus=None) -> tuple[np.ndarray, np.ndarray]:
        px, pz = player_xz
        if self.mode is CameraMode.SHOOTER:
            n = math.hypot(px, pz) or 1.0
            ox, oz = px / n, pz / n
            eye = np.array([px + ox * 1.6, layout.EYE_HEIGHT + 0.35, pz + oz * 1.6])
            target = RIM + np.array([0.0, -0.45, 0.0])
            return eye, target
        if self.mode is CameraMode.BROADCAST:
            # Oyuncunun arkasından, hafif yandan ve yüksekten: hem oyuncu hem pota kadrajda
            n = math.hypot(px, pz) or 1.0
            ox, oz = px / n, pz / n
            side_x, side_z = oz, -ox
            eye = np.array([px + ox * 6.5 + side_x * 3.0, 5.2, pz + oz * 6.5 + side_z * 3.0])
            target = np.array([px * 0.45, 1.9, pz * 0.45])
            if focus is not None:
                target = target * 0.75 + np.asarray(focus) * 0.25
            return eye, target
        return self.free_eye.copy(), self.free_eye + self.free_forward()

    def update(self, dt: float, player_xz: tuple[float, float], focus=None, snap: bool = False) -> None:
        eye, target = self.desired(player_xz, focus)
        if self.mode is CameraMode.FREE or snap:
            self.camera.eye, self.camera.target = eye, target
            return
        k = 1.0 - math.exp(-self.smoothing * dt)
        self.camera.eye = self.camera.eye + (eye - self.camera.eye) * k
        self.camera.target = self.camera.target + (target - self.camera.target) * k
