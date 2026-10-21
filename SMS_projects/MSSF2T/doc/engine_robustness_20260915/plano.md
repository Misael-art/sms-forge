# Plano de robustecimento — engine de luta para Master System

Data: 2026-09-15. Proposta de desenvolvimento, não claim de implementação.

## 1. Resultado que define sucesso

Um autor consegue criar outro jogo de luta 1v1 trocando **pacotes de conteúdo e configuração**, sem alterar o núcleo de combate, renderização, input ou áudio. A ROM resultante preserva resposta consistente, golpes legíveis, integridade gráfica, música com espaço para impactos e orçamento comprovado.

Entregáveis finais: biblioteca C pequena, compilador de conteúdo offline, schemas versionados, exemplos editáveis, manual por tarefa, jogo de referência com dois lutadores distintos, segundo jogo de demonstração de reuso e suíte de regressão no alvo. Um editor visual pode melhorar o fluxo; não deve atrasar um formato simples e utilizável.

O MSSF2T permanece projeto hospedeiro. Não renomear a pasta nem migrar tudo para outra árvore. Separar conteúdo específico Ken/Guile da engine. Assets de referência continuam exemplos de estudo enquanto não tiverem proveniência final comprovada.

## 2. Escopo e regras recomendadas

### Base obrigatória da engine v1

- Luta local 1v1: humano × humano, humano × CPU e treino.
- Dois botões: B1 soco, B2 chute, cima pulo; direção contextual e comandos especiais configuráveis. Não depender de botão Start de controle inexistente; Pause do console requer contrato próprio.
- Normais de pé/agachado/no ar, high/low/mid declarados, guarda e blockstun, hitstun, hitstop, pushbox, colisões, knockback, knockdown e wakeup.
- Projétil, comandos de movimento e charge, cancelamento por tabela, multi-hit com identidade, trades, KO/timeout/empate e regras de rounds configuráveis.
- Throw como capacidade v1 após fundamentos, com alcance, startup, prioridade, invulnerabilidade/escape declarados; não adicionar ao slice antigo implicitamente.
- Personagens e cenários por registro; paleta compartilhada validada para cada matchup, inclusive mirror match.
- BGM PSG e SFX com prioridade; música e áudio independentes do congelamento de gameplay.
- Treino: dummy parado/guarda/pulo, input visível, boxes debug, avanço de frame e replay com seed. Debug não integra imagem final.

### Escopo posterior, condicionado a medição

Super meter, cancelamentos avançados, IA extra, cenários com câmera larga, FM opcional, save, campanha e editor gráfico completo. Não iniciar netplay, roster massivo, PCM por software ou múltiplas variantes de hardware como pré-requisito. FM só amplia um PSG já completo; nunca vira dependência do jogo base.

As mudanças acima ampliam o GDD atual. Quando este plano for invocado para implementação, registrar essa nova finalidade e a fronteira da v1 nos docs antes do código. A entrega atual é apenas plano e prompt.

## 3. Arquitetura proposta

```text
src/engine/   input, command, fighter, combat, collision, physics,
              round, animation, render_sms, vram_queue, bank,
              audio, stage, scene, replay, debug_probe
inc/engine/   contratos públicos pequenos, com versão
content/      game, fighters, moves, stages, audio, rules
res/          recursos convertidos e rastreados
rascunho/     fontes de referência e experiências isoladas
```

Estrutura é proposta: o wrapper atual compila `src/*.c`; testar descoberta recursiva antes de mover fontes para subpastas. Se a política de curadoria ainda impedir adaptar o wrapper, usar prefixos de arquivo em `src/` temporariamente com os mesmos limites de módulo. Não quebrar build para obter uma árvore bonita.

O runtime consome tabelas C/binárias geradas; **não** parseia JSON/YAML no Z80. Começar por JSON para reduzir dependências. Evitar uma VM genérica de scripts ou um sistema de plugins dinâmicos. Extensões especiais usam enum/opcodes limitados e handlers fixos medidos.

### Contratos mínimos

| Contrato | Dados essenciais |
|---|---|
| GameDef | versão, roster, stages, ruleset, controles, região suportada |
| FighterDef | ID estável, dimensões/pivô, velocidades, salto, vida, moves, animações, paleta |
| MoveDef | comando, estados permitidos, startup/active/recovery, eventos por tick, boxes, dano, stun, pushback, hitstop, cancels |
| AnimFrame | duração, fonte/hash, bank/offset/size, metasprite, pivô, residência/prazo |
| BoxDef | tipo hit/hurt/push/throw, retângulo local, janela, nível, invulnerabilidade |
| ProjectileDef | pool, velocidade, lifetime, contato, clash, persistência após hit/KO |
| StageDef | chão/bounds, tiles/mapa, slots, paleta, bandas raster, música |
| Ruleset | rounds, timeout/tie, chip KO, guarda aérea, trades, cancel/meter opcionais |
| AudioCue | fonte/hash, banco, canais, prioridade, cooldown local, retomada |
| CombatEvent | tick, instância do ataque, hit index, atacante/alvo, hit/block/throw/KO |

