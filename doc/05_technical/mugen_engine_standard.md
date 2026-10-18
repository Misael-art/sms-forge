# Padrão de engenharia e entrega — MUGEN → Master System

Decisão humana vigente: 2026-09-26. Escopo: motor, consumidor de referência e
rotas de produção. O objetivo é excelência audiovisual e de combate no contexto
do jogo. AAA é uma avaliação de resultado; quantidade de efeitos não a demonstra.
Contrato executável: `tools/sms_wrapper/mugen_engine_contract_v1.json`.
Workflow: `tools/sms_wrapper/.agent/workflows/mugen-engine-quality.md`.

## Referência e fatos

O jogo de referência é **Samgukji III**, também chamado Sangokushi III, de luta
para SMS; não confundir com o jogo de estratégia da Koei. O catálogo identifica
1024 KB/8 Mbit. A escala e todas as técnicas atribuídas ao jogo no briefing são
referências propostas: esta revisão não fez disassembly nem medição da ROM desse
jogo. Elas não viram fatos históricos por repetição.

Fontes técnicas: [manual Sega Mark III](https://www.smspower.org/Development/SMSOfficialDocs),
[observações de hardware de Charles MacDonald](https://www.smspower.org/uploads/Development/msvdp-20021112.txt),
[PSG, investigação de Maxim](https://www.smspower.org/Development/SN76489),
[YM2413 e documentação vinculada](https://www.smspower.org/Development/YM2413),
[identificação do jogo](https://www.smspower.org/Games/SamgukjiIII-SMS).
A API local definitiva continua em `sdk/devkitSMS/SMSlib/SMSlib.h` e
`sdk/devkitSMS/PSGlib/PSGlib.h`. Exemplos e números de Mega Drive não são leis SMS.

## Piso obrigatório de entrega

1. Dois personagens reais consumidos por dados, um palco final autoral, HUD,
   música e SFX, um especial por lutador, comandos legíveis, rounds melhor de
   três, timeout/empate, resultado e revanche. Prova da troca de `.def` com
   hashes do núcleo C iguais antes/depois; personagem com nome diferente não basta.
2. LUTADORES GRANDES E LEGÍVEIS. Medir a altura opaca do corpo idle, sem arma,
   FX, padding transparente ou escala da janela. Alvo 45–55% da altura útil da
   arena declarada. Perfil inicial: canvas 256×192, HUD/reserva superior 32 px,
   área útil 160 px → **72–88 px**, coerente com a faixa aproximada 70–90.
   Usar 192 como denominador daria 87–105 px; não misturar os dois contratos.
   Esta divisão de 32/160 é a proposta inicial do perfil, não fato do jogo de
   referência. A cena pode declarar outra área útil e recalcular a faixa.
3. Escala uniforme por personagem/cena e preservação de proporção, pivots,
   AIR, duração e caixas. Não escolher divisor por tamanho de cada pose. Poses
   agachadas, aéreas e estendidas têm contratos específicos. O preset 1:4/48 px
   continua apenas como controle técnico histórico T10; não é teto do motor.
4. Orçamento simultâneo de corpo+FX+HUD+arena+som: RAM/stack, VRAM residente,
   endereço dos patterns de sprite, SAT e linha, bytes e ciclos de upload,
   latência input→estado→pose, fila e starvation. Medir também o degrau seguinte.
   Um corpo retangular 32×80 pode custar 4×5=20 sprites TALL; dois custam 40
   entradas e 8 por linha quando sobrepostos. É uma estimativa geométrica, não
   aprovação de arte, FX, VRAM ou tempo de upload. Altura não impõe 48 px.
5. Banking expansível com perfil Sega de 16 KiB e capacidade alvo 1 MiB,
   sem preencher ROM vazia para aparentar escala. Provar acesso a dados distintos
   nos bancos-limite, ponteiros, linker e ownership do slot com áudio/ISR.
   Conteúdo inclui metadata de pose, descritores AIR e índices META/METAL:
   não basta colocar somente pattern data em bancos se tabelas excedem o banco
   fixo ou deixam ponteiros inválidos após remapeamento.
   O ROM inicial pode ser menor; a capacidade do motor precisa de fixture própria.
6. Combate com cadência nominal NTSC/PAL no perfil suportado, sem ticks perdidos
   ou pior quadro estourado; vídeo de interação e sonda contínua sem pausas DAP.
   A tolerância de medição do emulador não redefine a velocidade do combate.
7. Arte vinculada ao binário, áudio musical revisado, proveniência e fidelidade
   por recurso, revisão independente e os sete eixos reconciliados na mesma ROM.
   PASS de boot, soma de flags ou sinal RMS não substituem esses aceites.

## Portfólio técnico com correções obrigatórias

“Baseline” é uma obrigação de resultado. “Candidata” é uma rota de investigação
que só entra na cena após comparação A/B e prova de custo/qualidade. O contrato
JSON exige decisão, prova e fallback para todas as técnicas abaixo.

| Técnica do briefing | Decisão e condição de engenharia |
|---|---|
| ROM de 8 Mbit e bank switching | Baseline de capacidade. Banco seleciona ROM já acessível; medir ponteiros/residência/ownership, incluindo metadata AIR/META/METAL e limites de 16 KiB; não atribuir latência de disco ao mapper. Codemasters exige outro backend e fixture, não apenas trocar um nome. |
| Metasprites 8×16 e ordenação dinâmica | Baseline. Recortar transparência, preservar pivot e reservar parte de SAT/linhas para FX. Simular pares de poses, facings, saltos, câmeras e ataques simultâneos antes da arte cara. |
| Flicker inteligente | Somente diagnóstico experimental. Modelar seleção antes da emissão e relatar duty cycle, maior sequência de omissão, prioridade e perigo visível. A entrega vigente exige zero omissões visíveis, <=8 sprites/scanline e <=64/SAT; vídeo com flicker reprova. Compactar/reautorizar a composição ou bloquear a cena; não reduzir 72–88 px nem chamar rotação de SAT de eliminação do limite. |
| CRAM por interrupção de linha | Candidata. Há uma paleta de sprites compartilhada. Trocas por bandas Y não dão duas paletas independentes a lutadores lado a lado na mesma faixa vertical. Validar timing de IRQ, portas VDP, cores, costura e restauração; BG e sprites não ganham bancos de paleta extras. |
| HUD no BG | Baseline. Atualizar células sujas e coalescer escrita; custo real de VRAM/CPU por frame, sem sprites de barra. |
| PSG em VBlank / roubo de canais | Cadência uma vez por frame e ownership são baseline; não é obrigatório ocupar a janela crítica de VRAM com o driver. Prioridade, preempção e restauração ao terminar o SFX devem acompanhar o estado musical corrente; não prometer restauração um frame após começar um SFX longo. |
| H-scroll por bandas / paralaxe | Candidata. SMS tem um plano BG; uma banda de scroll não reproduz dois planos independentes na mesma linha. Medir sweep completo de câmera, bordas, HUD e IRQ. |
| VCounter tweaking | Rejeitada a explicação de “escrever no contador para ganhar CPU”. VCounter é leitura; modo de vídeo e display blanking são controles diferentes. Menos linhas desenhadas podem ampliar janela de transferências, sem criar ciclos por quadro. Modo 192 é base; modos estendidos dependem do VDP. |
| PCM congelado / nibbles / delay assembly | Candidata após PSG. Atenuação PSG não é DAC linear de 4 bits; LUT e comportamento de tom dependem da implementação. Amostras empacotadas exigem custo de desempacotar. Clock, taxa e restauração do PSG/banco/estado de IRQ são contratos; DI não bloqueia NMI. Sem promessa de voz “limpa” nem CPU universal de 100%. |
| Espelho por software | Candidata comparada a espelho offline. LUT pode trocar ROM por RAM/ciclos/upload; economia é nos dados espelhados elegíveis, não necessariamente metade do cartucho. BG possui atributos de flip; sprites SMS não. |
| FX no BG | Candidata com owner, oclusão, restauro de tiles/mapa, câmera e HUD. É troca de recurso; alivia SAT mas consome BG/VRAM/upload. A atribuição específica ao Hadouken de SFII permanece não verificada. |
| Prefetch em RAM | Candidata. Medir acerto/miss e cancelamento sob 8 KiB incluindo stack. Cache reduz trabalho futuro de conversão/upload; ler ROM bancada não é streaming de armazenamento externo. |
| FM com fallback PSG | Expansão opcional. Detecção, waits de portas e arranjos próprios; nove canais melódicos ou configuração com ritmo não equivalem ao PSG. Não executar automaticamente os mesmos comandos VGM nos dois chips. Escritas e sequenciador têm custo. |
| PCM por IRQ de linha | Experimento de alto risco de timing. Interrupções por linha, prólogo, jitter e concorrência custam CPU; não aceitar “baixa CPU” sem número. Fallback PSG ou PCM em estado congelado. |
| Patch FM dinâmico | Candidata: patch custom é compartilhado pelas vozes que o usam; troca modifica todas elas. Medir agendamento, waits e regressão sonora. |
| Arpejo PSG | Candidata de arranjo musical; notas sucessivas simulam acorde e não liberam automaticamente os outros canais para qualquer SFX. Avaliar envelope, tempo e PAL/NTSC. |
| Palette cycling | Candidata de baixo custo, nunca custo zero: escreve CRAM e afeta todos os consumidores do índice. |
| Tiles BG animados / CHROMA-Shift | Candidata; 4 ou 8 tiles é hipótese a medir. Animação de padrões não cria plano extra. Transformação técnica mantém proveniência da arte autoral. |
| Deduplicação de patterns entre atores | Candidata apenas com igualdade byte-a-byte dos pares 8×16 e um índice VDP realmente compartilhado. Medir residency simultânea, remapeamento META/METAL, upload e comportamento visual. No corte atual, um par transparente economiza 64 B; facing fixo encosta nos 8 KiB sem folga, e qualquer facing ainda excede o limite. Fallback: pools independentes e reprovar a combinação que não cabe. |
| Coluna esquerda | Baseline quando H-scroll ativo: `VDPFEATURE_LEFTCOLBLANK` (R0 bit5), contabilizar os 8 px ocultos no viewport. |
| Esticamento por Y-scroll a cada linha | **Rejeitado como descrito no SMS:** scroll vertical é registrado para o frame; a receita não produz Mode 7. Perspectiva desenhada ou animação de tiles permanece investigável. |

Arrays de metadata `META/METAL` podem ser compartilhados entre poses por alias
de compilação somente quando os bytes são idênticos. O gerador conserva o nome
lógico e `_SIZE` de cada pose; o auditor de tamanho e o analisador resolvem o
alias até o array canônico. Silhueta ou máscara semelhante não autoriza
compartilhar índices. Medir o objeto/link do header integral depois da
deduplicação; se ainda exceder o segmento fixo, bankear as tabelas e provar os
endereços após cada troca. Um link aprovado de um elenco-piloto não prova a
capacidade de um elenco maior nem a reprodução AIR.

Para cada transição AIR consecutiva, medir os pares 8×16 novos após reúso
exato, somar os bytes a buscar e dividir pela duração do frame corrente. A
residência current+next que cabe em VRAM não prova que o prefetch termina a
tempo. O corte Ken/Ryu exige 480 B/VBlank para Ken idle 0→1 e 183 B/VBlank para
Ryu P2 idle 0→1; são demandas calculadas, não o throughput aceito do VDP. A
capacidade precisa ser medida na ROM com probe de pior quadro antes de aceitar
cadência.

O relatório pré-arte também deve fornecer um plano de slots reproduzível para
uma sequência cíclica completa: padrão byte-idêntico mantém seu slot, padrão
novo recebe slot livre durante o AIR corrente, e a metadata emitida aponta para
o novo mapa. O plano precisa carregar eixo/pivô, dx/dy, terminador e durações
AIR junto das fontes bank/offset. Este artefato dimensiona a integração e
alimenta o runtime; não substitui prova de VBlank, troca de facing nem captura
de AIR. Não reservar o mapa inteiro como se estivesse disponível para HUD/FX:
declarar quem possui os slots e medir a folga concorrente na cena.

Nenhuma técnica candidata passa por possuir uma função C ou uma tabela. Exige
self-check do instrumento, coreografia comum A/B, recurso certo, ROM, vídeo e
áudio quando pertinentes, e regressão de hitstop/KO/transição/restauração.

## Rotas assimiladas do SGDKForge

- Intake → IR independente → análise de fidelidade → contrato de cena →
  conversão → dados → consumidor. Registrar diferenças sem portar VM 68k ao Z80.
- Fonte intacta + candidato + relatório de perdas; comparação de silhueta,
  máscara, cores e movimentos em 1x. Aprovar uma pose não aprova a família toda.
- Piloto de uma família de FX: preservar todos os elementos AIR, inclusive
  vazios, tempos, loop, offset, eixo, CLSN; reservar paleta para o catálogo todo.
- Stage source-view e sweep completo: mapear dependências e velocidades por
  linha, depois decidir achatamento/bandas/reautoria para UM BG do SMS.
- Ownership explícito de CRAM, BG, bancos e filas; empréstimos restaurados em
  interrupção de golpe, KO, revanche e saída. Recursos não são intercambiáveis.
- Perfil com janela fixa e custo do próprio instrumento aferido; comparar mesma
  coreografia com áudio real. Percentuais do doador não são evidência do SMS.
- Efeitos cosméticos separados da lógica; trace de combate invariável com FX
  ligado/desligado; testes negativos que removem restauração devem reprovar.

## Execução e semântica dos gates

`PYTHONPATH=tools/sms_wrapper python3 -m mugen2sms quality-check --project SMS_projects/luta_mugen`
valida o contrato de planejamento. `--delivery` exige capacidades aceitas e
relatórios `sms_mugen_capability_evidence_v1`, cada um com ID, SHA da ROM,
status e artefatos hash-bound próprios. O auditor não produz esses resultados,
não interpreta vídeo e não substitui os gates de emulador/visual.

O pipeline `mugen_fighting_v1.json` combina esse preflight com os gates existentes.
A CLI oferece somente comandos SMS implementados; rota ausente deve falhar
claramente. O estado atual e a ordem de implementação vivem no projeto consumidor.
