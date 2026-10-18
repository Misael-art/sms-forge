#!/usr/bin/env python3
"""measure_frame_advance.py — o LOOP DA ROM avancou? (nao "o host aguentou")

Licao L013. O `measure_fps.py` le o titulo da janela ("Emulicious - 100%
(60 fps)"). Isso e a velocidade de EMULACAO: quanto o host conseguiu
processar. Uma ROM parada num `while(1){}` mantem o titulo em 60 fps, porque
o Z80 emulado continua girando a 3.58MHz — so nao esta desenhando nada novo.
O eixo `fps_constante` fechado so pelo titulo prova o emulador, nao o jogo.

A L013 ja tinha proposto o instrumento certo (contador na tela) e ele foi
substituido pelo mais fraco. Aqui ele volta, sem a parte fragil:

  A L013 dizia "OCR de digitos hex". Ler o glifo exige conhecer a fonte
  (SMS_autoSetUpTextRenderer traz a do SMSlib, que so existe dentro do
  SMSlib.lib). Nao e preciso: para medir TAXA basta contar QUANTAS VEZES o
  bloco 8x8 do digito MUDOU. Nao importa que digito e — importa que trocou.

  O HUD da arena_nocturna imprime tres nibbles de g_frame (hud.c:80-86):
      (29,0) = (g_frame>>7)&0xF   -> troca a cada 128 frames
      (30,0) = (g_frame>>3)&0xF   -> troca a cada   8 frames
      (31,0) =  g_frame    &0xF   -> troca a cada   1 frame

  fps = (n_trocas - 1) * periodo_do_digito / (t_ultima_troca - t_primeira)

  Medir entre a PRIMEIRA e a ULTIMA troca, e nao sobre a janela inteira,
  elimina a quantizacao de borda (a janela comeca e acaba no meio de um
  periodo). Com periodo 128 numa janela de 16s a borda vale +-8 fps — foi ela
  que fez uma ROM de 60 fps ser medida como 63.

Anti-aliasing (Nyquist): amostrar mais rapido que a troca, se nao transicoes
se perdem e o fps sai BAIXO (nunca alto — o erro e conservador). O digito de
128 frames troca a cada ~2.1s a 60fps. A folga e conferida sobre o intervalo
MEDIDO, nunca sobre o pedido na linha de comando.

Uso: measure_frame_advance.py --rom X.sms [--session ID] [--cell 29,0]
                              [--period 128] [--seconds 12] [-o saida.json]
                              [--self-check]
Exit: 0 avanco provado | 1 ROM nao avancou / fora da faixa | 2 ambiente
"""
import sys, os, json, time, argparse, subprocess, shutil, hashlib, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from png_io import read_png_rgb, PngError            # noqa: E402
import capture_evidence as CE                        # noqa: E402
from emulator_session import require_no_stale        # noqa: E402

TILE = 8
MIN_OVERSAMPLE = 3.0     # amostras por troca do digito; abaixo disso nao mede
# Um tile de texto tem 2 tons (fundo + traco); o backdrop piscando pode somar
# mais um. Acima disso ha OUTRA coisa sobre a celula — no laboratorio, um
# inimigo caindo (ex[]=190 passa por cima da coluna 24). A amostra e
# descartada em vez de virar "avanco do contador": descartar so pode fazer o
# fps medido sair BAIXO (o erro e conservador), nunca inflado.
MAX_CELL_COLORS = 4
# Amostras consecutivas para um estado ser considerado real (anti-rasgo).
MIN_RUN = 2
# Estados completos minimos para a mediana significar alguma coisa.
MIN_STATES = 5
# Dispersao maxima em torno da mediana para o ritmo ser chamado de CONSTANTE.
TOLERANCIA = 0.10
FPS_MIN, FPS_MAX = 50, 60


def cell_signature(rows, x0, y0, col, row, scale=1.0):
    """Assinatura do tile (col,row) da area de jogo na escala da captura. PURA.

    `rows` e o formato de png_io.read_png_rgb: lista de linhas, cada linha uma
    lista de tuplas (r,g,b) — NAO bytes planos.

    Assina a FORMA do glifo, nao as cores. O laboratorio pisca a cor de fundo
    a cada 8 frames (main.c:219, SMS_setBackdropColor) e os pixels de cor 0 do
    tile deixam o backdrop aparecer. Um hash do RGB cru contava esse flash como
    troca do contador: 18 trocas em 25s onde 60fps dariam 11.7, resultando num
    "92 fps" que nao media coisa alguma.

    Binarizar por "este pixel e a cor dominante da celula?" e imune a isso: se
    o fundo inteiro muda de cor, ele continua sendo o dominante e a mascara nao
    se mexe. So a troca do desenho do digito muda a mascara.
    """
    if scale <= 0:
        return None
    tile_size = int(round(TILE * scale))
    px = x0 + int(round(col * TILE * scale))
    py = y0 + int(round(row * TILE * scale))
    if (not rows or py < 0 or px < 0 or
            py + tile_size > len(rows) or
            px + tile_size > len(rows[0])):
        return None
    cells = [rows[py + dy][px + dx][:3]
             for dy in range(tile_size) for dx in range(tile_size)]
    if len(set(cells)) > MAX_CELL_COLORS:
        return None            # celula contaminada; amostra descartada
    modal = max(set(cells), key=cells.count)
    mask = bytes(1 if c != modal else 0 for c in cells)
    return hashlib.sha1(mask).hexdigest()[:12]


