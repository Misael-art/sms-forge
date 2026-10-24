# Pacote para o curador — pose budget de 8 sprites

Data: 2026-10-23. Estado: `awaiting_curator`. Este arquivo não emite ID de lição.

O dono aceitou o estudo de Ken e Ryu e pediu que o motor use a metodologia como default, converta os sprites, compile um piloto e compare com a ROM anterior. Isso já está no motor e no projeto `luta_mugem_rev2`. A promoção a lei da fábrica não foi feita. `SMS_GLOBAL.md`, `doc/agent_learning/learning_ledger.json`, `doc/curation/id_registry.json` e `doc/agent_learning/lesson_routes.json` permanecem como estavam. O registro lido nesta data declara `issued_through` `L138`. Conferir de novo antes de emitir qualquer ID. Não reutilizar `L012` nem a faixa `L020`–`L034`.

Índice machine-readable, sem chave `lessons`: `doc/curation/2026-10-23_pose_budget_aguardando_curador.json`.

## O que o dono pediu

1. Não congelar a conversão antiga. O encaixe só de tamanho, a faixa histórica de idle 72–88 px e o 1:4 continuam selecionáveis.
2. O default passa a ser um encaixe coerente com o Master System, e o projeto precisa nomear o framebuffer de origem. Game Gear (160×144) é referência declarada, não o alvo deste piloto.
3. A pose mais larga do corpo é a referência de conversão quando cerca de 70% das poses do corpo já cabem em 8 sprites. A fração é uniforme para todos os sprites, inclusive efeitos.
4. Os cerca de 30% que excediam 8 sprites ficam para estudo caso a caso. O piloto não redesenha esses quadros um a um.
5. O propósito declarado é cortar o esforço por quadro e ganhar velocidade de produção e folga de hardware. A ROM anterior, na escala uniforme 40/49, ainda deixava quadros acima de 8 colunas.
6. Registrar a condição, alterar o motor, converter, compilar e comparar as duas ROMs.

## Onde isso vive

| Peça | Caminho |
|---|---|
| Lei de projeto | `SMS_projects/luta_mugem_rev2/doc/28-pose-budget-8.md` |
| GDD | `SMS_projects/luta_mugem_rev2/doc/11-gdd.md`, primeiro parágrafo |
| Memória operacional | `SMS_projects/luta_mugem_rev2/doc/10-memory-bank.md`, seção 2026-10-23 |
| Perfil | `SMS_projects/luta_mugem_rev2/doc/display_profile.json` |
| Configs do piloto | `doc/continuity/config/ken_pose_budget.json` e `ryu_pose_budget.json` |
| Motor | `tools/sms_wrapper/mugen2sms/converters/display_fit.py` |
| Corte de cena | `tools/sms_wrapper/mugen2sms/generators/scene_cut.py`, `_prepare_pose_budget` |
| Teste | `tools/sms_wrapper/mugen2sms/tests/test_display_fit.py` |
| Arte | `SMS_projects/luta_mugem_rev2/out/display_fit/pose_budget_8/` |
| ROM nova | `SMS_projects/luta_mugem_rev2/out/rom/pose_budget_20261023.sms` |
| Comparação | `SMS_projects/luta_mugem_rev2/out/logs/pose_budget_20261023_compare.json` |

Configs históricas `ken_pilot_diag.json` e `ryu_pilot_diag.json` não foram editadas. `src/main.c` e `.mddev/project.json` vivos não foram editados. O build do piloto usou cópia temporária porque o manifesto vivo ainda aponta os 49 banks de `out/generated/ryu_ken_cross/`. Compilar o projeto vivo recria a ROM anterior.

## Fatos medidos

Ken: porta `open`, 71/100 ações de corpo já em 8 colunas ou menos, escala extra 2/3. Ryu: porta `near`, 107/154 = 0,6948, a mesma escala extra. A referência dos dois, depois do encaixe CPS2, é a ação 440, célula 96×48. Lista caso a caso: 29 ações do Ken e 47 do Ryu. Depois da escala extra, nenhuma célula de corpo passa de 8 colunas. Onze células de FX do Ryu continuam acima; a maior é `g8400` 112×24, 14 colunas. Retratos do grupo 9000 continuam 120×140 e não entram na referência.

