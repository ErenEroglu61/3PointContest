import numpy as np

from src.graphics.court import HALF_LENGTH
from src.graphics.hoop import HOOP_OFFSET_FROM_BASELINE

BASKET = np.array([HALF_LENGTH - HOOP_OFFSET_FROM_BASELINE,0.0,0.0])
ARC_RADIUS = 7.24
LOGO_EXTRA_DISTANCE = 1.83
CORNER_DISTANCE_X = 6.70
CORNER_Z = 6.9

def _on_arc(angle_dec: float, radius: float) -> np.ndarray:
    a = np.radians(angle_dec)
    return BASKET + np.array([-radius * np.cos(a), 0.0, radius * np.sin(a)])

MAIN_POSITIONS = {
    "corner_left": np.array([BASKET[0] - CORNER_DISTANCE_X, 0.0, -CORNER_Z]),
    "wing_left": _on_arc(-45.0, ARC_RADIUS),
    "top": _on_arc(0.0,ARC_RADIUS),
    "wing_right": _on_arc(45.0, ARC_RADIUS),
    "corner_right": np.array([BASKET[0] - CORNER_DISTANCE_X, 0.0, CORNER_Z])
}

LOGO_RADIUS = ARC_RADIUS + LOGO_EXTRA_DISTANCE
FROM_THE_LOGO_POSITIONS = {
    "logo_left": _on_arc(-22.5, LOGO_RADIUS),
    "logo_right": _on_arc(22.5,LOGO_RADIUS)
}