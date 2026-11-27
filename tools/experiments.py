"""README'deki "Deneyler" bölümünün sayılarını üretir.

    python -m tools.experiments
"""
import random
import statistics

import numpy as np

from src.contest.ai import AI_ROSTER, simulate_round
from src.contest.locations import COMPETITION_ORDER
from src.game import layout
from src.game.round import GameRound
from src.physics.ball_physics import BallBody, PhysicsWorld
from src.physics.shot import SWEET_SPOT, shot_velocity


def make_rate_by_meter(trials: int = 200) -> None:
    """Deney 1: güç barı hatasına göre isabet oranı (her noktadan)."""
    world = PhysicsWorld()
    rng = random.Random(0)
    errors = [0.0, 0.02, 0.04, 0.06, 0.08, 0.10]
    print("| Nokta | " + " | ".join(f"±{e:.2f}" for e in errors) + " |")
    print("|---" * (len(errors) + 1) + "|")
    for spot in COMPETITION_ORDER:
        x, z = layout.SPOT_POSITIONS[spot.name]
        ox, oz = layout.outward(spot.name)
        start = np.array([x - ox * 0.3, layout.RELEASE_HEIGHT, z - oz * 0.3])
        row = []
        for e in errors:
            made = 0
            for i in range(trials):
                meter = SWEET_SPOT + (e if i % 2 else -e)
                ball = BallBody(start, shot_velocity(start, world.hoop.center, meter, rng))
                for _ in range(300):
                    world.step(ball, 1 / 60)
                    if ball.made or ball.touched_floor:
                        break
                made += ball.made
            row.append(f"%{100 * made / trials:.0f}")
        print(f"| {spot.name} | " + " | ".join(row) + " |")


def ai_score_distribution(rounds: int = 2000) -> None:
    """Deney 2: yapay zekâ rakiplerin 70 sn'lik skor dağılımı."""
    print("| Oyuncu | Ort. | Std | Min | Max |")
    print("|---|---|---|---|---|")
    for name, profile in AI_ROSTER:
        rng = random.Random(1)
        scores = [simulate_round(profile, 70, rng).score for _ in range(rounds)]
        print(f"| {name} | {statistics.mean(scores):.1f} | {statistics.pstdev(scores):.1f} "
              f"| {min(scores)} | {max(scores)} |")


def perfect_round_time() -> None:
    """Deney 3: kusursuz oynayan botun 27 topu bitirme süresi."""
    r = GameRound("corner_right", countdown=0, rng=random.Random(0))
    t = 0.0
    while not r.done:
        if r.can_shoot and not r.meter.charging:
            r.press()
        if r.meter.charging and r.meter.phase < 0.5 and r.meter.value >= SWEET_SPOT:
            r.release()
        r.update(1 / 60)
        t += 1 / 60
    print(f"Kusursuz bot: {r.score} puan, 27 top {r.timer.elapsed:.1f} sn'de bitti")


if __name__ == "__main__":
    print("## Deney 1: güç barı hatası -> isabet\n")
    make_rate_by_meter()
    print("\n## Deney 2: yapay zekâ skor dağılımı\n")
    ai_score_distribution()
    print("\n## Deney 3\n")
    perfect_round_time()