Marcadores:

- Ken `7fba0349e33853efb81f0ed7fb1f967c9055cbe5ab1e7bad1bebc59f1b878244`, texto `display_fit: source=cps2 target=sms x=2/3 y=6/7 pose=2/3 gate=open`
- Ryu `0ded20292cd3bc8525fa58de0f055485d8df936c9ab69e0e3fe4a4195ba80cf8`, porta `near`
- Resumo `4ca2b8d76373297018b79bcc7e69e54ea9e88fcbd6ff4295b8b806cb9db4f4e4`
- Segunda passada no mesmo diretório: exit 2

Slots de pixel: Ken 1245763 → 402707; Ryu 3428516 → 1086817. Durações AIR preservadas. O chute `g440_1` fica 64×32. O primeiro idle fica 32×56; o quadro mais alto do grupo 0 fica 32×64.

ROM anterior, intacta, data 2026-10-20: `out/rom/luta_mugem_rev2.sms`, 851968 bytes, SHA-256 `087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65`, 49 banks, imagem 802816 bytes `3af7a307b304e29a40ab2997c846088438a570ac6ce9b32a889690edecc12f8f`, header `19edb320606f660a6a13c67933b99a3d5d19e0501acd2995e2250370cac98949`, escala 40/49.

ROM do piloto: `out/rom/pose_budget_20261023.sms`, 458752 bytes, SHA-256 `9008505cb82232e42d1b57d3ecb852af70f566625995cfd3cb5b526b277b1eba`, 24 banks, imagem 393216 bytes `468427efd8850a6323c7e4b99e216dea565e7e28e8f5fe23a6167edffe9bcba6`, header `3be5a775c1b0779af60a894f7a0f6970a4f3d85e248314b74b4b40c9a1678955`.

O corte tem as mesmas 48 poses do Ryu e 45 do Ken, a mesma contagem de quadros e as mesmas durações AIR. P1 é `ryu.zip`; P2 é `Ken_Majik_.zip`. Os diretórios continuam se chamando `p1_ken` e `p2_ryu`. Na escala 40/49 havia 9 quadros acima de 8 colunas em cada lutador, teto 12 no Ryu e 13 no Ken. Neste corte o Ryu chega a 6 colunas e o Ken a 8, no KO 64×32.

Testes citados pelo lote: `test_display_fit.py`, `test_sms_scale.py`, `test_scene_cut_scale_order.py`, `test_cli_sms.py`, 32 passed. O self-check de `display_fit.py` trava a razão 2/3 por 6/7, a recusa sem origem, a porta `near` no formato 107+46+1 e a porta fechada em 5 largas + 5 estreitas.

O Emulicious abriu a ROM nova. A captura da janela saiu preta. Status do piloto: `buildado`. Sem boot aceito, sem FPS, sem áudio, sem entrega visual, sem `scale_pilot`.

## Pontos que o curador precisa separar

Cada ponto traz o fato, o propósito e o limite. Inferência não vira técnica fechada.

### PB-01 — Default do motor

Fato: `DEFAULT_MODE` de `display_fit.py` é `pose_budget`. Omitir o modo aplica o encaixe de framebuffer e arma a segunda escala. `mode: framebuffer` deixa `pose_budget` falso e não aplica a escala extra.

Propósito: o tamanho coerente com o Master System deixa de ser estudo e passa a ser o caminho de conversão.

Limite: isso é política do motor neste workspace. Ainda não é seção de `SMS_GLOBAL.md`.

### PB-02 — Origem obrigatória e alvos

Fato: CPS1 e CPS2 são 384×224. SMS é 256×192, razão 2/3 na largura e 6/7 na altura. Game Gear é 160×144, razão 5/12 e 9/14. Origem ausente ou desconhecida é recusada. Origem igual ao alvo fica identidade 1/1. `legacy_quarter` e `fighter_scale` devolvem status `option` e este comando não reescreve pixel por eles.

