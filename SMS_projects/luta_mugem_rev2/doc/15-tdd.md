# TDD — luta_mugem_rev2

## Seleção e limites atuais — 2026-10-27

`LUTA_CONTACT_TRACE=1` registra no instante do contato, em um buffer `DATA`
identificado pelo `.map`, os frames lógicos e usados, poses residentes,
última submissão, facing e coordenadas. A sequência de publicação é par
quando completa e ímpar durante escrita; o leitor deve limitar a janela para
excluir wrap e tratar eventos múltiplos como ambíguos. A instrumentação custa
CPU e seus resultados não qualificam prazo nem provam o framebuffer.

No perfil de produção, `LUTA_PRESENT_HIT` fica ligado. O combate roda depois
de montar a sombra da SAT e só aceita o quadro submetido por inteiro, com a
âncora e a face dessa sombra, se o papel ainda for o atual. O cursor lógico
pode estar adiante e não aplica dano. Isso elimina pose futura invisível;
não prova scanout, limite de scanline nem que o quadro ativo chegou a tempo.
`probe_present_hits` conta contatos aceitos; `probe_present_unready` conta
atacantes pulados porque a submissão ou o papel não conferiam.
`LUTA_CONTACT_GUARD`, `LUTA_CONTACT_SAT` e o ator BG desligam esse caminho.

No schema 7 de `fight_runtime_data.h`, cada golpe carrega `pausetime` dos
dois lados e os tempos `ground.hittime`, `guard.hittime` e `air.hittime`
do primeiro HitDef do estado fonte. O pause congela os dois atores e
segura o pusher de corpo. O recover do defensor só conta depois do pause
dele: sem papel novo e sem velocidade de andar; a gravidade continua.
`guard.hittime` ausente copia `ground.hittime`. Não há sprite de dano nem
knockdown: common1 está fora do perfil, a pose atual permanece, e um papel
sem controle volta ao idle no chão ao fim do recover. Trip/fall da fonte
não vira queda. Um comando que casa durante o pause ou o recover é
consumido e não fica bufferizado. Schema 5 mantém o hitstop único do
personagem.

No schema 7, um acerto invalida a instância de ataque da vítima mesmo que a
pose anterior permaneça visível; uma nova instância exige mudança de papel.
O combate captura elegibilidade dos dois atores antes de resolver os contatos,
permitindo troca não letal no mesmo tick quando ambas as interseções são
encontradas. No caminho de pose submetida, as âncoras usadas são as da mesma
sombra da SAT; outros perfis não têm essa garantia. Para pausas concorrentes,
cada ator conserva o maior tempo solicitado. O loop ainda resolve P1 antes
de P2 e um KO impede o segundo contato: KO simultâneo e empate continuam sem
implementação qualificada. Essa política é aproximação, não equivalência CNS ou prova de que
as duas poses chegaram ao scanout. Os testes host cobrem interrupção após
pause/recover, ambos os lados e pausas assimétricas. Na ROM observou-se P1
atingido enquanto atacava, com a instância invalidada e recover; o caso
espelhado, as caixas futuras e a apresentação do contato continuam pendentes.

Na ROM histórica `7f530db3…` o pause 16 e o recover 21 do HP de Ryu
foram contados em stepping; a amostra do framebuffer é o topo do laço
seguinte (`probe_frame` 53, tick 52, pause ainda 16). Nesse HitDef
`guardtime` e `hittime` valem ambos 21, então a duração não separa
guarda e acerto. A guarda dessa ROM foi capturada depois, na sessão
`ff3ce3ec…`: kind 1, vidas inalteradas, recover 21, impulso único de
`guard_push` 5 px. A duração continua igual à do acerto; kind e vida
separam os eventos. Ver memory bank. Isso não fecha R06.

Duas políticas são candidatas, ambas zero por padrão e incompatíveis entre si.
`LUTA_CONTACT_GUARD` recusa e conta uma interseção lógica se os frames,
facing, patterns e posições não correspondem à última preparação cuja cópia
da SAT retornou. A lógica continua avançando, portanto o contato pode ser
perdido. `LUTA_CONTACT_SAT` compara caixas e coordenadas dessa última cópia,
desde que o residente continue vinculado à instância atual do papel; isso
altera o instante e, possivelmente, as caixas em relação à fonte. Mudança de
papel invalida o vínculo e novas requisições/publicações o restabelecem.
Ambas exigem trace e renderer sprite-only, recusam células cortadas ou
rejeitadas e não provam scanout nem ausência de perda por scanline. Não são
soluções aprovadas: os casos medidos e perdas ficam no memory bank.

