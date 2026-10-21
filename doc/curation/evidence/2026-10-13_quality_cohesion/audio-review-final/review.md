# Reteste independente de áudio V2

**Resultado:** 25/25 verificações focadas passaram. As três falhas anteriores foram corrigidas ou explicitamente recusadas pelo subconjunto de formato suportado.

- Atualização tone somente por par low/high contíguo: low+WAIT, low+END, low+EOF, high isolado e data depois de volume/noise são recusados, sem criar preview enganoso.
- Substrings comprimidas continuam recusadas antes da escrita de WAV.
- SFX compara primeira atenuação não muda e última escrita em ordem temporal estável. Foram exercitados multicanal, ordem externa trocada, empate temporal, mute final e silêncio.
- Oito modos de ruído conferidos no predicado e preview nominal; A4 usa período254 e fundamental aproximada440Hz.
- Corpus real36 streams: hashes preservados,11 reprovam a política M4 corrigida. Isso não declara qualidade musical ruim nem autoriza regeneração automática.

## Limites

Este transporte aceita um subconjunto declarado de PSGlib. Escritas low-only/high-only podem ser legítimas no driver/chip e são recusadas por falta de modelagem neste gate, não porque o hardware as proíbe. A heurística SFX global não prova fade por canal, mix, silêncio final completo ou ausência de clique. Preview LFSR nominal não valida ciclos, fase compartilhada, filtros ou emulação da ROM. Não executei emulador, full suite, mutação de assets ou documentos.

As fontes, casos e hashes estão em `result.json`; a revisão anterior permanece como evidência histórica.