Propósito: o projeto declara o padrão de origem na definição. Game Gear existe como referência nomeada.

Limite: a altura do SMS é 192 e a do CPS2 é 224, então o eixo Y escala. A regra de outro console em que o Y fica 1/1 não se transfere. Não aplicar um segundo esmagamento de aspecto por cima dessas frações sem medir.

### PB-03 — Amostragem, padding e o que não muda

Fato: vizinho mais próximo de pixel já indexado. `scale_length` é `max(1, (length * num) // den)`. Coordenada não negativa usa `(v * num + den // 2) // den`. Amostra usa `min(src_len - 1, (dst * den + num // 2) // num)`. O padding completa múltiplo de 8; a sobra inicial é `extra // 2` e o pixel ímpar fica à direita e embaixo. Índice 0 continua transparente. Tempo, flip e blend não mudam.

Propósito: a célula que entra na ROM é a célula padded, e a contagem de colunas usa essa célula.

Limite: a matemática inteira segue o encaixe já usado no motor, não o arredondamento de `sms_scale.py`.

### PB-04 — Corpo, FX e retrato

Fato: a pose é uma ação AIR. O custo é o quadro de corpo mais largo. Grupo 9000 e os `fx_groups` declarados não definem a referência. Os FX recebem a mesma escala extra, para a proporção entre corpo e efeito permanecer. Listas usadas: Ken 1001 e 1002; Ryu 1150, 1160, 1250, 1260, 3050, 8000, 8010, 8020, 8030, 8040, 8050, 8060, 8210, 8220, 8230, 8300, 8310, 8320, 8330, 8400 e 8410. O grupo 9010 do Ryu é misto e entrou como corpo.

Propósito: um efeito largo não pode escolher a escala do lutador. Uma lista vazia deixaria o `g8400` de 160 px, 20 colunas no encaixe só de tamanho, virar a referência e esmagar o corpo para 64/160.

Limite: a lista é explícita, copiada dos nomes de folha de FX do estudo anterior. Inferir `explod`, `projectile` e `helper` do CNS não foi implementado. Uma heurística “grupo ≥ 8000” perde os FX 1001 e 1002 do Ken.

### PB-05 — Porta de cerca de 70%

Fato: a porta abre em razão ≥ 0,70 (`open`). Entre 0,69 e 0,70 abre como `near`. Abaixo de 0,69 a escala extra fica 1/1 (`gate_closed`). Se a pose mais larga já tem largura ≤ 64 px, a escala extra fica 1/1 (`already_within`). A escala extra é `64 / largura` reduzida pelo máximo divisor comum. No Ken e no Ryu isso é 2/3.

Propósito: cumprir “cerca de 70%” sem arredondar a contagem. Ryu tem 107/154 = 69,48%. Tirar o grupo 9010 do denominador daria 107/153 = 69,93% e ainda não chega a 70%. Essa conta não foi alterada.

Limite: a unidade de decisão é a ação, não o quadro. A razão por quadro do estudo anterior era mais alta e não decide a porta.

### PB-06 — Duas passadas, não uma fração composta

Fato: a primeira passada é o encaixe de framebuffer com padding. A segunda é a escala uniforme com novo padding. O marcador só é escrito no fim.

Propósito: a coluna conta a célula padded. Compor 2/3 × 2/3 na origem, antes do padding, não produz a mesma célula.

Limite: se alguém precisar da fração desde o pixel CPS2, a largura composta é 4/9 e a altura composta é 4/7. O motor não usa esse atalho. A única trava contra uma terceira passada é o marcador.

### PB-07 — Caso a caso

Fato: `case_by_case` lista as ações que, depois do framebuffer e antes da escala extra, passavam de 8 colunas. Elas receberam a mesma fração do corpo. Nenhuma foi reautorada.

Propósito: separar o que a escala uniforme resolve do que ainda pede julgamento artístico. O esforço por quadro deixa de ser o caminho default.

