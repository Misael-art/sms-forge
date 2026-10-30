#!/usr/bin/env python3
"""capture_video.py — grava VIDEO do framebuffer do Emulicious (L054).

Por que existe (e o que o screenshot nao resolve): o cabecalho do
capture_evidence.py registra que neste host o frame de um estado TRANSITORIO
nao e capturavel de forma confiavel. `import`/`spectacle` fotografam o
compositor — janela do jogo misturada com a interface, contaminacao de cor nas
bordas, foco oscilante — e um PNG unico nao tem eixo temporal, entao transicao
de estado e animacao ficam sem lastro.

A gravacao nativa do Emulicious sai do FRAMEBUFFER, nao do X:
  - 256x192 exatos, a canvas do VDP, sem moldura, sem menu, sem desktop;
  - por construcao nao ha risco de vazar conteudo pessoal da tela (L017);
  - tem o eixo do tempo, entao a transicao E o objeto observado.

CADEIA REAL (nada simulado), toda verificada neste host em 2026-09-07:
  1. Emulicious tem gravacao de video desde 2024-03-31 (WhatsNew.txt:93),
     encodada por FFMPEG EXTERNO (propriedade `FFMPEGPath`).
  2. Os atalhos de teclado sao propriedades do Emulicious.ini com o prefixo
     `Keys` (constante lida do bytecode de platform/Emulicious.class, que
     constroi common/PropertyBasedKeySettings com esse prefixo):
         KeysStartVideoRecording=F7
         KeysStopVideoRecording=F8
     Sem essas linhas nao ha atalho nenhum: a acao existe so no menu.
  3. O arquivo entregue e `<nome-da-rom>.mp4` no diretorio recordings/;
     `temp.raw`/`temp.wav`/`temp.mp4` sao intermediarios da gravacao em curso.

TRES ARMADILHAS, TODAS DE FALHA MUDA (cada uma virou gate, nao comentario):
  a. Instancia ZUMBI do Emulicious rouba o foco E reescreve o Emulicious.ini
     com o estado dela ao morrer, apagando os atalhos recem-escritos. O
     atalho entao vai para a janela errada e recordings/ fica vazio, sem erro.
     -> o gate ABORTA se ja houver Emulicious rodando (mesmo motivo do L017).
  b. F10 parecia funcionar como 'parar' e nao funciona: no Swing/AWT F10 e o
     atalho nativo da barra de menus. A gravacao seguia aberta e so era
     finalizada quando o processo morria — produzindo um .mp4 valido que
     PARECIA prova de que o atalho pegou. Ver KEY_STOP.
  c. Mover o mp4 assim que o tamanho para de crescer corrompe o arquivo: o
     FFMPEG ainda precisa reabri-lo para escrever o atom moov. Ver
     _wait_encoded.

LIMITE HONESTO (§28): o video prova que a ROM desta build renderizou e que a
imagem MUDOU ao longo do tempo. NAO prova que a mecanica esta correta, nem que
a mudanca e a pretendida — isso continua exigindo olho humano ou um medidor
especifico. O bundle registra `has_audio` lido do arquivo; quando a trilha nao
e muxada, o gate diz isso em vez de deixar supor que o som foi provado.

Uso:
  capture_video.py --project <dir> --rom <rom.sms> [--seconds 8] [--out video]
                   [--press 'Right=400,Left=400'] [--frames 4] [--keep-temp]
  capture_video.py --probe-shortcut     # so confere/instala o atalho no .ini
  capture_video.py --self-check

Exit: 0 video gravado e verificado | 1 gravacao invalida | 2 ambiente ausente
      | 3 uso
"""
import sys, os, json, time, shutil, argparse, subprocess
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import emulator_input as ei
from capture_evidence import (resolve_jar, image_informative, _main_window_id,
                              _input_window_id, SMS_W, SMS_H)
from emulator_session import require_no_stale
from png_io import read_png_luma_samples, png_size, PngError

EMU_DIR = os.path.normpath(os.path.join(HERE, "..", "emuladores", "emulicious"))
INI = os.path.join(EMU_DIR, "Emulicious.ini")
REC_DIR = os.path.join(EMU_DIR, "recordings")

# F10 NAO serve para parar: no Swing/AWT F10 e o atalho nativo que ativa a
# barra de menus, entao ele abre o menu 'File' em vez de chegar a acao do
# emulador — a gravacao seguia aberta e so era finalizada quando o processo
# morria. O sintoma enganava: um .mp4 valido aparecia no fim, dando a impressao
# de que o atalho tinha funcionado. F7/F8 nao colidem com atalho de Swing nem
# com os padroes do Emulicious (F11 fullscreen, F12 screenshot).
KEY_START, KEY_STOP = "F7", "F8"
# Prefixo "Keys" lido do bytecode; sufixos sao os nomes de acao do jar.
INI_KEYS = {
    "KeysStartVideoRecording": KEY_START,
    "KeysStopVideoRecording": KEY_STOP,
}
# Menos que isso nao e um video, e um piscar: 1s a 60fps.
MIN_FRAMES = 60
MIN_DURATION_S = 1.0
# Fracao de amostras de luma que precisa mudar entre o primeiro e o ultimo
# frame para o video sustentar "algo aconteceu". Abaixo disso e tela parada.
MIN_MOTION = 0.01


