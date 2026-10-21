# Intake MUGEN — base/OUTROS — 2026-10-07

Leitura das fontes sem extraí-las ou alterá-las. Os resultados de parser e corte são derivados locais em `out/local_study`; não são ROM nem aprovação de uso público.

## Fontes Ryo e Terry

| Pacote | SHA-256 | Identidade | Inventário parseado | Licença |
|---|---|---|---|---|
| `OUTROS/ffspRyo_v3.zip` | `7272abcf787c0946fd388be84010b720579be5d301590b0eec8e7f22f0f32133` | Ryo Sakazaki; autor Raiwa | 553 sprites, 197 animações, 1.151 frames, 1.716 caixas CLSN, 123 comandos, 180 estados, 61 sons, 12 paletas | desconhecida; `ReadMe_v3.txt` identifica autor/data e comandos, sem concessão de licença |
| `OUTROS/A-Terry.zip` | `ad646be47eb314ee0ea8d5595b4524823e277a722c9162c59ce8bd05b085687c` | Terry Bogard; `Author: Falchion22` | 260 sprites, 134 animações, 518 frames, 1.980 caixas CLSN, 49 comandos, 113 estados, 28 sons, 4 paletas | desconhecida; não há README/licença no ZIP |

Os dois pacotes têm `.def`, `.sff`, `.air`, `.cns`, `.cmd`, `.act` e `.snd`; ambos usam SFF `1.0.1.0`. Os parsers terminaram sem erro estrutural e sem referência de arquivo obrigatória ausente. Isso ainda não comprova fidelidade visual, execução das ações ou compatibilidade com hardware.

## Lacunas da fonte

- Ryo declara `stcommon = common1.cns`, ausente no pacote; o parser substitui por `common_forge.cns` e registra 30 estados dessa origem. Isso é aproximação e precisa permanecer identificado no runtime.
- Ryo tem o sprite ausente `(20005, 5)`, usado por `Anim 20005`, frame 6.
- Terry tem `(99, 0)` em `Anim 1020` e `3010`, `(99, 2)` em `Anim 1005`, e `(1010, 2)` em `Anim 1010`. A conversão não pode alegar esses pixels presentes.
- A ação Ryo `221` é o estado “standing heavy punch (far)”, animação 221, selecionado pelo comando `z`. O corte atual declara `hp=220` e `punch_far=201`; ele não importa 221.
- O Ryo/Ryo gerado abaixo declara 18 papéis, mas a tabela de luta atual consome só 12. Permanecem sem roteamento `hit=5000`, `air_lp=600`, `air_hp=620`, `air_lk=630`, `air_hk=650` e `punch_far=201`; o relatório gerado agora torna essa perda explícita. Os dados `air_*` e o golpe distante ainda não são jogáveis por essa tabela.

## Outros itens de `OUTROS`

- `A-Mai.zip` contém outro pacote de personagem, fora da ordem atual de roster; licença desconhecida.
- `ffspRyoS.zip` é o stage “Gan-ryu Island”. Está excluído da produção: o escopo atual exige fundo sólido sem cenário.
- `ssf2tgeese.rar` contém um pacote Geese separado, atribuído no README a Vegeta 20XX; o autor pede contato antes de reutilizar material. O importador o analisa como fonte, mas não gera assets/runtime nem o usa como fonte de Ryo/Terry.
- O inventário completo atualizado de `base/` achou 14 arquivos compactados (13 ZIPs + 1 RAR), 4 DEFs de personagem, 26 DEFs de stage e 1 DEF de tipo desconhecido. Os arquivos antigos de `base/character/` não substituem os pacotes completos recém-curados de Ryo/Terry.

## Corte Ryo/Ryo produzido

