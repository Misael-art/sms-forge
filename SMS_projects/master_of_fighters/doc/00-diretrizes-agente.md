# 00-diretrizes-agente — master_of_fighters

> Regras de processo deste projeto. Autoridade #4.
> Não duplica a lei global: `tools/sms_wrapper/.agent/rules/SMS_GLOBAL.md` continua
> sempre ativa. Aqui ficam só os desvios e decisões LOCAIS deste projeto.

## Ordem de leitura obrigatória
1. `AGENTS.md` da raiz do workspace
2. `.agent/rules/SMS_GLOBAL.md`
3. `doc/10-memory-bank.md` (este projeto — estado real)
4. este arquivo

## Regra de ferro
**"Se não foi visto rodando no emulador, não existe."**
Vocabulário obrigatório: `documentado ≠ implementado ≠ buildado ≠
testado_em_emulador ≠ validado_budget`. Nunca pule um degrau na fala.

## Desvios locais aprovados
> Todo desvio da lei global precisa estar AQUI, com data e justificativa.
> Desvio não registrado é violação, não exceção.

| Data | Desvio | Justificativa | Aprovado por |
|------|--------|---------------|--------------|
| — | nenhum até agora | — | — |

## Ordem de trabalho de cena (não negociável)
```
roteiro → storyboard (planta baixa em pixel) → coreografia → MEDIÇÃO → orçamento
→ contrato de asset → model sheet → assets → runtime → EVIDÊNCIA
```
Decisão barata antes de arte cara. Gate executável entre cada transição.

## Contrato técnico de arte SMS

Depois da aprovação humana do concept/model sheet e antes de qualquer asset em
res/, criar um contrato por personagem ou item e uma prancha de prova técnica
conforme `doc/asset_conversion_proof_standard_v4.md`. A prancha contém somente
duas poses-chave (idle e ação), não a folha animada. Usar
`doc/asset_conversion_contract_template_v4.json` e
`tools/compose_sms_keypose_proof.py` para registrar fonte/hash, resolução,
escala, baseline/pivô, paleta indexada, fundo de inspeção, inventário 8×8,
limites físicos e orçamentos pendentes. Grades e anotações ficam em painéis
separados e nunca atravessam os pixels do sprite. Para este jogo, adotar como
referência visual de escala *Fatal Fury Special* (Game Gear): faixa de trabalho
de 66–72 px de altura corporal na tela SMS, centro de 70 px, conforme GDD/TDD.
Não tratar o alvo como lei física nem como dimensão fixa de canvas. PNG por pose
deve ser dimensionado pelo conteúdo, tile-alinhado em múltiplos de 8 e deixar
ao menos 1 px transparente em cada borda; 96×96 não é padrão automático.

A contagem de padrões da arte não equivale a alocação de VRAM, objetos SAT,
orçamento de VBlank, integração ou entrega. Não há número físico universal de
quadros por folha: o TDD e `doc/13-spec-cenas.md` definem o limite do projeto a
partir de pools, ROM/banking e carga medida. Rodar
`audit_asset_proof_sheet.py --manifest <proof.json> --project-root .`; ele
confere a origem indexada, refaz qualquer conversão nearest-neighbor declarada,
compara os recortes da prancha pixel a pixel, e reprova canvas sem borda vazia,
tile desalinhado ou equipamento cortado no limite. Isso valida integridade
estrutural, não anatomia ou fidelidade visual.
Também revisar a silhueta semântica dos terminais de armas/acessórios: um item
sem corte ainda pode parecer outro objeto se sua ponta, pomo ou cabeça for
achatada. O contrato de cor separa paletas de autoria das tabelas de runtime:
P1 é compartilhada por todos os sprites, P0 atende cenário/HUD, P1 índice 0 é
transparente para sprites e BG índice 0 sempre mostra uma cor visível. P0
índice 0 é a cor de backdrop reservada pelo projeto.
Aplicar os 12 princípios da animação na folha completa, com timing e evidências;
duas poses não validam movimento. Manter a prova em `data/source_art/` até
revisão visual independente, resolução dos budgets e aprovação humana.
`audit_sprite_cutout.py` verifica pixels órfãos e regiões materiais; se o
contrato só declarar componentes, o resultado fica pending e não libera
promoção.
Promoção segue os gates globais de recursos, proveniência, entrega e vínculo
asset→ROM, além da validação no emulador.

## Ao encerrar sessão
Atualize `doc/10-memory-bank.md` com o estado REAL (não o pretendido) e deixe
handoff explícito do próximo passo bloqueante.