As estruturas finais dependem de `sizeof`, linker map e profiling SDCC. Não copiar o tamanho dos tipos da HAMOOPIG. Separar IDs de personagem, índices de jogador e IDs de estado.

### Ordem do tick

1. Ler ambos os controles e produzir held/pressed/released; armazenar histórico inclusive em hitstop.
2. Reconhecer comandos usando facing temporal e janela declarada; consumir cada pedido uma vez.
3. Se simulação congelada, manter relógios que o Ruleset permite e preservar inputs; áudio/render seguem seu clock.
4. Atualizar intenções, física, estado e animação lógica para os dois jogadores.
5. Construir boxes de um snapshot; detectar contatos sem alterar o adversário durante a coleta.
6. Resolver contatos, prioridade/trade, dano/stun/pushback e resultado do round de forma determinística.
7. Emitir eventos para HUD/áudio/FX; consumidores não alteram novamente o dano.
8. Preparar SAT, deltas e buffers fora da janela de upload; fazer commit de VRAM e SAT no período seguro.
9. Publicar probe coerente com tick, pose lógica, pose apresentada, filas e custos.

Fazer uma prova mínima dessa ordem antes de generalizar todas as estruturas.

## 4. Estratégia gráfica: legibilidade dentro de limites reais

Baseline: 256×192, modo de sprite 8×16, canvas existente 32×64 preservado até decisão explícita; 16 KB VRAM, 8 KB RAM, 64 sprites totais e 8 por linha. Não impor números de Mega Drive. Slots de pattern, tilemap e SAT devem constar de um mapa de endereços sem sobreposição.

**32 px de largura não obriga quatro colunas opacas em toda linha.** A direção de arte deve medir perfis de ocupação por faixa de Y e ação. Dois corpos de quatro colunas já usam oito entradas; com projétil, é preciso redesenhar composição/pose ou escolher representação alternativa comprovada. Posição X distante não reduz essa soma.

Testar, antes da arte completa, três rotas:

1. Frames críticos residentes e metasprites esparsos: base prioritária, menor atraso e complexidade.
2. Corpo reaproveitado + tiles diferenciais de braço/perna: somente com fonte autorada e qualidade de pose preservada, sem boneco articulado rígido como resultado final.
3. Composição híbrida em BG para elemento compatível: experimento isolado, medindo restauração do cenário, alinhamento, oclusão e custo. Não assumir que resolverá toda luta.

Para ROM, comparar flip pré-gerado com bitrev no Z80 após banking. ROM extra pode comprar CPU, mas **não** elimina bytes enviados à VRAM. Medir chunks 64/96/128/192/256 somente com instrumento válido, além de cache/deltas. Registrar onde falha e selecionar solução pelo pior frame e atraso, não pela média.

O compilador rejeita um MoveDef cujo frame de contato não pode estar disponível no tick ativo. Medir `requested_tick`, `ready_tick`, `presented_tick` e starvation por jogador. Prefetch durante idle/startup deve ter prazo demonstrado. Não aceitar hitbox nova com membro antigo visível. Política de falta de cache não pode tornar startup variável; conteúdo deve caber no cronograma aprovado.

### Meta de animação e direção artística

Amostra inicial: idle 3–4 poses; caminhada 4–6; soco/chute ao menos antecipação, contato e recuperação semanticamente distintos; salto com saída/ápice/queda; hit, block, knockdown, wakeup, vitória e especial próprios. São metas de autoria, não promessa de que todos os frames únicos caibam residentes. Reaproveitar tiles com disciplina e ajustar após o experimento.

Manter apoio do pé e pivô estáveis, silhuetas separadas em ambos os lados, extensão clara de mão/pé, timing de peso e cor de foco distinta do cenário. Revisar nativo e ampliado por nearest-neighbor. Cais: reduzir competição de linhas do deck, hierarquia de luma e repetição visível; cenário original novo segue storyboard → coreografia → medição → contrato → arte. Não produzir cenário/personagem final por primitivas.

## 5. Banking, RAM e build

