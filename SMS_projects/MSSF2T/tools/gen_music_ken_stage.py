#!/usr/bin/env python3
"""Transcreve o tema do Ken (SSF2) do MID de referencia e emite o fluxo PSGlib.

Diferente da versao anterior (composicao ORIGINAL em La menor que nao soava
ao tema), este script LE o arquivo hasheado em
art_src_base/audio/music/reference/ssf2_ken_stage_vgmusic.mid e extrai a
cabeca do tema: compassos 19-24 (pick-up em 16/1 + 5), onde o riff dos
metais (tracks 7/8), o comping de guitarra (track 2), o baixo em semicolcheias
(track 6) e a bateria funk (track 1) tocam juntos.

O grid real do arquivo e a semicolcheia de 240 ticks (divisao 960, 90 BPM):
por isso a emulacao usa 16 passos/compasso, e nao a grade antiga de colcheia.
Transposicao para o piso do SN76489 (periodo <= 0x3FF, ou seja, nada abaixo
de ~110 Hz): lead +0 (C4-C5), guitarra +12, baixo +12 comclamp de oitava.

Economia de ROM (o cartucho e 32K sem paging e a folga e de dezenas de
bytes): o stream so escreve o registrador que MUDOU; repeticao da mesma
nota e articulada por mute de 1 frame + nivel (2 B), nunca por latch novo.

O tema e o stream de musica (PSGPlay em fight.c); a voz "FIGHT" da abertura
da luta e um SFX a parte (PSGSFXPlay nos canais 1+2+3, máscara verificada
em sdk/devkitSMS/PSGlib/PSGlib.h).

Uso:
  python3 tools/gen_music_ken_stage.py --emit       # inc/*.h + res/audio/*.psg
  python3 tools/gen_music_ken_stage.py --wav a.wav  # render p/ audicao
  python3 tools/gen_music_ken_stage.py --self-check
"""
import argparse
import os
import struct
import sys

PSG_CLOCK = 3579545
FPS = 60
WAIT = 0x38
END = 0x00

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
MID = os.path.join(PROJ, "art_src_base", "audio", "music", "reference",
                   "ssf2_ken_stage_vgmusic.mid")

# --- janela do tema ------------------------------------------------------
SIXTEENTH = 240          # ticks (divisao 960, compasso 4/4 = 3840)
LOOP_POS = 287           # 16a semicolcheia absoluta: pick-up do riff (C4)
BARS = 8                 # periodo completo: A + A' + virada de 2 + resposta
ROWS_PER_BAR = 16
ROW_FRAMES = 10          # 1 semicolcheia = 10 frames NTSC (~90 BPM real)
TOTAL_FRAMES = BARS * ROWS_PER_BAR * ROW_FRAMES          # 1280
TOTAL_ROWS = BARS * ROWS_PER_BAR                          # 128

T0 = LOOP_POS * SIXTEENTH
T1 = T0 + TOTAL_ROWS * SIXTEENTH

# tracks do SMF: 7/8 = metais (unissono dobrado), 2 = guitarra, 6 = baixo,
# 1 = bateria GM.
LEAD_TRACKS = (7, 8)
COMP_TRACK = 2
BASS_TRACK = 6
DRUM_TRACK = 1


def parse_mid(path):
    """Retorna {track_idx: [(start, dur, pitch), ...]} com running status."""
    blob = open(path, "rb").read()
    assert blob[:4] == b"MThd", "nao e um SMF"
    fmt, ntrk, div = struct.unpack(">HHH", blob[8:14])
    assert fmt == 1 and div == 960, (fmt, div)
    pos = 14
    tracks = {}
    for ti in range(ntrk):
        assert blob[pos:pos + 4] == b"MTrk", ti
        ln, = struct.unpack(">I", blob[pos + 4:pos + 8])
        body = blob[pos + 8:pos + 8 + ln]
        pos += 8 + ln
        t, rs, open_notes, out, j = 0, 0, {}, [], 0

        def vlq():
            nonlocal j
            v = 0
            while True:
                d = body[j]
                j += 1
                v = (v << 7) | (d & 0x7F)
                if not d & 0x80:
                    return v
        while j < len(body):
            t += vlq()
            b = body[j]
            if b < 0x80:
                # running status: b e o PRIMEIRO parametro; eventos de tom
                # (note on/off) tem dois — ler o segundo byte atras de b.
                ev, j = rs, j + 1
                if (ev & 0xF0) in (0x90, 0x80, 0xA0, 0xB0, 0xE0):
                    data = [b, body[j]]
                    j += 1
                else:
                    data = [b]
            else:
                ev = b
                j += 1
                if (ev & 0xF0) in (0xC0, 0xD0) or ev == 0xFF:
                    data = []
                    if ev == 0xFF:
                        mt = body[j]
                        j += 1
                        l = vlq()
                        j += l
                        if mt == 0x2F:
                            break
                elif ev in (0xF0, 0xF7):
                    # sysex (ex.: reset Roland no track 0): length VLQ + payload
                    l = vlq()
                    j += l
                    data = []
                else:
                    data = []
                    for _ in range(2):
                        if body[j] < 0x80:
                            data.append(body[j])
                            j += 1
            hi = ev & 0xF0
            if hi in (0x90, 0x80) and len(data) == 2:
                key = (ev & 0x0F, data[0])
                if hi == 0x90 and data[1] > 0:
                    open_notes[key] = t
                elif key in open_notes:
                    st = open_notes.pop(key)
                    out.append((st, t - st, data[0]))
            rs = ev
        tracks[ti] = out
    return tracks


