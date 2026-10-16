# Ported from SGDK-Forge (donor), read-only source.
#   donor path : tools/openbor2sgdk_forge/openbor2sgdk_forge/model_text.py
#   donor sha256: 3703e71ba6ade16474f0d3a3bb81f70730ebe1beeb1923710b3f3dec0e6d2466
#   license    : MIT (SGDK-Forge LICENSE, sha256 0b685fab1e0d2e0a9f85a4356a91c7bb16126be7b06e899f6cfed155cad2cf24)
#   port date  : 2026-10-15 (SMSForge openbor2sms front-end O1)
# Body below is byte-identical to the donor file (verified by cmp at port time);
# no behavioral change.
"""Directive parser for OpenBOR model and level text.

The grammar is the whitespace-separated command file used by the modules
under study. Every non-comment line becomes a directive with its source
line. Known commands update animation state; unknown commands are kept.
Nothing is dropped to make a later build succeed.

Delay, attack and bbox persistence follow the file shape observed in the
pilot (a command stays in force until another command replaces it, and a
new anim clears that state). This is not a measurement of the distributed
executable.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Directive:
    line: int
    command: str
    args: list[str]
    raw: str


@dataclass
class AttackDef:
    line: int
    slot: int
    x: int
    y: int
    right: int
    down: int
    damage: int
    power: int | None
    block: int | None
    noflash: int | None
    pausetime: int | None
    depth: int | None

    def cleared(self) -> bool:
        return self.right == 0 and self.down == 0 and self.damage == 0


@dataclass
class FrameDef:
    line: int
    path: str
    delay: int | None
    offset: tuple[int, int] | None
    bbox: tuple[int, int, int, int] | None
    attacks: list[AttackDef]
    script_bound: bool


@dataclass
class ScriptBlock:
    start_line: int
    end_line: int
    body: list[str]


@dataclass
class AnimDef:
    line: int
    name: str
    loop: int
    frames: list[FrameDef] = field(default_factory=list)
    directives: list[Directive] = field(default_factory=list)
    scripts: list[ScriptBlock] = field(default_factory=list)

    def directive_commands(self) -> list[str]:
        return [item.command for item in self.directives]


@dataclass
class ModelFile:
    path: str
    header: list[Directive]
    anims: list[AnimDef]
    issues: list[str]

    def anim(self, name: str) -> AnimDef | None:
        key = name.lower()
        for item in self.anims:
            if item.name.lower() == key:
                return item
        return None

    def header_value(self, command: str) -> list[str] | None:
        key = command.lower()
        for item in self.header:
            if item.command == key:
                return item.args
        return None


@dataclass
class SpawnDef:
    line: int
    name: str
    at: int | None
    health: int | None
    coords: tuple[int, int] | None
    flip: int | None
    extra: list[Directive]


@dataclass(frozen=True)
class PlayerStartDef:
    slot: int
    line: int
    x: int
    z: int
    y: int
    raw: str


@dataclass
class LevelFile:
    path: str
    header: list[Directive]
    spawns: list[SpawnDef]
    issues: list[str]
    timeline: list[Directive] = field(default_factory=list)
    player_starts: list[PlayerStartDef] = field(default_factory=list)

    def header_value(self, command: str) -> list[str] | None:
        key = command.lower()
        for item in self.header:
            if item.command == key:
                return item.args
        return None


def strip_comment(line: str) -> str:
    """Drop from the first unquoted '#'. OpenBOR treats that as a line comment."""
    in_quote = False
    for index, char in enumerate(line):
        if char == '"':
            in_quote = not in_quote
        elif char == "#" and not in_quote:
            return line[:index]
    return line


def tokenize(line: str) -> list[str]:
    return strip_comment(line).split()


def _int_token(token: str) -> int | None:
    try:
        return int(token, 10)
    except ValueError:
        return None


def _optional_int(args: list[str], index: int) -> int | None:
    if index >= len(args):
        return None
    return _int_token(args[index])


def _parse_attack(line_no: int, command: str, args: list[str], issues: list[str]) -> AttackDef | None:
    slot_text = command[6:]
    slot = 1 if slot_text == "" else _int_token(slot_text)
    if slot is None:
        issues.append(f"{line_no}: attack slot is not an integer in '{command}'")
        return None
    numbers = [_int_token(token) for token in args]
    if len(numbers) < 5 or any(value is None for value in numbers[:5]):
        # A short run of zeros is the clear idiom with the tail omitted.
        # A short run that contains a non-zero is not a box and not a clear.
        if numbers and all(value == 0 for value in numbers):
            return AttackDef(
                line=line_no,
                slot=slot,
                x=0,
                y=0,
                right=0,
                down=0,
                damage=0,
                power=None,
                block=None,
                noflash=None,
                pausetime=None,
                depth=None,
            )
        issues.append(f"{line_no}: attack needs five integers (x y right down damage)")
        return None
    return AttackDef(
        line=line_no,
        slot=slot,
        x=numbers[0],
        y=numbers[1],
        right=numbers[2],
        down=numbers[3],
        damage=numbers[4],
        power=_optional_int(args, 5),
        block=_optional_int(args, 6),
        noflash=_optional_int(args, 7),
        pausetime=_optional_int(args, 8),
        depth=_optional_int(args, 9),
    )


def parse_model(text: str, path: str = "<memory>") -> ModelFile:
    model = ModelFile(path=path, header=[], anims=[], issues=[])
    current: AnimDef | None = None
    offset: tuple[int, int] | None = None
    bbox: tuple[int, int, int, int] | None = None
    delay: int | None = None
    attacks: dict[int, AttackDef] = {}
    in_script = False
    script: ScriptBlock | None = None
    script_pending = False

    def reset_anim_state() -> None:
        nonlocal offset, bbox, delay, attacks, script_pending
        offset = None
        bbox = None
        delay = None
        attacks = {}
        script_pending = False

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        raw = raw_line.rstrip("\r")
        if in_script:
            tokens = tokenize(raw)
            command = tokens[0].lower() if tokens else ""
            if command == "@end_script":
                if script is not None:
                    script.end_line = line_no
                    if current is not None:
                        current.scripts.append(script)
                        current.directives.append(Directive(line_no, command, tokens[1:], raw))
                in_script = False
                script = None
                script_pending = True
            elif script is not None:
                script.body.append(raw)
            continue

        tokens = tokenize(raw)
        if not tokens:
            continue
        command = tokens[0].lower()
        args = tokens[1:]
        directive = Directive(line_no, command, args, raw)

        if command == "@script":
            in_script = True
            script = ScriptBlock(start_line=line_no, end_line=line_no, body=[])
            if current is not None:
                current.directives.append(directive)
            else:
                model.header.append(directive)
            continue

        if command == "anim":
            if not args:
                model.issues.append(f"{line_no}: anim without a name")
                continue
            current = AnimDef(line=line_no, name=args[0], loop=0)
            model.anims.append(current)
            reset_anim_state()
            continue

        if current is None:
            model.header.append(directive)
            continue

        current.directives.append(directive)
        if command == "loop":
            value = _optional_int(args, 0)
            if value is None:
                model.issues.append(f"{line_no}: loop needs an integer")
            else:
                current.loop = value
        elif command == "offset":
            x_value = _optional_int(args, 0)
            y_value = _optional_int(args, 1)
            if x_value is None or y_value is None:
                model.issues.append(f"{line_no}: offset needs two integers")
            else:
                offset = (x_value, y_value)
        elif command == "delay":
            value = _optional_int(args, 0)
            if value is None:
                model.issues.append(f"{line_no}: delay needs an integer")
            else:
                delay = value
        elif command == "bbox":
            coords = [_optional_int(args, index) for index in range(4)]
            if any(value is None for value in coords):
                model.issues.append(f"{line_no}: bbox needs four integers")
            else:
                bbox = (coords[0], coords[1], coords[2], coords[3])
        elif command == "frame":
            if not args:
                model.issues.append(f"{line_no}: frame without a path")
                continue
            current.frames.append(
                FrameDef(
                    line=line_no,
                    path=args[0].replace("\\", "/"),
                    delay=delay,
                    offset=offset,
                    bbox=bbox,
                    attacks=[attacks[slot] for slot in sorted(attacks)],
                    script_bound=script_pending,
                )
            )
            script_pending = False
        elif command == "attack" or (command.startswith("attack") and command[6:].isdigit()) or command == "shock" or (command.startswith("shock") and len(command) > 5 and command[5:].isdigit()):
            # shock uses the attack box layout. The stun reaction is not played.
            parse_command = ("attack" + command[5:]) if command.startswith("shock") else command
            parsed = _parse_attack(line_no, parse_command, args, model.issues)
            if parsed is None:
                continue
            if parsed.cleared():
                attacks.pop(parsed.slot, None)
            else:
                attacks[parsed.slot] = parsed
        elif command == "@end_script":
            model.issues.append(f"{line_no}: @end_script without @script")

    if in_script:
        model.issues.append(f"{script.start_line if script else 0}: @script is not closed")
    return model


def parse_level(text: str, path: str = "<memory>") -> LevelFile:
    level = LevelFile(path=path, header=[], spawns=[], issues=[])
    spawn: SpawnDef | None = None

    def close_spawn() -> None:
        nonlocal spawn
        if spawn is None:
            return
        if spawn.at is None:
            level.issues.append(
                f"{spawn.line}: spawn {spawn.name} is not followed by its own at directive"
            )
        level.spawns.append(spawn)
        spawn = None

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        tokens = tokenize(raw_line.rstrip("\r"))
        if not tokens:
            continue
        command = tokens[0].lower()
        args = tokens[1:]
        directive = Directive(line_no, command, args, raw_line.rstrip("\r"))
        level.timeline.append(directive)
        if command == "spawn":
            close_spawn()
            if not args:
                level.issues.append(f"{line_no}: spawn without a name")
                continue
            spawn = SpawnDef(
                line=line_no,
                name=args[0],
                at=None,
                health=None,
                coords=None,
                flip=None,
                extra=[],
            )
            continue
        if command == "at":
            value = _optional_int(args, 0)
            if value is None:
                level.issues.append(f"{line_no}: at needs an integer")
            else:
                if spawn is not None:
                    spawn.at = value
                    close_spawn()
            continue
        if command in {"spawn1", "spawn2", "spawn3", "spawn4"}:
            if len(args) != 3:
                level.issues.append(
                    f"{line_no}: player-start {command} needs exactly three integers (x z y)"
                )
                level.header.append(directive)
                continue
            values = [_int_token(value) for value in args]
            if any(value is None for value in values):
                level.issues.append(
                    f"{line_no}: player-start {command} fields x z y must be integers"
                )
                level.header.append(directive)
                continue
            slot = int(command[-1])
            if any(item.slot == slot for item in level.player_starts):
                level.issues.append(f"{line_no}: duplicate player-start slot {slot}")
            level.player_starts.append(
                PlayerStartDef(
                    slot=slot,
                    line=line_no,
                    x=values[0],
                    z=values[1],
                    y=values[2],
                    raw=directive.raw,
                )
            )
            level.header.append(directive)
            continue
        if spawn is not None:
            spawn.extra.append(directive)
            if command == "health":
                spawn.health = _optional_int(args, 0)
            elif command == "coords":
                x_value = _optional_int(args, 0)
                z_value = _optional_int(args, 1)
                if x_value is None or z_value is None:
                    level.issues.append(f"{line_no}: coords needs x and z integers")
                else:
                    spawn.coords = (x_value, z_value)
            elif command == "flip":
                spawn.flip = _optional_int(args, 0)
            continue
        level.header.append(directive)

    close_spawn()
    return level


def parse_models_index(text: str) -> list[tuple[str, str, int]]:
    """Return (alias, path, line) from load/know lines that carry a text path."""
    found: list[tuple[str, str, int]] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        tokens = tokenize(raw_line.rstrip("\r"))
        if len(tokens) < 3:
            continue
        if tokens[0].lower() not in {"load", "know"}:
            continue
        path = tokens[2].replace("\\", "/")
        if "/" not in path and not path.lower().endswith(".txt"):
            continue
        found.append((tokens[1], path, line_no))
    return found


def resolve_alias(entries: list[tuple[str, str, int]], alias: str) -> str | None:
    key = alias.lower()
    for name, path, _line in entries:
        if name.lower() == key:
            return path
    return None