- Primeiro fixture: dados conhecidos em dois bancos, leitura cruzada, interrupções e checksum esperado. Não copiar a spec antiga sem corrigir capacidade/endereço.
- Perfil de crescimento inicial a avaliar: 64/128 KB, expandindo para 256 KB quando o inventário justificar. Declarar tamanho físico final e suporte do mapper/conversor reais.
- Código do loop/ISR fixo. `BankedAssetRef={bank,offset,size}`; acesso limitado ao tempo em que o banco está mapeado. Não guardar ponteiro cru e trocar o banco antes de consumi-lo.
- Owner único do slot 2; restaurar banco em todos os retornos e ao redor de atualizações PSG. Escolher PSGlib normal ou MULTIBANK coerente com biblioteca linkada e headers.
- Reservar faixa dos probes e medir high-water da pilha. Mapear BSS, buffers, cache e stack; fracassar no build se houver interseção.
- Build reproduzível de conteúdo: tamanhos/bancos derivados, fontes/hash, saída determinística, diagnóstico de excesso de ROM/VRAM/SAT por asset.
- Toda lógica compartilhada de compilação permanece no wrapper. A spec vigente exige aprovação explícita de curadoria; preparar patch revisável, regressões e memória antes dessa decisão, se ela não tiver sido dada na sessão de implementação.

## 6. Gameplay e áudio: barra de qualidade

### Gameplay

Default proposto: reconhecimento aceita input válido no próximo tick de simulação; nenhum frame extra por fila de render. Medir atraso em ticks com replay e depois input real. Input→ação não é tempo da captura do host. Buffer inicial de ação a testar: 4–6 ticks, janela de comando 12–20, configuráveis; não tratar esses números de design como lei de hardware.

Testar footsies (aproximação/recuo), whiff punish, anti-air, high/low, salto por cima, corner escape e colisão no pouso. O treino precisa tornar esses testes previsíveis. IA usa o mesmo canal lógico de comandos, com reação/cooldown/dificuldade definidos; não lê input futuro nem injeta hits diretamente. CPU deve respeitar facing após troca de lado.

PAL/NTSC: escolher explicitamente política de ritmo. Recomenda-se perfis de 50/60 ticks com durações geradas preservando aproximadamente o tempo real e mantendo mínimos de ativo; todos os casos são revalidados em ambos. Alternativa 60 sim ticks em PAL exige provar custo de ticks duplos e apresentação. Não declarar suporte PAL somente por ajustar o timer.

### Som

Arranjo PSG base com melodia legível, baixo/ritmo e envelope coerente, reservando interrupções para SFX. Cue prioritário KO > impacto relevante > especial > interface, ajustável. Block e hit precisam soar distintos; cooldown por cue/canal evita que um disparo silencie impacto importante. Restaurar música sem nota presa após cada SFX.

Critérios: loop musical sem corte involuntário; mudança de banco sem corrupção; ataques consecutivos com feedback reconhecível; pausa/reset limpos; ausência de clipping digital e silêncio acidental, com escuta crítica registrada. Capturar pelo menos 60 s de combate pesado e BGM isolada; dados de sinal complementam a escuta. Testar 50/60 Hz e hardware/perfil PSG suportado. YM2413 fica extensão futura.

## 7. Backlog executável por marcos

| Marco | Dependência | Trabalho concreto | Saída / gate |
|---|---|---|---|
| M00 Baseline confiável | nenhuma | snapshot SHA, preservar alterações locais, fontes/gates, erros do laudo e instrumentos | mapa de verdade; comandos reprodutíveis; teste negativo de cada instrumento usado |
| M01 Correção essencial | M00 | buffer 128/96, normalização P2, modos humanos, reset, contatos simétricos, timeout/empate | fixtures antes falham e depois passam; casos 1P/2P/KO no alvo |
| M02 Medição e ROM bancada | M00; M01 para integração | probe por fase, stack, missed VBlank, mapper e áudio com banco | mapa sem overlaps; banking com áudio/ISR; contadores não saturam silenciosamente |
| M03 Render com prazos | M01,M02 | cache/residência, fila justa, SAT real, deadlines de pose | zero contato visual atrasado nos moves base; ≤8/linha e ≤64; nenhum upload fora da janela contratada |
| M04 Conteúdo compilável | M01,M02 | schemas/tabelas, FighterDef/MoveDef/StageDef, erros compreensíveis | um golpe novo só por dados; output determinístico; fixture inválida reprova com campo/causa |
| M05 Núcleo de luta v1 | M03,M04 | comandos, charge, guarda/stun, aéreos, cancels, throw/multi-hit e regras | matriz funcional determinística nos dois lados; input real confirma experiência |
| M06 Slice artístico e sonoro | M03,M04; integra M05 | 2 lutadores distintos, 1 cenário, animações completas, BGM e SFX | vídeo de ações, revisão visual, escuta e budgets simultâneos |
| M07 Ferramentas para o autor | M04,M06 | preview timeline/boxes/scanline, treino, mensagens de erro, tutorial | autor cria variante de lutador e cenário sem editar núcleo |
| M08 Prova de engine | M05–M07 | segundo pacote de jogo, terceiro lutador de perfil distinto, segundo palco | duas ROMs com mesmo núcleo; troca de conteúdo altera somente dados/assets/registro |
| M09 Robustez final | M08 | soak, transições, duas regiões, inventário, regressão e documentação | matriz completa ligada às SHAs finais; sem bloqueador crítico; status por eixo |

