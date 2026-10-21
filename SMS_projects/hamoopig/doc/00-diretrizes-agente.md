# 00-diretrizes-agente — hamoopig

> Autoridade #4. Lei global permanece em `tools/sms_wrapper/.agent/rules/SMS_GLOBAL.md`.

## Princípio de jogo (obrigatório — leia antes de qualquer ação)

Este projeto se mede pela **régua de jogo AAA**: o que o jogador vê e sente
tem de ser luta, não probe técnico.

1. **Nenhum lutador em pose estátua.** Idle e walk exigem ciclo (≥4 quadros
   distintos quando a folha da origem tiver). Golpe exige ≥3 quando a strip
   tiver. Um quadro por estado **não é entrega**.
2. **Os dois lados do roster.** O que vale para Ryo vale para Musgo. Não
   “completar P1 e deixar P2 estático”.
3. **Evidência de ciclo, não de still.** Screenshot único não prova animação.
   Dois stills com pose distinta ou `capture_video` do framebuffer.
4. **Não fechar atalho.** Cortar quadro do Musgo para caber em 32 KB, desenhar
   retângulo no grid, ou promover boot/HUD a qualidade visual **reprova**.
   O teto é mapper + stream 96 B, não pose única.
5. **Selo de fábrica `ready_for_aaa`.** Continua false até os 7 eixos + época
   `delivery`. Isso **não** autoriza trabalho abaixo da régua. A régua é o
   princípio; o selo é o gate.

Qualquer tarefa (arte, FSM, stream, ROM, docs) que viole 1–4 está desalinhada.
Pare e realinhe antes de commitar.

O desvio de 2026-09-19 (“silhueta técnica em C”) está **encerrado**.

## Ordem de leitura
1. `AGENTS.md` da raiz
2. `SMS_GLOBAL.md`
3. este arquivo (princípio acima)
4. `doc/11-gdd.md`
5. `doc/10-memory-bank.md`
6. `doc/CONTINUIDADE.md`

## Origem
`/mnt/sdcard/Projects/Sgdk Forge/SGDK_projects/HAMOOPIG [VER.001] [SGDK 211] [GEN] [ENGINE] [FIGHTING]/`
Não modificar. Cópia de pesquisa em `import/`. Sem caminhos absolutos no produto (ROM/código).
