"""Bağımlılıksız PNG yazıcı (ekran görüntüsü için)."""
import struct
import zlib
from pathlib import Path

import numpy as np


def save_png(path: Path | str, rgb: np.ndarray, flip: bool = True) -> Path:
    """``rgb``: (H, W, 3) uint8. OpenGL'den okunan görüntü alttan üste olduğu için
    varsayılan olarak dikey çevrilir."""
    img = np.ascontiguousarray(rgb[::-1] if flip else rgb, dtype=np.uint8)
    h, w, _ = img.shape
    raw = b"".join(b"\x00" + img[y].tobytes() for y in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)
    return path