Entrada: `data/ryo_v3_runtime_cut_20261006.json`, ação/paleta em P1 `ffspRyo_4`, P2 `ffspRyo_5`, alvo de idle de 72 px. O corte produziu dois slots e 77 poses por slot. Os arquivos por slot somariam 62 páginas de 16 KiB; como este piloto usa o mesmo pacote nos dois lados, a deduplicação exata do corte reduziu o blob físico para 31 páginas (507.904 bytes), antes de código, áudio, HUD e outros recursos.

Arquivos:

- `mugen_inventory.json` — inventário ZIP de `base/OUTROS`.
- `base_inventory.json` — inventário ZIP/RAR de `base/`, com hashes e metadados DEF/SFF.
- `ryo_ir.json`, `terry_ir.json` — resumos IR com autor preservado.
- `ryo_ryo_cut/versus_scene_manifest.json` — hashes, poses, paletas e bancos do corte.
- `ryo_ryo_cut/fight_runtime_data_manifest.json` — papéis consumidos e papéis ainda sem runtime.

Estado: fonte parseada, corte de assets gerado e tabelas de runtime conectadas ao `fight.c`; a unidade C compila. Link/build da ROM, execução em emulador, vídeo, frame advance, budgets e QA nativo ainda não realizados. Os documentos canônicos do projeto continuam retornando EIO, então a sessão QA não pode ser preparada com o contexto obrigatório.

## Runtime integrado — tentativa Ryo/Ryo em 2026-10-07

- O `fight.c` integrado passou a incluir `fight_runtime_data.h`, gerado por slot a partir dos manifests. LP/HP/LK/HK usam as ações configuradas (200/220/230/250), parâmetros de vida/física/dano vêm do respectivo manifest e o relatório mantém os seis papéis restantes como não roteados.
- `special` segue sem comando MUGEN roteado e sem entidade de projétil; a tecla dedicada ainda só seleciona a animação visual, sem hit/dano de especial.
- O namespace P1/P2 do corte é traduzido para os aliases de armazenamento Ken/Ryu usados pelos leitores bancados. A tradução afeta apenas identificadores de slot; sufixos de paleta como `_P2_TILES` ficam preservados.
- Geração automática pelo wrapper de descritores: 2 páginas de metadados, 1 página de dados AIR/CLSN e 1 página de índice. Com as 31 páginas do corte, o mapa desta tentativa usa 35 páginas, bancos 2–36.
- A validação por ação detectou pose bruta com pico de 9 sprites/linha na ação `1000` (papel `special`, quadro fonte 5). `audit_sprite_line_sim` reprova essa pose antes do scheduler. O `fight.c` já tem quotas por linha e rotação de peças, mas o resultado visual/flicker dessa proteção ainda precisa ser visto no ROM.
- O objeto SDCC de `fight.c` compilou com os cabeçalhos gerados pelo wrapper; isso é somente compilação de uma unidade, sem link nem ROM.
- O wrapper parou no gerador de PSG ao abrir `doc/audio_provenance_manifest.json` (EIO), depois de produzir as tabelas de runtime e comandos. Esse manifesto é obrigatório; nenhum PSG copiado ou inventado foi usado para contornar a falha. Sem ele não houve ROM e a QA nativa continua sem preparação, também por EIO nos documentos operacionais.

Verificações focadas: 18 testes passaram; self-checks de `integrated_runtime_data`, `pose_table`, `source_frame_data`, `trim_scene_header`, `cmd_patterns`, `audit_sprite_line_sim` e `build_luta_source_pair` passaram. O gate de pose bruta registrou 9 sprites/linha antes do scheduler. Os testes não cobrem a saída visual do scheduler em emulador.

Artefatos locais: `../ryo_ryo_runtime_20261007_c/inc/fight_runtime_data.h`, `../ryo_ryo_runtime_20261007_c/out/fight_runtime_data_manifest.json`, `../ryo_ryo_runtime_20261007_c/out/obj/fight.rel` e a testemunha bruta `../ryo_ryo_runtime_20261007_b/out/audit_sprite_pose54_manifest.json`.

