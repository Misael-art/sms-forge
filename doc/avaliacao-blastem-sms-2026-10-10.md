# BlastEm no SMSForge — avaliação e integração, 2026-10-10

## Parecer

Vale manter **Emulicious como emulador principal** e usar **BlastEm 1.0.0 como
segunda implementação de diagnóstico**. Há ganhos reais para rastrear mudança
de RAM, investigar envio ao VDP, comparar dumps e gravar transições/sinal PSG.
Esses recursos melhoram a investigação de defeitos; não estabelecem 60 FPS,
qualidade AAA, fidelidade musical ou compatibilidade universal do jogo.

| Recurso | Resultado SMS desta integração | Momento de uso |
|---|---|---|
| Watchpoint de memória CPU | Mudança RAM Z80, listas programadas e contadores observados | Life/FSM/cache/canário alterado indevidamente; exigir mapa e caminho de escrita real |
| Watchpoint VDP | Hook nativo direto não qualificado; `vdpregbreak` é M68K. Implementado breakpoint CPU de OUT com opcode vivo e porta verificados | Localizar envio de dados/endereço ao VDP; complementar com dumps posteriores |
| Debugger programável | Contadores/log/condicionais/continuação executados na ROM | Automatizar hipótese específica e reproduzir o mesmo caso |
| GDB Z2 | Implementado para M68K na fonte 1.0.0; não é stub Z80 | No SGDK/MD conforme sua própria aceitação; no SMS usar debugger nativo |
| APNG/WAVE | Capturados nativamente em sessão privada; bruto preservado e derivado APNG validado | Transição, animação, silêncio/sinal e comparação de trechos |
| VGM | Comandos PSG, waits e estrutura decodificados | Investigar mudança de registradores; não substituir WAVE/fidelidade |
| Visores | Paleta, dois atlas e name table derivados dos dumps implementados; visores nativos Mode4 confirmados na fonte | Separar erro de asset, tile, atributo, flip e paleta; captura automatizada das janelas nativas ainda não qualificada |
| Comparação de snapshots | Diff RAM/VRAM/CRAM/regs/PSG com janelas auditadas e faixas nomeadas da mesma SHA | Identificar mudança entre etapas; delta líquido não é número de escritas ou transferência |
| Manutenção | Consulta oficial, candidato paralelo, hashes e bloqueio de divergência exercitados | Atualizar com regressão explícita, preservando o pin qualificado |

O README 1.0.0 ainda afirma ausência de watchpoints GDB, mas
`gdb_remote.c` implementa Z2/z2 com `m68k_add_watchpoint`. Z3/Z4 não estão
implementados. O teste MD positivo relatado pelo usuário é compatível com o
código; não foi reclassificado como teste Z80/SMS.

## Provas e correções

- Na execução atual do coordenador: **2 eventos RAM e 952 + 952 eventos nos
  dois sites OUT**, com contadores programados concordantes. Campo `pc` do
  contexto pode estar stale; endereço do site é separado. Opcode vivo é
  conferido, divergência bloqueia e regiões bankáveis ficam fora do contrato.
- Subagente nativo: **3 sessões novas**, auditorias de ROM/ferramenta atuais
  aprovadas, cinco imagens inspecionadas e processos encerrados. Instrumentação
  registra RAM **0 → 8 → 0**, dois eventos RAM e **280 + 280 eventos OUT**.
- Controle silencioso: WAVE **2,005 s**, pico **0**, APNG **120 quadros**.
  Controle sonoro: WAVE **4,011 s**, pico **4026**, APNG **240 quadros**.
  VGM registra 11/93 comandos PSG; o controle silencioso tem apenas um sample
  de espera no log, demonstrando que ele omite silêncio final.
- APNG nativo apresenta CRC acTL incorreto após finalizar. Foi confirmado no
  código e nos bytes. O derivado corrige somente quatro bytes do checksum;
  os brutos e os pareceres anteriores foram preservados.
- Revisão independente encontrou e retestou cinco falhas: opcode/mapeamento,
  campos internos impossíveis, formato WAVE sem erro estruturado, WAVE
  truncado e VGM inválido. Os casos negativos agora reprovam.
