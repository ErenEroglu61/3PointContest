import moderngl
import numpy as np

from src.graphics.court import HALF_LENGTH

HOOP_HEIGHT = 3.05
HOOP_OFFSET_FROM_BASELINE = 1.575
RIM_RADIUS = 0.225
RIM_SEGMENTS = 32


class Hoop:
    def __init__(self, ctx, program, side: float = 1.0):
        self.center = np.array([side * (HALF_LENGTH - HOOP_OFFSET_FROM_BASELINE), HOOP_HEIGHT, 0.0])
        self.color = (1.0, 0.4, 0.1)
        self.mode = moderngl.TRIANGLE_FAN
        self.rim_vao = self._build_rim(ctx, program)

    def _build_rim(self, ctx: moderngl.Context, program: moderngl.Program):
        verts = [self.center.tolist()]
        for i in range(RIM_SEGMENTS + 1):
            angle = 2.0 * np.pi * i / RIM_SEGMENTS
            x = self.center[0] + RIM_RADIUS * np.cos(angle)
            z = self.center[2] + RIM_RADIUS * np.sin(angle)
            verts.append([x, self.center[1], z])
        data = np.array(verts, dtype="f4").tobytes()
        vbo = ctx.buffer(data)
        return ctx.vertex_array(program, [(vbo, "3f", "in_position")])