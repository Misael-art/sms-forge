# Concluir Alis jogável na Cena 02 de Master of Fighters

Você é responsável pela implementação, arte, integração e revisão de **Alis contra Alis** em `SMS_projects/master_of_fighters`. Entregue uma ROM em que duas pessoas possam controlar Alis, trocar os doze golpes abaixo, defender, agarrar, cair e voltar ao combate. Conduza uma rodada de trabalho até o aceite, com os ciclos internos de correção necessários. A primeira animação bem-sucedida encerra somente a linha que ela demonstrou.

## 1. Comece do que já funciona

Leia o AGENTS.md, a memória, GDD, roteiro, especificação da cena, TDD, comandos e repertório do consumidor. O espelho e o build integral estão registrados na b53. Comece pela [curadoria da b53](../curation/2026-11-22_alis_pouso_e_puxada.json) e pela [matriz do jogo](../../SMS_projects/master_of_fighters/doc/scene02_alis_espelho_qa.md). Confirme se há um SHA posterior. Use a b32 para a física do salto, a b49 para o lançador com foco interno e a b52 para a consequência do chute e a Puxada com Escudo. Preserve os oito pousos e as duas pressões novas demonstrados na b53. Feche os eixos abertos nessa ROM ou na sua sucessora: capture o PSG isolado e confirme som nos eventos do replay, atribua o atraso funcional por etapa e repita o duelo aéreo que atrasava quatro reações na b47. Registre a cobertura do controle físico quando disponível.

Mantenha a identidade do concept autorizado e a física do salto aprovada pelo dono. Na b32 o ápice é de 78 px, o voo dura 20 ticks e a nova pressão de salto durante a recuperação pode preparar a próxima decolagem. Preserve marcha com transferência de peso, proporções, material do escudo, som distinto de espada, cruzamento e guarda por fase. Abra no repertório existente uma linha por ação e reação. Registre nesta ordem comando, postura, função tática, resposta do adversário, poses, caixas, som, caso de teste e prova da ROM final.

## 2. Faça o espelho funcionar desde a entrada normal da cena

Revalide as duas instâncias e os controles independentes já existentes. Revise a inicialização, a física e os buffers por jogadora, os bancos, os endereços temporários, a ordem da SAT e as partes da espada compostas no fundo. Compartilhe arte imutável quando possível. Mantenha posição, face, vida, relógio, entrada, comando retido, estado de reação e propriedade dos efeitos por jogador. Pressione comandos diferentes no mesmo tick. Cruze, troque os lados, cause dano a apenas uma jogadora e reinicie o round.

Preserve o traje rosa de P1 e o verde de P2. A paleta física de sprites é compartilhada, com até 15 cores opacas e índice 0 transparente. Planeje duas combinações de índices dentro desse orçamento. Preserve leitura da pele, cabelo, lâmina e escudo. Mostre as duas Alis simultaneamente em tamanho nativo, juntas, separadas e após cruzarem. Teste se cada traje segue o controle e se mover uma espada recompõe corretamente o cenário da outra.

## 3. Complete os doze normais

| Postura | Botão 1 · toque | Botão 1 · sustentado | Botão 2 · toque | Botão 2 · sustentado |
|---|---|---|---|---|
| Em pé | Soco de guarda com escudo | Estocada forte de espada | Chute de distância | Chute de avanço |
| Abaixada | Soco rente ao escudo | Estocada ascendente | Chute baixo curto | Rasteira lateral |
| No ar | Soco aéreo de encontro | Estocada em descida | Chute de interceptação | Chute em mergulho |

Os nomes e a coreografia de partida vêm do repertório do projeto. Os doze normais já têm registros nos dois controles. Revalide o repertório completo na candidata integral e corrija cada linha que divergir. Registre qual limiar a ROM usa. Teste um tick antes, exatamente no limiar e um depois, soltura, botão mantido até o pouso e rearme. Resolva e documente a postura que vale quando o botão atravessa a decolagem ou o pouso. Verifique que o agarrão e o especial direcional preservam o acesso aos normais.

Para cada golpe desenhe preparação, fase ativa e recuperação com atuação que mostre direção, alcance e compromisso. Use os pivôs da ficha e marque por quadro caixa ofensiva, áreas vulneráveis, caixa de corpo e zona atingida. Diferencie fraco e forte na silhueta, tempo, alcance e risco. Registre dano e primeiro tick livre de cada atriz. Confira acerto, defesa compatível, erro no limite +1 px e oportunidade de resposta. No ar, exercite subida ou descida conforme o golpe, mudança de lado e pouso durante a recuperação. Cada golpe simples aplica dano uma vez por execução.

## 4. Desenhe o que a vítima faz