def quantize(events, t0=None, rows=None):
    """Eventos absolutos -> (linha, dur_linhas, pitch) na janela, 16a grid."""
    t0 = T0 if t0 is None else t0
    rows = TOTAL_ROWS if rows is None else rows
    t1 = t0 + rows * SIXTEENTH
    out = []
    for st, dur, p in events:
        if st + dur <= t0 or st >= t1:
            continue
        r = int(round((st - t0) / float(SIXTEENTH)))
        d = max(1, int(round(dur / float(SIXTEENTH))))
        if r >= rows:
            continue
        out.append((max(0, r), d, p))
    return out


def merge_unison(rows):
    """Tracks dobradas em unissono viram uma linha so; empate de onset
    simultaneo com pitch diferente fica o mais agudo (melodia por cima)."""
    best = {}
    for r, d, p in rows:
        k = (r, p)
        if k not in best or d > best[k]:
            best[k] = d
    by_row = {}
    for (r, p), d in best.items():
        if r in by_row and by_row[r][2] >= p:
            continue
        by_row[r] = (r, d, p)
    return sorted(by_row.values())


def seg_comp(rows):
    """Repeticoes consecutivas da MESMA nota do comping viram um segmento
    sustentado (economia: o pump de 16as da guitarra custa 3 B por nota e
    nao e audivel no tom sostenido do PSG)."""
    rows = sorted(rows)
    segs, i = [], 0
    while i < len(rows):
        r, d, p = rows[i]
        end = r + d
        while i + 1 < len(rows) and rows[i + 1][2] == p and rows[i + 1][0] <= end:
            end = max(end, rows[i + 1][0] + rows[i + 1][1])
            i += 1
        segs.append((r, max(1, end - r), p))
        i += 1
    return segs


def gate_eighths(rows):
    """Bateria/abaixo: mantém onsets na grade de colcheia (par), derrama o
    resto — 96 hits de 16a em 6 compassos nao cabem em 32 KB."""
    return [e for e in rows if e[0] % 2 == 0 or e[2] == 49]  # crash fica


# --- transposicao e periodos ---------------------------------------------
def tone_pitch(p, shift):
    """Sobe oitavas ate o periodo caber em 10 bits (>= ~110 Hz real)."""
    p += shift
    while _pitch_to_period(p) > 0x3FF:
        p += 12
    return p


def _pitch_to_period(p):
    freq = 440.0 * 2 ** ((p - 69) / 12.0)
    return max(1, min(0x7FF, int(round(PSG_CLOCK / (32.0 * freq)))))


CH_BASE = (0x80, 0xA0, 0xC0)


def tone_bytes(ch, div):
    return [CH_BASE[ch] | (div & 0x0F), 0x40 | ((div >> 4) & 0x3F)]


def vol_byte(ch, v):
    return (CH_BASE[ch] + 0x10) | (v & 0x0F)


def noise_bytes(mode):
    return [0xE0 | (mode & 7)]


def noise_vol(v):
    return [0xF0 | (v & 0x0F)]


# --- volumes ---------------------------------------------------------------
# Atenuacao: 0 = maximo, 15 = mudo.
LEAD_LO, LEAD_HI = 1, 5        # nota longa/aguda em LEAD_LO, passageira HI
COMP_VOL, COMP_OFF = 6, 15
BASS_VOL, BASS_ACC = 2, 4
KICK, SNARE, HAT = (0, 2), (3, 3), (2, 7)
PERC_OFF = 13                  # repouso do ruido (chiado fantasma sem ele)

