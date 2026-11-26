import numpy as np

from src.graphics.utils.math_utils import look_at, perspective


def test_look_at_puts_target_in_front_of_camera():
    # Kamera (0,0,5) noktasında, origine bakıyor.
    # Görüş uzayında origin, kameranın 5 birim önünde (-z yönünde) olmalı.
    view = look_at(
        eye=np.array([0.0, 0.0, 5.0]),
        target=np.array([0.0, 0.0, 0.0]),
        up=np.array([0.0, 1.0, 0.0]),
    )
    origin_in_view = view @ np.array([0.0, 0.0, 0.0, 1.0])
    assert np.allclose(origin_in_view[:3], [0.0, 0.0, -5.0])


def test_perspective_maps_near_plane_to_ndc_minus_one():
    near, far = 0.1, 100.0
    proj = perspective(fovy_deg=60.0, aspect=16 / 9, near=near, far=far)
    p = proj @ np.array([0.0, 0.0, -near, 1.0])
    ndc_z = p[2] / p[3]
    assert np.isclose(ndc_z, -1.0)


def test_perspective_maps_far_plane_to_ndc_plus_one():
    near, far = 0.1, 100.0
    proj = perspective(fovy_deg=60.0, aspect=16 / 9, near=near, far=far)
    p = proj @ np.array([0.0, 0.0, -far, 1.0])
    ndc_z = p[2] / p[3]
    assert np.isclose(ndc_z, 1.0)

from src.graphics.utils.math_utils import look_at, perspective


def test_look_at_puts_target_in_front_of_camera():
    # Kamera (0,0,5) noktasında, origine bakıyor.
    # Görüş uzayında origin, kameranın 5 birim önünde (-z yönünde) olmalı.
    view = look_at(
        eye=np.array([0.0, 0.0, 5.0]),
        target=np.array([0.0, 0.0, 0.0]),
        up=np.array([0.0, 1.0, 0.0]),
    )
    origin_in_view = view @ np.array([0.0, 0.0, 0.0, 1.0])
    assert np.allclose(origin_in_view[:3], [0.0, 0.0, -5.0])


def test_perspective_maps_near_plane_to_ndc_minus_one():
    near, far = 0.1, 100.0
    proj = perspective(fovy_deg=60.0, aspect=16 / 9, near=near, far=far)
    p = proj @ np.array([0.0, 0.0, -near, 1.0])
    ndc_z = p[2] / p[3]
    assert np.isclose(ndc_z, -1.0)


def test_perspective_maps_far_plane_to_ndc_plus_one():
    near, far = 0.1, 100.0
    proj = perspective(fovy_deg=60.0, aspect=16 / 9, near=near, far=far)
    p = proj @ np.array([0.0, 0.0, -far, 1.0])
    ndc_z = p[2] / p[3]
    assert np.isclose(ndc_z, 1.0)