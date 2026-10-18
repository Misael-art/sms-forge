# Prompt para o agente implementador

Você é o coordenador de produção do SMSForge. Implemente o consumidor paralelo
**luta_mugem_rev2**, uma engine de luta reutilizável para Master System que
importe o máximo tecnicamente viável de dados MUGEN. Os pilotos são **Ken e
Ryu dos pacotes raw usados pelo Mugenesis no SGDK Forge**. O destino é SMS,
não Mega Drive. O usuário autorizou a implementação progressiva, especialistas
e testes. Não trate este prompt como pedido de apenas diagnóstico ou plano.

## Contexto obrigatório

Workspace `/mnt/sdcard/Projects/SMSForge`.
Projeto `/mnt/sdcard/Projects/SMSForge/SMS_projects/luta_mugem_rev2`.
Leia AGENTS e diga `[Contexto SMS Carregado]`; leia RTK, arquitetura/lei central,
memory bank, GDD, spec e TDD do projeto e `doc/20-plano-implementacao.md`.
Leia `doc/22-intake-doador.json` e os pareceres preservados em
`data/intake/2026-10-15/`. Anexos não sobrepõem código/estado observado.
Fontes de verdade do doador: memory/context/matriz atuais, não `out/rom.bin`.

O projeto nasceu de bootstrap novo. Não depende de documentos ou outputs do
`luta_mugen` antigo, cujo `doc/` retorna EIO. Não copie aquele diretório, não
contorne o gate de contexto e não declare o cartão reparado. Faça preflight
de leitura, escrita e espaço nos destinos reais antes de build/testes.
`/run/user/1000` foi observado sem espaço em 15/10; não apague conteúdo alheio
nem altere globalmente o host. Se precisar de destino alternativo, adapte só
o processo/sessão em caminho explícito e verifique dependências do runner;
trocar TMPDIR sozinho não muda automaticamente o root das sessões.

## Meta jogável e limites

Ken/Ken primeiro, Ryu/Ryu depois, por fim Ken/Ryu e Ryu/Ken, com paleta P2,
controles/IA e todos golpes alcançáveis classificados por fidelidade. Normais,
defesa, saltos, colisão/hitstun, especiais, magias/projéteis, supers/power,
sparks, HUD, rounds/KO/timer/empate, hitstop/slowdown/shake finitos. Completar
título/PressStart, Arcade/Versus/Treino/Options, seleção/retratos, VS,
continue/final. Options e treino conforme GDD. **Todas telas com fundo sólido,
sem cenário ou backdrop**. Nenhum stage converter é pré-requisito deste produto.

Objetivos NTSC60/PAL50, resposta fluida, visual impactante e zero omissões
visíveis precisam ser pagos na ROM. Não prometer que sprites grandes cabem.
Antes do scheduler, calcule o limite inferior exato por scanline com dois
atores/poses/facing/FX reais: se exigir >8 objetos, sprite-only sem omissões
é impossível nessa composição. Escolha por medição BG/híbrido/cache/layout ou
proponha ajuste de escala/arte autorizado. Não esconder frames, remover IA/FX,
reduzir elenco ou congelar a simulação para obter um número bonito.

## O que reaproveitar e o que falta

`tools/sms_wrapper/mugen2sms/` tem parsers/SFFv1/PCX/AIR/CMD/CNS/IR/VM host,
conversão tiles/metasprites/paletas e runtime FSM restrito. Isso não é execução
CNS geral na ROM. O lowering atual declara que predicados/controllers da fonte
não são executados por suas tabelas. Não rotular FSM hardcoded de compatibilidade
MUGEN. `palette_contract.py` ainda contém import/modelo MD incompatíveis; reparar
como contrato SMS ou colocar em quarentena explícita, sem alias cosmético.
Parser stage sem consumidor fica documentado fora de escopo nesta revisão.

Do SGDK aproveitar precedência/AnimTime/controller semantics, matrizes de
fidelidade, provas fonte→dados→ROM, common-state profile, UI lifecycle,
instalação versionada/rollback e testes. Reimplementar custo/ABI no Z80.
Não copiar PAL0–PAL3, DMA, H40, XGM2, estruturas M68K ou limiares MD como SMS.
Options/Treino novos do MD estão `implementado/unbuilt`, não comprovados na ROM.

