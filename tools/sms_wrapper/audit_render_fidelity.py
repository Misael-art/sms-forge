#!/usr/bin/env python3
"""audit_render_fidelity.py — a tela mostra A ARTE AUTORAL? (fecha o L016)

O degrau que faltava. As checagens anteriores provam ORIGEM (veio de um SMS) e
NAO-VACUIDADE (nao e tela lisa), mas nao corretude: uma tela coerente com o
sprite ERRADO passa, e ruido fino de borda passa.

Tentativa que FALHOU (registrada para nao ser repetida): usar "fracao de blocos
8x8 com muitas cores" como detector universal de ruido. Calibrado no acervo
esparso deste projeto ele separa bem (0.000 limpo x 0.274 ruido), mas arte
AUTORAL detalhada (120 tiles de 8..15 cores) mede 1.000 — o detector reprovaria
o jogo inteiro. Aquele limiar so vale para cenas esparsas e esta declarado como
tal em screenshot_semantic_gate.

Este gate resolve por COMPARACAO COM A FONTE, que independe da densidade da
cena: pega a arte autoral (`res/sprites/*.png`), extrai a ESTRUTURA (quais
pixels compartilham a mesma cor, sem depender de qual cor a paleta atribuiu) e
procura essa mesma estrutura na captura. Se bate, a tela esta mostrando a arte
que foi desenhada — nao ruido, nao outro sprite.

Uso:
  audit_render_fidelity.py --shot <captura.png> --art <arte.png>
      [--at X,Y] [--min-match 0.90] [--json <saida>]
  audit_render_fidelity.py --shot <captura.png> --art <arte-indexada.png>
      --at X,Y --exact-indexed [--transparent-rgb RRGGBB] [--json <saida>]
  audit_render_fidelity.py --self-check
Exit: 0 arte confirmada na tela | 1 nao encontrada | 3 uso
"""
import sys, os, json, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from png_io import read_png_rgb, read_indexed_png, PngError   # noqa: E402
from sms_palette import nearest_code                          # noqa: E402

DEFAULT_MIN_MATCH = 0.90
# Escalas testadas: a janela do emulador raramente e 1:1 com o VDP.
SCALES = (1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.4, 1.5, 2.0)
# Quantos tons de tela uma mesma classe da arte pode ocupar. A escala do
# emulador mistura cores nas bordas (a moldura do heroi sai em 2 tons); ruido
# de VRAM espalha a classe por dezenas de tons.
MAX_TONES_PER_CLASS = 3

def structure(cells):
    """Relabela uma matriz de cores em CLASSES por ordem de aparicao.

    Torna a comparacao independente da paleta: o que importa e quais pixels
    compartilham a mesma cor, nao qual cor a paleta atribuiu a cada indice.
    """
    lab, out = {}, []
    for row in cells:
        r = []
        for c in row:
            if c not in lab:
                lab[c] = len(lab)
            r.append(lab[c])
        out.append(r)
    return out

def art_structure(art_path):
    """(estrutura, mascara_opaca, w, h).

    Indice 0 e TRANSPARENTE por contrato (§8): na tela esses pixels mostram o
    FUNDO (preto, estrelas, o que estiver atras), nao uma cor do sprite.
    Compara-los e comparar o cenario, nao a arte — foi o que segurou a
    coincidencia em 62.5% na primeira tentativa. So o opaco entra na conta.
    """
    img = read_indexed_png(art_path)
    px = img["pixels"]
    cells = [[px[y][x] for x in range(img["w"])] for y in range(img["h"])]
    mask = [[c != 0 for c in row] for row in cells]
    return structure(cells), mask, img["w"], img["h"]

def shot_structure(shot_path, x0, y0, w, h, scale=1.0, _cache={}):
    """Estrutura da regiao da captura, amostrada na ESCALA dada.

    A janela do emulador quase nunca e 1:1 com os 256x192 do VDP (moldura,
    barra de titulo, zoom). Sem tolerancia a escala o casamento estrutural
    falha por desalinhamento e nao por arte errada — foi o que aconteceu na
    primeira tentativa (62.5%).
    """
    key = shot_path
    if key not in _cache:
        _cache[key] = read_png_rgb(shot_path)
    sw, sh, rows = _cache[key]
    if x0 < 0 or y0 < 0:
        return None
    if x0 + int(w * scale) > sw or y0 + int(h * scale) > sh:
        return None
    cache = {}
    def q(px):
        if px not in cache:
            cache[px] = nearest_code(px)
        return cache[px]
    return structure([[q(tuple(rows[y0 + int(dy * scale)][x0 + int(dx * scale)]))
                       for dx in range(w)] for dy in range(h)])

