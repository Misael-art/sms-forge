# Curadoria de instrumentos — proposta mínima

Data: 2026-10-18. Inspeção somente leitura. Nenhum teste, build, emulador ou edição de repositório executado. Este arquivo é proposta de contrato e fixtures, não resultado de uma ferramenta nova.

## Escolha recomendada

Implementar o perfil estreito `journal_ram_v1` em `tools/sms_wrapper/audit_observed_cases.py`, conforme a direção do coordenador. O ganho imediato deve ser **rederivar asserts de RAM e intervalos VDP a partir dos ACKs primários de um journal preservado**, em vez de aceitar o resumo agregado que o mesmo coletor escreveu. Não tentar aprovar sincronismo visual completo no primeiro instrumento.

Não há ferramenta atual que faça essa rederivação geral. Não criar outro gate para duplicar snapshots, hashes, cleanup ou associação de subagente. Uma alternativa tecnicamente possível seria novo `kind` em `audit_import_semantics.py`, mas o escopo de observação primária também atende engines próprias/OpenBOR e não depende de semântica importada. O arquivo separado tem uma responsabilidade clara se mantiver esse limite.

## O que já existe e deve continuar com seu owner

| Instrumento existente | Já mede | Não mede / lacuna relevante |
|---|---|---|
| `audit_import_semantics.py` | AIR finito N+1 com identidade, coordenadas restritas, revisões/expiração de cache, refs hasheadas | Recebe trace/exports declarados; não rederiva de journal, não autentica imagem apresentada |
| `audit_subagent_session.py` | Pedido/worker/contexto/cobertura, bundle, ROM/sessão, hashes, precondição, ACKs com sessão, cleanup; classifica vídeos stepped sem FPS | Não calcula os asserts de gameplay do report nem prova a semântica dos offsets de RAM |
| `audit_counter_window.py` | Delta modular e unicidade sob limite declarado, incluindo wraps | Não autentica limite, reset ou unidade; usar sua API se algum contador modular entrar no novo perfil |
| `audit_meaningful_change.py` | Cruzamento textual entre eixo declarado e eixos false do build_record | Não mede causa dominante, magnitude de ganho nem timeline; não usá-lo para aprovar prazo/renderer |
| `audit_render_glitch.py` | Máscara de framebuffer contra conjunto legal, resíduo/omissão, cobertura em modo flicker, hashes ROM/vídeo | Melhor imagem legal é escolhida por frame; pose antiga legal pode passar mesmo quando a pose lógica esperada já mudou. Não mede input→hit nem identidade temporal correta |
| `session_bridge/isolated.py` | ACK com sessão/PID/seq/frame, journal de operações, publicação imutável por sessão com ROM/tooling/configuração | Usar esse journal, não criar uma timeline secundária que reescreva observações primárias |

`selftest.py` já registra `--self-check` dos gates na fase1 e usa fixtures/adversariais na fase2, incluindo `audit_import_semantics`, `audit_counter_window` e `audit_subagent_session` (aproximadamente linhas149–155 e194–264). A ferramenta nova cabe nesse mesmo padrão; não criar segundo runner.

## Contrato mínimo determinístico

Entrada JSON com schema versionado; CLI `--record PATH`, `--self-check` e saída JSON. O contrato não requer subagente fictício. Worker nativo, cleanup e promoção permanecem sob `session_qa.py`/`audit_subagent_session.py`.

Campos mínimos propostos:

```json
{
  "schema": "sms_observed_cases_v1",
  "profile": "journal_ram_v1",
  "rom": {"path": "/absolute/rom.sms", "sha256": "..."},
  "session": {"path": "/absolute/session.json", "sha256": "..."},
  "journal": {"path": "/absolute/commands.jsonl", "sha256": "..."},
  "layout_evidence": [{"path": "/absolute/source-or-map", "sha256": "..."}],
  "fields": {
    "enemy_hp": {"address": 49195, "type": "u8"}
  },
  "cases": [{
    "id": "life_unchanged",
    "points": {
      "before": [59],
      "after": [837]
    },
    "assertions": [{
      "op": "delta_eq", "field": "enemy_hp",
      "before": "before", "after": "after", "value": 0
    }]
  }]
}
```

Os nomes finais podem seguir a implementação do coordenador. A propriedade essencial é que points selecionem **seq de ACK real**, não um objeto de valores produzido pelo agente. A nova ferramenta deve calcular os valores e mostrá-los na saída com seq/frame/endereço/origem para cada assert. Não aceitar `observed_hp`, `presented_pose` ou `measured_latency` já calculados como autoridade.

Validações estruturais mínimas:

