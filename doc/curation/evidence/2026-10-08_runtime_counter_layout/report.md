# Curadoria — runtime, contadores e composição final (2026-10-08)

## Aplicado ao agente canônico

- SMS_GLOBAL §§103–104; nova skill sms-runtime-optimization.md; skills budget
  e visual, workflows MUGEN/art-review e mapa ARCHITECTURE atualizados.
- Novo audit_counter_window.py: delta modular, candidatos compatíveis com
  limite declarado e --require-exact. Limite/reset/janela não são autenticados
  por esse gate; não extrai hit rate de contador cumulativo.
- Checklist de concept model sheet exige document_and_layout e rejeita N/A;
  raw íntegra não aprova a folha composta. Texto de medição L108 alinhado com
  os cinco eixos atuais, sem trocar ID/dedup ou reescrever pareceres de arte.
- Selftests válido/inválido e registro/ledger/memória atualizados. Sem fontes,
  assets ou .agent locais de jogos alterados; nenhuma ROM nova executada.

## Evidência e correção de interpretação

O trial dirty-bit registra fast hits155→184. A fonte do clone declara
`draw_fast_hits` como unsigned char. O delta29 é modular8-bit; não há um limite
exato/janela de contador autenticados que excluam múltiplas voltas. A ideia de
“só29 hits úteis” fica não comprovada. No exemplo offline com limite358,29/285
são ambos candidatos. Não publicar29/358 como taxa; oportunidades e endpoints
precisam de instrumento revisado. counter_calibration.json preserva PASS de
consistência e FAIL de contagem exata; source_inventory.json congela a evidência.

FPS históricos: baseline43,15/42,32; dirty-bit37,69/38,36/41,29;
preflight32,46/33,11/36,14. Mantida rejeição dos candidatos diante da observação;
janelas/host/sessões diferentes não sustentam porcentagem de regressão causal
ou causa exclusiva. VCounter scan/emit localiza fase, não duraçãoCPU.

SAT slots fixos têm modelo estático400linhas/40quadros, mas QA declarou
blocked, sem sessão iniciada. Mídia de outra SHA presente no diretório não
aprova essa candidata. Seu runtime permanece not_run.

DrSocial14v3: checksum/cobertura atuais íntegros, checklist pending sem decisão
final do dono. Gate mede registro/status/hashes, não anatomia/composição por
visão computacional. A inclusão de layout não promove a imagem.

## Validação

- selftest95/95; probe de build opcional não executado.
- 55 ferramentas de medição com selfcheckPASS; learning capturePASS.
- Gate global doc_sync FAIL: 10 registros relativos a luta_mugen/doc (EIO/ENOENT).
  Nenhum bypass, recriação de documentos, fsck ou remount realizado.
- Revisão independente final passed_with_limits, em independent_review.json:
  23 casos focados/250enumerações modulares/3negativos de layout. Nenhuma
  execução ou aprovação do produto. Recomendação de resumo em original-artwork
  aplicada, e tabela input AGENTS alinhada à rota privada atual.

## Limites e retomada

Reaplica L013/L037/L061/L082/L089/L097/L106/L108; registry permanece L108.
Não promove cache/slots/60FPS/zero flicker/AAA. Ao restabelecer contexto
legível, preparar QA production nova da SHA alvo, medir incidência com janela
selada/counter suficiente, provar invalidação/render e comparar workload
completo. Recuperação de armazenamento permanece intervenção separada.
