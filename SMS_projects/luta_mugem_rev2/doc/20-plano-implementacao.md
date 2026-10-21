# Plano de implementação — luta_mugem_rev2

## Direção técnica

Este consumidor começa do aprendizado do wrapper, não de um clone do projeto
ilegível. Arte, semântica e testes do doador são referências por SHA. Fontes
do runtime MD não são binários SMS e seus resultados não qualificam este jogo.
O parecer anexado é inventário de hipóteses; conferência local prevalece.

Prioridade: provar a composição e uma interação completa antes de converter o
pacote inteiro. O maior risco visual é limite de 8 entradas de sprite por linha;
o maior risco de conversão é confundir tabelas FSM com execução de controllers.

| Lote | Trabalho | Saída e condição para avançar |
|---|---|---|
| M0 — contexto/intake | Ken/Ryu raw do SGDK, DEF/SFF/AIR/CMD/CNS/SND/paletas/common; manifests/SHA/licença; fonte wrapper e storage legíveis | Contexto próprio íntegro, fonte exata, common ausente explícito, nenhum caminho obrigatório no doc antigo |
| M1 — arquitetura visual | Limite inferior por scanline em escala/poses/overlap/FX reais; comparar sprite-only, BG/híbrido e layout | ROM diagnóstica do par, todos os quadros inspecionados, pools/VRAM/RAM/ROM/upload medidos; registrar decisão/fallback |
| M2 — núcleo semântico | Subconjunto CNS alcançável compilado, estados/actions/timing/CMD/CLSN/HitDef e controladores consumidos | Um normal de Ken com entrada→pose→contato→dano→recovery; prova differential fonte/host/C e ROM, sem hardcode por nome |
| M3 — Ken/Ken | Todas ações suportadas do pacote, defesa/movimento/queda/KO, especiais/projéteis/supers/power, IA | Matriz de movimentos/contextos, slot/paleta/facing, IA×IA/humano×IA/humano×humano, vídeos/traces/budgets |
| M4 — Ryu/Ryu | Importar pelo mesmo caminho, sem C especial de personagem; mesmos gates | Novas features fonte elevam perfil versionado com teste; nenhum fallback silencioso |
| M5 — cruzados | Ken/Ryu e Ryu/Ken; limites/guardas/cancels/projéteis/FX simultâneos | Testes dinâmicos contra oponente móvel; mesmos recursos em pior frame e troca de lados |
| M6 — match/HUD/áudio | Vida/power/timer/hits/rounds, intro/fight, resultados/timeout/empate/KO/hitstop/shake; música/SFX | Lifecycle completo e resets, mix ouvido com SFX sob carga, input/pacing/VRAM medidos na ROM atual |
| M7 — front-end | Título/PressStart, Arcade/Versus/Treino/Options, seleção/retrato, VS, continue/final | Todos caminhos/retornos por input real; som/paleta/bancos/objetos limpos; sem cenário |
| M8 — engine reutilizável | Perfis/matrizes/relatórios/versionamento, instalador/consumidor e regressão sem EIO legado | Reimportar ambos de snapshot limpo; layout/dados/config mudam sem editar núcleo; pacote com limitações e rollback |

Os lotes são verticais. M3/M4 incorporam somente os hooks mínimos de HUD/PSG
necessários à prova; M6 completa a apresentação. Inventário/offline/UI textual
podem avançar em ramo independente enquanto M1/M2 medem, sem integrar código
com o mesmo owner. Não deixar o front-end inteiro esperar uma VM universal.

## Matriz obrigatória por capacidade

Registrar arquivo/section/action/controller/trigger fonte, SHA, papel, lowering,
consumidor C, teste diferencial, ROM/SHA/sessão/trace, custo e estado:
`exact`, `approximate`, `blocked`, `dropped_by_owner`.
Parsed/generated/consumed/observed/budget_validated continuam níveis separados.
Qualquer unsupported alcançável em movimento exigido bloqueia sua aceitação;
inventário de comandos emitidos nunca conta como movimento implementado.

