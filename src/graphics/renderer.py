"""Çizim döngüsü: gölge haritası geçişi + sahne geçişi.

Sahne: dokulu saha, iki pota, rack'ler, pedestallar, tribünler, toplar ve animasyonlu file.
"""
import math
from pathlib import Path

import moderngl
import numpy as np

from src.contest.locations import COMPETITION_ORDER, SpotKind
from src.game import layout
from src.graphics import mesh as geo
from src.graphics.ball_object import MATERIAL_FOR, BallDraw
from src.graphics.court import generate_court_texture
from src.graphics.mesh import Mesh
from src.graphics.utils import hoop
from src.graphics.utils.hoop import MAT_COLOR, MAT_TEXTURE, MAT_UNLIT, PartSpec
from src.graphics.utils.math_utils import look_at, normalize, orthographic, rotate_y, to_gl, translate

SHADER_DIR = Path(__file__).parent / "shaders"
CLEAR_COLOR = (0.03, 0.04, 0.08)
JERSEY = (0.85, 0.15, 0.18)


def _load_program(ctx, name: str):
    return ctx.program(
        vertex_shader=(SHADER_DIR / f"{name}.vert").read_text(encoding="utf-8"),
        fragment_shader=(SHADER_DIR / f"{name}.frag").read_text(encoding="utf-8"),
    )