Cada marco pode exigir vários ciclos. Não há estimativa honesta de dias antes de M02/M03; banking e renderer são as maiores incertezas. Critério de replanejamento: se frames críticos não cumprem o prazo, interromper expansão do roster e rever representação com medições. M06 pode conceber arte antes, mas só produz folhas definitivas depois do contrato M03.

## 8. Matriz de aceitação

| Família | Casos mínimos |
|---|---|
| Input | cada botão/direção P1/P2; neutral humano; held/pressed/released; diagonais opostas; comandos válidos/negativos; lados trocados; input em hitstop |
| Contatos | hit/whiff/borda exata; high/low; block frontal/costas; agachado; aéreo; trade; dupla KO; hit de projétil simultâneo; multi-hit único por índice |
| Regras | KO P1/P2; timeout desigual/igual; empate seguido de round; vitória final; reset em hitstop/projétil; histórico limpo |
| Render | poses e lados; virar repetidamente; ambos mudam pose; contato com 2 projéteis; corner; mirror match; zero starvation; pose ativa apresentada a tempo |
| Memória | maior matchup; pilha/probe; bancos cruzados; música em banco distinto; asset excessivo rejeitado |
| Som | BGM; block/hit/KO; repetição rápida; prioridade; loop; reset; bancos; áudio no pior frame |
| Estabilidade | 100 ciclos título→luta→resultado→título; 30 min CPU×CPU; pelo menos 10.000 ticks de stress por perfil regional |
| Autoria | adicionar golpe, lutador, cenário e ruleset; erro de paleta/tempo/banco/box aponta campo; segundo jogo sem patch do core |

Metas de aceitação: zero corrupção/missed simulation tick fora de política declarada; zero overflow de sprites nos casos suportados; zero transferência tardia nos frames medidos; casos de gameplay com resultados esperados; áudio/visual revisados. Reportar máximo, distribuição e contexto, não só FPS médio. Medir degrau seguinte em laboratório e registrar falha/fallback: ambição com evidência.

Emulicious é a rota SMS deste workspace. Segundo emulador e hardware real ampliam confiança e devem constar separados; não exigir BlastEm para SMS por herança de SGDK. Um test runner host é útil, mas modelo Python do combate não prova o C compilado; usar núcleo C em harness quando possível e confirmar no Z80 por replay/probe.

## 9. Fluxo do autor e critério de facilidade

1. Copiar pacote exemplo, preencher nome/regras e selecionar controles.
2. Importar arte permitida com pivô/paleta; ferramenta exibe custo de tiles e scanline.
3. Editar MoveDef em timeline, anexar boxes/eventos; preview mostra startup, contato e recuperação.
4. Compilar dados e validar matchup. Excesso aponta frame e alternativas; não reduz escala sozinho.
5. Rodar build pelo wrapper, abrir treino e gravar replay/captura.
6. Produzir ROM e inventário com versão do core, assets e relatórios.

Começar com CLI + arquivos legíveis; depois preview local de timeline/boxes. A CLI proposta ainda não existe: o agente deve projetar comandos e documentar o uso real após implementá-los. Medida de facilidade: uma pessoa seguindo somente o tutorial consegue criar um normal, uma variante de personagem e um segundo palco; registrar tempo, erros e quantidade de arquivos editados. Gate estrutural: zero edição manual em `src/engine` nesses exercícios.

## 10. Persistência sem ciclo vazio

Cada ciclo deve atacar um bloqueador ou entregar capacidade verificável: hipótese → alteração limitada → teste → build → observação → evidência → memória. Duas falhas equivalentes pedem hipótese/rota diferente; não relaxar o teste nem só renomear reports. Ao faltar arte/revisão humana, seguir módulos independentes e manter o candidato em staging. Ao acabar contexto, salvar o comando seguinte e o teste pendente, sem promover status.

A conclusão exige capacidade de autoria comprovada e slice sensorial aprovado. Mais Markdown, menus, opções ou contagem de arquivos não substituem jogos montáveis e luta legível.
