#!/usr/bin/env python3
"""Le o bloco B.2a + contrato SMRT de uma sessao isolada, sem DAP.

Uso: read_probes.py <session_id> [--out file.json]
Leituras pos-selo apenas (o chamador decide quando ler apos done=1).
"""
import json
import sys
import os

sys.path.insert(0, "/mnt/sdcard/Projects/SMSForge/tools/sms_wrapper")
from session_bridge.isolated import load, MemoryReader  # noqa: E402

PROBES = [
    ("desired_p1", 0xC862, 2), ("desired_p2", 0xC864, 2),
    ("resident_p1", 0xC866, 2), ("resident_p2", 0xC868, 2),
    ("submit_p1", 0xC86A, 2), ("submit_p2", 0xC86C, 2),
    ("present_p1", 0xC86E, 2), ("present_p2", 0xC870, 2),
    ("wait_p1", 0xC872, 2), ("wait_p2", 0xC874, 2),
    ("overflow_p1", 0xC876, 2), ("overflow_p2", 0xC878, 2),
    ("superseded_p1", 0xC87A, 2), ("superseded_p2", 0xC87C, 2),
    ("sat_om_p1", 0xC87E, 2), ("sat_om_p2", 0xC880, 2),
    ("backlog_max", 0xC882, 2),
    ("upload_maxvbl", 0xC884, 2),
    ("vbl_entry", 0xC886, 1), ("vbl_exit_max", 0xC887, 1),
    ("disp_p1", 0xC818, 2), ("disp_p2", 0xC81A, 2),
    ("smrt_frame", 0xC8F0, 2),
    ("vline_min", 0xC8D2, 1), ("vline", 0xC8EA, 1), ("vovf", 0xC8EB, 2),
    ("phase", 0xC8ED, 1), ("worst_done", 0xC8EE, 1),
    # Lote B.2a: instrumento de estagios (linhas por etapa, doc/25 §90) +
    # bytes novos (uploaded_pairs x 64 B) + no-evict (evict_events) +
    # input->contato->recovery no mesmo selo (M2/wave-5a).
    ("stage_up_max", 0xC888, 1), ("stage_slice_max", 0xC889, 1),
    ("stage_sat_delta_max", 0xC88A, 1), ("entry_max", 0xC88B, 1),
    ("vbl_mid", 0xC88C, 1),
    # Lote B.2b: contrato SAT-64 (0xC88D..0xC897).
    ("add_p1_max", 0xC88D, 1), ("add_p2_max", 0xC88E, 1),
    ("add_total_max", 0xC88F, 1), ("sat_frames", 0xC890, 2),
    ("sat_frames_p1", 0xC892, 2), ("sat_frames_p2", 0xC894, 2),
    ("add_cur_p1", 0xC896, 1), ("add_cur_p2", 0xC897, 1),
    # Lote B.2b v3: instrumento do hibrido BG (0xC898..0xC89F). Escopo da
    # sessao inteira: cells/bytes/frames acumulam; overflow reprova o candidato.
    ("bg_cells_max", 0xC898, 1),
    ("bg_bytes_max", 0xC89A, 2), ("bg_frames", 0xC89C, 2),
    ("bg_overflow", 0xC89E, 2),
    # Lote B.2b-3b: flush PNT movido para o inicio do VBlank; sondas separadas
    # de flush e copySAT (linhas), diagnostico de pacing (u8).
    ("stage_flush_max", 0xC8A0, 1),
    ("stage_satcopy_max", 0xC8A1, 1),
    ("uploaded_pairs", 0xC80A, 2), ("evict_events", 0xC80C, 2),
    ("used_pairs_max", 0xC816, 2), ("free_pairs_min", 0xC814, 2),
    ("hit_events", 0xC826, 2), ("damage_p1", 0xC82A, 2),
    ("damage_p2", 0xC82C, 2), ("ko_events", 0xC834, 2),
    ("clsn_checks", 0xC836, 2),
]


def main():
    session = sys.argv[1]
    root, meta = load(session)
    reader = MemoryReader(root)
    out = {"session_id": meta["session_id"],
           "rom_sha256": meta["rom_sha256"], "probes": {}}
    for name, addr, width in PROBES:
        if width == 1:
            out["probes"][name] = reader.read_byte(addr)
        else:
            out["probes"][name] = reader.read_word(addr)
    if "--out" in sys.argv:
        path = sys.argv[sys.argv.index("--out") + 1]
        with open(path, "w") as fh:
            json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