- Os visores usam os 64 códigos SMS com teste exaustivo de ida/volta. Na
  fixture sem scroll/sprites, os 128 pixels de altura superiores da name table
  decodificada coincidem pixel a pixel com o framebuffer nativo; a linha de
  contador inferior pertence a outro instante de captura.
- Candidato paralelo instalado sem substituir o runtime; alteração sintética
  de um arquivo de licença foi recusada e a restauração voltou a passar.
- Comparador aplicado à sessão nativa: 14 bytes RAM alterados durante o input,
  5 no delta baseline→fim; keys e snapshot de input voltam a zero, contador
  acumulado persiste. Uma alteração/restauração pode ter delta zero. Relatórios
  externos não podem ser hardlinks dos dumps e usam substituição atômica.

Evidência preservada: [pacote](curation/evidence/2026-10-10_blastem_advanced/),
[auditoria runtime](curation/evidence/2026-10-10_blastem_advanced/runtime_audit.json),
[feedback nativo](curation/evidence/2026-10-10_blastem_advanced/native_media/final3-feedback.json),
[revisão final](curation/evidence/2026-10-10_blastem_advanced/native_review/expanded_review_final.json).
O índice de arquivo associa os caminhos originais `/tmp` aos arquivos
preservados sem reescrever os retornos dos subagentes.

## Como o agente escolhe

A arquitetura aponta para a skill `sms-emulator-diagnostics.md`, cuja matriz
seleciona o recurso pelo sintoma. O workflow ensina execução, contratos,
interpretação e limites; SMS_GLOBAL §§108/110 e L114–L120 canonizam as regras.
Um subagente independente aplicou a skill ao caso de lifebar corrompida,
60 FPS e SFX: escolheu Emulicious para a prova do jogo e BlastEm para a causa,
sem converter APNG, pico ou fixture em aprovação do produto.

`session_qa.py` continua sendo o coletor Emulicious. BlastEm tem auditor próprio
de pacote e feedback nativo real; não há intercâmbio fictício de session IDs.
Cópias `.agent` locais dos jogos não foram sobrescritas.

## Limites e próximos ganhos

PAL e throughput real BlastEm continuam sem qualificação. WAVE assíncrono não
tem alinhamento exato com APNG; ainda é necessário comparar referência musical
alinhada. Campos VDP do trap não provam instante do bus nem budget VBlank.
Visores derivados não são capturas do jogo. Não foi exercitado hardware físico.

Próximos ganhos úteis: importar símbolos SDCC com vínculo comprovado ao build; ampliar
sites OUT para bancos/OUTI/OTIR com identidade do mapeamento; qualificar captura
das janelas nativas; alinhar trechos de referência e validar PAL separadamente.
Essas extensões permanecem propostas.

Os documentos de `SMS_projects/luta_mugen` continuam com erro de leitura EIO;
este lote validou infraestrutura e ROMs diagnósticas preservadas, não o jogo.
O fechamento integral e seus limites estão em
`curation/evidence/2026-10-10_blastem_advanced/closure/`.

Primeiro fechamento: **selftest 101/101**, **61 ferramentas com self-check**
e learning capture limpo. O probe opcional de build de projeto não foi rodado.
Doc sync permanece **reprovado** por seis documentos ilegíveis EIO e quatro
referências de autoridade não resolvidas, todos em `luta_mugen`; não apontou
ferramentas fantasmas, IDs duplicados ou gates sem citação. A infraestrutura
diagnóstica e as instruções estão aplicadas; a promoção global fica aberta.

Segundo fechamento, incluindo o comparador: **selftest 102/102**, **62/62
ferramentas com self-check** e learning capture limpo. A revisão independente
retestou a proteção contra hardlinks/symlinks, sobrescrita de entrada, corrida
de gravação e fonte stale. O probe opcional de build de projeto não foi rodado;
doc sync mantém os mesmos dez problemas do Mugen. Registro final:
`curation/evidence/2026-10-10_blastem_advanced/closure_diff/summary.json`.

Fontes primárias: [release oficial](https://www.retrodev.com/blastem/downloads.html),
[recursos oficiais](https://www.retrodev.com/blastem/features.html),
[source fixado](https://www.retrodev.com/repos/blastem/archive/2b2a182f4522.tar.gz).
