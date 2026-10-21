# 11-gdd — pnt_16bit

> Design e escopo. **Autoridade #2 — "se não está no GDD, não entra."**

## Pitch (1 frase)
_(o jogo inteiro numa frase. Se não cabe, o escopo ainda não está travado.)_

## Gênero declarado
_(ex: action_platformer, puzzle, shmup. Precisa bater com `specialization` em
`.mddev/project.json` — `audit_specialization.py` compara os dois.)_

## Loop central
_(o que o jogador faz nos primeiros 10 segundos, repetidamente:
ação → resposta do sistema → consequência → nova decisão)_

## 5 Leis Fundamentais — como este jogo atende
- **Agência**: _(o input do jogador muda o mundo de forma visível?)_
- **Feedback**: _(toda ação tem resposta legível em <1 frame de percepção?)_
- **Fluxo**: _(dificuldade acompanha a competência crescente?)_
- **Consistência**: _(a mesma entrada produz o mesmo resultado, sempre?)_
- **Recompensa**: _(o que o jogador ganha por jogar bem?)_

## Cenas planejadas
| # | Nome | Escopo em 1 linha | Status |
|---|------|-------------------|--------|
| 01 | _(nome)_ | _(o que acontece)_ | documentado |

## Fora de escopo (explícito)
> Escrever o que NÃO entra é o que torna o escopo travável.
- _(item)_

## Teto de claims aprovado
_(o superlativo máximo que este projeto pode usar sobre si. `audit_claims.py`
reprova claim acima do teto. Comece humilde: "protótipo jogável".)_
