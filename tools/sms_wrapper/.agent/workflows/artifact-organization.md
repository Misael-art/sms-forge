# Workflow: organização e retomada de artefatos

Use ao criar ou retomar concepts, model sheets, sprite sheets, planilhas de
planejamento, provas de conversão, animação ou protótipos. O registro é um
índice dos arquivos reais; não cria outra árvore de arte nem substitui memory
bank, GDD, contratos, lineage ou manifestos de produção.

## Antes de produzir

1. Leia as autoridades do projeto e resolva o registro com
   `artifact_registry.py locate --project /caminho/absoluto/do/projeto
   --asset ID --kind PAPEL --variant main`. Projetos novos usam
   `doc/artifact_registry.json`; adoções existentes podem ser apontadas pelo
   catálogo central `doc/artifact_registry_catalog.json`. Havendo duas
   autoridades, reconciliar antes da escrita. Não criar um registro alternativo
   para contornar uma falha.
2. O coordenador mantém uma entrada por asset/papel/variante e dois ponteiros
   distintos: candidata ativa e aprovada. Maior versão, data mais recente,
   aparência ou PASS técnico não selecionam aprovação. Se os documentos
   discordarem, registrar o conflito e conferir a decisão e o hash. Histórico
   continua histórico; não reescrever pareceres antigos como se fossem atuais.
3. Reutilize a localização e o tipo registrados. Uma necessidade criativa nova
   amplia `kinds` no mesmo registro: finalidade, motivo concreto, procedimento,
   localização existente e papéis de arquivo requeridos. Só acrescentar uma
   localização quando as existentes não servirem; definir sua finalidade e
   evitar sobreposição. Uma nova vista, detalhe de arma ou comparação não
   justifica outra raiz do personagem. Variantes solicitadas coexistem em IDs
   explícitos, sem disputar o mesmo ponteiro. Experimentos paralelos devem ter
   hipóteses distintas registradas, não duas autoridades para a mesma escolha.
4. Reserve a próxima revisão com `status: reserved`, arquivos de saída exatos,
   IDs dos pais e motivo do delta. Paths são sempre relativos ao projeto;
   projeto e registro no pedido Harness são absolutos. Não repetir
   `SMS_projects/<projeto>/` dentro do projeto. Pais apontam a fonte real;
   metadata/lineage da revisão registra prompt, ferramenta e SHA/argumentos
   quando houver script, transformação, pose IDs, referências e escopo.
5. Execute `artifact_registry.py check --project /projeto --scan`. O Harness
   exige, para `visual_production` com escrita, `artifact_registry` contendo
   `project`, `path`, `sha256`, e `artifact_ids` reservados no task. `write_paths`
   deve listar exatamente os arquivos reservados, sem diretório amplo.
   Coordenador escreve o índice; workers produzem somente os arquivos designados.
   A mesma checagem vale para arquivos visuais/planilhas declarados por qualquer
   kind: chamar uma produção de `inventory` ou `visual_review` não dispensa a
   reserva. QA nativa continua usando seu pedido e diretório exclusivo de sessão
   via `session_qa.py`; seus manifests auditam as mídias internas, sem duplicar
   a árvore de capturas no registro visual. Não usar esse diretório para peças
   de criação. O Harness não inspeciona conteúdo futuro de um diretório genérico.

## Após cada tentativa

- Confira os arquivos realmente salvos antes da conversão: para sprite sheet
  com contrato de exportação, `audit_source_raster.py`. Arte bruta livre pode
  permanecer como referência; não declarar alpha/keycolor/paleta só pelo prompt.
- Troque a reserva por `candidate` e sele os arquivos pelo SHA. Inclua metadata,
  lineage e reviews como artefatos com pais, sem atribuir o mesmo arquivo a dois
  donos. Resultados de conversão/ROM são derivados com papéis próprios.
- Não sobrescreva revisão selada. Corrija em revisão nova e marque o ponteiro
  anterior como `superseded`, preservando seu hash e decisão histórica. Arte
  rejeitada só recebe `rejected` mediante registro da decisão; tentativa
  técnica falha pode ficar histórica com motivo e relatório.
  `parents` identifica inputs reais; `supersedes` liga a revisão anterior da
  mesma chave sem afirmar que os pixels foram derivados dela.
