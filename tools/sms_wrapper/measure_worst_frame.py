#!/usr/bin/env python3
"""measure_worst_frame.py — mede o worst-frame de VBlank NA ROM (L061).

Orçamento de cena "declarado" (ex.: doc/13-spec-cenas.md) não fecha eixo
nenhum até existir instrumento NA ROM. Padrão do probe SMRT (aditivo,
schema 1):
  - probe_vline (0xC7EA): VCounter lido após os uploads, CRAM, HUD e SAT do
    trecho de VBlank. VBlank começa em 0xC0 (linha 192 NTSC) e segue até
    o contador dar a volta; valor <0xC0 significa que o trabalho passou da
    janela segura e invadiu o próximo display ativo.
  - probe_vovf (0xC7EB, word): contador não saturante de frames com vline <
    0xC0. Delta de leituras = evidência dura, imune a amostragem e ao antigo
    falso teto em 255.
  - probe_phase (0xC7ED): última fase observada (1 CPU/input, 2 trabalho de
    VBlank, 3 amostra final de VDP, 4 preparação de metasprites em RAM).
Um segundo contador "missed" chegou a existir no WIP de 2026-09-15: incrementado
na MESMA condição de vovf, era redundante por construção e comeu 16 B do banco
(makesms "Bank 1 overflow"); removido do ROM e daqui. vovf é o único contador.
A ROM mede 3000 frames contínuos de MODO ATRAÇÃO (CPU x CPU: especiais,
projéteis, trocas de pose com stream, HUD e banners), depois sela vovf e o
menor vline em RAM. O DAP só conecta DEPOIS do selo: pause()/cont() durante a
janela fazia o Z80 perder tempo de frame e contaminava a própria grandeza.
3000 frames cobrem pelo menos 50 s a 60 Hz e 60 s a 50 Hz. Derrame não derruba
fps: espreme o streaming de VRAM, então "fps 60" não absolve orçamento estourado.

Pré-requisito do projeto: probe SMRT com probe_vline/probe_vovf nos
endereços acima, probe_worst_done/probe_vline_min em 0xC7EE/0xC7D2 e modo
atração que exercite o pior caminho.

Endereços são DERIVADOS de uma base de corredor (--probe-base, default
0xC700). Um projeto cujo _DATA encosta em 0xC790 realoca o bloco inteiro
(ex. 0xC900) sem mudar nenhum offset interno; o contrato de fonte e as
leituras seguem a base declarada (L089).

Uso:
  measure_worst_frame.py --project SMS_projects/MSSF2T \
      --rom SMS_projects/MSSF2T/out/rom/MSSF2T.sms [--seconds 45]

`--seconds` é a janela mínima solicitada (1–50 s); a ROM mede sempre 3000
frames. O runner deixa a emulação seguir sem DAP por 90 s por padrão; use
`--wait-seconds` (90–1800) para ROMs de diagnóstico abaixo de 50 FPS. O DAP
conecta uma vez após o prazo e lê o snapshot imutável.

Exit:
  0  pass — nenhum frame derramou no VBlank (vovf não avançou)
  1  reprova — vovf avançou (derramou), leitura sem lastro, ou ROM sem
     contrato de probe (sem_contrato: nada medido é evidência)
  2  ambiente ausente (java/emulador/DAP)
  3  uso (argumentos)
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import capture_evidence as CE                                    # noqa: E402
import measure_runtime_probe as MRP                              # noqa: E402
from emulicious_dap import PORT, magic_ok                         # noqa: E402

PROBE_BLOCK = 0xC700          # base canônica do corredor (--probe-base)
OFFSETS = {
    "header": 0xE0, "vline": 0xEA, "vovf": 0xEB, "phase": 0xED,
    "worst_done": 0xEE, "vline_min": 0xD2, "frame": 0xF0, "state": 0xF6,
    "profile_wait": 0xD0, "profile_stream": 0xD1, "profile_hud": 0xD3,
    "profile_sat": 0xD4, "profile_spill_max": 0xD6,
}
PROBE_HEADER = 0xC7E0         # magic 'SMRT' + byte de schema (L071/§56)
PROBE_VLINE = 0xC7EA
PROBE_VOVF = 0xC7EB
PROBE_PHASE = 0xC7ED
PROBE_WORST_DONE = 0xC7EE
PROBE_VLINE_MIN = 0xC7D2
PROBE_FRAME = 0xC7F0
PROBE_STATE = 0xC7F6
PROFILE_ADDRS = {
    "wait": 0xC7D0,
    "hud": 0xC7D3,
    "sat": 0xC7D4,
    "stream": 0xC7D1,
}
PROFILE_SPILL_MAX = 0xC7D6
LOOP_PROFILE_SEQ = 0xC7D2
LOOP_PROFILE_NAMES = (
    "wait", "hud", "sat", "stream", "track", "cpu_input", "step_p1",
    "step_p2", "logic_end", "draw_start", "draw_scan", "draw_schedule",
    "draw_emit", "draw_add", "render_end", "audio_end",
)
LOOP_PROFILE_FRAME_LINES = 262
PROBE_WINDOW_FRAMES = 3000
PROBE_DEFAULT_WAIT_SECONDS = int(PROBE_WINDOW_FRAMES / 50.0 + 30.0)
PROBE_MAX_WAIT_SECONDS = 1800
PROBE_MAX_SECONDS = PROBE_WINDOW_FRAMES / 60.0
VLIMIAR = 0xC0            # abaixo disso, o VDP ja voltou ao display ativo
GS = {0: "ROUND", 1: "FIGHT", 2: "KO", 3: "RESULT", 4: "TITLE"}


# ---------------------------------------------------------------- contrato
def _build_contract(block):
    """Regenera endereços e regex do contrato para uma base de corredor."""
    a = {k: block + off for k, off in OFFSETS.items()}
    decl = {
        "probe_vline em 0x%04X" % a["vline"]:
            re.compile(r"__at\(0x%04X\)" % a["vline"]),
        "probe_vovf WORD em 0x%04X" % a["vovf"]:
            re.compile(r"unsigned\s+int[^;]*__at\(0x%04X\)" % a["vovf"]),
        "probe_phase em 0x%04X" % a["phase"]:
            re.compile(r"__at\(0x%04X\)" % a["phase"]),
        "probe_worst_done em 0x%04X" % a["worst_done"]:
            re.compile(r"__at\(0x%04X\)" % a["worst_done"]),
        # 0xC7EF NÃO pode: topo da pilha do laço main (tecla stack=0xDFF0 no map;
        # calls/ISR espelham C7F0–FF na MESMA RAM) aliasa o bloco F0+ com leitura
        # plausível-falsa (medido no BlastEm: SP 0xDFFD, IX 0xDFFC). D2 é o único
        # byte do banco de sondas abaixo do fundo máximo do ISR e livre no
        # contrato (LOOP_PROFILE_SEQ só vale para ROMs com tl_snap).
        "probe_vline_min em 0x%04X" % a["vline_min"]:
            re.compile(r"__at\(0x%04X\)" % a["vline_min"]),
        "janela de 3000 frames": re.compile(
            r"#define\s+WORST_FRAME_WINDOW\s+3000u"),
    }
    prof = {name: re.compile(r"__at\(0x%04X\)\s+probe_profile_%s\b"
                             % (a["profile_" + name], name))
            for name in ("wait", "hud", "sat", "stream")}
    spill = re.compile(r"__at\(0x%04X\)\s+probe_vline_spill_max\b"
                       % a["profile_spill_max"])
    loop = (
        re.compile(r"__at\(0x[0-9A-Fa-f]{4}\)\s+tl_snap\[16\]"),
        re.compile(r"__at\(0x%04X\)\s+tl_snap_seq\b" % a["vline_min"]),
        re.compile(r"probe_frame\s*<=\s*WORST_FRAME_WINDOW"),
    )
    return a, decl, prof, spill, loop


def apply_probe_block(block):
    """Move o contrato inteiro para outra base de corredor (default 0xC700).

    A fonte da ROM precisa declarar as sondas na MESMA base: um relocated
    source não autentica sob a base canônica, e vice-versa — o contrato é
    não-vacuo por construção.
    """
    global PROBE_BLOCK, PROBE_HEADER, PROBE_VLINE, PROBE_VOVF, PROBE_PHASE
    global PROBE_WORST_DONE, PROBE_VLINE_MIN, PROBE_FRAME, PROBE_STATE
    global PROFILE_ADDRS, PROFILE_SPILL_MAX, LOOP_PROFILE_SEQ
    global DECL_RX, PROFILE_RX, PROFILE_SPILL_RX, LOOP_PROFILE_RX
    if block & 0xFF or not (0xC000 <= block <= 0xDF00):
        raise ValueError("base do corredor precisa ser uma página em "
                         "0xC000..0xDF00: %s" % hex(block))
    MRP.apply_probe_block(block)
    a, DECL_RX, PROFILE_RX, PROFILE_SPILL_RX, LOOP_PROFILE_RX = \
        _build_contract(block)
    PROBE_BLOCK = block
    PROBE_HEADER, PROBE_VLINE, PROBE_VOVF = (a["header"], a["vline"],
                                             a["vovf"])
    PROBE_PHASE, PROBE_WORST_DONE = a["phase"], a["worst_done"]
    PROBE_VLINE_MIN, PROBE_FRAME, PROBE_STATE = (a["vline_min"], a["frame"],
                                                 a["state"])
    PROFILE_ADDRS = {n: a["profile_" + n] for n in ("wait", "hud", "sat",
                                                    "stream")}
    PROFILE_SPILL_MAX = a["profile_spill_max"]
    LOOP_PROFILE_SEQ = a["vline_min"]
    return PROBE_HEADER


(PROBE_ADDR_MAP, DECL_RX, PROFILE_RX, PROFILE_SPILL_RX, LOOP_PROFILE_RX) = \
    _build_contract(PROBE_BLOCK)


PROBE_DECL_RX = re.compile(
    r"unsigned\s+(char|int)\s+__at\(0x([0-9A-Fa-f]{4})\)\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)(?:\[(\d+)\])?\s*;")


def declared_probes(path):
    """[(nome, endereco, largura)] para todo __at() do fonte — sem tabela copiada.

    Quem lê RAM do corredor precisa derivar o mapa do fonte declarado: a
    tabela hardcoded sobreviveu a três realocações de base e virou a causa
    das recidivas de L089 (fonte mudou de endereço, leitor seguiu no endereço
    velho e devolveu lixo plausível). `path` é o fonte OU um diretório
    contendo .c/.h.
    """
    files = []
    if os.path.isdir(path):
        files = [os.path.join(path, f) for f in sorted(os.listdir(path))
                 if f.endswith((".c", ".h"))]
    elif os.path.isfile(path):
        files = [path]
    out, seen = [], {}
    for f in files:
        with open(f, errors="replace") as fh:
            for m in PROBE_DECL_RX.finditer(fh.read()):
                kind, addr, name, count = (m.group(1), int(m.group(2), 16),
                                           m.group(3), m.group(4))
                width = 1 if kind == "char" else 2
                for i in range(int(count) if count else 1):
                    a = addr + i * width
                    for b in range(a, a + width):
                        if b in seen:
                            raise ValueError("sondas sobrepostas: %s@%04X e %s"
                                             % (seen[b], b, name))
                        seen[b] = name
                    out.append((name if not count else "%s[%d]" % (name, i),
                                a, width))
    return out
LOOP_PROFILE_ADDR_RX = re.compile(
    r"__at\(0x([0-9A-Fa-f]{4})\)\s+tl_snap\[16\]")
LOOP_PROFILE_NAMES_RX = re.compile(
    r"/\*\s*LOOP_PROFILE_NAMES:\s*([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*"
    r"[A-Za-z_][A-Za-z0-9_]*)*)\s*\*/")
LOOP_PROFILE_METRICS_RX = re.compile(r"/\*\s*LOOP_PROFILE_METRICS:\s*([^*]+)\*/")
LOOP_PROFILE_METRIC_RX = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*)\s*@\s*(0x[0-9A-Fa-f]{4})\s*:\s*u(8|16)")


def probe_contract(project):
    """A fonte declara o mapa e selo canônicos? (L071/§56/L082)

    O header SMRT na RAM autentica a identidade do probe, mas NÃO prova que
    a ROM instrumenta o worst-frame: arena_nocturna tem magic+schema e nenhum
    vline/vovf/phase — o 'pass' de lixo estático em 0xEA era falso verde
    (L077). vovf precisa ser WORD; done/min precisam selar uma janela
    contínua antes de qualquer pausa do DAP (L082)."""
    src = os.path.join(project, "src")
    text = ""
    if os.path.isdir(src):
        for f in sorted(os.listdir(src)):
            if f.endswith((".c", ".h")):
                with open(os.path.join(src, f), errors="replace") as fh:
                    text += fh.read()
    missing = [k for k, rx in DECL_RX.items() if not rx.search(text)]
    return (not missing), missing


def profile_contract(project):
    """Perfil opcional por checkpoints; não faz parte do contrato SMRT comum."""
    src = os.path.join(project, "src")
    text = ""
    if os.path.isdir(src):
        for f in sorted(os.listdir(src)):
            if f.endswith((".c", ".h")):
                with open(os.path.join(src, f), errors="replace") as fh:
                    text += fh.read()
    return (all(rx.search(text) for rx in PROFILE_RX.values())
            and PROFILE_SPILL_RX.search(text) is not None)


def loop_profile_contract(project):
    """A loop profile must be a complete, seqlock-protected snapshot."""
    src = os.path.join(project, "src")
    text = ""
    if os.path.isdir(src):
        for f in sorted(os.listdir(src)):
            if f.endswith((".c", ".h")):
                with open(os.path.join(src, f), errors="replace") as fh:
                    text += fh.read()
    return (all(rx.search(text) for rx in LOOP_PROFILE_RX)
            and loop_profile_address_text(text) is not None
            and text.count("tl_snap_seq++") >= 2
            and loop_profile_names(project) is not None
            and loop_profile_metrics(project) is not None)


def loop_profile_address_text(text):
    """Resolve the snapshot address from the source instead of assuming one map."""
    matches = list(LOOP_PROFILE_ADDR_RX.finditer(text))
    if len(matches) != 1:
        return None
    address = int(matches[0].group(1), 16)
    if not 0xC000 <= address <= 0xDFF0:
        return None
    return address


def loop_profile_address(project):
    """Read the declared address of tl_snap[16] from project source files."""
    src = os.path.join(project, "src")
    text = ""
    if os.path.isdir(src):
        for f in sorted(os.listdir(src)):
            if f.endswith((".c", ".h")):
                with open(os.path.join(src, f), errors="replace") as fh:
                    text += fh.read()
    return loop_profile_address_text(text)


def loop_profile_names(project):
    """Read optional source labels for the active prefix of tl_snap[16]."""
    src = os.path.join(project, "src")
    text = ""
    if os.path.isdir(src):
        for f in sorted(os.listdir(src)):
            if f.endswith((".c", ".h")):
                with open(os.path.join(src, f), errors="replace") as fh:
                    text += fh.read()
    matches = list(LOOP_PROFILE_NAMES_RX.finditer(text))
    if not matches:
        return LOOP_PROFILE_NAMES
    if len(matches) != 1:
        return None
    names = tuple(name.strip() for name in matches[0].group(1).split(","))
    if not (2 <= len(names) <= 16) or len(set(names)) != len(names):
        return None
    return names


def loop_profile_metrics(project):
    """Read optional fixed-RAM counters emitted with the loop snapshot."""
    src = os.path.join(project, "src")
    text = ""
    if os.path.isdir(src):
        for f in sorted(os.listdir(src)):
            if f.endswith((".c", ".h")):
                with open(os.path.join(src, f), errors="replace") as fh:
                    text += fh.read()
    matches = list(LOOP_PROFILE_METRICS_RX.finditer(text))
    if not matches:
        return ()
    if len(matches) != 1:
        return None
    specs = []
    used_addresses = set()
    used_names = set()
    for item in matches[0].group(1).split(","):
        match = LOOP_PROFILE_METRIC_RX.fullmatch(item.strip())
        if not match:
            return None
        name, address, bits = match.groups()
        address = int(address, 16)
        size = int(bits) // 8
        if (name in used_names or address < 0xC000 or address + size > 0xE000
                or any(address + offset in used_addresses for offset in range(size))):
            return None
        used_names.add(name)
        used_addresses.update(address + offset for offset in range(size))
        specs.append({"name": name, "address": address, "width": size})
    return tuple(specs) if specs else None


def profile_source_project(project, rom):
    """Prefer the declared source project over inferring from a ROM copy.

    Private emulator sessions run a copied ROM from a temporary session
    directory. Inferring the project from that copy loses the source tree,
    which made the measurement silently omit its optional loop profile.
    """
    explicit = os.path.abspath(project) if project else ""
    if explicit and os.path.isdir(os.path.join(explicit, "src")):
        return explicit
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(rom))))


def loop_profile_report(raw, seq, names=None, vblank_serials=None):
    """Decode the ROM's committed checkpoint snapshot, or reject it."""
    names = tuple(names or LOOP_PROFILE_NAMES)
    complete = isinstance(raw, (list, tuple)) and len(raw) == len(names) \
        and all(v is not None for v in raw)
    stable = seq is not None and (seq & 1) == 0
    wraps_known = (isinstance(vblank_serials, (list, tuple))
                   and len(vblank_serials) == len(names)
                   and all(v is not None for v in vblank_serials))
    cumulative = (profile_lines_with_vblank(raw, vblank_serials)
                  if complete and stable and wraps_known else
                  profile_lines(raw) if complete and stable else None)
    valid = cumulative is not None
    absolute = dict(zip(names, cumulative)) if valid else None
    stage_lines = ([cumulative[0]] + [cumulative[i] - cumulative[i - 1]
                                      for i in range(1, len(cumulative))]
                   if valid else None)
    return {
        "seq": seq,
        "coherent_snapshot": stable,
        "profile_valido": valid,
        "frame_wraps_known": wraps_known,
        "vblank_serials": list(vblank_serials) if wraps_known else None,
        "checkpoints": list(names),
        "raw": dict(zip(names, raw or [])),
        "linhas_desde_inicio": absolute,
        "linhas_desde_wait": absolute,  # compatibilidade do mapa padrão antigo
        "linhas_por_etapa": dict(zip(names, stage_lines)) if stage_lines else None,
    }


