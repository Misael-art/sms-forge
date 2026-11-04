"""Private recorder custody/cleanup tests; actual capture needs emulator proof."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from session_bridge import isolated


@pytest.mark.parametrize('seconds,name', [(0, 'clip'), (31, 'clip'),
                                         (True, 'clip'), (2, '../escape')])
def test_bad_capture_request_never_contacts_session(monkeypatch, seconds, name):
    monkeypatch.setattr(isolated, 'load', lambda _: pytest.fail('invalid request contacted session'))
    with pytest.raises(ValueError):
        isolated.realtime_video('unused', seconds, name)


def test_interrupted_capture_stops_native_stream(monkeypatch, tmp_path):
    (tmp_path / 'evidence').mkdir()
    monkeypatch.setattr(isolated, 'load', lambda _: (tmp_path, {}))
    operations = []

    def request(_session, operation, *_args):
        operations.append(operation)
        return {}

    def interrupted(_seconds):
        raise RuntimeError('interrupted capture')

    monkeypatch.setattr(isolated, 'request', request)
    monkeypatch.setattr(isolated.time, 'sleep', interrupted)
    with pytest.raises(RuntimeError, match='interrupted capture'):
        isolated.realtime_video('own-session', 1)
    assert operations == ['record-start', 'record-stop']


def test_truncated_rgb_is_not_encoded_or_approved(monkeypatch, tmp_path):
    (tmp_path / 'evidence').mkdir()
    monkeypatch.setattr(isolated, 'load', lambda _: (tmp_path, {}))
    operations = []

    def request(_session, operation, *_args):
        operations.append(operation)
        if operation == 'record-start':
            (tmp_path / 'evidence/clip.rgb').write_bytes(b'truncated')
        return {'recorded_frames': 60}

    monkeypatch.setattr(isolated, 'request', request)
    monkeypatch.setattr(isolated.time, 'sleep', lambda _: None)
    monkeypatch.setattr(isolated, 'checked', lambda *_a, **_k: pytest.fail('bad RGB reached encoder'))
    with pytest.raises(RuntimeError, match='length/count mismatch'):
        isolated.realtime_video('own-session', 1, 'clip')
    assert operations == ['record-start', 'record-stop']
    assert not (tmp_path / 'evidence/clip.json').exists()


def test_failed_start_does_not_stop_another_capture(monkeypatch, tmp_path):
    (tmp_path / 'evidence').mkdir()
    monkeypatch.setattr(isolated, 'load', lambda _: (tmp_path, {}))
    operations = []

    def request(_session, operation, *_args):
        operations.append(operation)
        raise RuntimeError('start rejected')

    monkeypatch.setattr(isolated, 'request', request)
    with pytest.raises(RuntimeError, match='start rejected'):
        isolated.realtime_video('own-session', 1)
    assert operations == ['record-start']
