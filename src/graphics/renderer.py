from pathlib import Path

import moderngl
import numpy as np

from src.graphics.utils.math_utils import look_at, perspective

SHADER_DIR = Path(__file__).parent / "shaders"


class Renderer:
    def __init__(self, ctx: moderngl.Context, width: int, height: int):
        self.ctx = ctx
        self.program = ctx.program(
            vertex_shader=(SHADER_DIR / "basic.vert").read_text(encoding="utf-8"),
            fragment_shader=(SHADER_DIR / "basic.frag").read_text(encoding="utf-8"),
        )
        self.ctx.enable(moderngl.DEPTH_TEST)

        view = look_at(
            eye=np.array([0.0, 10.0, 16.0]),
            target=np.zeros(3),
            up=np.array([0.0, 1.0, 0.0]),
        )
        projection = perspective(
            fovy_deg=45.0, aspect=width / height, near=0.1, far=200.0
        )


        self.program["view"].write(view.T.astype("f4").tobytes())
        self.program["projection"].write(projection.T.astype("f4").tobytes())
        self.program["model"].write(np.identity(4, dtype="f4").T.tobytes())

    def begin_frame(self) -> None:
        self.ctx.clear(0.1, 0.1, 0.12, depth=1.0)

    def draw(self, vao: moderngl.VertexArray, color: tuple[float, float, float]) -> None:
        self.program["color"].value = color
        vao.render(moderngl.TRIANGLES)