## Terry importado e cortes de roster — 2026-10-07

Configuração fonte: `../../../data/terry_falchion22_runtime_cut_20261007.json`.
Ela fixa escala uniforme com idle de 72 px, paletas ACT `norm`/`black` e o mapa
de botões específico do Terry: `x/y` para socos e `a/b` para chutes. O Ryo mantém
seu perfil `x/z` e `a/c`; ambos usam KEY_1 para soco, KEY_2 para chute e limiar
de 6 ticks. `PowerWave_x` é apenas um nome de comando preservado no corte; o
runtime não o roteia nem cria uma entidade de projétil.

A auditoria do `State -1` encontrou `x→200/205`, `y→210/215`, `a→220/225` e
`b→230/235` conforme distância/estado. O runtime comum ainda escolhe 200/210/
220/230; somente a variante curta 205 foi importada como papel sem consumo, e
215/225/235 foram excluídas do corte. A pose de agachamento é Action 11, não a
Action 100 de corrida. A guarda agachada ativa é Action 131 (hold de duração
`-1`); Action 141 é GUARDEND e não deve ser repetida. O papel KO usa Action 5110
com State 5150: Action 5140 não existe no pacote e `common.cns` cai para 5110.
Action 5155 mostra o mesmo quadro por um tick, mas não é chamada por essa lógica.
O runtime conserva só a pose KO de um frame; não executa as transições CNS.

O salto importa apenas Action 41. A fonte também usa Action 40 de início,
variantes direcionais 42/43 e ações de descida; o runtime ainda não encadeia
essas fases. `loop_start=0` em idle, caminhada, salto e agachamento é uma
política local, não uma declaração de `LoopStart` do AIR. O corte importa
Action 5000 de hit e as quatro ações aéreas 600/610/620/640, mas esses papéis
não são consumidos pelo loop atual. O `.cmd` ainda declara PowerWave x/y, Burn
Knuckle x/y, Crack Shoot a/b, Rising Tackle x/y e Power Geyser x/y; nenhum está
roteado para uma entidade de golpe/projétil no runtime.

A configuração registra 11 limitações de fidelidade/escopo. `scene_cut.py`
agora valida essa lista e a preserva no manifest por personagem; o corte de
roster e o relatório de runtime integrado também carregam as limitações por
slot. A política de paleta é neutra a personagens: P1 usa entradas 1–7, P2
entradas 9–15 e índice 0 permanece transparente. Os sprites faltantes `(99,0)`,
`(99,2)` e `(1010,2)` continuam fora das ações deste corte.

### Regeração após revisão de fonte — 20261007b

| Corte local | Poses P1/P2 | Páginas de arte | Bytes de arte | Páginas mapeadas totais* |
|---|---:|---:|---:|---:|
| `terry_terry_cut_20261007b` | 79 / 79 | 29 | 475.136 | 33 (bancos 2–34) |
| `ryo_terry_cut_20261007b` | 77 / 79 | 60 | 983.040 | 64 (bancos 2–65) |

\* Soma de arte, metadata de pose, frame data e índice de pose gerados; não
inclui código compilado nem áudio.

Os manifests novos confirmam os seis papéis não consumidos por slot: Terry
`hit`, quatro ações aéreas e `punch_close`; o Ryo mantém `hit`, quatro ações
aéreas e `punch_far`. Os aliases LP/HP/LK/HK foram convertidos para cada slot.
O gerador também emitiu oito padrões de comando por par, mas a presença de um
padrão no manifest não significa que o loop da luta o consuma. Os nomes de
diretório/símbolo `p1_ken`/`p2_ryu` e `ken`/`ryu` são namespaces internos
históricos; `source_def` e SHA nos manifests identificam o personagem importado.

