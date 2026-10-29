# Dr. Social — amostra CPS2 autoral v1

Estado: candidata distinta, autorizada pelo pedido de 2026-10-28. Escopo: uma
pose idle e `social_light_jab` J01–J06. Sem expansão do atlas ou promoção.

## Autoridades e conflito preservado

Identidade: model sheet CPS2-Alpha-Cel v4, SHA-256
`ddce2f5a302dd679610c1b0eb915ce10718a5df852f80e4a78af18db33426644`.
As decisões posteriores fixam cabelo exclusivamente cinza e óculos de latão.
Corpo humano esguio, casaco azul/ciano, colete separado, cravat bordô,
luvas claras, botas marrons e bengala completa permanecem invariantes.

A decisão `decisions/dr-social-animation-source-v08_2_owner_approval.json`
aprova a fonte exata de 61 poses em `res/approved_art/dr_social/`, SHA-256
`4e557095dcafd4f11a0369e6e993ad4fa99497ab529509dedd2445f83bcf89d8`.
O arquivo foi conferido. Memória, GDD, TDD e contrato v2 contêm afirmações
anteriores de aprovação pendente; essas afirmações estão superadas pela decisão
preservada. A reconciliação do registro conserva essa aprovação sem ampliar
seu escopo para conversão, animação contínua, composição ou orçamento.
O head genérico `animation_source/main` permanece sem aprovação representada:
seu kind admite caminhos em `data/source_art`, enquanto a decisão exata aponta
`res/approved_art`. Não foi inventado outro escopo de decisão para forçar esse
head. A decisão/hash explícitos continuam preservados na reconciliação.
A nova variante CPS2 não substitui a v08.2, não retoma a v02 bloqueada nem a
v07 rejeitada. A proibição de difusão no tratamento por máscaras da v08 não
se transfere a esta exploração generativa expressamente pedida pelo dono.

Limitação preexistente: `artifact_registry.py check --scan` interrompe no
relatório histórico ausente `out/diagnostics/dr_social_61_pose_review_v5/
conversion_report_61_pose_v5.json`. Não foi inventado ou refeito um relatório
histórico para aprovar a organização atual.

## Referência observada e receita selecionada

Ken: `../luta_mugem_rev2/data/derived/ken/ken8/ken.sff`, paleta `ken1.act`;
idle AIR 0: 66×94, 66×96, 64×98 e 66×93 px, pivôs aproximadamente no centro
da sola. AIR: seis entradas de seis ticks; quatro desenhos distintos.
Ataque de comparação: ação 250, grupo 230, cinco entradas 3/3/6/3/2 ticks.

Ryu: `../luta_mugem_rev2/data/derived/ryu/ryu/ryu.sff`, paleta `Ryu02.ACT`;
idle AIR 0: 64–66×93–98 px, seis entradas de cinco ticks e quatro desenhos.
Ataque 260: seis entradas 3/2/4/4/3/2 ticks; o último retorna ao grupo 220.
As paletas-fonte têm aproximadamente 15–16 índices opacos por desenho.
Índice lógico e RGB distinto são contagens diferentes.

Receita confrontada com `../luta_mugem_rev2/doc/28-pose-budget-8.md`:
`mugen2sms.converters.display_fit`, modo `pose_budget`, origem CPS2 384×224,
destino SMS 256×192, amostragem nearest de índices em dois passes:
framebuffer x=2/3, y=6/7, depois extra corporal 2/3 no piloto do par.
O piloto em `out/generated/pose_budget_pair_20261023/` conserva idles de
aproximadamente 32×56, até quatro células por scanline por ator. Não selecionar
o perfil histórico 40/49, `legacy_quarter` ou `fighter_scale` por nome/data.