def match_ratio(a, b, mask=None):
    """Coincidencia estrutural contando so as celulas OPACAS da arte.

    Nao compara classes absolutas (a ordem de rotulagem difere entre arte e
    tela): exige que celulas com a MESMA classe na arte tenham a mesma classe
    na tela, e que classes diferentes continuem diferentes.
    """
    pares = []
    for y, (ra, rb) in enumerate(zip(a, b)):
        for x, (ca, cb) in enumerate(zip(ra, rb)):
            if mask is None or mask[y][x]:
                pares.append((ca, cb))
    if not pares:
        return 0.0
    # Uma classe da arte pode aparecer em VARIOS tons na tela: a escala do
    # emulador mistura cores nas bordas das regioes (a moldura do heroi sai em
    # dois tons). O que NAO pode acontecer e classes diferentes da arte
    # compartilharem o mesmo tom — ai a estrutura se perdeu (ruido, sprite
    # errado, ou amostragem que achatou tudo numa cor).
    from collections import Counter
    uso = {}
    for ca, cb in pares:
        uso.setdefault(cb, Counter())[ca] += 1
    dono = {cb: cnt.most_common(1)[0][0] for cb, cnt in uso.items()}
    ok = sum(1 for ca, cb in pares if dono[cb] == ca) / len(pares)

    # COMPACTACAO: cada classe da arte tem que se concentrar em POUCOS tons.
    # Sem isto o criterio acima e permissivo demais — em ruido cada pixel tem
    # um tom proprio, logo cada tom vira "dono" trivial de si mesmo e o
    # casamento daria 100%. Foi o self-check que pegou isso.
    tons = {}
    for ca, cb in pares:
        tons.setdefault(ca, Counter())[cb] += 1
    fracoes = []
    for ca, cnt in tons.items():
        total = sum(cnt.values())
        top = sum(n for _, n in cnt.most_common(MAX_TONES_PER_CLASS))
        fracoes.append(top / total)
    compacto = sum(fracoes) / len(fracoes) if fracoes else 0.0
    return ok * compacto

def find_art(shot_path, art_path, at=None, min_match=DEFAULT_MIN_MATCH):
    """(problems, report). Procura a estrutura da arte na captura."""
    report = {"shot": shot_path, "art": art_path, "min_match": min_match}
    try:
        art, mask, aw, ah = art_structure(art_path)
    except (PngError, OSError, KeyError) as e:
        return [f"arte ilegivel: {e}"], report
    report["art_size"] = [aw, ah]
    try:
        sw, sh, _ = read_png_rgb(shot_path)
    except (PngError, OSError) as e:
        return [f"captura ilegivel: {e}"], report

    if at:
        cands = [(at[0] + dx, at[1] + dy)
                 for dy in range(-4, 3) for dx in range(-4, 3)]
    else:
        # Varredura cega da tela inteira e inviavel em Python puro (estourou
        # 2min). O localizador de sprite ja existente da a semente; em volta
        # dela basta uma vizinhanca pequena.
        try:
            from capture_evidence import largest_sprite_block
            blk = largest_sprite_block(shot_path)
        except Exception:
            blk = None
        if blk:
            _, bx0, _, by0, _ = blk
            cands = [(bx0 + dx, by0 + dy)
                     for dy in range(-6, 4) for dx in range(-6, 4)]
        else:
            from capture_evidence import game_area
            gx0, gy0, gx1, gy1 = game_area(sw, sh)
            cands = [(x, y)
                     for y in range(gy0, gy1 - ah, 4)
                     for x in range(gx0, gx1 - aw, 4)]
    best, best_at, best_scale = 0.0, None, None
    for (x, y) in cands:
        for scale in SCALES:
            st = shot_structure(shot_path, x, y, aw, ah, scale)
            if st is None:
                continue
            r = match_ratio(art, st, mask)
            if r > best:
                best, best_at, best_scale = r, (x, y), scale
        if best >= 0.999:
            break
    report["best_match"] = round(best, 4)
    report["found_at"] = list(best_at) if best_at else None
    report["scale"] = best_scale
    if best < min_match:
        return ([f"arte autoral NAO encontrada na tela (melhor coincidencia "
                 f"{best:.1%} < {min_match:.0%}) — a tela pode estar mostrando "
                 f"ruido, outro sprite, ou a arte corrompida"], report)
    return [], report

