"""Geometri üreticileri (saf NumPy) ve VBO/VAO sarmalayıcısı.

Her vertex: konum (3f), normal (3f), uv (2f) -> 8 float.
"""
import math

import numpy as np

VERTEX_ATTRS = (("in_position", 3), ("in_normal", 3), ("in_uv", 2))


def _pack(positions, normals, uvs) -> np.ndarray:
    return np.hstack([positions, normals, uvs]).astype("f4")


def box(sx: float, sy: float, sz: float) -> tuple[np.ndarray, np.ndarray]:
    """Merkezi orijinde, kenarları sx, sy, sz olan kutu."""
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    faces = [
        ((1, 0, 0), [(hx, -hy, hz), (hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz)]),
        ((-1, 0, 0), [(-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz)]),
        ((0, 1, 0), [(-hx, hy, hz), (hx, hy, hz), (hx, hy, -hz), (-hx, hy, -hz)]),
        ((0, -1, 0), [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz)]),
        ((0, 0, 1), [(-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]),
        ((0, 0, -1), [(hx, -hy, -hz), (-hx, -hy, -hz), (-hx, hy, -hz), (hx, hy, -hz)]),
    ]
    pos, nrm, uv, idx = [], [], [], []
    for normal, corners in faces:
        base = len(pos)
        pos += corners
        nrm += [normal] * 4
        uv += [(0, 0), (1, 0), (1, 1), (0, 1)]
        idx += [base, base + 1, base + 2, base, base + 2, base + 3]
    return _pack(np.array(pos), np.array(nrm), np.array(uv)), np.array(idx, dtype="u4")


def plane(width: float, depth: float, u_repeat: float = 1.0, v_repeat: float = 1.0):
    """XZ düzleminde, yukarı bakan dikdörtgen. uv: x -> u, z -> v."""
    hw, hd = width / 2, depth / 2
    pos = np.array([(-hw, 0, -hd), (hw, 0, -hd), (hw, 0, hd), (-hw, 0, hd)], dtype=float)
    nrm = np.tile([0.0, 1.0, 0.0], (4, 1))
    uv = np.array([(0, 0), (u_repeat, 0), (u_repeat, v_repeat), (0, v_repeat)], dtype=float)
    return _pack(pos, nrm, uv), np.array([0, 2, 1, 0, 3, 2], dtype="u4")


def sphere(radius: float, segments: int = 32, rings: int = 16):
    pos, nrm, uv = [], [], []
    for r in range(rings + 1):
        phi = math.pi * r / rings
        for s in range(segments + 1):
            theta = 2 * math.pi * s / segments
            n = (math.sin(phi) * math.cos(theta), math.cos(phi), math.sin(phi) * math.sin(theta))
            nrm.append(n)
            pos.append(tuple(radius * c for c in n))
            uv.append((s / segments, r / rings))
    idx = []
    row = segments + 1
    for r in range(rings):
        for s in range(segments):
            a, b = r * row + s, (r + 1) * row + s
            idx += [a, a + 1, b, a + 1, b + 1, b]
    return _pack(np.array(pos), np.array(nrm), np.array(uv)), np.array(idx, dtype="u4")


def cylinder(radius: float, height: float, segments: int = 24, caps: bool = True):
    """Tabanı y=0'da, y ekseni boyunca uzanan silindir."""
    pos, nrm, uv, idx = [], [], [], []
    for s in range(segments + 1):
        t = 2 * math.pi * s / segments
        c, sn = math.cos(t), math.sin(t)
        pos += [(radius * c, 0, radius * sn), (radius * c, height, radius * sn)]
        nrm += [(c, 0, sn), (c, 0, sn)]
        uv += [(s / segments, 0), (s / segments, 1)]
    for s in range(segments):
        a = 2 * s
        idx += [a, a + 1, a + 2, a + 1, a + 3, a + 2]
    if caps:
        for y, ny in ((0.0, -1.0), (height, 1.0)):
            center = len(pos)
            pos.append((0, y, 0)); nrm.append((0, ny, 0)); uv.append((0.5, 0.5))
            for s in range(segments + 1):
                t = 2 * math.pi * s / segments
                pos.append((radius * math.cos(t), y, radius * math.sin(t)))
                nrm.append((0, ny, 0))
                uv.append((0.5 + 0.5 * math.cos(t), 0.5 + 0.5 * math.sin(t)))
            for s in range(segments):
                idx += [center, center + 1 + s, center + 2 + s]
    return _pack(np.array(pos), np.array(nrm), np.array(uv)), np.array(idx, dtype="u4")