Ambos raw DEF pedem `common1.cns` ausente. O `common_forge.cns` é adaptação,
não equivalência demonstrada. Catalogue os estados dependentes e feche fonte
autorizada/equivalência antes de aceitar esses movimentos; diagnóstico limitado
pode avançar em ramos sem dependência, declarando a fronteira. Não inventar
common states para fazer o preflight passar silenciosamente.

## Como implementar

Siga lotes M0–M8. Comece agora pelo intake/preflight e piloto visual, em paralelo
com testes/compilador independentes quando possível. Priorize subconjunto CNS
alcançável AOT por perfil e predicados reais; compare VM compacta só com números.
Não bloquear o primeiro slice por VM universal, nem incorporar comportamento
por nome Ken/Ryu no C comum. Para todo recurso: fonte/section/trigger→IR→dados
→consumidor→teste diferencial→ROM/trace/budget. Unknown/unsupported têm motivo;
approximate precisa contrato e decisão; dropped exige decisão explícita.

Controle SMS tem dois botões. Derive perfil de CMD por lutador, com prioridade,
facing, release/hold/tier/contexto, cancel e one-pulse. Registre comandos sem
rota e conflitos; não sacrificar magias/supers silenciosamente. IA deve passar
pelo mesmo caminho de input e permitir prova causal, não escrever dano direto.
Teste defensor móvel, guard, lados, bordas, simultaneidades e reset dos objetos.

PSG/SND: som PCM importado não vira XGM2 no SMS. Classificar, transcrever ou
reautorar com proveniência e aprovação adequada; voz Fight é candidato medido
na abertura, com alternativa declarada. Conferir bit2 do noise, afinação,
arbitração/restauração de canais, mix música+SFX sob carga e audição independente.
Preview Python e peak não certificam qualidade musical. Não gerar arte final
por código; retratos/fontes/FX precisam fonte/contrato, não placeholders promovidos.

## Harness e teste

Use a ferramenta nativa para no máximo três especialistas ativos:
semântica/compilador; VDP/assets/budget; QA/áudio/gamefeel. Planeje com Harness,
reserve artefatos e write_paths não sobrepostos; coordenador integra, decide
claims e atualiza memória. QA por produtor diferente, sessão privada por worker,
pedido V2 e snapshots production legíveis. Não simule agentes em arquivos.
Cada worker retorna status, ROM/SID/SHA, cobertura, evidências, defeitos e cleanup.

Parametrize testes de integração para rev2 e fixtures temporárias unitárias;
remova dependência obrigatória dos manifestos EIO para o novo projeto sem
fabricar doação/binding. Não contar skipped/xfail/blocked como capacidade pronta.
Build/conversores/gates vivem no wrapper central; projeto é consumidor.

Emulicious para aceitação SMS; BlastEm privado para hipótese RAM/VDP/mapper.
Frames stepped provam sequência, não velocidade. Medir probe regional, pacing
da lógica, entrada→reação→pose→dano e pior VBlank em execução contínua; contador
ISR sozinho não comprova gameplay60. RAM total8KiB, VRAM16KiB compartilhada,
SAT64/8porlinha incluindo hidden, P1 compartilhada com15cores úteis, semDMA.
Mapa pós-link/corredor de sondas/stack/banks e buffers devem ser auditados.

Mudar DEF deve regenerar dados sem editar núcleo. Após cada lote: memória com
fontes/ROM/hash/casos/números/limites/blocker/próxima ação. Relato intermediário
`Resultado / Bloqueio / Próxima ação`. Persistir pelo ramo causal seguro;
não encerrar após inventário, parser, build, boot ou primeiro golpe se há
trabalho autorizado viável. Se houver bloqueio real, registrar sem mascarar e
avançar nos ramos independentes. Não apagar histórico nem commitar/publicar
sem a autorização aplicável. Entrega só após todos os eixos e reviews atuais;
não herdar AAA/FPS/áudio do MD, do legado ou de uma fixture.
