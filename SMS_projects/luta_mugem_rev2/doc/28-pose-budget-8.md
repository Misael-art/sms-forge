# Pose budget de 8 sprites — condição default

Data: 2026-10-23. Projeto: `luta_mugem_rev2`. Motor: `mugen2sms.converters.display_fit`.

## Condição

O default do motor continua `pose_budget`. O lote do par, no mesmo dia, trocou a unidade. A frase “cerca de 70% das ações já têm 8 colunas, então a mais larga vai a 64 px” descreve o piloto da manhã e fica na seção histórica abaixo. Não é mais o critério.

1. Encaixe de framebuffer. CPS2 384×224 vai para o Master System 256×192 com largura 2/3 e altura 6/7. Game Gear continua selecionável. Origem ausente ou desconhecida é recusada.
2. Pose neutra de cada lado: no máximo 4 colunas de 8 px na célula que a SAT recebe. Célula 8×16 toda transparente, omitida por `omit_blank_cells`, não entra. Dois idles no mesmo Y fecham em 8.
3. Golpe largo contra pose neutra: no máximo 5 colunas de um lado e 3 do outro. Pose acima disso entra em `case_by_case`. O lote não reautora pixel e não encolhe o corpo de novo para caber o golpe largo.
4. Se o idle já está em 4 colunas, a escala extra do corpo fica 1/1. `POSE_NEAR` 0,69 permanece no relatório como `within_8_ratio` e não abre nem fecha a escala.
5. Efeito declarado em `fx_groups` que passe de 3 colunas depois da fração do corpo não entra no corte. O grupo não é inferido por “≥ 8000”. O grupo 9000 continua fora da referência e não entra como sprite de luta.

`framebuffer`, `fighter_scale` (faixa histórica de 72–88 px) e `legacy_quarter` (1:4) continuam disponíveis e não são este default. Tempos, flips e blend não mudam. Índice 0 permanece transparente. Uma segunda passada no mesmo diretório é recusada.

## Piloto

O corte compilado continua o conjunto de ações de `ken_pilot_diag.json` e `ryu_pilot_diag.json`. A fração usada nesses quadros é a medida no personagem inteiro, não só nas ações do corte. A ação 440 define a referência de 64 px e não entra na lista de papéis da ROM. A ROM anterior permanece em `out/rom/luta_mugem_rev2.sms`. O piloto desta estratégia sai em outro arquivo.

## Resultado medido em 2026-10-23

Este bloco mede o piloto da manhã `9008505c…`. A ocupação do Ken, o diff de 14 pixels e os picos 10 e 12 do par estão no memory bank, seção «parecer da captura do par».

Ken: porta `open`, 71/100 ações do corpo já em 8 colunas ou menos, escala extra 2/3. Ryu: porta `near`, 107/154 (69,48%), a mesma escala extra 2/3. A lista caso a caso ficou com 29 ações do Ken e 47 do Ryu. Essas poses receberam a mesma fração; nenhuma foi reautorada. Depois dela, as células de corpo dos dois ficam em 8 colunas ou menos. Onze células de FX do Ryu, todas fora dos papéis do piloto, continuam acima de 8; a maior é `g8400` em 112×24, 14 colunas. O grupo 9000 permanece isento.

O corte da ROM tem as mesmas 48 poses do Ryu e 45 do Ken, com a mesma contagem de quadros e as mesmas durações AIR. Na estratégia anterior (40/49) havia 9 quadros acima de 8 colunas em cada lutador, com teto de 12 no Ryu e 13 no Ken. Neste corte, o Ryu chega a 6 colunas e o Ken a 8 (KO 64×32). Nenhum quadro incluído passa de 8.

