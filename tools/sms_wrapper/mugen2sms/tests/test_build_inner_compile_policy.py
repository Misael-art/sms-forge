"""Per-module SDCC size optimization keeps hot runtime code on speed defaults."""
from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
BUILD_INNER = ROOT / "tools" / "sms_wrapper" / "build_inner.py"
SPEC = importlib.util.spec_from_file_location("sms_build_inner_policy", BUILD_INNER)
assert SPEC and SPEC.loader
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


def test_size_optimization_can_be_scoped_to_named_sources():
    policy = {"code_size_sources": ["src/cpu_controller.c"]}
    assert BUILD.uses_code_size_optimization(policy, "src/cpu_controller.c")
    assert BUILD.uses_code_size_optimization(policy, r"src\cpu_controller.c")
    assert not BUILD.uses_code_size_optimization(policy, "src/fight.c")


def test_existing_project_wide_size_setting_still_wins():
    policy = {"optimization": "code_size", "code_size_sources": []}
    assert BUILD.uses_code_size_optimization(policy, "src/main.c")
