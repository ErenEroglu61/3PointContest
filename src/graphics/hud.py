"""2B arayüz katmanı: metin ve dikdörtgenler tek bir draw call ile çizilir."""
from pathlib import Path

import moderngl
import numpy as np

from src.graphics import font

SHADER_DIR = Path(__file__).parent / "shaders"


class HUD:
    def __init__(self, ctx: moderngl.Context):
        self.ctx = ctx
        self.program = ctx.program(
            vertex_shader=(SHADER_DIR / "hud.vert").read_text(encoding="utf-8"),
            fragment_shader=(SHADER_DIR / "hud.frag").read_text(encoding="utf-8"),
        )
        atlas = font.build_atlas()
        self.atlas_h, self.atlas_w = atlas.shape
        self.texture = ctx.texture((self.atlas_w, self.atlas_h), 1, atlas.tobytes())
        self.texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.capacity = 6 * 4096
        self.vbo = ctx.buffer(reserve=self.capacity * 8 * 4, dynamic=True)
        self.vao = ctx.vertex_array(self.program, [(self.vbo, "2f 2f 4f", "in_pos", "in_uv", "in_color")])
        self._verts: list[tuple] = []
        # dolu blok hücresinin ortası: düz renkli dikdörtgenler için
        bx, by = font.glyph_cell("\x7f")
        self._solid_uv = ((bx * font.CELL_W + 2.5) / self.atlas_w, (by * font.CELL_H + 3.5) / self.atlas_h)

    # ------------------------------------------------------------------
    def _quad(self, x0, y0, x1, y1, u0, v0, u1, v1, color) -> None:
        r, g, b, a = color if len(color) == 4 else (*color, 1.0)
        c = (r, g, b, a)
        self._verts += [
            (x0, y0, u0, v0, *c), (x1, y0, u1, v0, *c), (x1, y1, u1, v1, *c),
            (x0, y0, u0, v0, *c), (x1, y1, u1, v1, *c), (x0, y1, u0, v1, *c),
        ]

    def rect(self, x, y, w, h, color) -> None:
        u, v = self._solid_uv
        self._quad(x, y, x + w, y + h, u, v, u, v, color)

    def frame(self, x, y, w, h, color, t: float = 2) -> None:
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    @staticmethod
    def text_width(text: str, size: float = 3) -> float:
        return len(font.normalize_text(text)) * font.CELL_W * size - size

    def text(self, x, y, text: str, size: float = 3, color=(1, 1, 1, 1), align: str = "left",
             shadow: bool = True) -> None:
        text = font.normalize_text(text)
        if align != "left":
            w = self.text_width(text, size)
            x -= w if align == "right" else w / 2
        if shadow:
            self._text(x + size * 0.7, y + size * 0.7, text, size, (0, 0, 0, 0.55 * (color[3] if len(color) == 4 else 1)))
        self._text(x, y, text, size, color)

    def _text(self, x, y, text, size, color) -> None:
        for i, ch in enumerate(text):
            if ch == " ":
                continue
            cx, cy = font.glyph_cell(ch)
            u0 = cx * font.CELL_W / self.atlas_w
            v0 = cy * font.CELL_H / self.atlas_h
            u1 = (cx * font.CELL_W + font.GLYPH_W) / self.atlas_w
            v1 = (cy * font.CELL_H + font.GLYPH_H) / self.atlas_h
            gx = x + i * font.CELL_W * size
            self._quad(gx, y, gx + font.GLYPH_W * size, y + font.GLYPH_H * size, u0, v0, u1, v1, color)

    # ------------------------------------------------------------------
    def flush(self, screen_w: int, screen_h: int) -> None:
        if not self._verts:
            return
        data = np.array(self._verts, dtype="f4")
        self._verts.clear()
        if len(data) > self.capacity:
            data = data[: self.capacity]
        self.vbo.write(data.tobytes())
        self.program["u_screen"].value = (float(screen_w), float(screen_h))
        self.texture.use(location=0)
        self.program["u_font"].value = 0
        self.ctx.disable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.vao.render(moderngl.TRIANGLES, vertices=len(data))
        self.ctx.enable(moderngl.DEPTH_TEST)