def torus(major: float, minor: float, major_segments: int = 48, minor_segments: int = 12):
    """XZ düzleminde yatan simit (pota çemberi)."""
    pos, nrm, uv = [], [], []
    for i in range(major_segments + 1):
        u = 2 * math.pi * i / major_segments
        cu, su = math.cos(u), math.sin(u)
        for j in range(minor_segments + 1):
            v = 2 * math.pi * j / minor_segments
            cv, sv = math.cos(v), math.sin(v)
            n = (cv * cu, sv, cv * su)
            pos.append(((major + minor * cv) * cu, minor * sv, (major + minor * cv) * su))
            nrm.append(n)
            uv.append((i / major_segments, j / minor_segments))
    idx = []
    row = minor_segments + 1
    for i in range(major_segments):
        for j in range(minor_segments):
            a, b = i * row + j, (i + 1) * row + j
            idx += [a, b, a + 1, a + 1, b, b + 1]
    return _pack(np.array(pos), np.array(nrm), np.array(uv)), np.array(idx, dtype="u4")


def net_lines(rim_radius: float, depth: float = 0.42, strings: int = 12, rows: int = 4,
              bottom_ratio: float = 0.6, sway: float = 0.0) -> np.ndarray:
    """Pota filesi: elmas desenli çizgi parçaları (GL_LINES). ``sway`` sayı animasyonu."""
    pts = []
    for r in range(rows + 1):
        t = r / rows
        radius = rim_radius * (1 - (1 - bottom_ratio) * t) * (1 - 0.25 * sway * math.sin(math.pi * t))
        y = -depth * t * (1 + 0.35 * sway)
        offset = (r % 2) * 0.5
        ring = []
        for s in range(strings):
            a = 2 * math.pi * (s + offset) / strings
            ring.append((radius * math.cos(a), y, radius * math.sin(a)))
        pts.append(ring)
    lines = []
    for r in range(rows):
        for s in range(strings):
            a = pts[r][s]
            if r % 2 == 0:
                b1, b2 = pts[r + 1][s], pts[r + 1][(s - 1) % strings]
            else:
                b1, b2 = pts[r + 1][s], pts[r + 1][(s + 1) % strings]
            lines += [a, b1, a, b2]
    pos = np.array(lines, dtype=float)
    nrm = np.tile([0.0, 1.0, 0.0], (len(pos), 1))
    uv = np.zeros((len(pos), 2))
    return _pack(pos, nrm, uv)


class Mesh:
    """Vertex/index verisini GPU'ya yükler ve program başına VAO önbellekler."""

    def __init__(self, ctx, vertices: np.ndarray, indices: np.ndarray | None = None,
                 mode=None, dynamic: bool = False):
        import moderngl
        self.ctx = ctx
        self.mode = moderngl.TRIANGLES if mode is None else mode
        self.vbo = ctx.buffer(np.ascontiguousarray(vertices, dtype="f4").tobytes(), dynamic=dynamic)
        self.ibo = ctx.buffer(np.ascontiguousarray(indices, dtype="u4").tobytes()) if indices is not None else None
        self._vaos = {}

    def write(self, vertices: np.ndarray) -> None:
        self.vbo.write(np.ascontiguousarray(vertices, dtype="f4").tobytes())

    def vao(self, program):
        key = program.glo
        if key not in self._vaos:
            fmt, names = [], []
            for name, size in VERTEX_ATTRS:
                if name in program:
                    fmt.append(f"{size}f")
                    names.append(name)
                else:
                    fmt.append(f"{size}x4")  # programın kullanmadığı alanı atla
            content = [(self.vbo, " ".join(fmt), *names)]
            self._vaos[key] = self.ctx.vertex_array(program, content, self.ibo, index_element_size=4)
        return self._vaos[key]

    def render(self, program) -> None:
        self.vao(program).render(self.mode)
