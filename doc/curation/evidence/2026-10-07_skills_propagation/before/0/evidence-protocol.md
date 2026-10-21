# skill: evidence-protocol

## Critério único
"Se não foi visto rodando no emulador, não existe."

## Evidência mínima por entrega
1. Build verde (`out/build_record.json`).
2. Boot no emulador gate (**Emulicious**; openMSX não é SMS — L005) com
   captura INFORMATIVA (`capture_evidence.py` reprova tela branca/vazia).
3. Gameplay real: deslocamento do objeto controlado **na direção da tecla**,
   com canal vivo. Neste host: `emulator_input.py` (kdotool+ydotool).
   Lastros aceitos: `evidence.json.interaction_proven` **ou**
   `input_memory.json` (`input_provado` + `canal_teclado_vivo` + SHA da ROM).
   xdotool/XTEST em Wayland não fecha o eixo (L039).
4. FPS medido (frame counter no código + leitura no emulador).
5. Áudio audível na evidência.
6. Memory bank atualizado com status do vocabulário.

## Teto da captura de boot
Boot + rota de emulador, sem época visual `delivery` e sem mapa
asset→ROM, classifica `runtime_probe_passed_visual_epoch_failed`.
Prova execução. Não prova qualidade, cena final, escala nem AAA.
Gates: `audit_visual_delivery.py`, `audit_rom_asset_binding.py`.

## Estado curto: probe, não screenshot
Estado que dura ~20 frames (agachar, KO, troca de lado) não se prova por
`capture_evidence`: a mesma chamada cai em cenas diferentes (L054). Exponha
a pose/facing no probe e leia a RAM. Screenshot é sorteio.

## Proibições
- Simular/maquetar evidência (crime fundador).
- **Torcer o roteiro da atração/demo para o próprio teste passar** (L053).
  Caminho não observado permanece não observado. Classe causal:
  `evidence_script_tuned_to_pass`.
- Ler ferramenta sem self-check verde (§19).
- Claim acima do teto (§17).
- Promover captura de D1/probe/branding a entrega visual (§39).