class Renderer:
    def __init__(self, ctx: moderngl.Context, shadow_size: int = 2048, court_texture_width: int = 1536):
        self.ctx = ctx
        self.scene = _load_program(ctx, "basic")
        self.depth = _load_program(ctx, "depth")

        # Gölge haritası (derinlik dokusu, donanım karşılaştırmalı)
        self.shadow_size = shadow_size
        self.shadow_tex = ctx.depth_texture((shadow_size, shadow_size))
        self.shadow_tex.compare_func = "<="
        self.shadow_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.shadow_fbo = ctx.framebuffer(depth_attachment=self.shadow_tex)

        # Saha dokusu
        court = generate_court_texture(court_texture_width)
        h, w, _ = court.shape
        self.court_tex = ctx.texture((w, h), 3, np.ascontiguousarray(court).tobytes())
        self.court_tex.build_mipmaps()
        self.court_tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        self.court_tex.anisotropy = 8.0
        self.court_tex.repeat_x = self.court_tex.repeat_y = False

        self.floor = Mesh(ctx, *geo.plane(layout.COURT_WIDTH, layout.COURT_LENGTH))
        self.floor_model = translate(0, 0, layout.MIDCOURT_Z)
        self.apron = Mesh(ctx, *geo.plane(70, 80))
        self.apron_model = translate(0, -0.005, layout.MIDCOURT_Z)
        self.ball_mesh = Mesh(ctx, *geo.sphere(layout.BALL_RADIUS, 32, 20))
        self.ring_mesh = Mesh(ctx, *geo.cylinder(0.55, 0.01, 40))

        # Statik parçalar
        self.static_parts = [self._upload(p) for p in hoop.hoop_parts() + hoop.hoop_parts(far=True)
                             + hoop.stands_parts()]
        self.rack_parts: dict[tuple[str, bool], list] = {}
        for spot in COMPETITION_ORDER:
            if spot.kind is SpotKind.PEDESTAL:
                self.rack_parts[(spot.name, False)] = [self._upload(p) for p in hoop.pedestal_parts(spot.name)]
            else:
                for money in (False, True):
                    self.rack_parts[(spot.name, money)] = [self._upload(p) for p in hoop.rack_parts(spot.name, money)]

        # Oyuncu figürü (basit manken)
        self.player_parts = [
            (Mesh(ctx, *geo.box(0.16, 0.85, 0.2)), translate(-0.11, 0.425, 0), (0.15, 0.15, 0.18)),
            (Mesh(ctx, *geo.box(0.16, 0.85, 0.2)), translate(0.11, 0.425, 0), (0.15, 0.15, 0.18)),
            (Mesh(ctx, *geo.cylinder(0.2, 0.7, 20)), translate(0, 0.85, 0), JERSEY),
            (Mesh(ctx, *geo.sphere(0.12, 20, 12)), translate(0, 1.72, 0), (0.55, 0.38, 0.28)),
            (Mesh(ctx, *geo.box(0.1, 0.55, 0.1)), translate(-0.25, 1.55, 0.12), (0.55, 0.38, 0.28)),
            (Mesh(ctx, *geo.box(0.1, 0.55, 0.1)), translate(0.25, 1.55, 0.12), (0.55, 0.38, 0.28)),
        ]

        # File: yakın pota dinamik (sallanma animasyonu), uzak pota statik
        self.net_near = Mesh(ctx, geo.net_lines(layout.RIM_RADIUS), mode=moderngl.LINES, dynamic=True)
        self.net_far = Mesh(ctx, geo.net_lines(layout.RIM_RADIUS), mode=moderngl.LINES)

        # Işık: arena tavanından eğik gelen yönlü ışık
        self.light_dir = normalize(np.array([0.35, 1.0, 0.45]))
        center = np.array([0.0, 0.0, 6.0])
        light_view = look_at(center + self.light_dir * 40.0, center, up=(0.0, 0.0, -1.0))
        self.light_vp = orthographic(-19, 19, -19, 19, 1.0, 90.0) @ light_view

    # ------------------------------------------------------------------
    def _upload(self, spec: PartSpec):
        mesh = Mesh(self.ctx, *spec.geometry)
        return mesh, spec

    @staticmethod
    def _set(program, name: str, value) -> None:
        if name in program:
            program[name].value = value

    def _draw(self, mesh: Mesh, model: np.ndarray, color=(1, 1, 1), material: int = MAT_COLOR,
              shininess: float = 24.0, specular: float = 0.25, emissive: float = 0.0, alpha: float = 1.0,
              receive_shadow: bool = True) -> None:
        p = self.scene
        p["u_model"].write(to_gl(model))
        self._set(p, "u_color", tuple(color))
        self._set(p, "u_material", material)
        self._set(p, "u_shininess", float(shininess))
        self._set(p, "u_specular", float(specular))
        self._set(p, "u_emissive", float(emissive))
        self._set(p, "u_alpha", float(alpha))
        self._set(p, "u_receive_shadow", receive_shadow)
        mesh.render(p)

    def _draw_depth(self, mesh: Mesh, model: np.ndarray) -> None:
        self.depth["u_model"].write(to_gl(model))
        mesh.render(self.depth)

    # ------------------------------------------------------------------
    def _casters(self, balls, money_rack, player):
        for mesh, spec in self.static_parts:
            if spec.cast_shadow:
                yield mesh, spec.model
        for key, parts in self.rack_parts.items():
            spot, money = key
            if self._rack_variant_visible(spot, money, money_rack):
                for mesh, spec in parts:
                    yield mesh, spec.model
        for b in balls:
            yield self.ball_mesh, translate(*b.position) @ b.rotation
        if player is not None:
            base = self._player_base(player)
            for mesh, local, _ in self.player_parts:
                yield mesh, base @ local

    @staticmethod
    def _rack_variant_visible(spot: str, money: bool, money_rack: str | None) -> bool:
        if spot.startswith("logo"):
            return True
        return money == (spot == money_rack)

    @staticmethod
    def _player_base(player) -> np.ndarray:
        (x, z), (fx, fz) = player
        return translate(x, 0, z) @ rotate_y(math.atan2(fx, fz))

    def render(self, fbo, size: tuple[int, int], camera, balls: list[BallDraw], money_rack: str | None,
               time: float, net_sway: float = 0.0, highlight=None, player=None) -> None:
        """``player``: ((x, z), (yön_x, yön_z)) ya da None. ``highlight``: (x, z) işaret halkası."""
        ctx = self.ctx
        ctx.enable(moderngl.DEPTH_TEST)
        ctx.disable(moderngl.CULL_FACE)
        ctx.disable(moderngl.BLEND)

        # 1) Gölge geçişi
        self.shadow_fbo.use()
        ctx.viewport = (0, 0, self.shadow_size, self.shadow_size)
        self.shadow_fbo.clear(depth=1.0)
        self.depth["u_light_vp"].write(to_gl(self.light_vp))
        for mesh, model in self._casters(balls, money_rack, player):
            self._draw_depth(mesh, model)

        # 2) Sahne geçişi
        fbo.use()
        w, h = size
        ctx.viewport = (0, 0, w, h)
        fbo.clear(*CLEAR_COLOR, 1.0, depth=1.0)
        p = self.scene
        p["u_view"].write(to_gl(camera.view()))
        p["u_proj"].write(to_gl(camera.projection(w / max(1, h))))
        p["u_light_vp"].write(to_gl(self.light_vp))
        self._set(p, "u_light_dir", tuple(self.light_dir))
        self._set(p, "u_camera_pos", tuple(camera.eye))
        self._set(p, "u_time", float(time))
        self.court_tex.use(location=0)
        self.shadow_tex.use(location=1)
        self._set(p, "u_texture", 0)
        self._set(p, "u_shadow_map", 1)

        self._draw(self.apron, self.apron_model, (0.05, 0.08, 0.18), specular=0.1)
        self._draw(self.floor, self.floor_model, material=MAT_TEXTURE, shininess=40, specular=0.35)

        for mesh, spec in self.static_parts:
            self._draw(mesh, spec.model, spec.color, spec.material, spec.shininess, spec.specular)
        for (spot, money), parts in self.rack_parts.items():
            if self._rack_variant_visible(spot, money, money_rack):
                for mesh, spec in parts:
                    self._draw(mesh, spec.model, spec.color, spec.material, spec.shininess, spec.specular)

        if player is not None:
            base = self._player_base(player)
            for mesh, local, color in self.player_parts:
                self._draw(mesh, base @ local, color, specular=0.1)

        for b in balls:
            emissive = 0.55 if MATERIAL_FOR[b.ball_type] == hoop.MAT_BLUE_MONEY and not b.dim else 0.0
            color = (0.35, 0.35, 0.35) if b.dim else (1, 1, 1)
            self._draw(self.ball_mesh, translate(*b.position) @ b.rotation, color,
                       MATERIAL_FOR[b.ball_type], shininess=20, specular=0.18, emissive=emissive)

        # 3) Saydam / ışıksız öğeler
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        if highlight is not None:
            pulse = 0.45 + 0.25 * math.sin(time * 6.0)
            self._draw(self.ring_mesh, translate(highlight[0], 0.01, highlight[1]), (1.0, 0.85, 0.2),
                       MAT_UNLIT, alpha=pulse)
        self.net_near.write(geo.net_lines(layout.RIM_RADIUS, sway=net_sway))
        self._draw(self.net_near, hoop.net_model(), (0.95, 0.95, 0.95), MAT_UNLIT, alpha=0.9)
        self._draw(self.net_far, hoop.net_model(far=True), (0.95, 0.95, 0.95), MAT_UNLIT, alpha=0.9)
        ctx.disable(moderngl.BLEND)