Limite: depois da escala extra essas poses de corpo também cabem em 8 colunas no papel. A lista continua sendo dívida de revisão, não prova de que o desenho ficou bom. Os onze FX do Ryu que seguem acima de 8 colunas são outro conjunto: efeitos mais largos que a referência do corpo.

### PB-08 — Corte da ROM e o rótulo `downscale1:4`

Fato: `size_policy: pose_budget` escala o personagem inteiro, inclusive a ação 440, e devolve `pre_scaled` verdadeiro. `smsdev.generate` não divide de novo por 4. A faixa 72–88 não roda nesse caminho; a altura de conteúdo do idle ficaria fora dela. O manifesto guarda o relatório na chave histórica `fighter_scale`. Dentro dela, `ratio.numerator/denominator` é a escala extra 2/3, com `framebuffer_x` e `framebuffer_y` ao lado. A classe de fidelidade continua `approximate` com motivo `downscale1:4` quando a célula passa de 4 colunas ou de 3 sprites altos, porque `needs_scale` olha o tamanho já convertido.

Propósito: o piloto usa os mesmos papéis da ROM anterior e muda o tamanho dos pixels. A ação 440 define a fração mesmo fora da lista de papéis.

Limite: ler `downscale1:4` neste corte como “a arte foi reduzida a um quarto” é falso. Ler `numerator: 2` como se fosse a escala única 40/49 também é falso. O helper `_worst_scene` ainda divide por 4 quando `needs_scale` é verdadeiro; o número dele não é a coluna deste piloto.

### PB-09 — Oito colunas de um lutador não fecham a scanline da cena

Fato aritmético, sem `audit_sprite_line_sim`: uma célula de 64 px ocupa 8 sprites na scanline que ela cobre. O KO do Ken no corte chega a 8. O teto incluído do Ryu chega a 6. Os idles incluídos ocupam 4 cada. Duas poses largas na mesma linha somam as colunas.

Propósito: o alvo de 8 é o limite de um lutador, que era o estouro visto na escala 72–88. A curadoria `L090` já registrou que zero flicker nessa faixa ficou bloqueado por um piso de 9–10 sprites por linha.

Limite: esta aritmética não é aprovação de simulador nem de framebuffer. Dois lutadores no mesmo Y continuam podendo passar de 8. A SAT de uma célula 64×32 em modo tall é 16 entradas; duas células dessa ordem cabem nas 64 entradas e mesmo assim estouram a linha. Coluna não substitui `audit_sprite_line_sim.py`.

### PB-10 — Tamanho da ROM não é FPS

Fato: a imagem de banks caiu de 49 páginas de 16 KB para 24. A ROM caiu de 52 páginas (851968) para 28 páginas (458752).

Propósito: menos bytes de pose era um efeito esperado da célula menor.

Limite: nenhum `measure_fps.py`, `measure_frame_advance.py` nem `measure_worst_frame.py` rodou nesta ROM. Velocidade de produção e performance de jogo seguem como propósito, não como resultado.

### PB-11 — Boot não aceito

Fato: `audit_deterministic_boot.py --runs 1` devolveu PASS sobre uma captura preta de 311 bytes, com o emulador em `Update=0`. Uma segunda abertura, sem esse flag e com espera de cerca de 2 s, mostrou o menu do Emulicious e o miolo preto, 1251 bytes. As duas janelas foram encerradas.

Propósito: tentar ver a ROM. A ferramenta antiga de boot determinístico pode fotografar um frame preto e ainda assim comparar hashes iguais.

Limite: captura preta não é lutador visto. O status permanece `buildado`. Não promover a `testado_em_emulador`. Há lição antiga de canal e de escala de janela (`L039`, `L040`) e de sessão zumbi (`L057`); este lote não as reabre.

### PB-12 — O que este lote não promove

