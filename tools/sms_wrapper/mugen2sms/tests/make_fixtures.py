"""Builder de pacote MUGEN sintetico para testes (nunca arte real — politica do GDD).

Gera em tmp_path uma pasta-personagem minima e legal: .def/.sff(v1, 2 sprites +
1 link)/.act/.air/.cmd/.cns. Os valores exatos sao os contratos dos testes.
"""
from __future__ import annotations

import struct
from pathlib import Path

SPRITE_W = SPRITE_H = 16
GROUP = 5900


def _pcx_8bpp(w: int, h: int, pixels: bytes, palette: bytes = b"") -> bytes:
    """PCX 8bpp/1-plano como o MUGEN grava; RLE minimo (runs de 1 ou literais <0xC0)."""
    hdr = bytearray(128)
    hdr[0], hdr[1], hdr[3] = 0, 5, 8                      # fabricante, versao, bpp
    struct.pack_into("<4H", hdr, 4, 0, 0, w - 1, h - 1)
    hdr[65] = 1                                            # planes
    struct.pack_into("<H", hdr, 66, w)                     # bytes por linha (w par)
    out = bytearray(hdr)
    for v in pixels:
        if v >= 0xC0:
            out += bytes([0xC1, v])                        # run de 1 obrigatorio
        else:
            out.append(v)
    if palette:
        out += b"\x0c" + palette[:768]
    return bytes(out)


def _solid(idx: int) -> bytes:
    return bytes([idx]) * (SPRITE_W * SPRITE_H)