# GM -> (modo de ruido branco, atenuacao). Tons de tom-tom viram branco
# periodo 1/2; vibraslap (57) nao tem equivalente e e descartado.
DRUM_MAP = {36: KICK, 38: SNARE, 42: HAT, 44: HAT, 40: SNARE,
            49: (1, 3), 43: (2, 4), 45: (1, 4), 47: (1, 5), 48: (0, 5),
            51: (2, 5)}


def compose(tracks, rows=TOTAL_ROWS, row_frames=ROW_FRAMES,
            drums=True, bass_every=2):
    """Devolve {frame: [bytes]} com diff de registrador por canal.

    rows=row_frames=None explicitam o arranjo; `bass_every` controla a
    densidade do pump (2 = colcheias da batalha, 4 = semiminimas solenes
    da tela de titulo) e `drums=False` retira o canal de ruido."""
    total = rows * row_frames
    ev = {}

    def put(frame, data):
        ev.setdefault(frame, []).extend(data)

    def tone(ch, frame, pitch, vol):
        put(frame, tone_bytes(ch, _pitch_to_period(pitch)) + [vol_byte(ch, vol)])

    def vol(ch, frame, v):
        put(frame, [vol_byte(ch, v)])

    # canal 0 — metais: riff transcrito, nota longa com ataque forte
    lead = merge_unison(quantize(sum((tracks[i] for i in LEAD_TRACKS), []),
                                 rows=rows))
    for r, d, p in lead:
        f = r * row_frames
        tone(0, f, p + 0, LEAD_LO if (d >= 3 or p >= 72) else LEAD_HI)
        if d >= 4:                              # sustenido: respira o volume
            vol(0, f + min(d * row_frames - 2, 6), LEAD_LO + 2)

    # canal 1 — comping de guitarra em segmentos. Acento alternado (M2):
    # sem duas atenuacoes o colchao e buzina estatica.
    comp = seg_comp(quantize(tracks[COMP_TRACK], rows=rows))
    for si, (r, d, p) in enumerate(comp):
        f = r * row_frames
        tone(1, f, tone_pitch(p, 12), COMP_VOL + (si % 2))
        vol(1, min((r + d) * row_frames - 1, total - 1), COMP_OFF)

    # canal 2 — baixo: pump articulado por mute de 1 frame
    bass = [(r, d, p) for r, d, p in quantize(tracks[BASS_TRACK], rows=rows)
            if r % bass_every == 0]
    last = None
    for r, d, p in bass:
        f = r * row_frames
        pitch = tone_pitch(p, 12)
        vol(2, f, 15)                            # articulacao (staccato)
        if pitch != last:
            tone(2, f + 1, pitch, BASS_ACC if r % 8 == 4 else BASS_VOL)
        else:
            put(f + 1, [vol_byte(2, BASS_ACC if r % 8 == 4 else BASS_VOL)])
        last = pitch

    # canal 3 — bateria funk
    if drums:
        kit = {}
        for r, d, p in gate_eighths(quantize(tracks[DRUM_TRACK], rows=rows)):
            if p in DRUM_MAP:
                kit.setdefault(r, []).append((p, DRUM_MAP[p]))
        cur_mode = None
        for r in sorted(kit):
            f = r * row_frames
            hits = sorted(set(m for _, m in kit[r]),
                          key=lambda x: (x[1], x[0]))
            mode, v = hits[0]
            if mode != cur_mode:
                put(f, noise_bytes(mode))
                cur_mode = mode
            put(f, noise_vol(v))
            if len(hits) > 1:  # simultaneidade: segundo toque 1 frame depois
                mode2, v2 = hits[1]
                put(f + 1, noise_bytes(mode2) + noise_vol(v2))
                cur_mode = mode2
            put(min(f + 2, total - 1), noise_vol(PERC_OFF))

    return ev


def build_stream(ev, total_frames):
    """Serializa eventos + esperas no formato PSGlib (esperas no maximo de
    8 frames por byte)."""
    out = bytearray()
    pending = 0

    def flush_wait():
        nonlocal pending
        while pending > 0:
            n = min(8, pending)
            out.append(WAIT | (n - 1))
            pending -= n

    for f in range(total_frames):
        if f in ev:
            flush_wait()
            out.extend(ev[f])
        pending += 1
    flush_wait()
    out.append(END)
    return bytes(out)


