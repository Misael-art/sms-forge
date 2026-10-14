#!/usr/bin/env python3
"""Gate SPRITES/SCANLINE — simulador VDP de Master System.

Le um manifest JSON de cena (schema sprite_scene_manifest_v1) e reprova:
- >64 sprites ativos na SAT
- >8 entradas da SAT caindo na mesma scanline: o buffer de parsing do VDP tem 8
  entradas, preenchidas em ordem de SAT; da 9a em diante sao descartadas e o
  bit 6 do status e setado. Conta TODA entrada, inclusive `hidden` (transparente
  ou fora da tela) — §119, L129
- sprite com Y armazenado == 0xD0 no modo 192 linhas (colide com terminador da SAT)
- screen_h fora de {192, 224, 240} (modo de tela inexistente no VDP)
- sat_terminated declarado em 224/240: o terminador so existe no modo 192 (§118, L128)

Fisica aplicada (fonte: docs smspower/devkitSMS; leis em .agent/rules/SMS_GLOBAL.md):
- sprite_size global '8x8'|'8x16' (+ zoom opcional que DOBRA o footprint)
- `y` do manifesto e o Y passado a SMS_addSprite = primeira linha desenhada.
  A SMSlib grava stored_y = y - 1 (o VDP desenha em stored + 1), entao o Y que
  colide com o terminador 0xD0 e y = 0xD1 (a SMSlib o recusa com -2). Lastro:
  bytes de SMSlib_sprite em sdk/devkitSMS/SMSlib/SMSlib.lib + corpus Sprites.
- `sprites` esta em ordem de SAT. `hidden: true` marca entrada sem pixel visivel
  que a ROM mantem na SAT; ela ocupa buffer como qualquer outra.
- terminador 0xD0 so vale em 192 linhas; em 224/240 e um Y comum e o VDP percorre
  as 64 entradas (corpus smspower Sprites, hasheado; SMS_GLOBAL §118).

Uso: audit_sprite_line_sim.py <manifest.json> [--self-check]
Exit: 0 | 1 reprova | 3 uso
"""
import sys, json, argparse

SPRITE_H = {"8x8": 8, "8x16": 16}
SAT_MAX = 64
PER_LINE_MAX = 8
TERMINATOR_Y = 0xD0
TERMINATOR_SCREEN_H = 192
SCREEN_H_MODES = (192, 224, 240)

def contract_errors(manifest):
    """Validate declared entries before simulation; do not guess wrapped Y."""
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]
    errors = []
    size = manifest.get("sprite_size", "8x8")
    if not isinstance(size, str) or size not in SPRITE_H:
        errors.append("sprite_size must be hardware mode 8x8 or 8x16; wide art needs metasprites")
    for key in ("zoomed", "sat_terminated"):
        if key in manifest and type(manifest[key]) is not bool:
            errors.append(f"{key} must be boolean")
    screen_h = manifest.get("screen_h", 192)
    if type(screen_h) is not int or screen_h not in SCREEN_H_MODES:
        errors.append(f"screen_h {screen_h!r} fora dos modos do VDP {SCREEN_H_MODES}; integer required")
    sprites = manifest.get("sprites", [])
    if not isinstance(sprites, list):
        errors.append("sprites must be an array in SAT order")
        return errors
    for index, sprite in enumerate(sprites):
        if not isinstance(sprite, dict):
            errors.append(f"sprite {index}: entry must be an object")
            continue
        for key in ("x", "y", "tile"):
            value = sprite.get(key)
            if type(value) is not int or not 0 <= value <= 255:
                suffix = "; negative/wrapped Y is outside this profile" if key == "y" else ""
                errors.append(f"sprite {index}: {key} must be integer 0..255{suffix}")
        if "hidden" in sprite and type(sprite["hidden"]) is not bool:
            errors.append(f"sprite {index}: hidden must be boolean")
    return errors