| | ROM anterior | ROM pose_budget |
|---|---:|---:|
| Arquivo | `out/rom/luta_mugem_rev2.sms` | `out/rom/pose_budget_20261023.sms` |
| Bytes | 851968 | 458752 |
| SHA-256 | `087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65` | `9008505cb82232e42d1b57d3ecb852af70f566625995cfd3cb5b526b277b1eba` |
| Banks de 16 KB | 49 | 24 |
| Imagem de banks | 802816 B | 393216 B |

A ROM anterior conserva a data 2026-10-20. O `src/main.c` e o `.mddev/project.json` vivos não foram editados; a compilação usou uma cópia temporária. Comparação: `out/logs/pose_budget_20261023_compare.json`. O Emulicious abriu a ROM nova e a captura da janela saiu preta, então isto não é boot visto nem medida de FPS. Sem áudio e sem entrega visual.

Pacote para o curador da fábrica, sem ID de lição: `doc/curation/2026-10-23_pose_budget_aguardando_curador.md` na raiz do SMSForge. O índice está no JSON de mesmo nome. `SMS_GLOBAL.md` e o ledger não foram alterados.

## Aprovação e glitches de imagem

No mesmo dia o dono aprovou o método como padrão do motor. `pose_budget` segue o default. A ROM do piloto não foi recompilada nesta revisão.

O diagnóstico usou a conversão em memória e as folhas em `out/display_fit/pose_budget_8/`. A identidade entre o sprite e o tile empacotado fechou: 0 diferenças nos 39 sprites de papel do Ken e nos 40 do Ryu.

O defeito visível está na paleta compartilhada de 7 cores. O preto opaco, palavra CRAM 0, é a 8ª cor nos dois lutadores: 2400 pixels no Ken e 2320 no Ryu. A seleção só por frequência deixava o contorno de fora. Nos quadros de papel, 34 dos 39 do Ken perdiam 8% ou mais das arestas de contraste (2889 de 19479). No Ryu, 13 dos 40 (1624 de 22694). O cinto e o contorno do Ryu somem em parte dos quadros. No Ken o contorno some dentro do gi vermelho em mais quadros.

A correção reserva a cor mais escura e a mais clara, preto incluído, e cede o lugar da duplicata mais próxima. No mesmo conjunto a perda cai para 2140 arestas no Ken e 1585 no Ryu. O código está em `scene_cut._palette_codebook`.

A ROM com essa paleta é `out/rom/palette_reserve_20261023.sms`, 458752 bytes, SHA-256 `f9ef0e27eef5e29d530b0fa4e5c8325bd8df84a1ab6e7d93e77873f40a2b76cb`. O corte está em `out/generated/palette_reserve_20261023/`, 48 poses do Ryu e 45 do Ken, 24 banks. A palavra de paleta dentro da ROM, no offset 12311, é `00 1A 1B 16 3F 05 00 02 00 02 07 2B 0B 3F 00 16`. O branco `3F` e o preto opaco `00` ocupam um slot visível de cada lutador. A paleta anterior `00 1A 1B 16 2A 05 2B 02 00 02 07 2B 0B 1B 2F 16` não aparece nesse binário. A ROM do piloto `9008505c…` e a de produção `087df676…` permanecem nos arquivos de origem. `src/main.c` e `.mddev/project.json` vivos continuam apontando para `ryu_ken_cross`. Comparação: `out/logs/palette_reserve_20261023_compare.json`. Sem captura de emulador nesta ROM.

As folhas PNG gravavam o índice 0 com a cor do ACT e sem transparência. No Ryu essa cor é magenta `(255, 0, 255)`. No Ken é preto, e o buraco lia como mancha. `_write_png` agora grava transparência no índice 0. As folhas já escritas ficam como estão.

A amostragem abriu 26 pixels transparentes novos no Ken (9 sprites) e 44 no Ryu (15 sprites). Fechar esses pontos por votação criaria pixel onde a fonte tem vão. Essa correção não entrou.

O piloto continua `buildado`. Sem framebuffer aceito, sem FPS e sem entrega visual.