ZIPs de origem conferidos no lote anterior e não reescritos. O intake continua congelado; este piloto é encaixe de tamanho mais ROM diagnóstica, não conversão terminada do motor de luta. Especiais continuam sem projétil no runtime. A ROM `087df676…` não foi substituída. Não há claim de 60 fps, áudio, gameplay nem entrega visual. Números de Mega Drive não viram lei do Master System (`L001`). A faixa 72–88 e o contrato de escala por área opaca do idle continuam na doutrina existente (`L083`, §68); este default convive com eles como outra opção e o `scale_pilot.py` não foi executado sobre a célula nova. Pivô espelhado e metadata por paleta (`L086`, `L088`) não foram remedições deste lote. Plano periódico de slots (`L090`) e prova de framebuffer (`L091`) também não.

## Trabalho do curador, ainda não feito

1. Ler este pacote, `doc/28-pose-budget-8.md`, o JSON de comparação e as lições `L083`, `L086`, `L088`, `L090` e `L091` antes de emitir ID.
2. Decidir o alcance: política já aplicada no motor e neste projeto, ou também seção nova append-only de `SMS_GLOBAL.md`. Sem aprovação humana explícita para a lei, parar no pacote.
3. Se emitir ID, usar o próximo livre depois de reler `id_registry.json`. Não renumerar seção antiga. A lição precisa de `rule_section` e de ferramenta real. O self-check de `display_fit.py` já cobre razão, origem recusada, porta `near` e porta fechada. Ele não cobre lista de FX vazia, segunda divisão por 4, scanline de dois lutadores nem framebuffer da ROM.
4. Atualizar ledger com `dedup_key` e `lesson_routes.json` com o SHA do entrypoint depois de editar o texto. Refresh cego não demonstra absorção.
5. Rodar `selftest.py`, `validate_measurement_tools.py`, `audit_doc_sync.py` e `audit_learning_capture.py` antes de chamar a curadoria de fechada.
6. Manter `framebuffer`, `fighter_scale` e `legacy_quarter` selecionáveis. Uma lição que apague a faixa 72–88 contradiz o pedido do dono.
7. Tratar a lista caso a caso e os onze FX do Ryu como dívida, não como técnica resolvida.
8. Exigir captura de framebuffer da ROM `9008505c…` antes de qualquer claim visual ou de performance.

Conferência deste pacote, em 2026-10-23: `display_fit.py --self-check` imprimiu `display_fit self-check ok`. `audit_learning_capture.py --root` do SMSForge passou e gravou `SMS_projects/luta_mugem_rev2/out/logs/learning_audit_pose_budget_20261023.json`. Esse PASS confirma que o pacote não emitiu ID órfão. Não fecha a curadoria.

## Aprovação do padrão e classe de glitch ainda aberta

No mesmo dia o dono confirmou: o método é o padrão do motor. Isso confirma o default já implementado. Não emite ID e não autoriza escrever `SMS_GLOBAL.md`.

Diagnóstico posterior, medido e registrado em `SMS_projects/luta_mugem_rev2/doc/28-pose-budget-8.md`:

- Empacotar o tile não desloca pixel. 0 mismatches nos sprites de papel.
- A paleta de 7 cores por frequência excluía o preto opaco, 8ª cor nos dois. Ken: 34/39 quadros de papel com perda de aresta ≥ 8% (2889/19479). Ryu: 13/40 (1624/22694). É a classe “alguns quadros do Ryu, mais quadros do Ken”.
- A guarda nova reserva a cor mais escura e a mais clara e remove a duplicata mais próxima. A perda medida cai para 2140 e 1585 arestas. Testes em `test_scene_cut_palette_binding.py`. A ROM com a paleta reservada é `SMS_projects/luta_mugem_rev2/out/rom/palette_reserve_20261023.sms`, SHA-256 `f9ef0e27…`, 458752 bytes. A piloto `9008505c…` permanece no arquivo anterior. Esta ROM nova também está sem framebuffer aceito.
- Folhas PNG sem transparência mostravam o magenta do Ryu e o preto do Ken no índice 0. `_write_png` agora marca esse índice. As folhas existentes não foram regravadas.
- Amostragem: 26 pixels novos transparentes no Ken e 44 no Ryu. Preencher por votação foi avaliado e recusado.

