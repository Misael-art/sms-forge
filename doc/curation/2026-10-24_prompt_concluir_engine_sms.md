# Prompt — concluir e qualificar a engine de luta SMS

Você atua como engenheiro responsável pela engine de luta do SMSForge e pelo
consumidor `SMS_projects/luta_mugem_rev2`. Implemente, teste e integre até fechar
o escopo suportado. O objetivo é uma base reutilizável, robusta e com alto
acabamento para projetos MUGEN e autorais. AAA é uma direção de qualidade;
não é um claim que um agente ou gate possa certificar automaticamente.

## Entrada e autorização

Workspace: `/mnt/sdcard/Projects/SMSForge`.
Consumidor: `/mnt/sdcard/Projects/SMSForge/SMS_projects/luta_mugem_rev2`.
Core/ferramentas: `/mnt/sdcard/Projects/SMSForge/tools/sms_wrapper/`.

Leia AGENTS.md, `/home/misael/.codex/RTK.md`, a arquitetura e SMS_GLOBAL atuais.
Diga `[Contexto SMS Carregado]` antes de propor ações. Prefixe comandos de
shell com `rtk`; use `rtk proxy` quando precisar da saída sem filtragem.

Este pedido autoriza implementação no consumidor e na fábrica, testes,
diagnósticos isolados e atualização da memória/contratos. Preserve alterações
preexistentes e ROMs históricas. Não assuma autorização para merge/deploy,
apagar material alheio, reautorar arte, reduzir escopo ou aprovar claims.
Uma nova curadoria de regra global segue seu runbook e calibração.

Leia os quatro documentos da hierarquia no consumidor, seu manifesto e:

- `doc/curation/2026-10-24_mugenesis_rev2.md`;
- `doc/curation/2026-10-24_luta_mugem_rev2_backlog.json` e a lista `.md`;
- `SMS_projects/luta_mugem_rev2/doc/20-plano-implementacao.md`, documentos
  28–30 e pacotes PB-01–PB-18 da curadoria de 2026-10-23;
- workflow `mugen-engine-quality.md`, pipeline `mugen_fighting_v1.json`,
  `first-playable-slice.md`, `async-promotion-loop.md` e
  `causal-persistence-loop.md`;
- skills `sms-mugen-source-semantics.md`, `sms-runtime-optimization.md`,
  `sms-state-transitions.md`, `sms-fight-input-proof.md`, `sms-psg-audio.md`,
  `sms-banking-header.md`, `sms-vram-vblank-budget.md` e
  `sms-visual-excellence.md`, conforme o domínio alterado.

O backlog contém 55 pendências identificadas, com dependências e aceites.
Revalide o estado antes de executar: análise histórica não substitui o disco.
Mantenha esses IDs no acompanhamento; não marque item fechado apenas porque
o código foi escrito ou uma fixture passou.

## Baseline a conferir

- Produção nominal: `out/rom/luta_mugem_rev2.sms`, 851968 bytes,
  `087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65`.
- Prova limitada: `out/rom/pose_budget_settled_20261023.sms`, 458752 bytes,
  `698e58ed5a0e9256cf2497783b5b0a4343464c15138ce5783c5b9fd98879b13a`.
- A candidata bloqueia dez papéis largos/25 poses. Seu selo histórico tem
  `vline_min=4`, `vovf_delta=1740`, `done=1`: derramou. Não é solução final.
- Produção, dados selecionados e docs não convergem: `.mddev/project.json`
  usa 49 bancos `ryu_ken_cross`; contrato/TDD ainda narram B.2a e escala
  histórica; o build_record auditado tinha SHA `e697e906…`. Identifique a
  origem de cada registro antes de atualizar qualquer eixo.
- Captura nova em 2026-10-24: produção com P2 fragmentado e fundo repetido;
  candidata com dois corpos completos em um quadro. São provas estáticas,
  sem FPS/áudio/gameplay. O contador ROM difere do frame VDP.
- `common1.cns` está ausente nos dois ZIPs. `common_forge` é adaptação,
  sem equivalência provada. A FSM de papéis não é CNS completo.
- O renderer declara limitação de facing/payload; colisão usa dados da lógica
  enquanto pode exibir pose residente anterior. Esses contratos precisam fechar.
- EIO do irmão `luta_mugen` é conhecido. Não reconstruir documentos fictícios,
  tratar EIO como ausência ou esconder falhas globais para obter verde.

## Produto e limites

