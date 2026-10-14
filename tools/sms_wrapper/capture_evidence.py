#!/usr/bin/env python3
"""Gate EVIDENCIA — boot no emulador Emulicious + captura de janela verificada.

Cadeia real (nada simulado):
  1. localiza Emulicious.jar (emulators.json ou layout padrao)
  2. roda a ROM: java -jar Emulicious.jar -remotedebug 4901 rom.sms
  3. fecha dialogos de update, foca a janela principal
  4. captura a janela via spectacle -a (KDE/Wayland; DISPLAY herdado)
  5. detector de imagem vazia reprova capturas sem informacao
  6. escreve bundle emulator_evidence_v1 e encerra o emulador

NOTA HONESTA (licao L005): openMSX foi avaliado e NAO suporta Master System;
o adapter anterior (-machine sms) era especulacao e foi removido.

LIMITACOES DO HOST (L010, 2026-08-30) — captura do frame VIVO do jogo:
  1. DAP readbyte/readword retorna '$0' para QUALQUER endereco (até 1+1 -> $0):
     o avaliador do contexto 'repl' nao avalia de verdade -> NAO usar p/ estado.
  2. import -window <CANVAS INTERNA> congela no frame X inicial (Java/OpenGL
     numa camada nao-pixmap). ESCOPADO em 2026-09-01: na JANELA DE TOPO nao
     congela — 3 capturas consecutivas de ROM animada deram 3 hashes distintos.
     Por isso o caminho primario e `import -window <janela principal>` (§34).
     (texto original abaixo)
     import -window <canvas> congela no frame X inicial (render via Java/OpenGL
     em camada nao-pixmap): 3 capturas = hash identico. NAO reflete o estado vivo.
  3. spectacle -a / -f capturam o compositor: janela do jogo misturada com
     interface (contaminacao de cor nas bordas) e foco via windowactivate oscila.
  Consequencia: a LOGICA de vitoria e a RENDERIZACAO estao provadas por outros
  canais (simulacao exata + capturas 283x282), mas o FRAME especifico de um
  estado transitorio (VITORIA) nao e capturavel de forma confiavel neste host.
  Proximo passo: screenshot NATIVO do Emulicious (tecla F12 configurada) que
  grava o framebuffer do canvas direto em disco.

Uso:
  capture_evidence.py --project <dir> --rom <rom.sms> [--out nome]
  capture_evidence.py --check-image <png>     # so valida captura
  capture_evidence.py --self-check

Exit: 0 evidencia ok | 1 captura invalida | 2 ambiente ausente | 3 uso
"""
import sys, os, json, argparse, subprocess, shutil, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png_io import read_png_luma_samples, read_png_rgb, png_size, PngError

HERE = os.path.dirname(os.path.abspath(__file__))
EMU_JSON = os.path.normpath(os.path.join(HERE, "..", "emuladores", "emulators.json"))
DEFAULT_JAR = os.path.normpath(os.path.join(HERE, "..", "emuladores",
                                            "emulicious", "Emulicious.jar"))

def resolve_jar():
    cfg = {}
    if os.path.exists(EMU_JSON):
        try:
            cfg = json.load(open(EMU_JSON))
        except json.JSONDecodeError:
            cfg = {}
    cand = cfg.get("emulicious_jar") or DEFAULT_JAR
    if not os.path.isabs(cand) and not os.path.exists(cand):
        # relativo no emulators.json -> resolver contra a raiz do workspace
        cand = os.path.normpath(os.path.join(HERE, "..", "..", cand))
    return cand if os.path.exists(cand) else None

def _run(cmd, timeout=30):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None

def _main_window_id():
    """Janela principal do emulador (ignora dialogos e a janela 'platform-').

    O nome NAO e estavel: parado a janela e 'Emulicious', rodando ela vira
    'Emulicious - 100% (60 fps)' — e o titulo e justamente de onde o
    measure_fps.py tira o fps. Exigir igualdade exata (como estava aqui) fazia
    a janela sumir assim que a ROM comecava a rodar, que e o unico momento em
    que ha algo para fotografar.
    """
    r = _run(["xdotool", "search", "--name", "Emulicious"])
    if not r or r.returncode != 0:
        return None
    ids = [x.strip() for x in r.stdout.splitlines() if x.strip().isdigit()]
    for i in ids:
        n = _run(["xdotool", "getwindowname", i])
        name = n.stdout.strip() if n else ""
        if name == "Emulicious" or name.startswith("Emulicious - "):
            return i
    return None