`LUTA_DIAG_PSG=1` é uma carga de teste, desligada por padrão. Contato e
guarda reais enfileiram streams autorais genéricos (`sfx_hit`, canais 2+3;
`sfx_hurt`, canal 3); não são adaptação ou identidade sonora MUGEN. No mesmo
tick, acerto prevalece sobre guarda; guarda não interrompe acerto ainda ativo,
e acerto pode interromper o SFX em curso. Eventos excedentes são coalescidos;
guardas descartadas são contadas em u8. `PSGSFXFrame` roda uma vez por tick,
após SAT e antes do selo de VBlank. Não existe música, retomada de canal de
música, pause de jogo, KO ou transição sonora qualificada nessa opção.

As sondas de quantidade e primeiro tick de reprodução são u16 e exigem limite
de janela para excluir wrap; a entrada no PSG não prova som audível. Elas usam
`C8E5..C8E8`, fora do cabeçalho SMRT de cinco bytes e dos offsets do worst-frame;
`C8D0..C8D6` continuam reservados ao contrato de medição. Um teste compara os
endereços de áudio com os offsets publicados dos medidores. O teste de sinal,
a instrumentação e seus custos/limites por ROM estão no memory bank.

O renderer híbrido é uma experiência isolada, desligada por padrão
(`LUTA_BG_ACTOR=0`, `LUTA_BG_CAMERA=0`). Com BG habilitado, P1 referencia na
PNT os mesmos patterns de sua pose residente, com a paleta P1 e prioridade
de BG; P2 continua na SAT. Uma sombra de 8×10 tiles é atualizada antes do
streaming em VBlank. A PNT usa as 28 linhas do modo 192, o scroll Y é reduzido
em 224 e a primeira coluna fica mascarada pela exigência de scroll horizontal.
Não se reivindicam sobras da PNT inferior ou da SAT. O plano e os registradores
amostrados estão no memory bank; não incluem HUD, FX ou a composição completa.

A câmera experimental aplica o mesmo deslocamento horizontal aos dois
atores quando suas caixas residentes cabem fora da coluna mascarada. Quando
não cabem, registra conflito e mantém deslocamento zero; isso pode cortar
pixels. A escolha da câmera não foi aprovada para produto. Tampouco foram
qualificados facing, sobreposição, restauração, deadline ou HUD. A sonda de
apresentação de P1 fica sem valor afirmativo em BG: preparar a PNT não prova
o framebuffer. O teto de cor, as flags de prioridade/paleta e o orçamento de
VRAM são os do VDP/SMSlib, sem uma paleta independente por lutador.

O GDD vigente declara `pose_budget`: encaixe do framebuffer X 2/3 e Y 6/7,
escala extra 2/3 uniforme e idle de até quatro colunas de 8 px. A faixa
histórica de 72–88 px é outra opção, não o requisito deste consumidor. O
contrato de qualidade vincula esse perfil ao SHA do GDD; o auditor verifica
estrutura e vínculo, não fidelidade de pixels ou aprovação de arte.

O manifesto nominal agora seleciona `pose_budget_facing_20261027` (24 bancos),
regenerado do corte já previsto no GDD; a seleção anterior `ryu_ken_cross` de
49 bancos permanece como histórico. O header antigo de 49 bancos aponta P2
para outra convenção de face e o runtime atual o rejeita na compilação. Builds
de candidato gravam recibo/ROM em `out/candidates/` sem tocar a baseline. A
receita histórica de 24 bancos está em
`.mddev/candidates/pose_budget_pair_20261027.json`.
O comparativo de padding anterior está em
`.mddev/candidates/pose_budget_pair_power2_20261027.json`. Ambas as receitas
históricas apontam para o header antigo sem o contrato de faces; o fonte atual
as recusa e elas exigem o snapshot de fonte associado ao recibo histórico.

