#!/usr/bin/env python3
"""gen_pulso_music.py — partitura autoral JSON -> fluxo PSGlib, com piso medido.

Superficie de composicao do projeto: o musico (agente/humano) escreve NOTES,
envelopes e papeis de canal em `tools/partitura/*.json`; este emissor e
deterministico e serializa cada compasso em frames de VBlank no formato cru
PSGlib (latch >=0x80, dados 0x40..0x7F, WAIT 0x38+hold<=7, END 0x00).

Nao reinventa a fisica nem o contrato:
  - codificacao/periodos/render: importados de tools/sms_wrapper/make_psg_assets
    (precedente de gerador que honra o proprio piso);
  - o MESMO auditor do gate (`audit_psg_quality`) roda sobre o binario emitido:
    assert viol==0 antes de gravar qualquer .psg (L079: o claim e do stream).

Economia L080: latch so quando o valor MUDA (muda de nota/att); sustencao e
release viram eventos vol-only; esperas viram um byte ate 8 frames.

Uso:
  gen_pulso_music.py --self-check
  gen_pulso_music.py --all                 # emite todas as partituras
  gen_pulso_music.py --emit <partitura.json> [...]
  gen_pulso_music.py --wav <dir> [--all]   # pre-escuta numpy (nao substitui emulador)
Exit: 0 ok | 1 reprova no piso | 3 uso/entrada invalida
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
# raiz do wrapper compartilhado: SMS_projects/<proj>/tools -> repo/tools/sms_wrapper
WRAPPER = os.path.abspath(os.path.join(PROJECT, os.pardir, os.pardir,
                                       "tools", "sms_wrapper"))
sys.path.insert(0, WRAPPER)
import audit_psg_quality as aq          # noqa: E402  (o piso, medido no binario)
import make_psg_assets as mpa           # noqa: E402  (tone/stream_of/render_wav/nota/reuse)

PARTITURA_DIR = os.path.join(HERE, "partitura")
BUDGET_BYTES = 2048                      # teto de stream musical (precedente make_psg_assets)


def frames_por_passo(meta):
    """16avos -> frames de VBlank. >=2 por clausula M1 do proprio contrato."""
    fps = int(meta.get("fps", 60))
    bpm = int(meta["bpm"])
    return max(2, int(round(fps * 60.0 / (bpm * 4.0))))


def _period(nome):
    return mpa._hz_to_period(mpa.note(nome))


def vol(ch, att):
    return mpa.vol_only(ch, att)


def build_sfx(part):
    """Partitura de SFX (meta.tipo=='sfx') -> fluxo curto no canal declarado.

    Eventos em frames ABSOLUTOS; o ultimo deve ir a mudo (att 15) — S1 exige
    que termine mais baixo do que comeca, e gate PSGlib precisa do fade para
    nao cortar em clique. Canal 3 e proibido (TDD/arbitracao L041: SFX nunca
    no ruido, que pertence a musica)."""
    meta = part["meta"]
    ch = int(meta["canal"])
    assert ch in (1, 2), "SFX no canal %d — arbitration: apenas 1/2 (ch3 e da musica)" % ch
    ev = {}
    total = 0
    for e in part["eventos"]:
        f = int(e["f"])
        att = int(e["att"])
        if "nota" in e:
            data = mpa.tone(_period(e["nota"]), ch, att)
        else:
            data = vol(ch, att)
        ev.setdefault(f, []).extend(data)
        total = max(total, f + 1)
    blob = mpa.stream_of(ev, total)
    return blob


def _sfx_ends_mute(blob, ch):
    """O ultimo evento de volume do canal e mudo (S1 sem corte seco)."""
    events, _dur = aq.decode(blob)
    vs = [v for (_t, k, c, v) in events if k == 'v' and c == ch]
    return bool(vs) and vs[-1] == 15


def build_stream(part):
    """partitura dict -> bytes PSGlib. So dados: nada de aleatorio, nada de
    relogio de runtime — 1 execugao = 1 byte-exact blob."""
    meta = part["meta"]
    fp = frames_por_passo(meta)
    env = part["envelopes"]
    lead_env, arp_env, bass_env, perc_env = (env["lead"], env["arpejo"],
                                             env["baixo"], env["percussao"])
    ev = {}
    collisions = []

    def put(f, data):
        ev.setdefault(f, []).extend(data)

    compassos = part["compassos"]
    total = len(compassos) * 16 * fp

    for bi, bar in enumerate(compassos):
        base = bi * 16 * fp
        din = dict(lead_env)
        din.update(bar.get("dinamica", {}))

        # --- ch0 lead: ataque -> sustentacao -> release (mudo) ---
        for mel in bar.get("melodia", ()):
            pos, nome, dur = mel[0], mel[1], mel[2]
            f = base + pos * fp
            atk = mel[3] if len(mel) > 3 else din["ataque"]
            sus = mel[4] if len(mel) > 4 else din["sustentacao"]
            put(f, mpa.tone(_period(nome), 0, atk))
            f_end = f + dur * fp
            f_sus = min(f + int(din.get("soltura_frames", 3)), f_end - 1)
            if f_sus != f:
                put(f_sus, vol(0, sus))
            put(min(f_end, total - 1), vol(0, 15))

        # --- ch1 arpejo multiplexado: 2-3 frames/nota ~20-30 Hz (tecnica L078)
        q = int(arp_env["quadros_por_nota"])
        if bar.get("arpejo") and q >= aq.GAP_MIN:
            notas = bar["acorde"]
            ataques = arp_env["ataques"]
            for i, f in enumerate(range(base, base + 16 * fp, q)):
                put(f, mpa.tone(_period(notas[i % len(notas)]), 1,
                                 ataques[i % len(ataques)]))
            put(min(base + 16 * fp, total - 1), vol(1, 15))
        elif bar.get("arpejo"):
            collisions.append("arpejo q=%d < M1 %.1f" % (q, aq.GAP_MIN))

        # --- ch2 baixo pizzicato: ataque curto, decay, mudo ---
        for bs in bar.get("baixo", ()):
            pos, nome = bs[0], bs[1]
            f = base + pos * fp
            put(f, mpa.tone(_period(nome), 2, bass_env["ataque"]))
            put(f + int(bass_env["decay_frames"]), vol(2, bass_env["decay_att"]))
            put(min(f + int(bass_env["mudo_frames"]), total - 1), vol(2, 15))

        # --- ch3 percussao branca gateada: hit -> decay -> mudo ---
        for pc in bar.get("percussao", ()):
            pos, tipo = pc[0], pc[1]
            cfg = perc_env[tipo]
            f = base + pos * fp
            # Latch 0xE0|mode: bit2=1 e ruido BRANCO, bit2=0 e periodico
            # (assobio). A percussao do GDD e branca — mascara 0x07 preserva
            # o bit, 0x03 o apagava (§64/L128: registrador mal lido vira
            # defeito audivel).
            assert cfg["shift"] & 0x04, \
                "percussao exige ruido branco (bit2=1); shift=%d" % cfg["shift"]
            put(f, [0xE0 | (cfg["shift"] & 0x07)] + vol(3, cfg["att"]))
            put(min(f + int(cfg["decay"]), total - 1), vol(3, 15))

    blob = mpa.stream_of(ev, total)
    return blob, collisions


def validate(nome, blob):
    """O gate roda sobre o binario ANTES de existir em disco (L079)."""
    events, dur = aq.decode(blob)
    viol, warn, m = aq.analyze(events, dur)
    return viol, warn, m, dur


def validate_sfx(blob, ch):
    events, dur = aq.decode(blob)
    viol, warn = aq.analyze_sfx(events, dur)
    wrong = sorted({c for (_t, k, c, _v) in events if k == 'f' and c != ch})
    if wrong:
        viol = viol + ['canal: eventos de tone em %s, canal autorizado e ch%d'
                       % (wrong, ch)]
    if not _sfx_ends_mute(blob, ch):
        viol = viol + ['S1: ultimo volume do canal nao e mudo (corta em clique)']
    return viol, warn, dur


def manifest_entry(path_rel, blob, part, dur):
    meta = part["meta"]
    if meta.get("tipo") == "sfx":
        channels = "SFX_CHANNEL%d" % int(meta["canal"])
    else:
        channels = "music channels 0-3"
    return {
        "file": path_rel,
        "origin": "partitura autoral original emitida por gen_pulso_music.py",
        "author": "pulso_de_cristal (composicao autoral do agente)",
        "tool": "tools/gen_pulso_music.py",
        "partitura": os.path.relpath(
            os.path.join(PARTITURA_DIR, meta["nome"] + ".json"),
            PROJECT).replace(os.sep, "/"),
        "role": meta.get("cena", ""),
        "channels": channels,
        "frames": dur,
        "sha256": hashlib.sha256(blob).hexdigest(),
        "bytes": len(blob),
        "format": "PSGlib stream",
    }


def merge_manifest(entry):
    """Merge por campo 'file' (precedente make_psg_assets) — preserva
    proveniencia de entradas que este emissor nao conhece."""
    path = os.path.join(PROJECT, "doc", "audio_provenance_manifest.json")
    manifest = []
    if os.path.exists(path):
        loaded = json.load(open(path, encoding="utf-8"))
        if isinstance(loaded, dict):
            manifest = [a for a in loaded.get("assets", [])
                        if isinstance(a, dict) and "file" in a]
    for i, existente in enumerate(manifest):
        if existente["file"] == entry["file"]:
            manifest[i] = entry
            break
    else:
        manifest.append(entry)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"assets": manifest}, open(path, "w", encoding="utf-8"), indent=2)


def emit(part_path, quiet=False):
    part = json.load(open(part_path, encoding="utf-8"))
    nome = part["meta"]["nome"]
    if part["meta"].get("tipo") == "sfx":
        ch = int(part["meta"]["canal"])
        blob = build_sfx(part)
        viol, warn, dur = validate_sfx(blob, ch)
        if viol:
            print("[REPROVA] %s no piso de SFX (nao gravado): %s" % (nome, viol))
            return None
        if dur > aq.SFX_MAX_FRAMES:
            print("[REPROVA] %s: %df > %d (S2)" % (nome, dur, aq.SFX_MAX_FRAMES))
            return None
    else:
        blob, collisions = build_stream(part)
        if collisions:
            print("[FAIL] %s: %s" % (nome, collisions))
            return None
        viol, warn, m, dur = validate(nome, blob)
        if viol:
            print("[REPROVA] %s no piso de qualidade (nao gravado):" % nome)
            for v in viol:
                print("    VIOLACAO %s" % v)
            return None
    if len(blob) > BUDGET_BYTES:
        print("[REPROVA] %s: %dB > orcamento %dB" % (nome, len(blob),
                                                      BUDGET_BYTES))
        return None
    audio = os.path.join(PROJECT, "res", "audio")
    inc = os.path.join(PROJECT, "inc")
    os.makedirs(audio, exist_ok=True)
    os.makedirs(inc, exist_ok=True)
    psg = os.path.join(audio, nome + ".psg")
    open(psg, "wb").write(blob)
    mpa.write_header(os.path.join(inc, nome + ".h"), nome, blob)
    merge_manifest(manifest_entry(
        os.path.relpath(psg, PROJECT).replace(os.sep, "/"), blob, part, dur))
    if not quiet:
        if part["meta"].get("tipo") == "sfx":
            print("[OK] %s %dB dur=%df canal=%d (S1 decaimento/S2 <=%d ok)"
                  % (nome, len(blob), dur, int(part["meta"]["canal"]),
                     aq.SFX_MAX_FRAMES))
        else:
            print("[OK] %s %dB dur=%df unison=%s respira=ch%d(gap %.1f) ruidoB=%s"
                  % (nome, len(blob), dur, m.get("unison"),
                     m.get("camada_respira", {}).get("ch", -1),
                     m.get("camada_respira", {}).get("gap", 0.0),
                     m.get("ruido_branco", "—")))
        for w in warn:
            print("    aviso %s" % w)
    return blob


def all_partituras():
    return sorted(os.path.join(PARTITURA_DIR, f)
                  for f in os.listdir(PARTITURA_DIR) if f.endswith(".json"))


def determinism_check(part_path):
    b1, _ = build_stream(json.load(open(part_path, encoding="utf-8")))
    b2, _ = build_stream(json.load(open(part_path, encoding="utf-8")))
    assert b1 == b2, "emissor nao deterministico: %s" % part_path
    return b1


def self_check():
    ok = []
    # 1. periodo round-trip pela fisica do precedente
    ok.append(("periodo round-trip via decode",
               aq.decode(mpa.stream_of({0: mpa.tone(_period("A4"), 0, 2)},
                                       1)) [0][0][3] == _period("A4")))
    # 2. nota fora do SN76489 reprova no ato de emitir (nao silencia). O piso
    # fisico e period 16..1023 (§64/L128): A2=110 Hz (period 1017) e legal;
    # A1=55 Hz (period 2035) nao.
    try:
        mpa._hz_to_period(mpa.note("A1"))
        ok.append(("grave A1 acima de period 1023 e bloqueado", False))
    except AssertionError:
        ok.append(("grave A1 acima de period 1023 e bloqueado", True))
    ok.append(("grave A2 (110 Hz) e aceito",
               mpa._hz_to_period(mpa.note("A2")) == 1017))
    # 3. percussao periodica e bloqueada por construcao (§64: bit2=0 = assobio)
    part = json.load(open(all_partituras()[0], encoding="utf-8")) \
        if all_partituras() else None
    ok.append(("ha ao menos uma partitura para check", part is not None))
    if part:
        bad = json.loads(json.dumps(part))
        bad["envelopes"]["percussao"]["bumbo"]["shift"] = 3
        try:
            build_stream(bad)
            ok.append(("shift periodico vira FAIL", False))
        except AssertionError:
            ok.append(("shift periodico vira FAIL", True))
        good = json.loads(json.dumps(part))
        for env in good["envelopes"]["percussao"].values():
            env["shift"] |= 0x04
        blob, _cl = build_stream(good)
        _v, _w, m, _d = validate("selfcheck", blob)
        ok.append(("shift com bit2 vira ruido branco (m=1.0)",
                   m.get("ruido_branco") == 1.0))
    # 4. todas as partituras: deterministicas, dentro do piso, dentro do budget
    for pp in all_partituras():
        part = json.load(open(pp, encoding="utf-8"))
        nome = os.path.basename(pp)[:-5]
        if part["meta"].get("tipo") == "sfx":
            ch = int(part["meta"]["canal"])
            b1 = build_sfx(part)
            b2 = build_sfx(json.load(open(pp, encoding="utf-8")))
            ok.append(("%s sfx deterministico" % nome, b1 == b2))
            viol, _w, dur = validate_sfx(b1, ch)
            ok.append(("%s passa no piso SFX" % nome, viol == []))
            ok.append(("%s dur=%d <= S2 %d" % (nome, dur, aq.SFX_MAX_FRAMES),
                       dur <= aq.SFX_MAX_FRAMES))
            ok.append(("%s budget<=2048 (%dB)" % (nome, len(b1)),
                       len(b1) <= BUDGET_BYTES))
            continue
        blob = determinism_check(pp)
        viol, _w, m, dur = validate(nome, blob)
        ok.append(("%s passa no piso" % nome, viol == []))
        ok.append(("%s loop>=250 (dur=%d)" % (nome, dur), dur >= aq.LOOP_MIN))
        ok.append(("%s budget<=2048 (%dB)" % (nome, len(blob)),
                   len(blob) <= BUDGET_BYTES))
        # 5. M7 por construcao: a camada que respira e o lead (melodia), nao
        # o recheio — gap medio do ch0 >= BREATH_MIN
        ok.append(("%s lead respira (M7>=8f)" % nome,
                   m.get("gap_medio", {}).get(0, 0) >= aq.BREATH_MIN))
    for nome, bom in ok:
        print("  %-48s %s" % (nome, "ok" if bom else "FALHOU"))
    if not all(b for _, b in ok):
        print("[SELF-CHECK FAIL] gen_pulso_music")
        return 1
    print("[SELF-CHECK OK] gen_pulso_music (determinismo + piso audit_psg "
          "no binario + budget + M7 no lead)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--wav", metavar="DIR")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return self_check()
    paths = list(args.emit or [])
    if args.all:
        paths += all_partituras()
    if not paths:
        print("[FAIL_USO] --emit/--all/--self-check")
        return 3
    blobs = {}
    for pp in paths:
        blob = emit(pp)
        if blob is None:
            return 1
        nome = json.load(open(pp, encoding="utf-8"))["meta"]["nome"]
        blobs[nome] = (blob, json.load(open(pp, encoding="utf-8")))
    if args.wav:
        os.makedirs(args.wav, exist_ok=True)
        for nome, (blob, part) in blobs.items():
            out = os.path.join(args.wav, nome + ".wav")
            d = mpa.render_wav(out, blob,
                               fps=int(part["meta"].get("fps", 60)))
            print("[WAV] %s (%.1fs — pre-escuta numpy; o gate e o emulador)"
                  % (out, d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