Arte-fonte: clusters grandes, contorno escuro, volumes legíveis em cerca de
94 px. Conversão: sete cores por lutador no par reduzem detalhes/contorno;
o teste de reserva de preto foi considerado mais escuro pelo dono. Runtime:
a prova residente `698e58ed…` resolveu a fragmentação naquele quadro, mas
bloqueou dez papéis/25 poses largos; pior VBlank histórico derramou. Nenhuma
dessas propriedades constitui aprovação do novo Social ou do motor completo.
Ken/Ryu orientam construção e qualidade, nunca identidade, coreografia ou
pixels autorais. Seus arquivos permanecem referências privadas locais.

## Contrato observável da nova fonte

- Escala: corpo em guarda aproximadamente 100–108 px, cabeça ~14 px;
  Social mais ereto/esguio que os idles flexionados de Ken/Ryu. Cabeça, torso e
  pernas mantêm relação próxima de 7,5H; sem copiar sua massa muscular.
- Matriz de autoria proposta: célula lógica 128×128, margem transparente,
  baseline única e pivô fixo; essa é a fonte CPS2, não o canvas SMS.
- Contorno externo navy escuro de um pixel; divisões internas nas sobreposições.
  Diagonais em degraus intencionais; sem halo, blur, dithering ou confete.
- Luz superior esquerda. Planos sombra/base/luz contíguos; tecido azul com
  sombra teal/navy, pele quente, cabelo cinza frio, couro marrom e metal com
  reflexos pequenos. Óculos de latão separados do rosto; branco restrito às
  luvas/gola/haste. Fonte pode usar mais cores que a saída SMS.
- Ler ombro→cotovelo→punho→luva, separar lapela/colete/casaco e manter
  equipamento completo, fixo e sem recorte. Bengala romba, nunca lâmina;
  rapieira e bumerangue guardados não geram efeitos neste normal.
- Idle é uma única pose. Jab: J01 guarda; J02 carga curta; J03 extensão;
  J04 contato; J05 recolha com follow-through; J06 guarda recuperada.
  Durações propostas: 2/1/1/1/1/3 ticks, nove ticks por ação, sem deslocar
  o centro de massa. Não aumentar desenhos para esconder inconsistência.
- Geração grande só é matéria-prima. Inspecionar grade, alpha e cores reais;
  a exportação nativa exige revisão artística própria. Redução e quantização
  não demonstram acabamento. Aprovação fica pendente por hash/etapa.

## Evidência e continuidade

Inventário das referências e derivados do lote:
`out/diagnostics/dr_social_cps2_sample_v1/`.
Fontes candidatas: `data/source_art/sprite_studies/dr_social/review_drafts/
cps2_sample_v1/`. Reserva no registro central para `cps2-idle` e
`cps2-light-jab`, pais no model sheet v4. Prompts, originais e transformação
devem permanecer recuperáveis. Conversão preliminar expressamente autorizada
é diagnóstico; não promove arte, recurso ou gameplay.

## Fechamento da amostra revisável

**Resultado: candidata produzida, convertida, buildada e observada em ROM.
Revisão artística: `revise_before_growth`; nenhuma promoção.**

Fonte atual: `jab_revision_v3/jab_source.png` na pasta candidata acima,
384×256, seis células 128×128, SHA
`04d210857352d952be51109713cc5eadcd2212e4f38668cfba76a57337744872`.
O idle é a cópia exata de J01 em `idle_source_v3.png`, não outro desenho nem
um ciclo de idle. PNG fonte usa 30 RGBs próprios e transparência binária;
`audit_source_raster.py` mediu 31 RGBs contando o fundo e zero alpha parcial.
Os originais, prompts e tentativas anteriores permanecem preservados.

A v1 perdeu os óculos/cinza na extração e abriu demasiado o casaco. V2 conteve
as abas e fixou a paleta-fonte por material. V3 corrigiu J03/J04 e registrou
cada desenho pela sola/pivô, mantendo uma única escala 104/474 para a folha.
Isso corrige posicionamento na folha, sem redimensionar poses individualmente.
Não é prova semântica independente: a revisão visual permanece responsável
pela anatomia, materiais, equipamentos e leitura da ação.