O manifesto nominal pede `makesms -pp`: na comparação controlada em BlastEm,
uma imagem de 28 bancos acessou dados de bancos diferentes e a mesma imagem
preenchida a 32 eliminou a divergência nos 14 spans observados. Isso não prova
mapper físico. O corte de 24 bancos foi exercitado com o mesmo runtime, sem o
bloqueio histórico dos dez papéis. Dois atores em um quadro não aprovam
composição, comandos ou budget: os picos por scanline e o derrame continuam.

O tile vazio do fundo ocupa o pattern 256 em `0x2000`; o pool de sprites usa
`0x0000..0x1FFF`. O cancelamento de uma pose em voo quando se volta à pose
residente foi observado em uma transição na ROM `9654406b…`. A lógica de
combate ainda calcula contato a partir do frame desejado antes da publicação;
o cache corrigido não resolve a coerência pose/colisão. Escopo de medições,
SHAs e lacunas estão no memory bank; seções abaixo preservam medições históricas.
Cada alocação ou liberação do pool invalida explicitamente o memo de falha dos
dois lados, sem contador de geração sujeito a wrap de 8 bits. Transferências
contíguas agrupam no máximo três pares de 64 B por chamada da API de tamanho
byte; o budget por lado e a promoção após completar a pose permanecem. A
implementação e seu custo não aprovam o orçamento: os candidatos medidos
continuam derramando e a carga de entrega não está presente.

O cache agora distingue `(pose, face)`: P1 usa patterns/meta P1 direita ou
esquerda e P2 usa patterns/meta P2 direita ou esquerda, sempre da paleta
compartilhada. As duas faces adjacentes devem caber no mesmo banco de 16 KiB;
descritor inválido cancela o upload pendente e é contado. A origem usa a face
residente enquanto a nova face sobe; lógica/contato ainda podem estar adiante
da imagem. Sondas de orientação desejada, residente e submetida não são prova
de apresentação completa na SAT. Ao modelar filas em `commit_budget.py`, a
chave fornecida precisa distinguir as duas faces.

O input da IA usa cursor sequencial de beat/subframe, inicializado no boot e
avançado uma vez por tick da ROM; a consulta pura por frame continua para
acesso aleatório. Ao voltar de 65535 para 0, o cursor reinicia junto do frame.
O teste C cobriu a volta completa; a medição da ROM candidata ainda reprova
FPS e VBlank, conforme o memory bank.

O relógio da janela de pacing também usa quociente/resto sequenciais em vez
de divisão no caminho quente, inicializados no boot e reiniciados junto do
frame u16. Em 150 ticks a sonda avança uma unidade; `probe_b_step` satura em
255. A volta de 65535 foi testada no host e observada em ROM por stepping;
os selos de FPS e VBlank seguem reprovados.

`LUTA_SPECULATIVE_PREFETCH` é uma opção experimental desativada por padrão.
Ela reserva a próxima pose AIR no `pending`, sem publicá-la até o pedido
efetivo; pedidos urgentes têm prioridade de banda e podem recuperar reserva
especulativa do outro lado, sem evicção dos residentes. O recurso só prevê a
próxima entrada da animação corrente e não impede contato com pose visual
antiga. As sondas u16 de reserva, acerto completo e descarte são diagnósticas
e envolvem em 65536; não qualificam orçamento. As medições por SHA e as
falhas de FPS, VBlank e scanline estão no memory bank.

