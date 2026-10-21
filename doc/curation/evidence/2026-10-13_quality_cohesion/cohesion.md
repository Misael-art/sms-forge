# Coesão canônica atual — 2026-10-13

## Cobertura

68JSONs diretos de curadoria,113lições emitidas atéL129,113rotas de aplicação e81entradas no ledger. Entradas examinadas são legíveis e hasheadas; learning_capture real passou, sem definiçãoID duplicada. Referências de schemas/skills/workflows dos pipelines resolvem.4selfchecks focados passaram; não foi executada suíte integral ou emulador.

## Defeitos e curadoria deduplicada

1. **Schema de sprites atrasado:** enum8x8/16x16 exclui8x16 e ainda ensina X+32. Reutilizar L003/L006/L128/L129.
2. **Metadata L128 atrasada:** rota ainda declara offsetY aberto, apesar deL129 fechar y−1; SHA de skill não valida conteúdo dos limites. Reutilizar L128/L129.
3. **FPS incompleto:** fps_constant([60,None]) passa por descartar janela ausente; [50,50] também passa, enquanto consumidor registraNTSC. Isso não paga60FPS. Reutilizar L013/L035/L061/L077.
4. **Teto AAA/FPS fraco:** apenas presença de token/scope/approved_by/date permite owner vazio,date:null,semceilinge sem evidência. Token aprovado remove checagem global do projeto, mesmo scopeconcept/boot. Aprovação declarada não é comparação de mercado. Reutilizar L002/L036/L104/L123.
5. **ProducerY antigo:** pack_sms_metasprite ainda usa itemy+1==D0; L129 define logicalY−1. Reutilizar L121/L128/L129.
6. **Custo em skill:** metasprite16x16normal tem4entradasSAT mas2porlinha. Dois atoresladoalado consomem4porlinha, não8como ensinado. Reutilizar L001/L006/L061.

## Correção autorizada neste ramo

Somente audit_sprite_line_sim.py alterado:modo8x8/8x16,tiposstrict,coord0..255,hidden/zoom/sat_terminatedbooleanos,erroestruturadoemmanifestoinválido,semcoerçãofloat/string/bool. Negativo/wrappedY é explicitamente fora do perfil; não foi implementado quirksSMS1zoomsem prova.24casosfocados e70manifestosreaisdiagnósticospassaram;selfcheckPASS. Fixturegen_fixtures scene_ok16x16 e schema precisam de alinhamento pelo coordenador.

## Qualidade comercial e60Hz

Doutrina de evidência distingue título do emulador,stepping/APNGnominal econtador daROM; áudioisolado/proveniência/qualidademusical também são separados. Isso é uma base correta. Ainda é necessário registrar o que o contador daROM representa:VBlank/ISR,update de gameplay,pose apresentada e orçamento worst-frame são grandezas diferentes. fps_constante abrangente50..60não é prova específica60FPSNTSC. Comparação comercial requer critérios/contexto/referência observada; nem nomepipelineAAA nem token autorizado mede esse julgamento.

## Limites

Nenhum gameplay,arte,hardware ouFPS de jogo aprovado nesta rodada. Evidência lexical de rota não prova ensinamento semanticamente correto. Corpus L128/L129 está explicitamente sem emulador/console; offset da biblioteca foi lido, maswrapsilício/runtimeoverflow seguempendentes. EIO doMugen permanece observado emdiscoveryamplo,nãoresolvido.

cohesion.json incluihashes169inputs,coveragepor113IDs,8findingsestados/propostas,referênciaspipeline e limites. focused_cases.json preserva reproduções; sprite_manifest_strict_validation.json guarda24casos+70manifestos/SHA.
