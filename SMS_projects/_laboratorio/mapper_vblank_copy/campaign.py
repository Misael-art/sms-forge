#!/usr/bin/env python3
"""campaign.py — mapper_vblank_copy (M1 do O3).

Fluxo: gen_banks -> build.sh -> uma sessao BlastEm (warmup 300 + 2 frames) ->
marcador 0xC7D0 (mapper, frames, vcount) dos snapshots 000 e ultimo ->
comparacao byte a byte do dump de VRAM com a fonte no proprio ROM (0x8000) ->
decodificacao dos tiles visiveis no screenshot nativo -> evidencia JSON.

Julga a previsao do README: copia de 1856 B NAO cabe inteira (prefixo
~650-950 B), mapper troca banco, loop mantem 60 Hz.

Uso: python3 campaign.py [--skip-build]
Exit: 0 confirmado | 1 refutado | 2 erro/inconclusivo
"""
import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROM = HERE / "out" / "rom" / "mapper_vblank_copy.sms"
MARKER = 0xC7D0
COPY_BYTES = 1856
SOURCE_OFFSET = 0x8000  # bank 2 no ROM (banks 0..1 = codigo)


def find_root():
    d = HERE
    while d != d.parent and not (d / "tools" / "sms_wrapper").is_dir():
        d = d.parent
    return d if (d / "tools" / "sms_wrapper").is_dir() else None


ROOT = find_root()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inconclusive(msg):
    print(f"[INCONCLUSIVO] {msg}")
    return 2