1. Reutilizar `check_ref` para todas as refs; SHA da ROM deve coincidir com `session.rom_sha256`. Exigir session_id/PID/frame/seq numéricos válidos e sem bool nos lugares de inteiro. ROM binária presente e hasheada; source_rom textual da sessão não basta.
2. Ler JSONL sem eval, imports dinâmicos ou execução de expressões. `ack.ok == true`; sessão/PID devem coincidir com metadata. Seq únicos e estritamente crescentes. Cada seq selecionado deve existir exatamente uma vez e ser operação `read` aceita.
3. `args=[address,length]` devem descrever RAM SMS válida; `len(ack.ram)==length`; bytes inteiros0..255, sem bool. Campo integralmente dentro de um bloco real lido. Tipos fechados `u8`, `u16le`, `s16le` (ou enum equivalente), com ranges explícitos. Nenhuma inferência por nome do campo.
4. Um point com vários reads exige o mesmo ACK.frame e nenhuma operação que avance CPU entre o primeiro e o último (`run`, `step`, `sequence`, `video`; ampliar somente por contrato claro). Mesmo frame sozinho não exclui avanço CPU dentro do frame. O bridge atual pausa no `read`, mas uma operação intermediária pode executar ciclos sem cruzar uma borda VDP.
5. Cases/points/fields/assertions têm IDs únicos, tipos corretos e quantidade não zero. Referência a point/field ausente falha. RAM insuficiente, seq desconhecido, hash errado ou JSON malformado falham com diagnóstico, sem traceback cru e sem PASS parcial.
6. Operações fechadas bastam: `eq`, `delta_eq` (subtração inteira normal), `field_eq` (comparar campos/pontos) e `vdp_delta_le`/deadline equivalente. Não introduzir linguagem de fórmulas. Para delta de contador modular, delegar ao contrato existente de `audit_counter_window` com bound explícito, ou recusar inicialmente; não mascarar underflow com `&0xffff` indiscriminado.
7. Prazo VDP deriva de `ack.frame(after)-ack.frame(before)`, nunca de `sum(step args)`, probe_frame ou tempo do script. Não usar o frame absoluto como delta. Frame regressivo ou clock desconhecido bloqueia essa operação.
8. Para um claim input→hit, o começo deve estar ligado a operação `input`/trecho de `sequence` preservado e a máscara correta. Um par arbitrário de reads não autentica o início do input. O evento final precisa de condição de ROM explicitamente satisfeita, não apenas ACK de injeção.

Limite crítico do deadline: a diferença entre duas observações é **janela observada / limite superior de detecção**, não latência exata nem primeira ocorrência. Uma observação esparsa feita depois do prazo pode reprovar a cobertura da coleta; não prova sozinha que o evento ocorreu tarde. Para alegar primeiro hit/recovery, precisa amostragem suficiente e baseline que exclua evento anterior. A ferramenta deve nomear o resultado de acordo com esse limite.

Saída mínima: `ok`, `problems`, checks por caso com valores rederivados/ACKs/unidade, refs/SHA, e `claim_ceiling: primary_journal_record_consistency_only`. Não aceitar campos de entrada que elevem esse teto. Binding e rederivação não autenticam o executável do coletor, o significado dos offsets, ausência de adulteração antes do selo, fidelidade de gameplay ou hardware real.

## O que não deve entrar na primeira versão

- Nenhuma aprovação `presented_pixels` por RAM. `resident`, `submitted` e `presented_reported` podem ser campos distintos e comparados; o veredito continua sendo coerência dos probes declarados.
- Nenhuma exigência de que pose lógica == imagem visível em todos os ticks sem um perfil de pipeline que admita o atraso correto. Esse gate não deve proibir prefetch nem criar falso positivo por desenho de pipeline.
- Não calcular FPS dividindo ticks por tempo do processo de teste; não usar médias FPS para aprovar cadência de animação.
- Não duplicar SHA/cleanup/native dispatch dos gates de QA. Nenhum novo ID de lição é necessário antes da validação: aplicações de L013/L035/L064/L097/L098 e limites correlatos já cobrem grande parte da regra.

## Self-checks positivos e adversariais

Fixtures de `TemporaryDirectory`, `offline_fixture:true`, ROM sintética explicitamente não executável; nenhum asset final ou projeto ativo como output.

Positivos mínimos:

1. RAM u8, u16le e s16le decodificados corretamente, incluindo32768→−32768 em s16.
2. Vida43→43 satisfaz delta0; vida43→36 satisfaz delta−7; eq e field_eq válidos com pontos explícitos.
3. Multi-read com mesmo frame e sem avanço entre reads.
4. ACK inicialframe120, finalframe128 e deadline8 aceito; isso mede delta8, não128 nem quantidade solicitada de step.
5. Caso diagnóstico reprovado corretamente continua produzindo report legível com `ok:false`; não se transforma em erro de parser nem altera a evidência.

Negativos mínimos (mutações independentes do fixture bom):