O dono viu a ROM reservada mais escura e com menos acuidade. Na paleta `ken1`/`ryu02` dos 12 papéis, a média dos pixels opacos cai de 115,9 para 110,2 no Ken e de 142,3 para 137,5 no Ryu. O creme do Ken, 4840 pixels, luma 246, ia para o rosa, luma 195, porque o índice menor ganhava o empate de distância com o branco. A regra nova mantém as sete cores mais frequentes. Um contorno de fora só entra no lugar de um tom abaixo de luma 100, que não seja a cor mais usada, sem aumentar o erro quadrático e sem derrubar a média de todos os pixels opacos em mais de 1. O destaque a um canal do branco permanece. No empate, fica o vizinho de brilho mais próximo. Nestes dois lutadores o livro volta a ser o da frequência: Ryu `1A 1B 16 2A 05 2B 02`, Ken `02 07 2B 0B 1B 2F 16`. O preto opaco continua fora. O cinto fica no vermelho escuro mais próximo.

A ROM com essa paleta é `out/rom/palette_luma_20261023.sms`, 458752 bytes, SHA-256 `6fb424a3ddf32002d5de9c27685c1387fa89d4205365b344ba64fe8c866cd873`. O corte está em `out/generated/palette_luma_20261023/`, 48 poses do Ryu e 45 do Ken, 24 banks. A palavra de paleta dentro da ROM, no offset 12311, é `00 1A 1B 16 2A 05 2B 02 00 02 07 2B 0B 1B 2F 16`. A sequência escura `00 1A 1B 16 3F 05 00 02 00 02 07 2B 0B 3F 00 16` não aparece. O header do corte tem o mesmo SHA do piloto (`3be5a775…`). A imagem de banks é outra: `ec22ad12f88b8fa720e7bbcf9cb63f3072f359af019f53e80d924f7348375423`. A ROM reservada `f9ef0e27…`, a piloto `9008505c…` e a de produção `087df676…` permanecem. `src/main.c` e `.mddev/project.json` vivos continuam em `ryu_ken_cross`. Comparação: `out/logs/palette_luma_20261023_compare.json`. O arquivo `palette_luma_20261023.sms` não foi aberto neste lote. O arquivo irmão de mesmo byte, descrito abaixo, é outro caminho.

## Lote do par — 2026-10-23

A cena tem dois lutadores em sprite puro. Oito colunas são o teto de um. O idle deste corte, depois da fração, continua na faixa já vista: o quadro de boot mede 32×56 e a maior célula neutra mede 32×64. O corpo não foi encolhido de novo. O golpe que não cabe no par sai da escala uniforme e fica na lista.

A fração aplicada nos dois é framebuffer `x=2/3` `y=6/7` e extra `2/3`, porta `idle_to_4`. O idle do framebuffer ainda ocupa 6 colunas de SAT; 4/6 reduz para 2/3. `within_8_ratio` ficou no relatório: Ryu 0,8052 (124/154) e Ken 0,77 (77/100). `pose_near` 0,69 não decidiu a escala. Com arte já `pre_scaled`, o motivo de fidelidade nomeia `framebuffer x=2/3 y=6/7 extra=2/3`. O corte novo não contém a string `downscale1:4`. `ratio.numerator/denominator` é só a extra 2/3; o campo `meaning` diz que não é a escala 40/49.

Antes de mudar a fração, a ROM piloto `9008505c…` foi aberta numa sessão privada. O framebuffer 256×192 dos dois idles está em `out/evidence/pose_budget_20261023_idle_256x192.png`, 1667 bytes, SHA-256 `64f5b9451439b5c37e4644f9f067bd9f2c6c80e23a1564e3b19ebff0f7e98800`. Os sprites saem. O runtime não foi alterado. As listras verticais do Ken continuam.

