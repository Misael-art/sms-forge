# 11-gdd — openbor_sms_rev1

> Design e escopo. **Autoridade #2 — "se não está no GDD, não entra."**

## Pitch (1 frase)
Motor OpenBOR → Master System com primeiro produto: um **recorte jogável de
Golden Axe Legend (fase TOWN1, 1 jogador)** — andar em profundidade, atacar,
sofrer dano, cair e levantar — rodando de verdade no SMS e medido.

## Gênero declarado
`fighting` (beat 'em up de progressão, 1P primeiro). Mesmo gênero declarado em
`.mddev/project.json` (`specialization: fighting`) — `audit_specialization.py`
compara os dois. Não é jogo de rounds 1v1: ver eixos abaixo.

## Loop central
Andar pelo cenário com scroll (mundo horizontal + profundidade no chão) →
aproximar de inimigos → atacar com janelas de startup/active/recovery da fonte →
inimigo reage (dano, knockdown) → manter posição/ritmo → próximo grupo. A cada
10 segundos: movimento → ataque → resposta do sistema → reposicionamento.

## 5 Leis Fundamentais — como este jogo atende
- **Agência**: direções + 2 botões (proposta: ataque/pulo; direções e contexto
  para ações extra conforme a fonte); rota de pegar/soltar/arremessar/especial
  será registrada com conflitos no TDD quando existir.
- **Feedback**: dano/hitstop/knockdown legíveis no mesmo frame de percepção;
  hitstop medido, nunca presumido.
- **Fluxo**: dificuldade por fase/grupos do módulo, não por escalada arbitrária.
- **Consistência**: mesmo input → mesma pose/contato (prova input→pose→contato).
- **Recompensa**: progressão pela fase e domínio do combate.

## Eixos do gênero `fighting` neste recorte
- **hitboxes**: caixas de ataque/dano com profundidade, facing e frame ativo;
  sort visual não define colisão.
- **startup_active_recovery**: janelas por animação da fonte; `delay` OpenBOR
  convertido por regra racional declarada (nunca 1 delay = 1 frame VDP).
- **hitstop**: pausa curta de impacto; orçamento medido se adotado.
- **rounds**: **não há rounds** — o fluxo é por fase (combate → clear/derrota →
  continue/restart). Exceção declarada, não omissão.
- **specials**: conforme a fonte (magias/itens/comandos); rota de botões
  registrada antes de implementar.
- **guard**: conforme presença na fonte (defesa quando existir). Se a fonte não
  oferecer guard alcançável, registrar `dropped_by_owner` com a origem.

## Cenas planejadas
| # | Nome | Escopo em 1 linha | Status |
|---|------|-------------------|--------|
| 01 | TOWN1 (recorte GAL) | 1P × 1 inimigo → movimento/profundidade/pulo/ataque/dano/queda; cenário mínimo rastreado | documentado (O0) |
| 02 | bt_rescue (recorte BT) | segundo piloto: prova de generalização por dados (O7), perfil `bt_rescue` | fora do escopo imediato |

## Fora de escopo (explícito)
- Conversão do módulo completo / "OpenBOR completo" (O8 só com owners
  essenciais aceitos).
- 2P cooperativo: capacidade **separada**, com teste/orçamento próprios se
  entrar no contrato (nunca promovido com prova 1P).
- Conversão automática de áudio do PAK (WAV/BOR/OGG → PSG): áudio é fonte a
  **classificar/adaptar** com reautoria rastreável.
- YM2413/FM como dependência (opcional, só com ganho/custo demonstrados).
- Acabamento visual de grande estúdio, contagem de inimigos por suposição,
  taxa de quadros sem medição por ROM.

## Teto de claims aprovado
**"piloto técnico jogável (recorte), sem equivalência visual"** — até haver
ROM por hash com os 7 eixos de entrega provados.
