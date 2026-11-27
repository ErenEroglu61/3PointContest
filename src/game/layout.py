"""Saha ölçüleri ve atış noktalarının dünya koordinatları (metre, y yukarı).

Koordinat sistemi: pota çemberinin merkezi (0, 3.048, 0). Yakın dip çizgi z = -1.575,
saha +z yönünde orta sahaya doğru uzanır. Potaya bakan oyuncunun solu -x tarafıdır.
"""
import math

COURT_LENGTH = 28.65
COURT_WIDTH = 15.24
HALF_WIDTH = COURT_WIDTH / 2
RIM_TO_BASELINE = 1.575
BASELINE_Z = -RIM_TO_BASELINE
FAR_BASELINE_Z = BASELINE_Z + COURT_LENGTH
MIDCOURT_Z = BASELINE_Z + COURT_LENGTH / 2
FAR_RIM_Z = FAR_BASELINE_Z - RIM_TO_BASELINE

RIM_HEIGHT = 3.048
RIM_RADIUS = 0.2286
RIM_TUBE = 0.009
BALL_RADIUS = 0.119

BACKBOARD_FRONT_Z = -0.38
BACKBOARD_THICKNESS = 0.05
BACKBOARD_HALF_WIDTH = 0.915
BACKBOARD_BOTTOM = 2.90
BACKBOARD_TOP = 3.97

THREE_POINT_RADIUS = 7.24
CORNER_THREE_X = 6.706
CORNER_THREE_END_Z = math.sqrt(THREE_POINT_RADIUS ** 2 - CORNER_THREE_X ** 2)
LOGO_DISTANCE_BEHIND_LINE = 1.83  # 6 feet

KEY_WIDTH = 4.88
FREE_THROW_Z = BASELINE_Z + 5.79
CENTER_CIRCLE_RADIUS = 1.83

RELEASE_HEIGHT = 2.35
EYE_HEIGHT = 1.85


def _polar(radius: float, angle_deg: float) -> tuple[float, float]:
    """Açı, potanın tam karşısı (+z) 0°, oyuncunun soluna (-x) doğru negatif."""
    a = math.radians(angle_deg)
    return (radius * math.sin(a), radius * math.cos(a))


SHOOT_RADIUS = THREE_POINT_RADIUS + 0.35
LOGO_RADIUS = THREE_POINT_RADIUS + LOGO_DISTANCE_BEHIND_LINE + 0.2

# Oyuncunun ayak bastığı nokta (x, z)
SPOT_POSITIONS: dict[str, tuple[float, float]] = {
    "corner_left": (-(CORNER_THREE_X + 0.3), 0.35),
    "wing_left": _polar(SHOOT_RADIUS, -45),
    "logo_left": _polar(LOGO_RADIUS, -22.5),
    "center": _polar(SHOOT_RADIUS, 0),
    "logo_right": _polar(LOGO_RADIUS, 22.5),
    "wing_right": _polar(SHOOT_RADIUS, 45),
    "corner_right": (CORNER_THREE_X + 0.3, 0.35),
}


def outward(spot: str) -> tuple[float, float]:
    """Potadan noktaya doğru yatay birim vektör."""
    x, z = SPOT_POSITIONS[spot]
    length = math.hypot(x, z)
    return (x / length, z / length)


def left_of(spot: str) -> tuple[float, float]:
    """Potaya bakan oyuncunun soluna doğru yatay birim vektör."""
    ox, oz = outward(spot)
    return (-oz, ox)


def rack_position(spot: str) -> tuple[float, float]:
    """Rack/pedestal oyuncunun sol yanına, biraz geriye yerleştirilir."""
    x, z = SPOT_POSITIONS[spot]
    ox, oz = outward(spot)
    lx, lz = left_of(spot)
    return (x + lx * 0.85 + ox * 0.25, z + lz * 0.85 + oz * 0.25)


def facing_angle(spot: str) -> float:
    """Rack'in y ekseni etrafındaki dönüşü (radyan): uzun kenarı çembere teğet."""
    ox, oz = outward(spot)
    return math.atan2(ox, oz)
