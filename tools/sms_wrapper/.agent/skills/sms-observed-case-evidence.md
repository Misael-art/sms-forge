# skill: sms-observed-case-evidence

Use ao conferir um assert de RAM ou prazo observado contra o journal primário
de uma sessão privada. Aplicação de L013/L035/L064/L097/L098 e §128. Não
substitui QA de imagem/áudio, replay do jogo, nem a validação de sessão.

## Escolher a evidência que responde ao claim

- `audit_subagent_session.py`: pedido, ROM, contexto, caso, mídia e cleanup.
- `audit_observed_cases.py`: rederiva valores/deltas RAM e intervalos VDP dos
  ACKs preservados. “Sem dano” não é dano abaixo de um teto; delta zero nos
  endpoints é apenas saldo líquido e pode esconder dano seguido de cura.
  Use contador de eventos ou timeline adequada para ausência de hits;
  “chegou à borda” exige a posição final, não apenas estar dentro da arena.
- `audit_import_semantics.py`: coordenadas, identidade/duração AIR e revisão
  de cache nos perfis declarados. Bytes CLSN na ROM não provam contato visível.
- `audit_render_fidelity.py` / `audit_render_glitch.py`: arte/imagens legais
  no alcance do modo usado; imagem legal antiga pode ter timing incorreto.

## Perfil journal_ram_v1

O record de `audit_observed_cases.py --record RECORD` contém referências
absolutas `{path,sha256}` para `rom`, `session`, `journal` e `layout_source`.
O layout é a fonte revisada dos offsets: o gate não autentica seu significado.

`fields` mapeia nomes para `{address: inteiro, width: 1|2, signed: boolean}`.
O perfil limita reads à RAM nativa 0xC000..0xDFFF e blocos de até 256 bytes,
conforme a ponte atual. Operações desconhecidas são recusadas.
`points` mapeia checkpoints para `{seqs:[ACKs]}`. Reads de um checkpoint têm
o mesmo frame VDP, bytes coerentes e nenhuma execução/input entre eles.
Um ponto `{seqs:[N], anchor:"input"}` usa o ACK real de operação `input`.
O perfil ainda não extrai o começo de um gesto dentro de `sequence`/`video`.

Cada caso tem `id` e `conditions`, com ao menos um assert de RAM:

```json
{"id":"impacto","conditions":[
  {"op":"eq","point":"antes","field":"life","value":50},
  {"op":"delta_eq","from":"antes","to":"depois","field":"life","value":-7},
  {"op":"field_eq","point":"depois","field":"logical_pose","other_field":"submitted_pose"},
  {"op":"vdp_deadline","from":"entrada","to":"depois","max_vdp_frames":20}
]}
```

O exemplo é schema, não orçamento de gameplay. O prazo vem do GDD/caso. Delta
é subtração numérica, não contador modular: use `audit_counter_window.py` para
voltas. `--report-out` cria um arquivo novo e recusa destino existente.
Fixture completa executável: `audit_observed_cases.fixture(temp_dir)`; fica
marcada offline e não equivale a execução de ROM.

## Limites que mudam a decisão

RAM `current_pose` pode indicar apenas cache residente, mesmo com ator omitido.
Separe desejada → residente → submetida SAT/PNT → apresentada em framebuffer.
O gate pode comparar os probes declarados; não chama isso de pixels apresentados.
Exigir vídeo/frames e alinhamento temporal independente para contato visível.

ACK observado dentro do prazo prova aquele checkpoint. Uma observação tardia
reprova a cobertura/prazo amostrado, mas não demonstra quando um evento não
amostrado ocorreu pela primeira vez. Ticks lógicos completados por espera
crescente não aprovam latência. FPS requer execução contínua e ferramenta própria.

Caso agregado sem journal não pode ser reconstruído do resumo para passar.
Preserve o relato histórico e colete evidência nova. O selo de uma lista só
confere a lista fornecida: incluir positivo, negativo, terminal e vínculos de
sessão previstos no pedido. Falta de controle negativo é lacuna de cobertura.

Para decidir crescimento do jogo, leia `workflows/product-quality-checkpoint.md`.
Para mudar cache/renderer, leia `skills/sms-runtime-optimization.md`. Um teste
de consistência aprovado não substitui essas decisões nem a revisão perceptiva.

### Contato e recuperação de combate

Para dano, a observação RAM mede consequência lógica. Para contato perceptivo,
alinhar orientação, extensão visível do golpe e alvo no mesmo frame do hit.
Uma espada atrás do atacante com dano no adversário à frente é defeito de
apresentação mesmo com probe correto. Medir separadamente controle liberado
e pose final exibida; a fila de upload pode separar os dois. Definir o terminal
no pedido, capturar sua cauda e não extrapolar além da janela observada.