O corte novo está em `out/generated/pose_budget_pair_20261023/`. Os diretórios seguem `p1_ken` (corte do Ryu) e `p2_ryu` (corte do Ken). Nenhum papel obrigatório perdeu o quadro: o golpe largo permanece na ROM porque o runtime ainda chama o papel, e ao mesmo tempo entra em `case_by_case`. A lista completa de ações está em `versus_scene_manifest.json`, chave `fighter_scale`.

Pico de SAT do quadro mais largo de cada papel, lido no META emitido, modo tall, célula em branco já omitida:

| Papel | Ken (ação, SAT, px, células) | Ryu (ação, SAT, px, células) |
|---|---|---|
| idle | 0, 4, 32×56, 16 | 0, 4, 32×56, 16 |
| walk_f | 20, 4, 32×56, 16 | 20, 4, 32×56, 16 |
| walk_b | 21, 4, 32×64, 16 | 21, 4, 32×64, 16 |
| jump | 41, 4, 32×64, 14 | 41, 4, 32×64, 14 |
| crouch | 11, 4, 32×40, 12 | 11, 4, 32×40, 12 |
| guard | 120, 4, 32×56, 16 | 120, 4, 32×56, 16 |
| punch | 250, 6, 48×56, 17 — caso a caso | 260, 5, 48×56, 17 — caso a caso |
| hp | 450, 7, 56×48, 16 — caso a caso | 280, 6, 48×64, 17 — caso a caso |
| kick | 200, 6, 48×64, 20 — caso a caso | 200, 6, 48×64, 20 — caso a caso |
| hk | 220, 6, 56×56, 18 — caso a caso | 240, 6, 48×56, 18 — caso a caso |
| special | 1000, 6, 56×48, 18 — caso a caso | 1000, 4, 40×56, 15 — incluído |
| ko | 5080, 8, 64×32, 15 — caso a caso | 170, 4, 32×56, 16 — incluído |

Ken incluído: 59 ações, nenhum golpe dos doze papéis. Ken caso a caso: 41 ações. Ryu incluído: 77, entre elas special 1000 e ko 170. Ryu caso a caso: 77. Conta de ações do corpo: Ken 100, Ryu 154.

FX excluído do corte, pico de SAT acima de 3 depois da fração do corpo. Ryu, 92 sprites: 1150 (8), 1160 (3), 1250 (4), 1260 (3), 3050 (8), 8010 (2), 8020 (5), 8030 (4), 8050 (4), 8060 (5), 8210 (12), 8220 (7), 8230 (4), 8300 (4), 8310 (4), 8330 (10), 8400 (5). O `g8400` imagem 3 mede 112×24, SAT 12, largura padded 14 colunas. As imagens 0, 1, 2 e 4 do mesmo grupo também saem. Ken, 4 sprites: grupo 1001 (1) e 1002 (3), todos com SAT 4. Os grupos declarados 8000, 8040, 8320 e 8410 não tiveram sprite acima de 3 colunas e esta regra não os retirou. Nenhum deles foi desenhado no plano de fundo.

Eixo contra a sola opaca e caixa hurt contra o corpo, no primeiro quadro de corpo do idle e do soco de cada um. `sole_minus_axis` é a linha opaca de baixo menos `axis_y`. O padding duplo de 8 px foi isolado cortando o vão da primeira passada antes da extra 2/3.

| Quadro | Sprite | Fonte | Depois do framebuffer | Depois da extra | Cortar o pad e escalar | Hurt menos sola, fonte → final |
|---|---|---:|---:|---:|---:|---|
| Ken idle | g0 imagem 0 | −1 | 0 | −1 | −1 | 0 → 0 |
| Ken punch | g230 imagem 0 | −1 | −1 | −1 | −1 | 2 → 2 |
| Ryu idle | g0 imagem 1 | +1 | 0 | −1 | −1 | 0 → 2 |
| Ryu punch | g260 imagem 0 | 0 | −1 | −1 | 0 | 0 → 1 |

