# Plano de continuidade — kage_matsuri

Revisão: 2026-09-09. Objetivo: concluir a fatia `rua_matsuri` do GDD com arte final verificável, ciclo jogável completo e evidência da ROM final. Teto vigente: **protótipo jogável**. Esta revisão documental não valida uma entrega em emulador.

## 1. Autoridade e escopo

Leia o AGENTS.md da raiz, `/home/misael/.codex/RTK.md`, `tools/sms_wrapper/.agent/ARCHITECTURE.md`, a lei global e a hierarquia do projeto: memory bank, GDD, spec, diretrizes, manifesto, roteiro e TDD. A lei não está materializada na `.agent/` local inspecionada: use o framework central sem sobrescrever a pasta local. Use `rtk` nos comandos de shell.

Siga os workflows centrais `production-loop.md`, `causal-persistence-loop.md`, `evidence-protocol.md` e `independent-quality-review.md`. Leia as skills de domínio antes de produzir arte, animação, hardware/budget ou áudio.

Concluir significa: uma rua 256×192, Kage e samurais 16×32, andar, pular, combo de dois cortes, feedback de acerto/derrota, dois samurais, vitória no torii e reinício funcional. Preserve implementações existentes que passem na verificação.

Dano ao jogador, ataques/projéteis do samurai e nova cena depois do torii não estão especificados no GDD. A seção “Próximo” do memory bank não define essas mecânicas. Registre a decisão de escopo necessária, sem adicioná-las silenciosamente, e continue a conclusão independente da fatia. H-scroll e colisão 1-way são débitos explícitos, não técnicas concluídas. O manifesto exige NTSC e PAL: validar ambos sem retirar PAL para fechar a entrega.

## 2. Baseline inspecionada

ROM: `out/rom/kage_matsuri.sms`, 16384 bytes.
SHA-256: `11f64afade99bf215f7b642eb8d91eecea79ab042c4a81fbdd9a6859e84ffafa`.

| Item | Constatação | Pendência |
|---|---|---|
| Poses | `main.c` e `pack_kage.py` já têm seis poses, nas duas direções | Verificar semântica e arte final, não reimplementar |
| Fontes novas | `doc/handoff-assets.md` ainda descreve slash2/jump como provisórias | Resolver seleção e encerrar handoff |
| HUD | Vida e samurais restantes já existem, usando tiles existentes | Verificar leitura/overlap e objetivo 2→1→0; HP é estático no escopo atual |
| Contratos | Visual, binding e proveniência de áudio existem | Corrigir lastro semântico e cobertura |
| Gates | Cinco gates antigos passaram nesta revisão, após cinco self-checks PASS | PASS estrutural não fecha qualidade nem ciclo completo |
| SAT | Fixture: 22 sprites, pico 6/linha | Revalidar extremos de runtime |
| Input histórico | Direita/esquerda, pulo e pose 3, com SHA correspondente | Falta prova explícita de combo/pose 4, acertos, duas derrotas, vitória e reinício |
| FPS histórico | Título: 60 em seis amostras; DAP NTSC: 58,78/58,73 | Não arredondar para 60 constante; verificar método e PAL |
| Build record | Build/validation_report true; demais cinco eixos false | Conciliar evidência, registro e memória |

Na revisão inicial não foram encontrados vídeo, medição worst-frame ou selo de bundle em `out/evidence/`; esse estado foi superado pela execução P0→P4 desta continuação, mantendo os artefatos baseline separados.

## 3. Lacunas prioritárias

1. **Binding real:** o manifesto declara `sym_kage_*` e `sym_stage_tiles`, ausentes da busca em fonte, headers e mapa do linker. Arrays reais incluem `kage_right_tiles`, `kage_left_tiles`, `kage_ext_right_tiles`, `kage_ext_left_tiles`, `samurai_tiles`, `samurai_left_tiles`, `stage_tiles` e `stage_map`. O gate verifica presença/unicidade do campo symbol, sem provar sua ligação ao linker. Rastrear fonte→PNG→array/offset→linker→ROM, incluindo espelhados, mapa e paletas. Para vários PNGs num array, representar agrupamento/offsets conforme schema; não inventar aliases únicos para passar. Se necessário, manter prova complementar explícita e registrar limitação do schema. Alteração central exige autorização de curadoria.
2. **Escala e arte:** contrato visual avalia somente `*_idle_u.png`, metade superior 16×16, mínimo 15 px. Isso não prova a entidade 16×32 do GDD. Verificar composição superior/inferior, bbox opaco, registro dos pés/pivô e render da ROM. Não confundir altura da caixa com altura opaca nem reduzir exigência para passar. `visual_epoch: delivery` não transforma fonte provisória em arte aprovada.
3. **Budget:** a spec declara 92 B e usa FPS como justificativa temporal. Conferir cópia SAT na SMSlib e assembly; não presumir quatro bytes por sprite. Medir duração do trabalho e acessos VRAM, incluindo próximo degrau. Contagem de bytes não prova janela de VBlank. Tiles 0–255 são o layout de patterns atual, não toda a VRAM física ocupada.
4. **Probes e combo:** `reset_game()` não inicializa `probe_frame`. Definir inicialização determinística e verificar cold boot/reinício. Snapshot genérico em `runtime_probe.json` usa score/boss/over/wave, não os campos do TDD: conferir endereços, larguras e interpretação antes de usar valores. A janela de combo descrita no TDD difere da condição `slash_t >= 2 && slash_t <= 8` após decremento: medir limites e harmonizar código/documentação com design aprovado.
5. **Vitória:** `ST_WIN` já existe com `kills >= 2 && px > 200`, mudança de backdrop e B1 para reiniciar. Demonstrar entrada correta e feedback legível; testar B1 ainda pressionado ao entrar para detectar reinício imediato. Não concluir pela leitura de código.