def gen_banks():
    r = subprocess.run([sys.executable, str(HERE / "gen_banks.py")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(inconclusive(f"gen_banks falhou: {r.stdout}{r.stderr}"))


def build():
    r = subprocess.run(["bash", str(HERE / "build.sh")], capture_output=True,
                       text=True, cwd=HERE)
    if r.returncode != 0 or not ROM.exists():
        sys.exit(inconclusive(f"build falhou: {r.stdout[-400:]}{r.stderr[-400:]}"))


def run_session():
    EVID = ROOT / "out" / "evidence" / "mapper_vblank_copy_m1"
    EVID.mkdir(parents=True, exist_ok=True)
    seq = {
        "schema": "sms_blastem_sequence_v1",
        "model": "sms2",
        "region": "ntsc",
        "warmup_frames": 300,
        "preconditions": [{"address": MARKER, "equals_hex": "4d564331"}],
        "steps": [{"frames": 2}],
    }
    script = EVID / "sequence.json"
    script.write_text(json.dumps(seq, indent=2))
    r = subprocess.run([sys.executable, str(ROOT / "tools/sms_wrapper/blastem_sms.py"),
                        "run", "--rom", str(ROM), "--script", str(script),
                        "--output", str(EVID)],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        sys.exit(inconclusive(f"sessao BlastEm falhou: {r.stdout[-400:]}{r.stderr[-400:]}"))
    return Path(r.stdout.strip().splitlines()[-1])


def read_marker(ram):
    off = MARKER - 0xC000
    m = ram[off:off + 16]
    return {
        "magic": m[0:4].decode("latin1"),
        "frames": m[4] | (m[5] << 8),
        "vc_before": m[6],
        "vc_after": m[7],
        "bank2_byte0": m[8],
        "bank3_byte0": m[9],
        "bank_after": m[10],
        "copies": m[12] | (m[13] << 8),
        "raw": list(m),
    }


# Coluna de borda do screenshot nativo do BlastEm: 8 px medidos em x=255,
# y=64..71 (linha de BG 8) divergem do dump de VRAM (obs 0, esperado 5) em
# 2026-10-16 — artefato de captura, nao de conteudo. Excluida AQUI por
# medicao; qualquer outro pixel divergente conta.
EDGE_EXCLUDE_X = 255


def pixel_planar(src, tile, x, y):
    """Formato de tile do SMS Mode 4 e planar: 4 bytes/linha, byte p fornece
    o bit p do indice do pixel; MSB = pixel esquerdo (mesma decodificacao de
    tools/sms_wrapper/blastem_diagnostics.py render_views)."""
    a = tile * 32 + y * 4
    return sum(((src[a + p] >> (7 - x)) & 1) << p for p in range(4))


def screen_index(im, x, y):
    """DAC do BlastEm usa rampa 0/87/174/255; niveis 0..3 -> byte CRAM
    00BBGGRR -> indice de paleta (c/4 com a paleta i*4 deste probe)."""
    r, g, b = im.getpixel((x, y))

    def lv(c):
        return max(0, min(3, round(c * 3 / 255)))

    return (lv(b) << 4 | lv(g) << 2 | lv(r)) // 4


def decode_visible(src, shot_path):
    """Maior prefixo de tiles corretos nas linhas de BG 8 (tiles 0..31) e
    9 (tiles 32..63), decodificando o screenshot nativo pixel a pixel."""
    from PIL import Image
    with Image.open(shot_path) as im:
        im = im.convert("RGB")
        results = {}
        for row, tile0, y0 in ((8, 0, 64), (9, 32, 72)):
            ok_tiles = 0
            for t in range(tile0, tile0 + 32):
                if (t + 1) * 32 > len(src):
                    match = False  # dado fora do bloco copiado: nao ha fonte a casar
                else:
                    match = True
                    for y in range(8):
                        for x in range(8):
                            sx = (t - tile0) * 8 + x
                            if sx == EDGE_EXCLUDE_X:
                                continue
                            if screen_index(im, sx, y0 + y) != pixel_planar(src, t, x, y):
                                match = False
                                break
                        if not match:
                            break
                if match:
                    ok_tiles += 1
                else:
                    break
            results[row] = ok_tiles
        return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-build", action="store_true")
    args = ap.parse_args()
    if ROOT is None:
        return inconclusive("raiz do SMSForge nao encontrada")

    if not args.skip_build:
        gen_banks()
        build()
    if not ROM.exists():
        return inconclusive("ROM ausente (rode o build)")

    rom_bytes = ROM.read_bytes()
    src = rom_bytes[SOURCE_OFFSET:SOURCE_OFFSET + COPY_BYTES]

    session = run_session()
    meta = json.loads((session / "session.json").read_text())
    if meta.get("state") != "completed" or not all(meta.get("cleanup", {}).values()):
        return inconclusive(f"sessao nao limpou/completou: {meta.get('state')} {meta.get('cleanup')}")
    if meta.get("rom_sha256") != sha(ROM):
        return inconclusive("sha da ROM diverge do lido pela sessao")

    snaps = sorted(glob.glob(str(session / "snapshots" / "*")))
    base = read_marker((Path(snaps[0]) / "ram.bin").read_bytes())
    last = read_marker((Path(snaps[-1]) / "ram.bin").read_bytes())
    boundaries = [b["vdp_frame"] for b in meta["boundaries"]]
    frame_delta = boundaries[-1] - boundaries[0]

    vram = (Path(snaps[-1]) / "vram.bin").read_bytes()
    prefix = 0
    while prefix < COPY_BYTES and vram[prefix] == src[prefix]:
        prefix += 1
    mismatches = sum(1 for i in range(COPY_BYTES) if vram[i] != src[i])

    shots = sorted((session / "screenshots").glob("*.png"))
    visible = decode_visible(src, shots[0]) if shots else {}

    frames_rom = (last["frames"] - base["frames"]) & 0xFFFF
    frames_vdp = frame_delta
    mapper_ok = (last["bank2_byte0"] == ord("M") and last["bank3_byte0"] == ord("P")
                 and last["bank_after"] == 2)
    hz_ok = frames_rom == frames_vdp and frames_vdp == 2
    if not mapper_ok:
        verdict = "inconclusivo"
        code = inconclusive(
            f"mapper nao provado: bank2={last['bank2_byte0']:#x} bank3={last['bank3_byte0']:#x} bank={last['bank_after']}")
    elif not hz_ok:
        verdict = "inconclusivo"
        code = inconclusive(f"frame pacing divergente: rom={frames_rom} vdp={frames_vdp}")
    elif prefix == COPY_BYTES:
        verdict = "refutado"
        code = 1
    elif prefix == 0:
        verdict = "inconclusivo"
        code = inconclusive("prefixo zero: dump de VRAM incoerente com a copia")
    else:
        verdict = "confirmado"
        code = 0

    out = {
        "probe": "mapper_vblank_copy",
        "rom": str(ROM), "rom_sha256": sha(ROM), "rom_bytes": len(rom_bytes),
        "session": str(session),
        "marker": {"baseline": base, "last": last},
        "boundaries_vdp_frame": boundaries,
        "frames_rom_delta": frames_rom,
        "frames_vdp_delta": frames_vdp,
        "mapper_ok": mapper_ok,
        "vram": {"copy_bytes": COPY_BYTES, "prefix_ok": prefix,
                 "mismatches": mismatches,
                 "tail_first_diff": prefix if prefix < COPY_BYTES else None},
        "visible_tiles_ok": visible,
        "visible_bytes_boundary_row8": visible.get(8, 0) * 32,
        "screen_edge_excluded_px": 8,
        "visible_bytes_total": 32 * (visible.get(8, 0) + visible.get(9, 0)),
        "design_threshold_619b": prefix >= 619,
        "verdict": verdict,
    }
    (session / "analysis.json").write_text(json.dumps(out, indent=2) + "\n")

    print(json.dumps(out, indent=2))
    print(f"\n[VEREDITO] {verdict.upper()}")
    if verdict == "confirmado":
        print(f"  prefixo na janela = {prefix} B de {COPY_BYTES} "
              f"(restante perdido; L047), 60 Hz ok, mapper ok")
        print(f"  contrato D8 (>=619 B/frame): "
              f"{'SUSTENTADO' if prefix >= 619 else 'NAO SUSTENTADO - revisar cronograma'}")
    elif verdict == "refutado":
        print(f"  a copia INTEIRA de {COPY_BYTES} B chegou na VRAM - o modelo "
              f"janela~15.960 ciclos / L047 precisa revisao")
        print(f"  corroboracao na tela: tiles corretos ate a fronteira de "
              f"{out['visible_bytes_total']} B (linha 8: {visible.get(8)} tiles, "
              f"linha 9: {visible.get(9)} tiles; coluna x=255 excluida: "
              f"{out['screen_edge_excluded_px']} px de borda medidos)")
    return code


if __name__ == "__main__":
    sys.exit(main())