Derivação final: `out/diagnostics/dr_social_cps2_sample_v1/converted_tall_v5/`.
O sufixo v5 é tentativa de conversão, não revisão artística: as passagens 8×8
foram preservadas como falhas de representação; a final reutiliza o formato
tall 8×16 da referência. Os oito PNGs SMS passam recursos, os sete pares
Social/Ken passam o simulador com **31 SAT, pico 8, zero overflow**.
Pool residente: **212 padrões/6.784 B** na primeira metade de VRAM; nenhuma
pose depende de streaming. P1 tem 15 cores úteis comuns; fundo sólido usa P0.
Este inventário não inclui cenário/HUD/efeitos nem fecha o jogo completo.

ROM base: `out/candidates/dr_social_cps2_sample_v1/rom/master_of_fighters.sms`,
32.768 B, SHA
`f5d54b1545aa20ec41ec7da0290b2c948aeec393c025d71c2401254b58458b8d`.
`doc/rom_asset_binding.json` e o recibo do build ligam fonte, PNG SMS, símbolos,
header e ROM. SHA de `src/main.c` e header atual conferem com os inputs do
build. O consumidor nominal continua sem selecionar a candidata.

### Evidência real e limites

- Sessão de timeline `cc48e3714aeb4a529b931d98f10e283b`, encerrada: PNGs,
  leituras SMRT e vídeo nativo de 120 frames. Todos os framebuffers da janela
  combinam exatamente com os templates SMS. A pose submetida em 0xC7F6 aparece
  no framebuffer capturado seguinte. J02–J06 mostram holds 1/1/1/1/3; os dois
  ticks de J01 estão no traço da ROM, mas idle/J01 têm os mesmos pixels e não
  se distinguem só por RGB. Não promover esse caso a observação visual de IDs
  diferentes. O vídeo por stepping não mede throughput nem fluidez percebida.
- As janelas curtas deram 58,8/59,23 e falharam o alvo. Sessão nova de runtime
  `5cafeaab2fe445139578ed56f34c5488`, encerrada: janelas de oito segundos deram
  **59,43/59,56 fps**, dentro do alvo NTSC do instrumento. São taxas de janela,
  sem alegação de jitter/latência de input ou qualificação PAL.
- Mesmo binário, janela autônoma de 3.000 frames: `measure_worst_frame.py`
  passou com `vovf_delta=0`, selo `vline_min=207`. Degrau de +128 B por VBlank,
  ROM SHA `db7afa1e93e3b22f50b2d0bb38401295d5d736657223ce60707e9790a2b76fe7`,
  sessão `81f05d02bc9344d4a9fa34905ccbb7b4` encerrada: zero derrames,
  `vline_min=217`. Não converter esses snapshots em duração CPU ou capacidade
  máxima de streaming. JSONs e cleanup estão em `performance_sessions.json`
  e nos diretórios de evidência do owner.
- QA nativa independente: `/root/social_runtime_qa`, sessão
  `3623427cdfc54426af25979c2c42af07`, encerrada. **1/1 caso passou**, 120
  framebuffers coincidiram com PNGs esperados; seis desenhos e Ken íntegro.
  Pedido e relatório ficam em `independent_qa/` dentro do diagnóstico.
  `audit_subagent_session.py --require-passed` passou, teto `assigned_checks_only`.
- Os três bundles do coordenador passaram `check-bundle`. No primeiro, a INI
  de captura foi recuperada dos bytes exatos do launcher após o shutdown
  regravar a INI viva; SHA original conferido, sem alterar o recibo da captura.
  O registro `configuration_recovery.json` conserva essa recuperação.

Self-checks passaram antes das leituras. Seis testes do adaptador passaram,
incluindo preto opaco, hash errado, registro nativo, paleta comum e par largo
reprovado sem omitir células. Também passaram marcadores, corredor, tilemap,
mirror, scroll, tamanho de símbolo, contrato de animação e semântica do jab.
O gate de semântica não foi aplicado ao idle como ciclo: ele é uma pose estática.

