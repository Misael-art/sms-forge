"""Join native Scene 02 results by ROM, input case, action and player."""

import argparse
import hashlib
import json
from pathlib import Path


PLAYERS = ("p1", "p2")


def digest(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def load(path, sha):
    data = json.loads(path.read_bytes())
    if data["rom_sha256"] != sha:
        raise ValueError(f"Different ROM in {path}")
    return data


def first_free(samples, player, start):
    last_tick = samples[start]["logic_tick"]
    for row in samples[start:]:
        if row["logic_tick"] < last_tick:
            break
        if row[player]["can_act"]:
            return row["logic_tick"]
        last_tick = row["logic_tick"]
    return None


def run_cases(folder, sha):
    identity = load(folder / "input.json", sha)
    stepped = load(folder / "stepped-closed.json", sha)
    if stepped["state"] != "closed" or stepped["session_id"] != identity["session_id"]:
        raise ValueError(f"Stepped session is open or different in {folder}")
    runtime_path = folder / "runtime.json"
    runtime = None
    if runtime_path.is_file():
        observed = load(runtime_path, sha)
        if observed["session_id"] != identity["session_id"]:
            raise ValueError(f"Different runtime session in {folder}")
        sat = [observed["sat"], *observed["phase_sat"].values()]
        runtime = dict(overruns=observed["overruns"], fault=observed["fault"],
                       worst_vdp_gap=observed["worst_vdp_gap"],
                       peak_sat=max(row["entries"] for row in sat),
                       peak_scanline=max(row["max_per_scanline"] for row in sat))
    exposure_path = folder / "contact-pixels.json"
    exposure = {}
    if exposure_path.is_file():
        evidence = load(exposure_path, sha)
        if evidence["session_id"] != identity["session_id"]:
            raise ValueError(f"Different exposure session in {folder}")
        exposure = {(item["player"], item["logic_tick"]): item["scanout"]
                    for item in evidence["exposures"]}
        for scanout in exposure.values():
            if scanout and digest(folder / scanout["file"]) != scanout["sha256"]:
                raise ValueError("Framebuffer file differs from its exposure receipt")
    samples = identity["samples"]
    contacts = []
    for case, (begin, end) in identity["cases"].items():
        for index in range(begin, end):
            row = samples[index]
            before = samples[max(index - 1, 0)]
            for side, player in enumerate(PLAYERS):
                opponent = PLAYERS[1 - side]
                actor, victim = row[player], row[opponent]
                if actor["contact"] == 0:
                    continue
                contacts.append(dict(
                    case=case, actor=player, action=row["actions"][side], contact=actor["contact"],
                    vdp_frame=row["frame"], logic_tick=row["logic_tick"], input=actor["keys_consumed"],
                    victim_state_before=before[opponent]["state"], victim_state=victim["state"],
                    victim_reaction=row["reactions"][1 - side],
                    damage=before[opponent]["life"] - victim["life"],
                    attacker_free_tick=first_free(samples, player, index),
                    victim_free_tick=first_free(samples, opponent, index),
                    attacker_pose=[actor[key] for key in
                                   ("pose_requested", "pose_resident", "pose_presented")],
                    victim_pose=[victim["pose_requested"], victim["pose_presented"]],
                    victim_pivot_delta=[new - old for new, old in
                                        zip(victim["pivot"], before[opponent]["pivot"])],
                    offense=actor["boxes"]["attack"], vulnerability=victim["boxes"]["hurt"],
                    scanout=exposure.get((player, row["logic_tick"])),
                ))
    path = folder / "continuous/round-continuo.json"
    live = load(path, sha) if path.is_file() else None
    if live:
        closed = load(folder / "continuous-closed.json", sha)
        if closed["state"] != "closed" or closed["session_id"] != live["session_id"]:
            raise ValueError(f"Continuous session is open or different in {folder}")
        if (digest(path.with_suffix(".mp4")) != live["video_sha256"] or
            digest(path.parent / live["pcm"]["file"]) != live["pcm"]["sha256"]):
            raise ValueError(f"Continuous capture differs from its receipt in {folder}")
        live = {key: live[key] for key in ("session_id", "same_contacts", "actual_contacts",
                                          "guards", "same_guards", "ntsc_windows", "cadence",
                                          "pcm", "video_sha256") if key in live}
    return dict(folder=folder.name, session_id=identity["session_id"], contacts=contacts,
                runtime=runtime, continuous=live)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("scenarios", type=Path, nargs="+")
    args = parser.parse_args()
    sha = digest(args.rom)
    scenarios = [run_cases(folder, sha) for folder in args.scenarios]
    args.output.write_text(json.dumps(dict(rom_sha256=sha, scenarios=scenarios), indent=2) + "\n")


if __name__ == "__main__":
    main()
