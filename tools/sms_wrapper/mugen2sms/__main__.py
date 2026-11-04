"""Entradas SMS realmente implementadas; cada conversor conserva sua própria CLI."""
from __future__ import annotations
import argparse
import importlib
import sys

COMMANDS = {
    "inventory": "mugen2sms.inventory",
    "parse-char": "mugen2sms.ken_full_parse",
    "air-source-identity": "mugen2sms.analysis.air_source_identity",
    "generate": "mugen2sms.generators.smsdev",
    "scene-cut": "mugen2sms.generators.scene_cut",
    "versus-cut": "mugen2sms.generators.versus_scene_cut",
    "quality-check": "audit_mugen_engine_contract",
    "runtime-vram-plan": "mugen2sms.runtime.vram_plan",
    "runtime-commit-budget": "mugen2sms.runtime.commit_budget",
    "display-fit": "mugen2sms.converters.display_fit",
}

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="mugen2sms", description=__doc__)
    parser.add_argument("command", choices=COMMANDS)
    if not argv or argv[0] in ("-h", "--help"):
        parser.print_help()
        return 0 if argv else 2
    if argv[0] not in COMMANDS:
        parser.error("comando não implementado no alvo SMS: " + argv[0])
    return importlib.import_module(COMMANDS[argv[0]]).main(argv[1:])

if __name__ == "__main__":
    raise SystemExit(main())