Ken/Ken → Ryu/Ryu → Ken/Ryu → Ryu/Ken; mesmo core, dados/configuração distintos.
Fundo sólido em todas as telas. Walk/crouch/jump/guard, dano e recuperação,
normais/variantes/cancels/combos requeridos, especiais/projéteis/supers/power,
FX, rounds/timeout/empate, HUD, pausa, menus, seleção, treino e opções do GDD.
Dois pads SMS com direções e botões 1/2; Pause é controle do console/NMI.
Arcade/Versus/Treino e opções persistem em RAM da sessão.

Não acrescentar cenário, online, save, elenco extra ou compatibilidade MUGEN
irrestrita. Não portar DMA, XGM2, PAL0–3, WINDOW, limites H40, structs/ABI
M68K ou números de throughput do doador. Consulte SMSlib.h/PSGlib.h antes
de usar API. Sem float/double no loop, malloc/free, VRAM em massa fora da
janela segura ou mais de 8 sprites/linha e 64 na SAT nas composições aceitas.

Escala vigente: encaixe CPS2→SMS declarado e neutras até quatro células por
linha por ator; composição de golpe largo 5+3 é intenção de projeto que ainda
precisa ser demonstrada. Não impor quatro células a todo golpe e chamar isso
de conclusão. Não diminuir idle, apagar colunas/FX/perigo ou cortar movimentos
para obter PASS sem decisão humana de fidelidade/escopo.

## Execução em lotes verticais

1. **Identidade e preflight (ID01/ID02).** Inventarie dirty tree, fonte, gerador,
   binários, dependências e hashes. Faça build em destino isolado antes de
   tocar na principal. Selecione ROM por caminho+SHA, nunca pela mais recente
   por mtime. Preserve positivos e negativos e atualize a memória com fatos.
2. **Apresentação e prazo (R01–R06/R09–R13/IN05).** Comprove fundo e mapa VRAM;
   derive a geometria real de todas as poses/faces/composições alcançáveis.
   Compare reúso exato, recorte esparso, cache, prefetch, granularidade de cópia
   e BG/híbrido apenas onde medido. Fixe owners e invalidação por geração.
   Meça bytes novos por transição/tick e trabalho completo. Corpo parado
   completo não paga ação nem concorrência. Feche um golpe completo, incluindo
   resposta visual e contato coerentes, sem starvation ou pose parcial.
3. **Semântica alcançável (S01–S12/IN01–IN04).** Resolva dependências e matriz
   de fidelidade. Implemente o subconjunto CNS em lowering AOT com predicados
   executáveis; VM compacta é alternativa sob custo medido. Preserve ordem,
   unidades, timings AIR, CLSN, HitDef, vulnerabilidade e recursos. Unsupported
   obrigatório bloqueia aceitação. Compare fonte/IR/C/ROM com casos negativos.
4. **Quatro pares e objetos.** Complete o primeiro par antes de ampliar;
   introduza Ryu pelo mesmo caminho, sem C por personagem. Teste faces,
   cantos, defensor móvel, ar, guarda, cancelamentos e objetos simultâneos.
   Pools estáticos têm admissão/overflow/expiração/reset definidos e contadores;
   não sobrescreva entidade viva nem suma com efeito relevante silenciosamente.
5. **Match/HUD/PSG e fluxos (G01–G06/A01–A04).** Integre custos reais cedo.
   Faça round/match/revanche e troca de cena com teardown de input, estados,
   objetos, paleta, PNT/SAT, mapper e áudio. Treino/command list usam os mesmos
   dados do matcher. Soundtest enumera biblioteca real e vazio seguro. PSG tem
   proveniência, arbitragem e revisão auditiva; SND inventariado não é áudio SMS.
6. **Reuso e resiliência (RE01–RE06/Q01–Q04).** Centralize o core e reduza o
   consumidor a dados/configuração/integração. Defina IR neutro e ABI/features
   com limites reais de tipos/bancos. Faça C gerado incluir seu header e prove
   ABI errada em compilação. Receita inclui imagens/dados/proveniência/recibos
   em staging, falha injetada, rollback e recusa antes de escrita parcial.
   Demonstre outro consumidor limpo e um adaptador autoral para o mesmo core;
   não fabrique MUGEN para fonte autoral nem promova pixel procedural a arte.
7. **Qualificação final (Q02–Q07).** Stress/soak com carga completa e seeds,
   repetição de rounds/pausa/retorno, pools cheios, wrap, extremos numéricos e
   bancos-limite. Consolide os sete eixos e revisão independente na mesma SHA.

Cada lote mantém contrato → implementação → ROM → medição → memória. Testes
focados durante o lote; gates integrais uma vez por composição estável no
fechamento. Se duas tentativas equivalentes falharem sem delta causal, mude
hipótese/representação. Não encerre depois de um relatório ou milestone quando
houver próximo ramo seguro. Gate longo em background permite trabalho
independente; não fazer polling/narração repetitiva de CI. Um push por lote
completo, quando a política Git e a autorização da sessão permitirem.

