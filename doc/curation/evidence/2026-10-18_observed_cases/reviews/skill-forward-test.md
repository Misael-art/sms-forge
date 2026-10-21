# Aplicação independente da skill de casos observados

Data: 2026-10-18. Escopo: auditoria offline e leitura do repositório; sem build,
emulação, alteração de fontes/fixtures ou promoção. Nenhuma conclusão abaixo
declara uma ROM testada nesta rodada. Não li os reports/calibration existentes
nessa curadoria nem pareceres temporários dos outros revisores.

## Resultado dos três records

Ferramenta aplicada: `audit_observed_cases.py --record ... --report-out ...`.
Seu `--self-check` passou antes de usar as medições. Os relatórios novos estão
neste diretório; `commands.json` preserva argv, exit, stdout e stderr.

| Record | Resultado reproduzido | Claim sustentado | Limite |
|---|---|---|---|
| positive_control | PASS; byte em 0xC02B: 43 no ACK59/frameVDP310, 36 no ACK785/frameVDP646; delta -7 | O journal vinculado registra redução numérica de 7 nesse campo entre esses checkpoints | Interpretar como HP depende do layout histórico; não prova qual golpe, um único impacto, contato visível ou combate completo |
| negative_control | PASS; 43 no ACK59/frameVDP310 e 43 no ACK837/frameVDP663; delta 0 | O journal vinculado registra ausência de mudança líquida nesse campo entre os checkpoints | Não prova que nunca houve dano/restauração no intervalo, nem que o gesto efetivamente foi um whiff/guarda |
| contradictory_whiff | FAIL, exit1 esperado; o valor inicial 43 confere, mas delta real -7 contradiz o esperado 0 | Recusa o assert de ausência de mudança líquida | Usa o mesmo SHA de journal e session do positivo: não é uma terceira execução independente |

Todos apontam à mesma ROM SHA
`76cdbee3f10a58a07199b9012ff6dbe53df372d7532d6a8aa324089824425e73`.
O layout declara explicitamente que interpretar o byte5 do ator como HP vem
do relato histórico, não de autenticação independente do layout C. Assim,
"campo diminuiu 7" é mais estrito que "o soco causou exatamente 7 de dano".

## Combate, latência, visual e custódia

**Combate:** há dois resultados de delta distintos, com controle contraditório
efetivamente detectado. Faltam vínculo com o contrato de golpe/CLSN, estado de
guarda, posições/facing, consumo do gesto, terminal/recovery e imagem alinhada.
Não sustentam golpes especiais, IA completa, zero dano durante guarda ou luta
aprovada. Nenhum resultado foi promovido pela quantidade de checks passados.

**Latência:** positivo e contraditório abrangem 336 framesVDP entre as leituras;
negativo abrange 353. Esses números são intervalos entre endpoints de leitura,
não latência entrada→primeira reação/impacto. Os records não têm `vdp_deadline`
nem ponto com `anchor: input`. Seus journals têm operações `sequence`, não
operação `input` que o perfil atual exige como âncora. A skill avisa que não
extrai o início interno de gestos `sequence`/`video`. Logo, não há aprovação nem
reprovação de um deadline de gameplay declarado; tampouco FPS contínuo.

**Visual/cache:** os records não incluem PNG, vídeo, vínculo temporal com SAT/PNT
ou probes de desejada/residente/submetida. Não provam que a pose causadora do
dano estava visível, que não houve omissão do ator, congelamento, tile residual,
paridade incorreta ou colisão de pose futura. Uma imagem legal antiga pode
permanecer bonita enquanto a simulação ou a publicação do cache está errada.

**Sessão:** os snapshots lidos estão em `state: input_verified`, sem prova de
encerramento neste recorte. O gate de casos confere referências, SHA e coerência
de ACKs, mas declara que não autentica cleanup, origem do journal ou significado
dos probes. Não substituí esse escopo por aprovação de `audit_subagent_session`:
não foi fornecido pedido/report de QA nativa completo a este exercício.

## Imagem estável + FPS médio nominal aprova slice com cache?

**Não.** A imagem estável paga somente o conteúdo observado no frame; FPS médio
regional paga apenas taxa média nas janelas medidas. Ambos podem coexistir com
ator omitido, pose antiga retida, upload atrasado, ISR avançando sem gameplay
completo ou hitbox futura causando dano antes da pose apresentada.

Para decidir o crescimento do slice, pedir evidência da mesma ROM/janela/caso:

1. Contrato production legível com prazo esperado por ator, política do cache
   e distinção entre hitstop intencional e stall de upload.
