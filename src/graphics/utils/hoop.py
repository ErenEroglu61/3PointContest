"""Pota, rack, pedestal ve tribün parçalarının geometri + yerleşim tanımları.

Burada yalnızca NumPy verisi üretilir; GPU'ya yükleme renderer'da yapılır.
"""
import math
from dataclasses import dataclass, field

import numpy as np

from src.game import layout
from src.graphics import mesh as geo
from src.graphics.utils.math_utils import rotate_y, scale, translate

MAT_COLOR, MAT_TEXTURE, MAT_BALL, MAT_MONEY, MAT_BLUE_MONEY, MAT_UNLIT = range(6)

RIM_ORANGE = (0.95, 0.35, 0.05)
RACK_FRAME = (0.08, 0.08, 0.10)
MONEY_RACK_FRAME = (0.75, 0.10, 0.12)
RACK_TOP = 0.78
PEDESTAL_HEIGHT = 0.95
RACK_SLOT_SPACING = 0.28


@dataclass
class PartSpec:
    geometry: tuple[np.ndarray, np.ndarray]
    model: np.ndarray
    color: tuple[float, float, float]
    material: int = MAT_COLOR
    shininess: float = 24.0
    specular: float = 0.25
    cast_shadow: bool = True
    tag: str = ""
    extra: dict = field(default_factory=dict)


def hoop_parts(far: bool = False) -> list[PartSpec]:
    """Yakın potaya göre (çember merkezi orijin üstünde) parçalar; ``far`` ise ters çevrilir."""
    root = translate(0, 0, layout.FAR_RIM_Z) @ rotate_y(math.pi) if far else np.eye(4)
    r = layout.RIM_HEIGHT
    board_w = layout.BACKBOARD_HALF_WIDTH * 2
    board_h = layout.BACKBOARD_TOP - layout.BACKBOARD_BOTTOM
    board_cz = layout.BACKBOARD_FRONT_Z - layout.BACKBOARD_THICKNESS / 2
    board_cy = (layout.BACKBOARD_TOP + layout.BACKBOARD_BOTTOM) / 2
    front = layout.BACKBOARD_FRONT_Z + 0.002
    parts = [
        # Panya: cam (açık gri-mavi), siyah çerçeve, beyaz şut karesi
        PartSpec(geo.box(board_w, board_h, layout.BACKBOARD_THICKNESS),
                 translate(0, board_cy, board_cz), (0.78, 0.84, 0.90), shininess=80, specular=0.6),
        PartSpec(geo.box(0.61, 0.02, 0.006), translate(0, r + 0.45, front), (0.97, 0.97, 0.97)),
        PartSpec(geo.box(0.61, 0.02, 0.006), translate(0, r + 0.01, front), (0.97, 0.97, 0.97)),
        PartSpec(geo.box(0.02, 0.45, 0.006), translate(-0.295, r + 0.23, front), (0.97, 0.97, 0.97)),
        PartSpec(geo.box(0.02, 0.45, 0.006), translate(0.295, r + 0.23, front), (0.97, 0.97, 0.97)),
        PartSpec(geo.box(board_w, 0.05, 0.006), translate(0, layout.BACKBOARD_TOP - 0.025, front), (0.1, 0.1, 0.1)),
        PartSpec(geo.box(board_w, 0.05, 0.006), translate(0, layout.BACKBOARD_BOTTOM + 0.025, front), (0.1, 0.1, 0.1)),
        PartSpec(geo.box(0.05, board_h, 0.006), translate(-board_w / 2 + 0.025, board_cy, front), (0.1, 0.1, 0.1)),
        PartSpec(geo.box(0.05, board_h, 0.006), translate(board_w / 2 - 0.025, board_cy, front), (0.1, 0.1, 0.1)),
        # Çember ve bağlantı parçası
        PartSpec(geo.torus(layout.RIM_RADIUS, layout.RIM_TUBE * 1.6), translate(0, r, 0), RIM_ORANGE,
                 shininess=48, specular=0.5, tag="rim"),
        PartSpec(geo.box(0.12, 0.04, 0.16), translate(0, r - 0.02, layout.BACKBOARD_FRONT_Z + 0.07), RIM_ORANGE),
        # Destek: kollu direk ve pedli taban (dip çizginin arkasında)
        PartSpec(geo.box(0.25, 0.25, 1.65), translate(0, board_cy, layout.BACKBOARD_FRONT_Z - 0.9),
                 (0.12, 0.13, 0.16)),
        PartSpec(geo.box(0.3, 3.65, 0.3), translate(0, 1.82 + 0.1, -2.1), (0.12, 0.13, 0.16)),
        PartSpec(geo.box(1.3, 1.0, 1.9), translate(0, 0.5, -3.0), (0.12, 0.18, 0.42)),
        PartSpec(geo.box(1.0, 1.8, 0.5), translate(0, 0.9, -1.95), (0.12, 0.18, 0.42)),
    ]
    for p in parts:
        p.model = root @ p.model
    return parts


