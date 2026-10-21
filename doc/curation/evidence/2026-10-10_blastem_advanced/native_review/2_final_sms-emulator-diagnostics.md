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
nativo separado do coletor Emulicious. PAL, áudio e FPS BlastEm não estão
qualificados nesta rota. Compatibilidade SMS não herda a aceitação MD do SGDK.

Compare a mesma SHA e precondições da ROM, com input P1/P2 validado pelo consumo
real. Frames VDP, contador de lógica, PC e apresentações SDL são grandezas
diferentes; snapshot pode interromper a atualização de vários contadores.
CRAM interna do BlastEm não é código SMS de 6 bits. Não transferir DMA,
68000/GDB, dimensões 320×224 ou controles MD para contratos SMS.

Todo teste fecha apenas seus processos e registra identidade, cobertura,
falhas e limites. Divergência exige investigação; concordância não prova
hardware físico nem autoriza qualidade gráfica ou gameplay não observado.
