# workflow: release-rom

Pré-condição: os 7 eixos TRUE simultâneos (schema status_axes_v1).
Aplicar `product-quality-checkpoint.md`: declarar público/critério, contexto
completo da cena e evidência conjunta de controles, visual, áudio e fluidez.
Campo `constante_50_60` histórico ou título do emulador não sustenta sozinho
o alvo regional. Probe privado classifica NTSC60/PAL50 com tolerância explícita;
worst-frame/pacing e resposta do jogo são provas adicionais.

0. **Build em modo estrito** — prova as ferramentas antes de confiar na leitura delas:
   ```sh
   SMS_STRICT=1 ./build.sh
   ```
   Roda `validate_measurement_tools.py` (§19) + `audit_doc_sync.py` antes de compilar.
   Não roda a cada build por custo (~3s); **na entrega é obrigatório**.
1. `audit_claims.py` verde (teto de "release" aprovado por humano) **e**
   quarentena de placeholder vazia:
   ```sh
   python3 tools/sms_wrapper/audit_placeholder_quarantine.py --project . --check-release
   ```
   Placeholder é legítimo durante o desenvolvimento e **proibido** na entrega.
   Liberar exige `"release_approved": true` + `"approved_by"` no manifest —
   campo estruturado, nunca prosa (nota como "arte final pendente" não aprova).
2. **Evidência recapturada DEPOIS desta ROM** (§26). Relinkou, os eixos de
   runtime caíram — recapture e sele o bundle:
   ```sh
   python3 tools/sms_wrapper/seal_fresh_evidence_bundle.py \
       --rom out/rom/<nome>.sms --artifact <cada captura> -o out/evidence/bundle.json
   python3 tools/sms_wrapper/screenshot_semantic_gate.py <shot.png> --claim <eixo>
   python3 tools/sms_wrapper/reconcile_claims.py --project .
   ```
2b. **Vídeo do eixo que ACONTECE** (§45/L056). Screenshot não sustenta transição,
   animação nem game feel — um PNG não tem eixo do tempo (§36). Grave do
   framebuffer de sessão privada própria (§§93–99). Leia
   `emulator-isolated-session.md` e `subagent-emulator-qa.md`; prepare pedido
   production V2 com contexto legível, roteiro em frames e reviewer nativo.
   Para transição/golpe, um caso video captura durante a sequence, com cauda
   neutra explícita. Para trecho sem gesto simultâneo na sessão própria:
   ```sh
   rtk proxy python3 tools/sms_wrapper/capture_video.py \
       --session ID --ticks 120 --out video_release
   ```
   O `.mp4` e os frames-chave entram no `seal_fresh_evidence_bundle.py` do passo
   2 como qualquer outro artefato. Stepping não prova FPS real nem inclui
   áudio; medir execução contínua/probe e capturar sinal privado separadamente
   com `capture_audio.py --session ID`. Revisão musical usa trechos alinhados.
   Publicar/check-bundle e fechar somente por ID próprio, também na falha.
   Não encerrar instâncias alheias nem usar fallback ao desktop.
3. ROM versionada em `changelog/roms/build_vNNN/rom.sms`.
4. Teste em ≥2 emuladores (gate + secundário) e, quando possível, hardware real.
5. NTSC e PAL testados (timing normalizado provado).
6. Memory bank fecha o ciclo com links para evidências.

**Armadilha conhecida:** entregar com captura anterior à ROM final. Aconteceu no
laboratorio_01 (F6): as provas eram 6h mais velhas que o binário entregue.
Hoje `build_inner.py` rebaixa o eixo sozinho — não tente reescrever o registro
à mão para contornar.

## Projetar eixos e preservar fontes (L138; custódia L125/L133)

Para OpenBOR, `axis_projection.py --current-rom ROM --bundle BUNDLE
--consumption CONSUMPTION --runtime-metrics METRICS --qa-runtime RUNTIME
--qa-visual VISUAL --wav WAV --out-dir DIRETORIO_NOVO` revalida o bundle,
confere seu vínculo com o consumo e os hashes de métricas/WAV selados. Valida
cada QA contra pedido, contexto, cobertura, ROM, sessão fechada e bundle;
workers/sessões runtime e visual são distintos. IDs de casos vêm do relatório,
sem lista fixa. A autoridade nativa do reviewer ainda exige recibo conferido
pelo coordenador; JSON íntegro não autentica o agente que o escreveu.

Destino existente (inclusive symlink/hardlink) é recusado: criar saída nova
por lote. Para ativar caminhos legados do build, preservar a projeção anterior,
registrar a substituição deliberada e só então instalar a nova projeção
verificada. Não apagar fontes para fazer o gerador passar. Defaults M8 são
históricos e não autorizam herança no SHA atual. Projeção não mede novamente
FPS/áudio/gameplay e não apaga os achados visuais das fontes.

## Continuidade e restauração

Backup/snapshot e clone reproduzível sustentam continuidade, sem fechar
delivery. Conferir fonte, recursos bancados inclusive binários ignorados,
submódulos, permissões executáveis e toolchain; build a partir de clone limpo,
com log e SHA da ROM. Dependências em release devem ter nome, tamanho e hash
verificados. O caso de continuidade de 21/10 perdeu um banco O3 ignorado e
bits executáveis antes da correção: consultar `doc/continuity/20261021-reconciliation.md`.
Assets disponíveis no GitHub não provam restauração completa em outro host.
Depois da restauração, nova QA privada no ambiente atual; evidência antiga
é histórica. Projetos aposentados em `doc/retired-projects.md` não retornam ao
índice por um snapshot abrangente; conferir o índice, não somente `.gitignore`.

Ao restaurar evidência histórica, conferir também permissões: os bundles
O3 locais de M8/cap5 foram encontrados em 0777 nesta curadoria e o consumidor
recusou `immutable snapshot required`. Não desabilitar esse teste nem alterar
o original selado. Criar cópia separada em filesystem com semântica POSIX,
preservar bytes/tempos, restaurar somente nessa cópia o modo somente leitura
e revalidar integralmente hashes, sessões e cleanup. Declarar restauração de
acervo, sem nova medição e sem ativar projeções diagnósticas no build.