Validação estática: 14 testes focados passaram; os self-checks do corte versus,
runtime integrado e escalonador de linhas passaram. As dez unidades C não áudio
compilaram com SDCC em cada clone, sem link. `audio.c` ficou sem compilação
porque `psg_blobs.h` depende do manifesto PSG ilegível. `audit_row_schedule.py` passou 6.241
pares Terry/Terry e 6.083 Ryo/Terry, duas paridades, SAT máximo 48 e pico de 8
sprites por scanline, cobrindo as poses em janelas de 8 frames. Esse resultado
é modelo estático; não prova framebuffer nem flicker em ROM.

O wrapper gerou manifests, tabelas de runtime/comando, metadata, frame data e
índices, mas parou no gerador PSG ao ler `doc/audio_provenance_manifest.json`
(EIO). Os documentos canônicos do projeto também seguem em EIO. Não houve link,
ROM, sessão QA privada ou validação em emulador; esses eixos ficam `not_run`.
O corte `20261007a` permanece como histórico; `20261007b` é o corte corrente
com a guarda e o KO corrigidos.

Artefatos atuais: `../terry_terry_cut_20261007b/versus_scene_manifest.json`,
`../ryo_terry_cut_20261007b/versus_scene_manifest.json`,
`../terry_terry_runtime_20261007b/out/fight_runtime_data_manifest.json`,
`../ryo_terry_runtime_20261007b/out/fight_runtime_data_manifest.json`,
`../terry_terry_runtime_20261007b/out/audit_row_schedule_manifest.json`,
`../ryo_terry_runtime_20261007b/out/audit_row_schedule_manifest.json` e
`../../../data/terry_falchion22_runtime_cut_20261007.json`.

## Lote close e correção de acorde — 2026-10-07

Os cortes atuais são `../terry_terry_cut_20261007c_close/` e
`../ryo_terry_cut_20261007d_close/`. Os quatro State -1 de curta distância do
Terry (205/215/225/235) ficaram vinculados a `x/y/a/b`, à condição estrita
`P2BodyDist X < 15` e aos gates de ataque em pé (`Statetype=S`, `ctrl`, sem
`holddown`). O importador rejeita grupos/predicados adicionais que o runtime
não modela. O relatório agora registra flags, dano, política/fidelidade HitDef,
limiar escalado, `ground.front` fonte e fator de escala por slot.

A revisão encontrou e corrigiu o `ground.front` ausente no slot Ryo: no corte
Ryo/Terry, os fronts escalados são 3101/2928 Q8.8; os quatro close states do
Ryo permanecem sentinelas sem dano e usam fallback para ataques base. No
Terry/Terry, ambos os fronts são 2928 Q8.8 e os quatro close roles existem nos
dois slots. O runtime também exige máscara exata de botões, então `y+b` não
dispara por engano HP/HK simples; acordes não mapeados são rejeitados.

Validação estática: 55 testes focados passaram, incluindo extração fail-closed,
geração de dados por slot e anel C de comandos/acordes. Os self-checks do corte
versus/runtime integrado e o `audit_import_semantics.py` passaram; os contratos
de distância registraram 32/33 px para Terry/Terry e 33/34 px para Ryo/Terry.
`fight.c` compilou como unidade SDCC nos dois cortes. Esses resultados não
validam o loop no hardware.
Build/link de ROM e QA privada no emulador não rodaram: a leitura de
`doc/audio_provenance_manifest.json` e dos documentos canônicos do projeto
continua falhando com EIO. Estado desta entrega: dados gerados e objeto C
compilado; ROM/emulador, gameplay, FPS, áudio e budgets seguem `not_run`.

Artefatos: `../terry_terry_cut_20261007c_close/runtime_compile/out/fight_runtime_data_manifest.json`,
`../ryo_terry_cut_20261007d_close/runtime_compile/out/fight_runtime_data_manifest.json`,
`../terry_terry_cut_20261007c_close/runtime_compile/out/obj/fight.rel` e
`../ryo_terry_cut_20261007d_close/runtime_compile/out/obj/fight.rel`.

