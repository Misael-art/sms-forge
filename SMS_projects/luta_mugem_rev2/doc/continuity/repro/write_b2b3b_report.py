#!/usr/bin/env python3
import json
from pathlib import Path

OUT = Path('/mnt/sdcard/Projects/SMSForge/SMS_projects/luta_mugem_rev2/out/logs/runs/20261021T025418Z_b2b3b_sat_policy.json')

doc = {
 "schema": 1,
 "batch": "B2b-3b",
 "title": "Quota de SAT 6+2 passa 8/linha mas custa 22% do pacing e viola §129; 5+3 é o mínimo compatível e ainda falha o pacing (-12,4%)",
 "generated_at": "2026-10-21T02:54:18Z",
 "mandate": {
  "lote": "B.2",
  "section": "§92",
  "alvo": "híbrido BG corpo + partes/FX na SAT; fallback sprite-only com política de SAT declarada",
  "regra_de_falha": "se o híbrido falhar, produzir comparação concreta e tradeoff declarado; nunca reduzir arte/escala/FX em silêncio",
  "baseline_preservada": "v031/a613ca97 (pacing 6025 no selo 300 s); alvo do fallback v036 5745",
  "relatorio_anterior_preservado": "out/logs/runs/20261020T005000Z_b2b3_decision.json"
 },
 "clock_note": "Timestamps em UTC; o host local marcava 2026-10-20 23:5x. O selo v043 começou 2026-10-21T02:44:42Z e o par/vídeo v043 em 02:53:13Z.",
 "production": {
  "rom_sha256": "087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65",
  "src_main_c_sha256": "042ba22e4a0763daaa4e402b90a0a5d0d40a7b5923c17575ed012b6a89773bfe",
  "head": "da86de3",
  "state": "restaurada após cada build; sem commit/push; sem sessão de emulador viva ao fim"
 },
 "candidates": {
  "sprite_only_v036": {
   "role": "referência de pacing/render do fallback",
   "rom_sha256": "7002b0ba44e7d211476c096c511fe45c35184e3c3b815b9b486e09c765191926",
   "pacing": {"smrt_frame": 5745, "vovf": 2514, "stage_slice_max": 221, "verdict": "pass"},
   "render": {"p1_ink": 2262, "p2_ink": 587, "p2_fraction_of_p1": 0.26, "sat_om_p1": 382, "sat_frames_p1": 116, "verdict": "fail: SAT-64 omite o P2; nenhuma pose inteira"},
   "overall": "pacing pass; render fail; linha não medida em 3b"
  },
  "hybrid_v3_v037": {
   "role": "melhor híbrido BG + SAT livre; comparação §92",
   "rom_sha256": "b68061ced34c19d1a24bf1c531dc893e136dbe6711a38d89d74c94ddbed9d480",
   "render": {"p1": "2250/2250", "p2": "1786/1786", "residue": 0, "sat_free": "64/64", "single_frame": True, "verdict": "pass no quadro; estabilidade temporal não provada"},
   "pacing": {"smrt_frame": 3945, "vovf": 2237, "stage_slice_max": 255, "bg_cells_max": 70, "bg_bytes_max": 552, "verdict": "fail: -31,3% vs 5745"},
   "overall": "render pass; pacing fail; FX têm SAT livre"
  },
  "sat_order_v040": {
   "role": "sprite-only com ordem alternada P1/P2; melhor pacing, linha fail",
   "rom_sha256": "d998209b7f426485380e8584ef14fbda6bb7d4bbec6f7f639476c23c34f8f068",
   "source": {"path": "main.c.satpolicy_v040", "sha256": "ddc947a11881c141f50dac446f4167522b82fbc29bd3eaac5ccd8488a84cc669"},
   "pacing": {"smrt_frame": 5743, "vovf": 2514, "stage_slice_max": 221, "vbl_exit_max": 253, "sat_om_p1": 188, "sat_om_p2": 194, "sat_frames": 116, "add_total_max": 70, "wait_p1": 3586, "wait_p2": 3676, "verdict": "pass (-0,03% vs 5745)"},
   "line_sim": {"manifest": "shadow_f001.json/shadow_f002.json", "sprites": 64, "peak_per_line": 14, "overflow_lines": [78, 77], "first_violations": "linhas 85–89: 12 entradas > 8; 4 visíveis descartadas", "verdict": "fail"},
   "render": {"p1_ink": 2262, "p2_ink": 587, "p2_fraction_of_p1": 0.26, "sat_om_p1": 188, "sat_om_p2": 194, "sat_frames": 116, "verdict": "fail: P2 fragmentado"},
   "video": {"frames": 600, "distinct": 179, "canvas": [256, 192], "playback_hz": 59.92274340431231, "motion_fraction": 0.14225260416666666, "sha256": None, "verdict": "pass 256x192; movimento de quadro inteiro"},
   "overall": "pacing pass; linha fail; render fail"
  },
  "linecap_v041": {
   "role": "cap whole-cell por linha com varredura de 16 linhas; reprovado no pacing",
   "rom_sha256": "3f3dce97d7afd9c3dd5fadef972e71222c57e877cf52382fdccffaec501f58e9",
   "source": {"path": "main.c.linecap_v041", "sha256": "fb84591d…"},
   "pacing": {"smrt_frame": 2055, "vovf": 1711, "worst_done": 0, "stage_slice_max": 220, "vbl_exit_max": 255, "sat_om_p1": 17029, "sat_om_p2": 17266, "sat_frames": 1842, "add_total_max": 70, "damage_p1": 532, "ko_events": 0, "verdict": "fail: -64,2% vs 5745"},
   "line_sim": {"manifest": "linecap_f001.json/linecap_f002.json (simulação sobre a SAT v040, não SAT real do v041)", "sprites": 39, "peak_per_line": 8, "overflow_lines": 0, "verdict": "pass na simulação"},
   "overall": "pacing fail; linha só simulada"
  },
  "rowquota_v042": {
   "role": "quota 6 primário + 2 secundário por banda de 16 px; primeira política com linha real pass",
   "rom_sha256": "4431533947b96c8443ca335e198e4e5922445e8cf006f488b87bdd6f85adb00c",
   "source": {"path": "main.c.rowquota_v042", "sha256": "efde6b881db6d4701cb9118723c7567213611694e4443432d0dc36ea6dd69bf0"},
   "corridor": {"verdict": "pass", "probes": 110, "margin_bytes": 1539},
   "pacing": {"smrt_frame": 4483, "vovf": 2506, "worst_done": 1, "stage_slice_max": 215, "vbl_exit_max": 255, "sat_om_p1": 33993, "sat_om_p2": 47462, "sat_frames": 4483, "sat_frames_p1": 2863, "sat_frames_p2": 4216, "add_total_max": 70, "damage_p1": 1000, "ko_events": 1, "vline_min": 7, "verdict": "fail: -22,0% vs 5745"},
   "line_sim": {"manifests": ["shadow_v042_f001.json", "shadow_v042_f002.json"], "sprites": 40, "peak_per_line": 8, "overflow_lines": 0, "sprite_next_free": 40, "verdict": "pass"},
   "sat_composition": {"p1_cells": 30, "p1_per_band": 6, "p2_cells": 10, "p2_per_band": 2, "bands": 5, "sat_valid": "40/64", "note": "add_total_max=70 são tentativas; a SAT válida é 40"},
   "silhouette_129": {"p1_player": {"player_attack_upper_le_5": False, "player_band_max": 6, "enemy_critical_ge_2": True, "enemy_total_ge_5": True}, "p2_player": {"player_ge_3": False, "player_band_min": 2, "enemy_critical_ge_2": True, "enemy_total_ge_5": True}, "pass_both_roles": False, "verdict": "fail por construção: 6>5 ou 2<3"},
  "video": {"frames": 600, "distinct": 133, "canvas": [256, 192], "playback_hz": 59.92274340431231, "motion_fraction": 0.1158447265625, "endpoint_fraction": 0.0982666015625, "sha256": "783ccd0c60d741af96433610fc84a40359b7378f489e652a23400c758172a934", "antiphase_frames": "573/600", "verdict": "pass 256x192; alternância anti-fase regular"},
   "capture_caveat": "PNGs pareados f1020/f1021 têm o mesmo SHA ccdd51c5… e mostram o lado cheio oposto ao shadow SAT do snapshot 1020; a captura está um quadro de jogo atrasada/adiantada. O veredito visual usa o vídeo e a SAT shadow.",
   "overall": "pacing fail; linha pass; §129 fail; render parcial"
  },
  "rowquota_v043": {
   "role": "quota escalar 5+3 por banda de 16 px; política compatível com §129",
   "rom_sha256": "13b78bd2435673df089ed69302522d332c9418ea74331aeff95065c85e3920c7",
   "source": {"path": "main.c.rowquota_v043", "sha256": "eb5576ad73e5e79b3ec94a217e13b57faf38a264631ba65aaec3f7642a54cb59"},
   "corridor": {"verdict": "pass", "probes": 110, "margin_bytes": 1539},
   "pacing": {"smrt_frame": 5033, "vovf": 2506, "worst_done": 1, "stage_slice_max": 214, "vbl_exit_max": 255, "sat_om_p1": 28094, "sat_om_p2": 51482, "sat_frames": 5033, "sat_frames_p1": 3142, "sat_frames_p2": 5009, "add_total_max": 70, "damage_p1": 1000, "ko_events": 1, "vline_min": 9, "verdict": "fail: -12,4% vs 5745; +12,3% vs v042"},
   "line_sim": {"manifests": ["shadow_v043_f001.json", "shadow_v043_f002.json"], "f001": {"sprites": 25, "peak_per_line": 5, "note": "transição: P1 não emitido; P2 primário 5/banda"}, "f002": {"sprites": 40, "peak_per_line": 8, "p1_cells": 15, "p1_per_band": 3, "p2_cells": 25, "p2_per_band": 5, "sprite_next_free": 40}, "verdict": "pass nos dois snapshots; f002 é o estado de política"},
   "silhouette_129": {"sample": "shadow_v043_f002 (ambos os lados)", "p1_player": {"player_ge_3": True, "player_attack_upper_le_5": True, "enemy_critical_ge_2": True, "enemy_total_ge_5": True}, "p2_player": {"player_ge_3": True, "player_attack_upper_le_5": True, "enemy_critical_ge_2": True, "enemy_total_ge_5": True}, "pass_both_roles": True, "verdict": "pass"},
   "video": {"frames": 600, "distinct": 127, "canvas": [256, 192], "playback_hz": 59.92274340431231, "motion_fraction": 0.11895751953125, "endpoint_fraction": 0.08109537760416667, "sha256": "a257e6ee65db28be978e3f36b164b1d2ba20dd589633bd4f3cdf99828563b054", "antiphase_frames": "458/600 no limiar 1000", "verdict": "pass 256x192; 5/3 mais equilibrado (cheio ~1957, faixa ~974)"},
   "overall": "pacing fail; linha pass; §129 pass; visual 5/3 mais equilibrado"
  }
 },
 "sat_policy_tradeoff": {
  "physical_limit": "Dois corpos de ~56×80 geram até 14 células/16 px; 8/linha é o limite físico do VDP. O SAT-64 e a linha são orçamentos distintos.",
  "hybrid": {"render": "100% em um quadro", "pacing": 3945, "cost_vs_5745": "-31,3%", "sat_free": "0/64", "fx": "SAT livre para partes/FX", "status": "render pass; pacing fail"},
  "sprite_only_v040": {"render": "P2 26%; 382 omissões em 116 frames", "pacing": 5743, "cost_vs_5745": "-0,03%", "line": "pico 14; 78/77 linhas >8", "status": "pacing pass; linha fail"},
  "quota_6_2_v042": {"render": "um corpo cheio + faixa de 2 células; alternância ~7,5 Hz", "pacing": 4483, "cost_vs_5745": "-22,0%", "line": "40/8 pass", "silhouette": "6>5 ou 2<3 fail", "status": "linha pass; pacing/§129 fail"},
  "quota_5_3_v043": {"render": "5 células no primário + 3 no secundário; mais equilibrado, ainda parcial", "pacing": 5033, "cost_vs_5745": "-12,4%", "line": "40/8 pass", "silhouette": "5/3 pass", "status": "linha/§129 pass; pacing fail"},
  "precomputed_next": {"idea": "listas limitadas 5/3 por pose/lado, geradas offline; emitir sem checagem por célula; seleção espacial contígua/central", "expected": "pacing próximo do v040; linha/§129 pass; ainda é omissão declarada, não render 100%", "status": "R&D; exige mudança de gerador/struct e aprovação"}
 },
 "decision": {
  "promotions": [],
  "v042": "não promover: pacing fail e §129 fail; 6/2 é inválido por construção para §129",
  "v043": "não promover: pacing 5033 < 5745; 5/3 é a política compatível (linha/§129/visual), mas a implementação escalar não paga o pacing",
  "v041": "não promover: -64,2% de pacing",
  "v040": "não promover: linha fail",
  "v037": "não promover: pacing fail; híbrido fica como R&D",
  "recommended_policy": "5/3, não 6/2; próxima implementação é a lista pré-computada com seleção espacial coerente",
  "fx": "adiados/limitados no sprite-only; destino (BG/SAT/adiado) exige aprovação humana",
  "production_restored": True
 },
 "pending_approvals": [
  "fallback sprite-only + omissão declarada 5/3 e destino dos FX",
  "empacotamento 1 MB (header 0x4C vs arquivo de 52 bancos; cópia padded só para BlastEm)",
  "guarda/auto-padding no wrapper BlastEm + lição L139 (L137=silhueta, L138=projeção SHA, alocadas em 2026-10-19)",
  "política de quota 5/3 vs 6/2 (recomendação: 5/3)",
  "gerador/struct da lista pré-computada (curadoria de tools/ + asset pipeline)",
  "doc/15, manifest/contrato, doc/engine_quality_contract.json, CRAM P0/P1/P2, reancoragem D2/G, print do vram_plan.py"
 ],
 "evidence": {
  "custody": "out/evidence/loteB2b_20261019/b2b3b/",
  "previous_report": "out/logs/runs/20261020T005000Z_b2b3_decision.json",
  "sat_shadow_v040": ["out/evidence/loteB2b_20261019/b2b3b/sat/shadow_f001.json", "out/evidence/loteB2b_20261019/b2b3b/sat/shadow_f002.json"],
  "sat_shadow_v042": ["out/evidence/loteB2b_20261019/b2b3b/sat/shadow_v042_f001.json", "out/evidence/loteB2b_20261019/b2b3b/sat/shadow_v042_f002.json"],
  "sat_shadow_v043": ["out/evidence/loteB2b_20261019/b2b3b/sat/shadow_v043_f001.json", "out/evidence/loteB2b_20261019/b2b3b/sat/shadow_v043_f002.json"],
  "line_sim": ["out/evidence/loteB2b_20261019/b2b3b/sat/line_sim_v040_f001.out", "out/evidence/loteB2b_20261019/b2b3b/sat/line_sim_v040_f002.out", "out/evidence/loteB2b_20261019/b2b3b/sat/line_sim_v042_f001.out", "out/evidence/loteB2b_20261019/b2b3b/sat/line_sim_v042_f002.out", "out/evidence/loteB2b_20261019/b2b3b/sat/line_sim_v043_f001.out", "out/evidence/loteB2b_20261019/b2b3b/sat/line_sim_v043_f002.out"],
  "silhouette": ["out/evidence/loteB2b_20261019/b2b3b/sat/silhouette_v042.json", "out/evidence/loteB2b_20261019/b2b3b/sat/silhouette_v043_f002.json"],
  "videos": ["out/evidence/loteB2b_20261019/b2b3b/captures/video_v042_pair.mp4", "out/evidence/loteB2b_20261019/b2b3b/captures/video_v043_pair.mp4", "out/evidence/loteB2b_20261019/b2b3b/captures/video_v040_pair.mp4"],
  "blastem": ["out/evidence/loteB2b_20261019/b2b3b/blastem/v042_s1020_1021/", "out/evidence/loteB2b_20261019/b2b3b/blastem/v043_s1020_1021/"]
 },
 "limitations": [
  "audit_silhouette_integrity.py é específico do O3; a contagem §129 do luta_mugem é manual (células por banda/linha), não pixels nem ROM.",
  "present_p1/p2=65535 sob quota significa 'alguma célula omitida', não corpo ausente; a sonda não é gate desta política.",
  "sat_om alto no v042/v043 é omissão declarada da quota, não overflow do SAT-64; a SAT válida é 40/64 (SpriteNextFree).",
  "A captura pareada v042 f1020/f1021 é stale (mesmo SHA; lado cheio oposto ao shadow 1020); o vídeo e a SAT shadow são a evidência visual.",
  "O v043 f001 é uma transição com P1 não emitido; a amostra de política é o f002 (ambos os lados).",
  "O v041 só tem linha simulada sobre a SAT v040; não há SAT real do v041.",
  "O selo mede o contador de frames do loop; o estado de luta (damage/KO) pode diferir entre candidatos. O gate é smrt_frame, não o resultado do combate.",
  "O motion_timeline é variação de pixels de quadro inteiro; não prova AIR, semântica de animação ou qualidade visual.",
  "vline_min/vovf são indicadores de derrame; o pacing é medido por smrt_frame no selo de 300 s."
 ]
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
print(OUT)