Quando depender de decisão humana sobre controles, alteração de arte ou
escopo, formule a decisão com opções concretas e evidência. Continue as tarefas
independentes. Tempo sem resposta não é aprovação; mantenha o item bloqueado
sem bloquear trabalho que não depende dele.

## QA e critérios de aceite

Antes de QA automática, leia `emulator-isolated-session.md`,
`subagent-emulator-qa.md` e SMS_GLOBAL §§93–100. Use Emulicious privado por ID
e ROM SHA; sem fallback para desktop nem encerramento de processos alheios.
BlastEm SMS é diagnóstico complementar. Não transferir evidência MD.

Se delegar, seguir o harness atual: no máximo três workers, owners/caminhos
disjuntos, QA nativa com pedido V2, sessão própria e retorno real. Revisor é
distinto do produtor; não simular subagente em JSON. Coordenador confere IDs,
artefatos, mídias e claims. FPS sob reserva cooperativa, sem medições simultâneas.

Para cada capacidade, registrar fonte/section/ID/SHA, lowering, consumidor,
teste, ROM/SHA/sessão, estado observado e custo. Separar `parsed`, `generated`,
`consumed`, `observed`, `budget_validated`; `dropped_by_owner` requer decisão.

Exigir no domínio aceito:

- SAT emitida e observada dentro dos limites, sem omissão permanente nem
  flicker visível; comparar framebuffer com imagens legais durante ações e
  pelo menos duas voltas de animações/caches cíclicos.
- Pose desejada/residente/submetida/apresentada com geração e deadline;
  contato e física coerentes com o snapshot exibido, sem dano invisível.
- Worst-frame da carga completa, janela contínua sem DAP, `done=1` e zero
  overflow. `vline_min` é mínimo selado; snapshot `vline` não o substitui.
- Cadência regional contínua e prazos de input medidos; título60fps ou vídeo
  por stepping não medem o loop real. PAL tem política temporal explícita.
- RAM/stack/corredor, mapa VRAM, mapper/bancos e símbolos/SIZE da mesma build.
- Áudio isolado com duração/sinal, proveniência/canal/mix e revisão auditiva.
- Pacote inválido recusado antes de executar; falha de geração preserva a
  versão anterior; pool cheio tem política explícita e recuperação válida.
- Sete eixos simultâneos, época visual `delivery`, vínculo asset→ROM, frescor,
  conciliação de claims, revisão independente e memória atualizada.

`audit_composition_gate.py` e `audit_sole_alignment.py` foram revisados e
continuam **diagnósticos limitados**, fora dos gates globais. Self-check antes
de ler. O primeiro não prova o par nem implementação 5+3; o segundo mede última
linha opaca, que pode ser equipamento ou pose aérea. Não usar seus PASS para
aprovar o jogo. `require-distinct-fighters` não se aplica a espelhos legítimos.

Antes de cada comando, confira `--help` e a CLI real. Pontos de entrada existentes:

```sh
rtk proxy python3 tools/sms_wrapper/build_inner.py --project <consumidor>
rtk proxy python3 tools/sms_wrapper/audit_mugen_engine_contract.py --self-check
rtk proxy python3 tools/sms_wrapper/audit_mugen_engine_contract.py --project <consumidor>
rtk proxy env PYTHONPATH=tools/sms_wrapper python3 -m mugen2sms --help
rtk proxy python3 tools/sms_wrapper/selftest.py
rtk proxy python3 tools/sms_wrapper/validate_measurement_tools.py
rtk proxy python3 tools/sms_wrapper/audit_doc_sync.py
rtk proxy python3 tools/sms_wrapper/audit_learning_capture.py --root .
```

Delivery exige também `--delivery` e os gates atuais da pipeline; planning PASS
não fecha entrega. EIO preexistente no gate global deve ser relatado à parte,
com os resultados do escopo e sem declarar a fábrica inteira verde.

## Encerramento verificável

Entregue código e receita reproduzíveis, backlog atualizado por ID, contratos
atuais, resultados positivos/negativos, binários/bundles identificados e
memória operacional. Informe o que mudou, por que, como foi testado e os
limites restantes. Não prometa ausência universal de glitches: declare a
cobertura, carga, duração e regiões em que nenhum defeito foi observado.

Se o escopo estiver incompleto, continue pelo blocker dominante e pelos ramos
seguros. Quando uma decisão externa realmente impedir o restante, entregue a
prova mínima do bloqueio, opções executáveis e o estado preservado. Nunca
substitua conclusão da engine por mais um prompt de continuidade.