def evaluate_frames(checks):
    """Veredito sobre os frames-chave. Puro, testavel sem emulador.

    Exigir que TODOS sejam informativos reprova gravacao boa: o primeiro frame
    e legitimamente preto — a gravacao comeca antes de o VDP desenhar, e f00
    saiu 100% preto num video cujo resto mostra a luta inteira. Descartar a
    amostra inicial esconderia esse fato; entao ela e mantida no bundle e o
    criterio e outro: o ULTIMO frame precisa ter conteudo (a ROM continuava
    renderizando no fim) e a maioria precisa ter conteudo (nao foi um lampejo
    isolado num video preto).
    """
    if not checks:
        return False, "nenhum frame extraido"
    good = [c for c in checks if c["informative"]]
    if not checks[-1]["informative"]:
        return False, ("ultimo frame sem informacao (%s) — a ROM parou de "
                       "renderizar ou a janela sumiu" % checks[-1]["detail"])
    if len(good) * 2 <= len(checks):
        return False, ("apenas %d de %d frames com conteudo — video quase todo "
                       "vazio" % (len(good), len(checks)))
    return True, "%d de %d frames com conteudo" % (len(good), len(checks))


def _run(cmd, timeout=60, env=None):
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, env=env)
    except (subprocess.TimeoutExpired, OSError):
        return None


# ---------------------------------------------------------------- .ini ------
def read_ini(path=INI):
    props = {}
    try:
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, sep, v = line.partition("=")
            if sep:
                props[k.strip()] = v.strip()
    except OSError:
        pass
    return props


def missing_shortcuts(props):
    """Atalhos que faltam ou estao com valor diferente do esperado."""
    return {k: v for k, v in INI_KEYS.items() if props.get(k) != v}


def ensure_ini(ffmpeg_path, path=INI):
    """Instala atalhos + caminho do FFMPEG. So chamar com o emulador PARADO.

    Retorna (mudou, adicionadas). Preserva as demais linhas: o .ini guarda
    ROMs recentes, geometria de janela e filtros do depurador.
    """
    props = read_ini(path)
    wanted = dict(INI_KEYS)
    wanted["FFMPEGPath"] = ffmpeg_path
    # O padrao do Emulicious e FLAC, que o container MP4 nao aceita — AAC ao
    # menos e muxavel. NAO resolveu: com aac o arquivo continuou saindo so com
    # video neste host, entao a causa esta em outro lugar (provavelmente o
    # emulador so muxa som quando a gravacao de audio esta habilitada). Fica a
    # opcao correta, sem alegar conserto: o gate le `has_audio` do ARQUIVO e
    # avisa quando nao ha trilha, em vez de deixar supor que o som foi provado.
    wanted["VideoRecordingAudioCodec"] = "aac"
    add = {k: v for k, v in wanted.items() if props.get(k) != v}
    if not add:
        return False, {}
    lines = []
    if os.path.exists(path):
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    kept = [l for l in lines
            if l.strip().partition("=")[0].strip() not in add]
    kept += ["%s=%s" % (k, v) for k, v in sorted(add.items())]
    open(path, "w", encoding="utf-8").write("\n".join(kept) + "\n")
    return True, add


# ------------------------------------------------------------- ffprobe ------
def probe_video(path):
    """(ok, info|motivo). Le do ARQUIVO — nao confia no exit code do Java."""
    r = _run(["ffprobe", "-v", "error", "-show_entries",
              "format=duration:stream=codec_type,codec_name,width,height,nb_frames",
              "-of", "json", path])
    if not r or r.returncode != 0:
        return False, "ffprobe nao leu o arquivo (encoding falhou?)"
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return False, "ffprobe devolveu saida ilegivel"
    streams = data.get("streams", [])
    vid = next((s for s in streams if s.get("codec_type") == "video"), None)
    if vid is None:
        return False, "arquivo sem trilha de video"
    try:
        duration = float(data.get("format", {}).get("duration") or 0.0)
    except (TypeError, ValueError):
        duration = 0.0
    try:
        frames = int(vid.get("nb_frames") or 0)
    except (TypeError, ValueError):
        frames = 0
    info = {
        "codec": vid.get("codec_name"),
        "width": vid.get("width"),
        "height": vid.get("height"),
        "frames": frames,
        "duration_s": round(duration, 3),
        "has_audio": any(s.get("codec_type") == "audio" for s in streams),
    }
    return True, info


def evaluate_video(info, min_frames=MIN_FRAMES, min_duration=MIN_DURATION_S):
    """Gate puro sobre o que o ffprobe leu — testavel sem emulador."""
    if info["width"] != SMS_W or info["height"] != SMS_H:
        return False, ("video %sx%s nao e a canvas do VDP (%dx%d) — isso e "
                       "captura de tela, nao framebuffer"
                       % (info["width"], info["height"], SMS_W, SMS_H))
    if info["frames"] < min_frames:
        return False, ("apenas %d frames (min %d) — gravacao nao chegou a "
                       "rodar" % (info["frames"], min_frames))
    if info["duration_s"] < min_duration:
        return False, ("duracao %.2fs (min %.1fs)"
                       % (info["duration_s"], min_duration))
    return True, ("%s %dx%d, %d frames, %.2fs"
                  % (info["codec"], info["width"], info["height"],
                     info["frames"], info["duration_s"]))


