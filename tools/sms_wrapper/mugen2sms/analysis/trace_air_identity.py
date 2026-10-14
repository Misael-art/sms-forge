"""Decode per-tick AIR identities from the diagnostic TRC3 ROM trace."""
from __future__ import annotations

import re

AIR_TRACE_MAGIC = b"TRC3"
AIR_TRACE_HEADER_BYTES = 8
AIR_TRACE_RECORD_BYTES = 6
AIR_TRACE_MAX_TICKS = 340
SOURCE_IDENTITY_SCHEMA = "mugen2sms.air-source-identity/v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def validate_source_identity(source_identity: dict) -> None:
    """Fail closed unless the source manifest has a self-consistent AIR contract."""
    if not isinstance(source_identity, dict):
        raise ValueError("source AIR identity must be an object")
    if source_identity.get("schema") != SOURCE_IDENTITY_SCHEMA:
        raise ValueError("unsupported source AIR identity schema")
    if source_identity.get("kind") != "air_source_identity":
        raise ValueError("source AIR identity kind is missing or invalid")
    if source_identity.get("sequence_scope") != "one_finite_non_looping_action_pass":
        raise ValueError("source AIR identity must describe one finite non-looping pass")
    if source_identity.get("counter_bits") != 16:
        raise ValueError("source AIR identity counter_bits must be 16")

    action_id = source_identity.get("action_id")
    if type(action_id) is not int or not 0 <= action_id <= 0xFFFF:
        raise ValueError("source AIR action id must be uint16")
    durations = source_identity.get("durations")
    if (not isinstance(durations, list) or not durations or len(durations) > 255
            or any(type(value) is not int or not 0 < value < 32768 for value in durations)):
        raise ValueError("source AIR durations/elements exceed the finite runtime contract")

    expected_ids = [f"{action_id}:{index}" for index in range(len(durations))]
    expected_ids.append(f"{action_id}:terminal")
    if source_identity.get("boundary_element_ids") != expected_ids:
        raise ValueError("source AIR boundary IDs do not match ordered elements")
    cumulative = [0]
    for duration in durations:
        cumulative.append(cumulative[-1] + duration)
    boundary_ticks = source_identity.get("boundary_cumulative_ticks")
    if (not isinstance(boundary_ticks, list)
            or any(type(value) is not int for value in boundary_ticks)
            or boundary_ticks != cumulative):
        raise ValueError("source AIR cumulative boundaries differ from durations")

    elements = source_identity.get("elements")
    if not isinstance(elements, list) or len(elements) != len(durations):
        raise ValueError("source AIR elements do not match the duration list")
    for index, (element, duration) in enumerate(zip(elements, durations)):
        if (not isinstance(element, dict)
                or element.get("element_id") != f"{action_id}:{index}"
                or type(element.get("element_index")) is not int
                or element.get("element_index") != index
                or type(element.get("duration")) is not int
                or element.get("duration") != duration):
            raise ValueError(f"source AIR element {index} disagrees with its identity or duration")

    source = source_identity.get("source")
    if not isinstance(source, dict):
        raise ValueError("source AIR provenance is missing")
    for field in ("package_name", "def_path", "air_path"):
        if not isinstance(source.get(field), str) or not source[field].strip():
            raise ValueError(f"source AIR provenance field {field} is missing")
    for field in ("package_sha256", "air_sha256"):
        value = source.get(field)
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise ValueError(f"source AIR provenance field {field} is not a lowercase SHA-256")