def exact_indexed_render(shot_path, art_path, at, transparent_rgb=None):
    """Compare exact SMS palette RGB at an explicitly aligned native origin.

    This mode is for static conversion probes at 1:1 VDP resolution. It checks
    every nontransparent source pixel against its indexed RGB value. When a
    uniform diagnostic background is known, transparent pixels can also be
    checked so stale name-table/VRAM content cannot hide behind the sprite.
    """
    report = {"shot": shot_path, "art": art_path, "mode": "exact_indexed",
              "at": list(at) if at else None, "transparent_rgb": transparent_rgb}
    if at is None:
        return ["--exact-indexed exige --at X,Y na escala nativa"], report
    try:
        art = read_indexed_png(art_path)
        sw, sh, screen = read_png_rgb(shot_path)
    except (PngError, OSError) as exc:
        return [f"arte/captura ilegível: {exc}"], report
    x0, y0 = at
    w, h = art["w"], art["h"]
    report["art_size"] = [w, h]
    if x0 < 0 or y0 < 0 or x0 + w > sw or y0 + h > sh:
        return ["recorte de arte fora da captura"], report
    if transparent_rgb is not None and (len(transparent_rgb) != 3 or
            any(not isinstance(v, int) or not 0 <= v <= 255 for v in transparent_rgb)):
        return ["transparent_rgb precisa ser uma tripla RGB 0..255"], report

    opaque_total = transparent_total = opaque_bad = transparent_bad = 0
    first = []
    for y, row in enumerate(art["pixels"]):
        for x, index in enumerate(row):
            actual = tuple(screen[y0 + y][x0 + x])
            if index == 0:
                if transparent_rgb is not None:
                    transparent_total += 1
                    if actual != tuple(transparent_rgb):
                        transparent_bad += 1
                        if len(first) < 8:
                            first.append({"x": x, "y": y, "source_index": 0,
                                          "expected": list(transparent_rgb),
                                          "actual": list(actual)})
                continue
            opaque_total += 1
            if index >= len(art["palette"]):
                return [f"índice {index} sem cor PLTE na fonte"], report
            expected = tuple(art["palette"][index])
            if actual != expected:
                opaque_bad += 1
                if len(first) < 8:
                    first.append({"x": x, "y": y, "source_index": index,
                                  "expected": list(expected), "actual": list(actual)})
    report.update({"opaque_pixels": opaque_total, "opaque_mismatches": opaque_bad,
                   "transparent_pixels_checked": transparent_total,
                   "transparent_mismatches": transparent_bad,
                   "first_mismatches": first})
    problems = []
    if opaque_bad:
        problems.append(f"{opaque_bad}/{opaque_total} pixels opacos divergem da paleta indexada")
    if transparent_bad:
        problems.append(f"{transparent_bad}/{transparent_total} pixels transparentes não mostram o fundo declarado")
    return problems, report