## 4. Produção em ordem

### P0 — Preservar e reproduzir

- Inspecionar alterações/trabalho concorrente. O projeto inteiro aparece como não rastreado no Git: não limpar, adicionar ou commitar indiscriminadamente.
- Preservar ROM, hashes, fontes e evidências antes de regenerar. Não começar por `clean.sh`.
- Executar self-checks e gates da seção 5. Ler interfaces/schemas dos demais instrumentos; não inventar flags nem confiar em instrumento sem self-check verde.
- Atualizar memory bank distinguindo histórico, reproduzido e ainda não provado. Registrar blocker dominante.

Saída: baseline preservada e próxima ação causal definida.

### P1 — Fechar a arte integrada

- Inspecionar fontes slash2/jump e candidatos em `rascunho/anim_kage_slash2/` e `rascunho/anim_kage_combo/`. `f015.png` é candidato, não seleção aprovada. Comparar em tamanho nativo.
- Selecionar/reautorizar somente o necessário, com corpo inteiro, identidade e leitura distinta de slash1/slash2/jump. Personagem/cenário final não nasce de desenho procedural. Aplicar skill de imagem se gerar/editar raster.
- Registrar fontes, hashes e transformação; verificar chroma, preto opaco, arma cortada, pivô e paleta compartilhada. O handoff de arte limita aquele papel, não o coordenador de produção.
- Regenerar pelo empacotador existente, observando que também reescreve palco, paletas e áudio. Revisar todos os deltas.
- Corrigir contrato para demonstrar personagem completo e encerrar pendência do handoff com evidência, não apenas renomeando status.

Layout implementado:

| Tiles | Uso |
|---|---|
| 0–127 | BG |
| 128–159 / 160–191 | Quatro poses base Kage, direita / esquerda |
| 192–207 / 208–223 | Duas poses Samurai, direita / esquerda |
| 224–231 / 232–239 | Slash2 / jump, direita |
| 240–247 / 248–255 | Slash2 / jump, esquerda |

Saída: poses semanticamente distintas, pivô/escala preservados, fontes finais rastreadas e comparação de fidelidade/animação na ROM. A alocação por pose/direção do plano anterior estava incorreta.

### P2 — Fechar ciclo jogável

- Corrigir defeitos demonstrados dentro do GDD, sem ampliar mecânicas.
- Instrumentar campos necessários para HP/alive dos defensores, kills, estado, pose/facing e frames; confirmar espaço livre e ausência de conflito com RAM/pilha no linker.
- Provar andar/atacar nos dois sentidos; pular/pousar durante e fora de corte; B1 com soltura/repressão dentro e fora da janela; pose 4 distinta; acerto versus whiff; recuo/piscar; duas derrotas; objetivo 2→1→0; torii sem vitória enquanto há inimigo; vitória e reset restaurando entidades/HUD.
- Conferir bordas x=8/x=232, hitboxes e inimigos sobrepostos. Prova de golpe inclui estado do defensor e HP coerente, não somente pose do atacante.
- Usar vídeo de framebuffer para transições e DAP para eventos curtos. Estender `tools/prove_input_memory.py` com casos negativos quando necessário; nunca modificar jogo para esconder falha de teste.

Saída: matriz de casos com resultado, artefato e SHA, demonstrando ciclo completo.

### P3 — Medir budget e regiões

