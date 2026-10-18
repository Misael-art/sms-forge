"""Cabeçalho de padrões de comando (`P<slot>_CMD_<alias>`) para o runtime.

O anel temporal (`integrada/src/input.c`) lê o blob `_CMD_` versionado com
tier; este gerador é a única fonte desses bytes na ROM. Ele lê os `.cmd`
reais dos dois personagens pelos conversores do pipeline (`converters/sms_cmd`
+ mapa do GDD em `converters/sms_controls`) e publica nomes estáveis por
SLOT, não por personagem — assim trocar de elenco não muda uma linha de
`fight.c`, e o C nunca depende do prefixo de um `.def`.

Não regenera arte: o header de cena congelado da ROM fica intocado (doc/23 §2).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mugen2sms import character as character_loader                         # noqa: E402
from mugen2sms.converters import sms_cmd                                    # noqa: E402
from mugen2sms.converters.sms_controls import ControlMap, DEFAULT_MAP       # noqa: E402
from mugen2sms.generators import smsdev                                     # noqa: E402
from mugen2sms.inventory import sha256_file                                 # noqa: E402
from mugen2sms.parsers import cmd as cmdmod                                 # noqa: E402
from mugen2sms.source import Source                                         # noqa: E402

# Os nove movimentos de doc/23 §6.B exigem quatro golpes; sem os quatro alias
# não há contrato de input, então alias ausente é erro — nunca pose ausente.
REQUIRED_ALIASES = ("LP", "HP", "LK", "HK")
BLOB_FMT_VERSION = sms_cmd.BLOB_FMT_VERSION


def _norm(name: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "_", name).upper()


def resolve_aliases(config: dict, by_name: dict[str, bytes], skipped: dict[str, str],
                    config_name: str) -> dict[str, bytes]:
    """{ALIAS -> bytes} dos comandos declarados em `config["commands"]`."""
    out: dict[str, bytes] = {}
    for alias, requested in config.get("commands", {}).items():
        blob = by_name.get(_norm(requested))
        if blob is None:
            reason = skipped.get(requested) or skipped.get(requested.lower())
            detail = f"nao representavel ({reason})" if reason else "inexistente no .cmd"
            raise ValueError(f"alias {alias}: comando {requested!r} e {detail} "
                             f"({config_name})")
        out[_norm(alias)] = blob
    missing = [a for a in REQUIRED_ALIASES if a not in out]
    if missing:
        raise ValueError(f"alias obrigatorio ausente em {config_name}: "
                         + ", ".join(missing))
    return out


def control_map(config: dict) -> ControlMap:
    """Sem declaracao vale o mapa do GDD (doc/22) — mesma regra de scene_cut."""
    declared = config.get("controls")
    return DEFAULT_MAP if not declared else ControlMap.from_dict(declared)


def patterns_for(source: Path, config_path: Path) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    controls = control_map(config)
    ch = character_loader.load(Source(source))
    patterns, skipped = sms_cmd.to_patterns(ch.commands, controls)
    by_name = {_norm(p.name): sms_cmd.serialize_pattern(p) for p in patterns}
    return {
        "slug": smsdev.slug(Path(ch.def_path).stem),
        "def_path": ch.def_path,
        "aliases": {_norm(a): requested
                    for a, requested in config.get("commands", {}).items()},
        "commands_parseados": len(ch.commands),
        "commands_pulados": {k: skipped[k] for k in sorted(skipped)},
        "control_map": {"families": controls.families,
                        "thresholds": controls.thresholds,
                        "policy": controls.policy,
                        "dropped": list(controls.dropped),
                        "declarado_no_config": bool(config.get("controls"))},
        "patterns": resolve_aliases(config, by_name, skipped, config_path.name),
    }


def generate(p1_source: Path, p1_config: Path,
             p2_source: Path, p2_config: Path) -> tuple[str, dict]:
    artifacts: list[smsdev.Artifact] = []
    per_slot: dict[str, dict] = {}
    for index, (source, config) in enumerate(((p1_source, p1_config),
                                              (p2_source, p2_config))):
        slot = f"p{index + 1}"
        info = patterns_for(Path(source), Path(config))
        per_slot[slot] = info
        for alias, data in info["patterns"].items():
            if alias not in REQUIRED_ALIASES:
                continue        # alias de arte (button1/FF) nao e lido pelo anel
            artifacts.append(smsdev.Artifact(f"P{index}_CMD_{alias}", data, "cmd"))
    header = smsdev.render_header(artifacts, "ATTACK_CMDS")
    report = {
        "schema": "attack_cmds_v1",
        "generated_by": "tools/sms_wrapper/mugen2sms/generators/cmd_patterns.py",
        "blob_fmt_version": BLOB_FMT_VERSION,
        "sources": {"p1": str(p1_source), "p2": str(p2_source)},
        "configs": {"p1": str(p1_config), "p2": str(p2_config)},
        "source_sha256": {"p1": sha256_file(Path(p1_source)),
                          "p2": sha256_file(Path(p2_source))},
        "patterns": {slot: {alias.lower(): data.hex()
                            for alias, data in per_slot[slot]["patterns"].items()
                            if alias in REQUIRED_ALIASES}
                     for slot in ("p1", "p2")},
        "provenance": {slot: {k: v for k, v in per_slot[slot].items()
                              if k != "patterns"} for slot in ("p1", "p2")},
    }
    return header, report


def self_check() -> int:
    """Prova a máquina sem acervo: resolução de alias, tier no blob e falha fechada."""
    def command(name: str, text: str) -> cmdmod.Command:
        steps, errors = cmdmod.parse_command_string(text)
        return cmdmod.Command(name, steps, 15, 1, 1, text, errors)

    commands = [command("a", "a"), command("c", "c"), command("x", "x"),
                command("z", "z"), command("FF", "F, F"), command("mp", "b")]
    patterns, skipped = sms_cmd.to_patterns(commands, DEFAULT_MAP)
    by_name = {_norm(p.name): sms_cmd.serialize_pattern(p) for p in patterns}
    cfg = {"commands": {"lp": "A", "hp": "C", "lk": "X", "hk": "Z", "ff": "FF"}}
    resolved = resolve_aliases(cfg, by_name, skipped, "self_check.json")
    distinct = (resolved["LP"] != resolved["HP"] and resolved["LK"] != resolved["HK"])
    tiers = (resolved["LP"][0] == BLOB_FMT_VERSION and resolved["LP"][5] >> 2 == 1
             and resolved["HP"][5] >> 2 == 2)
    keys = (resolved["LP"][4] >> 4 == 1 and resolved["LK"][4] >> 4 == 2)
    try:
        resolve_aliases({"commands": {"lp": "a", "hp": "c", "lk": "x"}},
                        by_name, skipped, "self_check.json")
        falta_alias = False
    except ValueError:
        falta_alias = True
    try:
        resolve_aliases({"commands": {"lp": "nao_existe", "hp": "c",
                                      "lk": "x", "hk": "z"}},
                        by_name, skipped, "self_check.json")
        alias_inexistente = False
    except ValueError:
        alias_inexistente = True
    ok = distinct and tiers and keys and falta_alias and alias_inexistente
    print("self-check cmd_patterns:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--p1-source", type=Path)
    ap.add_argument("--p1-config", type=Path)
    ap.add_argument("--p2-source", type=Path)
    ap.add_argument("--p2-config", type=Path)
    ap.add_argument("--out-header", type=Path)
    ap.add_argument("--out-report", type=Path)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args(argv)
    if args.self_check:
        return self_check()
    required = (args.p1_source, args.p1_config, args.p2_source, args.p2_config,
                args.out_header, args.out_report)
    if any(v is None for v in required):
        ap.error("--p1-source/--p1-config/--p2-source/--p2-config/"
                 "--out-header/--out-report sao obrigatorios")
    header, report = generate(args.p1_source, args.p1_config,
                              args.p2_source, args.p2_config)
    args.out_header.parent.mkdir(parents=True, exist_ok=True)
    args.out_report.parent.mkdir(parents=True, exist_ok=True)
    args.out_header.write_text(header, encoding="utf-8")
    args.out_report.write_text(json.dumps(report, indent=2,
                                          ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[CMD] {len(report['patterns']['p1']) + len(report['patterns']['p2'])} "
          f"padroes; P1={report['provenance']['p1']['slug']} "
          f"P2={report['provenance']['p2']['slug']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
