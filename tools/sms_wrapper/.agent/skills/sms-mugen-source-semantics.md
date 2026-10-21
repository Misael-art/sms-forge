# skill: sms-mugen-source-semantics

Use para intake MUGEN e revisão de cortes/dados de combate. Especialização de
SMS_GLOBAL §§68/78–80/98/100, L037/L071/L083/L093–L095. Não assume compatibilidade
CNS completa nem ensina números de um corte como constantes do Master System.

## Fonte e estágios distintos

Identifique `.def`, pacote/AIR/CMD/CNS por SHA; nomes internos `ken`/`ryu` ou
`p1_ken`/`p2_ryu` podem ser namespaces históricos. `source_def` e SHA nos
manifests identificam a origem real. Classifique personagem/stage antes de
gerar; licença/restrições da fonte continuam registradas no intake. Inventário
ZIP/RAR não autoriza promover todos os itens a personagens ou assets finais.

| Estágio | O que sustenta | O que falta |
|---|---|---|
| parse / IR | Estrutura, referências e classificação direct/approximate/unsupported | Fidelidade executada e custo Z80 |
| generated | Tabelas, pools, patterns, comandos emitidos | Consumidor da ação e layout pós-link |
| consumed | Papel roteado no código/FSM/dispatcher | Prova da execução/efeito na ROM |
| ROM observada | Caso atribuído na SHA/sessão testada | Demais casos, worst-frame/FPS/áudio e qualidade |

`role_accounting`, `unconsumed_source_roles_by_slot`, `unsupported_runtime_roles`
e limitações por slot registram o alcance. Nome `special` ou padrão de comando
emitido não implementa projétil, dano, recurso power nem a sequência CNS.
Objeto C compilado não é link/ROM; SAT estático com âncoras fixas não prova
scanlines dinâmicas, upload ou ausência de flicker. Aponte o manifest exato:
um README pode registrar várias gerações históricas com escopos diferentes.

## Camada de chão/colisão por tile (tilemap bits 13–15)

A entrada de name table tem bits 13–15 que o VDP ignora e o SMSPower documenta
como "flags for collision and damage zones" (`Tilemap.txt`). O motor pode usá-los
como máscara por tile (solo/parede/zona de dano do stage), mas isso é SEMPRE
decisão declarada, nunca padrão: o gate `audit_tilemap_bounds.py` veda bits
13–15 por padrão e reprova qualquer `SMS_setTileatXY` que os arme sem
`--allow-tilemap-flags "<motivo>"`.

Regras para a camada de chão por tile:

- **Nenhuma bit 13–15 tem semântica até o TDD/spec de cenas do projeto
  `mugen_fighting_v1` a declarar.** Bit 13 ≠ "chão" por direito; o motor atual
  não lê esses bits, então promovê-los a colisão sem consumidor é o estágio
  `generated` sem `consumed` da tabela acima — nome/flag emitido não implementa
  hitzone.
- **Não colidir com metasprites/pools.** O mesmo bit não pode ser bandeira de
  tilemap e flag de pattern table de sprite: são memórias distintas; declare o
  domínio (só entrada de name table do stage) e o bitmask exato.
- **Fonte real da hitzone é o CNS/stage do MUGEN, não o bit.** O bit pode
  *carregar* uma classificação derivada do `ground.front`/`mugen_fighting_v1`
  intake, mas a verdade de colisão vem do AIR/HitDef já resolvido (ver
  "Entrada de golpe próximo/distante"). Bit sem lastro no intake é dedução, não
  evidência.
- **Meça antes de afirmar.** Uma hitzone por tile só vira claim quando o corte
  roda no emulador e a sobreposição é vista no framebuffer (`regra final de
  ferro`); até lá é `documentado`, não `testado_em_emulador`.

Gate no fechamento: `audit_tilemap_bounds.py` (coordenada L011 + bits 13–15
L132); rode `--self-check` antes de interpretar. Ver SMS_GLOBAL §123.

## States, actions e comportamento