def build(root: Path, with_command_states: bool = False) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    pal = bytes(((e * 37 + 11 * c) % 256) for e in range(256) for c in range(3))
    # PCX sem trailer de paleta faz o parser herdar prev_pal (preto) — o trailer
    # e obrigatorio aqui senão o conversor produz CRAM 0 e a cena some no VDP.
    s0 = _pcx_8bpp(SPRITE_W, SPRITE_H, _solid(3), pal)
    s1 = _pcx_8bpp(SPRITE_W, SPRITE_H, _solid(5), pal)
    # terceiro sprite: link para o indice 0 (0 bytes) — MUGEN usa muito
    # Imagens 3..8: poses DISTINTAS por acao (walk alterna 3/4, punch2 usa 8).
    # Politica anti-clon: nenhuma acao reusa o padrao de outra como ciclo
    # identico — cores solidas distintas + caixas clsn distintas.
    s3 = _pcx_8bpp(SPRITE_W, SPRITE_H, _solid(4), pal)   # walk A
    s4 = _pcx_8bpp(SPRITE_W, SPRITE_H, _solid(6), pal)   # walk B
    s5 = _pcx_8bpp(SPRITE_W, SPRITE_H, _solid(7), pal)   # crouch
    s6 = _pcx_8bpp(SPRITE_W, SPRITE_H, _solid(8), pal)   # guard
    s7 = _pcx_8bpp(SPRITE_W, SPRITE_H, _solid(9), pal)   # jump
    s8 = _pcx_8bpp(SPRITE_W, SPRITE_H, _solid(10), pal)  # punch2 startup
    # layout real: sub_i | blob_i (link = blob 0 B)
    images = [(GROUP, 0, s0, 0), (GROUP, 1, s1, 0), (GROUP, 2, b"", 0),
              (GROUP, 3, s3, 0), (GROUP, 4, s4, 0), (GROUP, 5, s5, 0),
              (GROUP, 6, s6, 0), (GROUP, 7, s7, 0), (GROUP, 8, s8, 0)]
    n = len(images)
    sub0 = 512                                             # "first" = primeiro subheader (convencao do parser)
    head = bytearray(b"ElecbyteSpr\x00" + bytes([0, 1, 0, 1]))
    head += b"\x00" * 4                                    # 16..19 reservado
    head += struct.pack("<II", n, sub0)                    # parser le n_images@20, first@24
    head = bytes(head).ljust(512, b"\x00")
    lens = [len(im[2]) for im in images]
    positions, p = [], sub0
    for i in range(n):
        positions.append(p)
        p += 32 + lens[i]
    chain = b""
    for (grp, img, blob, link), pos, nxt in zip(images, positions,
                                                  positions[1:] + [0]):
        sub = struct.pack("<IIhhHHHB", nxt, len(blob),
                          SPRITE_W // 2, SPRITE_H, grp, img, link, 0)  # same=0: cada PCX traz a propria paleta
        chain += bytes(sub).ljust(32, b"\x00") + blob
    (root / "mini.sff").write_bytes(head + chain)
    (root / "pal1.act").write_bytes(pal)
    (root / "mini.def").write_text(
        '[Info]\nname = "Mini"\ndisplayname = "Mini Fixture"\nauthor = "fixture"\n'
        '[Files]\nsprite = mini.sff\ncns = mini.cns\nanim = mini.air\ncmd = mini.cmd\n'
        'pal1 = pal1.act\n', encoding="ascii")
    (root / "mini.air").write_text(
        "[begin action 0]\nclsn2default:\nclsn2[0] = -8, -16, 8, 0\n"
        f"{GROUP}, 0, -8, -16, -1\n"
        "[begin action 20]\nclsn2[0] = -8, -16, 8, 0\n"
        f"{GROUP}, 3, -8, -16, 8\nclsn2[0] = -8, -16, 8, 0\n"
        f"{GROUP}, 4, -8, -16, 8\n"
        "[begin action 40]\nclsn2[0] = -8, -16, 8, 0\n"
        f"{GROUP}, 7, -8, -16, -1\n"
        "[begin action 100]\nclsn2[0] = -8, -12, 8, 0\n"
        f"{GROUP}, 5, -8, -16, -1\n"
        "[begin action 120]\nclsn2[0] = -8, -16, 8, 0\n"
        f"{GROUP}, 6, -8, -16, -1\n"
        "[begin action 200]\nclsn1[0] = 0, -14, 12, -8\nclsn2[0] = -8, -16, 8, 0\n"
        f"{GROUP}, 1, -8, -16, 3\n{GROUP}, 2, -6, -16, 5, H\n"
        "[begin action 201]\nclsn1[0] = 0, -16, 16, -4\nclsn2[0] = -8, -16, 8, 0\n"
        f"{GROUP}, 8, -8, -16, 3\n{GROUP}, 7, -8, -16, 4\n{GROUP}, 4, -8, -16, 5\n",
        encoding="ascii")
    (root / "mini.cmd").write_text(
        "[Command]\nname = punch\ncommand = a\n"
        "[Command]\nname = holdF\ncommand = /F\n"
        "[Command]\nname = special\ncommand = DB, D, DF + a\n",
        encoding="ascii")
    (root / "mini.cns").write_text(
        "[Data]\nlife = 250\n[Size]\nxscale = 1\nyscale = 1\n"
        "[Velocity]\nwalk.fwd = 2\nwalk.back = -1.5\njump.vx = 0\njump.vy = -10\n"
        "[Movement]\nairjump.num = 0\nairjump.height = 0\nyaccel = 0.5\n"
        "[Statedef 0]\ntype = S\nmovetype = I\nphysics = N\nanim = 0\nctrl = 1\n"
        "[State 0, 1]\ntype = ChangeAnim\ntrigger1 = 1\nvalue = 0\n"
        "[Statedef 20]\ntype = S\nmovetype = I\nphysics = S\nanim = 20\nctrl = 1\n"
        "[Statedef 40]\ntype = A\nmovetype = I\nphysics = A\nanim = 40\n"
        "[Statedef 100]\ntype = C\nmovetype = I\nphysics = C\nanim = 100\nctrl = 1\n"
        "[Statedef 120]\ntype = S\nmovetype = I\nphysics = S\nanim = 120\nctrl = 1\n"
        "[Statedef 200]\ntype = S\nmovetype = A\nphysics = S\nanim = 200\n"
        "[State 200, 1]\ntype = HitDef\ntrigger1 = time = 3\nattr = S, MA\ndamage = 5, 0\n"
        "[Statedef 201]\ntype = S\nmovetype = A\nphysics = S\nanim = 201\n"
        "[State 201, 1]\ntype = HitDef\ntrigger1 = time = 3\nattr = S, MA\ndamage = 8, 0\n",
        encoding="ascii")
    if with_command_states:
        # [Statedef -1] do .cmd: comando -> ChangeState (insumo da matriz de golpes)
        with open(root / "mini.cmd", "a", encoding="ascii") as f:
            f.write("[Statedef -1]\n"
                    "[State -1, punch]\ntype = ChangeState\nvalue = 200\n"
                    'triggerall = command = "punch"\ntrigger1 = statetype = S\ntrigger1 = ctrl\n'
                    "[State -1, special]\ntype = ChangeState\nvalue = 201\n"
                    'triggerall = command = "special"\ntrigger1 = statetype = S\ntrigger1 = ctrl\n'
                    "[State -1, ghost]\ntype = ChangeState\nvalue = 9999\n"
                    'triggerall = command = "holdF"\ntrigger1 = ctrl\n')
    return root