No Ken o pad não move a sola em relação ao eixo. No Ryu idle a diferença de 2 px entre a fonte (+1) e o resultado (−1) continua igual depois de cortar o pad: é a amostragem vizinho-mais-próximo que perde a linha de baixo, não o padding. No Ryu punch o pad responde por 1 px (o corte do pad devolve 0). O pedido era corrigir só acima de 1 px. Nada foi movido no sampler, no eixo nem na hurtbox.

> **Correção de medida (fecho de 2026-10-23):** esta tabela usou `sprite.axis_y` e ignorou `frame.y`. O `AXIS` emitido já inclui `frame.y`; refeita com `AXIS_y + linha da sola`, a hurt do Ryu idle fica em **+1 px**, não +2. A tabela corrigida e a decisão de não alterar o sampler estão na seção «Fechamento — quadro residente, composição legal e sola».

`audit_sprite_line_sim.py --self-check` imprimiu `[SELF-CHECK OK]` antes da leitura. Os três pares incluídos, mesmo Y, tall 8×16, zero violações: idle/idle 32 sprites, pico 8; Ken idle + Ryu special 30 sprites, pico 8; Ryu special + Ryu ko 30 sprites, pico 8. Evidência dos casos, sem reprovar o lote: Ken idle + Ken punch, 33 sprites, pico 10, 5 violações; Ken ko + Ryu idle, 31 sprites, pico 12, 5 violações. Relatório: `out/logs/pose_budget_pair_20261023/line_summary.json`.

| ROM | Bytes | SHA-256 | Banks |
|---|---:|---|---:|
| `out/rom/luta_mugem_rev2.sms` | 851968 | `087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65` | 49 |
| `out/rom/pose_budget_20261023.sms` | 458752 | `9008505cb82232e42d1b57d3ecb852af70f566625995cfd3cb5b526b277b1eba` | 24 |
| `out/rom/pose_budget_pair_20261023.sms` | 458752 | `6fb424a3ddf32002d5de9c27685c1387fa89d4205365b344ba64fe8c866cd873` | 24 |

A ROM do par é byte a byte igual a `out/rom/palette_luma_20261023.sms`. A imagem de banks é `ec22ad12…`, 393216 bytes, 24 banks. O arquivo de luma não foi sobrescrito e não foi o caminho capturado. A reservada `f9ef0e27…` permanece. `src/main.c` e `.mddev/project.json` vivos continuam em `ryu_ken_cross`, 49 banks. A compilação usou cópia temporária.

Framebuffer 256×192 dos dois idles desta ROM: `out/evidence/pose_budget_pair_20261023_idle_256x192.png`, 1658 bytes, SHA-256 `50beed8b55d73ff60f90384f52d60008e12e9d58070f8683f96209430e7a992a`. Sessão `387f8561097d44c4847e1f263523a81f`, encerrada. Ryu à esquerda, Ken à direita, fundo preto. As listras do Ken continuam. Status deste framebuffer: `testado_em_emulador`. Não é entrega visual.

`measure_worst_frame.py` sem janela de usuário, sonda `0xC800`, devolveu `sem_lastro`: frame 2035, `done` 0, motivo “janela worst-frame incompleta ou sem selo”. JSON: `out/evidence/sessions/387f8561097d44c4847e1f263523a81f/worst_frame/pose_budget_pair_worst.json`. Menos banks não é FPS. `validado_budget` fica proibido. Sem claim de 60 fps, áudio ou gameplay. Sem ID de lição e sem seção nova em `SMS_GLOBAL.md`.

Testes do motor neste fechamento: `test_display_fit.py`, `test_sms_budget_synthetic.py`, `test_scene_cut_scale_order.py` e `test_scene_cut_palette_binding.py`, 47 passed.

## Fechamento — quadro residente, composição legal e sola