def decode_buffer(buffer: bytes, expect_ticks: int = AIR_TRACE_MAX_TICKS) -> list[dict]:
    """Decode TRC3 state plus source action/element identity for both fighters."""
    if type(expect_ticks) is not int or not 1 <= expect_ticks <= AIR_TRACE_MAX_TICKS:
        raise ValueError(f"expected AIR trace ticks must be in 1..{AIR_TRACE_MAX_TICKS}")
    if len(buffer) < AIR_TRACE_HEADER_BYTES:
        raise ValueError("AIR trace shorter than header")
    if bytes(buffer[:4]) != AIR_TRACE_MAGIC:
        raise ValueError(f"AIR trace magic {bytes(buffer[:4])!r} != {AIR_TRACE_MAGIC!r}")
    done = buffer[4]
    count = buffer[5] | (buffer[6] << 8)
    record_bytes = buffer[7]
    if record_bytes != AIR_TRACE_RECORD_BYTES:
        raise ValueError(f"AIR trace record size {record_bytes} != {AIR_TRACE_RECORD_BYTES}")
    if done != 1 or count != expect_ticks:
        raise ValueError(f"AIR trace incomplete (done={done}, count={count}, expected={expect_ticks})")
    expected_size = AIR_TRACE_HEADER_BYTES + count * record_bytes
    if len(buffer) != expected_size:
        if len(buffer) < expected_size:
            raise ValueError("AIR trace payload truncated")
        raise ValueError("AIR trace has trailing bytes outside its declared payload")

    rows = []
    for tick in range(count):
        base = AIR_TRACE_HEADER_BYTES + tick * record_bytes
        row = {"tick": tick}
        for side, offset in (("p1", 0), ("p2", 3)):
            action_low, action_high, element = buffer[base + offset:base + offset + 3]
            row[f"{side}_air_action"] = action_low | (action_high << 8)
            row[f"{side}_air_element"] = element
        rows.append(row)
    return rows


def derive_action_boundaries(rows: list[dict], side: str,
                             source_identity: dict) -> dict:
    """Collapse one complete finite source action into N+1 ROM boundaries.

    The recorder samples after each logic tick. An action ending before its
    terminal row, repeating, skipping, or leaving elements out of order fails.
    """
    if side not in {"p1", "p2"}:
        raise ValueError("side must be p1 or p2")
    validate_source_identity(source_identity)
    if not isinstance(rows, list) or not rows:
        raise ValueError("AIR tick trace is empty")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("AIR tick trace contains a non-object row")
    if any(type(row.get("tick")) is not int or row.get("tick") != index
           for index, row in enumerate(rows)):
        raise ValueError("AIR tick trace has missing or reordered ticks")

    action_id = source_identity.get("action_id")
    durations = source_identity.get("durations")

    action_key = f"{side}_air_action"
    element_key = f"{side}_air_element"
    for index, row in enumerate(rows):
        action_value, element_value = row.get(action_key), row.get(element_key)
        if type(action_value) is not int or not 0 <= action_value <= 0xFFFF:
            raise ValueError(f"invalid AIR action id at tick {index}")
        if type(element_value) is not int or not 0 <= element_value <= 0xFF:
            raise ValueError(f"invalid AIR element index at tick {index}")
    matches = [index for index, row in enumerate(rows) if row.get(action_key) == action_id]
    if not matches:
        raise ValueError(f"source action {action_id} is absent from {side} trace")
    start, last = matches[0], matches[-1]
    if matches != list(range(start, last + 1)):
        raise ValueError(f"source action {action_id} is interrupted or repeated in {side} trace")
    if last + 1 >= len(rows):
        raise ValueError(f"source action {action_id} has no observed terminal boundary")

    starts: list[int] = []
    observed_ids: list[str] = []
    previous = -1
    for index in range(start, last + 1):
        element = rows[index].get(element_key)
        if type(element) is not int or not 0 <= element < len(durations):
            raise ValueError(f"invalid AIR element index at tick {index}")
        if element != previous:
            if element != previous + 1:
                raise ValueError(f"AIR elements are skipped or reordered at tick {index}")
            starts.append(rows[index]["tick"])
            observed_ids.append(f"{rows[index][action_key]}:{element}")
            previous = element
    if previous != len(durations) - 1 or len(starts) != len(durations):
        raise ValueError("ROM trace does not cover every source AIR element")

    terminal = rows[last + 1]
    if terminal["tick"] != rows[last]["tick"] + 1:
        raise ValueError("terminal boundary is not on the next logic tick")
    if terminal.get(action_key) == action_id:
        raise ValueError("terminal boundary still reports the source action")
    stamps = starts + [terminal["tick"]]
    observed_ids.append(f"{rows[last][action_key]}:terminal")
    observed = [(end - begin) & 0xFFFF for begin, end in zip(stamps, stamps[1:])]
    if observed != durations:
        raise ValueError(f"ROM AIR durations {observed} differ from source {durations}")

    return {
        "schema": "mugen2sms.air-identity-rom-trace/v1",
        "action_id": action_id,
        "side": side,
        "counter_bits": 16,
        "source_durations": durations,
        "air_boundary_stamps": stamps,
        "air_boundary_element_ids": observed_ids,
        "observed_durations": observed,
        "trace_tick_range": [rows[start]["tick"], terminal["tick"]],
    }