# -------------------------------------------------------------- frames ------
# ---------------------------------------------------------------- audio -----
def parse_wav(path):
    """Le o RIFF de verdade e devolve (info, motivo). Nada e assumido.

    Por que nao usar o modulo `wave`: ele acredita no cabecalho, e o cabecalho
    e justamente o que esta errado aqui. Medido no temp.wav do Emulicious: o
    chunk `data` DECLARA 1.231.916 bytes e o arquivo contem 615.958 — exatamente
    metade. O `fmt ` esta coerente (mono/44100/blockalign 2), e o payload tem a
    duracao certa do video; so o tamanho declarado mente. O FFMPEG bate em EOF
    no meio e descarta a trilha, e foi assim que o mp4 saiu mudo.

    Tambem nao se procura b'data' com .index(): esses bytes aparecem dentro do
    proprio audio. Os chunks sao percorridos.
    """
    try:
        with open(path, "rb") as f:
            head = f.read(12)
            if len(head) < 12 or head[0:4] != b"RIFF" or head[8:12] != b"WAVE":
                return None, "nao e um RIFF/WAVE"
            total = os.path.getsize(path)
            fmt, pos = None, 12
            while pos + 8 <= total:
                f.seek(pos)
                hdr = f.read(8)
                if len(hdr) < 8:
                    break
                cid = hdr[0:4]
                csz = int.from_bytes(hdr[4:8], "little")
                body = pos + 8
                if cid == b"fmt " and csz >= 16:
                    b = f.read(16)
                    fmt = {
                        "format": int.from_bytes(b[0:2], "little"),
                        "channels": int.from_bytes(b[2:4], "little"),
                        "rate": int.from_bytes(b[4:8], "little"),
                        "bits": int.from_bytes(b[14:16], "little"),
                    }
                elif cid == b"data":
                    if fmt is None:
                        return None, "chunk data antes de fmt"
                    real = max(0, total - body)
                    fmt.update({"data_offset": body, "declared": csz,
                                "actual": min(csz, real) if csz else real,
                                "truncated": csz > real})
                    if fmt["channels"] <= 0 or fmt["rate"] <= 0:
                        return None, "fmt com canais/taxa invalidos"
                    return fmt, "ok"
                pos = body + csz + (csz & 1)      # chunks tem padding par
    except OSError as e:
        return None, "wav ilegivel: %s" % e
    return None, "sem chunk data"


