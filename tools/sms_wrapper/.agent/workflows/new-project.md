# workflow: new-project

```sh
tools/sms_wrapper/new_project.sh <slug>
```
1. Instancia `SMS_projects/<slug>/` do modelo (`.agent` local não sobrescrito).
2. Preencher `doc/11-gdd.md` com o loop de jogo, controles, modos/telas,
   condição de resultado e exclusões explícitas — humano aprova o escopo.
   Não presumir fase, cenário ou modo que não esteja no GDD.
3. Escrever os beats e preencher **Casos do primeiro trecho jogável** no
   roteiro. Vincular as ações escolhidas ao resultado, ao caso negativo e à
   retomada. Justificar o que fica fora ou para depois pelo GDD. Na raiz:

   ```sh
   rtk proxy tools/sms_wrapper/run_host.sh python tools/sms_wrapper/audit_specialization.py --project SMS_projects/SLUG --slice-plan
   ```

   Substituir SLUG pelo projeto. O modelo pendente deve reprovar. Repetir após
   preencher o roteiro, antes do storyboard. Em qualquer gênero aplicar
   [primeiro trecho jogável](first-playable-slice.md). Em luta com duelo, abrir
   [lutador jogável](playable-fighter.md) já ao definir golpe, resposta do rival e controles.
   Projetos anteriores podem incorporar a seção do modelo ao roteiro no
   próximo trecho, preservando seus beats e regras locais.
4. Preencher `doc/15-tdd.md`: FSM e entradas, update por frame, feedback
   visível, pools/layout VRAM, custo CPU, RAM/ROM/banking e medidas de pior
   quadro. Nomear quais telas coexistem e quais carregam recursos separados.
   Se houver múltiplos estados, definir entrada/saída, owners e dados que
   persistem em `sms-state-transitions.md`.
5. Checagem da toolchain: `./build.sh`. A produção segue do roteiro para
   storyboard, coreografia e medição conforme `new-scene.md`.
6. Antes de criar o elenco ou o conteúdo final, seguir
   `first-playable-slice.md` para provar o núcleo no emulador. Para projeto
   MUGEN, acrescentar a especialização `mugen-engine-quality.md`.
7. Registrar no memory bank o estado REAL dos eixos, a ROM/hash testada e o
   próximo bloqueio causal.
