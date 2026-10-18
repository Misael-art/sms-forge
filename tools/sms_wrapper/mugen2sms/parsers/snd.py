"""Parser de .snd v1: container de WAVs indexados por (grupo, amostra)."""
from __future__ import annotations

import io
import struct
import wave
from dataclasses import dataclass

SIG = b"ElecbyteSnd\0"


class SndError(ValueError):
    pass


@dataclass
class Sound:
    group: int
    sample: int
    wav: bytes          # arquivo WAV original, intacto
    channels: int
    rate: int
    width: int          # bytes por amostra
    frames: int
    error: str | None = None

    @property
    def seconds(self) -> float:
        return self.frames / self.rate if self.rate else 0.0


def parse(data: bytes) -> tuple[list[Sound], list[str]]:
    if not data.startswith(SIG):
        raise SndError("assinatura ElecbyteSnd ausente")
    n, first = struct.unpack_from("<II", data, 16)
    sounds, warnings, pos = [], [], first
    for i in range(n):
        if pos + 16 > len(data):
            warnings.append(f"som {i}: subheader fora do arquivo")
            break
        nxt, length, grp, smp = struct.unpack_from("<IIII", data, pos)
        blob = data[pos + 16 : pos + 16 + length]
        s = Sound(grp, smp, blob, 0, 0, 0, 0)
        try:
            with wave.open(io.BytesIO(blob)) as w:
                s.channels, s.rate, s.width, s.frames = (
                    w.getnchannels(), w.getframerate(), w.getsampwidth(), w.getnframes())
        except (wave.Error, EOFError, struct.error) as e:
            s.error = f"WAV invalido: {e}"
            warnings.append(f"som {grp},{smp}: {s.error}")
        sounds.append(s)
        if nxt == 0 or nxt <= pos:
            break
        pos = nxt
    return sounds, warnings