O pusher no chão usa a soma das larguras `ground.front` convertidas nos dados
de cada slot e preserva a ordem anterior ao movimento; não usa mais hurtbox
com afastamento fixo de 1 px. `ground.front` e `ground.back` são campos de
largura no [tutorial oficial MUGEN](https://elecbyte.com/mugendocs-11b1/tutorial3.html).
A implementação é aproximação: ainda não executa `Width`/`PlayerPush`,
largura traseira ou push no ar. Geometria inválida é contada e não é
substituída por constante. A cobertura da ROM é limitada aos roteiros do
memory bank; pusher e facing não qualificam toda a física ou o combate.

`LUTA_UPLOAD_TRACE=1` habilita somente em candidato o anel diagnóstico de
8 registros com frame e pares efetivamente copiados por lado; o seq é
publicado depois do registro. A leitura exige limite menor que o anel e
auditoria aritmética do contador. Como as gravações ocorrem no VBlank, a ROM
instrumentada não valida o budget da ROM sem sonda. Quotas de 1, 2 e 4 pares
reprovaram no selo e aumentaram a espera de pose no roteiro observado; não
foram promovidas. O valor nominal continua 8, também reprovado em VBlank.

## Arquitetura proposta, não implementada
PacoteMUGEN imutável→parse→IRtipado→perfilcompat→loweringAOT/tabelas
com predicados executáveis→runtimeC/Z80→ROMmedida. Reusar parsers/testes
SMSsaudáveis; doMD portar semântica/método e testes, não ABI/runtimeM68K.
FSM12papéis atual só baseline/exercício, sem chamarCNScompleto.

DecisãoCNS: priorizar subconjunto AOT de estados/triggers/controllers
alcançáveis nos movimentosKen/Ryu, predicados preservados emruntime. Comparar
comVMcompacta apenas se custo/ROM/banking justificar. Não exigirVMuniversal
antes do primeiro slice, nem expandir hardcodecharacter para fingir conversão.
InteirosQ8.8/int16/signed32 apenas onde semântica precisa; operaçõeslargas
medidas. Ir24.8Python não prova custoZ80. UNSUPPORTED sempreemitido/visível,
sem stub silencioso deHitDef/Projectile/Helper/Power/AssertSpecial.

Runtime separa entidades/combate/input/CMD/IA/objetosFX/render/HUD/PSG/cenas.
Pools estáticos para2lutadores e objetos com lifecycle/maxcount/overflowpolicy.
Inputs normalizados facing, histórico/release/pressão/prioridade/cancel/state
validity; onepulse/onecommand. IA usa mesmo caminho de comandos e limitações
de controle do jogador, sem invocar dano/state direto como prova de controle.
Tracefonte→estado/action/element/CLSN→contato/dano/HUD porframe e slots.

CenaFSMúnica título/menu/options/select/VS/round/fight/pause/result/continue/
final/treino; owners/teardown/paleta/VRAM/áudio/banks/inputedge explícitos.
Fontes/menus requerem autoridade de asset; glifo técnico não aprova arte final.

Implementação central emtools/sms_wrapper/mugen2sms/, sem fork de engine no
projeto; gerados emdata/generated/ e outputs out/, thinbuildwrapper padrão.
Testes unitários usam fixtures temporárias explícitas; integrações consumidor
apontam --project rev2. Nunca mockarEIO comoPASS ou depender dos manifestos
do luta_mugen para o novo consumidor.

Backendrenderer só escolhido apósM1; paleta global SMS e metadadosP2 por
igualdadebytes, símbolos_SIZEgerados, bancosmedidos. PolíticasMDPAL0–3/DMA/
XGM2/H40/limites248px são proibidas como constantesSMS.

## Estado 2026-10-18: diagnóstico × produção × orçamento aprovado (Lotes A e B.1)

- **Diagnóstico (v031 `6f4a3cf5…`, ROM congelada):** runtime sprite-only
  diagnóstico, FSM 12 papéis, cadeia causal input→rota→papel→CLSN→dano→KO
  reproduzida com protocolo reforçado; relatórios `out/logs/runs/20261018T*`
  + `out/logs/freeze_v031_20261018.json`; custódia de sessão anexada. Selos
  antigos reprovaram 2456–2954/3000 iterações em hashes anteriores (não na
  v031; sem orçamento de VBlank medido nela). Teto do claim: `diagnostic_only`.
- **Produção (candidato v033 `14381bf4…`, Lote B.1):** perfil no mesmo
  sistema com uma única autoridade de runtime (`LUTA_PROFILE`; funções
  compartilhadas, dois laços); lógica/input/CNS/cache/metasprites no display
  ativo, escritas VDP (stream + SAT) dentro do VBlank pedido, janela medida
  por sonda. A fatia de VBlank fecha no candidato: worst-frame de 3000
  frames ROM medidos sem DAP = `vline_min=197`, `vovf_delta=0`, estado FIGHT
  com os dois atores e fundo sólido (sessão `0139ba8b…`, JSON `01138596…`,
  bundle `0b91a729…`); a ordem histórica (`LUTA_PROFILE 0`, controle v034
  `c0a5adab…`) estoura (88/2335) — instrumento, não o perfil entregável.
  Profundidade de pipeline = 1 frame (declarada). Abertos em B.2: teto de
  tempo do laço (~2 frames VDP/iteração; `probe_frame`/VDP ≈ 0,51–0,56),
  provisão visual (upload de 1 par de 64 B por VBlank contra pool de 128
  pares → flicker/omissão por loteria de emissão; triagem
  `out/evidence/blackscreen_triage_20261018/README.md` retificada por pixels:
  deslocamento de 1 px do P1, não arte distinta), híbrido BG corpo +
  partes/FX na SAT, probes distintas desejada/residente/submetida/apresentada.
  Matriz causal na ordem de produção: 31/32 (D2) ×2 e 30/32 no controle v034
  — classes de janela/distância/fase do instrumento, mecanismo presente no
  traço (`doc/10-memory-bank.md` §Lote B.1). Emulicious = produção/QA,
  BlastEm = diagnóstico.
- **Orçamento aprovado:** não existe. Metas do contrato (1 MiB de ROM etc.) são
  planejamento; corredor de sondas 77/1547 B e razão de instrumento (~2,222
  steps VDP/frame ROM) são contexto do diagnóstico, não cadência de produção.
  Orçamento nasce só de worst-frame com carga representativa, sem DAP, na ROM
  de produção, selado por SHA — o candidato v033 passou a fatia de VDP
  (2 atores + fundo sólido), não o entregável (HUD/FX/áudio). Histórico por
  ROM em `doc/10-memory-bank.md`.

## Estado 2026-10-18 (B.2a): política de produção medida (chunk 8 supersede); derrame por desenho registrado e linhas por etapa

- **Política vencedora (regra pré-registrada: cadence → churn → integridade →
  vovf; fixada antes dos números do serve).** Seis candidatos sequenciais com
  SHA próprio e único delta declarado (chunk 2/4/8 pares por lado ×
  supersede/serve em voo): p1c8 `a613ca97…` (chunk 8, supersede) vence —
  cadence 1,2332 (wait 3586+3844 / 6025 frames SMRT) e churn 326; ordem,
  candidatos e números no manifest
  `out/logs/runs/20261018T202627Z_loteB2a_manifest_a613ca974e2c.json`.
- **A fatia de VBlank agora carrega o custo real e derrama por desenho.**
  Os dois atores são servidos por VBlank (o "pass" da v033 servia 1 par/VBlank
  em round-robin e escondia um lado): worst-frame do vencedor `derramou`
  (vovf 2511/3000, vline_min 0, sessão `05f87780…`, JSON `b1bbb032…`); a
  janela de lógica segue intacta (entrada 194 constante), a imagem é sempre a
  última pose COMPLETA, no-evict medido (`evict_events=0`), overflow por lado
  registrado (198/291), pool no teto 128 pares com recuperação sem evict.
- **Linhas por etapa (instrumento `p1c8stg` `d566d814…`, delta = SÓ o patch de
  estágios vs vencedor):** upload ≤200, SAT copy ≤31, fatia ≤221 linhas,
  entrada ≤2; bytes novos 43.969 pares ≈ 2,81 MB na janela; recibo com
  funcional vivo (14 hits, 1 KO, 70 `clsn_checks`). Serve×chunk: o fit do
  serve em chunk 2 (vovf 1373) não generaliza para chunk 8 (2580 ≈ 2511) —
  hipótese refutada medida; serve preservado como alternativa para o
  pós-híbrido (§92 do mandato).
- **RAM/stack:** dados até 0xC1FD; stack SP=0xDFF0 com 5876 B livres acima do
  corredor; sondas 97 (produção) / 102 (instrumento), corredor pass com folga
  1539 B; contrato `contract_pass` pós-emenda (relatório
  `20261018T202727Z_mugen_contract_postB2a_4c592813ac6b.json`); 72 ferramentas
  de medição com self-check. `approved_budget` continua inexistente: nada aqui
  promove entregável, áudio ou qualidade visual.
- **Abertos (B.2b):** híbrido BG corpo + partes/FX na SAT, mapa VRAM por
  plano, paletas P0/P1/P2, movimento px/dirty regions/restauração, teto de
  SAT 64 sprites/cena como contrato medido + mecanismo do `sat_om_p2` do
  serve, vídeo de transição 256×192, reancoragem D2/G.
