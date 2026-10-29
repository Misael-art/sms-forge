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
