# skill: sms-score-banking

## Para quê
Múltiplos bancos de ROM (>48KB) no Master System via mapper Sega.

## Regras
- ≤48KB linear sem troca de banco (primeiro alvo). Mapper Sega: páginas de
  16KB; slot 0 (0xFFFD), slot 1 (0xFFFE), slot 2 (0xFFFF). Somente o primeiro
  1KiB (0x0000–0x03FF) é fixo na página 0; 0x0400–0x3FFF é paginável.
  `SMS_mapROMBank(n)` controla apenas o slot 2. Consulte `sms-banking-header.md`
  e o header antes de alterar a política dos demais slots.
- Código não-bancado restrito a 32KB (as últimas 16KB são paged-out).
- Dados: `--constseg BANKn` + `-Wl-b_BANKn=0x{n}4000`, montados via assets2banks.
- Header SEGA @0x7FF0; makesms calcula checksum.

## Decisão
Só usar mapper quando o orçamento foi medido (nunca "por precaução").
