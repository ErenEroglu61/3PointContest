"""Yarışma süreleri: 70 sn tur, 30 sn ilk tur tiebreaker'ı, 70 sn final tiebreaker'ı."""
import math

ROUND_SECONDS = 70.0
FIRST_ROUND_TIEBREAKER_SECONDS = 30.0
CHAMPIONSHIP_TIEBREAKER_SECONDS = 70.0


class ContestTimer:
    def __init__(self, duration: float = ROUND_SECONDS):
        if duration <= 0:
            raise ValueError("süre pozitif olmalı")
        self.duration = float(duration)
        self.elapsed = 0.0
        self.running = False

    def start(self) -> None:
        self.running = True

    def pause(self) -> None:
        self.running = False

    def reset(self) -> None:
        self.elapsed = 0.0
        self.running = False

    def update(self, dt: float) -> bool:
        """Süreyi ilerletir. Süre tam bu adımda dolduysa True döner (buzzer)."""
        if not self.running or self.expired:
            return False
        self.elapsed = min(self.duration, self.elapsed + max(0.0, dt))
        if self.expired:
            self.running = False
            return True
        return False

    @property
    def remaining(self) -> float:
        return max(0.0, self.duration - self.elapsed)

    @property
    def expired(self) -> bool:
        return self.elapsed >= self.duration


def format_clock(seconds: float) -> str:
    """70.0 -> '1:10', 9.42 -> '0:09.4' (son 10 saniyede ondalık gösterilir)."""
    seconds = max(0.0, seconds)
    if seconds < 10.0:
        return f"0:{seconds:04.1f}"
    whole = math.ceil(seconds)  # saat yukarı yuvarlanır: 69.2 -> 1:10
    return f"{whole // 60}:{whole % 60:02d}"
