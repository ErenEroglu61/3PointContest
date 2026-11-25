from dataclasses import dataclass
from enum import Enum

class SpotKind(Enum):
    RACK = "rack"
    PEDESTAL = "pedestal"

@dataclass(frozen=True)
class Spot:
    name: str
    kind: SpotKind

MAIN_LOCATIONS: tuple[Spot, ...] = (
    Spot("corner_left", SpotKind.RACK),
    Spot("wing_left", SpotKind.RACK),
    Spot("center", SpotKind.RACK),
    Spot("wing_right", SpotKind.RACK),
    Spot("corner_right", SpotKind.RACK)
)

FROM_THE_LOGO: tuple[Spot, ...] = (
    Spot("logo_left", SpotKind.PEDESTAL),
    Spot("logo_right", SpotKind.PEDESTAL)
)