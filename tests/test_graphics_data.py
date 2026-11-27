"""Grafik katmanının GPU gerektirmeyen kısımları: matrisler, geometri, doku ve font."""
import math

import numpy as np
import pytest

from src.game import layout
from src.graphics import font
from src.graphics import mesh as geo
from src.graphics.court import generate_court_texture
from src.graphics.utils.math_utils import (look_at, orthographic, perspective, rotate_axis, rotate_y,
                                           translate)


def test_look_at_moves_target_onto_negative_z_axis():
    view = look_at([3.0, 2.0, 5.0], [0.0, 1.0, 0.0])
    p = view @ np.array([0.0, 1.0, 0.0, 1.0])
    assert p[0] == pytest.approx(0, abs=1e-9) and p[1] == pytest.approx(0, abs=1e-9)
    assert p[2] < 0


def test_perspective_maps_near_and_far_planes():
    proj = perspective(60, 16 / 9, 0.1, 100)
    near = proj @ np.array([0, 0, -0.1, 1])
    far = proj @ np.array([0, 0, -100, 1])
    assert near[2] / near[3] == pytest.approx(-1)
    assert far[2] / far[3] == pytest.approx(1)


def test_orthographic_maps_box_to_unit_cube():
    m = orthographic(-2, 2, -1, 1, 1, 10)
    assert (m @ np.array([2, 1, -10, 1]))[:3] == pytest.approx([1, 1, 1])


def test_rotate_axis_matches_rotate_y():
    a = 0.7
    assert np.allclose(rotate_axis([0, 1, 0], a), rotate_y(a))


def test_translate():
    assert (translate(1, 2, 3) @ np.array([0, 0, 0, 1]))[:3] == pytest.approx([1, 2, 3])


@pytest.mark.parametrize("builder", [lambda: geo.box(1, 2, 3), lambda: geo.sphere(1, 12, 6),
                                     lambda: geo.cylinder(1, 2, 10), lambda: geo.torus(1, 0.1, 16, 6),
                                     lambda: geo.plane(2, 3)])
def test_mesh_builders_produce_valid_indices(builder):
    verts, idx = builder()
    assert verts.shape[1] == 8
    assert len(idx) % 3 == 0
    assert idx.max() < len(verts)
    normals = verts[:, 3:6]
    assert np.allclose(np.linalg.norm(normals, axis=1), 1.0, atol=1e-5)


def test_sphere_vertices_on_radius():
    verts, _ = geo.sphere(0.12, 16, 8)
    assert np.allclose(np.linalg.norm(verts[:, :3], axis=1), 0.12, atol=1e-6)


def test_net_sway_changes_shape():
    assert not np.allclose(geo.net_lines(0.23), geo.net_lines(0.23, sway=1.0))


def test_court_texture_shape_and_lines():
    tex = generate_court_texture(256)
    h, w, c = tex.shape
    assert (w, c) == (256, 3)
    assert h == round(256 * layout.COURT_LENGTH / layout.COURT_WIDTH)
    assert tex.dtype == np.uint8


def test_three_point_distances():
    # köşe çizgisi ile yayın birleştiği yer yay üzerinde olmalı
    assert math.hypot(layout.CORNER_THREE_X, layout.CORNER_THREE_END_Z) == pytest.approx(layout.THREE_POINT_RADIUS)
    for name, (x, z) in layout.SPOT_POSITIONS.items():
        d = math.hypot(x, z)
        assert d > layout.CORNER_THREE_X, name            # tüm atışlar üçlük çizgisinin dışından
    logo = math.hypot(*layout.SPOT_POSITIONS["logo_left"])
    assert logo >= layout.THREE_POINT_RADIUS + layout.LOGO_DISTANCE_BEHIND_LINE


def test_font_atlas_and_turkish_text():
    atlas = font.build_atlas()
    assert atlas.shape == (6 * font.CELL_H, 16 * font.CELL_W)
    assert font.normalize_text("Şampiyon güç") == "SAMPIYON GUC"
    cx, cy = font.glyph_cell("A")
    assert atlas[cy * font.CELL_H:(cy + 1) * font.CELL_H, cx * font.CELL_W:(cx + 1) * font.CELL_W].any()
