"""Immutable JSON report output. Inputs and existing reports are never replaced."""
import json
from pathlib import Path


def write_new_report(path, data):
    """Serialize before opening; exclusive create also rejects symlink/hardlink aliases."""
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    target = Path(path)
    with target.open("x", encoding="utf-8") as stream:
        stream.write(payload)


def self_check():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "lesson.json"
        source.write_text('{"lessons":[{"id":"example"}]}')
        before = source.read_bytes()
        for path in (source, root / "symlink.json", root / "hardlink.json"):
            if path.name == "symlink.json":
                path.symlink_to(source)
            elif path.name == "hardlink.json":
                path.hardlink_to(source)
            try:
                write_new_report(path, {"problems": [], "clean": True})
            except FileExistsError:
                pass
            else:
                raise AssertionError("existing destination was not refused")
            assert source.read_bytes() == before
        fresh = root / "run.json"
        write_new_report(fresh, {"clean": True})
        assert json.loads(fresh.read_text())["clean"] is True
        try:
            write_new_report(root / "invalid.json", {"bad": object()})
        except TypeError:
            pass
        assert not (root / "invalid.json").exists()
    print("[SELF-CHECK OK] exclusive JSON reports preserve existing inputs and aliases")
    return 0


def cli_self_check():
    """Exercise both aliases of all migrated CLIs without scanning a live repo."""
    import contextlib
    import importlib
    import io
    import tempfile
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "lesson.json"
        source.write_text('{"lessons":[{"id":"fixture"}]}')
        before = source.read_bytes()
        for name in ("audit_hardware_constants", "audit_header_claims", "audit_debug_markers", "audit_learning_capture"):
            module = importlib.import_module(name)
            outcome = ([], None) if name == "audit_header_claims" else []
            with patch.object(module, "audit", return_value=outcome), contextlib.redirect_stdout(io.StringIO()):
                for flag in ("--json", "--report-out"):
                    with patch("sys.argv", [name, flag, str(source)]):
                        assert module.main() == 3, name + " existing output must be refused"
                    assert source.read_bytes() == before
                fresh = root / (name + ".json")
                with patch("sys.argv", [name, "--report-out", str(fresh)]):
                    assert module.main() == 0
                assert json.loads(fresh.read_text())["clean"] is True
    print("[SELF-CHECK OK] four report CLIs preserve inputs with both output aliases")
    return 0