def canvas_viewport(w, h):
    """Return (scale, x0, y0) for a canvas fitted inside XCanvasPeer.

    Emulicious has a top-level frame with a menu and a child canvas. The child
    scales the 256x192 output to its current size; e.g. a 300x275 XCanvasPeer
    renders a 300x225 image centered vertically at y=25 (scale 1.171875).
    Sampling the parent at a fixed y=25 and rounding scale to a preset reads a
    black strip and can report a frozen ROM. Capture the child and derive its
    centered letterbox transform from the actual screenshot dimensions.
    """
    if w <= 0 or h <= 0:
        return 0.0, 0, 0
    scale = min(w / 256.0, h / 192.0)
    cw = int(round(256 * scale))
    ch = int(round(192 * scale))
    return scale, max(0, (w - cw) // 2), max(0, (h - ch) // 2)


def count_transitions(signatures):
    """Quantas vezes a assinatura mudou em relacao a anterior. PURA."""
    return sum(1 for a, b in zip(signatures, signatures[1:]) if a != b)


def debounce(samples, min_run=MIN_RUN):
    """Descarta estados que duram menos que `min_run` amostras. PURA.

    `import` fotografa a janela enquanto o emulador repinta, entao de vez em
    quando o digito sai RASGADO: metade do glifo velho, metade do novo. Esse
    estado intermediario existe por 1 amostra e transforma uma troca real em
    duas, inflando o fps (media de 1.52s entre trocas onde o real e 2.13s ->
    "84 fps" numa ROM travada em SMS_waitForVBlank a 60Hz).

    Com sobreamostragem de ~24x um estado legitimo aparece em dezenas de
    amostras seguidas; um de 1 amostra e rasgo. Descartar so pode ATRASAR o
    reconhecimento de uma troca em uma amostra (~0.09s), nunca inventar uma.
    """
    out, i, n = [], 0, len(samples)
    while i < n:
        j = i
        while j < n and samples[j][1] == samples[i][1]:
            j += 1
        if (j - i) >= min_run:
            out.extend(samples[i:j])
        i = j
    return out


def transition_times(samples):
    """Instantes em que a assinatura mudou. samples = [(t, sig), ...]. PURA."""
    return [t for (_, a), (t, b) in zip(samples, samples[1:]) if a != b]


def state_durations(samples):
    """Duracao de cada estado COMPLETO do digito, em segundos. PURA.

    Um estado = intervalo em que a assinatura nao muda. Mede-se de inicio a
    inicio (nao de primeira a ultima amostra, que subestima em um intervalo de
    amostragem). O primeiro e o ultimo estado sao cortados pela janela de
    observacao e por isso NAO entram.
    """
    inicios = [samples[0][0]]
    for (_, a), (t, b) in zip(samples, samples[1:]):
        if a != b:
            inicios.append(t)
    if len(inicios) < 3:
        return []
    return [b - a for a, b in zip(inicios, inicios[1:])][1:]


def _median(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def fps_from_transition_times(times, period_frames):
    """fps pelo INTERVALO entre a 1a e a ultima troca. PURA.

    Contar trocas e dividir pela janela total quantiza nas bordas: a janela
    comeca e termina no meio de um periodo, entao o resultado erra ate +-1
    troca (+-8 fps com periodo 128 numa janela de 16s) — foi o que produziu um
    "63 fps" numa ROM que roda a 60. Entre a primeira e a ultima troca, ao
    contrario, decorreram EXATAMENTE (n-1)*period frames. Sem borda, sem erro
    de arredondamento; sobra so a latencia de amostragem.
    """
    if len(times) < 2:
        return None
    span = times[-1] - times[0]
    if span <= 0:
        return None
    return round((len(times) - 1) * period_frames / span, 1)


def fps_from_transitions(transitions, period_frames, seconds):
    """fps = transicoes * frames_por_troca / segundos. PURA."""
    if seconds <= 0:
        return None
    return round(transitions * period_frames / seconds, 1)


def oversample_ok(interval_s, period_frames, fps_expected=60.0):
    """Amostragem respeita Nyquist com folga? PURA.

    `interval_s` tem de ser o intervalo MEDIDO, nao o pedido: cada captura leva
    ~1.5s (ativar janela + assentar), entao um --interval de 0.3s vira 1.5s na
    pratica. Checar o parametro em vez do realizado declarava folga de 7.1x
    onde a real era 1.4x.
    """
    if interval_s <= 0:
        return False, None
    troca_s = period_frames / fps_expected
    return (troca_s / interval_s) >= MIN_OVERSAMPLE, round(troca_s / interval_s, 1)


def verdict(samples, period_frames):
    """samples = [(t, assinatura), ...] em ordem cronologica.

    Usa a MEDIANA da duracao dos estados, nao a contagem de transicoes. Contar
    e dividir faz UM rasgo que sobreviva ao debounce contaminar todo o
    resultado (mediu-se 72 fps numa ROM travada em SMS_waitForVBlank a 60Hz).
    A mediana ignora outliers, e a dispersao em volta dela e exatamente o que o
    eixo se chama: fps CONSTANTE, nao fps medio.
    """
    brutas = len(samples)
    samples = debounce(samples)
    base = {"amostras": brutas, "amostras_estaveis": len(samples),
            "periodo_frames": period_frames, "fps_estimado": None,
            "sobreamostragem": None, "sobreamostragem_ok": False,
            "loop_da_rom_avancou": False, "aprovado": False}
    if len(samples) < 2:
        return {**base, "transicoes": 0, "estados_completos": 0}
    trans = count_transitions([x[1] for x in samples])
    span = samples[-1][0] - samples[0][0]
    interval = span / (len(samples) - 1)
    ok_ns, ratio = oversample_ok(interval, period_frames)
    dur = state_durations(samples)
    base.update({"transicoes": trans, "janela_s": round(span, 2),
                 "intervalo_medido_s": round(interval, 3),
                 "sobreamostragem": ratio, "sobreamostragem_ok": ok_ns,
                 "loop_da_rom_avancou": trans > 0,
                 "estados_completos": len(dur)})
    if len(dur) < MIN_STATES:
        base["motivo"] = (f"{len(dur)} estado(s) completo(s); "
                          f"{MIN_STATES} e o minimo para medir")
        return base
    # Passo 1: mediana bruta. Passo 2: um rasgo PARTE um estado em dois pedacos
    # curtos, e os pedacos puxam a mediana para baixo; descarta-se o que for
    # curto demais para ser um periodo e remediana-se. Estimar o periodo e
    # classificar artefato com o MESMO limiar seria circular — foi o erro da
    # primeira versao, que tolerava +-50% e depois media o desvio dentro
    # daquela mesma faixa.
    med0 = _median(dur)
    if med0 <= 0:
        return base
    inteiros = [d for d in dur if d >= 0.6 * med0] or dur
    med = _median(inteiros)
    if med <= 0:
        return base
    artefatos = [d for d in dur if abs(d - med) / med > TOLERANCIA]
    limite = max(1, len(dur) // 3)
    fps = round(period_frames / med, 1)
    base.update({
        "duracao_mediana_s": round(med, 3),
        "estados_fora_da_tolerancia": len(artefatos),
        "limite_de_artefatos": limite,
        "constante": len(artefatos) <= limite,
        "fps_estimado": fps,
        "aprovado": bool(trans > 0 and ok_ns and len(artefatos) <= limite
                         and FPS_MIN <= fps <= FPS_MAX),
    })
    return base


def self_check():
    # A fixture usa EXATAMENTE o formato de png_io.read_png_rgb (linhas de
    # tuplas rgb). Um self-check com bytes planos passava enquanto a ferramenta
    # estourava IndexError no PNG real — self-check calibrado no formato errado
    # nao e prova de nada (§20).
    w, h = 40, 24
    rows = [[(0, 0, 0)] * w for _ in range(h)]
    rows[9][8] = (255, 0, 0)                   # pixel em (8,9)
    a = cell_signature(rows, 0, 8, 1, 0)       # tile col=1,row=0 a partir de y0=8
    rows[9][8] = (0, 0, 0)
    b = cell_signature(rows, 0, 8, 1, 0)
    assert a != b, "assinatura tem de mudar quando o pixel do bloco muda"
    # bloco VIZINHO nao pode ser afetado -> nao esta lendo a area errada
    rows[9][8] = (255, 0, 0)
    c1 = cell_signature(rows, 0, 8, 2, 0)
    rows[9][8] = (0, 0, 0)
    assert c1 == cell_signature(rows, 0, 8, 2, 0), "bloco vizinho vazou"

    # A janela importada no host pode ser 384x313 com canvas 1,5x. A versão
    # antiga lia a coluna 19 quando solicitada a coluna 29 e perdia o marcador.
    scale, x0, y0 = 1.5, 0, 25
    tile_size = int(round(TILE * scale))

    def scaled_fixture(marker):
        fixture = [[(0, 0, 0)] * 384 for _ in range(48)]
        left = x0 + int(round(29 * TILE * scale))
        for dy in range(tile_size):
            for dx in range(tile_size):
                sx, sy = int(dx / scale), int(dy / scale)
                if marker and sx in (3, 4) and sy in (3, 4):
                    fixture[y0 + dy][left + dx] = (255, 255, 255)
        return fixture

    scaled_off, scaled_on = scaled_fixture(False), scaled_fixture(True)
    off_sig = cell_signature(scaled_off, x0, y0, 29, 0, scale)
    on_sig = cell_signature(scaled_on, x0, y0, 29, 0, scale)
    assert off_sig is not None and on_sig is not None and off_sig != on_sig, \
        "a escala 1,5 precisa detectar a troca no tile 29"
    assert cell_signature(scaled_off, x0, y0, 29, 0) == \
           cell_signature(scaled_on, x0, y0, 29, 0), \
        "fixture precisa reproduzir a leitura antiga em escala 1x"
    assert cell_signature(scaled_on, x0, y0, 30, 0, scale) == \
           cell_signature(scaled_off, x0, y0, 30, 0, scale), \
        "tile vizinho não pode herdar o marcador escalado"

    # CALIBRACAO DO XCanvasPeer 300x275: canvas 300x225 centralizada. O
    # recorte antigo do frame 300x300 usava (22,25,1.0), que lia a faixa preta
    # acima do jogo e declarava congelamento mesmo com o frame marker ativo.
    peer_w, peer_h = 300, 275
    peer_scale, peer_x0, peer_y0 = canvas_viewport(peer_w, peer_h)
    assert abs(peer_scale - (300 / 256)) < 0.0001 and \
           (peer_x0, peer_y0) == (0, 25), \
        (peer_scale, peer_x0, peer_y0)

    def peer_fixture(marker):
        fixture = [[(0, 0, 0)] * peer_w for _ in range(peer_h)]
        tile_px = int(round(TILE * peer_scale))
        left = peer_x0 + int(round(29 * TILE * peer_scale))
        for dy in range(tile_px):
            for dx in range(tile_px):
                sx, sy = int(dx / peer_scale), int(dy / peer_scale)
                if marker and (sx, sy) in ((2, 2), (3, 2), (2, 4)):
                    fixture[peer_y0 + dy][left + dx] = (255, 255, 255)
        return fixture

    peer_off, peer_on = peer_fixture(False), peer_fixture(True)
    peer_off_sig = cell_signature(peer_off, peer_x0, peer_y0, 29, 0,
                                  peer_scale)
    peer_on_sig = cell_signature(peer_on, peer_x0, peer_y0, 29, 0,
                                 peer_scale)
    assert peer_off_sig != peer_on_sig, \
        "viewport XCanvasPeer precisa detectar o marcador no tile 29"
    assert cell_signature(peer_off, 22, 25, 29, 0, 1.0) == \
           cell_signature(peer_on, 22, 25, 29, 0, 1.0), \
        "fixture precisa reproduzir a faixa preta lida pelo recorte antigo"

    # INVARIANCIA AO FLASH DE BACKDROP: mesmo desenho sobre fundo de outra cor
    # tem de dar a MESMA assinatura, senao o piscar do fundo vira "avanco".
    def glyph(bg, fg):
        g = [[bg] * w for _ in range(h)]
        for (dx, dy) in ((1, 1), (2, 1), (1, 3)):
            g[8 + dy][8 + dx] = fg
        return g
    s_azul = cell_signature(glyph((0, 0, 40), (255, 255, 255)), 0, 8, 1, 0)
    s_verde = cell_signature(glyph((0, 60, 0), (255, 255, 255)), 0, 8, 1, 0)
    assert s_azul == s_verde, "troca de cor de fundo nao pode contar como troca"
    outro = [[(0, 0, 40)] * w for _ in range(h)]
    outro[8 + 5][8 + 5] = (255, 255, 255)
    assert cell_signature(outro, 0, 8, 1, 0) != s_azul, "glifo diferente tem de diferir"

    # CELULA CONTAMINADA (sprite por cima): amostra descartada, nao "avanco"
    sujo = [[(0, 0, 40)] * w for _ in range(h)]
    for k in range(6):
        sujo[8 + k][8 + k] = (10 * k, 200 - 9 * k, 30 + 7 * k)
    assert cell_signature(sujo, 0, 8, 1, 0) is None, \
        "celula com muitos tons tem de ser descartada, nao assinada"

    assert count_transitions(["a", "a", "b", "b", "c"]) == 2
    assert count_transitions(["a"]) == 0
    assert count_transitions([]) == 0

    def series(n_amostras, dt, period_s, t0=0.0):
        """Serie sintetica: assinatura troca a cada `period_s` segundos."""
        out = []
        for i in range(n_amostras):
            t = t0 + i * dt
            out.append((t, f"sig{int(t / period_s)}"))
        return out

    # 60 fps com digito de 128 frames -> troca a cada 2.1333s
    v = verdict(series(300, 0.09, 128 / 60.0), 128)
    assert v["aprovado"] and 59 <= v["fps_estimado"] <= 61, f"caso bom reprovou: {v}"
    assert v["constante"], f"ritmo regular tem de ser constante: {v}"

    # REPROVA: ROM congelada. O titulo diria 60fps; aqui nao ha troca nenhuma.
    v = verdict([(i * 0.09, "parado") for i in range(300)], 128)
    assert not v["aprovado"] and not v["loop_da_rom_avancou"], \
        "ROM sem avanco nao pode passar — e exatamente o caso que a L013 pega"

    # REPROVA: 30 fps (troca a cada 4.2667s)
    v = verdict(series(600, 0.09, 128 / 30.0), 128)
    assert v["loop_da_rom_avancou"] and 29 <= v["fps_estimado"] <= 31
    assert not v["aprovado"], f"30fps nao pode fechar o eixo: {v}"

    # REPROVA: amostragem sem folga de Nyquist (intervalo MEDIDO de 1.5s contra
    # troca de 2.13s = 1.4x). Era o caso real que se declarava 7.1x por olhar o
    # parametro pedido (0.3s) em vez do realizado.
    v = verdict(series(30, 1.5, 128 / 60.0), 128)
    assert not v["sobreamostragem_ok"] and not v["aprovado"], \
        f"folga de {v['sobreamostragem']}x nao pode fechar o eixo: {v}"

    # ANTI-RASGO: um estado intruso de 1 amostra nao pode virar 2 trocas
    limpo = series(300, 0.09, 128 / 60.0)
    sujo = list(limpo)
    sujo[40] = (sujo[40][0], "RASGO")
    sujo[150] = (sujo[150][0], "RASGO2")
    assert count_transitions([x[1] for x in sujo]) > \
           count_transitions([x[1] for x in limpo]), "fixture nao injetou rasgo"
    v = verdict(sujo, 128)
    assert 59 <= v["fps_estimado"] <= 61, f"rasgo contaminou o fps: {v}"

    # RASGO PERSISTENTE (2 amostras, sobrevive ao debounce): a mediana tem de
    # aguentar. Era este caso que fazia contar-e-dividir reportar 72 fps.
    sujo2 = list(limpo)
    for k in (60, 61, 200, 201):
        sujo2[k] = (sujo2[k][0], f"RASGO{k // 100}")
    v = verdict(sujo2, 128)
    assert 59 <= v["fps_estimado"] <= 61, f"mediana nao aguentou o rasgo: {v}"
    assert v["estados_fora_da_tolerancia"] >= 2, \
        f"os pedacos curtos tinham de ser marcados como artefato: {v}"
    bruto = fps_from_transitions(v["transicoes"], 128, v["janela_s"])
    assert abs(bruto - 60) > abs(v["fps_estimado"] - 60), \
        f"contar-e-dividir ({bruto}) deveria errar mais que a mediana ({v['fps_estimado']})"

    # REPROVA: ritmo IRREGULAR (fps medio na faixa, mas engasgando)
    irregular, t, flip = [], 0.0, 0
    for i in range(400):
        irregular.append((t, f"s{flip}"))
        t += 0.09
        if t > (1.2 if flip % 2 else 3.0):
            pass
    # serie explicita: estados alternando 1.2s e 3.0s (media ~2.1s = 60fps)
    irregular, t, k = [], 0.0, 0
    for k in range(14):
        dur = 1.2 if k % 2 else 3.0
        n = int(dur / 0.09)
        for j in range(n):
            irregular.append((t + j * 0.09, f"e{k}"))
        t += n * 0.09
    v = verdict(irregular, 128)
    assert not v["constante"] and not v["aprovado"], \
        f"ritmo irregular nao pode fechar um eixo chamado fps_CONSTANTE: {v}"

    ok, _ = oversample_ok(0.2, 128)
    assert ok, "0.2s contra troca de 2.1s tem de passar"

    with tempfile.TemporaryDirectory(prefix="frame_advance_xauth_") as root:
        auth = os.path.join(root, "Xauthority")
        open(auth, "w").close()
        env = private_display_env(root, {"display": ":947", "host_display": ":0"})
        assert env["DISPLAY"] == ":947" and env["XAUTHORITY"] == auth
        assert "WAYLAND_DISPLAY" not in env
        try:
            private_display_env(root, {"display": ":0", "host_display": ":0"})
        except ValueError:
            pass
        else:
            raise AssertionError("host display accepted for isolated measurement")

    print("[SELF-CHECK OK] measure_frame_advance (reprova ROM congelada que o "
          "titulo diria 60fps, reprova amostragem sem folga de Nyquist e "
          "reprova 30fps, amostragem sem folga e ritmo irregular; fps pela mediana "
          "das duracoes de estado, imune a rasgo de captura)")
    return 0


def run(rom, cell, period, seconds, interval, settle, out):
    jar = CE.resolve_jar()
    if not jar or not os.path.exists(jar):
        print("[FAIL_AMBIENTE] Emulicious.jar nao encontrado", file=sys.stderr)
        return 2
    if not shutil.which("xdotool") or not shutil.which("import"):
        print("[FAIL_AMBIENTE] xdotool/import ausentes", file=sys.stderr)
        return 2
    # L057: a busca de janela e por NOME. Com outra instancia viva, o marcador
    # medido pode ser o de outra ROM — e o resultado sai como taxa DESTA.
    if not require_no_stale(why="medicao de avanco de frame"):
        return 2
    col, row = cell
    tmp = tempfile.mkdtemp(prefix="frame_advance_")
    # O modo sem remote-debug permite que o Emulicious entre em turbo quando
    # a janela não está sendo acompanhada. Nesse estado o título mostra
    # centenas de fps e o marcador muda mais rápido que a captura; isso mede
    # o host, não o contrato VBlank do SMS. O mesmo lançamento usado pelo gate
    # de evidência fixa a execução normal em 50/60 Hz.
    proc = subprocess.Popen(
        ["java", "-jar", jar, "-remotedebug", "4901", "-set", "Update=0",
         os.path.abspath(rom)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        main_wid = None
        wid = None
        for _ in range(30):
            time.sleep(1.0)
            main_wid = CE._main_window_id()
            if main_wid:
                wid = canvas_window_id(os.environ.copy())
            if main_wid and wid:
                break
        if not main_wid or not wid:
            print("[FAIL_AMBIENTE] janela do emulador nao apareceu", file=sys.stderr)
            return 2
        time.sleep(3.0)                      # deixa a ROM sair do boot
        # A captura usa a subjanela XCanvasPeer, sem menu. canvas_viewport
        # mede o encaixe/letterbox real da canvas 256x192 dentro dela.
        # Uma unica ativacao. O laco de amostragem NAO pode chamar
        # windowactivate a cada tiro: era isso que fazia o intervalo real ser
        # ~1.5s (folga de Nyquist de 1.4x) enquanto o parametro dizia 0.3s.
        # `import -window <id>` fotografa a janela pelo ID mesmo sem foco, e
        # por ser alvo-por-ID continua impossivel pegar o desktop (L007/L017).
        CE._run(["xdotool", "windowactivate", str(main_wid)])
        # O boot determinístico inclui title + warmup antes da atração. Sem
        # assentamento, os primeiros estados do marcador misturam title,
        # troca de name table e arena; a mediana então acusa um ritmo falso.
        # O tempo é explícito para que a evidência registre a condição de
        # observação, e não uma suposição escondida no código.
        time.sleep(max(0.0, settle))
        samples, descartadas = [], 0
        scale, x0, y0 = 1.0, 0, 0
        capture_size = None
        shot = os.path.join(tmp, "s.png")
        deadline = time.time() + seconds
        while time.time() < deadline:
            if os.path.exists(shot):
                os.remove(shot)
            r = CE._run(["import", "-window", str(wid), shot], timeout=20)
            t = time.time()
            if r and r.returncode == 0 and os.path.exists(shot):
                try:
                    w, h, rows = read_png_rgb(shot)
                    if w * h < CE.DESKTOP_PIXELS:
                        scale, x0, y0 = canvas_viewport(w, h)
                        capture_size = [w, h]
                        sig = cell_signature(rows, x0, y0, col, row, scale)
                        if sig is not None:
                            samples.append((t, sig))
                        else:
                            descartadas += 1
                except (PngError, OSError, IndexError):
                    pass
            if interval > 0:
                time.sleep(interval)
        if len(samples) < 2:
            print("[FAIL_AMBIENTE] captura nao produziu amostras suficientes",
                  file=sys.stderr)
            return 2
        v = verdict(samples, period)
        v.update({"rom": os.path.abspath(rom), "celula": [col, row],
                  "amostras_descartadas": descartadas,
                  "assentamento_s": settle, "escala_canvas": scale,
                  "origem_canvas": [x0, y0], "janela_capturada_px": capture_size})
        print(json.dumps(v, indent=2, ensure_ascii=False))
        if out:
            json.dump(v, open(out, "w"), indent=2, ensure_ascii=False)
        if not v["aprovado"]:
            print("[FAIL] avanco do loop da ROM nao provado", file=sys.stderr)
            return 1
        print(f"[OK] loop da ROM avancou: {v['transicoes']} trocas do digito, "
              f"fps={v['fps_estimado']}")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(tmp, ignore_errors=True)


def private_display_env(root, meta):
    """Pin X11 capture to this isolated session; never inherit host display."""
    display = meta.get("display")
    if not display or display == meta.get("host_display"):
        raise ValueError("private session display missing or equals host display")
    auth = os.path.join(str(root), "Xauthority")
    if not os.path.isfile(auth):
        raise ValueError("private Xauthority missing")
    env = os.environ.copy()
    for key in ("WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS"):
        env.pop(key, None)
    env["DISPLAY"] = display
    env["XAUTHORITY"] = auth
    return env


def private_window_id(env, expected_pid):
    """Bind one private Emulicious frame and its XCanvasPeer child to its PID."""
    found = subprocess.run(["xdotool", "search", "--onlyvisible", "--name",
                            "Emulicious"], capture_output=True, text=True,
                           env=env, timeout=10)
    if found.returncode != 0:
        return None, None
    windows = list(dict.fromkeys(x.strip() for x in found.stdout.splitlines()
                                 if x.strip().isdigit()))
    if len(windows) != 1:
        raise RuntimeError("private display must contain exactly one visible Emulicious window")
    main_wid = windows[0]
    owner = subprocess.run(["xdotool", "getwindowpid", main_wid],
                           capture_output=True, text=True, env=env, timeout=10)
    window_pid = None
    if owner.returncode == 0 and owner.stdout.strip().isdigit():
        window_pid = int(owner.stdout.strip())
        if window_pid != int(expected_pid):
            raise RuntimeError("private window PID differs from session emulator PID")
    canvas_wid = canvas_window_id(env)
    if not canvas_wid:
        return None, window_pid or int(expected_pid), main_wid
    canvas_owner = subprocess.run(["xdotool", "getwindowpid", canvas_wid],
                                  capture_output=True, text=True, env=env,
                                  timeout=10)
    if canvas_owner.returncode == 0 and canvas_owner.stdout.strip().isdigit():
        if int(canvas_owner.stdout.strip()) != int(expected_pid):
            raise RuntimeError("XCanvasPeer PID differs from session emulator PID")
    return canvas_wid, window_pid or int(expected_pid), main_wid


def canvas_window_id(env):
    """Return the sole visible XCanvasPeer large enough to contain an SMS canvas."""
    found = subprocess.run(["xdotool", "search", "--onlyvisible", "--name",
                            "XCanvasPeer"], capture_output=True, text=True,
                           env=env, timeout=10)
    if found.returncode != 0:
        return None
    candidates = []
    for wid in dict.fromkeys(x.strip() for x in found.stdout.splitlines()
                             if x.strip().isdigit()):
        geometry = subprocess.run(["xdotool", "getwindowgeometry", "--shell", wid],
                                  capture_output=True, text=True, env=env,
                                  timeout=10)
        if geometry.returncode != 0:
            continue
        values = dict(line.split("=", 1) for line in geometry.stdout.splitlines()
                      if "=" in line)
        if (int(values.get("WIDTH", "0")) >= CE.SMS_W and
                int(values.get("HEIGHT", "0")) >= CE.SMS_H):
            candidates.append(wid)
    if len(candidates) > 1:
        raise RuntimeError("display has multiple visible XCanvasPeer windows")
    return candidates[0] if candidates else None


def run_private(session, rom, cell, period, seconds, interval, settle, out):
    """Measure the in-ROM marker from this session's private Xvfb display.

    Captures target the session window directly. The emulator continues in
    real time; the sampling window contains no DAP reads or emulator pauses.
    """
    from session_bridge import isolated as iso
    if not shutil.which("xdotool") or not shutil.which("import"):
        print("[FAIL_AMBIENTE] xdotool/import ausentes", file=sys.stderr)
        return 2
    if not (0 < seconds <= 180):
        print("[FAIL_USO] --seconds deve estar entre 1 e 180", file=sys.stderr)
        return 3
    try:
        root, meta = iso.load(session)
        rom = os.path.abspath(rom)
        rom_sha = iso.sha(rom)
        if rom_sha != meta.get("rom_sha256"):
            raise ValueError("--rom SHA difere da ROM da sessão privada")
        if not iso.alive(meta.get("emulator_process", {})):
            raise ValueError("processo Emulicious da sessão não está vivo")
        env = private_display_env(root, meta)
        col, row = cell
        tmp = tempfile.mkdtemp(prefix="frame_advance_private_")
        try:
            wid, window_pid, main_wid = None, None, None
            for _ in range(30):
                wid, window_pid, main_wid = private_window_id(
                    env, meta["emulator_process"]["pid"])
                if wid:
                    break
                time.sleep(1.0)
            if not wid:
                raise RuntimeError("Emulicious window not found on private display")

            project = os.path.dirname(os.path.dirname(rom))
            prior = iso.request(root, "status")
            was_running = bool(prior.get("running"))
            with iso.performance_reservation(), iso.project_reservation(project):
                load_before = os.getloadavg()
                iso.request(root, "run")
                try:
                    time.sleep(max(0.0, settle))
                    samples, descartadas = [], 0
                    scale, x0, y0 = 1.0, 0, 0
                    capture_size = None
                    shot = os.path.join(tmp, "s.png")
                    deadline = time.time() + seconds
                    while time.time() < deadline:
                        if os.path.exists(shot):
                            os.remove(shot)
                        try:
                            result = subprocess.run(
                                ["import", "-window", str(wid), shot],
                                capture_output=True, text=True, env=env,
                                timeout=20)
                        except subprocess.TimeoutExpired:
                            result = None
                        captured_at = time.time()
                        if result and result.returncode == 0 and os.path.exists(shot):
                            try:
                                w, h, rows = read_png_rgb(shot)
                                if w * h < CE.DESKTOP_PIXELS:
                                    scale, x0, y0 = canvas_viewport(w, h)
                                    capture_size = [w, h]
                                    sig = cell_signature(rows, x0, y0, col, row, scale)
                                    if sig is not None:
                                        samples.append((captured_at, sig))
                                    else:
                                        descartadas += 1
                            except (PngError, OSError, IndexError):
                                pass
                        if interval > 0:
                            time.sleep(interval)
                    if len(samples) < 2:
                        raise RuntimeError("private capture produced fewer than two samples")
                    v = verdict(samples, period)
                    v.update({"rom": rom, "rom_sha256": rom_sha,
                              "celula": [col, row],
                              "amostras_descartadas": descartadas,
                              "assentamento_s": settle, "escala_canvas": scale,
                              "origem_canvas": [x0, y0],
                              "janela_capturada_px": capture_size,
                              "session_id": meta["session_id"],
                              "session_rom_sha256": meta["rom_sha256"],
                              "private_display": meta["display"],
                              "window_id": wid, "window_pid": window_pid,
                              "main_window_id": main_wid,
                              "host_load_before": load_before,
                              "host_load_after": os.getloadavg(),
                              "method": "continuous marker capture from PID-bound XCanvasPeer on exact private Xvfb display; no DAP reads or emulator pause during sampling"})
                    if out:
                        os.makedirs(os.path.dirname(os.path.abspath(out)),
                                    exist_ok=True)
                        with open(out, "w") as f:
                            json.dump(v, f, indent=2, ensure_ascii=False)
                    print(json.dumps(v, indent=2, ensure_ascii=False))
                    if not v["aprovado"]:
                        print("[FAIL] avanco do loop da ROM nao provado",
                              file=sys.stderr)
                        return 1
                    print(f"[OK] loop da ROM avancou: {v['transicoes']} trocas do digito, "
                          f"fps={v['fps_estimado']}")
                    return 0
                finally:
                    if not was_running:
                        try:
                            iso.request(root, "pause")
                        except Exception:
                            pass
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    except (OSError, RuntimeError, ValueError, KeyError) as e:
        print(f"[FAIL_AMBIENTE] {e}", file=sys.stderr)
        return 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom")
    ap.add_argument("--session", help="ID/path de sessão privada (§93), sem janela do host")
    ap.add_argument("--cell", default="29,0",
                    help="tile (coluna,linha) do digito do contador")
    ap.add_argument("--period", type=int, default=128,
                    help="frames entre duas trocas daquele digito")
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--interval", type=float, default=0.0,
                help="pausa extra entre tiros; 0 = tao rapido quanto o import permitir")
    ap.add_argument("--settle", type=float, default=10.0,
                    help="segundos de title/warmup antes da amostragem (default 10)")
    ap.add_argument("-o", "--out")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    if not a.rom:
        print("[ERRO] --rom obrigatorio", file=sys.stderr)
        return 2
    col, row = (int(v) for v in a.cell.split(","))
    if a.session:
        return run_private(a.session, a.rom, (col, row), a.period, a.seconds,
                           a.interval, a.settle, a.out)
    return run(a.rom, (col, row), a.period, a.seconds, a.interval, a.settle, a.out)


if __name__ == "__main__":
    sys.exit(main())
