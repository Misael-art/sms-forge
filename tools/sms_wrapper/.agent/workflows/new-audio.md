# workflow: new-audio

1. Música/SFX definidos no GDD; arbitração de canais no TDD (3 tone + noise).
2. Produzir PSG via tracker→PSGlib (ferramenta do artista); sample comprimido só com orçamento.
3. Integração: APIs confirmadas no `PSGlib.h` antes de usar.
   SFX no canal do manifesto; gate `audit_psg_channel_binding.py` (L041).
   Stream sem N cópias do mesmo frame; gate `audit_psg_redundancy.py` (L051).
4. Áudio entra no orçamento worst-frame da cena.
5. Evidência final inclui áudio audível. Silêncio → zumbis + controle
   histórico na mesma rodada (L048); não editar a ROM.
6. Revisão usa música isolada e mix com SFX da ação real, canais restaurados
   depois de pausa/round/tela e trechos alinhados quando comparar referência.
   `audit_psg_quality.py` aplica heurísticas declaradas; composição, balanço,
   clipping e adequação ao público precisam de audição/review independente.
   Preview sintetizado é controle offline, não captura do chip/emulador.