O dono viu a ROM `palette_reserve_20261023.sms` mais escura. A medição nas paletas `ken1` e `ryu02` dá média 110,2 no Ken e 137,5 no Ryu, contra 115,9 e 142,3 nas sete cores frequentes. O creme do Ken, 4840 pixels, caía no rosa. A guarda passou a recusar a troca quando o slot é um tom de corpo (luma 100 ou mais), quando é a cor mais usada, quando o erro quadrático sobe ou quando a média de todos os pixels opacos cai mais de 1. O empate de distância fica com o vizinho mais próximo em brilho. A ROM sucessora é `SMS_projects/luta_mugem_rev2/out/rom/palette_luma_20261023.sms`, SHA-256 `6fb424a3ddf32002d5de9c27685c1387fa89d4205365b344ba64fe8c866cd873`, 458752 bytes, também sem framebuffer aceito. O preto opaco continua fora das sete cores destes dois lutadores.

O curador não marca esta classe como fechada enquanto não houver framebuffer aceito. A ROM reservada permanece como evidência da paleta que escureceu. A guarda de código também não cobre lista de FX vazia, segunda divisão por 4, scanline dos dois lutadores nem essa captura.

## Parecer de 2026-10-23 — captura do par

Registrado a pedido do dono, sem ID de lição e sem escrita em `SMS_GLOBAL.md`. O texto operacional está em `SMS_projects/luta_mugem_rev2/doc/10-memory-bank.md`, seção «parecer da captura do par». PB-11 continua válido para a captura de janela preta. O framebuffer 256×192 posterior tem status `testado_em_emulador` e não é entrega visual.

### PB-13 — As duas capturas são o mesmo desenho

Fato: `pose_budget_20261023_idle_256x192.png` (1667 bytes, SHA-256 `64f5b9451439b5c37e4644f9f067bd9f2c6c80e23a1564e3b19ebff0f7e98800`) e `pose_budget_pair_20261023_idle_256x192.png` (1658 bytes, SHA-256 `50beed8b55d73ff60f90384f52d60008e12e9d58070f8683f96209430e7a992a`) têm a mesma ocupação opaca. O diff é de 14 pixels, todos no Ken, de `(170,0,0)` para `(170,85,85)`. Ryu: x 70–99, 30 px, y 108–160, idle legível. Ken: x 118–121 (4 px), vão, x 126–141 (16 px), vão, x 146–149 (4 px). O vão total é 32 px.

Propósito: separar «há tinta dos dois lados» de «o lutador está desenhado».

Limite: a ROM do par é byte a byte `palette_luma_20261023.sms` (`6fb424a3…`). A paleta não consertou o Ken. A causa (stream incompleto ou tile/ordem do P2) fica aberta até um quadro com as duas poses já residentes. O runtime não mudou.

### PB-14 — O zero do simulador não é a luta

Fato: `out/logs/pose_budget_pair_20261023/line_summary.json`, self-check antes da leitura. Incluídos com pico 8 e zero violações: idle/idle (32 sprites), Ken idle + Ryu special (30), Ryu special + Ryu ko (30). Fora do lote: Ken idle + Ken punch, pico 10, 5 violações; Ken ko + Ryu idle, pico 12, 5 violações.

Propósito: o relatório de linha precisa nomear a composição que a ROM pode mostrar.

Limite: `included_pair: false` não remove o papel. Os três zeros são dois parados, um especial de 4 colunas e o Ryu contra ele mesmo. A regra 5+3 não foi o par que passou.

### PB-15 — Golpe largo continua na ROM acima de 4 colunas

Fato: o runtime ainda exige Ken punch 250 (6), hp 450 (7), kick 200 (6), hk 220 (6), special 1000 (6), ko 5080 (8, 64×32); Ryu punch 260 (5), hp 280 (6), kick 200 (6), hk 240 (6). Contra um idle de 4 colunas na mesma linha o pico é 9, 10, 11 ou 12.

Propósito: `case_by_case` lista a dívida. A célula emitida é o que a SAT recebe.

Limite: marcar o papel como caso a caso não o tira do binário. A regra 5+3 ainda não é célula emitida.

### PB-16 — Hurtbox do idle do Ryu

