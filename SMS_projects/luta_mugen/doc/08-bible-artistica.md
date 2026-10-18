# 08-bible-artistica — luta_mugen

> Direção estética VINCULANTE. Adjetivo de direção precisa de piso numérico (§36).

## Doutrina
Dark Deco adaptado ao SMS: contraste alto, luz como recurso escasso, silhueta
legível a 256×192. Pixel art autoral obrigatória; pixel nascido de código como
personagem/cenário é bloqueado pelo gate de proveniência.

## Coerência do elenco e papel dos pilotos

Ken Masters ADV, derivado de sprites CPS2 arcade, é a referência de modelo,
proporção e acabamento para esta linha visual. O Ryu do piloto atual vem de
sprites de um bootleg de NES: continua válido como amostra técnica de paleta
P1/P2, binding de metadata e cache, mas não define o estilo, a escala visual do
elenco nem a arte final. Antes da produção completa de arte, substituir esse
Ryu por um modelo cuja origem, anatomia, proporções e acabamento sejam coesos
com Ken Masters ADV/CPS2. Manter Ryu apenas nos estudos técnicos enquanto for
necessário; não investir nele como personagem visual definitivo.

## Regras de cor
- Somente códigos 6-bit (contrato canal×85). Sem "gradiente suave" — não existe.
- ≤15 cores úteis por subpaleta (índice 0 = transparente).
- Contraste fg/bg ≥ piso de luma medido (audit_luma_floor.py).

## Model sheet e slice de validação antes da arte completa

Antes da produção completa, cada personagem passa por uma folha de modelo e
um slice técnico curto. A folha precisa mostrar escala de frente/verso,
proporção cabeça/torso/pernas, linha de chão, pivô, espelhamento, zonas de
colisão e as paletas de P1/P2. Para a luta, o corpo opaco em idle ocupa
72–88 px dos 160 px reservados ao combate (45–55%); mede-se a silhueta, sem
contar transparência ou padding do grid. A largura vem da arte e não se força
para igualar os lutadores.

| Gate do slice | Critério antes de liberar a produção completa |
|---|---|
| Silhueta | Idle em 72–88 px; escala uniforme por personagem em todos os frames, sem esticar largura/altura de poses separadamente. |
| Pivô e física | Eixos, offsets, facing espelhado e CLSN acompanham a mesma transformação; teste visual sobre a linha de chão e sem salto de pivô entre frames. |
| Animação | Idle completo e uma ação representativa percorrem todos os frames na ordem e duração AIR autoradas; vídeo do framebuffer, não só captura estática. |
| Paleta | P1/P2 usam pools explícitos e META/METAL do mesmo pool de patterns; contraste aprovado na paleta mestra. |
| Carga SMS | SAT ≤64, no máximo 8 sprites por scanline em cada combinação de poses/facings; flicker só é aceito após medir duty cycle e legibilidade da silhueta. |
| Ritmo | Upload de patterns, SAT, lógica e som cabem no VBlank medido; pior quadro sela 3.000 frames sem derrame e o probe mantém 50–60 FPS conforme região. |
| ROM/RAM | Fontes, bancos e cache medidos no link e no emulador; sem estimar folga a partir do tamanho do asset isolado. |

O primeiro slice técnico de 72–88 px percorreu AIR no clone, mas reprovou
ritmo: 25,2 FPS, 3.000/3.000 frames com derrame; o streaming consumiu 102
linhas e a cópia da SAT mais 16. Trate o resultado como evidência para
reprojetar o reaproveitamento de patterns e a composição dos sprites. Não
reduza a escala, desloque pivôs ou altere a duração AIR para fazer o teste
passar sem registrar uma decisão de direção.

Direção do piloto: Ken Masters ADV/CPS2 define o modelo e o acabamento. O Ryu
do bootleg NES permanece somente como fonte técnica de paleta/runtime e deve
ser substituído por modelo visualmente coerente com Ken/CPS2 antes da arte
completa. A substituição não apaga medições válidas de paleta e cache.
