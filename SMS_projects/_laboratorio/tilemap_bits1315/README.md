# tilemap_bits1315 — probe: o VDP preserva bits 13–15 e ignora na renderização?

## Pergunta (falsificável, escrita antes do código)

**Uma entrada de name table escrita pelo caminho normal da SMSlib com bits
13, 14 ou 15 armados (`índice | 0x2000/0x4000/0x8000`) (a) fica na VRAM com a
palavra de 16 bits íntegra — inclusive os bits 13–15, legíveis no dump
`vram.bin` do BlastEm — e (b) renderiza pixel a pixel idêntica à mesma entrada
sem flags, provando que o VDP ignora esses bits na consulta da tilemap?**

Se (a) NÃO, "some games use these bits as flags" (SMSPower `Tilemap.txt`,
selo Tier-1 em §6, L132/§123) implicaria tabela sombra fora da VRAM, e o
gancho de engine de §123 estaria desenhado sobre areia. Se (b) NÃO, algum bit
13–15 tem semântica de renderização que o corpus não documenta e §123
mentiria por omissão.

## Motivo

L132 entrou com `measurement_limits` declarando a preservação de bits pelo
VDP como não medida (LOTE F). O gate `audit_tilemap_bounds.py` (segundo eixo)
só decide literais estáticos; a pergunta de hardware é de escrita+leitura, e
o `blastem_sms.py` entrega os dois artefatos de uma sessão: `vram.bin`
(16384 B) por fronteira e o screenshot nativo 256×192.

## Desenho

Fundo apagado (tile 0 carregado e PNT zerada — VRAM não é limpa pela SMSlib,
lição pnt_16bit). Seis células na linha de tile 8, colunas 4..14 de 2 em 2:
`60`, `60|FL_13`, `60|FL_14`, `60|FL_15`, `60|FL_13|FL_14|FL_15`, `60`
(controle). Tile 60 assimétrico em X e Y para tornar visível qualquer
reinterpretação de bit (flip/prioridade/escala). Marcador `SI81`. Uma sessão
`sms2`, steps curtos; leitura offline das palavras em
`0x3800 + (8*32+col)*2` no `vram.bin` da última fronteira + corte das seis
células do screenshot e comparação pixel a pixel com a célula controle.

## Previsão registrada ANTES de rodar

- **Confirmado**: palavras da PNT no dump = `0x003C`, `0x203C`, `0x403C`,
  `0x803C`, `0xE03C`, `0x003C` (preservação byte-exata do que foi escrito)
  E as seis células do screenshot idênticas entre si (bits ignorados na
  render).
- **Refutado (preservação)**: dump mostra `0x003C` onde foi escrito bit
  armado → VDP/emulador mascara na escrita; §123 precisa de errata
  ("flags de jogo exigem tabela sombra") e isso é lição nova.
- **Refutado (render)**: célula com flag renderiza diferente do controle →
  algum bit tem semântica não documentada; §6/§123 precisam de errata.
- **Inconclusivo**: screenshot monocromático/congelado, dump com tamanho
  divergente, ou células indistinguíveis por causa de paleta/posição (erro
  de construção do probe, não do hardware).

## Leitura mecânica

`campaign.py` (neste diretório) roda a sessão, decodifica as seis palavras,
recorta as seis células, diffa contra o controle e imprime veredito + JSON em
`out/campaign_tier1_2026-10-14/tilemap_bits1315/verdict.json`. A ROM é o caso
real para `audit_tilemap_bounds.py`: o valor das células flagged é expressão
(`60 | FL_13`) e o gate a reportará como **não provado** — comportamento
declarado, registrado honestamente no veredito; o caminho de exceção é
demonstrado com `--allow-tilemap-flags "laboratorio: probe L132 bits 13-15"`.
