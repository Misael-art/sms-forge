# Concluir Alis jogável na Cena 02 de Master of Fighters

Você é responsável pela implementação, arte, integração e revisão de **Alis contra Alis** em `SMS_projects/master_of_fighters`. Entregue uma ROM em que duas pessoas possam controlar Alis, trocar os doze golpes abaixo, defender, agarrar, cair e voltar ao combate. Conduza uma rodada de trabalho até o aceite, com os ciclos internos de correção necessários. A primeira animação bem-sucedida encerra somente a linha que ela demonstrou.

## 1. Comece do que já funciona

Leia o AGENTS.md, a memória, GDD, roteiro, especificação da cena, TDD, comandos e repertório do consumidor. Registre nos documentos donos a decisão atual de usar o espelho, os doze normais e o agarrão. Preserve as fontes e o ensaio com Hayato para comparação. Confira se há candidata posterior à b32 e identifique seu SHA antes de editar. Use a [curadoria da b32](../curation/2026-11-21_alis_espelho.json) e o [replay e matriz da Cena 02](../../SMS_projects/master_of_fighters/doc/scene02_hayato_alis_qa.md) para localizar o primeiro elo ainda sem prova.

Mantenha a identidade do concept autorizado e a física do salto aprovada pelo dono. Na b32 o ápice é de 78 px, o voo dura 20 ticks e a nova pressão de salto durante a recuperação pode preparar a próxima decolagem. Preserve marcha com transferência de peso, proporções, material do escudo, som distinto de espada, cruzamento e guarda por fase. Abra no repertório existente uma linha por ação e reação. Registre nesta ordem comando, postura, função tática, resposta do adversário, poses, caixas, som, caso de teste e prova da ROM final.

## 2. Faça o espelho funcionar desde a entrada normal da cena

Instancie Alis duas vezes com controles independentes. Revise a inicialização que deriva o rival de P1, a física e os buffers específicos de uma única Alis, os bancos, os endereços temporários, a ordem da SAT e as partes da espada compostas no fundo. Compartilhe arte imutável quando possível. Mantenha posição, face, vida, relógio, entrada, comando retido, estado de reação e propriedade dos efeitos por jogador. Pressione comandos diferentes no mesmo tick. Cruze, troque os lados, cause dano a apenas uma jogadora e reinicie o round.

Produza traje 1 para P1 e traje 2 para P2. A paleta física de sprites é compartilhada, com até 15 cores opacas e índice 0 transparente. Planeje duas combinações de índices dentro desse orçamento. Preserve leitura da pele, cabelo, lâmina e escudo. Mostre as duas Alis simultaneamente em tamanho nativo, juntas, separadas e após cruzarem. Teste se cada traje segue o controle e se mover uma espada recompõe corretamente o cenário da outra.

## 3. Complete os doze normais

| Postura | Botão 1 · toque | Botão 1 · sustentado | Botão 2 · toque | Botão 2 · sustentado |
|---|---|---|---|---|
| Em pé | Soco de guarda com escudo | Estocada forte de espada | Chute de distância | Chute de avanço |
| Abaixada | Soco rente ao escudo | Estocada ascendente | Chute baixo curto | Rasteira lateral |
| No ar | Soco aéreo de encontro | Estocada em descida | Chute de interceptação | Chute em mergulho |

Os nomes e a coreografia de partida vêm do repertório do projeto. A linha em pé já tem controles históricos. Implemente as oito entradas baixas e aéreas e revalide as quatro em pé. Registre qual limiar a ROM usa. Teste um tick antes, exatamente no limiar e um depois, soltura, botão mantido até o pouso e rearme. Resolva e documente a postura que vale quando o botão atravessa a decolagem ou o pouso. Verifique que o agarrão e o especial direcional preservam o acesso aos normais.

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

Use o **Giro com o escudo** e o comando proposto **frente + 1 + 2** como ponto de partida. Registre a janela de simultaneidade, precedência, alcance, estado elegível e consequência no vazio. Preserve a origem dessa escolha no GDD e nos comandos.

Faça uma folha de exposição com duas linhas sincronizadas. A atacante alcança, firma a pega, gira, solta e recupera o apoio. A vítima é capturada, perde o apoio, acompanha a pega, separa-se na soltura, cai, fica deitada e levanta conforme a regra. Marque a âncora da mão e o ponto correspondente no corpo da vítima, o último quadro preso, o primeiro livre e o evento único de dano. Desenhe sprites próprios para as fases em que a atuação muda. Mantenha legíveis rosto, equipamento e juntas durante a sobreposição.

Teste P1 agarrando P2 e depois P2 agarrando P1, nas duas orientações, no meio e junto à parede. Faça também uma tentativa um pixel fora do alcance e outra contra alvo inelegível. Verifique ausência de dano no vazio, ausência de teletransporte na parede e liberação de ambos os controles. Um vídeo contínuo deve mostrar captura, giro, soltura, queda, chão e primeiro comando aceito após a recuperação.

## 6. Aceite e iteração

1. Trabalhe em lotes jogáveis. Para cada falha, registre o primeiro quadro divergente, corrija a causa, repita o caso e então repita os vizinhos que ele pode ter quebrado. Comece com cache frio e repita após marcha, espadada, diagonal e guarda. Compare comando consumido, ação, pose pedida, residente, submetida e pixels. Se a ROM causar dano antes de exibir a fase ativa, reabra o golpe.
2. Examine a arte nos dois lados a 1×, com som e na velocidade real. Confira proporção anatômica, sola, mão/equipamento, cores por material, transparência, silhueta do rival e faixa do HUD. Capture no emulador o efeito de acerto, defesa, erro e queda conforme o contrato de cada ação. Ouça o PSG isolado e na troca completa. Registre a origem de arte e som. Mantenha gravação bruta para avaliar sincronismo.
3. Use o wrapper, os gates do projeto e uma sessão privada por vez. Compare testes por quadros com pelo menos um round contínuo por entrada normal. Identifique SHA, sessão, trecho do vídeo, resultado esperado e observado. Meça o pior quadro com as duas Alis sobrepostas, lâminas, efeitos, HUD e áudio. Confira scanlines, SAT, VRAM, VBlank e cadência funcional NTSC. Alvo de 60 FPS, piso de 58 em **cada** janela válida, sem arredondamento. Preserve os critérios de dispersão e a prova de lógica, input e apresentação da fábrica.
4. Na ROM final, feche todas as linhas dos doze normais, das reações e dos dois papéis do agarrão. Revise as demais poses previstas no GDD, incluindo idle, saída e retorno, marcha, virada, salto, defesas, especiais e transições ou cutscenes já autorizadas para Alis. Registre o que cabe nesta cena e mantenha rastreável cada obrigação posterior da personagem. Magias ou Super que permanecem propostas exigem decisão de design antes de produção.
5. Entregue caminho da ROM jogável e SHA, comandos para os dois jogadores, matriz completa com evidência por linha, vídeo, áudio bruto, medições, parecer visual e memória atualizada. Aponte onde o dono pode ver cada chute, a diferença entre cabeça e abdômen, o agarrão e a queda. Confira os sete eixos de entrega e o vínculo da arte ao binário. Se uma linha obrigatória falhar, continue o ciclo enquanto houver correção executável. Diante de um impedimento externo real, preserve a última candidata, a linha aberta, o primeiro quadro divergente quando houver e a condição exata para retomar. Reserve o status de entrega completa para o conjunto aprovado.
