#!/usr/bin/env python3
"""Gera e valida doc/palettes_manifest.json — paleta exata por personagem.

Verdade: sms_palette.py do workspace (codigo 6-bit, RGB=canal*85, luma 0.30/0.59/0.11,
piso ΔY>=17). Rampas de material exigem ΔY>=17 entre tons vizinhos; cores de
mesma luma mas matiz diferente sao aceitas apenas separadas por contorno 1px
(política do traço SFZ2 registrada no GDD).
"""
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[3] / "tools" / "sms_wrapper"
sys.path.insert(0, str(TOOLS))
from sms_palette import code_rgb, luma, LUMA_FLOOR_DEFAULT  # noqa: E402

OUT = Path(__file__).resolve().parent / "palettes_manifest.json"

# cada entrada: (nome, codigo 6-bit). idx 0 implicito = transparente.
# ramps: grupos de tons do MESMO material que se encostam no sprite.
CHARACTERS = {
    "ga_warrior": {
        "classe": "pesado", "cor": "Golden Axe Warrior (SMS)",
        "colors": [
            # Mapeada do sheet de personagem SMS (Spriters Resource, asset
            # 29261): azul/ciano da armadura, capa vermelha, ouro, pele e branco.
            # A arte conceitual não usa o fundo teal do sheet como cor.
            ("outline", (1, 0, 0)),
            ("skin_light", (3, 2, 1)), ("skin_mid", (2, 1, 1)),
            ("leather_brown", (2, 1, 0)),
            ("armor_blue_shadow", (0, 0, 3)), ("armor_blue_mid", (0, 2, 3)),
            ("armor_blue_light", (1, 2, 3)), ("steel_cyan", (1, 3, 3)),
            ("cape_red", (3, 0, 1)),
            ("skin_highlight", (3, 2, 2)),
            ("gold_light", (3, 3, 1)),
            ("steel_white", (3, 3, 3)),
        ],
        "ramps": [["skin_light", "skin_mid", "outline"],
                  ["armor_blue_shadow", "armor_blue_mid", "armor_blue_light", "steel_cyan"],
                  ["outline", "cape_red"],
                  ["leather_brown", "gold_light"],
                  ["steel_cyan", "steel_white"]],
        "nota": "12 tons derivados do sheet de personagem SMS (Spriters Resource, asset 29261), aproximados para RGB canal×85; fundo teal excluído. O preto foi reservado ao índice transparente 0; contorno opaco usa o tom bordô escuro presente no sheet. Paleta corrigida: azul/ciano, ouro, vermelho, pele, branco e contorno.",
    },
    "lord_of_the_sword": {
        "classe": "pesado", "cor": "Lord of the Sword (Landau; sprite SMS)",
        "colors": [
            # Landau - Standing Left (SMS Power sprite archive): preserve its
            # coral skin, scarlet, olive/green, orange-gold, silver, and blue.
            # Additional steps extend those hues into clean SMS cel-shading.
            ("outline", (1, 1, 1)),
            ("skin_light", (3, 2, 2)), ("skin_mid", (3, 1, 1)),
            ("warm_mid", (2, 1, 0)), ("hair_olive", (1, 1, 0)), ("hair_deep", (1, 0, 0)),
            ("red_accent", (2, 0, 0)),
            ("tunic_light", (2, 3, 0)), ("tunic_mid", (1, 2, 0)), ("tunic_shadow", (0, 1, 0)),
            ("leather_light", (3, 2, 0)), ("steel_light", (3, 3, 3)), ("steel_mid", (2, 2, 2)),
            ("blue_cloth_light", (2, 2, 3)), ("blue_cloth_mid", (1, 1, 2)),
        ],
        "ramps": [["skin_light", "skin_mid", "warm_mid"],
                  ["warm_mid", "hair_olive", "hair_deep"],
                  ["tunic_light", "tunic_mid", "tunic_shadow"],
                  ["leather_light", "warm_mid", "hair_deep"],
                  ["steel_light", "steel_mid", "outline"],
                  ["blue_cloth_light", "blue_cloth_mid"]],
    },
    "hayato": {
        "classe": "medio", "cor": "Kenseiden",
        "colors": [
            ("hakama_orange_light", (3, 1, 0)),
            ("outline_wine_dark", (1, 0, 0)),
            ("hakama_red_shadow", (2, 0, 0)),
            ("kimono_white", (3, 3, 3)),
            ("sash_vermilion", (3, 0, 0)),
            ("hair_scabbard_dark", (1, 1, 1)),
            ("kimono_shadow", (2, 2, 2)),
            ("skin_shadow", (1, 1, 0)),
            ("hakama_orange_shadow", (2, 1, 0)),
            ("skin_light", (3, 2, 2)),
            ("skin_mid", (2, 1, 1)),
            ("deep_wine_shadow", (1, 0, 1)),
            ("warm_highlight", (3, 2, 1)),
            ("sash_red_highlight", (3, 1, 1)),
            ("sandal_shadow", (0, 1, 0)),
        ],
        "ramps": [["skin_light", "skin_mid", "skin_shadow"],
                  ["kimono_white", "kimono_shadow"],
                  ["hakama_orange_light", "hakama_orange_shadow", "hakama_red_shadow"],
                  ["sash_red_highlight", "sash_vermilion"]],
    },
    "joe_musashi": {
        "classe": "medio", "cor": "Shinobi",
        "colors": [
            ("outline", (0, 0, 0)),
            ("skin_light", (3, 2, 2)), ("skin_mid", (2, 1, 1)),
            ("garb_light", (1, 1, 3)), ("garb_mid", (0, 0, 2)),
            ("trim_cyan", (2, 2, 3)),
            ("scarf_red", (3, 0, 0)),
            ("steel_katana", (2, 2, 2)),
            ("highlight_white", (3, 3, 3)),
        ],
        "ramps": [["skin_light", "skin_mid"],
                  ["garb_light", "garb_mid"]],
        "alternos": {
            "classic_shinobi1": "swap de roles no mesmo pool: garb_* vira branco/acinzentado "
                                "(wraps 3,3,3 / 2,2,2 / 1,1,1) — traje classico do 1o Shinobi.",
        },
    },
    "joe_musashi_shadow_dancer_sms": {
        "classe": "medio", "cor": "Shadow Dancer (Takashi; Master System)",
        "colors": [
            # SMS Power's Takashi - Standing Right sprite: white/gray gi,
            # two reds, warm skin, and a tiny yellow accent. Source black
            # outline maps to deep wine because palette index 0 is transparent.
            ("outline_wine", (1, 0, 0)),
            ("skin_light", (3, 2, 1)),
            ("gi_white", (3, 3, 3)), ("gi_gray_light", (2, 2, 2)),
            ("gi_gray_deep", (1, 1, 1)),
            ("sash_red", (2, 0, 0)), ("accent_yellow", (3, 3, 0)),
        ],
        "ramps": [["gi_white", "gi_gray_light", "gi_gray_deep"],
                  ["sash_red", "outline_wine"]],
        "nota": "Estudo de traje inspirado no sprite Takashi - Standing Right de "
                "Shadow Dancer SMS Power (https://www.smspower.org/Sprites/ShadowDancer-SMS). "
                "Aproxima as cores extraídas à grade RGB canal×85; o contorno preto "
                "foi substituído por vinho profundo para respeitar índice 0 transparente. "
                "Não é asset final nem altera o traje base de Joe Musashi.",
    },
    "jj_zillion_ii": {
        "classe": "leve", "cor": "Zillion II: The Tri Formation (Master System)",
        "colors": [
            # Palette sampled from the in-game J.J - Standing sprite on SMS Power.
            # Original dark blue, violet-blue, magenta-red, orange, warm skin,
            # and white are mapped to RGB channel×85. Extra nearby shades give
            # clean three-tone ramps. Source black is replaced with opaque navy
            # because index 0 is reserved for transparency.
            ("outline_navy", (0, 0, 1)),
            ("hair_blue_deep", (0, 0, 2)),
            ("hair_blue_mid", (1, 1, 3)),
            ("hair_blue_light", (2, 2, 3)),
            ("uniform_magenta_deep", (2, 0, 1)),
            ("uniform_magenta_mid", (3, 0, 1)),
            ("uniform_magenta_light", (3, 1, 2)),
            ("orange_deep", (2, 1, 0)),
            ("orange_mid", (3, 1, 0)),
            ("orange_light", (3, 2, 1)),
            ("skin_deep", (2, 1, 1)),
            ("skin_mid", (3, 2, 2)),
            ("skin_light", (3, 3, 3)),
        ],
        "ramps": [["hair_blue_deep", "hair_blue_mid", "hair_blue_light"],
                  ["uniform_magenta_deep", "uniform_magenta_mid", "uniform_magenta_light"],
                  ["orange_deep", "orange_mid", "orange_light"],
                  ["skin_deep", "skin_mid", "skin_light"]],
        "nota": "Paleta de estudo para J.J. baseada nas cores do sprite J.J - Standing de Zillion II: The Tri Formation para Master System (SMS Power, https://www.smspower.org/Sprites/ZillionII-SMS). A pedido do dono, referências do anime consultadas apenas para o corte do uniforme; não definem a paleta, moveset ou lore do fan game. Cores mapeadas à grade 6-bit SMS; tons adjacentes extras só ampliam a sombra cel. Sem pixels copiados. Contorno preto usa navy #000055 para reservar o índice 0 transparente. Classe leve e escala ainda são propostas.",
    },
    "dr_ferdinand_social": {
        "classe": "medio", "cor": "Master of Darkness",
        "colors": [
            # Index 0 is transparent; use opaque navy ink in sprite assets.
            ("outline", (0, 0, 1)),
            ("skin_light", (3, 2, 2)), ("skin_mid", (2, 1, 1)),
            # Original Dr. Social sprite: bright blue clothing, deep teal
            # shadows, gray hair, and brown footwear. RGB is nearest-mapped
            # from the SMS Power sprite archive to SMS channel x85.
            ("suit_light", (1, 2, 3)), ("suit_mid", (0, 2, 2)),
            ("suit_deep", (0, 1, 1)),
            ("shirt_light", (3, 3, 3)), ("shirt_shadow", (2, 2, 2)),
            ("hair_gray", (1, 1, 1)), ("boot_brown", (1, 0, 0)),
            ("tie_burgundy", (2, 0, 1)),
            ("accent_red", (3, 0, 0)), ("arcane_violet", (2, 0, 3)),
            ("brass_glasses", (3, 3, 0)),
        ],
        "ramps": [["skin_light", "skin_mid"],
                  ["shirt_light", "shirt_shadow"],
                  ["suit_light", "suit_mid", "suit_deep"]],
        "nota": "traje azul/ciano, sombra teal, cabelo grisalho e botas castanhas "
                "mapeados do sprite SMS de Dr. Social (SMS Power, "
                "Dr.FerdinandSocial-StandingRight; RGB aproximado ao canal x85). "
                "Camisa branca, cravat burgundy e óculos de latão mantêm a "
                "direção autoral; contorno opaco usa navy #000055 porque índice "
                "0 é transparente. accent_red/arcane_violet são FX do arsenal, "
                "sem forma vampira (dono, 2026-10-03).",
    },
    "black_belt_karateka": {
        "classe": "medio", "cor": "Black Belt",
        "colors": [
            ("outline", (0, 0, 0)),
            ("skin_tan", (3, 2, 1)), ("skin_mid", (2, 1, 0)), ("skin_shadow", (1, 0, 0)),
            ("gi_light", (3, 3, 3)), ("gi_shadow", (2, 2, 2)), ("gi_deep", (1, 1, 1)),
            ("belt_red", (3, 0, 0)),
        ],
        "ramps": [["skin_tan", "skin_mid", "skin_shadow"],
                  ["gi_light", "gi_shadow", "gi_deep"]],
        "nota": "cabelo e cinto usam o outline (0,0,0) — mesmo codigo, sem custo de slot.",
    },
    "witch_psychic_world": {
        "classe": "leve", "cor": "Psychic World",
        "colors": [
            ("outline", (0, 0, 0)),
            ("skin_light", (3, 2, 2)), ("skin_mid", (2, 1, 1)),
            ("hair_purple", (2, 0, 3)), ("hair_shadow", (1, 0, 2)),
            ("dress_pink", (3, 1, 2)), ("dress_shadow", (2, 0, 1)),
            ("psychic_cyan", (0, 3, 3)), ("psychic_deep", (0, 2, 2)),
            ("gold_buckle", (3, 3, 0)),
            ("highlight_white", (3, 3, 3)),
        ],
        "ramps": [["skin_light", "skin_mid"],
                  ["hair_purple", "hair_shadow"],
                  ["dress_pink", "dress_shadow"],
                  ["psychic_cyan", "psychic_deep"]],
    },
    "alis_landale": {
        "classe": "leve", "cor": "Phantasy Star",
        "colors": [
            ("outline", (1, 0, 0)),
            ("skin_light", (3, 2, 2)), ("cream_light", (3, 3, 2)),
            ("hair_brown", (2, 1, 0)), ("warm_gold", (3, 2, 0)),
            ("pink_main", (3, 1, 2)), ("pink_light", (3, 2, 3)),
            ("suit_indigo", (1, 1, 2)), ("suit_silver", (2, 2, 2)),
            ("weapon_blue", (0, 1, 3)), ("weapon_cyan", (0, 3, 3)),
            ("gold_yellow", (3, 3, 0)), ("highlight_white", (3, 3, 3)),
        ],
        "ramps": [["cream_light", "skin_light"],
                  ["warm_gold", "hair_brown", "outline"],
                  ["pink_light", "pink_main"],
                  ["highlight_white", "suit_silver", "suit_indigo"],
                  ["weapon_cyan", "weapon_blue"],
                  ["gold_yellow", "warm_gold"]],
        "nota": "cores alinhadas ao retrato Alisa - Title screen de Phantasy Star SMS (SMS Power, referencia apenas de cor). O contorno usa marrom profundo #550000 porque preto puro e o indice transparente 0 na traducao.",
    },
    "boss_ninja_master": {
        "classe": "chefe", "cor": "Shinobi",
        "colors": [
            ("outline", (0, 0, 0)),
            ("skin_mid", (2, 1, 1)),
            ("garb_purple", (1, 0, 2)), ("garb_deep", (0, 0, 1)),
            ("mask_silver", (2, 2, 2)), ("mask_shadow", (1, 1, 1)),
            ("eye_red", (3, 0, 0)),
            ("blade_cyan", (0, 3, 3)),
            ("smoke_gray", (1, 1, 2)),
            ("highlight_white", (3, 3, 3)),
        ],
        "ramps": [["garb_purple", "garb_deep"], ["mask_silver", "mask_shadow"]],
    },
    "boss_count_dracula": {
        "classe": "chefe", "cor": "Master of Darkness",
        "colors": [
            ("outline", (0, 0, 0)),
            ("face_pale", (3, 3, 2)), ("face_shadow", (2, 2, 2)), ("face_deep", (1, 1, 1)),
            ("hair_white", (3, 3, 3)),
            ("cape_inner", (3, 0, 0)), ("cape_deep", (1, 0, 0)),
            ("suit_night", (0, 0, 1)),
            ("gold_clasp", (3, 3, 0)),
            ("eye_red", (2, 0, 1)),
        ],
        "ramps": [["face_pale", "face_shadow", "face_deep"],
                  ["cape_inner", "cape_deep"]],
        "nota": "capa externa usa outline (0,0,0) — preto absoluto sem gastar slot.",
    },
    "boss_luter": {
        "classe": "chefe", "cor": "Phantasy Star",
        "colors": [
            ("outline", (0, 0, 0)),
            ("skin_mid", (2, 1, 1)),
            ("robe_green", (0, 2, 0)), ("robe_deep", (0, 1, 0)),
            ("robe_purple", (1, 0, 2)),
            ("glow_green", (0, 3, 0)), ("glow_cyan", (0, 3, 3)),
            ("steel_dark", (1, 1, 1)),
            ("eye_red", (3, 0, 0)),
            ("highlight_white", (3, 3, 3)),
        ],
        "ramps": [["robe_green", "robe_deep"], ["glow_green", "glow_cyan"]],
    },
    "boss_dark_force": {
        "classe": "chefe", "cor": "Phantasy Star II (a confirmar)",
        "colors": [
            ("outline", (0, 0, 0)),
            ("body_purple", (2, 0, 3)), ("body_mid", (1, 0, 2)), ("body_deep", (0, 0, 1)),
            ("energy_cyan", (0, 3, 3)), ("energy_deep", (0, 2, 2)),
            ("eye_red", (3, 0, 0)),
            ("bone_light", (3, 3, 3)), ("bone_shadow", (2, 2, 2)),
            ("core_yellow", (3, 3, 0)),
        ],
        "ramps": [["body_purple", "body_mid", "body_deep"],
                  ["energy_cyan", "energy_deep"],
                  ["bone_light", "bone_shadow"]],
    },
}


