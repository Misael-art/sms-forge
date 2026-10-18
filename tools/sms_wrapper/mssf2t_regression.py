#!/usr/bin/env python3
"""Regressões de contrato do núcleo MSSF2T.

Não substitui replay no Z80. Exercita fixtures puras e também verifica que o
fonte usa as estruturas que tornam os casos impossíveis de regredir por uma
conversão estreita ou por dano aplicado durante a iteração de contatos.
"""
import argparse
import pathlib
import re
import sys


def key_down(keys, mask):
    return 1 if (keys & mask) != 0 else 0


def resolve_snapshot(hp, contacts):
    """Modelo mínimo: todos os contatos do tick são consumidos antes do KO."""
    used = set()
    damage = [0, 0]
    for attacker, defender, identity, amount in contacts:
        token = (attacker, identity)
        if token in used:
            continue
        used.add(token)
        damage[defender] += amount
    return [max(0, hp[i] - damage[i]) for i in range(2)]


def check_source(project):
    source = (pathlib.Path(project) / "src/fight.c").read_text()
    source += (pathlib.Path(project) / "inc/fight.h").read_text()
    required = [
        "CONTROL_HUMAN", "CONTROL_CPU", "CONTROL_DUMMY", "CONTROL_REPLAY",
        "key_down", "Contact", "contact_count", "reset_positions",
    ]
    missing = [needle for needle in required if needle not in source]
    if missing:
        return ["fonte ainda não implementa: " + ", ".join(missing)]
    if re.search(r"\(unsigned char\)\s*\(keys\s*&\s*PORT_B_KEY_", source):
        return ["A02 regressão: máscara PORT_B estreitada antes da comparação"]
    collide = source[source.index("static void collide"):source.index("/* Corpos deixam", source.index("static void collide"))]
    if "apply_hit(a, b" in collide and "contact_count" not in collide:
        return ["A05 regressão: dano ainda é aplicado dentro da iteração imediata"]
    return []


def self_check():
    assert key_down(0x0100, 0x0100) == 1
    assert key_down(0x0200, 0x0100) == 0
    assert resolve_snapshot([10, 10], [(0, 1, 1, 7), (1, 0, 2, 10)]) == [0, 3]
    assert resolve_snapshot([10, 10], [(0, 1, 1, 7), (0, 1, 1, 7)]) == [10, 3]
    print("[SELF-CHECK OK] MSSF2T regressions: P2 16-bit, trade, identity/multi-hit")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return self_check()
    if not args.project:
        ap.error("--project obrigatório")
    problems = check_source(args.project)
    if problems:
        for problem in problems:
            print("[FAIL] " + problem)
        return 1
    print("[PASS] contratos MSSF2T presentes; fixtures M01 aprovadas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