### Julgamento artístico e próximo delta

Os relatórios reais estão em
`dr_social_cps2_sample_independent_review_v1.json` e
`dr_social_cps2_sample_independent_review_v2.json`. O segundo confirma a melhora
do cabelo cinza, abas e cotovelo de J03, mas pede revisar a estabilidade dos
óculos/assinatura facial e tornar o contato J04 mais inequívoco. Não se exige
mostrar a lente distante quando o perfil a oclui. A conversão SMS perde ainda
mais rosto e separação lapela/colete. O checklist v3 bloqueia promoção com
eixos em fail/pending e aprovação do dono ausente; isso é resultado esperado,
não um gate técnico desativado. O objetivo de acabamento de referência ainda
não está pago. Não expandir atlas/personagens/movimentos.

Comparativos de identidade/escala, fonte e SMS nativos/ampliados:
`comparison_idle.png`, `comparison_jab.png`. Reprodução nominal e lenta:
`jab_comparison.apng`, `jab_comparison_slow.apng`. Evidência da ROM:
`live_timeline/social_jab.mp4`. Todos ficam no diagnóstico do owner; as
comparações com Ken/Ryu não são publicadas no Git de fontes.

Próximo passo: refino artístico localizado de rosto/óculos e contato, nova
revisão hash-bound antes de crescer/promover. Não tentar resolver esses eixos
por recolorações/filtros sucessivos ou por afrouxar máscaras. Áudio novo,
colisão, dano, balanceamento, cenário/HUD e gameplay não fazem parte desta ROM.

### Reprodução sem outro consumidor

Os PNGs autorais nativos e as receitas ficam no Git. A referência privada do
Ken é exportada do SFF já restaurado pelo bootstrap; não baixar outro pacote.
Exemplo a partir da raiz, antes de preparar os dados em um host limpo:

```sh
rtk proxy tools/sms_wrapper/run_host.sh python - <<'PY'
from pathlib import Path
import sys, hashlib
sys.path.insert(0, 'tools/sms_wrapper')
from mugen2sms.parsers import sff
d = Path('SMS_projects/luta_mugem_rev2/data/derived/ken/ken8')
blob = (d / 'ken.sff').read_bytes()
assert hashlib.sha256(blob).hexdigest() == '911e21b778af3e7a93cd69fe6132b8e87fb1cacddac757ada5842a8cb1c2172c'
sprites, _ = sff.parse(blob)
sprite = next(s for s in sprites if (s.group, s.image) == (0, 0))
palette = sff.read_act((d / 'ken1.act').read_bytes())
out = Path('SMS_projects/master_of_fighters/out/diagnostics/dr_social_cps2_sample_v1')
out.mkdir(parents=True, exist_ok=True)
target = out / 'ken_a0_g0_i0.png'
if target.exists():
    raise SystemExit('preservando referencia existente')
sff.to_image(sprite, palette).save(target, transparency=0)
PY
rtk proxy tools/sms_wrapper/run_host.sh python tools/sms_wrapper/prepare_authored_sprite_sample.py --self-check
rtk proxy tools/sms_wrapper/run_host.sh python tools/sms_wrapper/prepare_authored_sprite_sample.py --config SMS_projects/master_of_fighters/.mddev/dr_social_cps2_sample_v3.json --out SMS_projects/master_of_fighters/out/diagnostics/dr_social_cps2_sample_v1/converted_tall_v5
```

Usar `build_inner.py --project` com caminho absoluto do owner, `--manifest`
absoluto de `.mddev/dr_social_cps2_sample_build.json` e `--build-dir` novo sob
`out/candidates/`. Não sobrescrever recibos/ROMs existentes. A extração dos
originais é opcional para replay e usa `--extract-config` com a receita da
revisão correspondente; não reexecutar sobre fonte selada. Um rebuild em
outro SDK/host exige identificação e QA próprias. O áudio da amostra é
intencionalmente silencioso, sem aprovação do eixo musical.

