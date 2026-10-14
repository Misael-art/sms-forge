# skill: sms-banking-header

## Regras
- ≤48KB linear sem mapper (primeiro alvo de todo projeto).
- Mapper Sega: páginas de 16KB; slot 0 via 0xFFFD, slot 1 via 0xFFFE e
  slot 2 via 0xFFFF. Somente 0x0000–0x03FF permanece na página 0;
  0x0400–0x3FFF é paginável. Não confundir a política de manter código nos
  primeiros 32KB com um limite fixo do mapper. `SMS_mapROMBank(n)` altera
  somente o slot 2; os símbolos dos outros slots constam em SMSlib.h.
- Código não-bancado ≤32KB. Dados bancados: `--constseg BANKn` +
  `-Wl-b_BANKn=0x{n}4000`; assets2banks gera os fontes.
- Header SEGA @0x7FF0 ("TMR SEGA" + checksum + região); `makesms` cuida do checksum.

## Gate mental
Antes de adicionar mapper: o orçamento atual foi MEDIDO ou é chute? Mapper sem
medição é feature creep técnico.
