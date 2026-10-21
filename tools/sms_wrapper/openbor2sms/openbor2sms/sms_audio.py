"""Reautoria declarativa dos tres SFX O3/D11, sem conversao WAV -> PSG.

CLI: python3 -m openbor2sms.sms_audio --pak GAL.pak --expect-pak-sha256 HEX
     --expect-pak-bytes N --out DIRETORIO_CANDIDATO
     python3 -m openbor2sms.sms_audio --self-check

Somente autoria/emissao offline. Nao integra runtime, compila ou aprova som.
O header deve ser incluido UMA vez numa unidade de dados fixa (bancos 0..1).
O coordenador deve conferir enderecos < 0x8000 no .map: PSGSFXFrame nao troca
bancos, mesmo com PSGLIB_MULTIBANK; slot2 pertence ao streaming de poses.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import wave

from .pak import build_pak32, find_entry, read_entry, read_index


REPO = Path(__file__).resolve().parents[4]
DRIVER_FILES = {
    "sdk/devkitSMS/PSGlib/PSGlib.h":
        "89391c5e48b4d7ad5bc71fe840c531f9701ad705a0ba00252aacc382a75fa7f4",
    "sdk/devkitSMS-upstream/PSGlib/src/PSGlib.c":
        "d285ee5f901c7bc6a5609dc778217be1f47fb76d228833c5970766f9196364ab",
}
AUTHOR = "Codex, worker audio PSG OpenBOR pos-M6 (autoria assistida por IA)"
CHANNEL = 3
MASK = 0x02  # PSGlib.h: SFX_CHANNEL3; nao e (1 << CHANNEL).
MASK_NAME = "SFX_CHANNEL3"
HEADER_PATH = "inc/o3/psg_sfx.h"
MANIFEST_PATH = "doc/audio_provenance_manifest.json"
REFERENCE_ROOT = "data/source_openbor/gal_audio"


@dataclass(frozen=True)
class NoiseEvent:
    """Instante em ticks do driver, atenuacao 0..15, modo branco 4..6.

    None mantem o modo, evitando resetar o LFSR a cada escrita de volume.
    Modos 3/7 dependem de tone2 e nao pertencem a este contrato de um canal.
    """

    tick: int
    attenuation: int
    noise_mode: int | None = None


@dataclass(frozen=True)
class SfxSpec:
    symbol: str
    source_member: str
    trigger: str
    priority: int
    duration_ticks: int
    intent: str
    events: tuple[NoiseEvent, ...]


# Partitura autorada em ticks: ataque = sopro curto; impacto = transiente
# forte com cauda; queda = batida grave com decaimento mais longo. Sao escolhas
# de adaptacao sem comparacao auditiva, nao extracao de pitch/envelope do WAV.
SFX = (
    SfxSpec("sfx_attack", "data/sounds/att1.wav", "accepted_attack_once", 1, 6,
            "Sopro curto de golpe; brilho inicial e cauda breve.",
            (NoiseEvent(0, 3, 4), NoiseEvent(1, 5, 5), NoiseEvent(3, 9, 6),
             NoiseEvent(5, 12), NoiseEvent(6, 15))),
    SfxSpec("sfx_impact", "data/sounds/hit1.wav", "confirmed_hit_once", 2, 10,
            "Transiente de contato forte com cauda descendente em volume.",
            (NoiseEvent(0, 0, 4), NoiseEvent(1, 3, 5), NoiseEvent(3, 6, 6),
             NoiseEvent(6, 10), NoiseEvent(9, 13), NoiseEvent(10, 15))),
    SfxSpec("sfx_fall", "data/sounds/fall.wav", "knockdown_ground_contact_once",
            3, 18, "Batida de queda no solo; cauda de ruido mais longa.",
            (NoiseEvent(0, 1, 5), NoiseEvent(2, 4, 6), NoiseEvent(5, 7),
             NoiseEvent(9, 10), NoiseEvent(14, 13), NoiseEvent(18, 15))),
)


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def validate_spec(spec: SfxSpec) -> None:
    if type(spec.duration_ticks) is not int or not 1 <= spec.duration_ticks <= 45:
        raise ValueError("duration_ticks deve estar em 1..45")
    if type(spec.priority) is not int or not 1 <= spec.priority <= 255:
        raise ValueError("priority deve estar em 1..255")
    if (not spec.events or spec.events[0].tick != 0
            or spec.events[0].noise_mode is None
            or spec.events[0].attenuation == 15):
        raise ValueError("onset deve inicializar modo e volume audivel em tick 0")
    previous = -1
    for event in spec.events:
        if type(event.tick) is not int or not previous < event.tick <= spec.duration_ticks:
            raise ValueError("eventos devem ser estritamente crescentes e dentro da duracao")
        if type(event.attenuation) is not int or not 0 <= event.attenuation <= 15:
            raise ValueError("atenuacao deve estar em 0..15")
        if event.noise_mode is not None and (
                type(event.noise_mode) is not int or event.noise_mode not in (4, 5, 6)):
            raise ValueError("somente ruido branco independente de tone2 (4..6)")
        if event.tick < spec.duration_ticks and event.attenuation == 15:
            raise ValueError("mudo somente no terminal deste contrato")
        previous = event.tick
    terminal = spec.events[-1]
    if (terminal.tick != spec.duration_ticks or terminal.attenuation != 15
            or terminal.noise_mode is not None):
        raise ValueError("terminal deve silenciar no tick da duracao, sem reset do ruido")


def encode_sfx(spec: SfxSpec) -> bytes:
    """WAIT 0x38+n consome 1+n chamadas; 0x00 encerra PSGSFXPlay (sem loop)."""
    validate_spec(spec)
    stream = bytearray()
    tick = 0
    for event in spec.events:
        gap = event.tick - tick
        while gap:
            hold = min(8, gap)
            stream.append(0x38 + hold - 1)
            gap -= hold
        if event.noise_mode is not None:
            stream.append(0xE0 | event.noise_mode)
        stream.append(0xF0 | event.attenuation)
        tick = event.tick
    stream.append(0x00)
    return bytes(stream)


def inspect_stream(stream: bytes) -> dict:
    """Modelo restrito do ramo SFX do driver lido, nao emulador do SN76489.

    Rejeita loop points, substrings, dados soltos e escritas em outro canal.
    tick zero e a primeira chamada. O terminal e processado na chamada D+1.
    """
    tick = 0
    events = []
    mode = None
    attenuation = None
    for offset, byte in enumerate(stream):
        if byte == 0:
            if offset != len(stream) - 1 or not tick or attenuation != 15:
                raise ValueError("terminal ausente, prematuro, nao mudo ou com bytes posteriores")
            return {"duration_ticks": tick, "driver_calls_through_stop": tick + 1,
                    "channel": CHANNEL, "mask": MASK, "events": events}
        if 0x38 <= byte <= 0x3F:
            if mode is None or attenuation is None:
                raise ValueError("WAIT antes do onset")
            tick += 1 + (byte & 7)
        elif 0xE4 <= byte <= 0xE6:
            mode = byte & 7
            events.append({"tick": tick, "register": "noise", "value": mode})
        elif 0xF0 <= byte <= 0xFF:
            if mode is None:
                raise ValueError("volume sem modo de ruido inicializado")
            attenuation = byte & 15
            events.append({"tick": tick, "register": "attenuation", "value": attenuation})
        else:
            raise ValueError(f"byte fora do contrato ch3: 0x{byte:02x}")
    raise ValueError("stream sem terminador 0x00")


def driver_contract() -> list[dict]:
    records = []
    for relative, expected in DRIVER_FILES.items():
        data = (REPO / relative).read_bytes()
        if sha256(data) != expected:
            raise ValueError(f"driver/header mudou; revisar semantica antes de emitir: {relative}")
        records.append({"file": relative, "sha256": expected, "bytes": len(data)})
    return records


def _wav_info(blob: bytes) -> dict:
    try:
        with wave.open(io.BytesIO(blob), "rb") as source:
            count = source.getnframes()
            if not count or len(source.readframes(count)) != (
                    count * source.getnchannels() * source.getsampwidth()):
                raise ValueError("WAV vazio ou truncado")
            return {"format": "PCM_WAV_reference_only", "samples": count,
                    "sample_rate": source.getframerate(), "channels": source.getnchannels(),
                    "sample_width_bytes": source.getsampwidth()}
    except (wave.Error, EOFError) as exc:
        raise ValueError(f"referencia nao e WAV PCM legivel: {exc}") from exc


def _header() -> bytes:
    lines = ["/* Gerado por openbor2sms.sms_audio; reautoria PSG O3/D11.",
             " * Incluir UMA vez em unidade fixa dos bancos 0..1, nunca BANK2+.",
             " * Confirmar arrays inteiros abaixo de 0x8000 no .map.",
             " * PSGSFXFrame le ponteiro direto; slot2 e do uploader de poses.",
             " * SIZE = bytes; DURATION_TICKS = intervalos ate o mute/stop.",
             " * Prioridade deve ser aplicada pelo owner; PSGlib nao arbitra.",
             " */", "#ifndef O3_PSG_SFX_H", "#define O3_PSG_SFX_H",
             '#include "PSGlib.h"',
             "#if SFX_CHANNEL3 != 0x02", '#error "Mascara PSGlib divergente"', "#endif"]
    for spec in SFX:
        data = encode_sfx(spec)
        prefix = spec.symbol.upper()
        lines.extend([f"#define {prefix}_SIZE {len(data)}",
                      f"#define {prefix}_DURATION_TICKS {spec.duration_ticks}",
                      f"#define {prefix}_PRIORITY {spec.priority}",
                      f"#define {prefix}_MASK SFX_CHANNEL3",
                      f"static const unsigned char {spec.symbol}[{prefix}_SIZE] = {{",
                      "    " + ", ".join(f"0x{byte:02X}" for byte in data), "};"])
    lines.append("#endif")
    return ("\n".join(lines) + "\n").encode("ascii")


def generate(pak_blob: bytes, *, expected_sha256: str, expected_bytes: int,
             author: str = AUTHOR) -> dict[str, bytes]:
    """Gera um bundle em memoria; nenhum caminho do consumidor e implicito."""
    if sha256(pak_blob) != expected_sha256 or len(pak_blob) != expected_bytes:
        raise ValueError("PAK diverge do SHA-256/tamanho esperado")
    if not author.strip():
        raise ValueError("autoria explicita obrigatoria")
    drivers = driver_contract()
    index = read_index(pak_blob)
    outputs = {HEADER_PATH: _header()}
    assets = []
    for spec in SFX:
        reference = read_entry(pak_blob, find_entry(index, spec.source_member))
        wav = _wav_info(reference)
        reference_path = f"{REFERENCE_ROOT}/{spec.source_member}"
        outputs[reference_path] = reference
        data = encode_sfx(spec)
        inspection = inspect_stream(data)
        if inspection["duration_ticks"] != spec.duration_ticks:
            raise ValueError("duracao emitida diverge da partitura")
        relative = f"res/audio/{spec.symbol}.psg"
        outputs[relative] = data
        assets.append({
            "file": relative, "symbol": spec.symbol, "bytes": len(data),
            "sha256": sha256(data), "kind": "sfx", "author": author,
            "origin": "reautoria/adaptacao PSG declarativa do papel sonoro OpenBOR",
            "classification": "adapted", "fidelity_claim": False,
            "adaptation": "WAV do PAK e referencia de papel, nao PSG pronto. "
                          "Envelope e timbre autorados; sem transcricao automatica "
                          "ou comparacao auditiva com a fonte.",
            "reference": {"file": reference_path, "sha256": sha256(reference),
                          "bytes": len(reference), "pak_member": spec.source_member,
                          "wav": wav},
            "channels": MASK_NAME, "channel_indices": [CHANNEL], "mask": MASK,
            "priority": spec.priority, "trigger": spec.trigger, "intent": spec.intent,
            "duration_ticks": spec.duration_ticks,
            "duration_ms_at_60_calls_per_second": {"numerator": spec.duration_ticks * 1000,
                                                    "denominator": 60},
            "duration_ms_at_50_calls_per_second": spec.duration_ticks * 20,
            "driver_calls_through_stop": inspection["driver_calls_through_stop"],
            "events": [asdict(event) for event in spec.events],
            "encoded_events": inspection["events"],
        })
    manifest = {
        "schema": "openbor2sms.audio_provenance.v1", "contract": "O3/D11/M7",
        "author": author, "claim_ceiling": "offline_generation_and_stream_checks_only",
        "source_archive": {"sha256": expected_sha256, "bytes": expected_bytes},
        "generator": {"file": "tools/sms_wrapper/openbor2sms/openbor2sms/sms_audio.py",
                      "sha256": sha256(Path(__file__).read_bytes())},
        "driver_sources": drivers,
        "header": {"file": HEADER_PATH, "sha256": sha256(outputs[HEADER_PATH]),
                   "bytes": len(outputs[HEADER_PATH])},
        "assets": assets,
        "runtime_contract": {
            "implementation_status": "coordinator_integration_required",
            "music": "outside_O3", "channels": MASK_NAME, "mask": MASK,
            "placement": {"banks": [0, 1], "address_end_exclusive": 32768,
                          "verify_in_linker_map": True, "slot2_owner": "pose_stream"},
            "clock": "PSGSFXFrame exactly once per VBlank; never in both ISR and main",
            "duration": "ticks are intervals from onset tick 0 to mute/stop tick D; "
                        "D+1 driver calls include the terminal call; PAL not normalized",
            "arbitration": "one SFX owner; fall(3)>impact(2)>attack(1); choose highest "
                           "pending per tick before PSGSFXPlay; equal priority keeps current; "
                           "lower/equal dropped, no queue; higher preempts without resume; "
                           "clear priority when PSGSFXGetStatus()==PSG_STOPPED",
            "restore": "PSGSFXPlay calls PSGSFXStop before replacing; terminal 0x00 "
                       "calls PSGSFXStop and releases ch3; no music means mute. "
                       "Music restoration must be revalidated if music enters scope.",
            "pause_restart": "pause: freeze owner and PSGSFXFrame, PSGSilenceChannels; "
                             "resume: PSGRestoreVolumes then resume ticks; "
                             "restart: PSGSFXStop and clear owner priority/pending events",
            "attenuation": "initialize PSGSetSFXVolumeAttenuation(0) before playback",
            "loop": "PSGSFXPlay only; never PSGSFXPlayLoop or PSGPlay for these streams",
        },
        "validation": {"host_streams": "checked", "runtime": "not_run",
                       "audition": "not_run", "budget": "not_run"},
    }
    outputs[MANIFEST_PATH] = (json.dumps(manifest, ensure_ascii=False, sort_keys=True,
                                        indent=2) + "\n").encode("utf-8")
    return outputs


def write_bundle(destination: Path, outputs: dict[str, bytes]) -> None:
    """Emissao idempotente; nunca substitui um artefato existente divergente."""
    root = destination.resolve()
    targets = []
    for relative, blob in outputs.items():
        target = root / relative
        if root not in target.resolve().parents:
            raise ValueError("saida escapa do diretorio candidato")
        if target.exists() and target.read_bytes() != blob:
            raise ValueError(f"saida existente diverge; use candidato novo: {relative}")
        targets.append((target, blob))
    for target, blob in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with target.open("xb") as handle:
                handle.write(blob)


def self_check() -> int:
    # Oracle manual: 3 ticks de hold -> 0x3A -> mute+end na quarta chamada.
    fixture = SfxSpec("test", "test.wav", "test", 1, 3, "fixture",
                      (NoiseEvent(0, 2, 4), NoiseEvent(3, 15)))
    if encode_sfx(fixture) != bytes((0xE4, 0xF2, 0x3A, 0xFF, 0)):
        raise ValueError("self-check: WAIT/onset/terminal divergente")
    for invalid in (b"", b"\xe4\xf2\x38", b"\xe4\xf2\x38\x00",
                    b"\xe7\xf2\x38\xff\x00", b"\xc0\x40\x38\xff\x00",
                    b"\xe4\xf2\x38\xff\x00\x38"):
        try:
            inspect_stream(invalid)
        except ValueError:
            pass
        else:
            raise ValueError("self-check: stream invalido aceito")
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as handle:
        handle.setparams((1, 1, 8000, 0, "NONE", "not compressed"))
        handle.writeframes(bytes((128, 140, 128, 116)))
    pak_blob = build_pak32([(s.source_member, wav_buffer.getvalue()) for s in SFX])
    options = {"expected_sha256": sha256(pak_blob), "expected_bytes": len(pak_blob)}
    outputs = generate(pak_blob, **options)
    if outputs != generate(pak_blob, **options):
        raise ValueError("self-check: emissao nao deterministica")
    for spec in SFX:
        info = inspect_stream(outputs[f"res/audio/{spec.symbol}.psg"])
        if (info["duration_ticks"], info["mask"]) != (spec.duration_ticks, MASK):
            raise ValueError("self-check: duracao/mask divergente")
    with tempfile.TemporaryDirectory(prefix="openbor_sms_audio_") as temporary:
        write_bundle(Path(temporary), outputs)
        write_bundle(Path(temporary), outputs)
        for name, data in outputs.items():
            if (Path(temporary) / name).read_bytes() != data:
                raise ValueError("self-check: bundle divergente")
    print("[SELF-CHECK OK] sms_audio: stream, WAIT, terminal, canal, determinismo, bundle tmp")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--pak", type=Path)
    parser.add_argument("--expect-pak-sha256")
    parser.add_argument("--expect-pak-bytes", type=int)
    parser.add_argument("--out", type=Path, help="raiz explicita de bundle candidato; sem overwrite")
    parser.add_argument("--author", default=AUTHOR)
    args = parser.parse_args(argv)
    try:
        if args.self_check:
            return self_check()
        if any(value is None for value in (args.pak, args.expect_pak_sha256,
                                           args.expect_pak_bytes, args.out)):
            parser.error("--pak, --expect-pak-sha256, --expect-pak-bytes e --out obrigatorios")
        outputs = generate(args.pak.read_bytes(), expected_sha256=args.expect_pak_sha256,
                           expected_bytes=args.expect_pak_bytes, author=args.author)
        write_bundle(args.out, outputs)
    except (OSError, ValueError) as exc:
        print(f"[FAIL] sms_audio: {exc}", file=sys.stderr)
        return 1
    print(f"[OK] 3 SFX O3/D11 -> {args.out}; runtime/audicao/budget pendentes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
