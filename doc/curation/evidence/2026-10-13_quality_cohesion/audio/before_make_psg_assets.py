#!/usr/bin/env python3
"""Gera pequenos streams PSGlib nativos para arena_nocturna.

O formato consumido por PSGSFXFrame/PSGFrame é um fluxo de bytes do SN76489:
comandos de latch/dados por frame, 0x38 (PSGWait) e 0x00 (PSGEnd). Este
gerador mantém os quatro SFX fora do canal 0 e também escreve os .psg-fonte
binários junto dos headers C usados pelo build.
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_psg_quality as aq  # noqa: E402  (o piso que este gerador deve honrar)


WAIT = 0x38
END = 0x00


def tone(period, channel, volume):
    base = (0x80, 0xA0, 0xC0)[channel]
    # PSGlib reserva 0x00..0x3F para comandos; o byte alto de frequência
    # precisa do bit de dado 0x40 antes de chegar ao SN76489.
    return [base | (period & 0x0F), 0x40 | ((period >> 4) & 0x3F),
            base + 0x10 | (volume & 0x0F)]


def noise(mode, volume):
    return [0xE0 | (mode & 7), 0xF0 | (volume & 0x0F)]


def stream(frames):
    data = bytearray()
    for frame in frames:
        data.extend(frame)
        data.append(WAIT)
    data.append(END)
    return bytes(data)


def vol_only(ch, att):
    return [0x90 | (ch << 5) | (att & 0x0F)]


def _hz_to_period(hz):
    p = int(223721.0 / hz + 0.5)
    # O SN76489 divide 3.579545 MHz por 16*periodo: nota mais grave real
    # ~219 Hz (periodo 0x3FF). Um 110 Hz pedido aliasava mudo em mudo do
    # byte alto para 1010 -> 221 Hz: o "baixo" dos streams antigos soava uma
    # oitava acima do escrito. O gerador nao reescreve a fisica: exige
    # registro legitimo e composes ja nascem em A3+.
    assert 0x10 <= p <= 0x3FF, \
        "hz=%.1f -> period %d fora do SN76489 (16..1023; grave real ~219 Hz)" \
        % (hz, p)
    return p


_SEMI = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4,
         'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9,
         'A#': 10, 'Bb': 10, 'B': 11}


def note(name):
    """'A4' -> 440.0. Nome de nota em temperamento igual (geração offline)."""
    key = name[:-1]
    octv = int(name[-1])
    midi = (octv + 1) * 12 + _SEMI[key]
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def stream_of(ev, total):
    """dict frame->bytes -> fluxo PSGlib com esperas empacotadas (hold<=7)."""
    out = bytearray()
    f = 0
    while f < total:
        if f not in ev:
            out.append(WAIT)
            f += 1
            continue
        out.extend(ev[f])
        nxt = next((k for k in range(f + 1, total + 1) if k in ev), total)
        hold = min(7, nxt - f - 1)
        out.append(WAIT + hold)
        f += 1 + hold
    out.append(END)
    return bytes(out)


def arrange(bars, row, lead_att=1, harm_att=6, bass_att=2, swing=0):
    """Sequenciador de semicolcheias em piso L078 + M7 (andamento).

    grid: 16 passos/compasso; passo = `row` frames (row>=7 => semicolcheia
    >= 140 ms a 50 Hz: a semineia respira em >= 28 frames, M7).
    bar = dict com:
      chord: (hz, hz, hz)  -> camada harm ch1 em colcheias com acento
      lead:  ((pos, 'A4', dur), ...)  ch0, ataque + decay 3 frames depois
      bass:  ((pos, 'A3', dur), ...)  ch2, pizzicato
      perc:  ((pos, mode, att, hold), ...)  ch3 BRANCO gateado
    swing>0 atrasa as colcheias off-beat (pos%4==2) em `swing` frames.
    """
    ev = {}

    def put(f, data):
        ev.setdefault(f, []).extend(data)

    def fr(bar, pos):
        f = bar * 16 * row + pos * row
        if swing and pos % 4 == 2:
            f += swing
        return f

    total = len(bars) * 16 * row
    for bi, bar in enumerate(bars):
        chord = bar.get('chord')
        if chord:
            steps = bar.get('harm_steps', 2)
            for s in range(0, 16, steps):
                put(fr(bi, s), tone(_hz_to_period(chord[(s // steps) % 3]),
                                    1, harm_att if (s // steps) % 2 == 0
                                    else min(15, harm_att + 2)))
        for (pos, hz, dur) in bar.get('lead', ()):
            f = fr(bi, pos)
            put(f, tone(_hz_to_period(note(hz) if isinstance(hz, str) else hz),
                        0, lead_att))
            put(f + 3, vol_only(0, min(15, lead_att + 3)))
        for (pos, hz, dur) in bar.get('bass', ()):
            f = fr(bi, pos)
            put(f, tone(_hz_to_period(note(hz) if isinstance(hz, str) else hz),
                        2, bass_att))
            put(f + 3, vol_only(2, min(15, bass_att + 5)))
        for (pos, mode, att, hold) in bar.get('perc', ()):
            f = fr(bi, pos)
            put(f, [0xE0 | (mode & 0x03)] + vol_only(3, att))
            put(f + hold, vol_only(3, 15))

    return stream_of(ev, total)


# --- repertorio -----------------------------------------------------------
# A materia musical mora aqui porque e logica de build compartilhada; cada
# projeto escolhe o seu set por nome de pasta (identidade nao se herda do
# vizinho). Andamento: row=6..10 frames por semicolcheia — semineas entre
# 392 e 640 ms a 50 Hz (94-153 BPM). O piso antigo aceitava row=2 e por
# isso as faixas 'soavam aceleradas': a medicao M7 agora exige camada que
# respire, e aqui ela e a melodia sustentada, nao o recheio.

C, S, H = 0, 3, 2          # bumbo, caixa, chimbal (todos brancos)


def _backbeat(k=2, s=2, h=8):
    """Groove de batalha: bumbo 1 e do-&, caixa 2 e 4, chimbal em 8os."""
    return ((0, C, k, 4), (2, H, h, 2), (4, S, s, 3), (6, H, h, 2),
            (8, H, h, 2), (10, C, k, 3), (12, S, s, 3), (14, H, h, 2))


def _oompah(k=3, s=5):
    """Marcha saltitante do hamoopig: oom nos tempos 1/3, caixa mais frouxa
    nos 2/4 — as duas dinamicas dao envelope ao ch3 (M4 exige 2 atenuacoes).
    """
    return ((0, C, k, 2), (4, S, s, 2), (8, C, k, 2), (12, S, s, 2))


def _bar(chord=None, lead=(), bass=(), perc=(), harm_steps=2):
    d = {}
    if chord:
        d['chord'] = chord
        d['harm_steps'] = harm_steps
    if lead:
        d['lead'] = lead
    if bass:
        d['bass'] = bass
    if perc:
        d['perc'] = perc
    return d


def _ch(*names):
    return tuple(note(n) for n in names)


# arena_nocturna — 'Cidade Noturna': Am andaluz (Andalusian Am-G-F-E na
# abertura; batalha em Am com dominante E maior). Labio inferior do
# SN76489 e A3=220 Hz: todo 'baixo' abaixo disso aliasava oitava.
ARENA_BATTLE = [
    _bar(_ch('A4', 'C5', 'E5'),
         ((0, 'E5', 4), (6, 'D5', 2), (8, 'C5', 4), (12, 'A4', 4)),
         ((0, 'A3', 4), (6, 'E4', 2), (8, 'A3', 4), (13, 'E4', 1)),
         _backbeat()),
    _bar(_ch('F4', 'A4', 'C5'),
         ((0, 'C5', 4), (4, 'A4', 2), (6, 'C5', 2), (8, 'F5', 6)),
         ((0, 'F4', 4), (6, 'C4', 2), (8, 'F4', 4), (13, 'C4', 1)),
         _backbeat()),
    _bar(_ch('G4', 'B4', 'D5'),
         ((0, 'D5', 4), (4, 'B4', 2), (6, 'G4', 2), (8, 'B4', 4),
          (12, 'D5', 4)),
         ((0, 'G4', 4), (6, 'D4', 2), (8, 'G4', 4), (13, 'D4', 1)),
         _backbeat()),
    _bar(_ch('A4', 'C5', 'E5'),
         ((0, 'E5', 2), (2, 'D5', 2), (4, 'C5', 4), (8, 'A4', 8)),
         ((0, 'A3', 4), (6, 'E4', 2), (8, 'A3', 4), (13, 'E4', 1)),
         _backbeat()),
    _bar(_ch('E4', 'G#4', 'B4'),
         ((0, 'G#4', 4), (4, 'B4', 4), (8, 'E5', 4), (12, 'G#4', 2),
          (14, 'B4', 2)),
         ((0, 'E4', 4), (6, 'B3', 2), (8, 'E4', 4), (13, 'B3', 1)),
         _backbeat()),
    _bar(_ch('A4', 'C5', 'E5'),
         ((0, 'A4', 2), (2, 'C5', 2), (4, 'E5', 4), (10, 'G#4', 2),
          (12, 'A4', 4)),   # leading tone: a noite morde
         ((0, 'A3', 4), (6, 'E4', 2), (8, 'A3', 4), (13, 'E4', 1)),
         _backbeat()),
    _bar(_ch('G4', 'B4', 'D5'),
         ((0, 'B4', 4), (4, 'D5', 4), (8, 'G5', 4), (12, 'B4', 4)),
         ((0, 'G4', 4), (6, 'D4', 2), (8, 'G4', 4), (13, 'D4', 1)),
         _backbeat()),
    _bar(_ch('A4', 'C#5', 'E5'),
         ((0, 'E5', 4), (4, 'C#5', 2), (6, 'A4', 2), (8, 'C#5', 4),
          (12, 'E5', 4)),
         ((0, 'A3', 4), (6, 'E4', 2), (8, 'A3', 4), (13, 'E4', 1)),
         _backbeat()),
]

ARENA_TITLE = [
    _bar(_ch('A3', 'C4', 'E4'),
         ((0, 'A4', 6), (6, 'C5', 4), (10, 'E5', 6)),
         ((0, 'A3', 8), (8, 'E4', 8)), ((0, H, 7, 6),), harm_steps=4),
    _bar(_ch('G4', 'B4', 'D5'),
         ((0, 'D5', 8), (8, 'B4', 4), (12, 'G4', 4)),
         ((0, 'G4', 8), (8, 'D4', 8)), ((0, H, 5, 6),), harm_steps=4),
    _bar(_ch('F4', 'A4', 'C5'),
         ((0, 'C5', 8), (8, 'F5', 8)),
         ((0, 'F4', 8), (8, 'C4', 8)), ((0, H, 7, 6),), harm_steps=4),
    _bar(_ch('E4', 'G#4', 'B4'),
         ((0, 'B4', 6), (6, 'G#4', 4), (10, 'E5', 6)),
         ((0, 'E4', 8), (8, 'B3', 8)), ((0, H, 5, 6), (8, H, 7, 4)),
         harm_steps=4),
    _bar(_ch('A3', 'C4', 'E4'),
         ((0, 'E5', 4), (4, 'D5', 2), (6, 'C5', 2), (8, 'A4', 8)),
         ((0, 'A3', 8), (8, 'E4', 8)), ((0, H, 7, 6),), harm_steps=4),
    _bar(_ch('G4', 'B4', 'D5'),
         ((0, 'D5', 4), (4, 'B4', 4), (8, 'G4', 8)),
         ((0, 'G4', 8), (8, 'D4', 8)), ((0, H, 5, 6),), harm_steps=4),
    _bar(_ch('F4', 'A4', 'C5'),
         ((0, 'A4', 4), (4, 'C5', 4), (8, 'F5', 4), (12, 'C5', 4)),
         ((0, 'F4', 8), (8, 'C4', 8)), ((0, H, 7, 6),), harm_steps=4),
    _bar(_ch('E4', 'G#4', 'B4'),
         ((0, 'B4', 4), (4, 'E5', 4), (8, 'B4', 4), (12, 'G#4', 4)),
         ((0, 'E4', 8), (8, 'B3', 8)), ((0, H, 6, 6),), harm_steps=4),
]

# hamoopig — comedia em Do maior com swing: pentatonica saltitante,
# oom-pah de marcha de circo, cadencia I-vi-IV-V.
HAMOO_BATTLE = [
    _bar(_ch('C5', 'E5', 'G5'),
         ((0, 'G5', 2), (2, 'E5', 2), (4, 'C5', 2), (6, 'E5', 2),
          (8, 'G5', 4), (12, 'C6', 4)),
         ((0, 'C4', 2), (4, 'G4', 2), (8, 'C4', 2), (12, 'G4', 2)),
         _oompah()),
    _bar(_ch('A4', 'C5', 'E5'),
         ((0, 'A5', 2), (2, 'E5', 2), (4, 'A5', 4), (8, 'C6', 2),
          (10, 'A5', 2), (12, 'E5', 4)),
         ((0, 'A3', 2), (4, 'E4', 2), (8, 'A3', 2), (12, 'E4', 2)),
         _oompah()),
    _bar(_ch('F4', 'A4', 'C5'),
         ((0, 'F5', 2), (2, 'A5', 2), (4, 'F5', 4), (8, 'C5', 2),
          (10, 'F5', 2), (12, 'A5', 4)),
         ((0, 'F4', 2), (4, 'C4', 2), (8, 'F4', 2), (12, 'C4', 2)),
         _oompah()),
    _bar(_ch('G4', 'B4', 'D5'),
         ((0, 'D5', 2), (2, 'G5', 2), (4, 'B5', 4), (8, 'D5', 2),
          (10, 'G5', 2), (12, 'B5', 4)),
         ((0, 'G4', 2), (4, 'D4', 2), (8, 'G4', 2), (12, 'D4', 2)),
         _oompah()),
    _bar(_ch('C5', 'E5', 'G5'),
         ((0, 'E5', 2), (2, 'G5', 2), (4, 'C6', 4), (8, 'G5', 2),
          (10, 'E5', 2), (12, 'C5', 4)),
         ((0, 'C4', 2), (4, 'G4', 2), (8, 'C4', 2), (12, 'G4', 2)),
         _oompah()),
    _bar(_ch('A4', 'C5', 'E5'),
         ((0, 'C5', 2), (2, 'A5', 2), (4, 'E5', 4), (8, 'A5', 2),
          (10, 'C6', 2), (12, 'A5', 4)),
         ((0, 'A3', 2), (4, 'E4', 2), (8, 'A3', 2), (12, 'E4', 2)),
         _oompah()),
    _bar(_ch('F4', 'A4', 'C5'),
         ((0, 'A4', 2), (2, 'F5', 2), (4, 'C5', 4), (8, 'F5', 2),
          (10, 'A5', 2), (12, 'C6', 4)),
         ((0, 'F4', 2), (4, 'C4', 2), (8, 'F4', 2), (12, 'C4', 2)),
         _oompah()),
    _bar(_ch('G4', 'B4', 'D5'),
         ((0, 'B4', 4), (4, 'D5', 4), (8, 'G5', 2), (10, 'D5', 2),
          (12, 'B4', 2), (14, 'G4', 2)),
         ((0, 'G4', 2), (4, 'D4', 2), (8, 'G4', 2), (12, 'D4', 2)),
         _oompah()),
]

HAMOO_TITLE = [
    _bar(_ch('E4', 'G4', 'C5'),
         ((0, 'C5', 6), (6, 'E5', 4), (10, 'G5', 6)),
         ((0, 'C4', 8), (8, 'G4', 8)), ((0, C, 4, 4), (8, H, 8, 4)),
         harm_steps=4),
    _bar(_ch('E4', 'G4', 'C5'),
         ((0, 'E5', 6), (6, 'C5', 4), (10, 'E5', 6)),
         ((0, 'C4', 8), (8, 'G4', 8)), (), harm_steps=4),
    _bar(_ch('D4', 'F4', 'A4'),
         ((0, 'A4', 6), (6, 'C5', 4), (10, 'F5', 6)),
         ((0, 'F4', 8), (8, 'C4', 8)), ((0, C, 4, 4), (8, H, 8, 4)),
         harm_steps=4),
    _bar(_ch('D4', 'G4', 'B4'),
         ((0, 'G4', 4), (4, 'B4', 4), (8, 'D5', 8)),
         ((0, 'G4', 8), (8, 'D4', 8)), (), harm_steps=4),
    _bar(_ch('E4', 'G4', 'C5'),
         ((0, 'G5', 4), (4, 'E5', 4), (8, 'C5', 4), (12, 'E5', 4)),
         ((0, 'C4', 8), (8, 'G4', 8)), ((0, C, 4, 4), (8, H, 8, 4)),
         harm_steps=4),
    _bar(_ch('E4', 'G4', 'C5'),
         ((0, 'E5', 8), (8, 'D5', 4), (12, 'C5', 4)),
         ((0, 'C4', 8), (8, 'G4', 8)), (), harm_steps=4),
    _bar(_ch('D4', 'F4', 'A4'),
         ((0, 'F5', 6), (6, 'D5', 4), (10, 'A4', 6)),
         ((0, 'F4', 8), (8, 'C4', 8)), ((0, C, 4, 4), (8, H, 8, 4)),
         harm_steps=4),
    _bar(_ch('D4', 'G4', 'B4'),
         ((0, 'B4', 4), (4, 'G4', 4), (8, 'D5', 8)),
         ((0, 'G4', 8), (8, 'D4', 8)), ((0, C, 4, 6),), harm_steps=4),
]

# projeto -> (title, battle, row_title, row_battle, swing_battle)
SONGS = {
    'arena_nocturna': (ARENA_TITLE, ARENA_BATTLE, 10, 7, 0),
    'hamoopig': (HAMOO_TITLE, HAMOO_BATTLE, 9, 6, 2),
}
DEFAULT_SONG = 'arena_nocturna'


def assets(project=''):
    base = os.path.basename(os.path.abspath(project)) if project \
        else DEFAULT_SONG
    title, battle, row_t, row_b, swing = SONGS.get(base, SONGS[DEFAULT_SONG])
    shot = stream([tone(p, 2, a) for p, a in
                   ((0x0C0, 1), (0x0A8, 3), (0x090, 5),
                    (0x078, 7), (0x064, 10), (0x054, 14))])
    hit = stream([tone(p, 2, a) + noise(0x03, a)
                  for p, a in ((0x180, 1), (0x198, 3), (0x1B0, 6),
                               (0x1C8, 9), (0x1E0, 12), (0x1F0, 15))])
    hurt = stream([noise(0x07, a) for a in
                   (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 15)])
    down = stream([noise(0x07 if i < 18 else 0x03,
                         min(15, 1 + i // 2)) for i in range(30)])

    title_blob = arrange(title, row_t, lead_att=2, harm_att=7, bass_att=2)
    battle_blob = arrange(battle, row_b, lead_att=1, harm_att=7,
                          bass_att=2, swing=swing)
    return {"sfx_shot": shot, "sfx_hit": hit, "sfx_hurt": hurt,
            "sfx_down": down, "music_title": title_blob,
            "music_battle": battle_blob}


PSG_CLOCK = 3579545.0


def render_wav(path, data, rate=44100, fps=50):
    """Render local SN76489 (numpy) para audicao sem hardware/emulador."""
    import numpy as np
    import wave
    tone_div = [1, 1, 1]
    vol = [15, 15, 15, 15]
    noise_mode = 0
    chunks, phase = [], [0.0, 0.0, 0.0]
    rng = np.random.default_rng(7)

    def amp(v):
        return 0.0 if v >= 15 else 0.25 * (10 ** (-2.0 * v / 20.0))

    i = 0
    while i < len(data):
        b = data[i]
        if b == END:
            break
        if WAIT <= b <= 0x3F:
            frames = (b & 7) + 1
            n = int(rate * frames / fps)
            t = np.arange(n)
            buf = np.zeros(n)
            for ch in range(3):
                f = PSG_CLOCK / (32.0 * max(1, tone_div[ch]))
                ph = phase[ch] + t * f / rate
                buf += amp(vol[ch]) * np.sign(np.sin(2 * np.pi * ph))
                if n:
                    phase[ch] = (ph[-1] + f / rate) % 1.0
            if vol[3] < 15:
                shift = (0x10, 0x20, 0x40, 0x80)[noise_mode & 3]
                nf = PSG_CLOCK / (32.0 * shift)
                step = max(1, int(rate / nf))
                src = rng.choice((-1.0, 1.0), size=n // step + 1)
                buf += amp(vol[3]) * np.repeat(src, step)[:n]
            chunks.append(buf)
            i += 1
            continue
        if b & 0x80:
            ch = (b >> 5) & 3
            if b & 0x10:
                vol[ch] = b & 0x0F
                i += 1
            elif ch == 3:
                noise_mode = b & 3
                i += 1
            else:
                low = b & 0x0F
                high = data[i + 1] & 0x3F
                tone_div[ch] = (high << 4) | low
                i += 2
            continue
        i += 1
    sig = np.concatenate(chunks) if chunks else np.zeros(1)
    peak = np.max(np.abs(sig)) or 1.0
    pcm = (sig / peak * 0.85 * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return len(pcm) / rate


def write_header(path, symbol, data):
    guard = symbol.upper()
    with open(path, "w", encoding="utf-8") as f:
        f.write("/* gerado por make_psg_assets.py; fluxo PSGlib */\n")
        f.write(f"#define {guard}_SIZE {len(data)}\n")
        f.write(f"static const unsigned char {symbol}[{len(data)}] = {{\n")
        f.write(",".join(f"0x{b:02X}" for b in data))
        f.write("\n};\n")


def main():
    ap = argparse.ArgumentParser()
    # --project NAO e exigido pelo argparse: o --self-check nao o usa (retorna
    # antes de tocar em disco) e `required=True` tornava o proprio self-check
    # inalcancavel — a ferramenta ficou fora do registro do selftest por isso.
    ap.add_argument("--project")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--wav", metavar="DIR",
                    help="alem dos assets, renderiza pre-escuta numpy em DIR")
    args = ap.parse_args()
    data = assets(args.project or '')
    assert all(blob[-1] == END and WAIT in blob for blob in data.values())
    assert all(b < 0x80 or b >= 0xC0 for name, blob in data.items()
               if name.startswith("sfx_") for b in blob)
    if args.self_check:
        assert len(data["sfx_shot"]) == 25       # 6 frames + wait + end
        assert len(data["sfx_hit"]) == 37        # 6 frames + wait + end
        assert len(data["sfx_hurt"]) == 49      # 16 frames + wait + end
        assert len(data["sfx_down"]) == 91      # 30 frames + wait + end
        # prova cruzada: a saida deste gerador tem que passar no piso que ela
        # mesma fez nascer (L078/M7). O gerador reprovado outrora e o fixture
        # reprovado no gate; nunca mais verde por opiniao.
        for base in SONGS:
            titled, battled, rt, rb, sw = SONGS[base]
            blobs = (arrange(titled, rt), arrange(battled, rb, swing=sw))
            for nome, blob in zip(("music_title", "music_battle"), blobs):
                ev, dur = aq.decode(blob)
                viol, _warn, m = aq.analyze(ev, dur)
                assert not viol, "%s/%s reprova no piso: %s" % (base, nome,
                                                                 viol)
                assert dur >= aq.LOOP_MIN, "%s/%s loop %d < %d" % (
                    base, nome, dur, aq.LOOP_MIN)
                assert len(blob) <= 2048, \
                    "%s/%s estoura o orcamento de 2 KB (%dB)" % (
                        base, nome, len(blob))
        for nome in ("sfx_shot", "sfx_hit", "sfx_hurt", "sfx_down"):
            ev, dur = aq.decode(data[nome])
            viol, _w = aq.analyze_sfx(ev, dur)
            assert not viol, "%s reprova no piso: %s" % (nome, viol)
        print("[SELF-CHECK OK] make_psg_assets (SFX inalterados + musicas "
              "conformes ao piso audit_psg_quality em todos os temas)")
        return 0

    if not args.project:
        ap.error("--project e obrigatorio para gerar os assets")
    project = os.path.abspath(args.project)
    inc = os.path.join(project, "inc")
    audio = os.path.join(project, "res", "audio")
    os.makedirs(inc, exist_ok=True)
    os.makedirs(audio, exist_ok=True)
    # MERGE, nao sobrescrita: carrega o manifest existente e atualiza por
    # campo "file", preservando entradas que este gerador nao conhece (ex.
    # musicas emitidas por gen_music_ken_ref.py). Reescrever o arquivo
    # inteiro apagaria a proveniencia alheia a cada regeneracao de SFX.
    manifest_path = os.path.join(project, "doc",
                                 "audio_provenance_manifest.json")
    manifest = []
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            carregado = json.load(f)
        if isinstance(carregado, dict):
            manifest = [a for a in carregado.get("assets", [])
                        if isinstance(a, dict) and "file" in a]
    roles = {
        "sfx_shot": ("hero dispara", "SFX_CHANNEL2", 6),
        "sfx_hit": ("tiro colide e gera impacto", "SFX_CHANNELS2AND3", 6),
        "sfx_hurt": ("hero recebe dano", "SFX_CHANNEL3", 16),
        "sfx_down": ("boss derrotado", "SFX_CHANNEL3", 30),
        "music_title": ("tema da tela de titulo", "music channels 0-3",
                        None),
        "music_battle": ("tema da arena", "music channels 0-3", None),
    }
    for symbol, blob in data.items():
        psg = os.path.join(audio, symbol + ".psg")
        with open(psg, "wb") as f:
            f.write(blob)
        write_header(os.path.join(inc, symbol + ".h"), symbol, blob)
        role, channels, frames = roles[symbol]
        if frames is None:
            frames = aq.decode(blob)[1]   # duracao real medida no stream
        entrada = {"file": os.path.relpath(psg, project),
                   "origin": "stream autoral sintetizado para PSGlib",
                   "author": "SMSForge",
                   "tool": "make_psg_assets.py",
                   "role": role,
                   "channels": channels,
                   "frames": frames,
                   "sha256": hashlib.sha256(blob).hexdigest(),
                   "bytes": len(blob), "format": "PSGlib stream"}
        for i, existente in enumerate(manifest):
            if existente["file"] == entrada["file"]:
                manifest[i] = entrada
                break
        else:
            manifest.append(entrada)
        print(f"[OK] {os.path.relpath(psg, project)} {len(blob)}B")
    if args.wav:
        os.makedirs(args.wav, exist_ok=True)
        for symbol in ("music_title", "music_battle"):
            out = os.path.join(args.wav, symbol + ".wav")
            dur = render_wav(out, data[symbol])
            print(f"[WAV] {out} ({dur:.1f}s)")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"assets": manifest}, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
