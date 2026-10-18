#!/usr/bin/env python3
"""Transcreve o tema do Ken Stage (Super Street Fighter II Turbo) para PSGlib.

A referencia e o MIDI de fa arquivado em
art_src_base/audio/music/reference/ (proveniencia no README.md ao lado):
parser proprio de SMF, sem dependencia externa — chunks MThd/MTrk, delta-time
VLQ, running status, meta-evento de tempo. Nada do MIDI entra na ROM; o que
entra e a transcricao para os 3 canais de tom + 1 de ruido do SN76489.

Mapeamento de vozes (escolha automatica por media de altura entre stems com
>= MIN_STEM_NOTES notas; stems curtos sao floreio e ficam de fora):
  melodia (voz mais aguda ativa)      -> canal 0
  harmonia (stem restante mais ativo) -> canal 1
  baixo (voz mais grave ativa)        -> canal 2
  percussao (canal MIDI indice 9)     -> ruido canal 3
    bumbo <38 -> modo 0x06, caixa 38-41 -> 0x04, chimbal 42-47 -> 0x03,
    prato >=48 -> 0x05 (mesma familia de modos do gerador autoral)

A referencia repete a secao melodica: o periodo minimo de compassos e
detectado por assinatura de compasso e so um periodo e serializado — o
PSGEnd faz a lib voltar sozinha ao inicio (loop infinito). Se ainda assim o
fluxo estourar o orcamento duro de 945 B (slot atual na ROM), uma escada de
variantes abre mao de expressao (release de nota, decaimento de percussao),
de vozes secundarias e por fim de compassos — nunca inventa banking.

Nota grave: o SN76489 nao toca abaixo de ~109 Hz (divisor de 10 bits). Notas
do baixo abaixo do alcance sobem uma oitava por nota antes do clamp; o
contorno melodico fica acima do piso, ao custo de salto pontual.

Uso:
  python3 tools/gen_music_ken_ref.py --emit      # .psg + espelho + header
  python3 tools/gen_music_ken_ref.py --wav out/ken_ref_preview.wav
  python3 tools/gen_music_ken_ref.py --self-check
"""
import argparse
import os
import struct
import sys

PSG_CLOCK = 3579545
FPS = 60
WAIT = 0x38
END = 0x00

BUDGET = 945          # slot atual da musica na ROM; orcamento duro
MIN_STEM_NOTES = 200  # stems menores que isso sao floreio, nao voz

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
REFERENCE = os.path.join(PROJ, "art_src_base", "audio", "music",
                         "reference", "ssf2_ken_stage_vgmusic.mid")

# attenuacoes-base por voz (0 = maximo, 15 = mudo) — mesmas do gerador
# autoral, calibradas para o gate audit_audio (>=90% de janelas ativas).
VOL_LEAD = 1
VOL_HARM = 5
VOL_BASS = 2
VOL_PERC = 3
VOL_HAT = VOL_PERC + 5

CH_BASE = (0x80, 0xA0, 0xC0)

PERC_CHANNEL = 9  # canal GM de percussao (indice 0-based)


# --- parser SMF minimo (sem dependencia externa) --------------------------
def _vlq(data, i):
    """Delta-time VLQ: 7 bits por byte, bit alto continua."""
    v = 0
    while True:
        b = data[i]
        i += 1
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            return v, i


def parse_midi(path):
    """SMF -> (tpqn, tempo_us, stems, perc).

    stems: {(trk, ch): [(on_tick, off_tick, nota, vel)]} — notas pareadas;
    perc:  [(tick, nota, vel)] do canal GM de percussao.
    """
    raw = open(path, "rb").read()
    assert raw[:4] == b"MThd", "referencia nao e um MIDI valido (magic MThd)"
    tpqn = struct.unpack(">H", raw[12:14])[0]
    tempo_us = 500000
    stems = {}
    perc = []
    i = 14
    trk = -1
    while i < len(raw):
        chunk = raw[i:i + 4]
        ln = struct.unpack(">I", raw[i + 4:i + 8])[0]
        body = raw[i + 8:i + 8 + ln]
        i += 8 + ln
        if chunk != b"MTrk":
            continue
        trk += 1
        j = 0
        tick = 0
        run = None
        # pilha por (canal, nota): note-ons aguardando o note-off
        active = {}
        while j < len(body):
            d, j = _vlq(body, j)
            tick += d
            st = body[j]
            if st & 0x80:
                j += 1
                run = st
            else:
                st = run  # running status
            hi = st & 0xF0
            ch = st & 0x0F
            if hi in (0x90, 0x80):
                note, vel = body[j], body[j + 1]
                j += 2
                key = (ch, note)
                if hi == 0x90 and vel > 0:
                    active.setdefault(key, []).append((tick, vel))
                else:
                    if active.get(key):
                        on_tick, on_vel = active[key].pop(0)
                        if ch == PERC_CHANNEL:
                            perc.append((on_tick, note, on_vel))
                        else:
                            stems.setdefault((trk, ch), []).append(
                                (on_tick, tick, note, on_vel))
            elif hi in (0xA0, 0xB0, 0xE0):
                j += 2
            elif hi in (0xC0, 0xD0):
                j += 1
            elif st == 0xFF:
                mt = body[j]
                j += 1
                ln2, j = _vlq(body, j)
                if mt == 0x51 and ln2 == 3:
                    tempo_us = int.from_bytes(body[j:j + 3], "big")
                if mt == 0x2F:
                    j = len(body)  # fim de trilha
                else:
                    j += ln2
            elif st in (0xF0, 0xF7):
                ln2, j = _vlq(body, j)
                j += ln2
            else:
                j += 1
    return tpqn, tempo_us, stems, perc


