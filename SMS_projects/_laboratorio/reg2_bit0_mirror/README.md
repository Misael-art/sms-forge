# reg2_bit0_mirror — probe: reg2 com bit0=0 espelha a tilemap no VDP SMS1?

## Pergunta (falsificável, escrita antes do código)

**Com reg2 = `0xFE` (bit0=0, base $3800 mantida) em modo 192 e scroll Y 0,
o BlastEm no modelo `sms1` renderiza as linhas visíveis 16..23 da tela com o
conteúdo das linhas 0..7 da name table (bit10 do endereço VRAM da consulta
forçado a 0), e o MESMO binário no modelo `sms2` NÃO espelha (linhas 16..23
mostram seu próprio conteúdo)?**

Se NÃO em nenhum dos dois modelos, a lei Tier-1 do corpus
(`TilemapMirroring.txt`, L130/§121) **não se reproduz nos emuladores-alvo
deste host** — o gate `audit_tilemap_mirror.py` continua decidindo estática
sobre comportamento que nenhum silício em siílico medimos, e a matriz de
compatibilidade SMS1 (item A5 do dossiê, não aplicado) continua sem lastro.

## Motivo

L130 entrou como `documentado_com_gate; sem medição em emulador ou console`.
A consequência doutrinária central — "o defeito é invisível no emulador-alvo
SMS2/PC" — é exatamente uma afirmação sobre modelos de VDP distintos, e o
`blastem_sms.py` deste wrapper aceita `model: sms1|sms2`. Uma ROM, dois
modelos, um diff de screenshot: é a medição barata que fecha a promessa.

## Desenho

Tilemap com três bandas visuais distintas: linhas 0..7 = tile "topo aceso"
(sólido claro), linhas 8..15 = "base acesa" (sólido escuro), linhas 16..23 =
"colunas alternadas", 24..27 = apagado. A ROM escreve reg2 direto na porta
`0xBF` (a técnica proibida pela lei, proposital — o probe é a proibição em
ato), uma única vez no primeiro clique no botão 1; sessões sem clique servem
de controle (reg2 fica no padrão `0xFF` da SMSlib). Marcador
`volatile __at(0xC7D0)` magic `SIM1` + valor vivo de reg2 + contagem de
cliques. Sessões BlastEm controladas pelo roteiro (clique vs. sem clique ×
modelo sms1 vs. sms2), screenshots 256×192 nativos + `vdp_regs.bin` por
fronteira.

## Previsão registrada ANTES de rodar

- **Confirmado** (lei reproduzida no emulador): byte[2] de `vdp_regs.bin`
  == `0xFE` nos dois modelos; no modelo `sms1` a banda de pixels y=128..191
  é idêntica pixel a pixel à banda y=0..63; no modelo `sms2` a banda
  y=128..191 decodifica "colunas" e difere de y=0..63.
- **Refutado**: sms1 espelha SEM bit0=0 (sessão de controle do mesmo
  binário, reg2=0xFF, também espelha — a lei diria o contrário) ou sms2
  espelha com bit0=0 (a lei diria o contrário).
- **Inconclusivo (cenário C, provável)**: nenhum modelo espelha → BlastEm
  não modela o quirk SMS1; a lei permanece Tier-1 do corpus sem
  reprodução em silício neste host; §121 mantém o status `documentado`;
  NENHUM upgrade de matriz de maestria/compatibilidade é reivindicado.

## Leitura mecânica

`campaign.py` (neste diretório) roda as sessões, verifica `vdp_regs`,
compara as bandas pixel a pixel e imprime o veredito + JSON em
`out/campaign_tier1_2026-10-14/reg2_bit0_mirror/verdict.json`. A ROM é o
caso real que `audit_tilemap_mirror.py --source` deve reprovar (escrita
literal par ao reg2) e aprovar só com `--allow-sms1-mirror "<motivo>"` —
o campaign roda os dois modos e grava a saída como evidência do gate em
código vivo.
