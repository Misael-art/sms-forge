#!/usr/bin/env python3
"""luta_mugen_trace_dap.py — produtor de trilha por tick da ROM integrada do luta_mugen (doc/21 item 3, L097).

Por que nao ler tudo pelo DAP: o DAP so le com a emulacao PAUSADA e pausa/continua em tempo de parede, entao um
laco de leitura nao amostra tick a tick. Aqui a ROM CLONE grava o proprio estado a cada tick numa regiao de RAM
(TRC1/2: 12 B/tick, ate 170; TRC3: 6 B/tick, ate 340, com action_id e elemento AIR por lado) usando um roteiro embutido (o pad real e
ignorado: a trilha e deterministica). O DAP so DESPEJA o buffer depois que `done`=1.

Fluxo: roteiro -> trace_script.h -> copia isolada da arvore local (out/local_study/luta_integrada) com os
ganchos reais -> build_inner.py -> Emulicious + DAP -> decodifica -> JSON no formato de
mugen2sms/analysis/trace_compare.py, mais um .meta.json com SHA da ROM e do roteiro.

A ROM canonica NAO muda: `inc/trace_hooks.h` define os ganchos como identidade/vazio. `--check-canonical`
constroi a arvore sem e com os ganchos e exige ROMs identicas byte a byte.

Limites declarados: grava estado logico e, em TRC3, action ID + indice de elemento AIR — nao render, nao SAT,
nao tempo de Z80. TRC3 exige manifestos AIR-fonte e de corte/runtime hash-vinculados, --keep para reter
ROM/dump/sessao e uma acao finita completa.
Nao e evidencia de FPS nem de latencia de input humano.

Uso: luta_mugen_trace_dap.py --scenario NOME [--out trilha.json] | --check-canonical | --self-check
Exit: 0 ok | 1 reprovado | 2 ambiente ausente | 3 uso
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECT = ROOT / "SMS_projects" / "luta_mugen"
CANON = PROJECT / "integrada"
STUDY = PROJECT / "out" / "local_study" / "luta_integrada"
sys.path.insert(0, str(HERE))

K = {"u": 0x01, "d": 0x02, "l": 0x04, "r": 0x08, "lp": 0x10, "hp": 0x20, "guard": 0x40}
TRACE_BASE, TRACE_HDR, TRACE_REC, TRACE_MAX = 0xD200, 8, 12, 170
TRACE_GUARD = TRACE_BASE + 2048        # 8 canary bytes 0xA5 between trace and stack
SCHEMA = "luta_mugen_trace_v1"
AIR_TRACE_REC, AIR_TRACE_MAX = 6, 340
from mugen2sms.analysis import trace_air_identity as AIR_TRACE

# Cenarios: (roteiro P1, roteiro P2). Cada roteiro: "tokens:ticks ..."; tokens = '-' ou nomes unidos por '+'.
# Lote D 6.D (doc/23 secao D): "roteiro de entrada por acao" para as 9 acoes dos dois pads. P1 comeca a
# esquerda (frente = r, costas = l); P2 comeca a direita (frente = l, costas = r). Guarda = baixo + costas.
# Os tiers fortes (lp:9 / hp:9) NAO tem roteiro aqui: o corte nao tem pose daquele tier (fight.c
# attack_states = NO_ADV_STATE) e doc/24 registra o bloqueio de banco de pose -- medida sem pose seria
# numero de coisa nenhuma.
SCENARIOS = {
    "idle": ("-:170", "-:170"),
    "soco": ("-:10 lp:3 -:157", "-:170"),
    "soco_p2": ("-:170", "-:10 lp:3 -:157"),
    "chute": ("-:10 hp:3 -:157", "-:170"),
    "chute_p2": ("-:170", "-:10 hp:3 -:157"),
    "agachar": ("-:10 d:40 -:120", "-:170"),
    "agachar_p2": ("-:170", "-:10 d:40 -:120"),
    "andar_frente": ("-:10 r:60 -:100", "-:170"),
    "andar_frente_p2": ("-:170", "-:10 l:60 -:100"),
    "andar_tras": ("-:10 l:60 -:100", "-:170"),
    "andar_tras_p2": ("-:170", "-:10 r:60 -:100"),
    "pulo": ("-:10 u:2 -:158", "-:170"),
    "pulo_p2": ("-:170", "-:10 u:2 -:158"),
    "guarda": ("-:10 d+l:40 -:120", "-:170"),
    "guarda_p2": ("-:170", "-:10 d+r:40 -:120"),
}


# Variantes EXPERIMENTAIS aplicadas so na copia isolada (nunca na fonte canonica): lista de
# (arquivo, trecho antigo, trecho novo); cada trecho antigo precisa existir EXATAMENTE uma vez.
VARIANTS = {
    "baseline": [],
    # hipotese L099: o lutador cuja pose desejada ainda nao esta em tela (urgente) e servido antes do
    # que so pre-carrega a proxima pose; empate mantem a alternancia por paridade.
    "urgent_first": [
        ("inc/stream.h", "#define STREAM_SLOTS 128u",
         "#define STREAM_SLOTS 128u\nextern unsigned char stream_urgent[2];"),
        ("src/stream.c", "static unsigned char frame_parity;",
         "unsigned char stream_urgent[2];\nstatic unsigned char frame_parity;"),
        ("src/stream.c", "    if (frame_parity) { upload(1); upload(0); }\n    else              { upload(0); upload(1); }",
         "    if (stream_urgent[0] != stream_urgent[1]) {\n"
         "        if (stream_urgent[0]) { upload(0); upload(1); } else { upload(1); upload(0); }\n"
         "    } else if (frame_parity) { upload(1); upload(0); }\n"
         "    else              { upload(0); upload(1); }"),
        ("src/fight.c", "            if (!skip)\n                stream_request(i, req_pt, p->facing, req_pose);",
         "            if (!skip) {\n"
         "                stream_urgent[i] = (unsigned char)!stream_shows(i, c->want_pt, p->facing);\n"
         "                stream_request(i, req_pt, p->facing, req_pose);\n"
         "            }"),
    ],
}
# L099 (2a hipotese): o urgente simples nao separa os lutadores — o idle do Ryu tambem espera pose. Prioridade
# so para quem esta em ACAO (estado != idle) e ainda nao tem a pose desejada em tela.
VARIANTS["action_first"] = [
    (f, o, n.replace("(unsigned char)!stream_shows(i, c->want_pt, p->facing)",
                     "(unsigned char)(p->state != 0u && !stream_shows(i, c->want_pt, p->facing))"))
    for f, o, n in VARIANTS["urgent_first"]
]

# Opcao B (decisao do usuario: seguir a sugestao do agente): a LOGICA (animacao, hitbox, hurtbox) corre no tempo do
# AIR; a arte mostra a ultima pose COMPLETA. Mudancas: (1) tick_anim sem a guarda de pose visivel; (2) hit/hurt
# usam o quadro logico; (3) um upload em andamento nao e descartado por um alvo mais novo; (4) o display
# apresenta o ultimo alvo completo (mesma direcao), nao so o alvo exato.
VARIANTS["decoupled"] = [
    ("src/fight.c", "    if (visible_pose[pslot] != wanted_pose || fr->dur == 255) return;",
     "    (void)wanted_pose;\n    if (fr->dur == 255) return;"),
    ("src/fight.c", "        const Frame *attack_frame = frame_for_pose(pslot, visible_pose[pslot]);",
     "        const Frame *attack_frame = cur_frame(p, pslot);"),
    ("src/fight.c", "    const Frame *f = frame_for_pose(slot, visible_pose[slot]);\n    if (f->clsn) return f->clsn;",
     "    const Frame *f = cur_frame(p, slot);\n    if (f->clsn) return f->clsn;"),
    # (v2) NEXT pendente (em andamento OU completo e ainda nao apresentado) nao e descartado por um alvo mais
    # novo: o display o apresenta primeiro. So troca de direcao invalida o pendente (senao travaria).
    ("src/stream.c", "    if (n->pt) { release(n); stream_dropped++; }   /* stale upload never shown */",
     "    if (n->pt) {\n        if (n->facing == facing) return;\n        release(n); stream_dropped++;\n    }"),
    ("src/stream.c", "    if (!reclaim[who] && n->pt == want && n->facing == want_facing &&\n        load_done[who] == n->nslots) {",
     "    (void)want;\n    if (!reclaim[who] && n->pt && n->facing == want_facing &&\n        load_done[who] == n->nslots) {"),
]


def apply_variant(work: Path, name: str) -> str:
    """Aplica a variante na copia; devolve o sha256 do conjunto de trechos (rastreio)."""
    if name not in VARIANTS:
        raise SystemExit(f"[USO] variante '{name}' desconhecida; validas: {sorted(VARIANTS)}")
    h = hashlib.sha256(name.encode())
    for rel, old, new in VARIANTS[name]:
        f = work / rel
        txt = f.read_text(encoding="utf-8")
        if txt.count(old) != 1:
            raise SystemExit(f"[FAIL] variante {name}: trecho esperado {txt.count(old)}x (!=1) em {rel}: {old[:60]!r}")
        f.write_text(txt.replace(old, new, 1), encoding="utf-8")
        h.update((rel + old + new).encode())
    return h.hexdigest()


# ---------------------------------------------------------------- puro (testado no self-check)
def parse_track(text: str) -> list[tuple[int, int]]:
    """'lp:3 d+r:2 -:5' -> [(0x10,3),(0x0A,2),(0,5)]. Erro de sintaxe levanta ValueError (sem adivinhar)."""
    out = []
    for part in text.split():
        tok, _, n = part.rpartition(":")
        if not tok or not n.isdigit() or int(n) < 1:
            raise ValueError(f"token invalido '{part}' (esperado teclas:ticks, ticks>=1)")
        keys = 0
        if tok != "-":
            for name in tok.split("+"):
                if name not in K:
                    raise ValueError(f"tecla desconhecida '{name}' em '{part}' (validas: {sorted(K)} ou '-')")
                keys |= K[name]
        out.append((keys, int(n)))
    return out


def compile_script(p1: str, p2: str, ticks: int = TRACE_MAX) -> list[tuple[int, int, int]]:
    """RLE [(n, keys_p1, keys_p2)] com n<=255, cobrindo EXATAMENTE `ticks` ticks (completa/recusa)."""
    def expand(track):
        seq = [k for k, n in track for _ in range(n)]
        if len(seq) > ticks:
            raise ValueError(f"roteiro com {len(seq)} ticks excede a janela de {ticks}")
        return seq + [0] * (ticks - len(seq))
    a, b = expand(parse_track(p1)), expand(parse_track(p2))
    rle: list[list[int]] = []
    for x, y in zip(a, b):
        if rle and rle[-1][1] == x and rle[-1][2] == y and rle[-1][0] < 255:
            rle[-1][0] += 1
        else:
            rle.append([1, x, y])
    return [tuple(e) for e in rle]


def render_script_header(rle) -> str:
    body = ",".join(f"{n},{x},{y}" for n, x, y in rle)
    return ("/* gerado por luta_mugen_trace_dap.py — nao editar */\n"
            f"const unsigned char trace_script[] = {{ {body},0 }};\n")


FIELDS = ("state", "frame", "tick", "x", "life_lo", "flags")


def decode_buffer(buf: bytes, expect_ticks: int = TRACE_MAX) -> dict[str, list[dict]]:
    """Decodifica o despejo (cabecalho + registros) em {"p1": [...], "p2": [...]} -> trilha por tick.
    Recusa magic errado, gravacao nao concluida, tamanho de registro ou contagem diferentes do esperado."""
    if len(buf) < TRACE_HDR:
        raise ValueError("despejo menor que o cabecalho")
    if bytes(buf[:4]) != b"TRC1":
        raise ValueError(f"magic {bytes(buf[:4])!r} != b'TRC1' (ROM sem gravador ou outro binario)")
    done, n, rec = buf[4], buf[5] | (buf[6] << 8), buf[7]
    if rec != TRACE_REC:
        raise ValueError(f"tamanho de registro {rec} != {TRACE_REC}")
    if done != 1:
        raise ValueError(f"gravacao nao concluida (done={done}, n={n})")
    if n != expect_ticks:
        raise ValueError(f"{n} ticks gravados, esperado {expect_ticks}")
    if len(buf) < TRACE_HDR + n * rec:
        raise ValueError("despejo truncado")
    ticks = []
    for t in range(n):
        row = {"tick": t}
        base = TRACE_HDR + t * rec
        for side, off in (("p1", 0), ("p2", 6)):
            s, f, tk, x, lo, fl = buf[base + off:base + off + 6]
            row[f"{side}_state"], row[f"{side}_frame"], row[f"{side}_tick"] = s, f, tk
            row[f"{side}_x"] = x
            row[f"{side}_life"] = lo | (((fl >> 2) & 3) << 8)
            row[f"{side}_facing"] = fl & 1
            row[f"{side}_hit_done"] = (fl >> 1) & 1
            row[f"{side}_hitstop"] = (fl >> 4) & 1
            row[f"{side}_air"] = (fl >> 5) & 1
        ticks.append(row)
    return ticks


PROFILE_FIELDS = ("p1_state", "p1_frame", "p1_tick", "load_done_p1", "vc_wait", "vc_hud", "vc_sat", "vc_stream",
                  "slots_used", "vis_pose_p1", "load_done_p2", "dropped")


def decode_profile(buf: bytes, expect_ticks: int = TRACE_MAX) -> list[dict]:
    """Modo perfil ('TRC2'): mesmas recusas do decode_buffer; 12 campos inteiros por tick."""
    if len(buf) < TRACE_HDR:
        raise ValueError("despejo menor que o cabecalho")
    if bytes(buf[:4]) != b"TRC2":
        raise ValueError(f"magic {bytes(buf[:4])!r} != b'TRC2' (ROM sem gravador de perfil)")
    done, n, rec = buf[4], buf[5] | (buf[6] << 8), buf[7]
    if rec != TRACE_REC or done != 1 or n != expect_ticks or len(buf) < TRACE_HDR + n * rec:
        raise ValueError(f"perfil invalido (rec={rec}, done={done}, n={n}, bytes={len(buf)})")
    return [{"tick": t, **dict(zip(PROFILE_FIELDS, buf[TRACE_HDR + t * rec:TRACE_HDR + (t + 1) * rec]))}
            for t in range(n)]


def build_header_bytes(n: int, done: int = 1, rec: int = TRACE_REC) -> bytes:
    return b"TRC1" + bytes([done, n & 255, n >> 8, rec])


# ---------------------------------------------------------------- build (arvore isolada)
def _copy_tree(work: Path) -> None:
    if not (STUDY / "inc" / "versus_scene_runtime_full_generated.h").is_file():
        raise SystemExit(f"[FAIL_AMBIENTE] arvore local ausente: {STUDY} (dado derivado nao versionado)")
    shutil.copytree(STUDY, work, ignore=shutil.ignore_patterns("out", "__pycache__"))
    (work / "out").mkdir()
    import build_luta_integrada as B
    for src in sorted((CANON / "src").glob("*.c")):
        shutil.copy2(src, work / "src" / src.name)
    for name in B.HAND_HEADERS:
        shutil.copy2(CANON / "inc" / name, work / "inc" / name)
    shutil.copy2(CANON / ".mddev" / "project.json", work / ".mddev" / "project.json")


def make_clone(work: Path, script_header: str | None = None, main_override: str | None = None,
               profile: bool = False, variant: str = "baseline",
               air_identity: bool = False) -> Path:
    """Arvore isolada. script_header=None -> canonica (ganchos vazios). main_override: texto de main.c."""
    if profile and air_identity:
        raise ValueError("profile e AIR identity usam formatos de trace diferentes")
    _copy_tree(work)
    if main_override is not None:
        (work / "src" / "main.c").write_text(main_override, encoding="utf-8")
    apply_variant(work, variant)
    if script_header is not None:
        hooks = work / "inc" / "trace_hooks.h"
        shutil.copy2(CANON / "trace" / "trace_hooks_rec.h", hooks)
        if air_identity:
            hook_text = hooks.read_text(encoding="utf-8")
            guard = "#define TRACE_HOOKS_H\n"
            if hook_text.count(guard) != 1:
                raise SystemExit("[FAIL] trace hook header lacks its expected guard")
            hooks.write_text(hook_text.replace(guard, guard + "#define TRACE_AIR_IDENTITY 1\n", 1),
                             encoding="utf-8")
        shutil.copy2(CANON / "trace" / "trace_rec.c", work / "src" / "trace_rec.c")
        (work / "inc" / "trace_script.h").write_text(script_header, encoding="utf-8")
        trace_profile = 2 if air_identity else (1 if profile else 0)
        (work / "inc" / "trace_cfg.h").write_text(f"#define TRACE_PROFILE {trace_profile}\n", encoding="utf-8")
        if profile:      # instrumentacao so da copia de perfil: load_done static -> global (sem mudar logica)
            sc = work / "src" / "stream.c"
            txt = sc.read_text(encoding="utf-8")
            old = "static unsigned char load_done[2];"
            if old not in txt:
                raise SystemExit("[FAIL] stream.c nao tem a declaracao esperada de load_done (instrumentacao de perfil)")
            sc.write_text(txt.replace(old, "unsigned char load_done[2];", 1), encoding="utf-8")
    return work


def build_rom(work: Path) -> Path:
    r = subprocess.run([sys.executable, str(HERE / "build_inner.py"), "--project", str(work)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-2000:])
        raise SystemExit(f"[FAIL] build_inner rc={r.returncode} em {work}")
    roms = sorted((work / "out" / "rom").glob("*.sms"))
    if len(roms) != 1:
        raise SystemExit(f"[FAIL] esperava 1 ROM em {work}/out/rom, achei {len(roms)}")
    layout=CANON/"tools/check_ram_layout.py"
    maps=list((work/"out/obj").glob("*.map"))
    if not layout.is_file() or len(maps)!=1:
        raise SystemExit("[FAIL] RAM layout checker/map absent; trace cannot be authenticated")
    audit=subprocess.run([sys.executable,str(layout),"--map",str(maps[0]),"--rom",str(roms[0]),
                          "--sources",*[str(p) for p in sorted((work/"src").glob("*.c"))],
                          *[str(p) for p in sorted((work/"inc").glob("*.h"))]],
                         capture_output=True,text=True)
    (work/"out/trace_ram_layout.log").write_text(audit.stdout+audit.stderr)
    if audit.returncode:
        raise SystemExit("[FAIL] trace RAM contract overlaps or cannot be verified; see "+str(work/"out/trace_ram_layout.log"))
    return roms[0]


def _split_c_macro_args(body: str) -> list[str]:
    args = []
    start = 0
    parens = braces = brackets = 0
    quote = None
    escaped = False
    for index, char in enumerate(body):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ('"', "'"):
            quote = char
        elif char == "(":
            parens += 1
        elif char == ")":
            parens -= 1
        elif char == "{":
            braces += 1
        elif char == "}":
            braces -= 1
        elif char == "[":
            brackets += 1
        elif char == "]":
            brackets -= 1
        elif char == "," and parens == braces == brackets == 0:
            args.append(body[start:index].strip())
            start = index + 1
    tail = body[start:].strip()
    if tail:
        args.append(tail)
    return args


def _macro_call_spans(source: str, macro: str) -> list[tuple[int, int, list[str]]]:
    """Find balanced macro calls and split only top-level C arguments."""
    calls = []
    pattern = re.compile(rf"\b{re.escape(macro)}\s*\(")
    for match in pattern.finditer(source):
        opening = match.end() - 1
        depth = 1
        quote = None
        escaped = False
        index = opening + 1
        while index < len(source) and depth:
            char = source[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
            elif char in ('"', "'"):
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            index += 1
        if depth:
            raise ValueError(f"unterminated {macro} invocation")
        close = index - 1
        calls.append((match.start(), index,
                      _split_c_macro_args(source[opening + 1:close])))
    return calls


def strip_trace_hook_calls(main_source: str) -> str:
    """Make a same-revision baseline by expanding the canonical no-op hooks."""
    source, include_count = re.subn(
        r'^\s*#include\s+"trace_hooks\.h"\s*$', "", main_source, flags=re.M)
    if include_count != 1:
        raise ValueError(f"expected one trace_hooks.h include, found {include_count}")
    replacements = []
    for start, end, args in _macro_call_spans(source, "TRACE_RECORD"):
        if args:
            raise ValueError("TRACE_RECORD must have no arguments")
        replacements.append((start, end, "((void)0)"))
    pad_calls = _macro_call_spans(source, "TRACE_PAD")
    if len(pad_calls) != 2:
        raise ValueError(f"expected two TRACE_PAD calls, found {len(pad_calls)}")
    for start, end, args in pad_calls:
        if len(args) != 2 or not args[1]:
            raise ValueError("TRACE_PAD must have two arguments and a real-input expression")
        replacements.append((start, end, args[1]))
    for start, end, replacement in sorted(replacements, reverse=True):
        source = source[:start] + replacement + source[end:]
    return source


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_runtime_source_manifest(manifest: dict, source_identity: dict,
                                     side: str) -> dict:
    """Bind a source AIR identity to the selected source package in a scene cut."""
    if not isinstance(manifest, dict) or manifest.get("schema") != "sms_versus_scene_cut_v1":
        raise ValueError("runtime source manifest must use sms_versus_scene_cut_v1")
    sources = manifest.get("source_sha256")
    if not isinstance(sources, dict):
        raise ValueError("runtime source manifest has no source_sha256 map")
    slot_keys = [key for key in sources if isinstance(key, str) and key.startswith(side + "_")]
    if len(slot_keys) != 1:
        raise ValueError(f"runtime source manifest must identify exactly one {side} source")
    runtime_sha = sources[slot_keys[0]]
    source_sha = source_identity.get("source", {}).get("package_sha256")
    if runtime_sha != source_sha:
        raise ValueError(f"{side} runtime package SHA-256 differs from AIR source package")
    return {"slot": slot_keys[0], "package_sha256": runtime_sha}


def validate_runtime_cut_manifest(manifest: dict, source_identity: dict) -> set[int]:
    """Return declared action IDs from the exact per-character scene-cut manifest."""
    if not isinstance(manifest, dict):
        raise ValueError("runtime cut manifest must be an object")
    source_sha = source_identity.get("source", {}).get("package_sha256")
    if manifest.get("source_sha256") != source_sha:
        raise ValueError("runtime cut manifest package SHA-256 differs from AIR source package")
    roles = manifest.get("roles")
    if not isinstance(roles, list) or not roles:
        raise ValueError("runtime cut manifest has no role/action list")
    action_ids = set()
    role_names = set()
    for role in roles:
        if not isinstance(role, dict):
            raise ValueError("runtime cut manifest contains a malformed role")
        name, action_id = role.get("role"), role.get("action")
        if not isinstance(name, str) or not name.strip() or name in role_names:
            raise ValueError("runtime cut manifest role names must be unique non-empty strings")
        if type(action_id) is not int or not 0 <= action_id <= 0xFFFF:
            raise ValueError(f"runtime cut role {name} action must be uint16")
        role_names.add(name)
        action_ids.add(action_id)
    return action_ids


def runtime_action_ids(fight_source: str, frame_data_header: str, side: str) -> set[int]:
    """Read the source action IDs that the compiled character table can execute."""
    if side not in {"p1", "p2"}:
        raise ValueError("side must be p1 or p2")
    character_table = re.search(
        r"static\s+const\s+CharacterData\s+characters\s*\[\s*2\s*\]\s*=\s*\{(.*?)\n\};",
        fight_source, re.S)
    if not character_table:
        raise ValueError("fight source has no two-slot CharacterData table")
    animation_names = re.findall(
        r"^\s*\{\s*([A-Za-z_]\w*_anims)\s*,", character_table.group(1), re.M)
    if len(animation_names) != 2:
        raise ValueError("fight source does not expose two animation tables")
    table_name = animation_names[0 if side == "p1" else 1]
    table = re.search(
        rf"static\s+const\s+Anim\s+{re.escape(table_name)}\s*\[\s*(\d+)\s*\]\s*=\s*\{{(.*?)\n\}};",
        frame_data_header, re.S)
    if not table:
        raise ValueError(f"runtime frame data has no animation table {table_name}")
    declared_count = int(table.group(1))
    action_ids = [int(value) for value in re.findall(
        r"^\s*\{\s*(\d+)[uU]?\s*,", table.group(2), re.M)]
    if declared_count == 0 or len(action_ids) != declared_count:
        raise ValueError(f"runtime animation table {table_name} is incomplete")
    if any(not 0 <= value <= 0xFFFF for value in action_ids):
        raise ValueError(f"runtime animation table {table_name} contains a non-uint16 action")
    return set(action_ids)


def check_canonical(scratch: Path) -> int:
    """Compare current main.c with hook calls stripped vs canonical no-op macros."""
    current_main = (CANON / "src" / "main.c").read_text(encoding="utf-8")
    baseline_main = strip_trace_hook_calls(current_main)
    a = build_rom(make_clone(scratch / "sem_ganchos", None, baseline_main))
    b = build_rom(make_clone(scratch / "com_ganchos", None, current_main))
    sa, sb = sha256(a), sha256(b)
    print(f"sem ganchos {sa}\ncom ganchos {sb}")
    ok = sa == sb
    print("[PASS] ROM identica byte a byte: ganchos de custo zero" if ok else "[FAIL] ROMs diferem")
    return 0 if ok else 1


# ---------------------------------------------------------------- DAP
def dump_via_dap(rom: Path, log: Path, timeout_s: float = 90.0, magic: bytes = b"TRC1",
                 expected_ticks: int = TRACE_MAX, record_size: int = TRACE_REC) -> bytes:
    # Historical function name retained for callers. RAM now comes from the
    # private process bridge: no global Java search or fixed DAP port.
    from session_bridge.isolated import start,request,load,atomic,close_session
    session=start(rom)
    atomic(log.with_suffix(".session.json"),load(session)[1])
    try:
        deadline=time.monotonic()+timeout_s
        while True:
            hdr=request(session,"read",TRACE_BASE,TRACE_HDR)["ram"]
            if bytes(hdr[:4])==magic and hdr[4]==1:break
            if time.monotonic()>deadline:raise RuntimeError(f"trace incomplete: {hdr}")
            request(session,"step",120)
        n=hdr[5]|hdr[6]<<8
        if n>expected_ticks:raise ValueError("trace count exceeds RAM contract")
        data=bytearray(hdr)
        for offset in range(0,n*record_size,256):
            data.extend(request(session,"read",TRACE_BASE+TRACE_HDR+offset,min(256,n*record_size-offset))["ram"])
        guard=bytes(request(session,"read",TRACE_GUARD,8)["ram"])
        if guard!=b"\xA5"*8:raise RuntimeError(f"trace guard corrupted (stack overrun?): {guard.hex()}")
        if n!=expected_ticks or hdr[7]!=record_size:raise RuntimeError(f"trace header inconsistent: count={n} rec={hdr[7]}")
        log.write_text(f"private session {session}; guard intact {guard.hex()}; framebuffer/input independent of host\n")
        return bytes(data)
    finally:
        close_session(session)


def produce(name: str, out: Path, scratch: Path, keep: bool = False, profile: bool = False,
            variant: str = "baseline", air_source_manifest: Path | None = None,
            air_side: str = "p1", runtime_source_manifest: Path | None = None,
            runtime_cut_manifest: Path | None = None) -> int:
    if name not in SCENARIOS:
        print(f"[USO] cenario '{name}' desconhecido; validos: {sorted(SCENARIOS)}")
        return 3
    identity_mode = air_source_manifest is not None
    if identity_mode and profile:
        raise SystemExit("--air-source-manifest nao pode ser combinado com --profile")
    if identity_mode and not keep:
        raise SystemExit("--air-source-manifest exige --keep para reter ROM, dump e sessao")
    if identity_mode and runtime_source_manifest is None:
        raise SystemExit("--air-source-manifest exige --runtime-source-manifest para vincular fonte e corte")
    if identity_mode and runtime_cut_manifest is None:
        raise SystemExit("--air-source-manifest exige --runtime-cut-manifest do slot escolhido")
    if identity_mode and air_side not in {"p1", "p2"}:
        raise SystemExit("--air-side deve ser p1 ou p2")
    source_identity = None
    runtime_manifest = None
    runtime_binding = None
    runtime_cut = None
    runtime_cut_actions = None
    if identity_mode:
        try:
            source_identity = json.loads(air_source_manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SystemExit(f"[FAIL] manifesto AIR-fonte ilegivel: {exc}") from exc
        if (not isinstance(source_identity, dict)
                or source_identity.get("schema") != "mugen2sms.air-source-identity/v1"):
            raise SystemExit("[FAIL] schema de manifesto AIR-fonte nao suportado")
        try:
            AIR_TRACE.validate_source_identity(source_identity)
        except ValueError as exc:
            raise SystemExit(f"[FAIL] contrato/procedencia AIR-fonte invalido: {exc}") from exc
        try:
            runtime_manifest = json.loads(runtime_source_manifest.read_text(encoding="utf-8"))
            runtime_binding = validate_runtime_source_manifest(
                runtime_manifest, source_identity, air_side)
            runtime_cut = json.loads(runtime_cut_manifest.read_text(encoding="utf-8"))
            runtime_cut_actions = validate_runtime_cut_manifest(runtime_cut, source_identity)
        except (OSError, ValueError) as exc:
            raise SystemExit(f"[FAIL] manifesto de fonte do runtime invalido: {exc}") from exc
    p1, p2 = SCENARIOS[name]
    trace_max = AIR_TRACE_MAX if identity_mode else TRACE_MAX
    trace_rec = AIR_TRACE_REC if identity_mode else TRACE_REC
    rle = compile_script(p1, p2, ticks=trace_max)
    header = render_script_header(rle)
    work = scratch / f"trace_{name}"
    if work.exists():
        shutil.rmtree(work)
    make_clone(work, header, profile=profile, variant=variant, air_identity=identity_mode)
    if identity_mode:
        try:
            imported_actions = runtime_action_ids(
                (work / "src" / "fight.c").read_text(encoding="utf-8"),
                (work / "inc" / "source_frame_data.h").read_text(encoding="utf-8"),
                air_side)
        except (OSError, ValueError) as exc:
            raise SystemExit(f"[FAIL] inventario de AIR importado ilegivel: {exc}") from exc
        if source_identity["action_id"] not in imported_actions:
            raise SystemExit(
                f"[FAIL] AIR action {source_identity['action_id']} nao esta na tabela do runtime {air_side}; "
                "nao vou iniciar emulador com identidade de fonte sem import correspondente")
        if imported_actions != runtime_cut_actions:
            raise SystemExit(
                f"[FAIL] manifest do corte declara actions {sorted(runtime_cut_actions)}, "
                f"mas a tabela compilada {air_side} contem {sorted(imported_actions)}")
    rom = build_rom(work)
    magic = b"TRC3" if identity_mode else (b"TRC2" if profile else b"TRC1")
    raw = dump_via_dap(rom, work / "emu.log", magic=magic,
                       expected_ticks=trace_max, record_size=trace_rec)
    if identity_mode:
        ticks = AIR_TRACE.decode_buffer(raw, expect_ticks=trace_max)
        boundary_trace = AIR_TRACE.derive_action_boundaries(ticks, air_side, source_identity)
        out.parent.mkdir(parents=True, exist_ok=True)
        ticks_path = out.with_suffix(".ticks.json")
        ticks_path.write_text(json.dumps({name: ticks}, indent=2), encoding="utf-8")
        out.write_text(json.dumps(boundary_trace, indent=2), encoding="utf-8")
    else:
        ticks = decode_profile(raw) if profile else decode_buffer(raw)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({name: ticks}), encoding="utf-8")
    meta = {"schema": "mugen2sms.air-identity-rom-bundle/v1" if identity_mode else SCHEMA,
            "mode": "air_identity" if identity_mode else ("profile" if profile else "state"),
            "variant": variant, "variant_sha256": hashlib.sha256(json.dumps(VARIANTS[variant]).encode()).hexdigest(), "scenario": name, "script_p1": p1, "script_p2": p2, "ticks": len(ticks),
            "rom": str(rom), "rom_sha256": sha256(rom), "script_header_sha256":
            hashlib.sha256(header.encode()).hexdigest(), "dump_sha256": hashlib.sha256(raw).hexdigest(),
            "emulator": "Emulicious via DAP; buffer despejado so apos done=1 (leitura com emulacao pausada)",
            "scope": ("logical AIR action/element identity and finite action timing; diagnostic trace build, not visual or FPS proof" if identity_mode else
                      "perfil de fase (VCounter por fase) e pool; nao e estado da luta nem FPS" if profile else
                      "estado da luta por tick; nao e render, SAT, FPS nem latencia de input humano")}
    if identity_mode:
        meta.update({
            "air_side": air_side,
            "air_action_id": source_identity["action_id"],
            "air_source_manifest": str(air_source_manifest.resolve()),
            "air_source_manifest_sha256": sha256(air_source_manifest),
            "air_source_sha256": source_identity.get("source", {}).get("air_sha256"),
            "runtime_source_manifest": str(runtime_source_manifest.resolve()),
            "runtime_source_manifest_sha256": sha256(runtime_source_manifest),
            "runtime_source_binding": runtime_binding,
            "runtime_cut_manifest": str(runtime_cut_manifest.resolve()),
            "runtime_cut_manifest_sha256": sha256(runtime_cut_manifest),
            "runtime_cut_action_ids": sorted(runtime_cut_actions),
            "air_boundary_trace": str(out.resolve()),
            "air_tick_trace": str(out.with_suffix(".ticks.json").resolve()),
        })
    meta_path = out.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    if identity_mode:
        from audit_subagent_session import ref
        from audit_import_semantics import evaluate as audit_import_record
        source_path = air_source_manifest.resolve()
        ticks_path = out.with_suffix(".ticks.json")
        session_path = work / "emu.session.json"
        if not session_path.is_file():
            raise SystemExit("[FAIL] sessao privada nao deixou manifest de evidencias")
        record = {
            "schema": "mugen2sms.import-semantics/v1",
            "kind": "air_identity_timing",
            "counter_bits": 16,
            "source_durations": source_identity["durations"],
            "source_air": ref(source_path),
            "trace": ref(out),
            "runtime_source_manifest": ref(runtime_source_manifest.resolve()),
            "runtime_cut_manifest": ref(runtime_cut_manifest.resolve()),
            "evidence": [ref(source_path), ref(runtime_source_manifest.resolve()),
                         ref(runtime_cut_manifest.resolve()), ref(out), ref(ticks_path), ref(rom),
                         ref(meta_path), ref(session_path)],
        }
        verdict = audit_import_record(record, require_air_identity=True)
        if not verdict["ok"]:
            raise SystemExit("[FAIL] AIR identity audit rejected trace bundle: "
                             + "; ".join(verdict["problems"]))
        out.with_suffix(".record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"[PASS] {name}: {len(ticks)} ticks -> {out}  (ROM {meta['rom_sha256'][:12]})")
    if not keep:
        shutil.rmtree(work, ignore_errors=True)
    return 0


# ---------------------------------------------------------------- self-check
def self_check() -> int:
    ok = True

    def check(cond, msg):
        nonlocal ok
        if not cond:
            ok = False
            print("  [FAIL]", msg)

    check(parse_track("lp:3 d+r:2 -:5") == [(0x10, 3), (0x0A, 2), (0, 5)], "parse_track")
    for bad in ("lp", "lp:0", "xx:3", ":3", "lp:a"):
        try:
            parse_track(bad)
            check(False, f"deveria recusar '{bad}'")
        except ValueError:
            pass
    rle = compile_script("lp:3 -:10", "-:5 hp:2")
    check(sum(n for n, _, _ in rle) == TRACE_MAX, "RLE cobre exatamente a janela")
    expanded = [(x, y) for n, x, y in rle for _ in range(n)]
    check(expanded[:3] == [(0x10, 0)] * 3 and expanded[3:5] == [(0, 0)] * 2 and expanded[5:7] == [(0, 0x20)] * 2,
          "expansao do RLE confere com o roteiro")
    check(all(1 <= n <= 255 for n, _, _ in rle) and max(n for n, _, _ in compile_script("-:170", "-:170")) <= 255,
          "RLE respeita n<=255")
    try:
        compile_script("-:171", "-:1")
        check(False, "deveria recusar roteiro maior que a janela")
    except ValueError:
        pass
    check(render_script_header([(1, 2, 3)]).strip().endswith("{ 1,2,3,0 };"), "header termina com n=0")
    try:
        stripped = strip_trace_hook_calls(
            '#include "trace_hooks.h"\n'
            'k[0] = TRACE_PAD(0, read_pad(0));\n'
            'k[1] = TRACE_PAD(1, (active ? cpu(1u) : read_pad(1)));\n'
            'TRACE_RECORD();\n')
        check("TRACE_" not in stripped and "active ? cpu(1u) : read_pad(1)" in stripped
              and "((void)0);" in stripped, "baseline expande apenas hooks no-op")
        actual_main = (CANON / "src" / "main.c").read_text(encoding="utf-8")
        actual_baseline = strip_trace_hook_calls(actual_main)
        check("TRACE_PAD(" not in actual_baseline and "TRACE_RECORD(" not in actual_baseline,
              "baseline same-revision sem chamadas restantes")
    except (OSError, ValueError) as exc:
        check(False, f"strip_trace_hook_calls: {exc}")

    def fake(n=TRACE_MAX, done=1, magic=b"TRC1"):
        b = bytearray(magic + bytes([done, n & 255, n >> 8, TRACE_REC]))
        for t in range(n):
            b += bytes([1, t & 255, 2, 96, 232, 0b00001011]) + bytes([0, 0, 0, 152, 0, 0])
        return bytes(b)
    t = decode_buffer(fake())
    check(len(t) == TRACE_MAX and t[5]["p1_frame"] == 5 and t[0]["p1_x"] == 96 and t[0]["p2_x"] == 152,
          "decode: campos")
    check(t[0]["p1_life"] == 232 + 256 * 2 and t[0]["p1_facing"] == 1 and t[0]["p1_hit_done"] == 1,
          "decode: flags e vida de 10 bits")
    for label, buf in (("magic", fake(magic=b"XXXX")), ("nao concluida", fake(done=0)), ("contagem", fake(n=100)),
                       ("curto", b"TRC1"), ("truncado", fake()[:-5])):
        try:
            decode_buffer(buf)
            check(False, f"decode deveria recusar: {label}")
        except ValueError:
            pass
    pb = bytearray(b"TRC2" + bytes([1, TRACE_MAX & 255, 0, TRACE_REC]))
    for i in range(TRACE_MAX):
        pb += bytes([6, i & 255, 1, 3, 0xD1, 0xD9, 0xDC, 0xDF, 40, 0, 10, 0])
    pr = decode_profile(bytes(pb))
    check(len(pr) == TRACE_MAX and pr[7]["vc_sat"] == 0xDC and pr[7]["vc_stream"] == 0xDF and pr[7]["slots_used"] == 40,
          "decode_profile: campos")
    for label, buf in (("magic de estado", fake()), ("incompleto", bytes(pb[:4]) + bytes([0]) + bytes(pb[5:])),
                       ("curto", bytes(pb)[:20])):
        try:
            decode_profile(buf)
            check(False, f"decode_profile deveria recusar: {label}")
        except ValueError:
            pass
    try:
        decode_buffer(bytes(pb))
        check(False, "decode_buffer deveria recusar magic de perfil")
    except ValueError:
        pass
    air_raw = bytearray(b"TRC3" + bytes([1, 1, 0, AIR_TRACE_REC]))
    air_raw.extend([0xDD, 0, 0, 0, 0, 0])
    air_rows = AIR_TRACE.decode_buffer(bytes(air_raw), expect_ticks=1)
    check(air_rows[0]["p1_air_action"] == 221 and air_rows[0]["p1_air_element"] == 0
          and air_rows[0]["p2_air_action"] == 0 and air_rows[0]["p2_air_element"] == 0,
          "decode TRC3 action/element por lutador")
    try:
        runtime_manifest = {"schema": "sms_versus_scene_cut_v1",
                            "source_sha256": {"p1_ryo": "a" * 64, "p2_ryo": "a" * 64}}
        source_identity = {"source": {"package_sha256": "a" * 64}}
        binding = validate_runtime_source_manifest(runtime_manifest, source_identity, "p1")
        cut_actions = validate_runtime_cut_manifest(
            {"source_sha256": "a" * 64,
             "roles": [{"role": "idle", "action": 0}, {"role": "hp", "action": 221}]},
            source_identity)
        action_ids = runtime_action_ids(
            "static const CharacterData characters[2] = {\n"
            "    { ken_anims, ken_states, 1, 0 },\n"
            "    { ryu_anims, ryu_states, 1, 1 },\n};",
            "static const Anim ken_anims[2] = {\n    { 0u, 1u, 0u, 0u },\n"
            "    { 221u, 5u, 255u, 1u },\n};\n"
            "static const Anim ryu_anims[1] = {\n    { 0u, 1u, 0u, 0u },\n};",
            "p1")
        check(binding["slot"] == "p1_ryo" and action_ids == {0, 221}
              and cut_actions == action_ids,
              "preflight vincula pacote, manifest de corte e tabela compilada")
        try:
            validate_runtime_source_manifest(
                {"schema": "sms_versus_scene_cut_v1",
                 "source_sha256": {"p1_ryo": "b" * 64}}, source_identity, "p1")
            check(False, "runtime com pacote diferente deveria falhar")
        except ValueError:
            pass
    except (OSError, ValueError) as exc:
        check(False, f"preflight de identidade de runtime: {exc}")
    try:
        make_clone(Path("/tmp/unused"), profile=True, air_identity=True)
        check(False, "profile e AIR identity nao podem compartilhar schema")
    except ValueError:
        pass
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        w = Path(td)
        for rel in ("inc", "src"):
            (w / rel).mkdir()
        (w / "inc/stream.h").write_text("#define STREAM_SLOTS 128u\n")
        (w / "src/stream.c").write_text("static unsigned char frame_parity;\n    if (frame_parity) { upload(1); upload(0); }\n"
                                        "    else              { upload(0); upload(1); }\n")
        (w / "src/fight.c").write_text("            if (!skip)\n                stream_request(i, req_pt, p->facing, req_pose);\n")
        apply_variant(w, "urgent_first")
        check("stream_urgent[0] != stream_urgent[1]" in (w / "src/stream.c").read_text()
              and "stream_urgent[i] =" in (w / "src/fight.c").read_text(), "variante aplica os trechos")
        try:
            apply_variant(w, "urgent_first")      # 2a vez: trechos antigos ja nao existem (ou duplicariam)
            check(False, "variante reaplicada deveria falhar")
        except SystemExit:
            pass
    try:
        apply_variant(Path("."), "nao_existe")
        check(False, "variante desconhecida deveria falhar")
    except SystemExit:
        pass
    # o juiz de trilhas aceita a saida do decoder
    from mugen2sms.analysis import trace_compare as TC
    check(TC.compare({"s": t}, {"s": decode_buffer(fake())})["equivalent"], "trace_compare aceita trilhas iguais")
    check(not TC.compare({"s": t}, {"s": t[:-3]})["equivalent"], "trace_compare reprova cauda perdida")
    print("self-check luta_mugen_trace_dap:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scenario")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--scratch", type=Path, help="diretorio de trabalho (padrao: out/local_study/trace_work)")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--variant", default="baseline", help=f"experimento isolado: {sorted(VARIANTS)}")
    ap.add_argument("--profile", action="store_true", help="grava VCounter por fase e pool (TRC2) em vez do estado")
    ap.add_argument("--air-source-manifest", type=Path,
                    help="grava TRC3 com action/element por tick e deriva fronteiras auditaveis")
    ap.add_argument("--runtime-source-manifest", type=Path,
                    help="manifesto sms_versus_scene_cut_v1 que vincula pacote-fonte por lado (TRC3)")
    ap.add_argument("--runtime-cut-manifest", type=Path,
                    help="manifesto do corte do lutador selecionado, com ações e source_sha256 (TRC3)")
    ap.add_argument("--air-side", choices=("p1", "p2"), default="p1",
                    help="slot cuja action sera cotejada com o manifesto AIR-fonte")
    ap.add_argument("--check-canonical", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    if a.list:
        for k, (p1, p2) in SCENARIOS.items():
            print(f"{k}: P1 [{p1}]  P2 [{p2}]")
        return 0
    scratch = a.scratch or (PROJECT / "out" / "local_study" / "trace_work")
    scratch.mkdir(parents=True, exist_ok=True)
    if a.check_canonical:
        return check_canonical(scratch)
    if not a.scenario or not a.out:
        ap.error("--scenario e --out obrigatorios (ou --check-canonical / --self-check / --list)")
    return produce(a.scenario, a.out, scratch, a.keep, a.profile, a.variant,
                   a.air_source_manifest, a.air_side, a.runtime_source_manifest,
                   a.runtime_cut_manifest)


if __name__ == "__main__":
    sys.exit(main())