Data: 2026-10-23. ROM de prova: `out/rom/pose_budget_settled_20261023.sms`, 458752 bytes, SHA-256 `698e58ed5a0e9256cf2497783b5b0a4343464c15138ce5783c5b9fd98879b13a`, 24 banks. A produção `087df676…` e as outras três ROMs do bloco não foram tocadas. O gate foi compilado numa cópia temporária dos 24 banks; o diff está em `out/logs/pose_budget_settled_20261023/composition_gate/main_c_composition_gate.patch` e o header derivado em `out/generated/pose_budget_pair_20261023/versus_composition_gate.h` (SHA-256 `1da1e952…`). `src/main.c` e `.mddev/project.json` vivos continuam em `ryu_ken_cross`; nada foi commitado ou empurrado.

### Quadro residente

O binário `6fb424a3…` usa o ramo `LUTA_PROFILE 1`, que emite a pose residente. A prova da pose residente foi feita no ROM com gate. No frame **500**, as duas poses pedidas já estavam residentes:

| Sonda | P1 | P2 |
|---|---:|---:|
| desejada | 5 | 49 |
| residente | 5 | 49 |
| submetida | 5 | 49 |
| apresentada | 5 | 49 |

`_SpriteNextFree` = 32: **16 células P1 + 16 células P2**, contra as 16 células do idle. A SAT ocupa x 69–100 no P1 e x 142–173 no P2, nos mesmos Y 105/121/137/153. O Ken fecha o corpo nesse quadro; a listra anterior era pose não residente/upload incompleto, não ordem de tile. PNG: `out/evidence/sessions/a40818afa1a5468da0ccbcf4735fede7/resident_gate_frame500.png`, SHA-256 `7281231d…`, captura informativa 256×192. A captura anterior de frame 489 (`796b7149…`) fica como histórico; a de 500 é a prova estável.

### Composição legal

O idle permanece em 4 colunas. O gate deriva do META emitido (P1 `_META`, P2 `_P2_METAL`): uma pose só é exibida ao lado do idle quando nenhuma linha dela carrega mais de 4 células 8×16. Das 93 poses do corte, **25** passam de 4 células por linha. Por anim, caem P1 6/7/8/9 (punch, hp, kick, hk) e P2 6/7/8/9/10/11 (punch, hp, kick, hk, special, ko). O gate está em `set_role()`: papel derrubado não altera o papel corrente, o dado continua no corte e a recusa é contada. A prova emulada no frame 500 registrou `dropped_from_composition=2`, `block_p1=1` (role 7, 6 células), `block_p2=1` (role 7, 7 células); nenhuma coluna foi omitida e o idle não encolheu.

Dez pares medidos com `audit_sprite_line_sim.py` (self-check antes da leitura, mesmo Y, tall 8×16, transparente omitido):

| Par | Pico | Violações | Veredito |
|---|---:|---:|---|
| idle / idle | 8 | 0 | legal, 32 sprites |
| Ken punch 250 + Ryu idle | 10 | 5 | derrubado |
| Ken hp 450 + Ryu idle | 11 | 5 | derrubado |
| Ken kick 200 + Ryu idle | 10 | 5 | derrubado |
| Ken hk 220 + Ryu idle | 10 | 5 | derrubado |
| Ken special 1000 + Ryu idle | 10 | 5 | derrubado |
| Ken ko 5080 + Ryu idle | 12 | 5 | derrubado |
| Ryu punch 260 + Ken idle | 9 | 5 | derrubado |
| Ryu hp 280 + Ken idle | 10 | 5 | derrubado |
| Ryu kick 200 + Ken idle | 10 | 5 | derrubado |
| Ryu hk 240 + Ken idle | 10 | 5 | derrubado |

`dropped_from_composition`: `P1_PUNCH`, `P1_HP`, `P1_KICK`, `P1_HK`, `P2_PUNCH`, `P2_HP`, `P2_KICK`, `P2_HK`, `P2_SPECIAL`, `P2_KO`. O relatório com pico, frame, ação e células por linha está em `out/logs/pose_budget_settled_20261023/composition_gate/dropped_from_composition.json`. Ryu special 1000 e Ryu ko 170 continuam legais no gate (máximo 4 células/linha), mas não são os golpes largos deste lote.

