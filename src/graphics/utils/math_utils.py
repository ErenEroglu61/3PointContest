"""4x4 matris yardımcıları.

Matrisler NumPy'de satır-öncelikli tutulur ve sütun vektörlerle çarpılır (M @ v).
GLSL sütun-öncelikli beklediği için shader'a gönderirken ``to_gl`` ile transpoz alınır.
"""
import math

import numpy as np


def to_gl(m: np.ndarray) -> bytes:
    return np.ascontiguousarray(m.T, dtype="f4").tobytes()


def identity() -> np.ndarray:
    return np.eye(4)


def translate(x: float, y: float, z: float) -> np.ndarray:
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def scale(x: float, y: float | None = None, z: float | None = None) -> np.ndarray:
    y = x if y is None else y
    z = x if z is None else z
    return np.diag([x, y, z, 1.0])


def rotate_x(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]], dtype=float)


def rotate_y(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]], dtype=float)


def rotate_z(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=float)


def rotate_axis(axis, a: float) -> np.ndarray:
    """Rodrigues formülü ile keyfi eksen etrafında dönüş."""
    x, y, z = normalize(np.asarray(axis, dtype=float))
    c, s, t = math.cos(a), math.sin(a), 1 - math.cos(a)
    return np.array([
        [t * x * x + c, t * x * y - s * z, t * x * z + s * y, 0],
        [t * x * y + s * z, t * y * y + c, t * y * z - s * x, 0],
        [t * x * z - s * y, t * y * z + s * x, t * z * z + c, 0],
        [0, 0, 0, 1],
    ])


def normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def perspective(fov_y_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fov_y_deg) / 2)
    return np.array([
        [f / aspect, 0, 0, 0],
        [0, f, 0, 0],
        [0, 0, (far + near) / (near - far), 2 * far * near / (near - far)],
        [0, 0, -1, 0],
    ])


def orthographic(left, right, bottom, top, near, far) -> np.ndarray:
    return np.array([
        [2 / (right - left), 0, 0, -(right + left) / (right - left)],
        [0, 2 / (top - bottom), 0, -(top + bottom) / (top - bottom)],
        [0, 0, -2 / (far - near), -(far + near) / (far - near)],
        [0, 0, 0, 1],
    ])


def look_at(eye, target, up=(0.0, 1.0, 0.0)) -> np.ndarray:
    eye = np.asarray(eye, dtype=float)
    f = normalize(np.asarray(target, dtype=float) - eye)
    s = normalize(np.cross(f, np.asarray(up, dtype=float)))
    u = np.cross(s, f)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3] = s, u, -f
    m[:3, 3] = (-s @ eye, -u @ eye, f @ eye)
    return m


def lerp(a, b, t):
    return a + (b - a) * t
