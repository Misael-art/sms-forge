#!/usr/bin/env python3
"""Gate RECURSOS — valida PNGs contra o contrato visual SMS.

Reprova:
- PNG fora do grid 8x8 (BG) ou tamanho fora de {8x8,16x16} (sprite)
- cor fora dos codigos 6-bit (contrato canal*85)
- >15 cores uteis por subpaleta (indice 0 = transparente, nao conta como util)
- indice 0 opaco (sem tRNS)
- folha de sprite com cor usada fora da paleta declarada do personagem

Uso: audit_validate_resources.py --project <dir> [--kind bg|sprite|sheet] <png...>
     audit_validate_resources.py --project <dir> --character <id> --kind sheet <png...>
     audit_validate_resources.py --self-check
Exit: 0 aprova | 1 reprova (gate funcionou) | 3 uso invalido
"""
import sys, os, argparse, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png_io import read_indexed_png, PngError
import sms_palette as pal

MAX_USEFUL = 15
SPRITE_RESOURCE_GEOMETRIES = {(8, 8), (8, 16), (16, 16)}

def check_png(path, kind, character_colors=None):
    errors = []
    try:
        img = read_indexed_png(path)
    except PngError as e:
        return [str(e)]
    w, h = img["w"], img["h"]
    if w % 8 or h % 8:
        errors.append(f"grid 8x8 violado: {w}x{h}")
    if kind == "sprite" and (w, h) not in SPRITE_RESOURCE_GEOMETRIES:
        errors.append(f"sprite {w}x{h} fora de {{8x8,8x16,16x16}}")
    else:
        errors += _palette_errors(path, img)
    if character_colors is not None:
        errors += _character_palette_errors(path, img, character_colors)
    return errors

def _palette_errors(path, img):
    errors = []
    plte = img["palette"] or []
    for idx, rgb in enumerate(plte):
        if not pal.is_contract_color(tuple(rgb)):
            errors.append(f"{path}: paleta[{idx}] rgb{tuple(rgb)} fora dos codigos 6-bit "
                          f"(mais proximo: {pal.nearest_code(tuple(rgb))})")
    used = set()
    for row in img["pixels"]:
        used.update(row)
    useful = len([i for i in used if i != 0])
    if useful > MAX_USEFUL:
        errors.append(f"{path}: {useful} cores uteis > {MAX_USEFUL} (indice 0 nao conta)")
    if 0 not in img["trns"]:
        errors.append(f"{path}: indice 0 deve ser transparente (tRNS)")
    return errors

def _character_palette_errors(path, img, allowed_colors):
    used = set()
    for row in img["pixels"]:
        used.update(row)
    used.discard(0)
    palette = img["palette"] or []
    actual = {tuple(palette[i]) for i in used if i < len(palette)}
    outside = sorted(actual - set(allowed_colors))
    if outside:
        return [f"{path}: cores usadas fora da paleta declarada do personagem: {outside}"]
    return []

def _load_character_colors(project, character):
    manifest = os.path.join(project, "doc", "palettes_manifest.json")
    with open(manifest, encoding="utf-8") as f:
        data = json.load(f)
    entry = (data.get("characters") or {}).get(character)
    if not entry:
        raise ValueError(f"personagem '{character}' nao existe em {manifest}")
    colors = entry.get("colors") or []
    allowed = {tuple(c["rgb"]) for c in colors if isinstance(c.get("rgb"), list)}
    if not allowed:
        raise ValueError(f"personagem '{character}' sem RGBs em {manifest}")
    return allowed

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--kind", choices=("bg", "sprite", "sheet"), default="bg")
    ap.add_argument("--character", help="confere as cores usadas com doc/palettes_manifest.json")
    ap.add_argument("pngs", nargs="*")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()

    if args.self_check:
        import tempfile
        from png_io import write_indexed_png
        good_codes = ((3, 1, 0), (1, 0, 0), (2, 0, 0), (3, 3, 3), (3, 0, 0),
                      (1, 1, 1), (2, 2, 2), (1, 1, 0), (2, 1, 0), (3, 2, 2),
                      (2, 1, 1), (1, 0, 1), (3, 2, 1), (3, 1, 1), (0, 1, 0))
        good = [(0, 0, 0)] + [pal.code_rgb(c) for c in good_codes]
        px = [bytes(x % 16 for x in range(320)) for _ in range(240)]
        d = tempfile.mkdtemp(prefix="smsres_")
        okp = os.path.join(d, "ok_sheet.png"); write_indexed_png(okp, 320, 240, good, px)
        badp = os.path.join(d, "bad.png"); write_indexed_png(badp, 250, 100, good, [bytes([1] * 250)] * 100)
        offgridp = os.path.join(d, "offgrid.png")
        write_indexed_png(offgridp, 8, 8, [(0, 0, 0), (128, 64, 32)], [bytes([1] * 8)] * 8)
        many_colors = [(0, 0, 0)] + [pal.code_rgb((i & 3, (i >> 2) & 3, (i >> 4) & 3)) for i in range(1, 17)]
        many_color_rows = [bytes(1 + (x % 16) for x in range(320)) for _ in range(240)]
        many_colorp = os.path.join(d, "too_many.png")
        write_indexed_png(many_colorp, 320, 240, many_colors, many_color_rows)
        e1 = check_png(okp, "sheet", {pal.code_rgb(c) for c in good_codes})
        e2 = check_png(badp, "sheet")
        e3 = check_png(offgridp, "sheet")
        e4 = check_png(many_colorp, "sheet")
        e5 = check_png(okp, "sheet", {pal.code_rgb(c) for c in good_codes[:-1]})
        tall_sprite = os.path.join(d, "valid_sprite_8x16.png")
        write_indexed_png(tall_sprite, 8, 16, good,
                          [bytes([1] * 8) for _ in range(16)])
        e6 = check_png(tall_sprite, "sprite")
        assert not e1, f"self-check falhou em fixture valida: {e1}"
        assert any("grid" in x for x in e2), "self-check: gate nao reprovou grid invalido"
        assert any("fora dos codigos 6-bit" in x for x in e3), "self-check: gate nao reprovou cor fora do grid SMS"
        assert any("cores uteis > 15" in x for x in e4), "self-check: gate nao reprovou mais de 15 cores uteis"
        assert any("fora da paleta declarada" in x for x in e5), "self-check: gate nao reprovou paleta de personagem divergente"
        assert not e6, f"sprite SMS 8x16 válido não deveria reprovar: {e6}"
        print("[SELF-CHECK OK] validate_resources: sheet, sprite 8x8/8x16/16x16, grid, 6-bit, limite 15 e paleta de personagem")
        return 0

    if not args.pngs:
        print("[FAIL] nenhum PNG informado", file=sys.stderr)
        return 3
    character_colors = None
    if args.character:
        try:
            character_colors = _load_character_colors(args.project, args.character)
        except (OSError, ValueError, json.JSONDecodeError) as e:
            print(f"[FAIL] manifesto de paleta: {e}", file=sys.stderr)
            return 3
    all_errors = []
    for p in args.pngs:
        all_errors += check_png(p, args.kind, character_colors)
    if all_errors:
        for e in all_errors:
            print(f"[FAIL] {e}")
        return 1
    print(f"[PASS] {len(args.pngs)} PNG(s) dentro do contrato")
    return 0

if __name__ == "__main__":
    sys.exit(main())