# arranjo da tela de titulo: a mesma cabeca em 6 compassos sem bateria,
# semicolcheia de 12 frames — hino, nao groove. O pump do baixo fica
# (colcheias) porque sem ele o M6 nao encontra 2 canais melodicos.
TITLE_ROWS = 96
TITLE_ROW_FRAMES = 12
TITLE_FRAMES = TITLE_ROWS * TITLE_ROW_FRAMES           # 1152


def make(tracks=None):
    if tracks is None:
        tracks = parse_mid(MID)
    ev = compose(tracks)
    return build_stream(ev, TOTAL_FRAMES), TOTAL_FRAMES


def make_title(tracks=None):
    if tracks is None:
        tracks = parse_mid(MID)
    ev = compose(tracks, rows=TITLE_ROWS, row_frames=TITLE_ROW_FRAMES,
                 drums=False)
    return build_stream(ev, TITLE_FRAMES), TITLE_FRAMES


# --- voz "FIGHT" (sintese por formantes no PSG) ----------------------------
# /f/ = ruido branco periodo 3 fricado; /ai/ = F1 no canal 2 + F2 no canal 1
# deslizando de [a] (1000/1400 Hz) para [i] (400/2000 Hz) com pitch caindo;
# /t/ = rajada de ruido periodo 0. Jogada via PSGSFXPlay nos canais 1+2+3,
# que sao justamente os que a musica pode ceder por ~0,5 s na abertura.
def _hz(n):
    return max(1, min(0x3FF, int(round(PSG_CLOCK / (32.0 * n)))))


def build_voice():
    fr = []
    # F: ruido branco p3 fricado; vogais entram suaves nos formantes
    fr.append((noise_bytes(3) + noise_vol(2)
               + tone_bytes(1, _hz(2000)) + [vol_byte(1, 9)]
               + tone_bytes(2, _hz(400)) + [vol_byte(2, 9)]
               + [0xF0 | 15], 3))
    # [a]: F1 1000 / F2 1400, formante grave mais alta
    fr.append((tone_bytes(2, _hz(1000)) + [vol_byte(2, 2)]
               + tone_bytes(1, _hz(1400)) + [vol_byte(1, 5)]
               + noise_vol(15), 3))
    # [a]->[e] deslizante
    fr.append((tone_bytes(2, _hz(800)) + [vol_byte(2, 3)]
               + tone_bytes(1, _hz(1700)) + [vol_byte(1, 6)], 3))
    # [i]: F1 400 / F2 2000
    fr.append((tone_bytes(2, _hz(400)) + [vol_byte(2, 4)]
               + tone_bytes(1, _hz(2000)) + [vol_byte(1, 7)], 3))
    # extinguer vogal (pitch cai = /ay/ curto)
    fr.append(([vol_byte(2, 9), vol_byte(1, 11)], 2))
    # T: rajada seca p0 que decai imediatamente — S1 exige terminar mais
    # baixo do que comecar, senao o gate le o corte como clique.
    fr.append((noise_bytes(0) + noise_vol(2), 1))
    fr.append((noise_vol(10) + [vol_byte(1, 15), vol_byte(2, 15)], 1))
    fr.append((noise_vol(15), 0))
    out = bytearray()
    for data, hold in fr:
        out.extend(data)
        out.append(WAIT + hold if hold else WAIT)
    out.append(END)
    return bytes(out)


# --- render local (SN76489 em numpy), para audicao sem hardware ------------
def render_wav(path, data, rate=44100):
    import numpy as np
    import wave

    tone_div = [1, 1, 1]
    vol = [15, 15, 15, 15]
    noise_mode = 0
    chunks = []
    phase = [0.0, 0.0, 0.0]
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
            n = int(rate * frames / FPS)
            t = np.arange(n)
            buf = np.zeros(n)
            for ch in range(3):
                f = PSG_CLOCK / (32.0 * max(1, tone_div[ch]))
                ph = phase[ch] + t * f / rate
                buf += amp(vol[ch]) * np.sign(np.sin(2 * np.pi * ph))
                phase[ch] = (ph[-1] + f / rate) % 1.0 if n else phase[ch]
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


def write_header(path, symbol, note, data):
    with open(path, "w", encoding="utf-8") as f:
        f.write("/* gerado por tools/gen_music_ken_stage.py; fluxo PSGlib.\n"
                f" * {note}\n"
                " * NAO editar a mao — regenerar pelo script. */\n")
        f.write(f"#define {symbol.upper()}_SIZE {len(data)}\n")
        f.write(f"static const unsigned char {symbol}[{len(data)}] = {{\n")
        for i in range(0, len(data), 16):
            f.write(",".join(f"0x{b:02X}" for b in data[i:i + 16]) + ",\n")
        f.write("};\n")


