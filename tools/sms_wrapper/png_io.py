#!/usr/bin/env python3
"""png_io.py — leitura/escrita de PNG indexado (color type 3) em Python puro.

Contrato do workspace: assets visuais são PNG indexado de 8 bits, não-entrelaçado,
índice 0 transparente (tRNS). Nada de dependências externas: gates precisam rodar
em qualquer host. Falha LOUD em formato fora do contrato — nunca adivinhar.
"""
import struct, zlib, sys

SIGNATURE = b"\x89PNG\r\n\x1a\n"

class PngError(Exception):
    pass

def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c

def png_size(path):
    """Dimensoes (w,h) direto do IHDR."""
    data = open(path, "rb").read(33)
    if not data.startswith(SIGNATURE):
        raise PngError(f"{path}: nao e PNG")
    return struct.unpack(">II", data[16:24])

def write_png_rgb(path, w, h, rows):
    """Escreve PNG truecolor RGB8 (type 2, filtro 0). rows = h listas de w tuples."""
    def chunk(t, b):
        c = struct.pack(">I", len(b)) + t + b
        return c + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for (r, g, b) in row:
            raw += bytes((r, g, b))
    body = chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw)))
    body += chunk(b"IEND", b"")
    open(path, "wb").write(SIGNATURE + body)

def read_png_rgb(path):
    """Le qualquer PNG 8-bit e retorna (w,h,rows[tuples rgb])."""
    data = open(path, "rb").read()
    if not data.startswith(SIGNATURE):
        raise PngError(f"{path}: nao e PNG")
    pos, idat, ihdr, palette = 8, bytearray(), None, None
    while pos < len(data):
        ln, ct = struct.unpack(">I4s", data[pos:pos + 8]); body = data[pos+8:pos+8+ln]
        if ct == b"IHDR": ihdr = struct.unpack(">IIBBBBB", body)
        elif ct == b"PLTE": palette = [tuple(body[i:i+3]) for i in range(0, len(body), 3)]
        elif ct == b"IDAT": idat += body
        elif ct == b"IEND": break
        pos += 12 + ln
    w, h, depth, ctype_, comp, filt, interlace = ihdr
    if interlace != 0:
        raise PngError(f"{path}: interlace nao suportado")
    raw = zlib.decompress(bytes(idat))
    if depth < 8:
        # paletted (3) ou grayscale (0) com bit depth reduzido: expandir p/ escala 0-255
        if ctype_ == 3:
            spp = 8 // depth
            stride = (w + spp - 1) // spp
            frows = _unfilter(raw, w, h, 1, stride_override=stride)
            mask = (1 << depth) - 1
            out = []
            for y in range(h):
                row = frows[y]; cl = []
                for x in range(w):
                    byte_i = x // spp
                    shift = 8 - depth * ((x % spp) + 1)
                    pi = (row[byte_i] >> shift) & mask
                    r, g, b = (palette[pi] if palette and pi < len(palette) else (0, 0, 0))
                    cl.append((r, g, b))
                out.append(cl)
            return w, h, out
        elif ctype_ == 0:
            spp = 8 // depth
            stride = (w + spp - 1) // spp
            frows = _unfilter(raw, w, h, 1, stride_override=stride)
            mask = (1 << depth) - 1
            scale = 255 // mask
            out = []
            for y in range(h):
                row = frows[y]; cl = []
                for x in range(w):
                    byte_i = x // spp
                    shift = 8 - depth * ((x % spp) + 1)
                    v = (row[byte_i] >> shift) & mask
                    v = v * scale
                    cl.append((v, v, v))
                out.append(cl)
            return w, h, out
        else:
            raise PngError(f"{path}: depth {depth} so suportado p/ paletted/grayscale")
    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype_]
    frows = _unfilter(raw, w, h, nch)
    out = []
    for y in range(h):
        row = frows[y]; line = []
        for x in range(w):
            o = x * nch
            if ctype_ == 3:
                pi = row[o]; r, g, b = (palette[pi] if palette and pi < len(palette) else (0, 0, 0))
            elif ctype_ == 0: r = g = b = row[o]
            elif ctype_ == 4: r = g = b = row[o]
            else: r, g, b = row[o], row[o+1], row[o+2]
            line.append((r, g, b))
        out.append(line)
    return w, h, out

def _unfilter(raw, w, h, bpp, stride_override=None):
    """Desfaz filtros PNG genéricos. bpp = bytes por pixel."""
    stride = stride_override if stride_override is not None else w * bpp
    expected = (stride + 1) * h
    if len(raw) < expected:
        raise PngError(f"dados insuficientes ({len(raw)}<{expected})")
    out = []
    prev = bytearray(stride)
    off = 0
    for _ in range(h):
        f = raw[off]; line = bytearray(raw[off + 1:off + 1 + stride]); off += 1 + stride
        if f == 0:
            pass
        elif f == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                ul = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(left, prev[i], ul)) & 0xFF
        else:
            raise PngError(f"filtro {f} desconhecido")
        out.append(bytes(line))
        prev = line
    return out

