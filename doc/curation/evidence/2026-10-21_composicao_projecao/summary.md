# Curadoria — composição, projeção e continuidade (21/10/2026)

## Escopo

Aplicação de lições existentes, sem IDs novos: L137 (composição de ambos os
atores), L138 (projeção no SHA atual), L125/L133 (custódia), L013/L036/L091/L097
(limites de runtime, apresentação e QA). Registry permanece em L138, com 122
lições emitidas e rotas verificadas. Motores e evidência primária intactos.

## Mudanças

- Skills e workflows agora explicitam composição bilateral, contato visível
  na direção correta e terminais separados de controle e apresentação.
- Pisos de células do O3 não são leis gerais para MUGEN/SMS.
- Projeção revalida bundle e consumo, hashes de métricas/WAV e QA contra
  pedido/contexto/cobertura/ROM/sessão/cleanup. Casos são derivados da cobertura.
- Outputs existentes, symlinks e hardlinks são recusados; fontes preservadas.
- Selftest passa a exercer projeção e silhueta.
- Continuidade considera bancos ignorados, executáveis e permissões de
  snapshots. HAMOOPIG sai novamente do índice (108 arquivos), preservando
  a cópia original e a história técnica.

## Validação

| Verificação | Resultado |
|---|---|
| Selftest integral | 124/124; probe opcional de build não executado |
| Ferramentas de medição | 73/73 self-checks |
| Captura de lições/rotas | PASS |
| Sincronia documental na worktree de publicação | PASS |
| Workspace original | FAIL: dez falhas pré-existentes em luta_mugen |
| Projeção focada após revisão | PASS; 13 casos negativos, positivo e preservação de outputs/aliases |
| Fontes M8 aplicadas ao cap5 | Recusadas sem criar saída |
| Revalidação M8 e cap5 | PASS em cópias verificadas, sem executar emulador |

A calibração inicial recusou os snapshots originais em modo 0777: o consumidor
exige imutabilidade. Em cópias copy2 separadas em filesystem POSIX, o modo de
escrita foi removido e os bundles, métricas e QA foram integralmente
revalidados; todos os hashes de conteúdo permaneceram iguais. As permissões
dos originais não foram alteradas. Ver `calibration.json` (recusa inicial) e
`calibration-restored.json` (método e aceitação das cópias). Os subdiretórios
`m8` e `cap5` são projeções diagnósticas; nenhuma foi ativada no build do jogo.

## Limites e próxima aplicação

Sem nova execução de ROM, áudio ou hardware; nenhuma promoção de técnica,
jogo, entrega visual ou AAA. Os testes offline da projeção usam seams
explicitamente simulados para consumidor/selo; a calibração real não usa mocks.
O gate QA verifica integridade e cobertura, sem autenticar identidade nativa
do reviewer ou qualidade artística. O coordenador ainda confere recibos e
inspeciona os achados.

No OpenBOR, os casos restritos aprovados não resolvem o contato visível do
golpe; direção, terminal apresentado, PAL e oráculo full-frame continuam no
backlog do motor. No MUGEN, nenhuma política de corte/escala foi aprovada por
esta curadoria. Ao retomar, usar a fonte central das skills e os casos reais
do GDD; não propagar os pisos O3 como solução genérica.

A publicação usa branch codex/curadoria-20261021 sobre feat/luta-mugen-motor.
O PR anterior para master permanece separado. As 25 exclusões locais legadas
não integram o lote. Logs em `validation/`.