def simulate(manifest):
    errors = contract_errors(manifest)
    if errors:
        count = len(manifest.get("sprites", [])) if isinstance(manifest, dict) and isinstance(manifest.get("sprites", []), list) else 0
        return {"sprites": count, "peak_per_line": 0, "overflow_lines": 0,
                "overflow": [], "violations": errors,
                "scope": "declared_SMSlib_entries_only; negative/wrapped_Y_not_modelled"}
    errors = []
    size = manifest.get("sprite_size", "8x8")
    zoom = manifest.get("zoomed", False)
    h = SPRITE_H[size] * (2 if zoom else 1)
    sprites = manifest.get("sprites", [])
    screen_h = manifest.get("screen_h", 192)
    if screen_h not in SCREEN_H_MODES:
        errors.append(f"screen_h {screen_h} fora dos modos do VDP {SCREEN_H_MODES}")
        return {"sprites": len(sprites), "peak_per_line": 0, "violations": errors}
    has_terminator = screen_h == TERMINATOR_SCREEN_H
    if manifest.get("sat_terminated") and not has_terminator:
        errors.append(f"sat_terminated declarado em {screen_h} linhas: 0xD0 so termina "
                      f"a SAT no modo 192; o VDP percorre as 64 entradas")
    if len(sprites) > SAT_MAX:
        errors.append(f"SAT overflow: {len(sprites)} sprites > {SAT_MAX}")
    lines = {}
    for index, s in enumerate(sprites):
        y, x = s["y"], s["x"]
        if has_terminator and (y - 1) & 0xFF == TERMINATOR_Y:
            errors.append(f"sprite em ({x},{y}): Y armazenado colide com terminador 0xD0")
        for ly in range(y, min(y + h, screen_h)):
            lines.setdefault(ly, []).append(index)
    hidden = {i for i, s in enumerate(sprites) if s.get("hidden")}
    overflow = []
    for ly, entries in sorted(lines.items()):
        if len(entries) <= PER_LINE_MAX:
            continue
        dropped = entries[PER_LINE_MAX:]
        overflow.append({"line": ly, "buffer": entries[:PER_LINE_MAX], "dropped": dropped,
                         "dropped_visible": [i for i in dropped if i not in hidden]})
    for row in overflow[:5]:
        lost = (f"visiveis descartados (SAT) {row['dropped_visible']}" if row["dropped_visible"]
                else "so entradas hidden descartadas")
        errors.append(f"scanline {row['line']}: {PER_LINE_MAX + len(row['dropped'])} entradas > "
                      f"{PER_LINE_MAX}; buffer cheio, overflow (status bit 6); {lost}")
    peak = max((len(v) for v in lines.values()), default=0)
    report = {"sprites": len(sprites), "peak_per_line": peak,
              "overflow_lines": len(overflow), "overflow": overflow[:5],
              "violations": errors}
    return report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", nargs="?")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        ok = {"sprite_size": "8x16", "zoomed": False,
              "sprites": [{"y": 10 + i * 20, "x": 40, "tile": i} for i in range(8)],
              "screen_h": 192}
        tall_pair = {"sprite_size": "8x16", "zoomed": False,
                     "sprites": [{"y": y, "x": fighter_x + col * 8,
                                  "tile": n & 0xFF}
                                 for fighter_x in (48, 176)
                                 for y in (96, 112, 128)
                                 for col in range(4)
                                 for n in (fighter_x + y + col,)],
                     "screen_h": 192}
        bad = {"sprite_size": "8x8",
               "sprites": [{"y": 50, "x": 16 + i * 4, "tile": i} for i in range(9)],
               "screen_h": 192}
        sat = {"sprite_size": "8x8",
               "sprites": [{"y": i % 192, "x": 40, "tile": 0} for i in range(65)],
               "screen_h": 192}
        d0 = [{"y": TERMINATOR_Y + 1, "x": 40, "tile": 0}]
        ghosts = [{"y": 50, "x": 0, "tile": 0, "hidden": True} for _ in range(8)]
        hero = [{"y": 50, "x": 120, "tile": 1}]
        r_ghost_first = simulate({"sprite_size": "8x8", "sprites": ghosts + hero, "screen_h": 192})
        r_hero_first = simulate({"sprite_size": "8x8", "sprites": hero + ghosts, "screen_h": 192})
        r_old_d0 = simulate({"sprite_size": "8x8", "screen_h": 192,
                             "sprites": [{"y": TERMINATOR_Y - 1, "x": 40, "tile": 0}]})
        r_ok, r_tall, r_bad, r_sat = (simulate(ok), simulate(tall_pair),
                                      simulate(bad), simulate(sat))
        r_d0_192 = simulate({"sprite_size": "8x8", "sprites": d0, "screen_h": 192})
        r_d0_224 = simulate({"sprite_size": "8x8", "sprites": d0, "screen_h": 224})
        r_trunc = simulate({"sprite_size": "8x8", "sprites": d0, "screen_h": 224,
                            "sat_terminated": True})
        r_mode = simulate({"sprite_size": "8x8", "sprites": [], "screen_h": 200})
        assert not r_ok["violations"], r_ok
        assert not r_tall["violations"] and r_tall["peak_per_line"] == 8, r_tall
        assert any("scanline" in v for v in r_bad["violations"]), r_bad
        assert any("SAT" in v for v in r_sat["violations"]), r_sat
        assert any("terminador" in v for v in r_d0_192["violations"]), r_d0_192
        assert not r_d0_224["violations"] and r_d0_224["peak_per_line"] == 1, r_d0_224
        assert any("sat_terminated" in v for v in r_trunc["violations"]), r_trunc
        assert any("screen_h" in v for v in r_mode["violations"]), r_mode
        # buffer-fill: 8 entradas hidden antes na SAT derrubam o sprite visivel
        assert r_ghost_first["overflow"][0]["dropped_visible"] == [8], r_ghost_first
        assert any("visiveis descartados" in v for v in r_ghost_first["violations"]), r_ghost_first
        assert r_hero_first["overflow"][0]["dropped_visible"] == [], r_hero_first
        assert any("so entradas hidden" in v for v in r_hero_first["violations"]), r_hero_first
        # stored = y - 1: y = 0xCF grava 0xCE e nao colide com o terminador
        assert not r_old_d0["violations"], r_old_d0
        import copy
        for malformed in (None, [], "bad", 1):
            assert simulate(malformed)["violations"], malformed
        for key, value in (("sprite_size", "16x16"), ("sprite_size", []),
                           ("screen_h", 192.0), ("screen_h", True),
                           ("zoomed", 1), ("sat_terminated", "false"),
                           ("sprites", {}), ("sprites", [None])):
            value_manifest = copy.deepcopy(ok)
            value_manifest[key] = value
            assert simulate(value_manifest)["violations"], value_manifest
        for key, value in (("y", -1), ("y", 256), ("y", 40.9), ("y", "40"),
                           ("x", True), ("x", -1), ("tile", 256), ("hidden", "false")):
            value_manifest = copy.deepcopy(ok)
            value_manifest["sprites"][0][key] = value
            assert simulate(value_manifest)["violations"], value_manifest
        print("[SELF-CHECK OK] sprite_line_sim")
        return 0
    if not args.manifest:
        print("[FAIL] manifest obrigatorio", file=sys.stderr)
        return 3
    try:
        with open(args.manifest, encoding="utf-8") as stream:
            rep = simulate(json.load(stream))
    except (OSError, ValueError, UnicodeError, RecursionError) as error:
        rep = {"sprites": 0, "peak_per_line": 0, "violations": [f"manifest unreadable: {error}"]}
    print(json.dumps(rep))
    if rep["violations"]:
        for v in rep["violations"]:
            print(f"[FAIL] {v}")
        return 1
    print(f"[PASS] {rep['sprites']} sprites, pico {rep['peak_per_line']}/linha")
    return 0

if __name__ == "__main__":
    sys.exit(main())