def wav_payload_stats(info, path, cap=1 << 22):
    """(amostras, peak) lendo so o payload REAL. Silencio nao vira prova."""
    if info["bits"] != 16:
        return None, None
    import array
    try:
        with open(path, "rb") as f:
            f.seek(info["data_offset"])
            raw = f.read(min(info["actual"], cap))
    except OSError:
        return None, None
    a = array.array("h")
    a.frombytes(raw[: len(raw) // 2 * 2])
    if not a:
        return 0, 0
    return len(a), max(abs(x) for x in a)


def attach_audio(video, wav, log=print):
    """Anexa a trilha do `wav` ao `video`. Devolve (ok, detalhe).

    Resiliencia deliberada — o formato vem do ARQUIVO, nunca de constante:
      * taxa, canais e bits saem do `fmt `; mono/estereo e 44,1k/22k dao no mesmo;
      * se o cabecalho declara mais do que existe, usa-se o que existe;
      * PCM 16 bits vai como raw (contorna o tamanho mentiroso); qualquer outro
        formato e entregue ao FFMPEG como .wav mesmo, que sabe mais que nos;
      * payload vazio ou mudo NAO e anexado — trilha silenciosa deixaria alguem
        alegar som (L048);
      * o video so e substituido se o resultado tiver AUDIO e mantiver a
        contagem de frames. Falhou, o video original fica intacto e o gate
        segue valendo como prova de imagem.
    """
    if not os.path.isfile(wav):
        return False, "sem temp.wav (o emulador nao gravou audio)"
    if shutil.which("ffmpeg") is None:
        return False, "ffmpeg ausente"
    info, why = parse_wav(wav)
    if info is None:
        return False, why

    before = probe_video(video)[1]
    n, peak = wav_payload_stats(info, wav)
    if info["actual"] <= 0:
        return False, "payload de audio vazio"
    if peak == 0:
        return False, ("payload mudo (peak=0) — nao anexado; trilha silenciosa "
                       "nao e prova de som (L048)")

    dst = video + ".withaudio.mp4"
    if info["bits"] == 16 and info["format"] == 1:
        # raw: ignora o tamanho declarado e usa exatamente os bytes que existem
        payload = video + ".pcm"
        try:
            with open(wav, "rb") as src, open(payload, "wb") as out:
                src.seek(info["data_offset"])
                remaining = info["actual"]
                while remaining > 0:
                    chunk = src.read(min(1 << 20, remaining))
                    if not chunk:
                        break
                    out.write(chunk)
                    remaining -= len(chunk)
        except OSError as e:
            return False, "falha ao extrair payload: %s" % e
        ain = ["-f", "s16le", "-ar", str(info["rate"]),
               "-ac", str(info["channels"]), "-i", payload]
    else:
        payload = None
        ain = ["-i", wav]

    # SEM `-shortest`: a trilha termina uns frames antes do video (o emulador
    # para de amostrar audio antes do ultimo quadro) e o -shortest cortava o
    # VIDEO para caber — 455 -> 452 frames. O guard de contagem de frames pegou
    # e recusou o remux, corretamente: prova de imagem nao se encurta para
    # acomodar som. Sem ele, `-c:v copy` devolve o video intacto e o audio
    # simplesmente acaba antes, que o MP4 aceita.
    r = _run(["ffmpeg", "-y", "-v", "error", "-i", video] + ain +
             ["-c:v", "copy", "-c:a", "aac", dst], timeout=180)
    if payload and os.path.exists(payload):
        os.remove(payload)
    if not r or r.returncode != 0 or not os.path.exists(dst):
        if os.path.exists(dst):
            os.remove(dst)
        return False, "ffmpeg nao muxou (%s)" % ((r.stderr or "").strip()[:120]
                                                 if r else "timeout")

    ok, after = probe_video(dst)
    if not ok or not after.get("has_audio"):
        os.remove(dst)
        return False, "resultado sem trilha de audio"
    if before and after["frames"] and before["frames"] and \
            after["frames"] != before["frames"]:
        os.remove(dst)
        return False, ("remux mexeu no video (%d -> %d frames) — descartado"
                       % (before["frames"], after["frames"]))
    # Da contagem de BYTES reais, nao de `n`: wav_payload_stats le so uma
    # amostra do inicio (cap), entao `n` subestimaria gravacoes longas.
    bytes_per_s = info["rate"] * info["channels"] * max(1, info["bits"]) / 8.0
    audio_s = info["actual"] / bytes_per_s if bytes_per_s else 0.0
    shutil.move(dst, video)
    return True, ("%d canal(is) @ %dHz, peak=%d, %.2fs de audio para %.2fs de "
                  "video%s" % (info["channels"], info["rate"], peak, audio_s,
                               (before or {}).get("duration_s", 0.0),
                               ", cabecalho declarava %d bytes e havia %d"
                               % (info["declared"], info["actual"])
                               if info["truncated"] else ""))


def extract_frames(video, out_dir, base, n=4, duration=None):
    """N PNGs em instantes ESPALHADOS pelo video. Sem recorte: o frame JA e a
    canvas 256x192 — nao existe moldura, menu nem desktop para recortar.

    Seek explicito em vez do filtro `thumbnail`: `thumbnail` escolhe o frame
    mais 'representativo' de cada lote, o que tende a devolver quase o mesmo
    quadro varias vezes e zerava a medida de movimento. Aqui os instantes sao
    declarados, entao 'primeiro' e 'ultimo' significam o que dizem.
    """
    if duration is None:
        ok, info = probe_video(video)
        duration = info["duration_s"] if ok else 0.0
    if duration <= 0:
        return []
    n = max(2, n)
    out = []
    for i in range(n):
        frac = 0.02 + (0.96 * i / (n - 1))
        dst = os.path.join(out_dir, "%s_f%02d.png" % (base, i))
        r = _run(["ffmpeg", "-y", "-v", "error", "-ss", "%.3f" % (duration * frac),
                  "-i", video, "-frames:v", "1", "-pix_fmt", "rgb24", dst],
                 timeout=60)
        if r and r.returncode == 0 and os.path.exists(dst):
            out.append(dst)
    return out


def frame_motion(path_a, path_b):
    """Fracao de amostras de luma que mudou entre dois frames NATIVOS."""
    try:
        if png_size(path_a) != png_size(path_b):
            return 0.0
        va = read_png_luma_samples(path_a)
        vb = read_png_luma_samples(path_b)
    except (PngError, OSError):
        return 0.0
    if not va or len(va) != len(vb):
        return 0.0
    return sum(1 for x, y in zip(va, vb) if abs(x - y) > 16) / len(va)


def image_timeline_motion(images):
    """Pixel changes across the whole timeline; not actor/action recognition."""
    from PIL import ImageChops
    first = previous = None
    maximum = adjacent = endpoint = 0.0; frames = changed = 0
    def difference(a,b):
        if a.size!=b.size: raise ValueError("timeline canvas changed")
        hist=ImageChops.difference(a,b).histogram()
        return sum(hist[17:])/float(a.width*a.height)
    for img in images:
        current=img.convert("L")
        if first is None: first=current.copy()
        else:
            delta=difference(previous,current);adjacent=max(adjacent,delta)
            if delta>0: changed+=1
        endpoint=difference(first,current);maximum=max(maximum,endpoint)
        previous=current.copy();frames+=1
    return {"decoded_frames":frames,"max_from_initial_fraction":maximum,
            "max_adjacent_fraction":adjacent,"endpoint_fraction":endpoint,
            "changed_transitions":changed,"motion_fraction":max(maximum,adjacent),
            "scope":"whole-frame pixel variation only; HUD changes do not prove fighter motion or AIR state"}


def timeline_motion(video):
    """Decode every native frame instead of mistaking equal endpoints for freeze."""
    from PIL import Image
    ok,info=probe_video(str(video))
    if not ok or info.get("width")!=SMS_W or info.get("height")!=SMS_H:
        raise ValueError("timeline requires native 256x192 video")
    process=subprocess.Popen(["ffmpeg","-nostdin","-v","error","-i",str(video),
                              "-map","0:v:0","-f","rawvideo","-pix_fmt","gray","-"],
                             stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    size=SMS_W*SMS_H
    def images():
        for _ in range(90000):
            payload=b""
            while len(payload)<size:
                part=process.stdout.read(size-len(payload))
                if not part:break
                payload+=part
            if not payload:return
            if len(payload)!=size:raise ValueError("incomplete decoded frame")
            yield Image.frombytes("L",(SMS_W,SMS_H),payload)
        raise ValueError("timeline exceeds 90000 frames")
    try:
        result=image_timeline_motion(images())
        if process.wait(timeout=10)!=0 or result["decoded_frames"]<2:
            raise ValueError("video decode failed or too short")
        return result
    finally:
        if process.poll() is None:process.kill();process.wait()
        process.stdout.close()


# --------------------------------------------------------------- record -----
def _tap(key, wid, iid, tries=6):
    """Atalho do emulador pelo canal provado (L039), fail-closed no foco.

    A ativacao via KWin nao pega de primeira quando a janela acabou de ser
    mapeada: `getactivewindow` ainda devolve a anterior. Isso e corrida de
    compositor, nao ausencia de canal — insistir e legitimo; desistir depois
    de N tentativas mantem o gate fechado.
    """
    backend = focused = None
    for _ in range(tries):
        done, backend, focused = ei.press_spec("%s=60" % key,
                                               x11_window=wid, x11_input=iid)
        if done:
            return True, backend, focused
        time.sleep(1.0)
    return False, backend, focused


def snapshot_mp4(rec_dir=REC_DIR):
    """{nome: mtime} dos mp4 ja existentes — o novo e o que nao estiver aqui."""
    out = {}
    try:
        for f in os.listdir(rec_dir):
            if f.endswith(".mp4"):
                out[f] = os.path.getmtime(os.path.join(rec_dir, f))
    except OSError:
        pass
    return out


def _wait_encoded(before, timeout=120, rec_dir=REC_DIR):
    """Espera o FFMPEG FECHAR o mp4 e devolve o caminho dele.

    Duas coisas que custaram uma execucao cada:

    1. O nome do arquivo NAO e `temp.mp4`. `temp.raw`/`temp.wav`/`temp.mp4` sao
       intermediarios; ao parar a gravacao pelo atalho o emulador entrega
       `<nome-da-rom>.mp4`. Procurar por temp.mp4 fazia o gate declarar 'FFMPEG
       nao entregou' com o video pronto ao lado, no mesmo diretorio.
    2. 'Tamanho estavel' e criterio errado: o FFMPEG para de escrever pacotes,
       o tamanho congela por segundos, e so entao ele REABRE o arquivo para
       deslocar os dados e gravar o atom moov (faststart). Mover nesse
       intervalo produz um .mp4 sem moov — 269 KB de nada, e o log do emulador
       diz 'Unable to re-open ... for shifting data'.

    Dai o unico criterio honesto: um mp4 NOVO (ou remexido) que o ffprobe
    consiga LER — so o moov escrito permite ler duracao e dimensao.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        now = snapshot_mp4(rec_dir)
        cands = [f for f, mt in now.items()
                 if f not in before or mt > before[f]]
        for f in sorted(cands, key=lambda f: now[f], reverse=True):
            path = os.path.join(rec_dir, f)
            if os.path.getsize(path) > 0 and probe_video(path)[0]:
                return path
        time.sleep(1.0)
    return None


def capture(project, rom, seconds=8, out_name="video", press=None, frames=4,
            settle_frames=300, keep_temp=False):
    jar = resolve_jar()
    if not jar:
        print("[FAIL_AMBIENTE] Emulicious.jar nao encontrado. Instale em "
              "tools/emuladores/emulicious/ ou registre 'emulicious_jar' em "
              "tools/emuladores/emulators.json. Gate NAO simula evidencia.")
        return 2
    ffmpeg = shutil.which("ffmpeg")
    missing = [t for t in ("java", "ffprobe") if not shutil.which(t)]
    if ffmpeg is None:
        missing.append("ffmpeg")
    if missing:
        print("[FAIL_AMBIENTE] ferramentas ausentes: %s (o Emulicious encoda "
              "por FFMPEG externo)" % ", ".join(missing))
        return 2
    if ei.select_backend() is None:
        print("[FAIL_AMBIENTE] sem canal de teclado (kdotool+ydotool ou "
              "xdotool) — o atalho de gravacao nao teria como ser enviado.")
        return 2
    if not os.path.isfile(rom):
        print("[FAIL] ROM inexistente: %s" % rom)
        return 1

    # Instancia zumbi: rouba o foco E reescreve o .ini ao morrer, apagando o
    # atalho. Falha muda -> gate fecha antes (L017/L057).
    if not require_no_stale(why="gravacao de video"):
        return 2

    changed, added = ensure_ini(ffmpeg)
    if changed:
        print("[INFO] Emulicious.ini atualizado: %s"
              % ", ".join(sorted(added)))

    out_dir = os.path.join(project, "out", "evidence")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(REC_DIR, exist_ok=True)
    # Intermediarios de uma gravacao interrompida confundem a deteccao de
    # "comecou a gravar". O mp4 FINAL de terceiros nao e tocado: a lista de
    # antes e o que separa o arquivo desta execucao dos que ja estavam la.
    for f in os.listdir(REC_DIR):
        if f.startswith("temp."):
            os.remove(os.path.join(REC_DIR, f))
    mp4_before = snapshot_mp4()

    video_out = os.path.join(out_dir, "%s.mp4" % out_name)
    log_path = os.path.join(out_dir, "%s_emu.log" % out_name)
    logf = open(log_path, "w")
    audio_ok, audio_why = False, "nao tentado"
    proc = subprocess.Popen(
        ["java", "-jar", jar, "-set", "Update=0", os.path.abspath(rom)],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        wid = None
        for _ in range(40):                       # ~20s esperando a janela
            time.sleep(0.5)
            if proc.poll() is not None:
                break
            wid = _main_window_id()
            if wid:
                time.sleep(max(0.0, settle_frames / 60.0))
                break
        if proc.poll() is not None:
            print("[FAIL] emulador morreu antes de abrir a janela (log: %s)"
                  % log_path)
            return 1
        iid = _input_window_id(wid) if wid else None

        ok, backend, focused = _tap(KEY_START, wid, iid)
        if not ok:
            print("[FAIL] foco nao ficou no emulador para %s (backend=%s, "
                  "focused=%s) — o atalho iria para outra janela (L039)"
                  % (KEY_START, backend, focused))
            return 1
        # O emulador escreve temp.raw enquanto grava: se nada aparecer, o
        # atalho nao chegou e nao adianta esperar o resto.
        for _ in range(20):
            time.sleep(0.25)
            if any(f.startswith("temp.") for f in os.listdir(REC_DIR)):
                break
        else:
            props = read_ini()
            falta = missing_shortcuts(props)
            print("[FAIL] gravacao nao comecou: nada apareceu em %s apos %s. "
                  "%s" % (REC_DIR, KEY_START,
                          ("Atalho ausente no .ini: %s" % ", ".join(sorted(falta)))
                          if falta else "Atalho presente no .ini — o evento de "
                          "tecla nao chegou a janela certa."))
            return 1

        pressed = []
        if press:
            pressed = [k for k, _ in ei.press_spec(
                press, x11_window=wid, x11_input=iid)[0]]
        remaining = seconds - (0.5 * len(pressed))
        if remaining > 0:
            time.sleep(remaining)

        ok, backend, focused = _tap(KEY_STOP, wid, iid)
        if not ok:
            print("[FAIL] foco perdido antes de %s — gravacao ficou aberta e "
                  "o arquivo nao sera encodado" % KEY_STOP)
            return 1
        produced = _wait_encoded(mp4_before)
        if produced is None:
            print("[FAIL] FFMPEG nao entregou nenhum mp4 novo em %s (encoding "
                  "falhou ou travou). O Emulicious sinaliza isso na propria "
                  "titlebar; veja %s" % (REC_DIR, log_path))
            return 1
        shutil.move(produced, video_out)
        # O Emulicious grava o audio em temp.wav mas nao o muxa (cabecalho com
        # tamanho dobrado, L056). Anexar aqui, ANTES da limpeza do finally, e o
        # unico momento em que o payload ainda existe.
        audio_ok, audio_why = attach_audio(video_out,
                                           os.path.join(REC_DIR, "temp.wav"))
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()
        logf.close()
        if not keep_temp:
            for f in os.listdir(REC_DIR):
                if f.startswith("temp."):
                    os.remove(os.path.join(REC_DIR, f))

    ok, info = probe_video(video_out)
    if not ok:
        print("[FAIL] %s" % info)
        return 1
    ok, why = evaluate_video(info)
    if not ok:
        print("[FAIL] %s" % why)
        return 1

    shots = extract_frames(video_out, out_dir, out_name, n=frames,
                           duration=info["duration_s"])
    checks = []
    for p in shots:
        good, detail = image_informative(p)
        checks.append({"frame": p, "informative": good, "detail": detail})
    motion_timeline = timeline_motion(video_out)
    motion = motion_timeline["motion_fraction"]
    frames_ok, why_frames = evaluate_frames(checks)
    # `screenshot` alimenta quem so entende o bundle v1: tem que ser um frame
    # COM conteudo, nao o preto da largada.
    still = next((c["frame"] for c in reversed(checks) if c["informative"]), None)

    bundle = {
        "schema": "emulator_evidence_v2",
        "project": os.path.basename(os.path.abspath(project)),
        "rom": rom,
        "video": video_out,
        "screenshot": still,
        "frames": checks,
        "motion_fraction": round(motion, 4),
        "motion_timeline": motion_timeline,
        "informative": frames_ok and motion >= MIN_MOTION,
        "detail": "%s | %s" % (why, why_frames),
        "has_audio": info["has_audio"],
        "audio_attached": audio_ok,
        "audio_detail": audio_why,
        "duration_s": info["duration_s"],
        "frame_count": info["frames"],
        "input_script": press,
        "keys_pressed": pressed if press else None,
        "tool": "emulicious-video+ffmpeg",
        "chain_of_custody": [
            "launch: java -jar %s -set Update=0" % os.path.basename(jar),
            "gate: nenhuma outra instancia de Emulicious viva",
            "ini: KeysStartVideoRecording=%s / KeysStopVideoRecording=%s"
            % (KEY_START, KEY_STOP),
            "record: framebuffer do emulador (256x192), encode por FFMPEG",
            "move: %s -> %s" % (os.path.basename(produced), video_out),
            "check: ffprobe (dimensao/frames/duracao) + luma dos frames",
        ],
    }
    json.dump(bundle, open(os.path.join(out_dir, "%s.json" % out_name), "w"),
              indent=2)

    if not shots:
        print("[FAIL] video gravado mas nenhum frame pode ser extraido — "
              "arquivo suspeito")
        return 1
    if not frames_ok:
        print("[FAIL] %s" % why_frames)
        return 1
    if motion < MIN_MOTION:
        print("[FAIL] pouca variacao visual: pico %.2f%% ao longo da "
              "timeline (min %.0f%%). Este video nao "
              "prova estado transitorio." % (motion * 100, MIN_MOTION * 100))
        return 1

    print("[PASS] video registrado: %s" % video_out)
    print("       %s | %s | movimento=%.1f%%" % (why, why_frames, motion * 100))
    if info["has_audio"]:
        print("       audio anexado do emulador: %s" % audio_why)
        print("       [NOTA] a trilha prova que HAVIA som, nao que e a musica "
              "certa nas notas certas (§28). Eixo de audio: capture_audio.py.")
    else:
        print("       [NOTA] sem trilha de audio: %s. Este bundle NAO prova "
              "som — use capture_audio.py." % audio_why)
    return 0


def _probe_shortcut():
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        print("[FAIL_AMBIENTE] ffmpeg ausente")
        return 2
    if not require_no_stale(why="instalacao de atalho no Emulicious.ini"):
        return 2
    changed, added = ensure_ini(ffmpeg)
    props = read_ini()
    falta = missing_shortcuts(props)
    print("ini: %s" % INI)
    for k, v in sorted(INI_KEYS.items()):
        print("  %-28s = %s" % (k, props.get(k, "<ausente>")))
    print("  %-28s = %s" % ("FFMPEGPath", props.get("FFMPEGPath", "<ausente>")))
    if changed:
        print("[INFO] instalado: %s" % ", ".join(sorted(added)))
    return 1 if falta else 0


def _self_check():
    from PIL import Image
    a=Image.new("L",(256,192),0);b=Image.new("L",(256,192),255)
    cycle=image_timeline_motion([a,b,a]);freeze=image_timeline_motion([a,a,a])
    assert cycle["motion_fraction"]==1 and cycle["endpoint_fraction"]==0
    assert freeze["motion_fraction"]==0 and freeze["changed_transitions"]==0
    # gate de dimensao: captura de janela (com moldura) tem que reprovar
    ok, why = evaluate_video({"width": 283, "height": 282, "frames": 400,
                              "duration_s": 6.0, "codec": "h264"})
    assert not ok and "framebuffer" in why, why
    ok, why = evaluate_video({"width": SMS_W, "height": SMS_H, "frames": 10,
                              "duration_s": 6.0, "codec": "h264"})
    assert not ok and "frames" in why, why
    ok, why = evaluate_video({"width": SMS_W, "height": SMS_H, "frames": 400,
                              "duration_s": 0.2, "codec": "h264"})
    assert not ok and "duracao" in why, why
    ok, why = evaluate_video({"width": SMS_W, "height": SMS_H, "frames": 446,
                              "duration_s": 7.44, "codec": "h264"})
    assert ok, why
    # caso REAL de 2026-09-07: f00 preto (gravacao comeca antes do VDP
    # desenhar) e o resto com a luta na tela — isso e video bom.
    def _c(*flags):
        return [{"informative": f, "detail": "luma", "frame": "f%d" % i}
                for i, f in enumerate(flags)]
    ok, why = evaluate_frames(_c(False, True, True, True))
    assert ok, why
    ok, why = evaluate_frames(_c(True, True, False, False))
    assert not ok and "ultimo frame" in why, why
    ok, why = evaluate_frames(_c(False, False, False, True))
    assert not ok and "quase todo vazio" in why, why
    ok, why = evaluate_frames([])
    assert not ok, why
    # --- parser de WAV: o formato sai do ARQUIVO, nunca de constante ---------
    import tempfile as _tf, struct as _st

    def _wav(channels=1, rate=44100, bits=16, payload=b"", declared=None,
             extra_chunk=False):
        data = _st.pack("<HHIIHH", 1, channels, rate,
                        rate * channels * bits // 8, channels * bits // 8, bits)
        body = b"WAVE"
        if extra_chunk:      # LIST antes do data: parser tem que caminhar
            body += b"LIST" + _st.pack("<I", 4) + b"INFO"
        body += b"fmt " + _st.pack("<I", len(data)) + data
        body += b"data" + _st.pack("<I", len(payload) if declared is None
                                   else declared) + payload
        f = _tf.NamedTemporaryFile(suffix=".wav", delete=False)
        f.write(b"RIFF" + _st.pack("<I", len(body)) + body)
        f.close()
        return f.name

    # caso real do Emulicious: data declara o DOBRO do que existe
    p = _wav(payload=b"\x11\x22" * 100, declared=400)
    try:
        i, why = parse_wav(p)
        assert i and i["truncated"] and i["actual"] == 200, (i, why)
        assert i["declared"] == 400 and i["channels"] == 1
        n, peak = wav_payload_stats(i, p)
        assert n == 100 and peak == 0x2211, (n, peak)
    finally:
        os.unlink(p)
    # estereo 22050: nada e assumido
    p = _wav(channels=2, rate=22050, payload=b"\x00\x01" * 40)
    try:
        i, _ = parse_wav(p)
        assert i["channels"] == 2 and i["rate"] == 22050 and not i["truncated"]
    finally:
        os.unlink(p)
    # chunk desconhecido antes do data (e b'data' dentro do payload)
    p = _wav(payload=b"data" * 10, extra_chunk=True)
    try:
        i, why = parse_wav(p)
        assert i and i["actual"] == 40, (i, why)
    finally:
        os.unlink(p)
    # payload mudo nao vira prova de som (L048)
    p = _wav(payload=b"\x00\x00" * 50)
    try:
        i, _ = parse_wav(p)
        assert wav_payload_stats(i, p)[1] == 0
        ok, why = attach_audio(os.devnull, p)
        assert not ok and "mudo" in why, why
    finally:
        os.unlink(p)
    # arquivos que nao sao WAV nao explodem o gate
    assert parse_wav(os.devnull)[0] is None
    assert attach_audio(os.devnull, "/nao/existe.wav")[0] is False
    # prefixo do .ini: "Keys" + nome da acao, sem separador
    assert set(INI_KEYS) == {"KeysStartVideoRecording", "KeysStopVideoRecording"}
    assert INI_KEYS["KeysStartVideoRecording"] == "F7"
    assert "F10" not in INI_KEYS.values(), "F10 abre o menu do Swing"
    assert ei.EVDEV["F7"] == 65 and ei.EVDEV["F8"] == 66
    # ensure_ini preserva as outras linhas do .ini
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False) as f:
        f.write("Recent0=/algum/rom.sms\nKeysStartVideoRecording=F1\n")
        tmp = f.name
    try:
        changed, added = ensure_ini("/usr/bin/ffmpeg", path=tmp)
        props = read_ini(tmp)
        assert changed and props["Recent0"] == "/algum/rom.sms"
        assert props["KeysStartVideoRecording"] == "F7", props
        assert props["FFMPEGPath"] == "/usr/bin/ffmpeg"
        assert not missing_shortcuts(props)
        assert ensure_ini("/usr/bin/ffmpeg", path=tmp)[0] is False, "nao idempotente"
    finally:
        os.unlink(tmp)
    print("[OK] capture_video self-check")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project")
    ap.add_argument("--rom")
    ap.add_argument("--session",help="private session: record framebuffers by VDP frame, without audio")
    ap.add_argument("--ticks",type=int,default=120,help="VDP frames for private session recording")
    ap.add_argument("--realtime",action="store_true",help="private session: native framebuffer stream during unpaused run, duration from --seconds")
    ap.add_argument("--seconds", type=float, default=8.0)
    ap.add_argument("--out", default="video")
    ap.add_argument("--press", help="roteiro de input: 'Right=400,Left=400'")
    ap.add_argument("--frames", type=int, default=4,
                    help="frames-chave extraidos do video")
    ap.add_argument("--keep-temp", action="store_true")
    ap.add_argument("--probe-shortcut", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args(argv)
    if a.self_check:
        return _self_check()
    if a.session:
        from session_bridge.isolated import video,realtime_video,load,sha
        try:
            if a.rom and sha(a.rom)!=load(a.session)[1]["rom_sha256"]:raise ValueError("ROM/session mismatch")
            if a.press:raise ValueError("--press milliseconds incompatible with private frame-paced input")
            record=(realtime_video(a.session,a.seconds,a.out) if a.realtime else
                    video(a.session,a.ticks,a.out))
            record["motion_timeline"]=timeline_motion(record["path"])
            from session_bridge.isolated import atomic
            atomic(Path(record["path"]).with_suffix('.json'),record)
            print(json.dumps(record,indent=2));return 0
        except (OSError,RuntimeError,ValueError) as e:
            print("[FAIL] "+str(e));return 2
    if a.realtime:
        ap.error("--realtime requires an isolated --session")
    if a.probe_shortcut:
        return _probe_shortcut()
    if not (a.project and a.rom):
        ap.print_usage()
        print("erro: --project e --rom sao obrigatorios")
        return 3
    return capture(a.project, a.rom, seconds=a.seconds, out_name=a.out,
                   press=a.press, frames=a.frames, keep_temp=a.keep_temp)


if __name__ == "__main__":
    sys.exit(main())
