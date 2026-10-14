# skill: sms-tile-occupancy

## Conceito
Quantos tiles 8×8 únicos uma cena ocupa na VRAM (sem deduplicação H/V flip, que
não existe no SMS — a dedup é só por valor igual).

## Método
- Contar tiles únicos de todos os assets de BG da cena.
- Alocar 1 slot por tile único; index ≤255 no name table.
- Degradar a cena se estourar (nunca estourar o orçamento).

## Gate
- audit_validate_resources (grid 8×8) + contagem manual no spec de cenas.

## Base da name table (SMS_GLOBAL §121, L130)
- O registrador 2 define a base da PNT; a SMSlib inicializa com 0xFF (bit0=1).
- No SMS1, reg2 com bit0=0 força o bit10 do endereço VRAM da name table a 0:
  as 12 linhas inferiores da tela virtual espelham as 12 primeiras. No
  emulador-alvo SMS2/PC o defeito é invisível — escreve-se aqui e quebra-se
  no console.
- Qualquer escrita custom ao reg2 passa por `audit_tilemap_mirror.py`
  (--source/--rom/--snapshots); exceção deliberada estilo *Ys* JP exige
  `--allow-sms1-mirror "<motivo>"` com o motivo no memory bank.
