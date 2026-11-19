# Prompt para o próximo agente — Master of Fighters

```text
[Contexto SMS Carregado]

Aplique a metodologia do SMSForge ao Master of Fighters. Parta dos model sheets aprovados e leve um lutador até um duelo controlável e validado em uma ROM de Master System. Trabalhe na raiz registrada do SMSForge. Neste host Windows, ela é E:\misael\Projects\SMSForge. O consumidor é SMS_projects/master_of_fighters.

Comece pelo AGENTS.md e por tools/sms_wrapper/.agent/workflows/playable-fighter.md. Use as skills centrais sms-fighter-direction.md e sms-sprite-animation.md. No consumidor, confira o memory bank, GDD, especificação da cena, TDD, registro de arte e decisões vigentes do proprietário.

1. Escolha o par e fixe o ponto de partida.

Priorize Hayato como lutador focal, pois o corte curto já tem um controle de atuação e timing documentado. Confirme o papel, caminho, SHA e alcance da aprovação do model sheet, da escala e da sequência. Escolha um adversário autorizado pelo GDD cuja arte e estados permitam demonstrar defesa, dano e uma resposta jogável. J.J. é candidato se essas condições forem atendidas. Se outro par tiver evidência melhor, registre o motivo e prossiga com ele. Respeite o congelamento do Dr. Social.

Registre no handoff o par, a cena, o comando autorizado, a ação distintiva, a resposta esperada do rival e o primeiro elo ainda sem prova. Preserve como controle cada combinação de desenhos e exposições já aceita.

2. Construa o menor duelo completo.

O jogador deve conseguir partir da guarda, mover-se para entrar ou sair de alcance, executar a ação pelo controle de dois botões e recuperar o comando. O adversário deve poder sofrer o acerto, defender e responder em uma situação reproduzível. Use os comandos e as regras do GDD. Um limiar de botão presente em um visualizador experimental continua provisório até haver decisão de design aplicável ao duelo.

Mantenha os dois lutadores na régua comum do elenco. Confira altura anatômica, chão, proporções, materiais, silhueta, mão e equipamento nas duas faces. Preserve a personalidade pelo modo de apoiar o peso, avançar, ameaçar e recuperar a guarda. Trabalhe primeiro no gesto que falhar durante a reprodução em velocidade normal. Ajuste a exposição quando o problema for ritmo e redesenhe a pose quando o problema for trajetória ou leitura.

3. Ligue o desenho à lógica do golpe.

Rode o self-check de audit_animation_contract.py e gere a folha de exposição com --manifest e --exposure-sheet. Para o corte documentado de Hayato, use hayato_animation_contract_v4.json e a sequência hayato_short_cut depois de confirmar que continuam vigentes. Só acrescente --active-window quando houver uma hipótese explícita no contrato de combate ou no TDD.

Acompanhe separadamente o input consumido, o estado lógico, a pose solicitada, a pose residente, a pose apresentada, as caixas de contato, a reação do defensor e o primeiro tick em que cada lado volta a agir. Meça a composição mais cara com os dois lutadores, cenário e HUD antes de ampliar o atlas. Verifique SAT, sprites por linha, VRAM, streaming e pior VBlank.

4. Prove o duelo na ROM.

Use o wrapper oficial, uma build candidata em destino novo e uma sessão privada de Emulicious. Confira os recursos do host antes da carga, comece com um job e preserve a baseline. Vincule fonte, asset convertido, símbolo e ROM por SHA.

Execute pelo menos estes casos com pré-condição e resultado esperado definidos antes da coleta:

- Acerto de perto e no limite. Confira a pose apresentada, o tick de contato, o dano e a reação.
- Erro logo além do alcance. Confira a ausência de dano, a recuperação e a oportunidade real de resposta.
- Defesa e contra-ataque. Meça quando cada lado volta a agir e se a resposta alcança o atacante após o recuo.
- Troca de face e de P1/P2. Repita o caso crítico junto ao canto e verifique espelhamento, prioridade visual e coerência do resultado.

Use trace e framebuffer para localizar as fronteiras. Use vídeo em velocidade normal para julgar atuação e legibilidade. Meça a cadência em execução contínua, com input, lógica, apresentação e áudio sob carga real. O alvo é 60 FPS, com piso de 58 em cada janela válida, sem arredondamento, pelo menos duas janelas e dispersão máxima de 2 FPS. Registre o pior frame.

5. Corrija e feche com evidência.

Se um caso falhar, identifique a primeira divergência entre o esperado e o observado, corrija a causa e repita o caso e as regressões afetadas. Preserve os controles aceitos. Uma ROM alterada exige evidência fresca do novo SHA. Avance enquanto houver uma correção segura dentro do recorte autorizado.

Entregue a ROM candidata e seu SHA, o registro da build, a tabela dos casos com esperado e observado, os traces, vídeo, áudio, medições de FPS e orçamento, parecer visual e confirmação de limpeza da sessão. Atualize o memory bank e o handoff existentes. Declare “duelo validado” somente quando os sete eixos da fábrica, o vínculo asset→ROM e a época visual de entrega estiverem comprovados para esse mesmo binário. Se faltar um aceite humano ou existir um bloqueio concreto, indique o eixo pendente e a evidência exata que permitirá retomá-lo.
```