- Hash stale, ROM da sessão diferente, sessão/PID do ACK diferente, ACK recusado.
- Seq repetido, fora de ordem, inexistente, selecionando `step` como se fosse `read`.
- RAM curta, byte bool/float/>255, comprimento/args incorretos, campo fora do intervalo, tipo/endian desconhecido, valores de assert bool/float inválidos.
- Cases/assertions vazios, IDs duplicados, point/field desconhecido, entrada JSON não objeto ou JSONL quebrado.
- Point formado por reads em frames distintos; mesmo frame com step/run intermediário.
- Vida43→36 rotulada delta0 deve falhar. Contexto esperado7 mas observado0 deve falhar, não aceitar só contador role_changes>0.
- Deadline8 com deltaVDP9 falha o prazo observado; contador ROM que avançou6 não substitui esse relógio.
- Input de máscara errada, input ausente ou início escolhido depois do evento não paga input→hit.
- `presented_pixels:true` ou claim de FPS/AAA não vira capacidade aceita; probe de cache sozinho não autoriza esses claims.

Fase2 do `selftest.py`: pelo menos fixture positivo real do parser, negativo vida43→36/expected0 e negativo multi-read mesmo frame com avanço CPU intermediário. Manter todos os casos do `--self-check`; não substituir a suíte existente. Nada de emulador no self-check.

## Acervo real disponível para dogfood read-only

### OpenBOR M6 — dois journals preservados na mesma ROM

Raiz: `/mnt/sdcard/Projects/SMSForge/SMS_projects/openbor_sms_rev1`.
ROM esperada: `76cdbee3f10a58a07199b9012ff6dbe53df372d7532d6a8aa324089824425e73`.

1. `out/evidence/m6/sessions/0b271ce0621a4adc914ab5c4d37be07b/commands.jsonl`
   - SHA rederivado nesta leitura: `c4d1825c6a406e3ec2a3235dc81b8a75a91ab07ec9754c1da9784bfcfab2ba24`.
   - 839 rows. Read `args=[49190,30]` (base 0xC026): byte 5, endereço 0xC02B, valor 50 no ACK seq 4/frame 180, 43 no seq 59/frame 310 e 43 no seq 837/frame 663.
   - Controle positivo aritmético: comparar43→43 (delta0). Esses dois checkpoints, sozinhos, não comprovam distância41 nem ausência de contato em toda a janela; para isso selecionar também os pontos de geometria/caso corretos.
2. `out/evidence/m6/sessions/f41e8c8c089042be85fd1c9643900043/commands.jsonl`
   - SHA rederivado nesta leitura: `7b199e5c1b013f4335d930752a44c6344bc28e6241694ac393982023b8286c9e`.
   - 825 rows. Mesmo bloco: 43 no seq 59/frame 310; 36 no seq 785/frame 646 e no seq 823/frame 646.
   - Controle negativo aritmético real: assert delta0 nessa seleção deve falhar; delta−7 deve passar. Não editar o resumo ou journal para produzir o resultado.

Os respectivos `session.json` estão nas mesmas pastas; precisam entrar nas refs do dogfood. Os resumos `out/evidence/m6/depth_*.json` são derivados e não substituem esses reads. O report do caso alinhado possuía campos whiff com dz6/43→36, enquanto o claim agregado dizia whiff41/43→43: a nova ferramenta deve impedir essa troca de controle ao exigir seq/caso/valores explícitos, sem presumir que o nome `depth` autentique o caso.

O endereço0xC02B acima foi usado para rederivação dos bytes preservados e corresponde ao layout declarado pelo coletor; bindar o header/map/source apropriado antes de chamá-lo semanticamente de HP. Um hash de layout não prova sua interpretação.

### MUGEN rev2 — evidência insuficiente como controle negativo de custódia

`/mnt/sdcard/Projects/SMSForge/SMS_projects/luta_mugem_rev2/out/logs/wave5b_rom_causal.json` (SHA58ac2040…) e log agregado existem para ROM6f4a3cf5…, porém o journal/session temporário não foi preservado. O instrumento novo deve recusar auditoria de observações primárias desse29/29 por ausência dos primários. Não fabricar um journal a partir do resumo para criar fixture real positivo.

Há um ACK bruto histórico em `out/evidence/m2_wave5a/probe_read_f1027.json`, seq12/frameVDP2220 e ROMloop1027, na ROMv029. Serve para demonstrar que os relógios são distintos e para validar um decoder de bloco; isoladamente não é janela completa nem prova da v031. Fixtures sintéticos podem representar o caso de regressão, claramente separados desse artefato real.

## Próximo ganho, depois da primeira ferramenta

O novo gate resolve rederivação e janela observada; ele não resolve o renderer. Para provar apresentado, a extensão futura mais enxuta é permitir a `audit_render_glitch` uma **timeline de identidade esperada por frame VDP**, com origem independente e binding a vídeo/ROM/poses, além do modo atual de melhor imagem legal. Isso reprova imagem válida de pose errada no instante do hit, enquanto o gate primário verifica os probes de lógica/residência/submissão. Precisa fixtures onde pose antiga é uma imagem legal e, mesmo assim, falha a timeline; não construir expected copiando a captura sob teste.

Essa extensão futura só deve ser promovida depois de existir um oráculo válido. Não converter uma lista de IDs declarados nem um probe chamado `presented` em prova de pixels apresentados.
