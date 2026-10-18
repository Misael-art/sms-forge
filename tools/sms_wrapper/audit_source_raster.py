#!/usr/bin/env python3
"""Preflight a saved sprite-sheet source, without converting or promoting it.

Contract (all rectangles use x,y,width,height in saved-image pixels)::

  {"schema":"sms_source_raster_contract_v1", "image_sha256":"<64 hex>",
   "dimensions_px":[16,8], "frame_count":2,
   "expected_frame_ids":["A01","A02"],
   "frames":[{"id":"A01","rect_px":[0,0,8,8]},
             {"id":"A02","rect_px":[8,0,8,8]}],
   "transparency":{"mode":"binary_alpha"},
   "grid":{"columns":2,"rows":1,"cell_px":[8,8]}}

grid and max_unique_rgb are optional. The other transparency mode is
opaque_key with rgb:[r,g,b]: it checks opacity and exact key presence only,
not background uniformity or whether a key-colored pixel is background.
max_unique_rgb counts all saved RGB values, including hidden transparent RGB;
it is an explicit source contract, never an implicit Master System limit.
Frame rectangles/IDs describe declared slots, not recognized drawn poses.
Concepts/free raw art are outside this gate. No image is modified. Anatomy,
lighting, artistic quality, runtime palettes, emulation and promotion remain
outside its scope; indexed cleanup/proof/animation gates retain their roles.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import warnings

from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 64 * 1024 * 1024
MAX_PIXELS = 16 * 1024 * 1024
MAX_CONTRACT_BYTES = 1024 * 1024
MAX_FRAMES = 1024
SCHEMA = "sms_source_raster_contract_v1"


def positive(value):
    return type(value) is int and value > 0


def pair(value):
    return isinstance(value, list) and len(value) == 2 and all(map(positive, value))


def text_id(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 128


def contract_errors(contract):
    errors = []
    if not isinstance(contract, dict):
        return ["contract must be an object"]
    if contract.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    digest = contract.get("image_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        errors.append("image_sha256 must contain 64 hexadecimal characters")
    dimensions = contract.get("dimensions_px")
    valid_dimensions = pair(dimensions)
    if not valid_dimensions or dimensions[0] * dimensions[1] > MAX_PIXELS:
        errors.append("dimensions_px must be two positive integers within pixel bound")
    count = contract.get("frame_count")
    if not positive(count) or count > MAX_FRAMES:
        errors.append(f"frame_count must be 1..{MAX_FRAMES}")
    expected = contract.get("expected_frame_ids")
    if (not isinstance(expected, list) or not expected or
            any(not text_id(x) for x in expected)):
        errors.append("expected_frame_ids must be a nonempty list of IDs")
    elif len(set(expected)) != len(expected):
        errors.append("expected_frame_ids must be unique")
    frames = contract.get("frames")
    if not isinstance(frames, list) or not frames or len(frames) > MAX_FRAMES:
        errors.append(f"frames must contain 1..{MAX_FRAMES} objects")
        frames = []
    if isinstance(expected, list) and count != len(expected):
        errors.append("frame_count differs from expected_frame_ids count")
    if count != len(frames):
        errors.append("frame_count differs from frames count")
    ids, rectangles = [], []
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            errors.append(f"frame {index}: expected an object")
            continue
        fid, rect = frame.get("id"), frame.get("rect_px")
        if not text_id(fid):
            errors.append(f"frame {index}: invalid id")
        else:
            ids.append(fid)
        if (not isinstance(rect, list) or len(rect) != 4 or
                any(type(x) is not int for x in rect) or
                min(rect[:2]) < 0 or min(rect[2:]) <= 0):
            errors.append(f"frame {index}: rect_px must be nonnegative x,y and positive width,height")
            continue
        x, y, width, height = rect
        if valid_dimensions and (x + width > dimensions[0] or y + height > dimensions[1]):
            errors.append(f"frame {index}: rectangle outside declared canvas")
        for previous_index, (px, py, pw, ph) in rectangles:
            if x < px + pw and px < x + width and y < py + ph and py < y + height:
                errors.append(f"frames {previous_index}/{index}: rectangles overlap")
        rectangles.append((index, rect))
    if len(set(ids)) != len(ids):
        errors.append("frames contain duplicate IDs")
    if ids != expected:
        errors.append("frame ID order differs from expected_frame_ids")
    transparency = contract.get("transparency")
    if not isinstance(transparency, dict):
        errors.append("transparency must be an object")
    elif transparency.get("mode") == "binary_alpha":
        if "rgb" in transparency:
            errors.append("binary_alpha does not accept a key rgb")
    elif transparency.get("mode") == "opaque_key":
        rgb = transparency.get("rgb")
        if (not isinstance(rgb, list) or len(rgb) != 3 or
                any(type(x) is not int or not 0 <= x <= 255 for x in rgb)):
            errors.append("opaque_key requires rgb as three integers 0..255")
    else:
        errors.append("transparency.mode must be binary_alpha or opaque_key")
    ceiling = contract.get("max_unique_rgb")
    if "max_unique_rgb" in contract and (not positive(ceiling) or ceiling > 16777216):
        errors.append("max_unique_rgb must be 1..16777216 when declared")
    grid = contract.get("grid")
    if "grid" in contract:
        if (not isinstance(grid, dict) or not positive(grid.get("columns")) or
                not positive(grid.get("rows")) or not pair(grid.get("cell_px"))):
            errors.append("grid requires positive columns, rows and cell_px")
        else:
            columns, rows = grid["columns"], grid["rows"]
            fw, fh = grid["cell_px"]
            if [columns * fw, rows * fh] != dimensions:
                errors.append("grid extent differs from dimensions_px")
            if columns * rows != count:
                errors.append("grid cell count differs from frame_count")
            for index, frame in enumerate(frames):
                expected_rect = [(index % columns) * fw, (index // columns) * fh, fw, fh]
                if not isinstance(frame, dict) or frame.get("rect_px") != expected_rect:
                    errors.append(f"frame {index}: rectangle differs from row-major grid")
    return errors


def bounded_bytes(path, limit):
    with Path(path).open("rb") as handle:
        payload = handle.read(limit + 1)
    if len(payload) > limit:
        raise ValueError(f"file exceeds {limit}-byte bound: {path}")
    return payload


def audit(image_path, contract):
    """Return measured facts and a narrow gate decision for one immutable read."""
    errors = contract_errors(contract)
    report = {"schema": "sms_source_raster_audit_v1", "ok": False,
              "scope": "saved_sprite_sheet_source_preconversion",
              "claims": {"declared_slots_only": True, "background_uniformity": False,
                         "artistic_quality": False, "sms_runtime_palette": False,
                         "runtime_validated": False, "promotion_approved": False},
              "image": {"path": str(Path(image_path).resolve())},
              "problems": errors}
    if errors:
        return report
    try:
        payload = bounded_bytes(image_path, MAX_IMAGE_BYTES)
        digest = hashlib.sha256(payload).hexdigest()
        report["image"].update({"sha256": digest, "bytes": len(payload)})
        if digest != contract["image_sha256"].lower():
            errors.append("image SHA-256 differs from contract")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(payload)) as source:
                if source.format != "PNG":
                    raise ValueError("source must be a PNG")
                if source.width * source.height > MAX_PIXELS:
                    raise ValueError("source exceeds pixel bound")
                if getattr(source, "n_frames", 1) != 1:
                    raise ValueError("source must be a single-image PNG, not APNG")
                if source.mode not in {"RGB", "RGBA", "P", "L", "LA", "1"}:
                    raise ValueError(f"unsupported source mode: {source.mode}")
                source.load()
                dimensions, mode = list(source.size), source.mode
                rgba = source.convert("RGBA")
        if dimensions != contract["dimensions_px"]:
            errors.append("saved image dimensions differ from contract")
        histogram = rgba.getchannel("A").histogram()
        total = dimensions[0] * dimensions[1]
        rgb = rgba.convert("RGB")
        colors = rgb.getcolors(maxcolors=total)
        unique = len(colors)
        report["measured"] = {"dimensions_px": dimensions, "mode": mode,
                              "unique_rgb": unique, "alpha_zero_pixels": histogram[0],
                              "alpha_255_pixels": histogram[255],
                              "partial_alpha_pixels": sum(histogram[1:255]),
                              "declared_frame_ids": contract["expected_frame_ids"],
                              "declared_frame_count": contract["frame_count"]}
        transparency = contract["transparency"]
        if transparency["mode"] == "binary_alpha":
            if sum(histogram[1:255]):
                errors.append("binary_alpha: saved image contains intermediate alpha")
            if histogram[0] == 0:
                errors.append("binary_alpha: no transparent pixels")
            if histogram[255] == 0:
                errors.append("binary_alpha: no opaque pixels")
        else:
            key = tuple(transparency["rgb"])
            key_pixels = next((n for n, value in colors if value == key), 0)
            report["measured"]["exact_key_pixels"] = key_pixels
            if histogram[255] != total:
                errors.append("opaque_key: all pixels must be opaque")
            if key_pixels == 0:
                errors.append("opaque_key: exact RGB key is absent")
        if "max_unique_rgb" in contract and unique > contract["max_unique_rgb"]:
            errors.append(f"unique RGB count {unique} exceeds explicit source limit {contract['max_unique_rgb']}")
    except (OSError, ValueError, SyntaxError, UnidentifiedImageError,
            Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        errors.append(f"source unreadable: {exc}")
    report["ok"] = not errors
    return report


def write_report(path, report, protected):
    target = Path(path)
    for source in protected:
        if target.resolve() == Path(source).resolve() or (
                target.exists() and Path(source).exists() and os.path.samefile(target, source)):
            raise ValueError("report output must not overwrite image or contract")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent,
                                         prefix=".source-raster-", delete=False) as handle:
            temporary = handle.name
            json.dump(report, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary, target)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def self_check():
    with tempfile.TemporaryDirectory(prefix="sms-source-raster-selfcheck-") as directory:
        root = Path(directory)
        image = Image.new("RGBA", (16, 8), (0, 0, 0, 0))
        image.putpixel((2, 2), (255, 255, 255, 255))
        image.putpixel((10, 2), (255, 255, 255, 255))
        path = root / "fixture.png"
        image.save(path)
        contract = {"schema": SCHEMA, "image_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "dimensions_px": [16, 8], "frame_count": 2,
                    "expected_frame_ids": ["A01", "A02"],
                    "frames": [{"id": "A01", "rect_px": [0, 0, 8, 8]},
                               {"id": "A02", "rect_px": [8, 0, 8, 8]}],
                    "transparency": {"mode": "binary_alpha"},
                    "grid": {"columns": 2, "rows": 1, "cell_px": [8, 8]}}
        assert audit(path, contract)["ok"]
        negatives = 0
        def reject(value, image_path=path):
            nonlocal negatives
            assert not audit(image_path, value)["ok"], value
            negatives += 1
        for key, value in [("schema", "wrong"), ("image_sha256", "0" * 64),
                           ("dimensions_px", [15, 8]), ("dimensions_px", [True, 8]),
                           ("frame_count", 3), ("frame_count", True),
                           ("expected_frame_ids", ["A01", "A01"]),
                           ("expected_frame_ids", ["A02", "A01"]),
                           ("expected_frame_ids", [[], {}]), ("frames", [None]),
                           ("frames", {}), ("transparency", []),
                           ("transparency", {"mode": []}), ("max_unique_rgb", 1),
                           ("max_unique_rgb", True), ("grid", {"columns": 0}),
                           ("grid", {"columns": 1, "rows": 2, "cell_px": [8, 8]})]:
            mutated = copy.deepcopy(contract)
            mutated[key] = value
            reject(mutated)
        for rect in ([0, 0, 16, 8], [15, 0, 8, 8], [-1, 0, 8, 8], [8, 0, 0, 8],
                     [8, 0, True, 8], [8, 0, 8], "bad"):
            mutated = copy.deepcopy(contract)
            mutated["frames"][1]["rect_px"] = rect
            reject(mutated)
        mutated = copy.deepcopy(contract)
        mutated["frames"][1]["id"] = "A01"
        reject(mutated)
        for malformed in (None, [], "bad", 1):
            reject(malformed)
        translucent = image.copy()
        translucent.putpixel((2, 2), (255, 255, 255, 127))
        translucent_path = root / "translucent.png"
        translucent.save(translucent_path)
        mutated = copy.deepcopy(contract)
        mutated["image_sha256"] = hashlib.sha256(translucent_path.read_bytes()).hexdigest()
        reject(mutated, translucent_path)
        for opaque in (False, True):
            alpha_image = Image.new("RGBA", (16, 8), (0, 0, 0, 255 if opaque else 0))
            alpha_path = root / f"alpha-{opaque}.png"
            alpha_image.save(alpha_path)
            mutated = copy.deepcopy(contract)
            mutated["image_sha256"] = hashlib.sha256(alpha_path.read_bytes()).hexdigest()
            reject(mutated, alpha_path)
        opaque_path = root / "opaque.png"
        image.convert("RGB").save(opaque_path)
        keyed = copy.deepcopy(contract)
        keyed["image_sha256"] = hashlib.sha256(opaque_path.read_bytes()).hexdigest()
        keyed["transparency"] = {"mode": "opaque_key", "rgb": [0, 0, 0]}
        assert audit(opaque_path, keyed)["ok"]
        keyed["transparency"]["rgb"] = [255, 0, 255]
        reject(keyed, opaque_path)
        keyed["transparency"]["rgb"] = [True, 0, 0]
        reject(keyed, opaque_path)
        indexed_path = root / "indexed.png"
        indexed = Image.new("P", (16, 8), 0)
        indexed.putpalette([0, 0, 0, 255, 255, 255] + [0] * 762)
        indexed.putpixel((2, 2), 1)
        indexed.save(indexed_path, transparency=0)
        mutated = copy.deepcopy(contract)
        mutated["image_sha256"] = hashlib.sha256(indexed_path.read_bytes()).hexdigest()
        assert audit(indexed_path, mutated)["ok"]
        bad_path = root / "broken.png"
        bad_path.write_bytes(b"not png")
        reject(contract, bad_path)
        contract_path = root / "contract.json"
        contract_path.write_text(json.dumps(contract))
        for protected in (path, contract_path):
            before = protected.read_bytes()
            try:
                write_report(protected, {}, [path, contract_path])
            except ValueError:
                pass
            else:
                raise AssertionError("protected input overwritten")
            assert protected.read_bytes() == before
        print(f"self-check: PASS (binary/RGB/indexed positives; {negatives} negatives; input preservation)")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--json", type=Path, help="write JSON report atomically; stdout always prints JSON")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        self_check()
        return 0
    if args.image is None or args.contract is None:
        parser.error("--image and --contract are required")
    try:
        payload = bounded_bytes(args.contract, MAX_CONTRACT_BYTES)
        contract = json.loads(payload.decode("utf-8"))
        report = audit(args.image, contract)
        report["contract"] = {"path": str(args.contract.resolve()),
                              "sha256": hashlib.sha256(payload).hexdigest()}
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        report = {"schema": "sms_source_raster_audit_v1", "ok": False,
                  "problems": [f"contract unreadable: {exc}"]}
    if args.json is not None:
        try:
            write_report(args.json, report, [args.image, args.contract])
        except (OSError, ValueError) as exc:
            report["ok"] = False
            report.setdefault("problems", []).append(f"report output refused: {exc}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