## Aprovação do método e encaminhamento — 2026-10-29

O proprietário declarou: “APROVADO O METODO REGISTRE PARA CURADORIA FUTURA E
VAMOS PARA O PROXIMO PASSO”. O registro canônico deste encaminhamento é
`curation_candidates/2026-10-29_dr_social_cps2_source_to_rom_method.json`:
contém receita, evidências com hashes, medidas e questões para o curador.
O método está aprovado para continuidade do projeto; a curadoria global é
futura. Não há novo ID, regra ou gate promovido neste registro.

A aprovação tem escopo de método. O parecer artístico v2 e o checklist v3
continuam íntegros; o próximo passo operacional é corrigir localmente a
assinatura dos óculos e a leitura de contato J04, com fonte e revisão próprias.
Nenhum PNG, ROM ou evidência da amostra selada foi sobrescrito por este registro.

## Próximo passo executado — reparo facial v5 e nova ROM, 2026-10-29

A aprovação do método está no registro de curadoria futura acima. A amostra
atual para revisão é **v5**, sem ampliação de atlas, estados ou frame-data.
Fonte: `jab_revision_v5/jab_source.png`, SHA
`44ae0342e9db909d467907c1c21633165f5ee8dd1034b90d596d38498abd9c05`.
Idle é a cópia exata de J01 em `idle_source_v5.png`.

| Tentativa | Delta e resultado |
|---|---|
| v4 | Reparo facial solicitado no raster grande; óculos não fecharam no nativo. Parecer v4 `revise_before_growth`; não selecionada. |
| v5 | Entrada: matriz nativa v3 ampliada4× por nearest, extração1/4 alinhada. Parecer v5 passou o reparo facial nos seis rostos, sem regressão corporal material; não aprova a sequência inteira. |
| v6 | Tentou alinhar o contato J04, mas alongou o alcance. Conversor reprovou J04 com33SAT/pico9; não foi buildada. |
| v7 | Tentativa compacta preservada, ainda com articulação de contato insuficiente na inspeção do produtor; não selecionada. |

Os quatro originais e prompts foram produzidos com `imagegen` integrado e
preservados em `jab_revision_v4/` a `jab_revision_v7/`. A geração não preservou
pixels estritamente fora da face: deltas por quadro registram as mudanças.
Não chamar a passagem de edição pixel-local nem a extração de polimento final.
Os checklists v4/v5 são inputs congelados anteriores aos pareceres; seus hashes
continuam exatos nos pedidos. O resultado independente facial v5 está no parecer
separado `dr_social_cps2_sample_independent_review_v5.json`.

A v5 usa a mesma paleta-fonte30, grade384×256, células128×128, seis poses e
2/1/1/1/1/3ticks propostos. Conversão: `.mddev/dr_social_cps2_sample_v5.json`
→ `face_revision_v5/converted/` no diagnóstico. Mesma receita SMS, extra4/6
escolhida pelo idle;216 padrões/6.912B,31SAT salvo J04=32, pico8 nos sete pares.
Corpo não foi encolhido para caber em J04; a tentativa larga foi reprovada.

No consumidor existente, `MOF_CPS2_SAMPLE=5` seleciona somente o header novo;
valor1 preserva a baseline anterior. Não há outro consumidor ou lógica de build
no projeto. Manifestos de build: `.mddev/dr_social_cps2_face_v5_build.json` e
`dr_social_cps2_face_v5_stress_build.json`; gerar por `build_inner.py` em destino
novo. A receita de extração v5 é1/4 do nativo ampliado, diferente de104/474 usado
na v3. Ela é tentativa observada neste caso, não regra global homologada.

