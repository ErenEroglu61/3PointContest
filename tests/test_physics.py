import numpy as np
import pytest

from src.game import layout
from src.physics.ball_physics import GRAVITY, BallBody, PhysicsWorld
from src.physics.shot import SWEET_SPOT, PowerMeter, launch_velocity, shot_velocity


def release_point(spot):
    x, z = layout.SPOT_POSITIONS[spot]
    ox, oz = layout.outward(spot)
    return np.array([x - ox * 0.3, layout.RELEASE_HEIGHT, z - oz * 0.3])


def fly(start, velocity, seconds=5.0):
    world = PhysicsWorld()
    ball = BallBody(start, velocity)
    events = []
    for _ in range(int(seconds * 60)):
        events += world.step(ball, 1 / 60)
        if ball.resting:
            break
    return ball, events


def test_launch_velocity_passes_through_target_analytically():
    start = np.array([0.0, 2.0, 7.0])
    target = np.array([0.0, 3.05, 0.0])
    v = launch_velocity(start, target, 50)
    t = 7.0 / -v[2]                         # hedefin yatay mesafesine varış süresi
    y = start[1] + v[1] * t - 0.5 * GRAVITY * t * t
    assert y == pytest.approx(target[1], abs=1e-9)


def test_unreachable_angle_raises():
    with pytest.raises(ValueError):
        launch_velocity([0, 0, 5], [0, 10, 0], 20)


@pytest.mark.parametrize("spot", list(layout.SPOT_POSITIONS))
def test_perfect_release_is_made_from_every_spot(spot):
    start = release_point(spot)
    ball, events = fly(start, shot_velocity(start, PhysicsWorld().hoop.center, SWEET_SPOT))
    assert ball.made
    assert "made" in events


@pytest.mark.parametrize("meter", [0.3, 1.0])
def test_bad_release_misses(meter):
    start = release_point("center")
    ball, _ = fly(start, shot_velocity(start, PhysicsWorld().hoop.center, meter))
    assert not ball.made


def test_ball_bounces_on_floor_and_comes_to_rest():
    ball, events = fly([0.0, 2.0, 5.0], [0.0, 0.0, 0.5], seconds=10)
    assert "floor" in events
    assert ball.resting
    assert ball.position[1] == pytest.approx(layout.BALL_RADIUS)


def test_backboard_reflects_ball():
    ball, events = fly([0.0, 3.8, 1.0], [0.0, 0.0, -6.0], seconds=0.25)
    assert "board" in events
    assert ball.velocity[2] > 0


def test_rim_collision_pushes_ball_out():
    world = PhysicsWorld()
    # top çemberin ön kenarına tam üstten düşüyor
    ball = BallBody([0.0, layout.RIM_HEIGHT + 0.5, layout.RIM_RADIUS], [0.0, 0.0, 0.0])
    events = []
    for _ in range(60):
        events += world.step(ball, 1 / 60)
    assert "rim" in events
    assert ball.touched_rim


def test_power_meter_ping_pongs():
    m = PowerMeter(period=2.0)
    m.start()
    m.update(0.5)
    assert m.value == pytest.approx(0.5)
    m.update(0.5)
    assert m.value == pytest.approx(1.0)
    m.update(0.5)
    assert m.value == pytest.approx(0.5)
    assert m.release() == pytest.approx(0.5)
    assert not m.charging and m.value == 0.0