- Conferir headers/implementação SMSlib e assembly: ordem do VBlank, montagem/cópia SAT, PSG e transferências VRAM. Build/validação central permanece no wrapper.
- Localizar instrumento worst-frame aplicável e validar self-check. O projeto não possui `tools/measure_worst_frame.py`; não copiar probe de outro jogo sem adaptar schema, fase e região. Se exigir mudança central, registrar autorização de curadoria necessária e continuar ramos independentes.
- Medir dois inimigos, HUD cheio, movimento/pulo, combo, SFX/música e transição. Medir próximo degrau em configuração de teste identificada, separada da ROM final. Não chamar caminho vazio de pior caso.
- Atualizar spec com grandezas realmente medidas, método, limites regionais, derrames e provas. FPS do título não absolve estouro.
- Validar NTSC e PAL: ritmo do emulador, avanço da ROM e velocidade/duração de movimento, salto, combo e áudio; normalizar temporização quando necessário para cumprir contrato.

Saída: budget medido, extremos SAT/scanline aprovados e duas regiões verificadas.

### P4 — Congelar, capturar e concluir

- Build final via `build.sh`, sem `--skip-pre-gates`. Verificar tamanho/mapa/proveniência e atualizar binding completo ao SHA final.
- Executar gates aplicáveis de recursos, sprites/modo/scanline, debug, tilemap, contraste, proveniência visual/áudio, canal PSG, tamanhos de símbolos, animação, fidelidade, placeholders, delivery/binding e processo. Registrar não aplicabilidade fundamentada quando houver.
- Review independente read-only no checkpoint vertical_slice/release_candidate, conforme workflow/router, ligado aos hashes. Não autoaprovar nem fabricar parecer. Corrigir defeitos e renovar review quando artefatos mudarem.
- Usar `emulator_session.py`; não matar emulador do usuário indiscriminadamente. Wayland: canal validado `emulator_input.py`. Áudio isolado pelo `capture_audio.py`.
- Depois do último build, executar ciclo automatizado contínuo de boot determinístico, captura/fidelidade, gameplay completo, vídeo nativo 256×192, FPS/avanço, áudio/mix e `seal_fresh_evidence_bundle.py`. Montar comandos pelas interfaces reais. Identificar e preservar provas NTSC/PAL.
- Conciliar por `reconcile_claims.py`, segundo schema/pré-condições; revisar build record e atualizar memory bank/TDD/spec/handoff. Novo binário invalida provas anteriores: recapturar, nunca adulterar datas/hashes/booleanos.

Saída final: sete eixos simultâneos sustentados (build, validation_report, boot, gameplay, FPS, áudio, memória), arte final delivery com binding real, budget medido e review independente válido. Entregar caminho/SHA da ROM, evidências regionais e débitos fora de escopo. Não criar `promotion_claims/aaa.json`: AAA está fora do GDD e o produtor não aprova teto para apagar blocker.

## 5. Entradas verificadas

Da raiz `/mnt/sdcard/Projects/SMSForge`, repetir `--self-check` de cada script antes de confiar na análise. Os cinco self-checks e comandos abaixo passaram nesta revisão:

```bash
rtk proxy python3 tools/sms_wrapper/audit_claims.py --project SMS_projects/kage_matsuri
rtk proxy python3 tools/sms_wrapper/audit_audio_provenance.py --project SMS_projects/kage_matsuri
rtk proxy python3 tools/sms_wrapper/audit_visual_delivery.py --project SMS_projects/kage_matsuri --delivery
rtk proxy python3 tools/sms_wrapper/audit_rom_asset_binding.py --project SMS_projects/kage_matsuri --require
rtk proxy python3 tools/sms_wrapper/audit_sprite_line_sim.py SMS_projects/kage_matsuri/doc/sprite_scene_rua_matsuri.json
```

Depois de preservar baseline e alterar fontes, as entradas existentes de produção são:

```bash
rtk proxy python3 SMS_projects/kage_matsuri/tools/pack_kage.py
rtk proxy bash SMS_projects/kage_matsuri/build.sh
```

Nesta continuação o empacotamento/build foi executado pelo wrapper; `SMS_EVIDENCE=1` não substituiu matriz de gameplay, budget, review e selo.

## 6. Persistência

Avançar de P0 a P4 sem encerrar após diagnóstico, documento ou milestone isolado. Duas tentativas equivalentes sem evidência nova encerram a rota: mudar hipótese/instrumento/representação. Perguntar somente por decisão irredutível de produto, autorização externa/curadoria necessária ou bloqueio real; continuar o que não depende da resposta. Sem canal de emulador/arte/review, registrar bloqueio e esgotar ramos seguros sem simular validação.

Ao encerrar, informar estado real, delta, rotas tentadas, blockers, teto e menor próxima ação. Este plano substitui a proposta anterior, não substitui o memory bank nem expande o GDD.
