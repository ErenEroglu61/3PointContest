import moderngl
import numpy as np

HALF_LENGTH = 14.325
HALF_WIDTH = 7.62


class Court:
    def __init__(self, ctx: moderngl.Context, program: moderngl.Program):
        vertices = np.array([
            -HALF_LENGTH, 0.0, -HALF_WIDTH,
             HALF_LENGTH, 0.0, -HALF_WIDTH,
             HALF_LENGTH, 0.0,  HALF_WIDTH,

            -HALF_LENGTH, 0.0, -HALF_WIDTH,
             HALF_LENGTH, 0.0,  HALF_WIDTH,
            -HALF_LENGTH, 0.0,  HALF_WIDTH,
        ], dtype="f4")

        self.vbo = ctx.buffer(vertices.tobytes())
        self.vao = ctx.vertex_array(program, [(self.vbo, "3f", "in_position")])
        self.color = (0.80, 0.55, 0.30)