# workflow: new-project

```sh
tools/sms_wrapper/new_project.sh <slug>
```
1. Instancia `SMS_projects/<slug>/` do modelo (`.agent` local não sobrescrito).
2. Preencher `doc/11-gdd.md` com o loop de jogo, controles, modos/telas,
   condição de resultado e exclusões explícitas — humano aprova o escopo.
   Não presumir fase, cenário ou modo que não esteja no GDD.
3. Preencher `doc/15-tdd.md`: FSM e entradas, update por frame, feedback
   visível, pools/layout VRAM, custo CPU, RAM/ROM/banking e medidas de pior
   quadro. Nomear quais telas coexistem e quais carregam recursos separados.
   Se houver múltiplos estados, definir entrada/saída, owners e dados que
   persistem em `sms-state-transitions.md`.
4. Primeiro ciclo: `./build.sh` (deve falhar honesto se toolchain ausente).
5. Antes de criar o elenco ou o conteúdo final, seguir
   `first-playable-slice.md` para provar o núcleo no emulador. Para projeto
   MUGEN, acrescentar a especialização `mugen-engine-quality.md`.
6. Registrar no memory bank o estado REAL dos eixos, a ROM/hash testada e o
   próximo bloqueio causal.