2. QA nativa isolada com controles positivos/negativos e retorno ao terminal:
   input aceito→desejada→residente→submetida SAT/PNT→framebuffer→consequência.
   Não reconstruir o primário ausente a partir de um resumo de aprovação.
3. Journal/probes e vídeo frame-paced alinhados durante gesto e recuperação,
   cobrindo ambos os atores, mudanças de pose/facing, overlap, cancelamento por
   dano, invalidação e geração abandonada; FX/HUD/IA/áudio conforme coexistem.
4. `audit_observed_cases.py` para RAM/deadline observado compatível;
   `audit_import_semantics.py` para identidade AIR/CLSN no escopo do perfil;
   `audit_render_fidelity.py` e `audit_render_glitch.py` para pixels/imagens
   legais. Esses gates não substituem revisão de timing e contato visível.
5. Execução contínua com `measure_runtime_probe.py`, janelas regionais e carga
   do host registradas, mais `measure_worst_frame.py` e deadline por frame.
   Vídeo por stepping não paga throughput; ISR isolada não paga frame completo.

## Feedback concreto sobre a skill

**Aplicação eficaz:** a skill forneceu comando executável, perfil, exemplo,
escolha de ferramenta por claim e limites que mudam a decisão. Seguindo-a,
obtive dois PASS restritos e uma recusa real sem chamar o acervo de gameplay
aprovado. Seus avisos sobre quatro estados da pose e `sequence` evitaram
inferência incorreta de visual e latência neste pedido.

**Lacunas de usabilidade/cobertura:**

- O relatório atual retorna `actual`/`expected`, mas não expõe valores completos
  dos pontos, frames e seqs que aprovou. Precisei ler os primários e gravar
  `primary_observations.json` para explicar 43→36 e os intervalos. Uma saída de
  pontos rederivados hash-bound tornaria o parecer mais rastreável.
- O perfil reconhece prazo apenas de `input` direto. Os dois journals reais
  usam `sequence`: a limitação está bem declarada, mas o agente não pode medir
  latência desse acervo com o gate atual. Evolução futura precisa preservar o
  começo real do gesto, sem sintetizar ACK nem editar o histórico.
- Aprovação `delta_eq:0` mede variação líquida; não significa ausência absoluta
  de dano entre checkpoints. A frase "sem dano precisa delta zero" pode ser
  lida como suficiente. Seria útil explicitar a diferença entre zero líquido
  e ausência de eventos transitórios, exigindo trace/contador quando necessário.
- O gate não fornece síntese da matriz solicitada (positivos, negativos,
  terminais/estados). A skill manda preservá-la, corretamente; o coordenador
  ainda precisa conferir cobertura de forma explícita, não contar arquivos.
- A skill de casos não aponta diretamente para runtime/product-quality por
  caminho; li esses documentos para a segunda parte do pedido. Um link de
  encaminhamento explícito reduziria o risco de parar no PASS de RAM ao decidir
  qualidade de um slice com cache.

Nenhuma dessas lacunas foi ocultada como funcionalidade implementada ou corrigida
nesta revisão, que é somente leitura.

## Artefatos e reprodução

- `positive_control.report.json`, `negative_control.report.json`,
  `contradictory_whiff.report.json`: saídas novas do gate.
- `commands.json` e `*.command.json`: comandos de medição executados e retornos.
- `primary_observations.json`: endpoints e operações contados dos primários.
- `sources.json`: 18 arquivos lidos/vinculados com SHA e bytes; ROM somente
  hasheada, nunca executada.

Comandos principais, todos a partir de `/mnt/sdcard/Projects/SMSForge`:

```sh
rtk proxy python tools/sms_wrapper/audit_observed_cases.py --self-check
rtk proxy python tools/sms_wrapper/audit_observed_cases.py --record doc/curation/evidence/2026-10-18_observed_cases/positive_control/record.json --report-out /tmp/curation-forward-20261018/positive_control.report.json
rtk proxy python tools/sms_wrapper/audit_observed_cases.py --record doc/curation/evidence/2026-10-18_observed_cases/negative_control/record.json --report-out /tmp/curation-forward-20261018/negative_control.report.json
rtk proxy python tools/sms_wrapper/audit_observed_cases.py --record doc/curation/evidence/2026-10-18_observed_cases/contradictory_whiff/record.json --report-out /tmp/curation-forward-20261018/contradictory_whiff.report.json
```

As leituras adicionais usaram `rtk proxy cat`, `rg --files` e `sed` nos caminhos
indicados em `sources.json`, além de Python somente para extrair seq/frame/byte
e calcular hashes. Saídas exclusivamente em `/tmp/curation-forward-20261018`.