Controllers prioritários: ChangeState/ChangeAnim, anim/time/ctrl/state/facing,
pos/vel/physics, HitDef/guard/hitpause, Life/Power/Var, Projectile, Explod,
Pause/SuperPause, Target e Helper quando efetivamente usados. AssertSpecial
com efeito de combate não pode virar noop. Preservar ordem triggerall/triggerN,
short-circuit/precedência, units, AnimTime/AnimElem, var lifetime e cancel.
Não presumir que todos esses recursos já existem nem impor 40 controllers MD
como requisito inicial: alcance real das fontes determina o backlog.

## Bloqueios já conferidos

- `palette_contract.py`: import quebrado e modelo PAL0–3/SGDK; substituir por
  contrato SMS ou isolar como legado. Não resolver apenas com alias de import.
- VM host existe; emissor/runtime CNS geral C não foram encontrados. FSM
  atual reconhece subconjunto e não executa predicados arbitrários do fonte.
- Stage parser órfão não é prioridade, pois o pedido mantém todas telas sem
  cenário. Registrar ausência; não gastar M0/M1 implementando stage converter.
- Testes antigos acoplados a doc de `luta_mugen` não qualificam rev2. Separar
  unit fixtures autocontidas de testes de integração `--project`/manifest.
  Skip de dependência antiga permanece `not_run`, não PASS do jogo novo.
- Ambos DEF referenciam `common1.cns` ausente nos ZIPs doadores. Não extrair
  de uma instalação desconhecida nem assumir equivalência do `common_forge`.
  Permitir piloto explicitamente limitado às actions resolvidas; fechamento
  de gameplay requer fonte comum autorizada ou adaptação diferencial explícita.
- `/run/user/1000` estava sem espaço. Novo diretório no cartão não repara
  filesystem. Checar os destinos reais do runner, inclusive configuração/cache,
  antes de iniciar sessão; sem limpeza de processos/arquivos de terceiros.

## Harness operacional

Coordenador integra, aprova claims, atualiza memória e guarda os contratos.
Até três especialistas ativos, sem delegação recursiva:

1. **Semântica/compilador:** intake, compat matrix, lowering/controllers e
   testes fonte→IR→C; escreve apenas arquivos centrais reservados.
2. **VDP/assets:** escala/paleta/metasprites/BG/híbrido, banco/VRAM/SAT e
   artefatos de medição reservados. Não reautoriza arte.
3. **QA/áudio/gamefeel:** casos por ROM exata, sessões próprias, feedback
   nativo e cobertura. Alternar foco ao delta; medição FPS serializada.

Reviewers distintos de seus produtores. Preparar pedido V2 com snapshots de
memory/GDD/spec/TDD e relação independent/chained; workers não partilham sessão.
Não usar nomes de agentes em JSON para simular delegação. Antes de gravar
visual/planilha, registrar reserva no artifact_registry; runtime branches têm
write_paths exclusivos. Não dividir módulos fortemente acoplados em writes
paralelos; um ramo fica com o coordenador até interface estável.

## Gates de fechamento

Build central; recursos/proveniência; sprite mode/scanline; mapa VRAM;
corredor probe e mapa RAM/stack; símbolos/SIZE; contrato engine/import semantics;
AIR identidade N+1 quando aplicável; render fidelity/glitch em timeline;
gameplay/IA/input; FPS regional e worst-frame; áudio privado/proveniência/mix;
review independente, contexto e memória atuais. Consultar CLI existente antes
de escrever comandos; ferramenta proposta começa como proposta, não executável.

Emulicious é produção/QA SMS. BlastEm privado é diagnóstico complementar de
RAM/VDP/mapper; GDB M68K e testes MD não provam Z80/SMS. Não herdar claims de
uma ROM/fixture anterior. PAL/hardware/som exato só sobem com suas próprias provas.
