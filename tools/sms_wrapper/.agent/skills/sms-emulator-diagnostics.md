---
name: sms-emulator-diagnostics
description: Escolher e executar diagnósticos Master System em Emulicious privado ou BlastEm SMS privado, comparar estado Z80/VDP/mapper e distinguir relógios e representações. Use quando investigar divergência de emulador ou regressão de hardware; não aprova FPS, áudio ou entrega a partir de stepping.
---

# Diagnósticos SMS com duas implementações

Emulicious é a rota principal de produção/QA: input, vídeo, áudio privado,
probe da ROM, FPS e worst-frame. Leia os workflows centrais
`emulator-isolated-session.md` e `subagent-emulator-qa.md` antes de testar.

Use BlastEm para obter segunda observação de uma hipótese específica sobre
Z80, mapper, RAM/VRAM, registradores VDP ou estado PSG. Siga
`../workflows/blastem-sms-diagnostics.md`: instalação oficial fixada, execução
privada limitada via `blastem_sms.py`, auditor `audit_blastem_sms.py` e feedback
nativo separado do coletor Emulicious. PAL, áudio final e FPS BlastEm não estão
qualificados nesta rota. APNG/WAVE/VGM nativos são capturas diagnósticas medidas.
Compatibilidade SMS não herda a aceitação MD do SGDK.

Compare a mesma SHA e precondições da ROM, com input P1/P2 validado pelo consumo
real. Frames VDP, contador de lógica, PC e apresentações SDL são grandezas
diferentes; snapshot pode interromper a atualização de vários contadores.
CRAM interna do BlastEm não é código SMS de 6 bits. Não transferir DMA,
68000/GDB, dimensões 320×224 ou controles MD para contratos SMS.

Todo teste fecha apenas seus processos e registra identidade, cobertura,
falhas e limites. Divergência exige investigação; concordância não prova
hardware físico nem autoriza qualidade gráfica ou gameplay não observado.

## Escolher pelo sintoma

- Byte de life/FSM/cache alterado: watchpoint nativo de mudança RAM,
  `diagnostics.cpu_watches`; testar o caminho de escrita efetivamente usado.
- Upload/endereço VDP errado: breakpoint CPU no `OUT` verificado da SHA atual,
  `vdp_io_breakpoints`. É trap antes da instrução; não é hook VDP de hardware.
- Tile, flip, mapa ou paleta incorretos: dumps e visores SMS derivados;
  comparar também o framebuffer. Name table sem scroll não é gameplay.
- Mudança entre fronteiras: `blastem_dump_diff.py`, opcionalmente com faixas
  nomeadas da mesma SHA. Delta zero pode ocultar escrita seguida de restauração;
  blocos de VRAM modificados não são tiles gráficos únicos nem custo de upload.
- Transição/flicker/som ausente: APNG/WAVE/VGM durante o gesto, conferindo
  cobertura, duração, conteúdo e limites; para entrega usar gates Emulicious.
- Instalação ou release nova: `blastem_maintenance.py releases/status`,
  candidato paralelo com hashes explícitos; sem promoção automática.

Leia a seção avançada do workflow para schema, exemplos e limites. GDB Z2 de
escrita existe no stub **M68K** 1.0.0 apesar do README antigo; isso não cria
stub GDB Z80. `vdpregbreak` também é Genesis/M68K. Não oferecer esses caminhos
ao SMS. `observed_pc` pode estar stale no trap; endereço do site é separado.
APNG bruto tem defeito conhecido de CRC acTL; preservar bruto e usar derivado
que corrige somente o checksum identificado. WAVE é assíncrono, VGM pode
omitir silêncio final; nem duração nominal nem sinal provam 60fps/música certa.