| Evento provocado em jogo | Leitura que deve aparecer no framebuffer |
|---|---|
| Acerto na cabeça em pé | Cabeça e ombros cedem a partir do contato alto. |
| Acerto no abdômen em pé | Tronco fecha sobre a região atingida. O perfil difere da reação alta. |
| Acerto em Alis abaixada | Reação baixa com apoio e altura coerentes até a retomada. |
| Impacto na guarda em pé e na guarda baixa | Escudo recebe a carga e o corpo absorve o impacto na respectiva altura. |
| Impacto na guarda aérea | Escudo e corpo reagem durante o arco. Mostrar contato, continuação e pouso. |
| Queda, chão e levantada | Mostrar perda de apoio, descida, impacto, pose deitada por tempo legível e retomada do controle. No KO, respeitar o encerramento do round. |

Defina como o árbitro escolhe cabeça ou abdômen quando uma caixa alcança as duas regiões. Registre o estado anterior ao contato, a zona resolvida, dano ou bloqueio, recuo e pose publicada no tick. Reproduza o mesmo ataque contra guarda correta e contra vítima vulnerável. Exiba a diferença entre levantar o escudo e receber impacto. Teste o caso aéreo com uma atacante capaz de alcançar a vítima.

## 5. Faça o agarrão como uma ação de duas personagens

Revalide a **Puxada com Escudo** com frente e as duas pressões novas de 1 e 2 na mesma leitura. Alis alcança, pega pelo braço, puxa em solo de 32 para 24 px, firma o apoio e avança o escudo. A rival conserva o lado, recebe um único dano no impacto, recua em dois passos e cai. No centro, o recuo medido na b52 foi 14 px. Perto da parede, confira quanto a arena permite recuar. Mostre a pose própria de recolhimento da atacante quando a rival já estiver no chão e acompanhe a levantada até o primeiro comando aceito.

Faça P1 e P2 alternarem os papéis e as faces, no centro e no canto. Confira a mão de pega, a exposição do escudo e da reação no mesmo impacto, a tentativa a 33 px e o alvo aéreo inelegível. Preserve as duas trajetórias na folha de exposição. Revise as proporções contra a guarda e o concept v4 em cada fase, inclusive a última.

No chute aéreo forte, comprove 12 ticks de impacto e recuo de até 7 px observado no alvo em pé. O leve tem 8 ticks. Registre a volta ao controle e exercite a defesa aérea. No pouso de cada normal, compare última leitura no ar e primeira em solo, a caixa desativada, o botão antigo mantido até soltar e um botão novo aceito na leitura do pouso. Mostre o próximo golpe na sua soltura. Os dois trajes precisam preservar peitoral índigo, lâmina ciano separada, pele e bracelete também nos pixels do fundo.


## 6. Aceite e iteração

1. Trabalhe em lotes jogáveis. Para cada falha, registre o primeiro quadro divergente, corrija a causa, repita o caso e então repita os vizinhos que ele pode ter quebrado. Comece com cache frio e repita após marcha, espadada, diagonal e guarda. Compare comando consumido, ação, pose pedida, residente, submetida e pixels. Se a ROM causar dano antes de exibir a fase ativa, reabra o golpe.
2. Examine a arte nos dois lados a 1×, com som e na velocidade real. Confira proporção anatômica, sola, mão/equipamento, cores por material, transparência, silhueta do rival e faixa do HUD. Capture no emulador o efeito de acerto, defesa, erro e queda conforme o contrato de cada ação. Ouça o PSG isolado e na troca completa. Registre a origem de arte e som. Mantenha gravação bruta para avaliar sincronismo.
3. Use o wrapper, os gates do projeto e uma sessão privada por vez. Compare testes por quadros com pelo menos um round contínuo por entrada normal. Identifique SHA, sessão, trecho do vídeo, resultado esperado e observado. Meça o pior quadro com as duas Alis sobrepostas, lâminas, efeitos, HUD e áudio. Confira scanlines, SAT, VRAM, VBlank e cadência funcional NTSC. Alvo de 60 FPS, piso de 58 em **cada** janela válida, sem arredondamento. Preserve os critérios de dispersão e a prova de lógica, input e apresentação da fábrica.
4. Na ROM final, feche todas as linhas dos doze normais, das reações e dos dois papéis do agarrão. Revise as demais poses previstas no GDD, incluindo idle, saída e retorno, marcha, virada, salto, defesas, especiais e transições ou cutscenes já autorizadas para Alis. Registre o que cabe nesta cena e mantenha rastreável cada obrigação posterior da personagem. Magias ou Super que permanecem propostas exigem decisão de design antes de produção.
5. Entregue caminho da ROM jogável e SHA, comandos para os dois jogadores, matriz completa com evidência por linha, vídeo, áudio bruto, medições, parecer visual e memória atualizada. Aponte onde o dono pode ver cada chute, a diferença entre cabeça e abdômen, o agarrão e a queda. Confira os sete eixos de entrega e o vínculo da arte ao binário. Se uma linha obrigatória falhar, continue o ciclo enquanto houver correção executável. Diante de um impedimento externo real, preserve a última candidata, a linha aberta, o primeiro quadro divergente quando houver e a condição exata para retomar. Reserve o status de entrega completa para o conjunto aprovado.
