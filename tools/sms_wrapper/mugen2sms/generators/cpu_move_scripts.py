"""Compile supported MUGEN commands into deterministic CPU input scripts.

The output samples use the same relative input levels returned by
``cpu_controller_step``. They do not select a state or bypass the runtime
command ring: a game build must still generate the matching ``_CMD_`` blob and
state adapter from the same source package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mugen2sms import character as character_loader                         # noqa: E402
from mugen2sms.converters import sms_cmd                                    # noqa: E402
from mugen2sms.converters.sms_controls import ControlMap, DEFAULT_MAP       # noqa: E402
from mugen2sms.generators.smsdev import slug                                # noqa: E402
from mugen2sms.inventory import sha256_file                                 # noqa: E402
from mugen2sms.parsers import cmd as cmdmod                                 # noqa: E402
from mugen2sms.source import Source                                         # noqa: E402

INPUT_KEY_1 = 0x10
INPUT_KEY_2 = 0x20
INPUT_BUFFER = 16
DEFAULT_TIER_TICKS = 6

DIR_TO_CPU = {"U": 0x08, "D": 0x04, "B": 0x02, "F": 0x01,
              "DF": 0x05, "DB": 0x06, "UF": 0x09, "UB": 0x0A}


def compile_command(command: cmdmod.Command, controls: ControlMap = DEFAULT_MAP,
                    tier_ticks: int = DEFAULT_TIER_TICKS,
                    sample_limit: int = INPUT_BUFFER) -> tuple[list[int] | None, str | None]:
    """Return pad-level samples or a reason the current runtime cannot play it.

    One sample is a ROM tick. Weak buttons use press/release; strong buttons
    stay down until the configured threshold pulse. Explicit release steps get
    a release edge, and a final weak release gets one settling tick so the
    runtime's pulse-consumption rule can observe the release condition.
    """
    patterns, skipped = sms_cmd.to_patterns([command], controls)
    if skipped:
        return None, next(iter(skipped.values()))
    if len(patterns) != 1 or len(patterns[0].steps) != len(command.steps):
        return None, "cmd-sem-mapeamento-unico-de-passos"

    samples: list[int] = []
    timed_release_anchor: int | None = None
    carry = 0
    for source_step, code in zip(command.steps, patterns[0].steps):
        if source_step.strict:
            return None, "strict-step-nao-suportado-no-runtime"
        if any(key.hold and key.release for key in source_step.keys):
            return None, "hold-e-release-no-mesmo-token"

        # Convert the converter's F/B/U/D nibble. Diagonals are already ORed.
        # For `$D`/`$F`, the CPU chooses the exact cardinal direction here;
        # the paired blob accepts the neighboring diagonals as well.
        directions = ((0x08 if code.dir & 0x01 else 0) |
                      (0x04 if code.dir & 0x02 else 0) |
                      (0x02 if code.dir & 0x04 else 0) |
                      (0x01 if code.dir & 0x08 else 0))
        keys = ((INPUT_KEY_1 if code.keys & 0x01 else 0) |
                (INPUT_KEY_2 if code.keys & 0x02 else 0))
        current = directions | keys | carry

        if keys:
            if code.tier == 1:
                if any(key.hold and key.key not in sms_cmd.DIR_BITS and
                       key.key not in sms_cmd.DIAGONALS for key in source_step.keys):
                    return None, "hold-de-botao-fraco-nao-representavel"
                duration = 1
            elif code.tier == 2:
                physicals = [str(index + 1) for index in range(2)
                             if code.keys & (1 << index)]
                thresholds = []
                for physical in physicals:
                    family_thresholds = controls.thresholds.get(physical, [])
                    if not family_thresholds:
                        return None, "limiar-forte-ausente-no-mapa"
                    thresholds.append(family_thresholds[0])
                if any(value != tier_ticks for value in thresholds):
                    return None, "limiar-forte-diverge-do-runtime"
                if thresholds and len(set(thresholds)) != 1:
                    return None, "acorde-com-limiares-diferentes"
                duration = tier_ticks
            else:
                return None, "tier-sem-implementacao-no-runtime"
        else:
            duration = 1
        if code.rel_time:
            duration = max(duration, code.rel_time)

        samples.extend([current] * duration)
        release_mask = 0
        for key in source_step.keys:
            if not key.release:
                continue
            if key.key in sms_cmd.DIR_BITS:
                release_mask |= DIR_TO_CPU.get(key.key, 0)
            elif key.key in sms_cmd.DIAGONALS:
                release_mask |= DIR_TO_CPU[key.key]
            else:
                physical, _tier = controls.locate(key.key) or (None, None)
                release_mask |= INPUT_KEY_1 if physical == "1" else INPUT_KEY_2

        # A weak event is emitted on the first sample without the key. This
        # also supplies an ordinary next-step transition when the command has
        # no explicit release modifier.
        if keys and code.tier == 1:
            samples.append(current & ~keys)
        elif release_mask:
            samples.append(current & ~release_mask)
            if code.rel_time:
                timed_release_anchor = len(samples) - 1

        if release_mask and keys and code.tier == 1:
            # At the weak pulse tick, release and tier both match. The input
            # matcher accepts the explicit release on the following neutral
            # tick, after the pulse has expired.
            samples.append((current & ~keys) & ~release_mask)

        held = 0
        for key in source_step.keys:
            if not key.hold:
                continue
            if key.key in sms_cmd.DIR_BITS:
                held |= DIR_TO_CPU.get(key.key, 0)
            elif key.key in sms_cmd.DIAGONALS:
                held |= DIR_TO_CPU[key.key]
            else:
                physical, _tier = controls.locate(key.key) or (None, None)
                held |= INPUT_KEY_1 if physical == "1" else INPUT_KEY_2
        carry = held

        if len(samples) > 0xFF:
            return None, "script-maior-que-255-amostras"

        if code.rel_time and not release_mask:
            return None, "release-time-sem-evento-de-soltura"

    if not samples:
        return None, "cmd-vazio"
    # A one-step button command has no inter-step interval: a six-tick strong
    # press still matches at its final tier pulse even when MUGEN's sequence
    # window is one tick. For multi-step commands, reject scripts whose
    # generated spacing cannot fit that window.
    timed_anchors = [index for index, source_step in enumerate(command.steps)
                     if any(key.release_time for key in source_step.keys)]
    if timed_anchors:
        # Charge time is counted by the runtime's held-direction counter, not
        # by its 16-sample sequence window. The window starts at the release
        # event, as prior samples may have been overwritten during the charge.
        if timed_release_anchor is None:
            return None, "release-time-sem-evento-de-soltura"
        suffix_span = len(samples) - 1 - timed_release_anchor
        if suffix_span >= sample_limit:
            return None, f"script-maior-que-anel-{sample_limit}"
        if len(command.steps) > 1 and suffix_span > command.time:
            return None, "script-excede-janela-time-do-cmd"
    else:
        if len(samples) > sample_limit:
            return None, f"script-maior-que-anel-{sample_limit}"
        if len(command.steps) > 1 and len(samples) - 1 > command.time:
            return None, "script-excede-janela-time-do-cmd"
    return samples, None


def serialize_command_pattern(command: cmdmod.Command,
                              controls: ControlMap = DEFAULT_MAP
                              ) -> tuple[bytes | None, str | None]:
    """Serialize the exact input-ring matcher paired with a CPU script."""
    patterns, skipped = sms_cmd.to_patterns([command], controls)
    if skipped:
        return None, next(iter(skipped.values()))
    if len(patterns) != 1 or len(patterns[0].steps) != len(command.steps):
        return None, "cmd-sem-mapeamento-unico-de-passos"
    return sms_cmd.serialize_pattern(patterns[0]), None


def compile_catalog(source: Path, move_report: Path,
                    controls: ControlMap = DEFAULT_MAP,
                    tier_ticks: int = DEFAULT_TIER_TICKS,
                    sample_limit: int = INPUT_BUFFER) -> tuple[str, dict]:
    character = character_loader.load(Source(source))
    report = json.loads(move_report.read_text(encoding="utf-8"))
    by_name: dict[str, list[tuple[int, cmdmod.Command]]] = {}
    for index, command in enumerate(character.commands):
        by_name.setdefault(command.name.casefold(), []).append((index, command))

    prefix = slug(Path(character.def_path).stem)
    included: list[dict] = []
    excluded: list[dict] = []
    for row_index, row in enumerate(report):
        if row.get("status") in ("DROPPED", "BLOCKED"):
            excluded.append({"row": row_index, "target": row.get("target"),
                             "commands": row.get("commands", []),
                             "reason": "analysis-" + str(row.get("status")).lower()})
            continue
        names = row.get("commands", [])
        if len(names) != 1:
            excluded.append({"row": row_index, "target": row.get("target"),
                             "commands": names,
                             "reason": "compound-or-alternative-triggers-need-cns-resolution"})
            continue
        target = int(row["target"])
        state = character.states.get(target)
        if state is None:
            excluded.append({"row": row_index, "target": target,
                             "reason": "target-state-missing-from-ir"})
            continue
        state_type = chr(state.statetype)
        if state_type not in ("S", "A"):
            excluded.append({"row": row_index, "target": target,
                             "state_type": state_type,
                             "reason": "state-type-not-observable-by-current-cpu"})
            continue
        for name in row.get("commands", []):
            matches = by_name.get(str(name).casefold(), [])
            if len(matches) != 1:
                excluded.append({"row": row_index, "target": row.get("target"),
                                 "command": name,
                                 "reason": "command-name-" +
                                 ("ausente" if not matches else "ambiguo")})
                continue
            command_index, command = matches[0]
            samples, reason = compile_command(command, controls, tier_ticks,
                                              sample_limit)
            if reason:
                excluded.append({"row": row_index, "target": row.get("target"),
                                 "command": command.name, "raw": command.raw,
                                 "reason": reason})
                continue
            pattern_blob, pattern_reason = serialize_command_pattern(command, controls)
            if pattern_reason or pattern_blob is None:
                excluded.append({"row": row_index, "target": target,
                                 "command": command.name,
                                 "reason": pattern_reason or "runtime-pattern-ausente"})
                continue
            included.append({"row": row_index, "target": target,
                             "command_index": command_index,
                             "command": command.name, "raw": command.raw,
                             "analysis_status": row.get("status"),
                             "state_type": state_type,
                             "move_flags": 0x08 if state_type == "A" else 0,
                             "samples": samples,
                             "pattern_blob": list(pattern_blob)})

    lines = [f"#ifndef {prefix}_CPU_MOVE_SCRIPTS_H",
             f"#define {prefix}_CPU_MOVE_SCRIPTS_H", "",
             "/* Gerado por mugen2sms.generators.cpu_move_scripts. */",
             "/* Scripts em niveis relativos; nao selecionam estado nem ignoram _CMD_. */", ""]
    for index, entry in enumerate(included):
        sym = f"{prefix}_CPU_SCRIPT_{index}"
        vals = ", ".join(f"0x{sample:02X}" for sample in entry["samples"])
        pattern_vals = ", ".join(
            f"0x{value:02X}" for value in entry["pattern_blob"])
        lines.extend([f"#define {sym}_STATE {entry['target']}u",
                      f"#define {sym}_COMMAND_INDEX {entry['command_index']}u",
                      f"#define {sym}_FLAGS 0x{entry['move_flags']:02X}u",
                      f"#define {sym}_SAMPLE_COUNT {len(entry['samples'])}u",
                      f"#define {sym}_PATTERN_SIZE {len(entry['pattern_blob'])}u",
                      f"static const unsigned char {sym}_SAMPLES[{len(entry['samples'])}] = {{ {vals} }};",
                      f"static const unsigned char {sym}_PATTERN[{len(entry['pattern_blob'])}] = {{ {pattern_vals} }};",
                      ""])
    script_type = f"{prefix}CpuScript"
    lines.extend(["typedef struct {",
                  "    unsigned short target_state;",
                  "    unsigned char command_index;",
                  "    unsigned char state_type;",
                  "    unsigned char flags;",
                  "    unsigned char sample_count;",
                  "    const unsigned char *samples;",
                  "    unsigned char pattern_size;",
                  "    const unsigned char *pattern;",
                  f"}} {script_type};", "",
                  f"#define {prefix}_CPU_SCRIPT_COUNT {len(included)}u",
                  f"static const {script_type} {prefix}_CPU_SCRIPTS["
                  f"{max(1, len(included))}] = {{"])
    for index, entry in enumerate(included):
        sym = f"{prefix}_CPU_SCRIPT_{index}"
        lines.append(
            f"    {{{sym}_STATE, {sym}_COMMAND_INDEX, '{entry['state_type']}', "
            f"{sym}_FLAGS, {sym}_SAMPLE_COUNT, {sym}_SAMPLES, "
            f"{sym}_PATTERN_SIZE, {sym}_PATTERN}},")
    if not included:
        lines.append("    {0u, 0u, 0u, 0u, 0u, 0, 0u, 0},")
    lines.extend(["};", "",
                  f"#endif /* {prefix}_CPU_MOVE_SCRIPTS_H */", ""])
    output = "\n".join(lines)
    machine_report = {
        "schema": "cpu_move_scripts_v1",
        "generated_by": "tools/sms_wrapper/mugen2sms/generators/cpu_move_scripts.py",
        "source": str(source),
        "source_sha256": sha256_file(source),
        "move_report": str(move_report),
        "move_report_sha256": hashlib.sha256(move_report.read_bytes()).hexdigest(),
        "control_map": {"families": controls.families,
                        "thresholds": controls.thresholds,
                        "policy": controls.policy},
        "tier_ticks": tier_ticks,
        "sample_limit": sample_limit,
        "included": included,
        "excluded": excluded,
        "counts": {"included": len(included), "excluded": len(excluded)},
        "header_sha256": hashlib.sha256(output.encode("ascii")).hexdigest(),
    }
    return output, machine_report


def _command(name: str, text: str, time: int = 15) -> cmdmod.Command:
    steps, errors = cmdmod.parse_command_string(text)
    return cmdmod.Command(name, steps, time, 1, 1, text, errors)


def self_check() -> int:
    weak, weak_reason = compile_command(_command("lp", "a"))
    strong, strong_reason = compile_command(_command("hp", "c", time=1))
    qcf, qcf_reason = compile_command(_command("wave", "~D, DF, F, x"))
    four_way, four_way_reason = compile_command(_command("charge", "/$D, DF, x"))
    charge_time, charge_time_reason = compile_command(
        _command("rising", "~15$D, U, x", time=10))
    strict, strict_reason = compile_command(_command("strict", ">D, DF, F, x"))
    ok = (
        weak_reason is None and weak == [INPUT_KEY_1, 0]
        and strong_reason is None and strong == [INPUT_KEY_1] * DEFAULT_TIER_TICKS
        and qcf_reason is None
        and qcf == [0x04, 0, 0x05, 0x01, INPUT_KEY_2, 0]
        and serialize_command_pattern(_command("wave", "~D, DF, F, x"))[0]
        == bytes((sms_cmd.BLOB_FMT_VERSION, 4, 15, 1,
                  0x02, 0x02, 0, 0x0A, 0x00, 0,
                  0x08, 0x00, 0, 0x20, 0x04, 0))
        and four_way is not None and four_way_reason is None
        and charge_time == [0x04] * 15 + [0, 0x08, INPUT_KEY_2, 0]
        and charge_time_reason is None
        and strict is None and strict_reason == "strict-step-nao-suportado-no-runtime"
    )
    print("self-check cpu_move_scripts:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path)
    parser.add_argument("--moves", type=Path)
    parser.add_argument("--out-header", type=Path)
    parser.add_argument("--out-report", type=Path)
    parser.add_argument("--controls", type=Path)
    parser.add_argument("--tier-ticks", type=int, default=DEFAULT_TIER_TICKS)
    parser.add_argument("--sample-limit", type=int, default=INPUT_BUFFER)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    required = (args.source, args.moves, args.out_header, args.out_report)
    if any(item is None for item in required):
        parser.error("--source/--moves/--out-header/--out-report são obrigatórios")
    controls = DEFAULT_MAP if not args.controls else ControlMap.from_json(
        args.controls.read_text(encoding="utf-8"))
    errors = controls.validate()
    if errors:
        parser.error("mapa de controles inválido: " + "; ".join(errors))
    header, report = compile_catalog(args.source, args.moves, controls,
                                    args.tier_ticks, args.sample_limit)
    args.out_header.parent.mkdir(parents=True, exist_ok=True)
    args.out_report.parent.mkdir(parents=True, exist_ok=True)
    args.out_header.write_text(header, encoding="ascii")
    args.out_report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")
    print(f"[CPU CMD] {report['counts']['included']} scripts; "
          f"{report['counts']['excluded']} excluídos; {args.out_header}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
