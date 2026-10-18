# mapper_vblank_copy — probe: a cópia bancada de 1856 B cabe na janela do VBlank?

## PERGUNTA (falsificável, escrita ANTES do código)

Numa ROM de **128 KB com mapper Sega** (dados no bank 2 mapeado em `0x8000` via
`SMS_mapROMBank`), a cópia de um **bloco bancado de 1856 B** para a VRAM
(`0x0000`, tile 0) executada logo após `SMS_waitForVBlank()` **completa dentro
da janela do VBlank** — VRAM dumps do emulador idênticos à fonte no prefixo —
mantendo o loop da ROM a **60 Hz NTSC**, com a troca de banco provada por
leitura?

1856 B = a pior pose do O3 (ax/a102, 29 células × 2 tiles + folga de bloco).
A janela declarada por §9 é ≈4,5 ms NTSC (≈15.960 ciclos Z80).

## PERGUNTA SECUNDÁRIA (contrato de projeto O3, D8)

O cronograma "pose em 3 frames" (1856/3 = **619 B/frame**) é sustentável?
Isto é: o prefixo correto medido é ≥ 619 B?

## MOTIVO

M1 do lote O3 (escopo `doc/artifacts/o3_combat_scope_20261016.json`, decisão
D8): a arte do combate não cabe residente; o desenho depende de upload por
VBlank. §9 manda medir ("estimativa de duração do VBlank não é orçamento
aprovado de transferência") e L047 diz que escrita no display ativo se perde.
O probe paga as duas afirmações na mesma sessão.

## DESENHO

- ROM 128 KB: banks 0–1 = código; bank 2 = bloco padrão (1856 B, byte 0 = 'M');
  bank 3 = prova de troca (byte 0 = 'P'); banks 4–7 = reserva 0x00, mergeadas
  num único `-mbank` (limite de 8 merges, L084).
- Loop: `SMS_waitForVBlank` → lê `SMS_getVCount` (antes) → prova o mapper
  (lê bank 2 e bank 3 com `SMS_mapROMBank`) → `SMS_VRAMmemcpy(0x0000, 0x8000,
  1856)` → lê `SMS_getVCount` (depois) → incrementa contadores.
- Marcador `volatile __at(0xC7D0)` (corredor do laboratório, L009):
  `MVC1` + frames + vcount antes/depois + byte do bank 2 ('M') + byte do
  bank 3 ('P') + banco vivo (2) + contagem de cópias.
- Evidência: sessão BlastEm (warmup 300 + 2 frames) → `ram.bin` do snapshot 000
  (baseline) e do último; `vram.bin` do último comparado byte a byte com a
  fonte lida do próprio ROM (offset `0x8000`); screenshot nativo 256×192 com a
  faixa visível (linhas de BG 8–9 = tiles 0..63) decodificada pixel a pixel
  contra o padrão; fronteira visível = maior prefixo de tiles corretos.

## PREVISÃO REGISTRADA ANTES DE RODAR

1. **Mapper**: o byte lido de `0x8000` após `SMS_mapROMBank(3)` é `'P'` (0x50),
   não `'M'` (0x4D); banco vivo = 2. (Se falhar: mapper/emulador não é o que o
   TDD assume e TODO o plano O3 muda de forma.)
2. **Cópia**: o bloco de 1856 B **NÃO cabe inteiro** na janela. Loop de cópia
   ≈18–24 ciclos/byte contra ≈15.960 ciclos → prefixo correto entre **~650 e
   ~950 B**; o restante perde-se (L047) e o dump mostra a fronteira.
3. **60 Hz**: os contadores de frame da ROM e do debugger avançam 1:1 (frame
   pacing mantido — o loop total gasta bem menos que um frame).
4. **Tela**: a fronteira aparece na linha 8 do BG (tiles corretos até ≈tile
   20–29); além dela, tiles estagnados/zerados; linha 9 idem a partir do
   tile 32.
5. **Contrato O3**: se prefixo ≥ **619 B**, o cronograma D8 (pose em 3 frames)
   está pago com a margem medida; se < 619, o espalhamento cresce para 4+
   frames e/ou entram patches byte-run intra-animação — refutação tem
   consequência declarada, não silêncio.

**Refutado se**: os 1856 B chegarem inteiros (janela ≫ 4,5 ms ou escrita fora
da janela não se perde) — aí o modelo §9/L047 precisa revisão.
**Inconclusivo se**: magic ausente, loop sem frame pacing, ou dump de VRAM
incoerente com o marcador (instrumento duvidoso).

## VEREDITO — 2026-10-16 (BlastEm sms2/NTSC; ROM sha `8d874029…`, 131072 B)

**REFUTADO** — a previsão de perda não se confirmou. Sessão
`blastem-sms-2a717d8399b94c0389252aed046ecc3a` (`state: completed`, cleanup OK);
análise em `analysis.json` da própria sessão. Reprodução: `python3 campaign.py`.

| Previsão | Resultado medido | Status |
|---|---|---|
| 1. Mapper troca | `0x8000` → `'M'` (77) com bank 2, `'P'` (80) com bank 3, banco vivo 2 | **CONFIRMADO** |
| 2. Cópia perde ~50–65% | cópia inteira: `prefix_ok=1856`, `mismatches=0` | **REFUTADO** |
| 3. 60 Hz | `frames_rom_delta=2` == `frames_vdp_delta=2` | **CONFIRMADO** |
| 4. Fronteira na tela | linha BG 8: 32/32; linha BG 9: 26/32 → fronteira exata em 1856 B | **REFUTADO** |
| 5. D8 (≥619 B/frame) | 1856 B/frame íntegros; `design_threshold_619b: true` | **SUSTENTADO** |

Detalhes medidos:

- A cópia de 1856 B leva ~224 linhas de varredura (`vc_before=194` →
  `vc_after=162`, atravessando a janela declarada de §9 ≈4,5 ms) e **mesmo assim
  todos os bytes chegaram**: `vram.bin` == fonte do bank 2 no próprio ROM,
  zero divergências nas 1856 posições.
- **Corroboração independente na tela** (screenshot nativo decodificado pixel a
  pixel com o decode planar oficial): tiles corretos até a fronteira exata de
  **1856 B visíveis** (linha 8: 32 tiles × 32 B; linha 9: 26 tiles). Tiles
  58–63 (bytes ≥1856, nunca copiados) permanecem zerados — a fronteira visível
  reproduz o comprimento da cópia. 8 px divergentes, todos na coluna x=255
  (artefato de borda da captura, excluído no `campaign.py` por medição).
- O contador de cópias avança 1 por frame em ambos os snapshots (294→296):
  cópia + espera cabem no frame, sem degradar o pacing.

**Ressalva declarada (não silenciosa):** o veredito vale para **emuladores**. O
modelo §9/L047 — "escrita na VRAM fora da janela se perde" — não se reproduziu
no BlastEm: ele não bloqueia a escrita durante o display ativo.

**Medida cruzada (Emulicious, mesmo ROM sha `8d874029…`, 2026-10-16):** mesmo
resultado — linha BG 8: 32/32 tiles corretos; linha BG 9: 26/26 até a fronteira
exata de **1856 B** (tiles 58–63 fora do bloco, como esperado). Ferramenta:
`capture_evidence.py` (self-check OK; `emu_cross.json` com chain of custody) +
mesmo decode planar do viewport (`emu_cross_viewport_256x192.png`). Fato de
instrumento: o VRAM inicial do Emulicious **não é zero** (garbage; os tiles
nunca copiados exibem lixo) — o BlastEm inicializa com zero; o hardware real é
indefinido. A fronteira de 58 tiles casa o comprimento da cópia nos dois, então
a comparação com a fonte continua decisiva.

**Aberto (exige decisão humana):** (a) hardware real não medido — as restrições
de acesso do CPU à VRAM durante display ativo no silício não foram testadas
aqui; (b) revisão de L047/§9 via `curation-learning.md` — este probe é o
candidato de lição (fato separado da inferência: L047 nasceu de resíduo visual
de troca de tela, não de uma medição de perda de dado). Enquanto a decisão não
for tomada, o D8 fica **como está** — a folga medida é evidência a favor da
simplificação, não autorização.

**Nota de método (formato de tile):** o SMS Mode 4 grava tile em formato
**planar** — 4 bytes/linha = 4 bitplanes; o byte `p` fornece o bit `p` do
índice de cada pixel, MSB = pixel esquerdo. Não é "2 pixels por byte/nibble".
O decodificador canônico vive em `tools/sms_wrapper/blastem_diagnostics.py`
(`render_views`/`pixel`); o primeiro `decode_visible` do `campaign.py` usava o
modelo errado (0 tiles casando — sintoma, não veredito). O probe também usa a
rampa DAC real do BlastEm (0/87/174/255), não a referência digital 85/170/255.