def stream_asserts(data, total, name):
    assert data[-1] == END, f"{name}: fluxo precisa terminar em PSGEnd"
    assert END not in data[:-1], f"{name}: PSGEnd prematuro"
    i, seen = 0, 0
    while i < len(data) - 1:
        b = data[i]
        if WAIT <= b <= 0x3F:
            seen += (b & 7) + 1
            i += 1
        elif b & 0x80 and not (b & 0x10) and ((b >> 5) & 3) != 3:
            assert data[i + 1] >= 0x40, f"{name}: byte alto sem 0x40 em {i}"
            i += 2
        else:
            assert b >= 0x80, f"{name}: dado 0x{b:02X}@{i} invade comando"
            i += 1
    assert seen == total, f"{name}: frames {seen} != {total}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--wav")
    ap.add_argument("--title-wav")
    ap.add_argument("--voice-wav")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()

    data, total = make()
    title, title_total = make_title()
    voice = build_voice()

    if args.self_check:
        sys.path.insert(0, os.path.abspath(os.path.join(
            PROJ, os.pardir, os.pardir, "tools", "sms_wrapper")))
        import audit_psg_quality as aq
        stream_asserts(data, total, "music")
        ev, dur = aq.decode(data)
        viol, warn, m = aq.analyze(ev, dur)
        assert not viol, f"piso musical reprovado: {viol}"
        assert not warn, f"avisos no tema: {warn}"
        stream_asserts(title, title_total, "title")
        evt, dart = aq.decode(title)
        violt, wart, mt = aq.analyze(evt, dart)
        assert not violt, f"piso do titulo reprovado: {violt}"
        # o titulo e deliberadamente sem bateria: so o aviso de ruido e aceito
        assert all('M4' in w for w in wart), f"aviso inesperado no titulo: {wart}"
        evv, durv = aq.decode(voice)
        stream_asserts(voice, durv, "voice")
        vs, ws = aq.analyze_sfx(evv, durv)
        assert not vs, f"voz reprovada: {vs}"
        assert durv <= 45 and len(voice) <= 64, (durv, len(voice))
        print(f"[SELF-CHECK OK] gen_music_ken_stage: batalha {len(data)} B / "
              f"{total} frames ({total / FPS:.1f}s), titulo {len(title)} B / "
              f"{dart} frames, voz {len(voice)} B / {durv} frames; "
              f"gap medio {m['gap_medio']}, unison {m['unison']}")
        return 0

    print(f"stream: {len(data)} bytes, {total} frames = {total / FPS:.2f}s "
          f"| titulo: {len(title)} bytes, {title_total} frames "
          f"| voz: {len(voice)} bytes")
    if args.wav:
        print(f"wav: {args.wav} ({render_wav(args.wav, data):.2f}s)")
    if args.title_wav:
        print(f"titulo: {args.title_wav} "
              f"({render_wav(args.title_wav, title):.2f}s)")
    if args.voice_wav:
        print(f"voz: {args.voice_wav} "
              f"({render_wav(args.voice_wav, voice):.2f}s)")
    if args.emit:
        write_header(os.path.join(PROJ, "inc", "music_battle.h"),
                     "music_battle",
                     "Tema do Ken (SSF2) transcrito do MID de referencia: "
                     "metais / guitarra / baixo / bateria funk, 90 BPM, "
                     "loop de 8 compassos", data)
        write_header(os.path.join(PROJ, "inc", "music_title.h"),
                     "music_title",
                     "Cabeca do tema do Ken em arranjo de titulo: 4 "
                     "compassos, sem bateria, baixo em semiminimas", title)
        write_header(os.path.join(PROJ, "inc", "sfx_fight.h"), "sfx_fight",
                     'Voz "FIGHT" da abertura da luta: sintese por formantes '
                     "(canais 1+2+3)", voice)
        raw = os.path.join(PROJ, "res", "audio")
        os.makedirs(raw, exist_ok=True)
        with open(os.path.join(raw, "music_ken_stage.psg"), "wb") as f:
            f.write(data)
        with open(os.path.join(raw, "music_battle.psg"), "wb") as f:
            f.write(data)
        with open(os.path.join(raw, "music_title.psg"), "wb") as f:
            f.write(title)
        with open(os.path.join(raw, "sfx_fight.psg"), "wb") as f:
            f.write(voice)
        print("emit: inc/{music_battle,music_title,sfx_fight}.h "
              "res/audio/{music_ken_stage,music_battle,music_title,"
              "sfx_fight}.psg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
