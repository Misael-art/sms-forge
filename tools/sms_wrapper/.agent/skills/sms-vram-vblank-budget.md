# skill: sms-vram-vblank-budget

## Não existe DMA
Toda transferência em massa passa pela CPU dentro do VBlank (~4.5ms NTSC).

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
  Escritas fora do VBlank deixam resto na tela; limpar linha a linha não
  fecha a classe (L047).
