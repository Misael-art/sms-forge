#!/usr/bin/env python3
"""Exercise trace orchestration against prerecorded fake bridge replies only."""
import contextlib
import importlib.util
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("alis_input_trace", HERE / "alis_input_trace.py")
trace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trace)


def sample(frame, pose=0, elapsed=0, latch=0, triggers=0, pressure=0):
    data = [0] * 15
    data[0:2] = [frame & 255, (frame >> 8) & 255]
    data[6], data[9], data[10], data[11], data[12] = pose, elapsed, latch, triggers, pressure
    return data


def check_case(mode, replies, fail=False):
    seen, frames = [], [0]
    data = iter(replies)

    def request(_root, operation, *args):
        seen.append((operation, args))
        if operation == "read":
            return {"frame": frames[0], "ram": next(data)}
        if operation == "step":
            if fail:
                raise RuntimeError("fixture bridge interruption")
            frames[0] += args[0]
        return {"frame": frames[0]}

    with tempfile.TemporaryDirectory(dir=ROOT / ".runtime") as temp:
        out = Path(temp) / "trace.json"
        meta = {"rom_sha256": "a" * 64, "session_id": "test"}
        with patch.object(trace.isolated, "load", return_value=(Path(temp), meta)), \
             patch.object(trace.isolated, "request", side_effect=request), \
             contextlib.redirect_stdout(io.StringIO()):
            try:
                trace.run("test", "a" * 64, mode, 3, out, False)
            except RuntimeError:
                if not fail:
                    raise
            else:
                if fail:
                    raise AssertionError("bridge interruption not propagated")
        result = json.loads(out.read_text())
        assert [op for op in seen if op[0] == "input"][-1][1] == (0, 0, 0)
        assert result["status"] == ("incomplete" if fail else "collected_requires_interpretation")
        assert result["rom_sha256"] == "a" * 64
        return result


def main():
    trace.self_check()
    pressed = check_case("press", [sample(0), sample(1, pressure=1),
                                     sample(2, pressure=2), sample(3, pressure=3), sample(4)])
    assert [s["label"] for s in pressed["samples"]] == ["baseline", "pressed", "pressed", "pressed", "released"]
    replies = [sample(0), sample(1, 1, 0, 1, 1, 12), sample(2, 1, 1, 0, 1, 0),
               sample(3, 1, 2, 0, 1, 0), sample(4, 1, 3, 0, 1, 0)]
    replies += [sample(5+i, 3 if i < 12 else 0, i % 6, int(i >= 11), 1, min(i+1, 12)) for i in range(16)]
    replies += [sample(22, 0, 0, 0, 1, 0)]
    boundary = check_case("last_recovery", replies)
    assert sum(s["label"] == "repress_last_recovery_attempt" for s in boundary["samples"]) == 16
    check_case("press", [sample(0)], fail=True)
    print("[SELF-CHECK OK] fake bridge ordering, release and interruption; no ROM executed")


if __name__ == "__main__":
    main()