Fato: no primeiro quadro, o padding duplo não desloca a sola mais de 1 px. Ken idle e Ken punch ficam em delta 0. Ryu punch move 1 px pelo pad. A hurt do Ryu idle passa de 0 para 2 px além da sola porque a linha de baixo não foi amostrada.

Propósito: separar deslocamento de padding de furo de amostragem.

Limite: sampler, eixo e hurtbox não foram alterados.

### PB-17 — Orçamento de VBlank sem número

Fato: `measure_worst_frame.py` na sonda `0xC800` devolveu `sem_lastro` (frame 2035, `done` 0). A imagem passou de 49 banks para 24.

Propósito: tamanho da ROM e velocidade do quadro são medidas diferentes.

Limite: `validado_budget` continua fechado. 24 banks não são FPS. Sem 60 fps, áudio, gameplay ou entrega visual.

### PB-18 — O que este parecer não promove

A produção `087df676…` permanece. `src/main.c` e `.mddev/project.json` vivos seguem em `ryu_ken_cross`. Compilar o projeto vivo recria a ROM antiga. Sem ID de lição e sem `SMS_GLOBAL.md`. O bloco «Resultado medido» de `doc/28-pose-budget-8.md` descreve o piloto da manhã; a condição viva é o parágrafo do par. O próximo lote pede o quadro com as duas poses residentes, a medição de cada composição que a ROM pode mostrar, e pico acima de 8 como reprovação dessa composição.

## Nota de 2026-10-23 — o critério vigente deixou de ser a porta de 70%

O lote do par, registrado em `SMS_projects/luta_mugem_rev2/doc/28-pose-budget-8.md`, substitui a unidade descrita em PB-05, PB-08 e PB-09. A porta de cerca de 70% e a pose mais larga em 64 px ficam como história do piloto da manhã. O critério vigente mede a célula da SAT: 4 colunas na pose neutra de cada lado, 5 e 3 no golpe largo contra a neutra, e caso a caso acima disso. `POSE_NEAR` não abre nem fecha a escala. O motivo do corte novo nomeia `framebuffer x=2/3 y=6/7 extra=2/3` e não grava `downscale1:4`. Efeito acima de 3 colunas sai do corte; o `g8400` não foi para o plano de fundo.

PB-11 continua válido para a captura de janela preta. Depois dele, o framebuffer 256×192 do piloto `9008505c…` mostrou os dois idles (`pose_budget_20261023_idle_256x192.png`, SHA-256 `64f5b945…`). Isso não promove o piloto. A ROM do par, `pose_budget_pair_20261023.sms`, SHA-256 `6fb424a3…`, 458752 bytes, é outro caminho e é byte a byte igual a `palette_luma_20261023.sms`. O arquivo de luma não foi o caminho capturado e não foi sobrescrito. O framebuffer do par, SHA-256 `50beed8b…`, mostra os dois idles. O item 8 desta lista, que pedia captura de `9008505c…` antes de claim visual, não autoriza claim visual desta captura: as listras do Ken continuam, `validado_budget` segue proibido e não há ID de lição. `SMS_GLOBAL.md` não foi editado.

## Nota de fechamento — PB-13 a PB-18

O lote de 2026-10-23 fechou PB-13 a PB-18 como medição, sem promoção. O registro completo, com inventário de SHA, dez pares, gate de composição, correção da sola e pior quadro, está em `doc/curation/2026-10-23_pose_budget_fechamento_pb13_pb18.md` e no JSON de mesmo nome. PB-13 fechou com pose residente no frame 500 (16+16 células SAT; Ken fecha o corpo); PB-14 fechou com dez pares reais de pico 9–12; PB-15 fechou com gate derivado do META (25/93 poses, dez papéis derrubados); PB-16 fechou com a sola do Ryu corrigida de 2 px para 1 px; PB-17 fechou como `derramou`, `vline_min=4`, `vovf_delta=1740`; PB-18 permanece: produção `087df676…` intacta, sem ID, sem `SMS_GLOBAL.md`, sem ledger, sem commit. `validado_budget` continua proibido.
