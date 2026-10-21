# skill: sms-vram-vblank-budget

## Não existe DMA
Toda transferência passa pela CPU. A política de produção exige commits VDP
dentro da janela medida da cena, com orçamento de SAT/PNT/CRAM/patterns; não
usar uma duração aproximada fixa como prova de capacidade. Preparar lógica,
metasprites e filas no display ativo pode ser a escolha correta: toda a lógica
não precisa caber no VBlank.

L136/§127 mediu integridade de escrita fora do VBlank em dois emuladores;
isso não aprova tearing, prazo de apresentação ou efeito no ritmo. Separar
integridade dos bytes, janela de commit e deadline do loop. Um VCounter lido
apenas ao fim não exclui ter atravessado períodos inteiros; analisar serial,
região e voltas quando o caminho puder exceder um frame (§103).

## Orçamento = contrato
1. Listar transferências por frame (tiles, name table, SAT, paleta).
2. Medir worst-frame real (contador de ciclos/instrução + evidência de emulador).
3. Registrar em `13-spec-cenas.md` com campo `method` ≠ "estimado".
4. Fechar orçamento SEM medir o degrau seguinte é proibido (§18).

## Diagnóstico e validade dos dados (SMS_GLOBAL §§97–98)

Use baseline anterior ao trabalho e fronteiras da mesma janela selada antes
de atribuir derrames. `audit_stage_attribution.py` confere contagens e teto de
claim; não mede ciclos, nem aprova budget com overflow. Timestamps de duração
exigem tratar região e voltas do VCounter. Cota de 64 B/frame e banda de
admissão de um piloto não são throughput universal.
Selo/congelamento precisam de revisão fonte/probe e vínculo da observação;
consistência numérica sozinha não prova que os contadores pararam no selo.

Preparar colisão antes do VBlank só é seguro com validade de posição, facing,
hurtbox e estado até o contato. `audit_import_semantics.py` reprova registros
stale, mas o runtime e casos nativos precisam demonstrar invalidação/recompute.
Prova de P2 estacionário não aprova a versão dinâmica.

## Técnicas

Para otimizar caches/emissão SAT, use `sms-runtime-optimization.md` (§103).
Declare janela ativa e largura dos contadores: delta de byte pode esconder
voltas. `audit_counter_window.py --require-exact` mede unicidade sob limite
declarado; não prova a instrumentação. Preserve idle/FX/IA/áudio no alvo;
renderer-off e P2 passivo são controles diagnósticos, não budget de entrega.
- Streaming de tiles entre frames com cota fixa.
- Compressão ZX7/aPLib: descompressão custa CPU do frame — medir junto.
- `SMS_VRAMmemcpy*` / `SMS_loadTileMapAreaatAddr` — assinaturas SEMPRE no header.
- Transição de tela: **display off**, reescrever o mapa inteiro, display on.
  A receita fecha a classe de resíduos de transição de L047; não explicar o
  resultado por perda automática de bytes fora do VBlank (corrigida por L136).

## Mapa de VRAM e a janela do reg6 (SMS_GLOBAL §124, L133)

VRAM = 16 KB com layout de tabela: tiles 0-255 em `$0000-$1FFF`, tiles
256-447 em `$2000-$37FF`, tilemap em `$3800-$3EFF`, SAT em `$3F00-$3FFF`.
O índice de sprite é 1 byte na SAT: o sprite só alcança a janela de 256
tiles apontada pelo **reg6** — `$FB` base `$0000` (256 únicos), `$FF` base
`$2000` (192 únicos; default da SMSlib, troca por
`SMS_useFirstHalfTilesforSprites`, `SMSlib.h:53`). BG indexa 0-511 e não
sofre a janela.

Sobras têm **guarda**, não são espaço livre: `$3F40-$3F7F` (2 tiles, gap da
SAT), `$3E00-$3EFF` (8 tiles, só sem scroll vertical em modo 192),
`$3F20-$3F3F`+`$3FC0-$3FFF` (3 tiles, só com ≤31 sprites + `$D0` na 32ª
entrada, e o terminador `$D0` só vale em 192 — §118). Tilemap extra trocada
via reg2 (duplo buffer / menu / split HBlank estilo Sylvan Tale) consome
`linhas×64` bytes da zona de tiles e no SMS1 exige bit0=1 do reg2 (§121).

Ferramenta: `measure_vram_map.py --plan plano.json [--snapshots DIR]` —
julga colisões, janela do reg6, motivos de tilemap extra, sobras reclamadas
e confere reg5/reg6 vivos dos dumps `blastem_sms.py` contra o plano.
Na spec-cenas, o contrato declara endereços, janela de sprite e sobras
usadas; sem plano declarado, "cou porque sobrou" não é argumento.
Patterns BG, PNT e SAT precisam de regiões simultâneas disjuntas. Somar
current/pending dos dois atores, FX e HUD na mesma cena; comparar o custo de
um ator com a região inteira não demonstra que o par cabe.
