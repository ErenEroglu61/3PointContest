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

# Yarışma sırası: pedestallar, tepe (center) rack'in iki yanında,
# center ile wing arasında yer alır (kural dokümanı s.1).
COMPETITION_ORDER: tuple[Spot, ...] = (
    MAIN_LOCATIONS[0],   # corner_left
    MAIN_LOCATIONS[1],   # wing_left
    FROM_THE_LOGO[0],    # logo_left
    MAIN_LOCATIONS[2],   # center
    FROM_THE_LOGO[1],    # logo_right
    MAIN_LOCATIONS[3],   # wing_right
    MAIN_LOCATIONS[4],   # corner_right
)

# Ekranda gösterilecek kısa etiketler
SPOT_LABELS: dict[str, str] = {
    "corner_left": "SOL KOSE",
    "wing_left": "SOL KANAT",
    "logo_left": "SOL LOGO",
    "center": "TEPE",
    "logo_right": "SAG LOGO",
    "wing_right": "SAG KANAT",
    "corner_right": "SAG KOSE",
}


def spot_by_name(name: str) -> Spot:
    for spot in COMPETITION_ORDER:
        if spot.name == name:
            return spot
    raise KeyError(name)
