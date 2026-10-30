# TDD — luta_mugem_rev2

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