### Sola e hurt — correção da medida

A tabela anterior desta seção usou `sprite.axis_y` e ignorou `frame.y`; o `AXIS` gerado já é `frame.y - sprite.axis_y`. Refazendo com o `AXIS` emitido e a hurtbox escalada pelos mesmos dois passes:

| Quadro | `AXIS_y` | linha da sola | `AXIS_y + sola` | hurt bottom | hurt − sola |
|---|---:|---:|---:|---:|---:|
| Ryu idle F0 | −53 | 53 | 0 | 1 | **+1** |
| Ryu punch F0 | −56 | 59 | 3 | 0 | −3 |
| Ken idle F0 | −53 | 53 | 0 | −1 | −1 |
| Ken punch F0 | −57 | 60 | 3 | 1 | −2 |

A premissa de “2 px” não se reproduz: a medida corrigida do idle do Ryu é **1 px**, não 2. A linha de origem do Ryu idle realmente não é amostrada pelo `_sample` atual, mas os quatro amostradores testados no pipeline real de dois passes (`current`, `ceil`, `full`, `src_len`) **não movem a linha da sola do Ryu**; `full` move a sola do Ken em 1 px e não fecha o Ryu. Como a correção não traz a hurt do Ryu de volta à sola, o sampler, o eixo e a hurtbox ficam **inalterados**. A diferença é de arredondamento/axis, não de padding; nenhuma hitbox nova foi inventada.

### Pior quadro

O pior quadro só rodou depois de o Ken fechar. Na ROM final com gate: `derramou`, `vline_min=4`, `vovf_delta=1740`, `snapshot done=1`, `frames_rom_final=4079`, JSON `out/evidence/sessions/a40818afa1a5468da0ccbcf4735fede7/worst_frame/worst_frame_gate_final.json`. Na ROM pré-gate `c45dbd4a…`: `derramou`, `vline_min=2`, `vovf_delta=1770`, `snapshot done=1`, frame 3946. O valor 144 que aparecia no resumo anterior era o `vline` do snapshot, **não** o `vline_min` selado. As duas ROMs derramam; o gate não comprou orçamento. `validado_budget` continua proibido, e 24 banks continuam medindo tamanho, não FPS.

Status deste lote: `testado_em_emulador`, com o PNG do frame 500. Sem entrega visual, sem FPS, sem áudio e sem gameplay. Nenhum ID de lição; `SMS_GLOBAL.md` e o ledger não foram alterados.

Registro para curadoria futura: `doc/curation/2026-10-23_pose_budget_fechamento_pb13_pb18.md` (narrativa) e `doc/curation/2026-10-23_pose_budget_fechamento_pb13_pb18.json` (índice). O pacote traz o inventário de SHA, o fechamento PB-13–PB-18, os dez pares, os dez papéis derrubados, a correção da sola, o pior quadro, sete aprendizados candidatos sem ID e as quatro ferramentas de medição implementadas e testadas. Promoção a lei da fábrica continua pendente de aprovação humana.

As ferramentas canônicas ficam em `tools/sms_wrapper/`: `audit_composition_gate.py` (25/93 poses; P1 anims 6–9, P2 anims 6–11), `audit_sole_alignment.py` (quatro quadros de referência: `+1`, `−3`, `−1`, `−2`), `measure_worst_frame.py` (schema `v2`, `sealed_field=vline_min`) e `audit_sprite_line_sim.py` (opt-in `--require-distinct-fighters`). Todas passam em `--self-check`; a regressão `mugen2sms/tests/test_measurement_gates_pose_budget.py` tem 8 testes. A varredura ampla de sola mede 93 quadros, mas o lote continua julgado pelos quatro de referência; a ferramenta mede, não classifica. Nada disso reabriu emulador nem autoriza `validado_budget`.