def read_indexed_png(path):
    """Retorna dict {w,h,palette:[(r,g,b)],pixels:[bytes],trns:set} (contrato de assets)."""
    data = open(path, "rb").read()
    if not data.startswith(SIGNATURE):
        raise PngError(f"{path}: nao e PNG")
    pos, idat, palette, trns, ihdr = 8, bytearray(), None, None, None
    while pos < len(data):
        if pos + 8 > len(data):
            raise PngError(f"{path}: chunk truncado")
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        crc = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        if zlib.crc32(ctype + body) & 0xFFFFFFFF != crc:
            raise PngError(f"{path}: CRC invalido no chunk {ctype}")
        if ctype == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif ctype == b"PLTE":
            palette = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif ctype == b"tRNS":
            trns = list(body)
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break
        pos += 12 + length
    w, h, depth, ctype_, comp, filt, interlace = ihdr
    if depth != 8 or ctype_ != 3:
        raise PngError(
            f"{path}: contrato exige PNG indexado 8-bit (type 3); recebido depth={depth} type={ctype_}")
    if interlace != 0:
        raise PngError(f"{path}: entrelacado nao suportado pelo contrato")
    raw = zlib.decompress(bytes(idat))
    out = _unfilter(raw, w, h, 1)
    return {"w": w, "h": h, "palette": palette, "pixels": out,
            "trns": {i for i, alpha in enumerate(trns or ()) if alpha == 0},
            "partial_alpha": {i for i, alpha in enumerate(trns or ()) if 0 < alpha < 255}}

def read_png_luma_samples(path, max_samples=4096, box=None):
    """Le QUALQUER PNG 8-bit (gray/RGB/indexed/RGBA) e retorna amostras de luma.
    box=(x0,y0,x1,y1) recorta antes de amostrar. Usado pelo gate de evidencia."""
    data = open(path, "rb").read()
    if not data.startswith(SIGNATURE):
        raise PngError(f"{path}: nao e PNG")
    pos, idat, ihdr, palette = 8, bytearray(), None, None
    while pos < len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif ctype == b"PLTE":
            palette = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break
        pos += 12 + length
    w, h, depth, ctype_, comp, filt, interlace = ihdr
    if depth != 8 or interlace != 0:
        raise PngError(f"{path}: depth {depth}/interlace nao suportado na leitura")
    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype_)
    if nch is None:
        raise PngError(f"{path}: color type {ctype_} nao suportado")
    x0, y0, x1, y1 = box if box else (0, 0, w, h)
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(w, x1); y1 = min(h, y1)
    if x1 <= x0 or y1 <= y0:
        raise PngError("box vazio")
    raw = zlib.decompress(bytes(idat))
    rows = _unfilter(raw, w, h, nch)
    samples = []
    step = max(1, ((x1 - x0) * (y1 - y0)) // max_samples)
    idx = 0
    for y in range(y0, y1):
        row = rows[y]
        for x in range(x0, x1):
            if idx % step == 0:
                o = x * nch
                if ctype_ == 3:
                    pi = row[o]
                    r, g, b = palette[pi] if palette and pi < len(palette) else (0, 0, 0)
                elif ctype_ == 0:
                    r = g = b = row[o]
                elif ctype_ == 4:
                    r = g = b = row[o]
                else:
                    r, g, b = row[o], row[o + 1], row[o + 2]
                samples.append(int(round(0.30 * r + 0.59 * g + 0.11 * b)))
            idx += 1
    return samples

def write_indexed_png(path, w, h, palette, pixels, trns=(0,)):
    """Escreve PNG indexado com filtro 0. `pixels` = lista de h bytes-rows."""
    def chunk(t, b):
        c = struct.pack(">I", len(b)) + t + b
        return c + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0)
    plte = b"".join(bytes(p) for p in palette)
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        raw += row
    body = chunk(b"IHDR", ihdr) + chunk(b"PLTE", plte)
    if trns:
        body += chunk(b"tRNS", bytes(trns))
    body += chunk(b"IDAT", zlib.compress(bytes(raw)))
    body += chunk(b"IEND", b"")
    open(path, "wb").write(SIGNATURE + body)

if __name__ == "__main__":
    # self-check minimo: roundtrip
    pal = [(0, 0, 0), (255, 255, 255)]
    px = [bytes([0, 1] * 4), bytes([1, 0] * 4)]
    write_indexed_png("/tmp/opencode/pngio_selfcheck.png", 8, 2, pal, px)
    got = read_indexed_png("/tmp/opencode/pngio_selfcheck.png")
    assert got["w"] == 8 and got["h"] == 2 and got["pixels"][1][0] == 1
    assert 0 in got["trns"]
    print("[SELF-CHECK OK] png_io")
