"""Saha dokusu: prosedürel parke + çizgiler, boyalı alanlar ve "From the Logo" çıkartmaları.

Doku NumPy ile üretilir (harici görsel dosyası gerekmez). Satır 0 = yakın dip çizgi (v=0),
sütun 0 = sol yan çizgi (u=0).
"""
import math

import numpy as np

from src.game import layout

LINE_WIDTH = 0.05
LINE_COLOR = np.array([0.06, 0.09, 0.22])
KEY_COLOR = np.array([0.10, 0.20, 0.48])
DECAL_RED = np.array([0.80, 0.12, 0.16])
ORANGE = np.array([0.93, 0.47, 0.13])
WHITE = np.array([0.95, 0.95, 0.95])


def _blend(img: np.ndarray, mask: np.ndarray, color, alpha: float = 1.0) -> None:
    m = (mask.astype(np.float32) * alpha)[..., None]
    img *= (1.0 - m)
    img += m * np.asarray(color, dtype=np.float32)


def _ring(d: np.ndarray, radius: float, width: float = LINE_WIDTH) -> np.ndarray:
    return np.abs(d - radius) < width / 2


def _wood(X: np.ndarray, Z: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    plank_w = 0.075
    plank = np.floor((X + layout.HALF_WIDTH) / plank_w).astype(np.int32)
    n_planks = int(plank.max()) + 2
    stagger = rng.uniform(0, 3.0, n_planks).astype(np.float32)
    board = np.floor((Z + stagger[plank]) / 2.4).astype(np.int32)
    board_id = (plank * 7919 + board * 104729) % 4096
    tint = rng.uniform(-0.06, 0.06, 4096).astype(np.float32)[board_id]

    phase = rng.uniform(0, 2 * math.pi, n_planks).astype(np.float32)[plank]
    grain = (np.sin(Z * 23.0 + phase + 1.7 * np.sin(Z * 2.3 + phase)) * 0.025
             + np.sin(Z * 71.0 + phase * 3.0) * 0.012)
    base = np.array([0.82, 0.64, 0.44], dtype=np.float32)
    img = np.empty(X.shape + (3,), dtype=np.float32)
    shade = 1.0 + tint + grain
    for c in range(3):
        img[..., c] = base[c] * shade
    # plank aralarındaki ince çizgi
    seam = ((X + layout.HALF_WIDTH) % plank_w) < 0.004
    end_seam = ((Z + stagger[plank]) % 2.4) < 0.004
    _blend(img, seam | end_seam, (0.45, 0.32, 0.2), 0.35)
    return img


def _paint_end(img, X, D, along):
    """Bir potanın tarafını boyar. ``D``: potaya uzaklık (yatay), ``along``: potadan
    orta sahaya doğru mesafe (dip çizgi = -1.575)."""
    inside_court = along >= -layout.RIM_TO_BASELINE
    # Üçlük alanı hafif koyu (görseldeki gibi)
    in_arc = ((D < layout.THREE_POINT_RADIUS) | (along < layout.CORNER_THREE_END_Z)) & \
             (np.abs(X) < layout.CORNER_THREE_X) & inside_court
    _blend(img, in_arc, (0.55, 0.38, 0.24), 0.22)
    # Boyalı alan (key)
    key_len = layout.FREE_THROW_Z - layout.BASELINE_Z
    in_key = (np.abs(X) < layout.KEY_WIDTH / 2) & inside_court & (along < -layout.RIM_TO_BASELINE + key_len)
    _blend(img, in_key, KEY_COLOR, 0.75)

    lines = np.zeros(X.shape, dtype=bool)
    arc_part = along >= layout.CORNER_THREE_END_Z
    lines |= _ring(D, layout.THREE_POINT_RADIUS) & arc_part & inside_court
    corner = (np.abs(np.abs(X) - layout.CORNER_THREE_X) < LINE_WIDTH / 2) & inside_court & ~arc_part
    lines |= corner
    ft_along = -layout.RIM_TO_BASELINE + key_len
    key_edge = (np.abs(np.abs(X) - layout.KEY_WIDTH / 2) < LINE_WIDTH / 2) & inside_court & (along <= ft_along)
    key_top = (np.abs(along - ft_along) < LINE_WIDTH / 2) & (np.abs(X) <= layout.KEY_WIDTH / 2)
    lines |= key_edge | key_top
    ft_dist = np.sqrt(X ** 2 + (along - ft_along) ** 2)
    lines |= _ring(ft_dist, 1.83) & (along >= ft_along)
    dashed = _ring(ft_dist, 1.83) & (along < ft_along) & ((np.arctan2(X, along - ft_along) * 6) % 1.0 < 0.5)
    lines |= dashed
    lines |= _ring(D, 1.22) & (along >= 0) & inside_court          # restricted area
    _blend(img, lines, LINE_COLOR)


def _logo_decal(img, X, Z, cx, cz):
    d = np.sqrt((X - cx) ** 2 + (Z - cz) ** 2)
    _blend(img, d < 0.55, DECAL_RED, 0.92)
    _blend(img, _ring(d, 0.42, 0.05), WHITE)
    _blend(img, d < 0.18, WHITE)


def _center_logo(img, X, Z):
    cz = layout.MIDCOURT_Z
    d = np.sqrt(X ** 2 + (Z - cz) ** 2)
    _blend(img, d < 1.55, (0.07, 0.12, 0.30), 0.95)
    _blend(img, _ring(d, 1.38, 0.06), WHITE)
    ball = d < 0.9
    _blend(img, ball, ORANGE)
    seams = (np.abs(X) < 0.025) | (np.abs(Z - cz) < 0.025) | _ring(np.sqrt((X - 1.15) ** 2 + (Z - cz) ** 2), 0.95, 0.05) \
        | _ring(np.sqrt((X + 1.15) ** 2 + (Z - cz) ** 2), 0.95, 0.05)
    _blend(img, ball & seams, (0.1, 0.05, 0.02))
    # Kırmızı-beyaz-mavi şerit
    stripe = (np.abs(Z - cz) < 0.18) & (np.abs(X) > 1.0) & (np.abs(X) < 1.35)
    _blend(img, stripe & (X < 0), DECAL_RED)
    _blend(img, stripe & (X > 0), (0.12, 0.3, 0.85))


def generate_court_texture(width: int = 1024, seed: int = 7) -> np.ndarray:
    """(H, W, 3) uint8 saha dokusu. Yükseklik saha oranına göre hesaplanır."""
    height = int(round(width * layout.COURT_LENGTH / layout.COURT_WIDTH))
    rng = np.random.default_rng(seed)
    xs = (np.arange(width, dtype=np.float32) + 0.5) / width * layout.COURT_WIDTH - layout.HALF_WIDTH
    zs = (np.arange(height, dtype=np.float32) + 0.5) / height * layout.COURT_LENGTH + layout.BASELINE_Z
    X, Z = np.meshgrid(xs, zs)

    img = _wood(X, Z, rng)

    # Yakın pota (z=0) ve uzak pota
    _paint_end(img, X, np.sqrt(X ** 2 + Z ** 2), Z)
    far_along = layout.FAR_RIM_Z - Z
    _paint_end(img, X, np.sqrt(X ** 2 + far_along ** 2), far_along)

    # Orta saha çizgisi, orta yuvarlak, logo
    _center_logo(img, X, Z)
    mid = (np.abs(Z - layout.MIDCOURT_Z) < LINE_WIDTH / 2)
    center_ring = _ring(np.sqrt(X ** 2 + (Z - layout.MIDCOURT_Z) ** 2), layout.CENTER_CIRCLE_RADIUS)
    _blend(img, mid | center_ring, LINE_COLOR)

    # "From the Logo" çıkartmaları
    for name in ("logo_left", "logo_right"):
        cx, cz = layout.SPOT_POSITIONS[name]
        _logo_decal(img, X, Z, cx, cz)

    # Saha sınır çizgileri (sahanın içinde)
    border = ((np.abs(X) > layout.HALF_WIDTH - LINE_WIDTH)
              | (Z < layout.BASELINE_Z + LINE_WIDTH)
              | (Z > layout.FAR_BASELINE_Z - LINE_WIDTH))
    _blend(img, border, LINE_COLOR)

    return (np.clip(img, 0.0, 1.0) * 255).astype(np.uint8)
