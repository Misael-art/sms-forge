# Matriz de consumidores × sessões privadas (2026-10-05)

Execução **manual interativa** (`run.sh` de cada projeto: abre a janela do emulador para uma pessoa) é distinta de
**validação automatizada**, que deve usar sessão privada explícita (`tools/sms_wrapper/session_consumer.py`:
ROM+SHA, uma sessão, mesmo ID em tudo, `close_session` em `finally`, sem fallback ao desktop).

| Caminho | Comportamento atual | Estado | Evidência exigida |
|---|---|---|---|
| `luta_mugen/tools/prove_input.py` | portas P1/P2 da sessão, frames do VDP, RAM SMRT | **migrado** — 7/7 eixos PASS | `out/evidence/t5_input_memory_<sessão>.json` |
| `luta_mugen/tools/prove_round_lifecycle.py` | idem; KO e reset de round por RAM | **migrado** — PASS | `t10_round_lifecycle_<sessão>.json` |
| `tools/sms_wrapper/luta_mugen_trace_dap.py` | sessão privada + gate de RAM + guard da pilha | **migrado** (trilha em 0xD200) | ver `doc/curation/2026-10-05_l057...json` |
| `hamoopig/tools/prove_walk.py`, `prove_punch.py` | sessão privada, frames | **migrados** — PASS (SHA real da sessão no JSON) | `walk_probe_<sessão>.json`, `punch_probe_<sessão>.json` |
| `hamoopig/tools/prove_basic/guard/throw/special.py` | DAP fixo 4901, `xdotool`/`press_spec`, `sleep` | **pendente** | reescrever sobre `session_consumer`; ROM atual difere dos SHAs fixados no script |
| `hamoopig/tools/capture_scenes.py`, `capture_cycles.py` | DAP + foco de janela (`capture_scenes.py` tem edição não commitada de outro agente) | **pendente** | idem; preservar a edição alheia |
| `MSSF2T/tools/prove_input_memory.py` (1354 l.), `prove_poses.py` | DAP + teclado do host + `sleep` | **pendente** | reescrita por fase com `sequence`; ROM MSSF2T compilada em 2026-10-05 |
| `kage_matsuri/tools/prove_input_memory.py` (934 l.), `measure_worst_frame_cycle.py` | `xdotool keydown`, DAP | **pendente** | idem |
| `*/run.sh` (arena_nocturna, hamoopig, kage_matsuri, laboratorio_01, luta_mugen, master_of_fighters, MSSF2T, modelo, `_laboratorio/*`) | `java -jar Emulicious.jar`, abre janela do usuário | **manual interativo — mantido**; não é validação | não usar como gate |
| `capture_evidence/video/audio`, `measure_runtime_probe`, `emulator_input` (`--session`) | rota privada disponível | **migrados** (fábrica) | — |
| OpenBOR | nenhum consumidor localizado | n/a | mesmo ID/SHA quando existir |

`emulicious_dap.py` e as rotas históricas por DAP/teclado continuam existindo para os pendentes; **não** são aceitas como
evidência concorrente-segura.
