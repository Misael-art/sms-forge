# skill: evidence-protocol

## Critério único
"Se não foi visto rodando no emulador, não existe."

## Evidência mínima por entrega
1. Build verde (`out/build_record.json`).
2. Boot no emulador gate (**Emulicious**; openMSX não é SMS — L005) com
   captura INFORMATIVA (`capture_evidence.py` reprova tela branca/vazia).
   Para investigação cruzada Z80/VDP/mapper, BlastEm SMS é complementar (§108):
   leia `blastem-sms-diagnostics.md`. Ele possui sessão/auditor próprios e não
   transfere sua aquisição por stepping para os eixos FPS/áudio/entrega.
3. Gameplay real: objeto controlado identificado, consequência na direção do
   input e estado do defensor quando houver golpe. QA usa sessão privada
   `emulator_input.py --session ID --script roteiro.json` (§93). ACK da ponte
   não prova consumo pela ROM; probe/trilha e framebuffer sustentam o caso.
   Referências históricas `input_memory.json` conservam seu alcance e SHA;
   não transferir o resultado para outra build ou outro canal.
4. FPS medido com contador da ROM em execução contínua, usando
   `measure_runtime_probe.py --session ID` e probe SMRT real. Título 60fps ou
   vídeo por stepping não pagam throughput. Registre carga/reserva do host.
5. Áudio capturado no sink privado da sessão. Sinal do PID é presença;
   fidelidade musical exige ouvir/comparar referência em trechos alinhados.
6. Memory bank atualizado com status do vocabulário.

Os sete eixos incluem também validation_report. Delivery exige época visual
e vínculo asset→ROM; cada claim usa evidência fresca da mesma SHA/sessão.
Veja `emulator-isolated-session.md` e `subagent-emulator-qa.md` centrais atuais:
contexto production legível, snapshots e reviewer nativo (§§94–99).
Falta de isolamento aborta; não há fallback automático ao desktop. A rota
histórica kdotool+ydotool é supersedida para QA automatizada; não disputa foco
nem encerra instâncias alheias. Feche somente sua sessão por ID.

## Teto da captura de boot
Boot + rota de emulador, sem época visual `delivery` e sem mapa
asset→ROM, classifica `runtime_probe_passed_visual_epoch_failed`.
Prova execução. Não prova qualidade, cena final, escala nem AAA.
Gates: `audit_visual_delivery.py`, `audit_rom_asset_binding.py`.

## Estado curto: probe, não screenshot
Estado curto (agachar, KO, troca de lado) exige timeline, baseline e probe/trilha
da ROM. Screenshot isolada não mede duração/ordem. Leituras DAP pausadas podem
perder elementos curtos (L054/L097); dumps posteriores de gravador ROM ou
coleta em frames VDP pagos permitem associar estado ao quadro. Rollover e
identidade dos elementos AIR seguem §§97/100, não igualdade dos pixels.

## Proibições
- Simular/maquetar evidência (crime fundador).
- **Torcer o roteiro da atração/demo para o próprio teste passar** (L053).
  Caminho não observado permanece não observado. Classe causal:
  `evidence_script_tuned_to_pass`.
- Ler ferramenta sem self-check verde (§19).
- Claim acima do teto (§17).
- Promover captura de D1/probe/branding a entrega visual (§39).
