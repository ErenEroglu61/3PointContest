from dataclasses import dataclass,field
from typing import Callable

class FakeClock:
    def __init__(self):
        self.now = 0.0

    def advance(self,seconds:float):
        self.now += seconds

    def __call__(self) -> float:
        return self.now

@dataclass
class Timer:
    duration: float
    clock: Callable[[], float]
    started_at: float = field(init=False)

    def __post_init__(self):
        self.started_at = self.clock()

    def expired(self) -> bool:
        return self.clock() - self.started_at >= self.duration