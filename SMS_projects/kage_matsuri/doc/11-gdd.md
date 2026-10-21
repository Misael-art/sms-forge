# 11-gdd — kage_matsuri

> Design e escopo. **Autoridade #2 — "se não está no GDD, não entra."**

## Pitch (1 frase)
Fatia jogável de rua de matsuri: o ninja Kage corre, pula e encadeia um combo
de dois cortes contra samurais de festival, num palco colorido ao estilo
Asterix-SMS com tema Goemon.

## Gênero declarado
platformer

Eixos congelados da matriz: jump_buffer, coyote_time, colisao_1_way,
gravidade, scrolling. Nesta fatia: jump_buffer 4 frames, coyote 4 frames,
plataformas sólidas (sem 1-way — débito), gravidade por altura, palco
256×192 sem H-scroll (H-scroll — débito; LEFTCOLBLANK só quando o scroll
existir, L043).

## Loop central
Andar / pular / cortar (B1) → inimigo recua ou cai → avançar a rua até o
torii. Combo: segundo B1 na janela do primeiro corte vira o segundo golpe.

## 5 Leis Fundamentais
- **Agência**: d-pad move Kage; B1 corta; segundo B1 encadeia.
- **Feedback**: pose muda no golpe; samurai pisca e cai; lanternas e palco
  são o cenário, não o blob de gameplay.
- **Fluxo**: um corredor, dois samurais, torii no fim.
- **Consistência**: mesma tecla, mesmo deslocamento; gravidade por altura
  (L050), não por rótulo de estado.
- **Recompensa**: chegar ao torii com os samurais derrotados.

## Cenas planejadas
| # | Nome | Escopo em 1 linha | Status |
|---|------|-------------------|--------|
| 01 | rua_matsuri | palco 256×192, combo 2 hits, 2 samurais, vitória no torii | implementado |

## Escala (locked)
- Canvas 256×192.
- Kage 16×32 (SPRITEMODE_TALL, metasprite 2×2 de 8×16 = 4 SAT).
- Samurai 16×32 (idem). Pico de scanline: 6 (3 corpos × 2 sprites/linha).
- Não reduzir personagem para poupar tiles.

## Régua visual (não fonte de pixel)
Asterix Master System: cor saturada, palco denso, animação de caminhada
legível. Ganbare Goemon: tema de ninja/samurai de festival. Pixels do
cartucho são autorais (Imagine + tradução paleta mestra L055).

## Fora de escopo
- Boss, lojas, diálogo, mapa-mundo, 2P, YM2413.
- Mais de uma rua.
- Claim AAA.

## Teto de claims aprovado
protótipo jogável
