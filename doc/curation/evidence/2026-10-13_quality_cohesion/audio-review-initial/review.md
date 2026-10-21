# Revisão independente de áudio — 2026-10-13

Análise própria formulada antes de ler o resultado do worker; fontes locais PSGlib e BlastEm inspecionadas. Sem emulador, full suite, regeneração de assets ou mutação de documentos/repositório.

## Correções confirmadas

- Divisor nominal de tone **32 × período**, incluindo A4 período254; preview FFT perto de440Hz.
- Oito modos: bit2 distingue branco4–7 de periódico0–3; lowbits3 acompanha períodoch2 nominal.
- Autotestes das duas ferramentas passam; substrings comprimidas reprovam antes de criar WAV.
- 36 streams reais reauditados em leitura; hashes preservados conferem;11 agora reprovam M4, concordando com o relatório do worker. Isso é mudança da política corretamente aplicada, não prova de música ruim.

## Três lacunas adversariais

1. `render_wav([0x80,0x38,0])` consome WAIT como highdata. Decoder relata1frame; preview produz0,000125s em8000Hz, em vez0,02s. O driver/chip permite atualização do nibblebaixo seguida deWAIT; preview precisa preservar estado de latch ou recusar gramática que não modela.
2. `decode([0x90,0x42,0x38,0])` cria evento de frequência32 depois de latchvolume. PSGlib descreve non-latch como dados tone; BlastEm fixado ignora dado sob latchvolume. Entrada deve ser recusada ou tratada conforme modelo declarado, nunca inventar frequência.
3. `analyze_sfx([(0,v,ch2,1),(1,v,ch0,14)],2)` inverte início/fim porque agrupa por canal, reprovando decaimento1→14 como14→1. Usar ordem temporal e declarar política por canal ou geral.

## Limites

Preview não reproduz fases de bus, filtros analógicos, compartilhamento de contadorch2/noise, amplitude absoluta ou duração exata por relógio. A normalização por pico modifica nível relativo entre arquivos. M4 conta comandos mesmo no mudo; ruído periódico pode ser escolha legítima de composição. PASS é apenas política de eventos.

Comentários antigos do repertório ainda dizem A3≈220Hz como menorfrequência, incompatível com a nova fórmula(~109Hz no período1023). Piso16 é decisão de composição, não limite físico do chip.

27 de30 verificações focadas passam;3 adversariais reproduzem limitações. Evidências e fontes SHA-bound em `result.json`, fixtures temporárias e logs neste diretório.