# --- altura -> divisor SN76489 -------------------------------------------
def note_period(note):
    """Numero MIDI -> divisor de 10 bits (f = clk / (32*div)); notas abaixo
    do alcance do SN76489 sobem de oitava em oitava ate caber."""
    while True:
        freq = 440.0 * 2 ** ((note - 69) / 12.0)
        div = int(round(PSG_CLOCK / (32.0 * freq)))
        if div <= 1023 or note > 120:
            return max(1, min(1023, div))
        note += 12


def tone_bytes(ch, div):
    """Latch de tom: byte alto precisa de 0x40 para nao virar comando PSGlib."""
    return [CH_BASE[ch] | (div & 0x0F), 0x40 | ((div >> 4) & 0x3F)]


def vol_byte(ch, v):
    return (CH_BASE[ch] + 0x10) | (v & 0x0F)


def noise_bytes(mode):
    return [0xE0 | (mode & 7)]


def noise_vol(v):
    return [0xF0 | (v & 0x0F)]


def drum_mode(pitch):
    if pitch < 38:
        return 0x06                     # bumbo
    if pitch < 42:
        return 0x04                     # caixa
    if pitch < 48:
        return 0x03                     # chimbal fechado
    return 0x05                         # prato / chimbal aberto


def vel_att(base, vel):
    """Attenuacao (0=max..15=mudo) por voz base + dinamica do MIDI."""
    return max(0, min(14, base + (127 - vel) // 32))


# --- analise da referencia ------------------------------------------------
class Ref:
    """Referencia analisada: vozes escolhidas, grade de frames, forma."""

    def __init__(self, path):
        self.tpqn, tempo_us, stems, perc = parse_midi(path)
        self.bpm = round(60_000_000.0 / tempo_us, 1)
        self.frames_per_tick = FPS * tempo_us / (1_000_000.0 * self.tpqn)
        self.bar_ticks = self.tpqn * 4
        self.frame_per_bar = round(self.bar_ticks * self.frames_per_tick)

        big = {k: ns for k, ns in stems.items() if len(ns) >= MIN_STEM_NOTES}
        assert big, "nenhum stem com notas suficientes na referencia"

        def avg_pitch(k):
            ns = stems[k]
            return sum(n for _, _, n, _ in ns) / len(ns)

        self.melody = max(big, key=avg_pitch)
        self.bass = min(big, key=avg_pitch)
        rest = [k for k in big if k not in (self.melody, self.bass)]
        self.harmony = max(rest, key=lambda k: len(stems[k])) if rest else None

        self.mel_notes = sorted(stems[self.melody])
        self.bass_notes = sorted(stems[self.bass])
        self.harm_notes = sorted(stems[self.harmony]) if self.harmony else []

        # forma: assinatura de compasso da melodia -> periodo minimo.
        # A janela comeca no primeiro compasso COM melodia (a intro so de
        # groove da referencia nao vale repeticao a cada loop).
        sig = {}
        for on, off, n, v in self.mel_notes:
            sig.setdefault(on // self.bar_ticks, set()).add(
                (on % self.bar_ticks, n))
        self.mel_start = min(sig)
        self.mel_bars = max(sig) - self.mel_start + 1
        filled = tuple(frozenset(sig[b]) for b in sorted(sig))
        self.mel_period = len(filled)
        for p in range(1, len(filled) // 2 + 1):
            if all(filled[i] == filled[i % p] for i in range(len(filled))):
                self.mel_period = p
                break
        last_tick = max([off for _, off, _, _ in self.mel_notes] +
                        [off for _, off, _, _ in self.bass_notes] +
                        [t for t, _, _ in perc])
        self.total_bars = last_tick // self.bar_ticks + 1
        self.perc = perc


# --- serializacao ---------------------------------------------------------
def voice_events(notes, ch, bars_n, bar_ticks, fpt, base_vol, releases,
                 start_tick=0):
    """Eventos de registrador de uma voz tonal na janela de bars_n compassos
    a partir de start_tick.

    Legato por padrao: so escreve volume quando a dinamica muda (o
    registrador do PSG persiste), economizando 1 B por nota.
    """
    window = start_tick + bars_n * bar_ticks
    frames_n = bars_n * round(bar_ticks * fpt)
    ev = {}
    last_att = None

    def put(frame, data):
        if 0 <= frame < frames_n:
            ev.setdefault(frame, []).extend(data)

    put(0, [vol_byte(ch, base_vol)])
    in_window = [x for x in notes if start_tick <= x[0] < window]
    for k, (on, off, n, v) in enumerate(in_window):
        f = round((on - start_tick) * fpt)
        att = vel_att(base_vol, v)
        data = tone_bytes(ch, note_period(n))
        if att != last_att:
            data = data + [vol_byte(ch, att)]
            last_att = att
        put(f, data)
        if releases and k + 1 < len(in_window):
            end_f = round((off - start_tick) * fpt)
            nxt = round((in_window[k + 1][0] - start_tick) * fpt)
            if end_f > f and end_f < nxt:
                put(end_f, [vol_byte(ch, 15)])
                last_att = None
    return ev


def perc_events(hits, bars_n, bar_ticks, fpt, sparse, decays,
                start_tick=0):
    """Eventos de ruido; com sparse, chimbal so em colcheia (grade par)."""
    window = start_tick + bars_n * bar_ticks
    frames_n = round(window * fpt)
    sixteenth = max(1, bar_ticks // 4)
    ev = {}

    def put(frame, data):
        if 0 <= frame < frames_n:
            ev.setdefault(frame, []).extend(data)

    put(0, noise_bytes(0x03) + noise_vol(15))
    for t, n, v in hits:
        if t >= window:
            break
        if t < start_tick:
            continue
        mode = drum_mode(n)
        if sparse and 42 <= n < 48 and (t // sixteenth) % 2:
            continue  # chimbal em semifusa cai fora na variante enxuta
        f = round((t - start_tick) * fpt)
        base = VOL_PERC if n < 42 else VOL_HAT if n < 48 else VOL_PERC + 2
        att = vel_att(base, v)
        put(f, noise_bytes(mode) + noise_vol(att))
        if decays and n < 42:  # bumbo/caixa apagam; chimbal morre sozinho
            put(f + (4 if n < 38 else 3), noise_vol(15))
    return ev


def build_stream(ev, total_frames):
    """Mesma serializacao do gerador autoral: eventos + esperas de ate 8."""
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


def make_variant(ref, bars_n, harmony, releases, decays, sparse):
    """Monta o fluxo de uma variante; devolve (bytes, frames_totais)."""
    fpt = ref.frames_per_tick
    start = ref.mel_start * ref.bar_ticks
    ev = {}
    for src_ev in (voice_events(ref.mel_notes, 0, bars_n, ref.bar_ticks, fpt,
                                VOL_LEAD, releases, start),
                   voice_events(ref.harm_notes, 1, bars_n, ref.bar_ticks, fpt,
                                VOL_HARM, releases, start) if harmony and
                   ref.harm_notes else {},
                   voice_events(ref.bass_notes, 2, bars_n, ref.bar_ticks, fpt,
                                VOL_BASS, releases, start),
                   perc_events(ref.perc, bars_n, ref.bar_ticks, fpt, sparse,
                               decays, start)):
        for f, data in src_ev.items():
            ev.setdefault(f, []).extend(data)
    total = bars_n * ref.frame_per_bar
    return build_stream(ev, total), total


def variant_ladder(period):
    """Escada de riqueza: mais compassos > harmonia > expressao > enxuto."""
    ladder = []
    for bars_n in (period, max(4, period // 2), max(4, period // 4)):
        for harmony in (True, False):
            for releases in (True, False):
                for decays in (True, False):
                    for sparse in (False, True):
                        ladder.append((bars_n, harmony, releases, decays,
                                       sparse))
    return ladder


def make():
    """Escolhe a variante mais rica que cabe no orcamento."""
    ref = Ref(REFERENCE)
    for opt in variant_ladder(ref.mel_period):
        stream, total = make_variant(ref, *opt)
        if len(stream) <= BUDGET:
            return ref, opt, stream, total
    menor = min(len(make_variant(ref, *o)[0]) for o in
                variant_ladder(ref.mel_period))
    raise SystemExit(f"nenhuma variante cabe em {BUDGET} B "
                     f"(menor teste: {menor} B)")


# --- render local (SN76489 em numpy), igual ao gerador autoral ------------
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


def write_header(path, symbol, data, harmony):
    """Mesma estrutura do header atual consumido pelo C (linhas de 16 B)."""
    vozes = ("melodia / harmonia / baixo" if harmony
             else "melodia / baixo (harmonia cortada no orcamento)")
    with open(path, "w", encoding="utf-8") as f:
        f.write("/* gerado por tools/gen_music_ken_ref.py; fluxo PSGlib.\n"
                " * Transcricao do tema do Ken Stage (SSF2T): referencia MIDI\n"
                " * em art_src_base/audio/music/reference/ (proveniencia no\n"
                " * README.md). 4 canais PSG (" + vozes + " /\n"
                " * percussao de ruido); a lib repete sozinha no PSGEnd.\n"
                " * NAO editar a mao — regenerar pelo script. */\n")
        f.write(f"#define {symbol.upper()}_SIZE {len(data)}\n")
        f.write(f"static const unsigned char {symbol}[{len(data)}] = {{\n")
        for i in range(0, len(data), 16):
            f.write(",".join(f"0x{b:02X}" for b in data[i:i + 16]) + ",\n")
        f.write("};\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--wav")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()

    ref, opt, data, total = make()
    bars_n, harmony, releases, decays, sparse = opt

    relatorio = (f"{ref.bpm} BPM, {ref.tpqn} TPQN; melodia cobre "
                 f"{ref.mel_bars} compassos, periodo detectado "
                 f"{ref.mel_period}, total {ref.total_bars}; serializado "
                 f"{bars_n} compasso(s) a partir do compasso "
                 f"{ref.mel_start}; notas: melodia {len(ref.mel_notes)}, "
                 f"harmonia {len(ref.harm_notes)} "
                 f"({'ativa' if harmony else 'cortada'}), "
                 f"baixo {len(ref.bass_notes)}, percussao {len(ref.perc)} hits")

    if args.self_check:
        assert data[-1] == END, "fluxo precisa terminar em PSGEnd"
        assert END not in data[:-1], "PSGEnd prematuro no meio do fluxo"
        # nenhum byte de dado pode cair na faixa de comando 0x01..0x37
        i, seen = 0, 0
        while i < len(data) - 1:
            b = data[i]
            if WAIT <= b <= 0x3F:
                seen += (b & 7) + 1
                i += 1
            elif b & 0x80 and not (b & 0x10) and ((b >> 5) & 3) != 3:
                assert data[i + 1] >= 0x40, f"byte alto sem 0x40 em {i}"
                i += 2
            else:
                assert b >= 0x80, (f"byte de dado invadiu faixa de comando: "
                                   f"0x{b:02X}@{i}")
                i += 1
        assert seen == total, f"frames somam {seen}, esperado {total}"
        assert len(data) <= BUDGET, f"fluxo {len(data)} B estoura {BUDGET} B"
        print(f"[SELF-CHECK OK] gen_music_ken_ref: {len(data)} B, "
              f"{total} frames ({total / FPS:.1f}s)")
        print("[SELF-CHECK] " + relatorio)
        return 0

    print(f"stream: {len(data)} bytes de {BUDGET} (sobram {BUDGET - len(data)}), "
          f"{total} frames = {total / FPS:.2f}s")
    print("variante escolhida (compassos, harmonia, release, decaimento, "
          "perc enxuta): " + str(opt))
    print("referencia: " + relatorio)
    if args.wav:
        dur = render_wav(args.wav, data)
        print(f"wav: {args.wav} ({dur:.2f}s)")
    if args.emit:
        raw = os.path.join(PROJ, "res", "audio")
        os.makedirs(raw, exist_ok=True)
        with open(os.path.join(raw, "music_ken_stage.psg"), "wb") as f:
            f.write(data)
        # espelho: mesmo conteudo, nome historico usado pelo fluxo shrink
        with open(os.path.join(raw, "music_battle.psg"), "wb") as f:
            f.write(data)
        out = os.path.join(PROJ, "inc", "music_battle.h")
        write_header(out, "music_battle", data, harmony)
        print(f"emit: {out} + res/audio/music_ken_stage.psg "
              f"+ res/audio/music_battle.psg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