ROM v5: `out/candidates/dr_social_cps2_face_v5/rom/master_of_fighters.sms`,
32.768B, SHA
`fc46d77b9fea6ffd63c262aa085de3e1e623409c1db3e706e163d9d2439cf24b`.
Stress128: `out/candidates/dr_social_cps2_face_v5_stress128/rom/master_of_fighters.sms`,
SHA `a5c013a83d9d4e8678fa71d832d9fcedffed6a9cd77937389328f849a00edde7`.
Binding canônico atualizado para v5; a baseline v3 e seus recibos permanecem
intactos, com código original no commit `ba706e8`.

QA nativa `/root/social_runtime_qa`, sessão `b2f3d33e89d84c9f8c68e089eacb6059`,
encerrada:1/1 caso e120/120 framebuffers exatos; seis checks de fidelidade.
Pedido/relatório/vídeo em `face_revision_v5/independent_qa/`; vídeo real
`run_3b757b7927b247dcb2f70a2a73894c39/case_0.mp4`. Seis desenhos e Ken íntegro
observados, mas sem afirmar fluidez percebida. Óculos se comprimem num pequeno
agrupamento latão/escuro; lapela/colete ainda perdem definição. Não exigir dois
aros completos em perfil nem tratar perda de detalhe como automaticamente aceita.

Sessão performance `93578b87ccbe4375931aec912dc9cd8d`: duas janelas8s,
59,62/59,79fps NTSC; janela autônoma3000frames sem derrame, `vline_min=207`.
Sessão stress `c3161d84042a4bda9367fa521597b810`: mesmo tamanho de janela,
zero derrames, `vline_min=217`, transferindo128B adicionais por VBlank. Ambas
encerradas; bundles verificados. `performance_sessions.json` conserva números,
ROMs, carga do host e cleanup. FPS paga somente médias das janelas, não jitter,
latência, game feel ou PAL. Os outros campos do layout genérico SMRT não são
semântica de combate desta ROM; foram usados magic/schema/contador de frames.

Self-checks passaram antes das leituras; seis testes do adaptador e gates de
recursos, sete composições, debug, corredor, sprite mode, tilemap, semântica,
contrato, binding e QA passaram. Checklist v5 retorna pending(código2), com
cobertura íntegra, sem aprovação do dono; não é FAIL técnico nem promoção.
Auditoria global do registro continua bloqueada pelo relatório histórico v5
ausente, já identificado. Não foi preenchido retroativamente.

Comparação de fonte/SMS em1× e nearest: `face_revision_v5/source_sms_comparison.png`.
Comparação facial com baseline: `source_and_faces_comparison.png`. Animação
nominal/lenta: `jab_source_v5_60hz.apng` e `jab_source_v5_slow.apng`.
Próximo checkpoint: julgamento temporal do contato compacto na mídia nova e
aceite explícito das simplificações do rosto/roupa na escala SMS, antes de
ampliar conteúdo ou promover. A v08.2 segue aprovada no seu próprio escopo.

## Amostra v8 — contato legível e grade compensada, 2026-10-29

**Estado corrente da amostra: v8, seis quadros.** A fonte61poses v08.2 aprovada
continua intacta e em outro papel. A v8 não foi escolhida por número/data:
resolve uma causa específica do bloqueio do contato, sem nova geração artística.

Fonte `jab_revision_v8/jab_source.png`, SHA
`877f6e5b232b542f29b0d5794026fe3894d469beee6c47c02e9520d5c976ae41`.
`assembly_recipe.json` prova a montagem indexada sem transformar pixels:
J01/J02/J03/J05/J06 são cópias exatas da v5; J04 é a cópia exata do contato reto
já autorado na v6. Paleta, alpha, escala e pivôs não mudam. Idle permanece o
J01/v5, idêntico ao J01/v8. Os prompts/originais de Imagegen continuam nos pais
v5/v6; não houve Imagegen novo, pintura por código ou novo movimento neste lote.

### Causa e implementação