def _self_check():
    import tempfile, shutil, random
    from png_io import write_indexed_png, write_png_rgb
    from sms_palette import code_rgb
    d = tempfile.mkdtemp(prefix="smsfid_")
    try:
        # arte autoral 8x8: cruz (2 classes + fundo)
        pal = [(0, 0, 0), (255, 255, 255), (0, 170, 170)]
        px = []
        for y in range(8):
            px.append(bytes([1 if (x == 0 or x == 7 or y == 0 or y == 7)
                             else (2 if (x in (3, 4) or y in (3, 4)) else 0)
                             for x in range(8)]))
        art = os.path.join(d, "art.png")
        write_indexed_png(art, 8, 8, pal, px)

        # tela que CONTEM a arte (em cores DIFERENTES: so a estrutura importa)
        W = H = 32
        cor = {0: code_rgb((0, 0, 0)), 1: code_rgb((3, 3, 0)), 2: code_rgb((0, 0, 3))}
        rows = [[code_rgb((0, 0, 0))] * W for _ in range(H)]
        for y in range(8):
            for x in range(8):
                rows[12 + y][10 + x] = cor[px[y][x]]
        shot = os.path.join(d, "shot.png")
        write_png_rgb(shot, W, H, rows)
        p, r = find_art(shot, art, at=(10, 12))
        assert not p, f"arte presente deveria ser encontrada: {p} {r}"
        assert r["best_match"] >= 0.99, r

        # tela de RUIDO no mesmo lugar -> nao encontra
        rnd = random.Random(3)
        pal64 = [code_rgb((a, b, c)) for a in range(4) for b in range(4) for c in range(4)]
        noise_rows = [[rnd.choice(pal64) for _ in range(W)] for _ in range(H)]
        noise = os.path.join(d, "noise.png")
        write_png_rgb(noise, W, H, noise_rows)
        p, _ = find_art(noise, art, at=(10, 12))
        assert p, "ruido nao pode passar por arte autoral"

        # tela com OUTRO sprite (estrutura diferente) -> nao encontra
        rows2 = [[code_rgb((0, 0, 0))] * W for _ in range(H)]
        for y in range(8):
            for x in range(8):
                rows2[12 + y][10 + x] = cor[1 if (x + y) % 2 else 0]
        other = os.path.join(d, "other.png")
        write_png_rgb(other, W, H, rows2)
        p, _ = find_art(other, art, at=(10, 12))
        assert p, "sprite errado nao pode passar por arte autoral"

        # Conversão indexada SMS: todos os pixels opacos devem preservar RGB;
        # quando o fundo é uniforme, índice 0 também precisa mostrar esse fundo.
        exact_rows = [[(0, 0, 0)] * W for _ in range(H)]
        for y in range(8):
            for x in range(8):
                if px[y][x]:
                    exact_rows[12 + y][10 + x] = pal[px[y][x]]
        exact_shot = os.path.join(d, "exact.png")
        write_png_rgb(exact_shot, W, H, exact_rows)
        p, exact_report = exact_indexed_render(exact_shot, art, (10, 12), (0, 0, 0))
        assert not p and exact_report["opaque_mismatches"] == 0 and \
            exact_report["transparent_mismatches"] == 0, (p, exact_report)

        changed_rows = [list(row) for row in exact_rows]
        changed_rows[12][10] = (170, 0, 0)
        changed_shot = os.path.join(d, "exact_changed.png")
        write_png_rgb(changed_shot, W, H, changed_rows)
        p, changed_report = exact_indexed_render(changed_shot, art, (10, 12), (0, 0, 0))
        assert p and changed_report["opaque_mismatches"] > 0, \
            "pixel de conversão alterado deveria reprovar"

        dirty_rows = [list(row) for row in exact_rows]
        dirty_rows[13][11] = (255, 0, 255)  # índice 0 na fonte, sujeira no BG
        dirty_shot = os.path.join(d, "dirty_bg.png")
        write_png_rgb(dirty_shot, W, H, dirty_rows)
        p, dirty_report = exact_indexed_render(dirty_shot, art, (10, 12), (0, 0, 0))
        assert p and dirty_report["transparent_mismatches"] > 0, \
            "tilemap transparente sujo deveria reprovar"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] render_fidelity (comparação estrutural e pixel-a-pixel; "
          "reprova pixel divergente e lixo sob transparência)")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot")
    ap.add_argument("--art")
    ap.add_argument("--at", help="X,Y para checar uma posicao especifica")
    ap.add_argument("--min-match", type=float, default=DEFAULT_MIN_MATCH)
    ap.add_argument("--exact-indexed", action="store_true",
                    help="pixel-a-pixel em PNG 8-bit indexado e captura 1:1")
    ap.add_argument("--transparent-rgb", help="verifica pixels de índice 0 contra RRGGBB")
    ap.add_argument("--json")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()
    if not (a.shot and a.art):
        print("[FAIL] --shot e --art obrigatorios", file=sys.stderr)
        return 3
    at = None
    if a.at:
        x, _, y = a.at.partition(",")
        at = (int(x), int(y))
    if a.exact_indexed:
        transparent_rgb = None
        if a.transparent_rgb:
            raw = a.transparent_rgb.lstrip("#")
            if len(raw) != 6:
                print("[FAIL] --transparent-rgb exige RRGGBB", file=sys.stderr)
                return 3
            try:
                transparent_rgb = tuple(int(raw[i:i + 2], 16) for i in (0, 2, 4))
            except ValueError:
                print("[FAIL] --transparent-rgb exige hexadecimal RRGGBB", file=sys.stderr)
                return 3
        problems, report = exact_indexed_render(a.shot, a.art, at, transparent_rgb)
        if a.json:
            json.dump({"problems": problems, **report}, open(a.json, "w"), indent=2)
        if problems:
            for problem in problems:
                print(f"[FAIL] {problem}")
            return 1
        print(f"[PASS] conversão indexada exata: {report['opaque_pixels']} pixels opacos" +
              (f", {report['transparent_pixels_checked']} transparentes/fundo"
               if transparent_rgb else "") + f" em {at}")
        return 0
    if a.transparent_rgb:
        print("[FAIL] --transparent-rgb requer --exact-indexed", file=sys.stderr)
        return 3
    problems, report = find_art(a.shot, a.art, at, a.min_match)
    if a.json:
        json.dump({"problems": problems, **report}, open(a.json, "w"), indent=2)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        return 1
    print(f"[PASS] arte autoral CONFIRMADA na tela: {os.path.basename(a.art)} "
          f"em {report['found_at']} ({report['best_match']:.1%} de coincidencia "
          "estrutural)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