O AIR da especificação MUGEN 1.0 usa game ticks, nominalmente 60/s; não aplicar
a unidade de outro motor, como uma interpretação de delay OpenBOR. PAL exige
política temporal explícita e prova regional. Verifique exposição inicial,
elementos de duração 1, holds/LoopStart e terminal; avançar a FSM antes de emitir
pode pular a primeira imagem. Fonte primária: [AIR Elecbyte](https://www.elecbyte.com/mugendocs/air.html).

CLSN sem Default é associado ao elemento; Default fornece a caixa persistente
da ação. Não inferir carry-forward de caixas comuns por intenção presumida do
autor. Testar caixa específica, Default, override e transição de ação conforme
a versão fonte. Concordância de parsers e bytes no binário não é replay do
executável MUGEN. Consulte também o [tutorial oficial de colisões](https://www.elecbyte.com/mugendocs-11b1/tutorial2.html).

Resolva a ação realmente chamada pelo estado; não inferir KO/crouch/guard por
número semelhante. Guarde hold `-1`, GUARDEND finito, fases de salto e
transições CNS separadamente. `loop_start=0` imposto pelo corte é política
local, não `LoopStart` declarado no AIR. Fonte com política diferente fica
como aproximação/limitação até haver consumidor e prova nova.

Para AIR finito, o produtor `mugen2sms/analysis/air_source_identity.py` gera
fonte hash-bound com IDs `ação:elemento` e terminal. Não funde elementos com
sprite repetido; recusa LoopStart explícito e durações não finitas/ambíguas
no perfil atual. Use o record como `source_air` de `air_identity_timing`, com
trace ROM novo e `--require-air-identity`. Export fonte é source-only; não
preencher timestamps ROM a partir da duração esperada.

## Entrada de golpe próximo/distante

`scene_cut.py` extrai perfis restritos. Próximo reconhece a porta direta em
pé/controle, comando sem holddown e `P2BodyDist X < inteiro`, recusando
predicados/grupos que aquele perfil não modela. Fallback distante deriva o
complemento de uma regra próxima anterior com mesmo comando; conserve a
ordem dos ChangeState. O perfil far registra outros grupos como não compilados:
entrada direta não aprova chain/cancel. Não generalizar para qualquer CNS.

Na distância, declare unidades fonte, razão de escala e `ground.front` dos
dois slots. P2BodyDist não é distância entre eixos. Preserve valor racional
até Q8.8 e teste ambos os lados do limiar; `audit_import_semantics.py` mede
apenas o perfil standing/facing/uniform-scale. Valores 45/46, 72/107 ou
5512 Q8.8 são exemplos históricos do Ryo/Terry, não defaults de outro elenco.

`fight_runtime_data.py` exige dados de origem/geometria para variantes
presentes e reporta os papéis sem consumidor. Revise HitDef aproximado,
velset/physics omitidos e fallback sem dano por slot. Teste máscara exata de
botões: acorde não mapeado não deve disparar ataque simples. Ryo e Terry
têm comandos/tier próprios; não copiar o perfil do personagem anterior.

## Expressões, pacotes e medição

Para comparar trilhas antes/depois (L096), use
`mugen2sms/analysis/trace_compare.py before.json after.json --out-json report.json`.
Comprimento, cenários, chaves e conteúdo por tick fazem parte do contrato;
uma cauda perdida ou acrescentada reprova. Não use apenas `zip`, que descarta
o trecho excedente. Execute `--self-check` antes de interpretar o resultado.
Equivalência mede os campos registrados, não render, tempo Z80 nem estado
omitido; a origem e a janela de cada trilha precisam de evidência própria.

A forma `Animelem = 2,[0,16]` é intervalo do tempo do elemento, inclusivo.
O teste de VM cobre -1/0/16/17; parser/bytecode aprovado não mede execução Z80.
Formas diferentes e features não suportadas exigem perfil/testes próprios.
Source RAR usa extração temporária privada via 7z/7zz e preserva SHA do pacote;
recusa traversal/links nos casos medidos. Os testes sintéticos de archive não
são certificação universal de segurança nem custo para qualquer pacote.

Regressão focada: `test_close_attack_contract.py`, `test_fight_runtime_data.py`,
`test_air_source_identity.py`, `test_expr_value_list.py`,
`test_source_archives.py` em `mugen2sms/tests`. Gates:
`audit_import_semantics.py`, `audit_symbol_size_sync.py`, contrato de engine e
simulador de scanline. Self-check da ferramenta antes de interpretar resultado.

Depois: build/link pelo wrapper, QA privada nativa com contexto production
legível (§99), casos por personagem/par/IA, contato e guard/facing móveis,
vídeo/probe/trace frescos, worst-frame e execução contínua. EIO na documentação
é bloqueio de preparação; trabalhos offline acessíveis não apagam esse blocker.
