"""Formato de runtime SMS para poses geradas (contrato citado, nao inventado):

- Metasprite = triplas `dx, dy, tile` terminadas por dx=0x80 (`METASPRITE_END`,
  SMSlib.h:214-216); byte-a-byte idêntico ao formato provado em ROM por
  MSSF2T (`ken_idle_meta` em SMS_projects/MSSF2T/inc/ken_idle_tiles.h:58-64 e
  SMS_addMetaSprite em SMSlib_metasprite.c upstream: dx/dy assinados somados à
  origem, tile absoluto). Origem = topo-esquerda da pose: `dx = coluna*8`,
  `dy = linha*16` (para baixo; runtime converte pés->topo conhecendo a altura).
- Tiles em modo `SPRITEMODE_TALL` (8x16, SMSlib.h:54-57): o VDP lê pares
  (topo, base) em índices par/ímpar consecutivos — índice de runtime sempre par
  (`pool_idx*2`), blob = concatenação de pares de 64 B dedupados por conteúdo.
- SMS NÃO tem flip de sprite: espelho horizontal é OUTRO padrão em VRAM
  (precedente MSSF2T `TILE_FB1L`); em 4bpp planar espelhar = inverter bits de
  cada byte. Facing esquerda usa o par espelhado + regra MSSF2T `dx' = lo+hi-dx`
  (coluna tx -> (tw-1-tx)*8). Custo de VRAM do espelho é medido, não escondido.
- P2 usa índices 9..15 na MESMA sprite palette física (única no SMS,
  SMSlib.h:249-250); índice 0 continua transparente. Como P1/P2 passam pela
  conversão/deduplicação separadamente, a ordem e a quantidade dos pares podem
  divergir. O gerador deve emitir META/METAL próprios para o pool de cada ACT,
  ou provar identidade do layout antes de compartilhar índices. Restrição do
  GDD: |pal(P1) ∪ pal(P2)| <= 15.
"""
from __future__ import annotations

_REV = bytes(int(f"{b:08b}"[::-1], 2) for b in range(256))
_BLANK = bytes(32)
_BLANK_PAIR = _BLANK + _BLANK


def _cell_bytes(pose, pl) -> bytes:
    """Tile canônico do pose + flags do placement -> 32 B como aparecem na tela."""
    t = pose.tiles[pl.tile]
    rows = [t[i * 4:(i + 1) * 4] for i in range(8)]
    if pl.vflip:
        rows.reverse()
    out = bytearray()
    for r in rows:
        out += r.translate(_REV) if pl.hflip else r
    return bytes(out)


def _mirror_pair(pair: bytes) -> bytes:
    return bytes(_REV[b] for b in pair)


def _layout(pose):
    """(pool, ordem de desenho, mirrors, tw, n_linhas_tall)."""
    tw = -(-pose.width // 8)
    th = -(-pose.height // 8)
    cells = {(pl.x // 8, pl.y // 8): pl for pl in pose.placements}
    rows = -(-th // 2)

    def pair_at(tx: int, row: int) -> bytes:
        top = _cell_bytes(pose, cells[(tx, row * 2)]) if row * 2 < th else _BLANK
        bot = _cell_bytes(pose, cells[(tx, row * 2 + 1)]) if row * 2 + 1 < th else _BLANK
        return top + bot

    pool: list[bytes] = []
    index: dict[bytes, int] = {}

    def intern(pair: bytes) -> int:
        if pair not in index:
            index[pair] = len(pool)
            pool.append(pair)
        return index[pair]

    order = [(tx, row, intern(pair_at(tx, row)))
             for row in range(rows) for tx in range(tw)]
    normals = list(range(len(pool)))            # espelhos entram DEPOIS dos normais
    mirrors = {i: intern(_mirror_pair(pool[i])) for i in normals}
    return pool, order, mirrors, tw, rows


def pack_tiles_tall(pose) -> tuple[bytes, dict[int, int]]:
    """(blob 64 B/par dedupado, map pool_idx -> pool_idx do espelho H)."""
    pool, _, mirrors, _, _ = _layout(pose)
    return b"".join(pool), mirrors


def build_frames(pose, tile_base: int = 0, facing: int = 0,
                 omit_blank_cells: bool = False) -> bytes:
    """Triplas (dx, dy, tile) + terminador 0x80; tile = tile_base + pool_idx*2."""
    pool, order, mirrors, tw, _rows = _layout(pose)
    out = bytearray()
    for tx, row, idx in order:
        # A fully transparent 8x16 cell contributes no visible pixels and
        # needlessly consumes a physical SAT entry. The packed blank pattern
        # remains available; only its metadata placement is omitted.
        if omit_blank_cells and pool[idx] == _BLANK_PAIR:
            continue
        i = mirrors[idx] if facing else idx
        dx = (tw - 1 - tx) * 8 if facing else tx * 8
        dy = row * 16
        out += bytes([dx & 0xFF, dy & 0xFF, (tile_base + i * 2) & 0xFF])
    out.append(0x80)
    return bytes(out)


def decode_indices(tile32: bytes) -> list[int]:
    """32 B 4bpp planar -> 64 índices MSB-first (inverso de sms_tiles._encode_tile)."""
    out = []
    for r in range(0, len(tile32), 4):
        p0, p1, p2, p3 = tile32[r:r + 4]
        for x in range(8):
            m = 0x80 >> x
            out.append(((p0 & m) > 0) | ((p1 & m) > 0) << 1
                       | ((p2 & m) > 0) << 2 | ((p3 & m) > 0) << 3)
    return out


def _encode_indices(idx: list[int]) -> bytes:
    out = bytearray()
    for r in range(0, len(idx), 8):
        planes = [0, 0, 0, 0]
        for x in range(8):
            c = idx[r + x]
            for p in range(4):
                planes[p] |= ((c >> p) & 1) << (7 - x)
        out += bytes(planes)
    return bytes(out)


def shift_palette_indices(blob: bytes, offset: int) -> bytes:
    """P2: indices != 0 somam offset (mod 16); 0 permanece transparente."""
    out = bytearray()
    for t in range(0, len(blob), 32):
        idx = decode_indices(blob[t:t + 32])
        out += _encode_indices([0 if v == 0 else (v + offset) & 15 for v in idx])
    return bytes(out)