def _input_window_id(main_id=None):
    """Janela que recebe o joypad no Emulicious Java/AWT.

    A moldura `Emulicious` pode ficar focada enquanto o listener de teclas
    está na subjanela nativa `XCanvasPeer`. Enviar o evento apenas à moldura
    produz uma captura aparentemente válida, mas sem controle — exatamente o
    falso negativo que o probe de gameplay detectou.
    """
    r = _run(["xdotool", "search", "--name", "XCanvasPeer"])
    if not r or r.returncode != 0:
        return main_id
    for i in r.stdout.split():
        g = _run(["xdotool", "getwindowgeometry", "--shell", i])
        if not g:
            continue
        vals = dict(line.split("=", 1) for line in g.stdout.splitlines()
                    if "=" in line)
        if int(vals.get("WIDTH", "0")) >= SMS_W:
            return i
    return main_id

# Acima disto a "captura" e a tela inteira, nao a janela do emulador (L017).
DESKTOP_PIXELS = 1_500_000

def image_informative(path, min_variance=40.0, box=None):
    """Captura valida tem variacao real de LUMA (tela branca/preta lisa reprova)."""
    try:
        vals = read_png_luma_samples(path, box=box)
    except PngError:
        return False, f"{path}: PNG ilegivel"
    n = len(vals)
    if not n:
        return False, "imagem vazia"
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / n
    return var >= min_variance, f"variancia de luma={var:.1f} (min {min_variance})"

SMS_W, SMS_H = 256, 192          # canvas do VDP; a moldura fica FORA dela
# Escalas que o Emulicious realmente grava no .ini. Nao interpolar.
_EMU_SCALES = (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 4.0, 5.0)


def capture_scale(w, h):
    """Fator da janela sobre a canvas nativa 256×192 (L040).

    Limiares de forma em pixels da janela invertem o veredito quando o
    Emulicious grava Scale=2.25 no ini: lutador 32×64 vira 72×144 e cai
    no filtro. A escala e entrada declarada do gate, nao um detalhe de UI.
    """
    usable_w, usable_h = w, max(1, h - 25)
    best = 1.0
    for s in _EMU_SCALES:
        if 256 * s <= usable_w + 12 and 192 * s <= usable_h + 12:
            best = s
    return best


