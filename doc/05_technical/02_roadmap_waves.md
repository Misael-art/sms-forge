# Roadmap de maestria Master System

O registry `01_registry_maestria_sms.json` distingue conhecimento mapeado de
evidência indexada. Em 2026-10-27, os 32 registros antes promovidos foram
reconciliados para `mapped`, mantendo `legacy_claim`. Provas históricas podem
ser reindexadas, mas não aprovam uma ROM nova. A antiga afirmação de Wave 0
conquistada não tinha custódia suficiente no registry.

## 0. Recuperar a prova existente

Owner: curadoria, `audit_mastery_registry.py` e workflow `laboratory-mode.md`.
Priorizar provas já existentes de tiles/PNT, sprites, paleta, mapper e input.
Vincular fonte, build, ROM, mídia e relatório com SHA completo e escopo.
O gate valida custódia, não julga conteúdo ou confirma execução por si.
Ausência no host exige restaurar a evidência pelo mecanismo de continuidade,
sem reconstruir a história a partir de um teste novo.

## 1. Fechar uma interação de produção

Owner: consumidor atual, `first-playable-slice.md`. Para `luta_mugem_rev2`,
reutilizar o backlog de 55 itens, começando por ID01 e R01/R02/R03/R05/R06/R09.
Provar dois atores completos, streaming com prazo, pose/contato coerentes e
budget conjunto. Acrescentar R10/IN05 para cadência e resposta. Não ampliar
elenco nem criar outra engine durante esse fechamento.

## 2. Tornar a interação legível e interessante

Owner: direção, `game-design-core-loop.md` e `product-quality-checkpoint.md`.
Escolher referência por aspecto, desenhar aprendizado/decisão/recuperação,
medir movimento e câmera do gênero, ouvir música e SFX sob carga e registrar
teste com jogadores. Uma nota de agente não certifica diversão.

## 3. Explorar um degrau técnico que beneficie o jogo

Owner: laboratório; perfil/hipótese, controle e próximo degrau medido.

| Candidata | Benefício a demonstrar | Custo e contraprova |
|---|---|---|
| V04/R01 line IRQ e h-scroll | profundidade legível sem perder ação | jitter, custo ISR, HUD e scroll em retorno |
| M04 streaming/cache | mais poses sem resposta atrasada | prazo por ator, uploads, invalidação, starvation |
| P04/P05 transformação/ciclo de paleta | materiais e atmosfera legíveis | P0/P1 compartilhadas, alterações indesejadas no HUD/ator |
| B02/Z06 bancos | conteúdo além da residência atual | banco fixo, ponteiros, ISR e fronteiras do linker |
| A03 samples PSG | evento sonoro com função clara | CPU/ROM, mix e continuidade do jogo |
| A04 FM opcional | arranjo alternativo autoral | driver/target e experiência PSG completa |
| I03 NTSC/PAL | mesma intenção de tempo nas regiões suportadas | movimento, input, animação, andamento e budgets por alvo |

R02 (paleta raster) permanece hipótese com perfil de VDP explícito. R03 não
é scroll Y nativo por coluna: qualquer ilusão equivalente precisa de outra
representação medida. Half-brightness/add-sub são transformações de paleta
da biblioteca, não unidades de blend do VDP. S05/S06 usam a correção L003:
X sem offset e shift de 8 px. Não reabrir a hipótese refutada de 32 px.

## 4. Reproduzir e entregar

Owner: integração/QA; receita reproduzível, testes de borda e soak, alvos
regionais declarados, revisão independente e sete eixos na mesma ROM.
Experimentação em emulador e ensaio em console físico são qualificações
distintas. Medir em revisão de hardware declarada antes de prometer
compatibilidade universal. Não existe wave que certifique qualquer gênero.

Avaliação e prioridades: `doc/curation/2026-10-27_production_capability_review.md`.