def state_label(project, state):
    """Use enum ST_* when the project declares one; otherwise retain GS map."""
    if state is None:
        return None
    src = os.path.join(project, "src")
    if os.path.isdir(src):
        for f in sorted(os.listdir(src)):
            if not f.endswith((".c", ".h")):
                continue
            with open(os.path.join(src, f), errors="replace") as fh:
                m = re.search(r"enum\s*\{([^}]+)\}", fh.read())
            if not m:
                continue
            names = re.findall(r"\bST_[A-Z0-9_]+\b", m.group(1))
            names = [n for n in names if n != "ST_N_STATES"]
            if names:
                return names[state][3:] if state < len(names) else str(state)
    return str(GS.get(state, state))


def profile_lines(raw):
    """Converte checkpoints VCounter em linhas desde o primeiro checkpoint.

    NTSC tem a descontinuidade documentada DA→D5 e volta FF→00. D5–DA pode
    ocorrer dos dois lados da primeira descontinuidade, então a ordem temporal
    resolve a ocorrência mais cedo compatível. O acumulador aceita várias
    voltas completas da tela; um frame caro pode passar de 262 linhas.
    """
    def candidates(v):
        if v is None:
            return []
        if v < 0xC0:
            return [70 + v]
        if v <= 0xD4:
            return [v - 0xC0]
        if v <= 0xDA:
            return [v - 0xC0, 27 + v - 0xD5]
        return [27 + v - 0xD5]

    if not raw or any(v is None for v in raw):
        return None
    first = min(candidates(raw[0]))
    elapsed = [0]
    prev = first
    for v in raw[1:]:
        choices = []
        for base in candidates(v):
            wraps = max(0, (prev - base + 261) // 262)
            choices.append(base + wraps * 262)
        if not choices:
            return None
        prev = min(choices)
        elapsed.append(prev - first)
    return elapsed


def profile_vcounter_candidates(v):
    """Map SMS VCounter readings to possible lines relative to VBlank."""
    if v is None:
        return []
    if v < 0xC0:
        return [70 + v]
    if v <= 0xD4:
        return [v - 0xC0]
    if v <= 0xDA:
        return [v - 0xC0, 27 + v - 0xD5]
    return [27 + v - 0xD5]


def profile_lines_with_vblank(raw, vblank_serials):
    """Resolve full VCounter wraps with a serial sampled at each checkpoint.

    The VCounter-only path chooses the smallest compatible elapsed interval.
    That aliases one or more complete SMS frames when a phase takes multiple
    frames. The VBlank interrupt serial adds those wraps back in.
    """
    if (not isinstance(raw, (list, tuple)) or
            not isinstance(vblank_serials, (list, tuple)) or
            not raw or len(raw) != len(vblank_serials) or
            any(v is None for v in raw) or
            any(v is None for v in vblank_serials)):
        return None
    minimum = profile_lines(raw)
    first_candidates = profile_vcounter_candidates(raw[0])
    if minimum is None or not first_candidates:
        return None
    first_line = min(first_candidates)
    elapsed = [0]
    for i in range(1, len(raw)):
        serial_delta = (int(vblank_serials[i]) -
                        int(vblank_serials[i - 1])) & 0xFF
        min_prev, min_cur = minimum[i - 1], minimum[i]
        min_crossings = ((first_line + min_cur) // LOOP_PROFILE_FRAME_LINES -
                         (first_line + min_prev) // LOOP_PROFILE_FRAME_LINES)
        if serial_delta < min_crossings:
            return None
        elapsed.append(elapsed[-1] + (min_cur - min_prev) +
                       (serial_delta - min_crossings) * LOOP_PROFILE_FRAME_LINES)
    return elapsed


# ---------------------------------------------------------------- logica pura
def analyze(samples, vovf_inicio, vovf_fim, limiar=VLIMIAR):
    """Veredito do worst-frame a partir de amostras + delta do contador.

    - vovf_delta > 0: REPROVA — frames com trabalho dentro do VBlank,
      contados pela própria ROM (imune a amostragem).
    - vovf_delta == 0 e vline_min < limiar: contradição por construção
      (vovf conta exatamente esses frames fora do blank) — leitura sem lastro.
    - leitura None não conta como amostra; sem amostra nenhuma, sem
      veredito.
    """
    vline_min = None
    validos = [s for s in samples if s.get("vline") is not None]
    for s in validos:
        if vline_min is None or s["vline"] < vline_min:
            vline_min = s["vline"]
    if vovf_inicio is None or vovf_fim is None:
        return {"verdicto": "sem_lastro", "vline_min": vline_min,
                "vovf_delta": None, "amostras": len(validos)}
    if not validos:
        return {"verdicto": "sem_lastro", "vline_min": None,
                "vovf_delta": vovf_fim - vovf_inicio, "amostras": 0}
    delta = vovf_fim - vovf_inicio
    if delta > 0:
        return {"verdicto": "derramou", "vline_min": vline_min,
                "vovf_delta": delta, "amostras": len(validos)}
    if vline_min < limiar:
        return {"verdicto": "sem_lastro", "vline_min": vline_min,
                "vovf_delta": delta, "amostras": len(validos)}
    return {"verdicto": "pass", "vline_min": vline_min,
            "vovf_delta": 0, "amostras": len(validos)}


def analyze_snapshot(vline_min, vovf_total, done, frame, seconds=45.0):
    """Julga o snapshot selado pela ROM depois de 3000 frames sem DAP."""
    if not (0 < seconds <= PROBE_MAX_SECONDS):
        return {"verdicto": "sem_lastro", "vline_min": vline_min,
                "vovf_delta": None, "amostras": 0,
                "motivo": "janela solicitada fora do limite 1..50 s"}
    if done != 1 or frame is None or frame < PROBE_WINDOW_FRAMES:
        return {"verdicto": "sem_lastro", "vline_min": vline_min,
                "vovf_delta": None, "amostras": 0,
                "motivo": "janela worst-frame incompleta ou sem selo"}
    if vline_min is None or vovf_total is None:
        return {"verdicto": "sem_lastro", "vline_min": vline_min,
                "vovf_delta": None, "amostras": 0,
                "motivo": "snapshot de worst-frame ilegivel"}
    r = analyze([{"vline": vline_min}], 0, vovf_total, VLIMIAR)
    r["frames_medidos"] = PROBE_WINDOW_FRAMES
    r["frames_rom_final"] = frame
    r["janela_s_min"] = PROBE_MAX_SECONDS
    r["janela_selada"] = bool(done)
    return r


# ---------------------------------------------------------------- ambiente
def effective_wait_seconds(requested=None):
    if requested is None:
        return PROBE_DEFAULT_WAIT_SECONDS
    if not (PROBE_DEFAULT_WAIT_SECONDS <= requested <= PROBE_MAX_WAIT_SECONDS):
        raise ValueError("--wait-seconds deve estar entre %d e %d" %
                         (PROBE_DEFAULT_WAIT_SECONDS, PROBE_MAX_WAIT_SECONDS))
    return float(requested)


def measure(rom, project, seconds=45.0, out_name="worst_frame",
            wait_seconds=None):
    if not (0 < seconds <= PROBE_MAX_SECONDS):
        print("[FAIL_USO] --seconds deve estar entre 1 e %.0f; "
              "a ROM sela 3000 frames" % PROBE_MAX_SECONDS)
        return 3, None
    try:
        wait_s = effective_wait_seconds(wait_seconds)
    except ValueError as e:
        print("[FAIL_USO] %s" % e)
        return 3, None
    okc, missing = probe_contract(project)
    if not okc:
        out_dir = os.path.join(project, "out", "evidence")
        os.makedirs(out_dir, exist_ok=True)
        res = {"verdicto": "sem_contrato", "vline_min": None,
               "vovf_delta": None, "amostras": 0, "janela_s": seconds,
               "runner_wait_s": wait_s,
               "motivo": "fonte da ROM nao declara: " + "; ".join(missing),
               "rom": os.path.abspath(rom),
               "rom_sha256": hashlib.sha256(open(rom, "rb").read()).hexdigest(),
               "estados_vistos": [], "amostras_brutas": []}
        with open(os.path.join(out_dir, out_name + ".json"), "w") as f:
            json.dump(res, f, indent=1)
        print("[worst-frame] veredito=sem_contrato — %s" % "; ".join(missing))
        print("               nada medido neste endereco e evidencia; "
              "instrumente o mapa e o selo canonicos antes de claimar budget")
        return 1, res
    jar = CE.resolve_jar()
    if not jar:
        print("[FAIL_AMBIENTE] Emulicious.jar nao encontrado (resolve_jar)")
        return 2, None
    if not shutil.which("java"):
        print("[FAIL_AMBIENTE] java ausente")
        return 2, None
    if not MRP._zombie_guard() or not MRP._port_free():
        return 2, None
    out_dir = os.path.join(project, "out", "evidence")
    os.makedirs(out_dir, exist_ok=True)
    logf = open(os.path.join(out_dir, out_name + "_emu.log"), "w")
    proc = subprocess.Popen(
        ["java", "-jar", jar, "-remotedebug", str(PORT), os.path.abspath(rom)],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        # 3000 frames levam no máximo 60 s a 50 Hz; 30 s cobrem boot/carga
        # lentos observados no host. Nenhum pause()/cont() ocorre na janela.
        print("[worst-frame] DAP desconectado por %.0f s; aguardando selo "
              "de %d frames" % (wait_s, PROBE_WINDOW_FRAMES))
        time.sleep(wait_s)
        dap = MRP._connect_live()
        if dap is None:
            print("[FAIL] canal DAP nao ficou vivo (porta %s)" % PORT)
            return 1, None
        try:
            return _session(dap, out_dir, out_name, seconds, rom, project,
                            wait_s)
        finally:
            dap.close()
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        logf.close()


def measure_private(session, project, seconds=45.0, out_name="worst_frame", wait_seconds=None):
    """Sessao privada (§93): ROM roda em tempo real SEM nenhuma leitura durante a janela; uma unica
    leitura depois do selo (done=1). Sem porta DAP, sem janela do usuario. Carga do host registrada."""
    import json as _j
    from session_bridge.isolated import load, sha, request, MemoryReader, performance_reservation, project_reservation
    root, meta = load(session)
    rom = str(root / "emulator/rom.sms")
    wait_s = effective_wait_seconds(wait_seconds)
    out_dir = os.path.join(os.path.abspath(project), "out", "evidence", "sessions", meta["session_id"], "worst_frame")
    os.makedirs(out_dir, exist_ok=True)
    reader = MemoryReader(root)
    with performance_reservation(), project_reservation(project):
        load_before = os.getloadavg()
        f0 = reader.read_word(PROBE_FRAME)
        print("[worst-frame] sessao %s: tempo real por %.0f s sem leituras" % (meta["session_id"][:8], wait_s))
        request(root, "run")
        time.sleep(wait_s)
        code, res = _session(reader, out_dir, out_name, seconds, rom, project, wait_s)
        reader.pause()
    if res is not None:
        res.update(session_id=meta["session_id"], session_rom_sha256=meta["rom_sha256"], frame_inicio_leitura=f0,
                   host_load_before=load_before, host_load_after=os.getloadavg(),
                   chain_of_custody=["sessao privada Emulicious; run em tempo real; nenhuma leitura na janela",
                                     "uma leitura apos selo done=1; FPS/host nao atribuidos sem controle"])
        with open(os.path.join(out_dir, out_name + ".json"), "w") as f:
            _j.dump(res, f, indent=1)
    return code, res


def _session(dap, out_dir, out_name, seconds, rom, project, wait_seconds):
    # _connect_live retorna pausado, mas só DEPOIS dos 3000 frames autônomos.
    # A ROM congela vovf/vline_min em done=1, logo o attach não altera a amostra.
    header = dap.read_block(PROBE_HEADER, 5)
    sha = hashlib.sha256(open(rom, "rb").read()).hexdigest()
    if not magic_ok(header):
        res = {"verdicto": "sem_contrato", "vline_min": None,
               "vovf_delta": None, "amostras": 0, "janela_s": seconds,
               "runner_wait_s": wait_seconds,
               "motivo": "probe SMRT/schema 1 ausente em 0x%04X "
                         "(lido=%s) — ROM sem instrumento válido"
                         % (PROBE_HEADER, header),
               "rom": os.path.abspath(rom), "rom_sha256": sha,
               "estados_vistos": [], "amostras_brutas": []}
        with open(os.path.join(out_dir, out_name + ".json"), "w") as f:
            json.dump(res, f, indent=1)
        print("[worst-frame] veredito=sem_contrato — header SMRT ausente")
        return 1, res

    vl = dap.read_byte(PROBE_VLINE)
    vmin = dap.read_byte(PROBE_VLINE_MIN)
    vf = dap.read_word(PROBE_VOVF)
    ph = dap.read_byte(PROBE_PHASE)
    st = dap.read_byte(PROBE_STATE)
    done = dap.read_byte(PROBE_WORST_DONE)
    frame = dap.read_word(PROBE_FRAME)
    res = analyze_snapshot(vmin, vf, done, frame, seconds)
    res["janela_s"] = seconds
    res["runner_wait_s"] = wait_seconds
    res["vovf_inicio"] = 0
    res["vovf_fim"] = vf
    res["rom"] = os.path.abspath(rom)
    res["rom_sha256"] = sha
    snapshot_state = state_label(project, st)
    res["estado_snapshot"] = snapshot_state
    res["estados_vistos"] = []  # janela selada não manteve série de estados
    res["amostras_brutas"] = [{"t": "snapshot", "vline": vl,
                               "vline_min": vmin, "vovf": vf,
                               "phase": ph,
                               "estado_snapshot": snapshot_state,
                               "frame": frame, "done": done}]
    profile_project = profile_source_project(project, rom)
    if profile_contract(profile_project) and not loop_profile_contract(profile_project):
        raw_profile = {name: dap.read_byte(addr)
                       for name, addr in PROFILE_ADDRS.items()}
        raw_profile["spill_max"] = dap.read_byte(PROFILE_SPILL_MAX)
        order = list(PROFILE_ADDRS)
        cumulative = profile_lines([raw_profile[name] for name in order])
        overflow_snapshot_valid = (vf == 0 or
                                   raw_profile["spill_max"] < VLIMIAR)
        profile_valid = (done == 1 and frame is not None and
                         frame >= PROBE_WINDOW_FRAMES and
                         raw_profile["spill_max"] is not None and
                         overflow_snapshot_valid and cumulative is not None)
        res["perfil_vcounter"] = {
            "raw": raw_profile,
            "profile_valido": profile_valid,
            "linhas_desde_wait": dict(zip(order, cumulative or [])),
            "linhas_por_etapa": (dict(zip(
                order, [cumulative[0]] + [cumulative[i] - cumulative[i - 1]
                                          for i in range(1, len(cumulative))]))
                if cumulative else None),
        }
    if loop_profile_contract(profile_project):
        names = loop_profile_names(profile_project)
        seq_before = dap.read_byte(LOOP_PROFILE_SEQ)
        raw = dap.read_block(loop_profile_address(profile_project), len(names))
        seq_after = dap.read_byte(LOOP_PROFILE_SEQ)
        seq = (seq_before if seq_before == seq_after else None)
        metrics = loop_profile_metrics(profile_project)
        metric_values = {}
        if metrics:
            for metric in metrics:
                metric_values[metric["name"]] = (
                    dap.read_byte(metric["address"])
                    if metric["width"] == 1
                    else dap.read_word(metric["address"]))
            res["perfil_loop_metricas"] = metric_values
        serial_names = tuple(name + "_vblank" for name in names)
        serials = ([metric_values[name] for name in serial_names]
                   if all(name in metric_values for name in serial_names)
                   else None)
        res["perfil_loop_vcounter"] = loop_profile_report(
            raw, seq, names, vblank_serials=serials)
    with open(os.path.join(out_dir, out_name + ".json"), "w") as f:
        json.dump(res, f, indent=1)
    print("[worst-frame] veredito=%s vovf_delta=%s vline_min=%s "
          "amostras=%d estados=%s"
          % (res["verdicto"], res["vovf_delta"], res["vline_min"],
             res["amostras"], res["estados_vistos"]))
    return (0 if res["verdicto"] == "pass" else 1), res


# ---------------------------------------------------------------- self-check
def self_check():
    ok = []

    r = analyze([{"vline": 0xFF}, {"vline": 0xD5}], 7, 7)
    ok.append(("pass sem derrame", r["verdicto"] == "pass"
               and r["vovf_delta"] == 0 and r["vline_min"] == 0xD5))
    r = analyze([{"vline": 0xD0}, {"vline": 0x72}], 7, 9)
    ok.append(("derrame reprovado pelo contador", r["verdicto"] == "derramou"
               and r["vovf_delta"] == 2))
    r = analyze([{"vline": None}], None, None)
    ok.append(("leitura perdida = sem lastro", r["verdicto"] == "sem_lastro"))
    r = analyze([], 3, 3)
    ok.append(("zero amostras = sem lastro", r["verdicto"] == "sem_lastro"))
    # vline dentro do display com contador parado é contradição.
    r = analyze([{"vline": 0x70}], 5, 5)
    ok.append(("vline baixo sem contador = sem lastro",
               r["verdicto"] == "sem_lastro"))
    r = analyze([{"vline": 0xFF}], 255, 255)
    ok.append(("contador WORD sem delta passa",
               r["verdicto"] == "pass"))
    r = analyze_snapshot(0xD5, 0, 1, PROBE_WINDOW_FRAMES + 300, 45)
    ok.append(("snapshot completo sem derrame passa",
               r["verdicto"] == "pass" and r["frames_medidos"] == 3000))
    r = analyze_snapshot(0x50, 2, 1, PROBE_WINDOW_FRAMES + 300, 45)
    ok.append(("snapshot completo com derrame reprova",
               r["verdicto"] == "derramou" and r["vovf_delta"] == 2))
    ok.append(("espera padrao preserva 90 s",
               effective_wait_seconds() == 90))
    ok.append(("espera longa aceita ROM lenta",
               effective_wait_seconds(150) == 150.0))
    try:
        effective_wait_seconds(89)
        short_wait_rejected = False
    except ValueError:
        short_wait_rejected = True
    ok.append(("espera curta nao reduz janela selada", short_wait_rejected))
    try:
        effective_wait_seconds(1801)
        long_wait_rejected = False
    except ValueError:
        long_wait_rejected = True
    ok.append(("espera tem limite superior", long_wait_rejected))
    r = analyze_snapshot(0xD5, 0, 0, PROBE_WINDOW_FRAMES + 300, 45)
    ok.append(("snapshot sem selo nao fecha janela",
               r["verdicto"] == "sem_lastro"))
    r = analyze_snapshot(0xD5, 0, 1, PROBE_WINDOW_FRAMES - 1, 45)
    ok.append(("snapshot curto nao fecha janela",
               r["verdicto"] == "sem_lastro"))
    r = analyze_snapshot(0xD5, 0, 1, PROBE_WINDOW_FRAMES + 300, 51)
    ok.append(("janela acima do probe nao e suportada",
               r["verdicto"] == "sem_lastro"))
    prof = profile_lines([0xC3, 0xD9, 0x20, 0x40])
    ok.append(("checkpoints VCounter atravessam retorno FF->00",
               prof == [0, 22, 99, 131]))
    prof = profile_lines([0xAF, 0xEE, 0x20])
    ok.append(("checkpoints VCounter aceitam mais de uma volta",
               prof == [0, 69, 119]))
    loop_prof = loop_profile_report(
        [194, 195, 211, 211, 218, 5, 52, 66, 67, 123, 175, 238, 238, 238,
         238, 241],
        2)
    ok.append(("perfil do loop aceita snapshot completo par",
               loop_prof["profile_valido"]
               and loop_prof["linhas_por_etapa"]["cpu_input"] == 49
               and loop_prof["linhas_por_etapa"]["step_p1"] == 47
               and loop_prof["linhas_por_etapa"]["step_p2"] == 14))
    loop_prof = loop_profile_report(
        [194, 195, 211, 211, 218, 5, 52, 66, 67, 123, 175, 238, 238, 238,
         238, 241],
        3)
    ok.append(("perfil do loop rejeita snapshot em escrita",
               not loop_prof["coherent_snapshot"]
               and not loop_prof["profile_valido"]))
    loop_prof = loop_profile_report([194, None], 2)
    ok.append(("perfil do loop rejeita snapshot truncado",
               not loop_prof["profile_valido"]))
    raw = [194, 244, 93, 133, 187, 191]
    serials = [10, 10, 12, 12, 12, 12]
    loop_prof = loop_profile_report(
        raw, 2,
        ("loop_start", "uploads_end", "input_cmd_end", "combat_end",
         "hud_render_end", "loop_end"),
        vblank_serials=serials)
    ok.append(("serial VBlank recupera voltas completas ocultas",
               loop_prof["profile_valido"]
               and loop_prof["frame_wraps_known"]
               and loop_prof["linhas_por_etapa"]["input_cmd_end"] == 629
               and loop_prof["linhas_desde_inicio"]["loop_end"] == 783))
    ok.append(("serial VBlank inconsistente reprova perfil",
               profile_lines_with_vblank([191, 194], [10, 10]) is None))
    loop_prof = loop_profile_report([0xC1, 0xCD], 2,
                                   ("loop_start", "map_build_end"))
    ok.append(("perfil do loop aceita nomes definidos pela fonte",
               loop_prof["profile_valido"]
               and loop_prof["linhas_por_etapa"]["map_build_end"] == 12))
    ok.append(("checkpoints VCounter sem dados rejeitam",
               profile_lines([0xC0, None]) is None))
    # contrato do probe: sem header SMRT+schema, nenhuma leitura e evidencia
    ok.append(("lixo sem magic nao autentica",
               magic_ok([0, 0, 0, 0, 0]) is False))
    ok.append(("SMRT+schema1 autentica",
               magic_ok(list(b"SMRT") + [1]) is True))
    ok.append(("SMRT+schema2 (D10) autentica",
               magic_ok(list(b"SMRT") + [2]) is True))
    ok.append(("magic certo com schema errado rejeita",
               magic_ok(list(b"SMRT") + [3]) is False))
    ok.append(("header ausente (None) rejeita", magic_ok(None) is False))
    # contrato de fonte: a triade precisa estar DECLARADA no fonte da ROM
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        sd = os.path.join(td, "src")
        os.makedirs(sd)
        mc = os.path.join(sd, "m.c")

        session_rom = os.path.join(td, "private", "session-1", "emulator", "rom.sms")
        os.makedirs(os.path.dirname(session_rom))
        with open(session_rom, "wb") as f:
            f.write(b"test")
        ok.append(("sessao privada preserva projeto explicito do perfil",
                   profile_source_project(td, session_rom) == os.path.abspath(td)))
        inferred_project = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(session_rom))))
        ok.append(("ROM copiada sem projeto-fonte usa fallback local",
                   profile_source_project(os.path.join(td, "missing"), session_rom)
                   == inferred_project))

        def _src(body):
            with open(mc, "w") as f:
                f.write(body)
            return probe_contract(td)

        okc, miss = _src(
            "volatile unsigned char __at(0xC7EA) probe_vline;\n"
            "volatile unsigned int  __at(0xC7EB) probe_vovf;\n"
            "volatile unsigned char __at(0xC7ED) probe_phase;\n"
            "volatile unsigned char __at(0xC7EE) probe_worst_done;\n"
            "volatile unsigned char __at(0xC7D2) probe_vline_min;\n"
            "#define WORST_FRAME_WINDOW 3000u\n")
        ok.append(("triade completa autentica", okc and not miss))
        okc, miss = _src(
            "volatile unsigned char __at(0xC7EA) probe_vline;\n"
            "volatile unsigned char __at(0xC7EB) probe_vovf;\n"
            "volatile unsigned char __at(0xC7ED) probe_phase;\n"
            "volatile unsigned char __at(0xC7EE) probe_worst_done;\n"
            "volatile unsigned char __at(0xC7D2) probe_vline_min;\n"
            "#define WORST_FRAME_WINDOW 3000u\n")
        ok.append(("vovf como BYTE rejeita (saturacao)", not okc))
        okc, miss = _src(
            "volatile unsigned char __at(0xC7EA) probe_vline;\n"
            "volatile unsigned int  __at(0xC7EB) probe_vovf;\n"
            "volatile unsigned char __at(0xC7ED) probe_phase;\n"
            "volatile unsigned char __at(0xC7EE) probe_worst_done;\n"
            "volatile unsigned char __at(0xC7D2) probe_vline_min;\n"
            "#define WORST_FRAME_WINDOW 2999u\n")
        ok.append(("janela diferente de 3000 rejeita", not okc))
        okc, miss = _src(
            "volatile unsigned char __at(0xC7EA) probe_vline;\n")
        ok.append(("so vline rejeita (faltam campos do contrato)",
                   not okc and len(miss) == 5))
        okc, miss = _src("int main(void){return 0;}\n")
        ok.append(("ROM sem probe algum rejeita (arena/laboratorio)",
                   not okc and len(miss) == 6))
        with open(mc, "a") as f:
            f.write("volatile unsigned char __at(0xC7D0) probe_profile_wait;\n"
                    "volatile unsigned char __at(0xC7D1) probe_profile_stream;\n"
                    "volatile unsigned char __at(0xC7D3) probe_profile_hud;\n"
                    "volatile unsigned char __at(0xC7D4) probe_profile_sat;\n"
                    "volatile unsigned char __at(0xC7D6) probe_vline_spill_max;\n")
        ok.append(("perfil opcional exige snapshot do maior derrame",
                   profile_contract(td)))
        with open(mc, "a") as f:
            f.write("volatile unsigned char __at(0xC790) tl_snap[16];\n"
                    "volatile unsigned char __at(0xC7D2) tl_snap_seq;\n")
        ok.append(("perfil do loop resolve o endereço do snapshot declarado",
                   loop_profile_address(td) == 0xC790))
        with open(mc, "a") as f:
            f.write("volatile unsigned char __at(0xC7F8) tl_snap[16];\n")
        ok.append(("perfil do loop rejeita snapshot absoluto duplicado",
                   loop_profile_address(td) is None
                   and not loop_profile_contract(td)))
        # Keep the remaining mutation checks on a single, unambiguous snapshot.
        text = open(mc, errors="replace").read()
        text = text.replace("volatile unsigned char __at(0xC790) tl_snap[16];\n", "")
        with open(mc, "w") as f:
            f.write(text)
        bad_addr = text.replace("__at(0xC7F8) tl_snap[16]",
                                "__at(0xBFF0) tl_snap[16]")
        with open(mc, "w") as f:
            f.write(bad_addr)
        ok.append(("perfil do loop rejeita snapshot fora da RAM do SMS",
                   loop_profile_address(td) is None
                   and not loop_profile_contract(td)))
        with open(mc, "w") as f:
            f.write(text)
        ok.append(("perfil do loop rejeita snapshot sem selo da janela",
                   not loop_profile_contract(td)))
        with open(mc, "a") as f:
            f.write("if (probe_frame <= WORST_FRAME_WINDOW) {\n"
                    "  tl_snap_seq++;\n  tl_snap_seq++;\n}\n")
        ok.append(("perfil do loop exige mapa e seqlock completos",
                   loop_profile_contract(td)))
        with open(mc, "a") as f:
            f.write("/* LOOP_PROFILE_NAMES: loop_start, map_build_end */\n")
        ok.append(("perfil do loop lê nomes de checkpoint da fonte",
                   loop_profile_names(td) == ("loop_start", "map_build_end")
                   and loop_profile_contract(td)))
        with open(mc, "a") as f:
            f.write("/* LOOP_PROFILE_METRICS: cells@0xC7D8:u16, runs@0xC7DA:u8 */\n")
        metrics = loop_profile_metrics(td)
        ok.append(("perfil do loop lê métricas fixas opcionais",
                   metrics == ({"name": "cells", "address": 0xC7D8, "width": 2},
                               {"name": "runs", "address": 0xC7DA, "width": 1})
                   and loop_profile_contract(td)))
        with open(mc, "a") as f:
            f.write("/* LOOP_PROFILE_METRICS: extra@0xC7DC:u8 */\n")
        ok.append(("perfil do loop rejeita diretiva de métricas duplicada",
                   loop_profile_metrics(td) is None
                   and not loop_profile_contract(td)))
        with open(mc, "a") as f:
            f.write("/* LOOP_PROFILE_NAMES: duplicate, duplicate */\n")
        ok.append(("perfil do loop rejeita nomes duplicados",
                   loop_profile_names(td) is None
                   and not loop_profile_contract(td)))
        # --- corredor realocado (L089): o contrato é base-dependente
        def _triade(block):
            return (
                "volatile unsigned char __at(0x%04X) probe_vline;\n"
                "volatile unsigned int  __at(0x%04X) probe_vovf;\n"
                "volatile unsigned char __at(0x%04X) probe_phase;\n"
                "volatile unsigned char __at(0x%04X) probe_worst_done;\n"
                "volatile unsigned char __at(0x%04X) probe_vline_min;\n"
                "volatile unsigned char __at(0x%04X) probe_profile_wait;\n"
                "volatile unsigned char __at(0x%04X) probe_profile_stream;\n"
                "volatile unsigned char __at(0x%04X) probe_profile_hud;\n"
                "volatile unsigned char __at(0x%04X) probe_profile_sat;\n"
                "volatile unsigned char __at(0x%04X) probe_vline_spill_max;\n"
                "#define WORST_FRAME_WINDOW 3000u\n"
                % (block + OFFSETS["vline"], block + OFFSETS["vovf"],
                   block + OFFSETS["phase"], block + OFFSETS["worst_done"],
                   block + OFFSETS["vline_min"],
                   block + OFFSETS["profile_wait"],
                   block + OFFSETS["profile_stream"],
                   block + OFFSETS["profile_hud"],
                   block + OFFSETS["profile_sat"],
                   block + OFFSETS["profile_spill_max"]))

        _src(_triade(0xC900))
        ok.append(("fonte realocada em 0xC900 reprova sob a base canonica",
                   not probe_contract(td)[0] and not profile_contract(td)))
        apply_probe_block(0xC900)
        ok.append(("fonte realocada autentica sob a base declarada",
                   probe_contract(td)[0] and profile_contract(td)))
        ok.append(("realocar move cabecalho, frame, estado e perfil",
                   PROBE_HEADER == 0xC9E0 and PROBE_FRAME == 0xC9F0
                   and PROBE_STATE == 0xC9F6 and PROBE_VLINE_MIN == 0xC9D2
                   and PROFILE_ADDRS["wait"] == 0xC9D0
                   and PROFILE_SPILL_MAX == 0xC9D6
                   and LOOP_PROFILE_SEQ == 0xC9D2
                   and MRP.PROBE_BASE == 0xC9E0
                   and MRP.FRAME_ADDR == 0xC9F0
                   and MRP.SNAP_ADDRS["pz"] == 0xC9FB
                   and MRP.SNAP_ADDRS["py"] == 0xC9FD
                   and MRP.SNAP_ADDRS["p2state"] == 0xC9FE))
        _src(_triade(0xC700))
        ok.append(("fonte canonica reprova sob a base realocada",
                   not probe_contract(td)[0] and not profile_contract(td)))
        for bad in (0xC950, 0xBF00, 0xE000):
            try:
                apply_probe_block(bad)
                rejected = False
            except ValueError:
                rejected = True
            ok.append(("base invalida %s rejeitada" % hex(bad), rejected))
        apply_probe_block(0xC700)
        ok.append(("base canonica restaurada",
                   PROBE_HEADER == 0xC7E0 and MRP.PROBE_BASE == 0xC7E0
                   and _src(_triade(0xC700))[0] and profile_contract(td)))

        # leitura do corredor derivada do fonte (dono de declared_probes)
        dp = os.path.join(td, "dp")
        os.makedirs(dp)
        with open(os.path.join(dp, "p.c"), "w") as f:
            f.write("volatile unsigned char __at(0xC900) a;\n"
                    "volatile unsigned int  __at(0xC901) b;\n"
                    "volatile unsigned char __at(0xC903) v[3];\n")
        probes = declared_probes(dp)
        ok.append(("declared_probes expande word e array",
                   probes == [("a", 0xC900, 1), ("b", 0xC901, 2),
                              ("v[0]", 0xC903, 1), ("v[1]", 0xC904, 1),
                              ("v[2]", 0xC905, 1)]))
        with open(os.path.join(dp, "q.c"), "w") as f:
            f.write("volatile unsigned char __at(0xC900) a;\n"
                    "volatile unsigned char __at(0xC902) b;\n")
        try:
            declared_probes(dp)
            overlap_caught = False
        except ValueError:
            overlap_caught = True
        ok.append(("sonda no byte alto de um word vira sobreposicao",
                   overlap_caught))
        os.remove(os.path.join(dp, "q.c"))
        with open(os.path.join(dp, "q.c"), "w") as f:
            f.write("volatile unsigned char __at(0xC901) c;\n")
        try:
            declared_probes(dp)
            word_overlap_caught = False
        except ValueError:
            word_overlap_caught = True
        ok.append(("byte baixo dentro de um word reprovado",
                   word_overlap_caught))
        ok.append(("fonte sem __at devolve corredor vazio",
                   declared_probes(os.path.join(td, "dp2")) == []))

        with open(mc, "w") as f:
            f.write("enum { ST_IDLE, ST_WALK_F, ST_N_STATES };\n")
        ok.append(("enum de estado do projeto rotula snapshot corretamente",
                   state_label(td, 0) == "IDLE"
                   and state_label(td, 1) == "WALK_F"))
    for nome, bom in ok:
        print("  %-42s %s" % (nome, "ok" if bom else "FALHOU"))
    if not all(b for _, b in ok):
        print("[SELF-CHECK FAIL] worst-frame")
        return 1
    print("[SELF-CHECK OK] measure_worst_frame")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--rom")
    ap.add_argument("--seconds", type=float, default=45.0,
                    help="janela minima solicitada, 1..50 s (ROM sela 3000 frames)")
    ap.add_argument("--wait-seconds", type=float,
                    help="espera DAP, 90..1800 s (default 90; diagnostico de ROM lenta)")
    ap.add_argument("--out", default="worst_frame")
    ap.add_argument("--probe-base", default="0xC700",
                    help="base do corredor de sondas (default 0xC700; "
                         "ex. 0xC900 para ROMs cujo _DATA encosta em 0xC790)")
    ap.add_argument("--session", help="ID de sessao privada (sem DAP global)")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return self_check()
    try:
        apply_probe_block(int(args.probe_base, 16))
    except ValueError as e:
        print("[FAIL_USO] %s" % e)
        return 3
    if args.session:
        code, _ = measure_private(args.session, args.project, args.seconds, args.out, args.wait_seconds)
        return code
    if not args.rom or not os.path.isfile(args.rom):
        print("[FAIL_AMBIENTE] ROM obrigatoria e inexistente: %s" % args.rom)
        return 3
    code, _ = measure(args.rom, args.project, args.seconds, args.out,
                      args.wait_seconds)
    return code


if __name__ == "__main__":
    sys.exit(main())