### Continuação: fallback distante do Ryo — 2026-10-07

A fonte `ffspRyo.def` confirma a seleção ordenada do golpe LP: State 200 é o
ataque próximo (`P2BodyDist X < 32`) e State 201 é o fallback para distância
`>= 32`. O runtime agora seleciona `punch_far` no State 201 com o limiar
escalado 5512 Q8.8 (`32 * 72 / 107`), preservando entrada direta em pé/com
controle e sem `holddown`. Grupos de trigger para chain/cancel permanecem
registrados como não compilados; o suporte cobre apenas a entrada direta.

Os dois manifests integrados foram regenerados com a tabela ampliada para 20
papéis de estado e `fight.c` compilou como unidade SDCC em ambos os cortes.
Ryo/Terry reporta `punch_far` disponível apenas no slot P1, limiar `[5512, 0,
0, 0]` e `ground.front` 3101/2928 Q8.8; Terry/Terry mantém far slots ausentes
e `ground.front` 2928/2928. O contrato estático de distância está vinculado aos
SHA das duas fontes e registra os casos `axis_gap_sms` 45/46 como abaixo/acima
do limiar de origem. O lote focado fechou com 59 testes passando.

Isso valida extração, geração de tabelas e compilação do objeto; não valida
link, ROM, gameplay ou emulador. Esses eixos continuam `not_run`, pois o
manifesto PSG e os documentos canônicos do projeto retornam EIO.

### Expansão dos fallbacks distantes do Ryo — 2026-10-07

A revisão nativa estática confirmou três pares adicionais nos gates `State -1`
do Ryo, além de LP: HP `220→221` pelo comando `z`, LK `230→231` por `a` e HK
`250→251` por `c`. Os quatro pares usam a regra próxima `< 32` antes do
fallback distante, com porta direta em pé/controle e sem `holddown`. O mapa de
dois tiers ainda descarta `y/b`; as condições de chain/cancel continuam no
manifest como grupos não compilados.

O corte `../ryo_terry_cut_20261007e_farset/` gerou 94 poses de Ryo e 97 de
Terry; a arte ocupa os bancos 2–75. Os dados derivados usam metadata 76–77,
frames 78 e índice de poses 79. `p1_far_distances_q8` é `[5512, 5512, 5512,
5512]`; os danos de runtime são 30/62/35/80 para State 201/221/231/251, com
política de HitDef aproximada. A fonte também registra que State 220 near usa
`velset=2,0,0` enquanto o runtime mantém velocidade HP zero, e que States
250/251 usam `physics=N`, não importado pelo runtime.

Validação focada: 56 testes passaram. `fight.c` compilou como unidade SDCC
(exit 0). `audit_row_schedule.py` passou 9.118 pares de poses, duas paridades,
SAT máximo 48 e pico de 8 sprites por scanline, no modelo de âncoras fixas.
`audit_import_semantics.py --record` aceitou o contrato estático de distância
com casos de separação 45/46; o teto permanece `declared_record_consistency_only`.
O revisor nativo cobriu os gates das quatro rotas e identificou as limitações
acima; esta foi revisão estática, sem sessão de emulador.

Build/link e sessão QA privada seguem `not_run`: o manifesto PSG e os
documentos canônicos `10-memory-bank.md`, `11-gdd.md` e `15-tdd.md` continuam
retornando EIO. Esses resultados não validam gameplay, FPS, áudio, orçamento
dinâmico nem execução em ROM.

Artefatos: `../ryo_terry_cut_20261007e_farset/runtime_compile/out/fight_runtime_data_manifest.json`,
`../ryo_terry_cut_20261007e_farset/runtime_compile/out/far_distance_contract.json`,
`../ryo_terry_cut_20261007e_farset/runtime_compile/out/audit_row_schedule_manifest.json`
e `../ryo_terry_cut_20261007e_farset/runtime_compile/out/obj/fight.rel`.