def game_area(w, h):
    """(x0, y0, x1, y1) da area de JOGO, para captura com ou sem moldura.

    `import -window` preserva a barra de menu do Emulicious acima da canvas. Em
    capturas reais deste acervo, tanto a janela compacta 283x282 quanto a
    captura sem moldura 256x217 colocam a canvas SMS 256x192 em y=25; na janela
    compacta ela fica centralizada horizontalmente e sobra espaço preto abaixo.
    O antigo `h - SMS_H` apontava para y=90 na janela 283x282 e fazia o medidor
    ler o fundo, não o HUD. Com Scale>1 a canvas cresce; o recorte acompanha.
    """
    s = capture_scale(w, h)
    cw, ch = int(round(SMS_W * s)), int(round(SMS_H * s))
    x0 = max(0, (w - cw) // 2)
    y0 = 25 if h >= ch + 25 else max(0, h - ch)
    return (x0, y0, min(w, x0 + cw), min(h, y0 + ch))

def viewport_box(path):
    """Metade central da imagem = viewport do jogo dentro da janela do emulador."""
    w, h = png_size(path)
    return (w // 4, h // 4, (3 * w) // 4, (3 * h) // 4)

def _luma_grid(path, box):
    from png_io import PngError as _E
    vals = read_png_luma_samples(path, box=box)   # pode lancar
    return vals

def viewport_diff(path_a, path_b):
    """Fracao de amostras de luma do viewport que mudou (>16 níveis)."""
    box = viewport_box(path_a)
    wa, ha = png_size(path_a); wb, hb = png_size(path_b)
    if (wa, ha) != (wb, hb):
        return 0.0
    try:
        va = _luma_grid(path_a, box)
        vb = _luma_grid(path_b, box)
    except PngError:
        return 0.0
    if len(va) != len(vb):
        return 0.0
    changed = sum(1 for x, y in zip(va, vb) if abs(x - y) > 16)
    return changed / max(1, len(va))

def player_region_diff(path_a, path_b):
    """Fracao alterada no corredor inicial do hero.

    O VANTA-9 é uma silhueta deliberadamente esparsa em 16x16 lógico; após
    quantização, seus fragmentos não formam um componente conexo grande o
    bastante para `largest_sprite_block`. O boss, ao contrário, forma o maior
    componente e se move sozinho. Esta região exclui o boss e a HUD, então a
    mudança só pode vir do hero/projétil do teste; o limiar evita ruído de
    captura e é registrado no bundle.
    """
    try:
        wa, ha = png_size(path_a)
        wb, hb = png_size(path_b)
        if (wa, ha) != (wb, hb):
            return 0.0, None
        gx0, gy0, _, _ = game_area(wa, ha)
        s = capture_scale(wa, ha)
        box = (gx0 + int(24 * s), gy0 + int(72 * s),
               gx0 + int(128 * s), gy0 + int(152 * s))
        va = read_png_luma_samples(path_a, box=box)
        vb = read_png_luma_samples(path_b, box=box)
    except (PngError, OSError):
        return 0.0, None
    if len(va) != len(vb) or not va:
        return 0.0, box
    changed = sum(1 for x, y in zip(va, vb) if abs(x - y) > 16)
    return changed / len(va), box

def press_keys(window_id, spec):
    """Executa spec 'Tecla=ms,Tecla=ms' no canal deste host (L039).

    Wayland/KWin: kdotool + ydotool (uinput). X11: xdotool com foco
    verificado. XTEST neste host nao atravessa o KWin — nao usar como
    prova de gameplay. Retorna [(tecla, ms)] enviados; lista curta =
    foco falhou (fail-closed).
    """
    import emulator_input as ei
    input_id = _input_window_id(window_id)
    done, backend, focused = ei.press_spec(
        spec, x11_window=window_id, x11_input=input_id)
    if not done:
        print("[FAIL] foco/canal nao ficou no emulador para '%s' "
              "(backend=%s, focused=%s) — tecla iria para outra janela "
              "(L007/L039)" % (spec, backend, focused))
    return done



_KEY_DIR = {
    "Right": (1, 0), "Left": (-1, 0), "Up": (0, -1), "Down": (0, 1),
    "KP_Right": (1, 0), "KP_Left": (-1, 0), "KP_Up": (0, -1), "KP_Down": (0, 1),
}


def _native_delta(step):
    """Deslocamento em pixels da canvas 256×192 (L040)."""
    s = float(step.get("capture_scale") or 1.0) or 1.0
    ndx = step.get("native_dx")
    ndy = step.get("native_dy")
    if ndx is None:
        ndx = (step.get("sprite_dx") or 0) / s
    if ndy is None:
        ndy = (step.get("sprite_dy") or 0) / s
    return ndx, ndy


def _direction_ok(step, thresh=8):
    """Tecla de eixo exige sinal coerente; tecla sem eixo aceita |d|>=thresh."""
    key = (step.get("key") or "").split("+")[-1]
    ndx, ndy = _native_delta(step)
    vec = _KEY_DIR.get(key)
    if vec is None:
        return abs(ndx) >= thresh or abs(ndy) >= thresh
    sx, sy = vec
    if sx:
        return ndx * sx >= thresh
    if sy:
        return ndy * sy >= thresh
    return False


def _identity_stable(steps):
    """Area do blob nao pode saltar para outro objeto (L038/L042)."""
    areas = []
    for s in steps:
        bb = s.get("sprite_bbox")
        if bb and len(bb) >= 1 and bb[0]:
            areas.append(bb[0])
    if len(areas) < 2:
        return True
    ref = areas[0]
    slack = max(ref * 0.5, 20)
    return all(abs(a - ref) <= slack for a in areas)


def interaction_verdict(steps):
    """§29 — gameplay se fecha pelo DESLOCAMENTO do objeto controlado. PURA.

    Forte exige simultaneamente (L038–L040):
      - deslocamento nativo >= 8px NA DIRECAO da tecla (nao abs(dx));
      - identidade do blob estavel;
      - se probe_keys foi observado, pelo menos um passo com eco != 0.
    Fraco: fracao da regiao do corredor do hero mudou >= 2% — serve a
    DIAGNOSTICO no bundle e NUNCA fecha o eixo sozinho: scroll, animacao de
    boss e morte mudam a regiao sem input nenhum. A versao anterior fechava
    com `forte or fraco` (L035): o gate violava exatamente a regra que
    citava nos proprios comentarios.
    """
    weak = any(s.get("player_region_changed", 0.0) >= 0.02 for s in steps)
    echoes = [s.get("probe_keys") for s in steps if "probe_keys" in s]
    if echoes and all(int(x or 0) == 0 for x in echoes):
        return False, weak
    if not _identity_stable(steps):
        return False, weak
    strong = any(_direction_ok(s) for s in steps)
    return strong, weak


def largest_sprite_block(path, min_px=25, x_max=None):
    """Maior aglomerado conexo de cor saturada na area de jogo -> (n, x0, x1, y0, y1).

    Serve para medir DESLOCAMENTO do objeto controlado, em vez de "quanto da tela
    mudou". A metrica global de luma nao distingue o jogador obedecendo de um
    inimigo caindo, de uma morte, ou (antes do L017) do desktop do usuario.
    """
    try:
        w, h, rows = read_png_rgb(path)
    except (PngError, OSError):
        return None
    gx0, gy0, gx1, gy1 = game_area(w, h)       # adapta-se a captura com/sem moldura
    s = capture_scale(w, h)
    min_native = min_px * s * s
    pts = {(x, y) for y in range(gy0, gy1 - 8) for x in range(gx0 + 4, gx1 - 4)
           if max(rows[y][x]) - min(rows[y][x]) > 60 and max(rows[y][x]) > 110}
    seen, best = set(), None
    for pt in pts:
        if pt in seen:
            continue
        stack, comp = [pt], []
        while stack:
            c = stack.pop()
            if c in seen or c not in pts:
                continue
            seen.add(c); comp.append(c)
            x, y = c
            stack += [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
        if len(comp) < min_native:
            continue
        xs = [a for a, _ in comp]; ys = [b for _, b in comp]
        bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        # Tem que ter FORMA DE SPRITE: colunas de estrelas e bordas de janela
        # formam faixas finas e altissimas e sequestravam a medicao.
        # Limiares em pixels NATIVOS (L040): 40px era o teto do heroi 16x16
        # do laboratorio; lutador 32x64 (MSSF2T) e legal. Em Scale=2.25 o
        # 32x64 vira 72x144 e o filtro absoluto (bw<=48) sequestrava a
        # barra de vida. Faixas de chrome continuam cortadas pela razao 3:1.
        bw_n, bh_n = bw / s, bh / s
        if not (6 <= bw_n <= 48 and 6 <= bh_n <= 80):
            continue
        if max(bw, bh) > 3 * min(bw, bh):
            continue
        if x_max is not None and max(xs) >= x_max:
            continue
        if best is None or len(comp) > best[0]:
            best = (len(comp), min(xs), max(xs), min(ys), max(ys))
    return best

def _shoot_window(shot, wid, tries=4):
    """Captura a JANELA do emulador, provando pelo tamanho que nao pegou o desktop.

    L017: `spectacle -a` fotografa a janela ATIVA. Se o emulador perde o foco
    (dialogo, outra app, instancia zumbi), a "evidencia" vira um screenshot do
    desktop do usuario — que passa no detector de vacuidade e pode conter
    conteudo pessoal. Aqui isso e detectado, o arquivo e descartado e a captura
    e refeita depois de reativar a janela.
    """
    usa_import = shutil.which("import") is not None
    for attempt in range(tries):
        _run(["xdotool", "windowactivate", "--sync", str(wid)])
        _run(["xdotool", "windowraise", str(wid)])
        _run(["xdotool", "windowfocus", "--sync", str(wid)])
        time.sleep(1.2 if attempt == 0 else 2.0)
        if os.path.exists(shot):
            os.remove(shot)
        if usa_import:
            # ALVO POR ID (L007/L008): `spectacle -a` fotografa a janela ATIVA e
            # ja capturou o desktop do usuario (L017). `import -window` nao tem
            # como pegar outra janela — e ainda vem sem a moldura.
            r = _run(["import", "-window", str(wid), shot], timeout=60)
        else:
            r = _run(["spectacle", "-a", "-b", "-n", "-o", shot], timeout=60)
        if not os.path.exists(shot):
            continue
        try:
            w, h = png_size(shot)
        except (PngError, OSError):
            continue
        if w * h < DESKTOP_PIXELS:
            return True, (w, h)
        os.remove(shot)          # desktop: descarta (pode ter conteudo pessoal)
    return False, None

def capture(project, rom, out_name="evidence", keep=False, settle_frames=300,
            press_spec=None):
    jar = resolve_jar()
    if not jar:
        print("[FAIL_AMBIENTE] Emulicious.jar nao encontrado. Instale em "
              "tools/emuladores/emulicious/ ou registre 'emulicious_jar' em "
              "tools/emuladores/emulators.json. Gate NAO simula evidencia.")
        return 2
    missing = [t for t in ("java", "xdotool") if not shutil.which(t)]
    if missing:
        print(f"[FAIL_AMBIENTE] ferramentas ausentes: {', '.join(missing)}")
        return 2
    # `import` (ImageMagick) e o caminho primario: alveja a janela por ID.
    # `spectacle` fica como fallback — e so ele precisa do shim de libavcodec
    # (L007). Sem nenhum dos dois nao ha captura.
    if not (shutil.which("import") or shutil.which("spectacle")):
        print("[FAIL_AMBIENTE] nenhuma ferramenta de captura: instale "
              "ImageMagick (import) ou spectacle")
        return 2
    # Atração determinística é válida para demonstrar arte e coreografia, mas
    # invalida um teste de controle baseado apenas no deslocamento final: o
    # sprite já se moveria sem a tecla. O projeto pode voltar a habilitar o
    # claim quando o harness receber input real ou fornecer um build de teste
    # sem a atração.
    if press_spec:
        main_c = os.path.join(project, "src", "main.c")
        try:
            source = open(main_c, encoding="utf-8").read()
        except OSError:
            source = ""
        if "g_demo_mode = 1" in source and "g_demo_mode = 0" not in source:
            print("[FAIL] gameplay inconclusivo: a ROM possui atração automática; "
                  "deslocamento durante o intervalo não prova a tecla. Use um "
                  "build sem g_demo_mode para testar controle humano.")
            return 1
    # L017/L057: com outra instancia viva, xdotool acha a janela errada e o
    # spectacle -a captura a janela ATIVA (ja capturou o desktop do usuario).
    from emulator_session import require_no_stale
    if not require_no_stale(why="captura de evidencia"):
        return 2
    out_dir = os.path.join(project, "out", "evidence")
    os.makedirs(out_dir, exist_ok=True)
    shot = os.path.join(out_dir, f"{out_name}.png")
    log_path = os.path.join(out_dir, f"{out_name}_emu.log")
    logf = open(log_path, "w")
    # settle: frames de jogo antes da captura (~5s a 60fps)
    proc = subprocess.Popen(
        ["java", "-jar", jar, "-remotedebug", "4901", "-set", "Update=0",
         os.path.abspath(rom)],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        wid = None
        for _ in range(40):                      # ~20s esperando janela
            time.sleep(0.5)
            if proc.poll() is not None:
                break
            r = _run(["xdotool", "search", "--name", "Update Behaviour"])
            if r and r.returncode == 0:          # dialogo de update atrapalha foco
                for d in r.stdout.split():
                    _run(["xdotool", "windowclose", d.strip()])
            wid = _main_window_id()
            if wid:
                time.sleep(max(0.0, settle_frames / 60.0))
                break
        if not wid or proc.poll() is not None:
            print(f"[FAIL] emulador nao abriu janela (log: {log_path})")
            return 1
        ok_win, dim = _shoot_window(shot, wid)
        if not ok_win:
            print("[FAIL] nao foi possivel capturar a JANELA do emulador (so o "
                  "desktop). Arquivos descartados — podem conter conteudo "
                  "pessoal. Verifique foco/instancias (L017).")
            return 1
        ok, why = image_informative(shot)
        ok_vp, why_vp = image_informative(shot, box=viewport_box(shot))
        informative = ok and ok_vp
        bundle = {
            "project": os.path.basename(os.path.abspath(project)),
            "rom": rom,
            "screenshot": shot,
            "informative": informative,
            "detail": f"janela: {why} | viewport central: {why_vp}",
            "tool": "emulicious-2026-03-27+xdotool+spectacle",
            "chain_of_custody": [
                f"launch: java -jar {os.path.basename(jar)} -remotedebug 4901",
                "window: xdotool search/activate 'Emulicious'",
                "capture: spectacle -a (janela ativa)",
                "check: luma da janela INTEIRA e do VIEWPORT CENTRAL",
            ],
        }
        json.dump(bundle, open(os.path.join(out_dir, f"{out_name}.json"), "w"),
                  indent=2)
        if not ok:
            print(f"[FAIL] captura sem informacao ({why}) — tela branca/vazia?")
            return 1
        if not ok_vp:
            print(f"[FAIL] viewport central sem informacao ({why_vp}) — "
                  "ROM nao renderiza? Janela sem o jogo em foco?")
            return 1
        print(f"[PASS] evidencia registrada: {shot}")
        print(f"       janela {why} | viewport {why_vp}")
        # ---- modo gameplay: input script + diffs por passo -----------------
        if press_spec:
            steps = []
            prev = shot
            # o sprite pode sumir em frames de flash (invulnerabilidade):
            # compara sempre contra a ULTIMA posicao conhecida, nao contra None.
            # O boss ocupa 64x64 e também se move na atração. Para o claim de
            # input, medir apenas o corredor inicial do hero separa o objeto
            # controlado da coreografia do inimigo; o limite é coordenada da
            # canvas capturada, não uma leitura do desktop.
            try:
                sw, sh = png_size(shot)
                gx0, _, _, _ = game_area(sw, sh)
                scale = capture_scale(sw, sh)
                player_x_max = gx0 + int(160 * scale)
            except (PngError, OSError):
                player_x_max = None
                scale = 1.0
            last_blk = largest_sprite_block(shot, x_max=player_x_max)
            for i, (key, ms) in enumerate(press_keys(wid, press_spec), 1):
                # Passos curtos preservam janelas transitórias (tiro/impacto)
                # sem perder a prova de deslocamento do input.
                time.sleep(0.1)
                step_shot = os.path.join(out_dir, f"{out_name}_step{i}.png")
                # L017: passo tambem precisa provar que fotografou a JANELA.
                # Era exatamente aqui que o desktop vazava: a comparacao entre
                # dois screenshots de desktop dava "interacao provada" medindo
                # a area de trabalho do usuario mudando, nao o jogo.
                ok_step, _ = _shoot_window(step_shot, wid)
                if not ok_step:
                    print(f"[FAIL] passo {i}: so foi possivel capturar o desktop, "
                          "nao a janela do emulador (L017). Descartado.")
                    return 1
                frac = viewport_diff(prev, step_shot)
                blk = largest_sprite_block(step_shot, x_max=player_x_max)
                dx = dy = None
                if blk and last_blk:
                    dx = ((blk[1] + blk[2]) // 2) - ((last_blk[1] + last_blk[2]) // 2)
                    dy = ((blk[3] + blk[4]) // 2) - ((last_blk[3] + last_blk[4]) // 2)
                if blk:
                    last_blk = blk
                region_frac, region_box = player_region_diff(prev, step_shot)
                steps.append({"key": key, "ms": ms, "shot": step_shot,
                              "viewport_changed": round(frac, 4),
                              "sprite_bbox": list(blk) if blk else None,
                              "sprite_dx": dx, "sprite_dy": dy,
                              "native_dx": None if dx is None else round(dx / scale, 2),
                              "native_dy": None if dy is None else round(dy / scale, 2),
                              "capture_scale": scale,
                              "player_region_changed": round(region_frac, 4),
                              "player_region_box": list(region_box)
                              if region_box else None})
                prev = step_shot
            # §29 (L035): so o sinal FORTE fecha; o fraco fica no bundle
            # como diagnostico. Ver interaction_verdict().
            moved_sprite, moved_player_region = interaction_verdict(steps)
            moved = moved_sprite
            bundle = json.load(open(os.path.join(out_dir, f"{out_name}.json")))
            bundle["gameplay"] = {"press_script": press_spec, "steps": steps,
                                  "capture_scale": scale,
                                  "sprite_displacement_proven": moved_sprite,
                                  "player_motion_region_proven": moved_player_region,
                                  "interaction_proven": moved}
            json.dump(bundle, open(os.path.join(out_dir, f"{out_name}.json"), "w"),
                      indent=2)
            if not moved:
                print("[FAIL] interacao nao provada: o sprite controlado nao "
                      "se deslocou >= 8px na direcao comandada (§29). "
                      "Mudanca de regiao/viewport sem deslocamento e sinal "
                      "fraco e NAO fecha o eixo; confira o canal de input.")
                return 1
            for s in steps:
                print(f"       [{s['key']}={s['ms']}ms] viewport mudou "
                      f"{s['viewport_changed']*100:.1f}%")
            print("[PASS] GAMEPLAY provado por observacao (input -> mudanca)")
        return 0
    finally:
        if not keep and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        logf.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--rom")
    ap.add_argument("--session",help="private emulator session ID/path; never focus the host desktop")
    ap.add_argument("--input-script",help="JSON sequence with durations in VDP frames")
    ap.add_argument("--frames", type=int, default=300,
                    help="frames de jogo antes da captura (default 300)")
    ap.add_argument("--out", default="evidence")
    ap.add_argument("--keep", action="store_true",
                    help="nao encerrar o emulador apos a captura")
    ap.add_argument("--press", default=None,
                    help="script de input 'Right=1500,Down=800' p/ modo GAMEPLAY")
    ap.add_argument("--check-image")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        import tempfile
        from png_io import write_indexed_png
        d = tempfile.mkdtemp(prefix="smsev_")
        blank = os.path.join(d, "blank.png")
        write_indexed_png(blank, 32, 24, [(255, 255, 255)], [bytes([0] * 32)] * 24)
        ok, _ = image_informative(blank)
        assert not ok, "captura branca deveria ser reprovada"
        noisy = os.path.join(d, "noisy.png")
        rows = [bytes([(i + j) & 1 for j in range(64)]) for i in range(48)]
        write_indexed_png(noisy, 64, 48, [(0, 0, 0), (255, 255, 255)], rows)
        ok2, _ = image_informative(noisy)
        assert ok2, "captura com padrao deveria passar"
        pa = os.path.join(d, "player_a.png")
        pb = os.path.join(d, "player_b.png")
        base = [bytes([0] * 256) for _ in range(217)]
        moved_rows = [bytearray(row) for row in base]
        for y in range(105, 137):
            for x in range(40, 72):
                moved_rows[y][x] = 1
        write_indexed_png(pa, 256, 217, [(0, 0, 0), (255, 255, 255)], base)
        write_indexed_png(pb, 256, 217,
                          [(0, 0, 0), (255, 255, 255)], moved_rows)
        frac, box = player_region_diff(pa, pb)
        assert box == (24, 97, 128, 177) and frac >= 0.02, \
            "regiao do hero nao detectou movimento da fixture"
        # §29/L035: a regressao exata da linha `moved = forte or fraco` —
        # sinal fraco sozinho NAO fecha gameplay (a fixture abaixo e o caso
        # que o gate antigo APROVAVA e a regra proibe).
        assert interaction_verdict([{"key": "Right", "sprite_dx": 8,
                                     "player_region_changed": 0.0}]) == \
            (True, False), "sinal forte deixou de fechar"
        assert interaction_verdict([{"key": "Right", "sprite_dx": 0,
                                     "player_region_changed": 0.5}]) == \
            (False, True), "sinal fraco sozinho fechou o eixo (§29 violado)"
        assert interaction_verdict([{"key": "Right", "sprite_dx": 0,
                                     "player_region_changed": 0.0}]) == \
            (False, False), "sem sinal algum fechou o eixo"
        # L038: Right com blob andando para a ESQUERDA nao fecha.
        assert interaction_verdict([{"key": "Right", "sprite_dx": -32,
                                     "player_region_changed": 0.0}]) == \
            (False, False), "L038: direcao oposta fechou o eixo"
        # L039: eco de teclado observado e morto nao fecha, mesmo com dx certo.
        assert interaction_verdict([{"key": "Right", "sprite_dx": 32,
                                     "probe_keys": 0,
                                     "player_region_changed": 0.0}]) == \
            (False, False), "L039: probe_keys=0 fechou o eixo"
        assert interaction_verdict([{"key": "Right", "sprite_dx": 32,
                                     "probe_keys": 0x08,
                                     "player_region_changed": 0.0}]) == \
            (True, False), "eco de input valido deixou de fechar"
        # L040: limiares de forma em pixels nativos. Janela 2.25x, lutador 32x64.
        big_w, big_h = 576, 457
        assert capture_scale(big_w, big_h) == 2.25, capture_scale(big_w, big_h)
        assert capture_scale(283, 282) == 1.0
        scaled = os.path.join(d, "scaled_fighter.png")
        pal = [(0, 0, 0), (220, 40, 40)]
        rows = [bytearray(big_w) for _ in range(big_h)]
        # canvas comeca em y=25; lutador 72x144 = 32x64 nativos
        for y in range(25 + 40, 25 + 40 + 144):
            for x in range(90, 90 + 72):
                rows[y][x] = 1
        write_indexed_png(scaled, big_w, big_h, pal, rows)
        blk = largest_sprite_block(scaled)
        assert blk, "L040: lutador 32x64 em Scale=2.25 deveria ser visto"
        bw = blk[2] - blk[1] + 1
        bh = blk[4] - blk[3] + 1
        assert 60 <= bw <= 90 and 120 <= bh <= 160, (bw, bh)
        shutil.rmtree(d)
        print("[SELF-CHECK OK] evidence (imagem vazia, direcao, eco, escala nativa)")
        return 0
    if args.check_image:
        ok, why = image_informative(args.check_image)
        print(("[PASS] " if ok else "[FAIL] ") + why)
        return 0 if ok else 1
    if args.session:
        from session_bridge.isolated import load,sha,request,sequence,capture as private_capture,publish
        from pathlib import Path
        try:
            root,meta=load(args.session)
            if args.rom and sha(args.rom)!=meta["rom_sha256"]:raise ValueError("--rom differs from session ROM")
            if args.press:raise ValueError("private input uses --input-script in frames, not --press in milliseconds")
            if args.input_script:
                with open(args.input_script) as src:sequence(root,json.load(src))
            else:request(root,"step",args.frames)
            record=private_capture(root,args.out+".png")
            bundle=publish(root,args.out+".png",Path(args.project)/"out/evidence/sessions")
            print("[PASS] framebuffer da sessao: "+str(bundle))
            print("Input recebido/aplicado exige observacao da ROM para claim de gameplay.")
            return 0
        except (OSError,RuntimeError,ValueError) as e:
            print("[FAIL] "+str(e),file=sys.stderr);return 2
    if not args.rom:
        print("[FAIL] --rom obrigatorio (ou use --check-image / --self-check)",
              file=sys.stderr)
        return 3
    sys.exit(capture(args.project, args.rom, args.out, args.keep, args.frames,
                     args.press))

if __name__ == "__main__":
    sys.exit(main())
