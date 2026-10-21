#!/usr/bin/env python3
"""audit_silhouette_integrity.py — cobertura de silhueta na composicao O3.

O defeito medido no M8 nao era paleta, canvas nem decode: com o jogador em
a102 (ataque), as linhas 1/2 do jogador ocupavam 7/8 entradas e o inimigo
ficava com zero celulas de cabeca/tronco. Um gate de "imagem legal" aprovava.

Este gate le as tabelas emitidas (nao o PNG, nao a narrativa):
  inc/o3/o3_poses.h   celulas emitidas de cada pose (ordem de prioridade)
  inc/o3/o3_rows.h    contagem do jogador por linha de canvas
e simula a mesma politica de linhas do runtime de forma independente:
  - jogador desenha inteiro; sua contagem por linha e estatica;
  - inimigo e visitado na ordem do array emitido (densidade desc);
  - a linha do inimigo so aceita uma celula se ec + 1 + max(jogador em
    linhas sobrepostas) <= 8;
  - topo < 1 nao desenha; topo >= 192 desenha mas nao conta.

Reprova quando:
  - qualquer pose de ataque tem > --max-attack-upper celulas nas linhas 1/2
    (o cap D9-a3 e o que devolve as scanlines ao inimigo);
  - em qualquer caso ataque x inimigo-de-pe x lado x base x dz, as linhas
    criticas do inimigo (1/2 por padrao) ficam com < --min-enemy-row cada
    ou < --min-enemy-total no total;
  - o corpo do jogador (linhas 1/2/3) fica com < --min-player-row.

Escopo declarado: cobertura de celulas na composicao emitida. NAO julga
anatomia, recorte, estilo, sombra ou qualidade artistica; NAO prova a ROM.
As poses de queda/morte do inimigo ficam fora do veredito (o corpo deitado
tem outra geometria); a regressao/QA visual cobre esse caso a parte.

Uso:
  audit_silhouette_integrity.py --project DIR [--record JSON] [--art JSON]
      [--min-enemy-row 2] [--min-enemy-total 5] [--min-player-row 3]
      [--json SAIDA] [--self-check]
Exit: 0 passa | 1 reprova | 3 uso
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCREEN_H = 192
PER_LINE = 8
ROW_PITCH = 16
ENEMY_STANDING_FRAMES = ("idle01", "walk01", "walk03", "pain01", "pain02")
DEFAULT_ATTACK_FRAMES = ("a101", "a102", "a103", "a104", "a105")
DEFAULT_ENEMY_ROWS = (1, 2)
DEFAULT_PLAYER_ROWS = (1, 2, 3)
DEFAULT_DZ = (-24, -8, 0, 8, 24)
DEFAULT_BASES = (148, 152)

_POSE_RE = re.compile(
    r"const\s+o3_cell\s+o3_(ax|long)_pose(\d+)\[\]\s*=\s*\{(.*?)\};",
    re.S)
_CELL_RE = re.compile(r"\{\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(\d+)\s*\}")
_ROWS_RE = re.compile(
    r"const\s+unsigned\s+char\s+o3_ax_rows\s*\[\s*\d+\s*\]\s*\[\s*\d+\s*\]\s*=\s*\{(.*?)\};",
    re.S)
_DEF_RE = re.compile(r"#define\s+(O3_\w+)\s+([^\s/]+)")
_NUM_RE = re.compile(r"-?\d+")


def _num(token):
    return int(_NUM_RE.search(token).group(0))


def parse_pose_arrays(text):
    """{actor: {pose_index: [{'dx','dy','slot'}]}} a partir do header C."""
    out = {"ax": {}, "long": {}}
    for match in _POSE_RE.finditer(text):
        actor = match.group(1)
        index = int(match.group(2))
        cells = [
            {"dx": int(dx), "dy": int(dy), "slot": int(slot)}
            for dx, dy, slot in _CELL_RE.findall(match.group(3))
        ]
        out[actor][index] = cells
    if not out["ax"] or not out["long"]:
        raise ValueError("o3_poses.h sem arrays ax/long reconheciveis")
    return out


def parse_rows(text):
    """Matriz o3_ax_rows[pose][row] do header C."""
    match = _ROWS_RE.search(text)
    if not match:
        raise ValueError("o3_rows.h sem o3_ax_rows reconhecivel")
    rows = []
    for group in re.findall(r"\{([^{}]+)\}", match.group(1)):
        rows.append([int(x) for x in group.split(",") if x.strip()])
    if not rows:
        raise ValueError("o3_ax_rows vazio")
    return rows


def parse_defines(text):
    out = {}
    for name, raw in _DEF_RE.findall(text):
        try:
            out[name] = _num(raw)
        except (AttributeError, ValueError):
            pass
    return out


def load_frames(path):
    """{actor: [nomes de frame]} na ordem de pose = frame*2 + lado."""
    data = json.loads(Path(path).read_text())
    poses = data.get("poses", {})
    out = {}
    for actor in ("ax", "long"):
        frames = poses.get(actor, {}).get("frames")
        if not isinstance(frames, list) or not frames:
            raise ValueError(f"{path}: poses.{actor}.frames ausente/vazio")
        out[actor] = frames
    return out


def pose_index(frames, frame, side):
    try:
        frame_i = frames.index(frame)
    except ValueError as exc:
        raise ValueError(f"frame '{frame}' nao existe no registro de arte") from exc
    return frame_i * 2 + (0 if side == "left" else 1)


def pose_rows(cells, dy0):
    """Linha de canvas de cada celula; falha se dy nao cair na grade de 16."""
    rows = {}
    for cell in cells:
        delta = cell["dy"] - dy0
        if delta % ROW_PITCH:
            raise ValueError(f"dy {cell['dy']} fora da grade de {ROW_PITCH}px")
        row = delta // ROW_PITCH
        if row < 0:
            raise ValueError(f"dy {cell['dy']} acima do canvas")
        rows[row] = rows.get(row, 0) + 1
    return rows


def _overlap_rows(row, player_rows, dy0p, dy0e, base_p, base_e):
    """Linhas do jogador que dividem scanlines visiveis com a linha do inimigo."""
    if not 0 <= row <= (SCREEN_H // ROW_PITCH):
        return []
    e0 = base_e + dy0e + ROW_PITCH * row
    if e0 < 1 or e0 > SCREEN_H - 1:
        return []
    out = []
    for rp, count in player_rows.items():
        if count <= 0:
            continue
        p0 = base_p + dy0p + ROW_PITCH * rp
        if p0 < 1:
            continue
        if min(SCREEN_H - 1, e0 + 15, p0 + 15) >= max(1, e0, p0):
            out.append(rp)
    return out


def kept_enemy(player_rows, enemy_cells, dy0p, dy0e, base_p, base_e,
               limit=PER_LINE):
    """Simulacao independente: quantas celulas do inimigo sobrevivem por linha.

    Usa a ordem do array emitido (a mesma da SAT), sem chamar o gerador.
    Retorna ({row: kept}, [drops]).
    """
    ec = {}
    drops = []
    for order, cell in enumerate(enemy_cells):
        delta = cell["dy"] - dy0e
        if delta % ROW_PITCH:
            raise ValueError(f"celula inimiga com dy {cell['dy']} fora da grade")
        row = delta // ROW_PITCH
        y0 = base_e + dy0e + ROW_PITCH * row
        if y0 < 1:
            continue
        if y0 < SCREEN_H:
            overlap = _overlap_rows(row, player_rows, dy0p, dy0e,
                                    base_p, base_e)
            m = max((player_rows[r] for r in overlap), default=0)
            if ec.get(row, 0) + 1 + m > limit:
                drops.append({"order": order, "row": row,
                              "dx": cell["dx"], "dy": cell["dy"]})
                continue
        ec[row] = ec.get(row, 0) + 1
    return ec, drops


def worst_cases(ec, source_rows, critical):
    """Metricas do caso: contagens nas linhas criticas e fonte por linha."""
    counts = [ec.get(r, 0) for r in critical]
    source = [source_rows.get(r, 0) for r in critical]
    return {
        "critical_rows": list(critical),
        "kept": counts,
        "source": source,
        "total": sum(counts),
        "min_row": min(counts) if counts else 0,
    }


def evaluate(poses, rows, frames, attack_frames, row_cap,
             min_enemy_row, min_enemy_total, min_player_row,
             enemy_rows, player_rows, bases, dz_values,
             dy0p, dy0e, limit=PER_LINE,
             enemy_frames=ENEMY_STANDING_FRAMES):
    """Roda o matrix ataque x inimigo de pe; devolve o relatorio."""
    failures = []
    cases = 0
    worst = None
    min_row_seen = None
    min_total_seen = None
    attack_upper = []

    # 1) cap do ataque (D9-a3) e corpo do jogador (linhas 1/2/3)
    for frame in attack_frames:
        for side in ("left", "right"):
            pi = pose_index(frames["ax"], frame, side)
            if pi < 0 or pi >= len(rows):
                failures.append({
                    "kind": "missing_player_rows", "frame": frame,
                    "side": side, "pose": pi})
                continue
            row_values = rows[pi]
            upper = max(row_values[1] if len(row_values) > 1 else 0,
                        row_values[2] if len(row_values) > 2 else 0)
            attack_upper.append({"frame": frame, "side": side,
                                 "upper_rows_1_2": upper,
                                 "rows": row_values})
            if upper > row_cap:
                failures.append({"kind": "attack_upper_over_cap",
                                 "frame": frame, "side": side,
                                 "upper_rows_1_2": upper, "cap": row_cap})
            body = [row_values[r] if len(row_values) > r else 0
                    for r in player_rows]
            if min(body) < min_player_row:
                failures.append({"kind": "player_body_thin",
                                 "frame": frame, "side": side,
                                 "rows": dict(zip(player_rows, body)),
                                 "min": min(body),
                                 "required": min_player_row})

    # 2) matrix de composicao
    for pframe in attack_frames:
        for pside in ("left", "right"):
            pi = pose_index(frames["ax"], pframe, pside)
            player_counts = {r: rows[pi][r] for r in range(len(rows[pi]))
                             if rows[pi][r] > 0}
            for eframe in enemy_frames:
                for eside in ("left", "right"):
                    ei = pose_index(frames["long"], eframe, eside)
                    enemy_cells = poses["long"].get(ei)
                    if enemy_cells is None:
                        failures.append({"kind": "missing_enemy_pose",
                                         "frame": eframe, "side": eside,
                                         "pose": ei})
                        continue
                    source_rows = pose_rows(enemy_cells, dy0e)
                    for base_p in bases:
                        for dz in dz_values:
                            base_e = base_p + dz
                            ec, drops = kept_enemy(
                                player_counts, enemy_cells, dy0p, dy0e,
                                base_p, base_e, limit)
                            metric = worst_cases(ec, source_rows, enemy_rows)
                            cases += 1
                            if min_row_seen is None or metric["min_row"] < min_row_seen:
                                min_row_seen = metric["min_row"]
                            if min_total_seen is None or metric["total"] < min_total_seen:
                                min_total_seen = metric["total"]
                            key = (metric["total"], metric["min_row"],
                                   sum(metric["kept"]))
                            if worst is None or key < worst[0]:
                                worst = (key, {
                                    "player": {"frame": pframe, "side": pside,
                                               "pose": pi,
                                               "rows": player_counts},
                                    "enemy": {"frame": eframe, "side": eside,
                                              "pose": ei,
                                              "source_rows": source_rows},
                                    "base_player": base_p,
                                    "base_enemy": base_e,
                                    "dz": dz,
                                    "ec": {str(k): v for k, v in sorted(ec.items())},
                                    "drops": len(drops),
                                    "metric": metric,
                                })
                            if (metric["min_row"] < min_enemy_row
                                    or metric["total"] < min_enemy_total):
                                if len(failures) < 40:
                                    failures.append({
                                        "kind": "enemy_silhouette_thin",
                                        "player": {"frame": pframe,
                                                   "side": pside,
                                                   "pose": pi},
                                        "enemy": {"frame": eframe,
                                                  "side": eside,
                                                  "pose": ei},
                                        "base_player": base_p,
                                        "base_enemy": base_e,
                                        "dz": dz,
                                        "ec": {str(k): v for k, v in sorted(ec.items())},
                                        "kept": metric["kept"],
                                        "source": metric["source"],
                                        "total": metric["total"],
                                        "min_row": metric["min_row"],
                                        "required_row": min_enemy_row,
                                        "required_total": min_enemy_total,
                                    })

    report = {
        "schema": "o3_silhouette_integrity_v1",
        "scope": "cobertura de celulas emitidas; nao julga arte nem prova ROM",
        "screen_h": SCREEN_H,
        "limit_per_line": limit,
        "attack_frames": list(attack_frames),
        "enemy_standing_frames": list(ENEMY_STANDING_FRAMES),
        "enemy_critical_rows": list(enemy_rows),
        "player_critical_rows": list(player_rows),
        "attack_upper_cap": row_cap,
        "attack_upper_max": max((a["upper_rows_1_2"] for a in attack_upper),
                                default=0),
        "attack_upper": attack_upper,
        "bases": list(bases),
        "dz_values": list(dz_values),
        "cases": cases,
        "min_enemy_row": min_row_seen,
        "min_enemy_total": min_total_seen,
        "requirements": {"enemy_row": min_enemy_row,
                         "enemy_total": min_enemy_total,
                         "player_row": min_player_row},
        "worst": None if worst is None else worst[1],
        "failures": failures,
        "ok": not failures,
        "note": ("poses de queda/morte do inimigo ficam fora do veredito; "
                 "regressao/QA visual cobre a geometria deitada"),
    }
    return report


def _locate(project, record, art):
    project = Path(project)
    if record:
        record_path = Path(record)
    else:
        candidates = sorted((project / "data/generated/emit").glob(
            "o3_emission_*.json"))
        if not candidates:
            raise FileNotFoundError("nenhum o3_emission_*.json no projeto")
        record_path = candidates[-1]
    rec = json.loads(record_path.read_text())
    if art:
        art_path = Path(art)
    else:
        candidates = sorted((project / "data/generated/art").glob(
            "o3_art_conversion_*.json"))
        if not candidates:
            raise FileNotFoundError("nenhum o3_art_conversion_*.json no projeto")
        art_path = candidates[-1]
    return record_path, rec, art_path


def run(project, record, art, min_enemy_row, min_enemy_total,
        min_player_row, max_attack_upper, enemy_rows, player_rows,
        bases, dz_values):
    project = Path(project)
    record_path, rec, art_path = _locate(project, record, art)
    poses_text = (project / "inc/o3/o3_poses.h").read_text()
    rows_text = (project / "inc/o3/o3_rows.h").read_text()
    poses = parse_pose_arrays(poses_text)
    rows = parse_rows(rows_text)
    defines = parse_defines(rows_text)
    dy0p = defines.get("O3_DY0P", -80)
    dy0e = defines.get("O3_DY0E", -72)
    pitch = defines.get("O3_ROW_PITCH", ROW_PITCH)
    if pitch != ROW_PITCH:
        raise ValueError(f"O3_ROW_PITCH {pitch} != {ROW_PITCH}")
    frames = load_frames(art_path)
    trim = rec.get("ax_attack_trim", {}) if isinstance(rec, dict) else {}
    attack_frames = tuple(trim.get("frames") or DEFAULT_ATTACK_FRAMES)
    row_cap = int(trim.get("row_cap", 5))
    if max_attack_upper is not None:
        row_cap = int(max_attack_upper)
    report = evaluate(
        poses, rows, frames, attack_frames, row_cap,
        min_enemy_row, min_enemy_total, min_player_row,
        tuple(enemy_rows), tuple(player_rows), tuple(bases),
        tuple(dz_values), dy0p, dy0e)
    report["record"] = str(record_path)
    report["art"] = str(art_path)
    report["record_generated_at"] = rec.get("generated_at")
    return report


def self_check():
    """Prova o detector: cap8 derruba a cabeca; cap5 preserva; parser le C."""
    sample_poses = (
        "const o3_cell o3_ax_pose00[] = {{-8,-80,0},{0,-64,1}};\n"
        "const o3_cell o3_long_pose00[] = {{-8,-56,0},{0,-56,1}};\n")
    poses = parse_pose_arrays(sample_poses)
    assert poses["ax"][0][0] == {"dx": -8, "dy": -80, "slot": 0}
    assert poses["long"][0][1]["dy"] == -56
    sample_rows = ("const unsigned char o3_ax_rows[2][6] = "
                   "{{0,7,8,4,6,4},{0,5,5,4,6,4}};")
    rows = parse_rows(sample_rows)
    assert rows[0] == [0, 7, 8, 4, 6, 4]
    assert rows[1] == [0, 5, 5, 4, 6, 4]
    defines = parse_defines("#define O3_DY0P (-80)\n#define O3_DY0E (-72)\n")
    assert defines == {"O3_DY0P": -80, "O3_DY0E": -72}

    # 5 celulas em cada linha critica, jogador enchendo 8/8 -> zero sobra.
    enemy = ([{"dy": -56, "dx": -16 + 8 * i, "slot": i} for i in range(5)]
             + [{"dy": -40, "dx": -16 + 8 * i, "slot": 5 + i}
                for i in range(5)])
    ec8, _ = kept_enemy({1: 8, 2: 8}, enemy, -80, -72, 152, 152)
    assert ec8.get(1, 0) == 0 and ec8.get(2, 0) == 0, ec8
    ec5, _ = kept_enemy({1: 5, 2: 5}, enemy, -80, -72, 152, 152)
    assert ec5.get(1, 0) == 3 and ec5.get(2, 0) == 3, ec5
    # linha 2 com 2 celulas: total 5, ainda leitura minima
    enemy2 = enemy[:5] + [{"dy": -40, "dx": 0, "slot": 5},
                          {"dy": -40, "dx": 8, "slot": 6}]
    ec2, _ = kept_enemy({1: 5, 2: 5}, enemy2, -80, -72, 152, 152)
    assert ec2.get(1, 0) == 3 and ec2.get(2, 0) == 2, ec2
    # linha 2 com 1 celula: total 4, reprova o piso
    enemy1 = enemy[:5] + [{"dy": -40, "dx": 0, "slot": 5}]
    ec1, _ = kept_enemy({1: 5, 2: 5}, enemy1, -80, -72, 152, 152)
    assert ec1.get(1, 0) == 3 and ec1.get(2, 0) == 1, ec1

    # cap: linhas 1/2 acima de 5 reprovam; 5/5 passam
    assert max(rows[0][1], rows[0][2]) > 5
    assert max(rows[1][1], rows[1][2]) <= 5

    # evaluate sintetico: cap8 falha; cap5 passa (com inimigo de 5/5)
    frames = {"ax": ["a101"], "long": ["walk01"]}
    synth = {"ax": {0: [{"dx": -8, "dy": -80, "slot": 0}],
                    1: [{"dx": 0, "dy": -80, "slot": 0}]},
             "long": {0: enemy, 1: enemy}}
    bad_rows = [[0, 7, 8, 4, 6, 4], [0, 7, 8, 4, 6, 4]]
    good_rows = [[0, 5, 5, 4, 6, 4], [0, 5, 5, 4, 6, 4]]
    bad = evaluate(synth, bad_rows, frames, ("a101",), 5,
                   2, 5, 3, (1, 2), (1, 2, 3), (152,), (0,), -80, -72,
                   enemy_frames=("walk01",))
    assert not bad["ok"] and bad["min_enemy_row"] == 0, bad["min_enemy_row"]
    good = evaluate(synth, good_rows, frames, ("a101",), 5,
                    2, 5, 3, (1, 2), (1, 2, 3), (152,), (0,), -80, -72,
                    enemy_frames=("walk01",))
    assert good["ok"], good["failures"]
    print("[SELF-CHECK OK] audit_silhouette_integrity "
          "(cap8 zera cabeca; cap5 preserva; parser C e piso 2/5)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default=".")
    ap.add_argument("--record")
    ap.add_argument("--art")
    ap.add_argument("--min-enemy-row", type=int, default=2)
    ap.add_argument("--min-enemy-total", type=int, default=5)
    ap.add_argument("--min-player-row", type=int, default=3)
    ap.add_argument("--max-attack-upper", type=int)
    ap.add_argument("--enemy-rows", default="1,2")
    ap.add_argument("--player-rows", default="1,2,3")
    ap.add_argument("--bases", default="148,152")
    ap.add_argument("--dz", default="-24,-8,0,8,24")
    ap.add_argument("--json")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args(argv)
    if args.self_check:
        return self_check()
    try:
        report = run(
            args.project, args.record, args.art,
            args.min_enemy_row, args.min_enemy_total, args.min_player_row,
            args.max_attack_upper,
            [int(x) for x in args.enemy_rows.split(",") if x.strip()],
            [int(x) for x in args.player_rows.split(",") if x.strip()],
            [int(x) for x in args.bases.split(",") if x.strip()],
            [int(x) for x in args.dz.split(",") if x.strip()])
    except (OSError, ValueError, KeyError) as exc:
        print(f"[FAIL] silhueta: {exc}")
        return 1
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2))
    if report["ok"]:
        print(f"[PASS] silhueta: {report['cases']} casos; "
              f"inimigo min linha={report['min_enemy_row']} "
              f"total={report['min_enemy_total']} "
              f"(piso {report['requirements']['enemy_row']}/"
              f"{report['requirements']['enemy_total']}); "
              f"jogador min={report['requirements']['player_row']}; "
              f"ataque max linhas 1/2={report['attack_upper_max']}/"
              f"{report['attack_upper_cap']}")
        return 0
    for failure in report["failures"][:8]:
        print(f"[FAIL] {failure}")
    print(f"[FAIL] silhueta: {len(report['failures'])} falha(s); "
          f"min inimigo={report['min_enemy_row']}/"
          f"{report['min_enemy_total']}; "
          f"ataque max={report['attack_upper_max']}/"
          f"{report['attack_upper_cap']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