### Itens adicionais de OUTROS e intervalo temporal Animelem — 2026-10-07

`A-Mai.zip` (SHA-256 `7bc86caa1397b00bbb8943cdffdc9d08842c74284f7baa57b6af4c888b8fb255`) identifica
Mai Shiranui, autora Falchion22. Parse estrutural: 257 sprites, 3 paletas, 136
ações, 469 frames, 1.569 caixas CLSN, 51 comandos, 26 sons e 133 estados;
sem referência de arquivo/sprite ausente ou erro de parser. Dos 627 controladores,
544 são direct, 56 approximate e 27 unsupported. A geração `smsdev` produziu
1.822 artefatos / 194.974 bytes e passou o simulador estático com pico de 8
sprites por linha e SAT 32; 193 itens ficaram excluídos pela classificação.
Isso valida a conversão offline desse pacote, não runtime de Mai em ROM. Licença
continua desconhecida e não houve promoção de personagem/arte ao jogo.

`ssf2tgeese.rar` (SHA-256 `d1b7a9e8ce6acd517f186f4676025f680950f349bd8b608bba7f3ad4c963d934`)
identifica Geese, autor Vegeta 20XX. O README interno pede contato antes de
reutilizar material, salvo a exceção que descreve para personagens derivados;
por isso não foram gerados assets SMS nem runtime. O `Source` agora aceita `.rar`
diretamente via `7z/7zz`, extrai em diretório temporário privado, mantém o SHA
do RAR original e recusa nomes com traversal e links simbólicos. O inventário
agora lista ZIP e RAR: `OUTROS` tem 5 arquivos compactados sem erro; o inventário
de `base/` tem 14, incluindo 1 RAR.
O primeiro passe achou que `Animelem = 2,[0,16]` abortava: a cláusula temporal
por intervalo não estava no parser. `expr.py` agora traduz essa forma para
`animelemtime(2)` dentro do intervalo inclusivo. Os testes executam as bordas
`-1, 0, 16, 17`, preservam `animelem = n` e `timemod`, e a suíte focada de
expressões passou 25 casos. A suíte focada de Source/expressões/personagem/
inventário passou 40 casos. Uma revisão nativa independente confirmou o
bytecode/flags e a semântica da VM; segue sendo QA estática, sem ROM. Com isso o
parse concluiu: 449 sprites, 12 paletas, 173 ações, 747 frames, 594
entradas CLSN, 50 comandos, 28 sons e 119 estados; 505/120/34 controladores
direct/approximate/unsupported. Cinco referências de sprite seguem ausentes
nas ações 53 e 72. `geese_ir.json` registra `source_sha256` igual ao SHA do RAR;
nenhum asset derivado foi guardado.

`ffspRyoS.zip` permanece identificado como stage Gan-ryu Island, não personagem;
fica fora do corte atual de fundo sólido. O inventário ZIP/RAR lista Mai, Ryo,
Terry, o stage e Geese. O parser CLI também aceita o RAR.

No fechamento do lote, a suíte completa `mugen2sms/tests` ficou em 237 passed /
57 failed. O teste temporal legado foi alinhado ao campo atual `hitdef_events` e
passou; nenhuma falha restante atinge os testes de Source/expressões/inventário.
As 57 falhas restantes são 1 teste de build que depende de
`rom_asset_binding.json` e 56 de paridade que dependem de
`doacao_md_mugen2sms.json`; ambos retornam EIO no projeto. Não recuperei nem
recriei esses manifests.

Artefatos locais: `mugen_inventory.json`, `base_inventory.json`, `mai_ir.json`,
`mai_smsdev/` e `geese_ir.json`. Esses resultados
são parse/conversão estáticos. Não houve corte de luta, build/link, ROM ou sessão
QA privada: os documentos canônicos do projeto e `audio_provenance_manifest.json`
continuam retornando EIO. Portanto gameplay, FPS, áudio e orçamento em hardware
seguem `not_run`.