def net_model(far: bool = False) -> np.ndarray:
    root = translate(0, 0, layout.FAR_RIM_Z) @ rotate_y(math.pi) if far else np.eye(4)
    return root @ translate(0, layout.RIM_HEIGHT, 0)


def rack_transform(spot: str) -> np.ndarray:
    x, z = layout.rack_position(spot)
    return translate(x, 0, z) @ rotate_y(layout.facing_angle(spot))


def rack_parts(spot: str, all_money: bool) -> list[PartSpec]:
    t = rack_transform(spot)
    frame = MONEY_RACK_FRAME if all_money else RACK_FRAME
    parts = [
        PartSpec(geo.box(1.5, 0.05, 0.34), t @ translate(0, RACK_TOP, 0), frame, tag="rack"),
        PartSpec(geo.box(1.5, 0.06, 0.03), t @ translate(0, RACK_TOP + 0.05, 0.16), frame),
        PartSpec(geo.box(1.5, 0.06, 0.03), t @ translate(0, RACK_TOP + 0.05, -0.16), frame),
    ]
    for lx in (-0.7, 0.7):
        for lz in (-0.14, 0.14):
            parts.append(PartSpec(geo.box(0.04, RACK_TOP, 0.04), t @ translate(lx, RACK_TOP / 2, lz), (0.2, 0.2, 0.22)))
    return parts


def pedestal_parts(spot: str) -> list[PartSpec]:
    t = rack_transform(spot)
    return [
        PartSpec(geo.cylinder(0.24, 0.06), t, (0.1, 0.1, 0.12)),
        PartSpec(geo.cylinder(0.08, PEDESTAL_HEIGHT - 0.06), t @ translate(0, 0.06, 0), (0.85, 0.85, 0.88),
                 shininess=60, specular=0.5),
        PartSpec(geo.cylinder(0.16, 0.05), t @ translate(0, PEDESTAL_HEIGHT - 0.05, 0), (0.12, 0.3, 0.85)),
    ]


def ball_slot_position(spot: str, slot: int, pedestal: bool) -> np.ndarray:
    """Rack/pedestal üzerindeki top yuvasının dünya konumu."""
    t = rack_transform(spot)
    if pedestal:
        local = np.array([0.0, PEDESTAL_HEIGHT + layout.BALL_RADIUS - 0.02, 0.0, 1.0])
    else:
        local = np.array([(slot - 2) * RACK_SLOT_SPACING, RACK_TOP + 0.025 + layout.BALL_RADIUS, 0.0, 1.0])
    return (t @ local)[:3]


def stands_parts() -> list[PartSpec]:
    """Saha çevresinde basamaklı tribünler ve reklam panoları."""
    parts = []
    hw = layout.HALF_WIDTH
    length = layout.COURT_LENGTH + 8
    cz = layout.MIDCOURT_Z
    for side in (-1, 1):
        for tier in range(6):
            depth = 1.2
            x = side * (hw + 3.2 + tier * depth + depth / 2)
            h = 0.6 + tier * 0.55
            shade = 0.10 + 0.025 * (tier % 2)
            parts.append(PartSpec(geo.box(depth, h, length), translate(x, h / 2, cz),
                                  (shade, shade * 1.1, shade * 1.6), specular=0.05, cast_shadow=False))
        # saha kenarı reklam panosu
        parts.append(PartSpec(geo.box(0.12, 0.9, layout.COURT_LENGTH), translate(side * (hw + 2.0), 0.45, cz),
                              (0.08, 0.14, 0.45), specular=0.4, cast_shadow=False))
    for tier in range(5):
        depth = 1.2
        z = layout.BASELINE_Z - 5.0 - tier * depth - depth / 2
        h = 0.6 + tier * 0.55
        parts.append(PartSpec(geo.box(2 * hw + 16, h, depth), translate(0, h / 2, z),
                              (0.10, 0.11, 0.17), specular=0.05, cast_shadow=False))
    return parts


def ball_model(position, rotation: np.ndarray | None = None) -> np.ndarray:
    m = translate(*position)
    if rotation is not None:
        m = m @ rotation
    return m @ scale(1.0)