A grade8×16 original une partes de linhas opacas diferentes dentro dos mesmos
intervalos SAT e mede5células no J04, mais4do Ken. Um deslocamento da **grade**
por(3,9)px, compensado no META, muda esses intervalos, conservando cada pixel.
O adaptador oficial ganhou `packing_phase_px` opcional por pose, default[0,0].
Ele acrescenta só transparência antes de chamar `to_sms_pose`, `pack_tiles_tall`,
`build_frames` e o compactor existentes, e retira o mesmo deslocamento da
posição META. Não há outro conversor, consumidor ou redução de corpo/ataque.

O controle `.mddev/dr_social_cps2_sample_v8_grid0_control.json` usa as mesmas
fontes, escala, pivôs e paleta da configuração ativa, mudando apenas essa grade.
**Todos os oito PNGs SMS são byte-idênticos entre controle e candidata.**
J04: pico9→8, SAT33→34; pool218→220padrões. Controle reprovado e não buildado;
fontes v6/v7 e ROMs antigas continuam intactas. `phase_comparison.json` conserva
esses controles. A troca custa mais SAT/patterns totais, não oculta esse custo.

O emissor da amostra soma offsets unsigned antes de `SMS_addSprite`. O header
SDK declara Y de16bits com checks; -4 codificado como252 somaria324, não68.
O adaptador recusa fases que exijam offsets relativos negativos/incompatíveis;
a v8 usa só offsets não negativos. Não se alterou o emissor medido. Self-check
decodifica os pixels em128fases do packer; nove testes cobrem preto opaco,
reprodução exata, defaults idênticos, largura realmente impossível e essa
recusa. Defaults da v5 reproduzem o header e PNGs antigos byte a byte. Replay
com o guard final também refaz todos os dados v8 ligados no build sem diferença.

### Fonte e referência

O parecer `dr_social_cps2_sample_independent_review_v8.json` passou os13eixos
integrais da fonte/chaves estáticas: J03 dobrado, J04 estendido inequívoco e
J05 recolhido; identidade, óculos, biotipo, materiais, bengala e apoios coesos.
Isso não é aprovação de playback contínuo, SMS pelo dono ou produção/AAA.
O checklist de entrada v8 permanece congelado. O resumo posterior
`dr_social_cps2_sample_art_checklist_v8_reviewed.json` referencia esse parecer,
com aceites temporal/SMS e dono pendentes, bloqueando promoção.

Receita de referência continua a escolhida em `luta_mugem_rev2/doc/28-pose-budget-8.md`:
fontes Ken `ken8/ken.sff` e Ryu `ryu/ryu.sff`, ACTs `ken1`/`Ryu02`, idles
exportados66×94 neste comparativo. Social tem corpo~104px em célula128×128,
com postura mais ereta/esguia. Mesma direção de contorno/plano de materiais;
identidade/pixels não são copiados. SMS: framebuffer x2/3,y6/7 e extra corporal
4/6=2/3 derivada só do idle. `comparison_identity.png` mostra modelv4, Ken/Ryu,
fonte e SMS, em nativo/nearest. Hashes e papéis em `reference_comparison.json`.
Essas comparações privadas não são publicadas no Git.

### Nova ROM e observação

Seleção `MOF_CPS2_SAMPLE=8` no mesmo consumidor;5e1 preservam dados anteriores.
Receita `.mddev/dr_social_cps2_sample_v8.json`; manifestos de build
`dr_social_cps2_contact_v8_build.json` e `dr_social_cps2_contact_v8_stress_build.json`.
ROM `out/candidates/dr_social_cps2_contact_v8/rom/master_of_fighters.sms`,32.768B,
SHA `452cd56594db3764da4b3d1c61e8e5f2e9d66714907b2edd3fbc453da3be240f`.
220padrões/7.040B residentes;31SAT nas outras poses e34no J04, pico8 em todos
os sete pares. Mesma P1 de15cores, layoutVRAM e setup com display desligado;
somente SAT por tick na ROM base. Binding atual cobre Social e referência Ken.