- `approved` exige decisão `sms_artifact_decision_v1` ligada a ID, papel e todos
  os paths/SHA daquela revisão, com ator owner e origem textual da decisão.
  Registre a decisão real do usuário; nunca a fabrique. O gate verifica
  consistência declarada, não autentica o autor da aprovação. Aprovar uma fonte
  não aprova conversão, animação, ROM ou entrega. Nenhum `approved` organizacional
  dispensa os gates de `artwork-to-rom-lifecycle.md`.
  Na adoção, o adaptador estreito `sms_animation_source_lineage_v1` preserva a
  declaração original existente de fonte animada; confere personagem, arquivo,
  SHA e copia literalmente `approval_scope`. Não autentica a declaração nem
  transforma esse escopo em aprovação da conversão/ROM.
- Feche com `check --scan`, atualize memory bank com ID do registro, candidata,
  aprovada, conflitos, próxima etapa e links. Na retomada, resolver esses IDs;
  não regenerar material íntegro por não lembrar seu caminho.

## Diretório ativo e arquivo histórico

Após a decisão do dono, deixe na raiz do diretório do asset apenas a revisão
aprovada ativa e seus sidecars canonizados. Mantenha outra aprovação de papel
distinto em `approved_records/`, uma revisão aprovada substituída em
`historical_approved/` e exercícios/candidatas em `review_drafts/`. Não apague
nem sobrescreva o arquivo histórico. Toda movimentação path-bound atualiza o
registro e as referências operacionais; guarde um mapa reversível com SHA antes
e depois. Se a revisão independente foi feita antes da movimentação, preserve o
relatório original como evidência daquela localização e demonstre a continuidade
por hash idêntico e pelo mapa de organização. Organização não altera nem renova
a aprovação artística.

## Adoção do acervo existente

`artifact_registry.py inventory --project /projeto --roots data/source_art
--json /novo/relatorio.json` descobre e hasheia sem mover arquivos. Relatórios
de descoberta não são outro registro autoritativo. Use `legacy_inventory` para
arquivos preservados ainda sem classificação; isso não lhes dá aprovação.
Localizações `managed` bloqueiam arquivos não registrados com `--scan`;
`legacy` ficam explicitamente fora dessa cobertura exaustiva. Adote por lote,
sem apagar descartes, renomear milhares de peças ou promover status pelo nome.

O catálogo central é a autoridade de localização, com projeto/path únicos;
ele não duplica o conteúdo do registro. Cópias `.agent` antigas continuam
intactas: leia este workflow central antes de nova produção.

## Alcance do gate

`artifact_registry.py` mede unicidade de IDs/revisões/heads, propriedade de
paths, SHA, pais sem ciclos, reservas, destinos, decisão e cobertura das áreas
managed. Não julga se dois tipos têm a mesma finalidade artística, não bloqueia
um processo que ignore o Harness e não oferece lock transacional de filesystem.
O coordenador serializa alterações do registro e repete o preflight antes de
produzir. Inventário/PASS de organização não prova qualidade, poses desenhadas,
fidelidade de render, hardware, FPS, gameplay ou entrega.
# Divergência entre decisão e memória (L124/L127)

Se uma decisão nova aprova a fonte, mas memory/registry ainda dizem pending,
registre conflito e confira o escopo e bytes da candidata/cópia aprovada. Uma
imagem em `res/approved_art` não é prova de integração, build ou ROM executada.
Não herdar evidência de uma ROM anterior para nova folha; resolver seu hash e
produzir evidência atual antes de promoção de runtime. Mudança de autorização
exige atualizar método/manifesto/output path da revisão; não reescrever o
relatório histórico. Caminhos ou SHA truncados são blockers de vínculo, não
motivo para regenerar arte intacta. Concilie o registro central com a autoridade
operacional antes de iniciar outro ciclo; marque o ramo afetado bloqueado se
essa conciliação ainda depender de documentos/pareceres indisponíveis.
