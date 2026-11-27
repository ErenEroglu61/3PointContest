"""Prosedürel ses efektleri (NumPy ile üretilir, ses dosyası gerekmez).

Windows'ta ``winsound`` ile çalınır; diğer sistemlerde sessizce devre dışı kalır.
"""
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

RATE = 22050


def _envelope(n: int, attack: float, decay: float) -> np.ndarray:
    t = np.arange(n) / RATE
    env = np.exp(-t / decay)
    a = max(1, int(attack * RATE))
    env[:a] *= np.linspace(0, 1, a)
    return env


def _noise(n: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).uniform(-1, 1, n)


def _lowpass(x: np.ndarray, alpha: float) -> np.ndarray:
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def synth(name: str) -> np.ndarray:
    """Ses örneklerini -1..1 aralığında üretir."""
    if name == "swish":
        n = int(0.42 * RATE)
        x = _noise(n, 1)
        x = x - _lowpass(x, 0.08)            # yüksek geçiren: "şşş" sesi
        return x * _envelope(n, 0.05, 0.12) * 0.7
    if name == "rim":
        n = int(0.4 * RATE)
        t = np.arange(n) / RATE
        x = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((620, 0.6), (1480, 0.4), (2950, 0.25)))
        return x * _envelope(n, 0.001, 0.07) * 0.6
    if name == "board":
        n = int(0.25 * RATE)
        t = np.arange(n) / RATE
        x = np.sin(2 * np.pi * 140 * t) * 0.7 + _lowpass(_noise(n, 2), 0.2) * 0.6
        return x * _envelope(n, 0.001, 0.05) * 0.8
    if name == "bounce":
        n = int(0.2 * RATE)
        t = np.arange(n) / RATE
        freq = 110 - 40 * t / t[-1]
        return np.sin(2 * np.pi * np.cumsum(freq) / RATE) * _envelope(n, 0.002, 0.05) * 0.9
    if name == "buzzer":
        n = int(1.0 * RATE)
        t = np.arange(n) / RATE
        x = np.sign(np.sin(2 * np.pi * 180 * t)) * 0.5 + np.sin(2 * np.pi * 360 * t) * 0.3
        env = np.ones(n)
        env[-2000:] = np.linspace(1, 0, 2000)
        return x * env * 0.45
    if name == "tick":
        n = int(0.12 * RATE)
        t = np.arange(n) / RATE
        return np.sin(2 * np.pi * 880 * t) * _envelope(n, 0.002, 0.04) * 0.6
    if name == "go":
        n = int(0.45 * RATE)
        t = np.arange(n) / RATE
        return (np.sin(2 * np.pi * 1320 * t) * 0.5 + np.sin(2 * np.pi * 660 * t) * 0.3) * _envelope(n, 0.005, 0.2)
    if name == "money":
        n = int(0.6 * RATE)
        t = np.arange(n) / RATE
        x = sum(np.sin(2 * np.pi * f * t) * (t > d) for f, d in ((1047, 0.0), (1319, 0.08), (1568, 0.16)))
        swish = np.zeros(n)
        s = synth("swish")
        swish[:len(s)] = s
        return x * _envelope(n, 0.005, 0.25) * 0.35 + swish * 0.6
    raise KeyError(name)


SOUND_NAMES = ("swish", "rim", "board", "bounce", "buzzer", "tick", "go", "money")


def write_wav(path: Path, samples: np.ndarray) -> None:
    data = (np.clip(samples, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())


class SoundBank:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and sys.platform == "win32"
        self._files: dict[str, Path] = {}
        if not self.enabled:
            return
        try:
            import winsound  # noqa: F401
            folder = Path(tempfile.mkdtemp(prefix="3pc_sfx_"))
            for name in SOUND_NAMES:
                path = folder / f"{name}.wav"
                write_wav(path, synth(name))
                self._files[name] = path
        except Exception:
            self.enabled = False

    def play(self, name: str) -> None:
        if not self.enabled or name not in self._files:
            return
        import winsound
        winsound.PlaySound(str(self._files[name]), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