QA nativa `/root/social_runtime_qa`, sessão `80cebe97316e468bbbcc2eec8ddac9fd`,
encerrada:1/1caso,120/120framebuffers exatos e sete checks individuais, incluindo
Ken na composição do contato. Braço/punho/luvaJ04 íntegros e recuperação sem
resíduos. Vídeo real `independent_qa/run_fd39fc88eedc423fa155b9442bad5e23/case_0.mp4`.
`transition_with_reference.png` mostra a transição; relatórios/gate preservados.

Sessão performance `b3bc1620274a4f1faf3752275b533299`,encerrada: SMRT em8s,
59,62/59,74fpsNTSC; janela autônoma3000frames0derrame, mínimo207. Stress128B,
ROM SHA `7ce342bcd35bc8d89d75d6583fcf9bee6cacfea023683d0085769d7135a188ea`,
sessão `8905b516d2f445f8a8f15bd8adb30848`,encerrada:0derrame, mínimo217.
Não há claim de capacidade máxima, duraçãoCPU, jitter, PAL, áudio ou gameplay.

### Timing observado, separado da percepção

A primeira coleta de input após performance encontrou `probe_keys=0` no ponto
de2VDP, apesar do ACK32, e foi preservada como cobertura falha em `timing/` e
`performance_sessions.json`. Não se corrigiu SDK/ABI por hipótese: a ROM viva
retorna KeysStatus emDE e o ISR atualiza o cache. A sessão controlada seguinte
lê o cache e o probe a cadaVDP e demonstra consumo; não se afirma causa exclusiva
para a amostra anterior nem se transforma espera extra em prazo de gameplay.

Sessão `b80042e52b4847d8a678693a7eee819e`,encerrada: traço/provas em
`timing_observed_input/`. Após controle explícito de autoplay e baseline idle,
uma pressão de Button1 produz J01..J06 e recuperação. 13casos de RAM/journal
passaram em `audit_observed_cases.py` com anchors reais de input. O registrov1
foi recusado por usar deadline entre reads; o registrov2 corrige apenas a forma
do contrato da ferramenta, sem mudar bytes, sessão ou expectativas do golpe.
Ambos ficam preservados; nenhum gate foi modificado ou afrouxado.

Ordem submetida observada:1h0,1h1,2h0,3h0,4h0,5h0,6h0,6h1,6h2,0h0.
Assim, os holds2/1/1/1/1/3 ocorrem na ROM. Os21framebuffers conferem com os
PNGs e mostram lag1VDP da submissão à apresentação. J02–J06 têm exposição
RGB1/1/1/1/3; idle/J01 iguais dependem também do probe, não distinguem IDs por
cor. Pontos nativos, ACKs e controles permitem rederivação; stepping não mede
FPS nem certifica fluidez percebida. Todas as quatro sessões do lote fecharam.

### Entrega revisável

Em `contact_grid_v8/`: `comparison_identity.png`, `comparison_jab.png`,
`contact_before_after.png`, `jab_isolated_9ticks.apng`,
`jab_runtime_cycle_30ticks.apng` (21idle+9ação), `jab_slow.apng`, conversão,
ROMs/recibos via paths do build, QA e probes. As durações APNG emms arredondam;
a prova de prazo vem da ROM, não do arquivo animado.
Óculos/rosto e lapela/colete simplificam no tamanho SMS. A revisão independente
considerou isso oportunidade de julgamento na escala real, não defeito fonte
bloqueante. Permanecem aceite humano temporal/SMS e promoção por etapa; não
expandir atlas/moveset antes do checkpoint. Não houve certificaçãoAAA ou
integração de produção. Fontes/receitas entram no Git; pacote e recibo local de
recuperação são identificados em `archive_receipt.json`, sem promessa de backup
em outro host ou release de produto.
