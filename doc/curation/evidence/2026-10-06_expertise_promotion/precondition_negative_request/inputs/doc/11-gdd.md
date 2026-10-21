# 11-gdd — laboratorio_01

> Escopo travado. **Se não está aqui, não entra.**

## Pitch (1 frase)
Laboratório de validação do SMSForge: uma cena interativa mínima que prova o
pipeline inteiro (gates → runtime → evidência) — não é um jogo.

## Cena 01 "boot_interativo" (escopo desta iteração)
1. Cursor-fixture (sprite 16×16, role=ui, declarado como FIXTURE de pipeline)
   movível com o d-pad na tela 256×192.
2. Contador de frames em hex no canto (base para medição futura de fps).
3. Spinner animado contínuo (prova de execução viva no viewport).

## 5 Leis Fundamentais — como atendem
- Agência: d-pad move o cursor visivelmente.
- Feedback: cursor responde 1:1 ao input; contador muda a cada frame.
- Fluxo: n/a (cena única de validação).
- Consistência: movimento fixo de 2px/frame nas 4 direções.
- Recompensa: n/a nesta cena.

## Cena 02 "sala do bloco" (F4 — primeiro gameplay real)
1. Campo 24×18 (moldura em 4..27,4..25) com 1 bloco 2×2 empurrável e 1 alvo 2×2.
2. Jogador (cursor 2×2) empurra bloco 1 célula por input (colisão AABB, sem atravessar paredes).
3. Vitória: bloco cobre alvo → borda pisca e contador congela; START reinicia.

## Fora de escopo (explícito)
- Áudio além do blip já entregue (F3).
- Sprites hardware (aguarda F1 fechar L006).
- Scroll / múltiplas salas.

## Cena 03 "cacador de sprites" (L006 em runtime — 2026-08-30)
1. Jogador = sprite 8x8 (hero, tile 128) movido por d-pad (SPRITEMODE_NORMAL — solucao L006).
2. Alvo = sprite animado (vai-e-vem), vitoria ao colidir.
3. Prova: sprites em runtime (evidencia cena03_sprites.png).

## Cena 04 "corredor estelar" (combina tudo — 2026-08-30)
1. Jogador sprite 8x8 (hero) movido por d-pad.
2. 3 inimigos (sprites 8x8) caindo, respawn; HP 3, game over + START reinicia.
3. Scroll BG horizontal com campo de estrelas.
4. Musica PSG rica (music_battle, 4 canais melodia+baixo+noise, PSGlib em loop).
5. HUD: HP + score (frame counter).
- Prova: cena04_sprites.png + audio_battle.wav (96% ativo, peak 9936).

## Eixos congelados — action_shooter (especialização)
- agencia: d-pad move o jogador 1 célula/frame.
- feedback_de_dano: hitstop (6f) + flash de invulnerabilidade + shake.
- sprites_8x8: jogador/inimigos/projétil (SPRITEMODE_NORMAL).
- scroll: BG horizontal com campo de estrelas.
- dificuldade_progressiva: velocidade dos inimigos cresce com o tempo.
- hitstop: congela a ação no impacto (game feel).