def main():
    floor = LUMA_FLOOR_DEFAULT
    errors, notes = [], []
    manifest = {
        "schema": "mof_palettes_v1",
        "date": "2026-10-03",
        "authority": "doc/11-gdd.md §Direção de arte; sms_palette.py (codigo 6-bit)",
        "rules": {
            "codes": "canais 0..3; RGB de contrato = canal*85",
            "transparent_index": 0,
            "max_usable": 15,
            "luma_floor_delta_y": floor,
            "same_luma_policy": "pares com ΔY < piso so validos se separados por contorno 1px (traço SFZ2)",
        },
        "characters": {},
    }
    for name, ch in CHARACTERS.items():
        entries = []
        ymap = {}
        seen_rgb = {}
        for i, (role, code) in enumerate(ch["colors"], start=1):
            rgb = code_rgb(code)
            if rgb in seen_rgb:
                errors.append(f"{name}: rgb duplicado {role} == {seen_rgb[rgb]}")
            seen_rgb[rgb] = role
            y = round(luma(rgb), 2)
            ymap[role] = y
            entries.append({"index": i, "role": role, "code": list(code),
                            "rgb": list(rgb), "y": y})
        if len(entries) > 15:
            errors.append(f"{name}: {len(entries)} cores uteis > 15")
        for ramp in ch.get("ramps", []):
            for a, b in zip(ramp, ramp[1:]):
                d = abs(ymap[a] - ymap[b])
                if d < floor:
                    errors.append(f"{name}: rampa {a}->{b} ΔY={d:.1f} < piso {floor}")
        for i, e in enumerate(entries):
            for f in entries[i + 1:]:
                d = abs(e["y"] - f["y"])
                if 0 < d < floor:
                    notes.append(f"{name}: {e['role']}/{f['role']} ΔY={d:.1f} "
                                 f"— exige contorno entre eles no sprite")
        manifest["characters"][name] = {
            "classe": ch["classe"], "origem": ch["cor"],
            "usable_colors": len(entries), "colors": entries,
            **({"alternos": ch["alternos"]} if "alternos" in ch else {}),
            **({"nota": ch["nota"]} if "nota" in ch else {}),
        }
    OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"[WRITE] {OUT}")
    for n in notes:
        print("[NOTE]", n)
    if errors:
        for e in errors:
            print("[FAIL]", e)
        sys.exit(1)
    print(f"[OK] {len(CHARACTERS)} paletas validadas: codigos 6-bit, rampas ΔY>={floor}, <=15 uteis")


if __name__ == "__main__":
    main()
