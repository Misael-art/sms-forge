# workflow: laboratory-mode

Modo `laboratory`. Vive em `SMS_projects/_laboratorio/`. Serve para **responder
uma pergunta sobre o hardware**, não para produzir jogo.

O laboratório é onde a suposição vira fato pago (§23). Toda técnica em `mapped`
na matriz de maestria sobe de nível aqui, ou não sobe.

1. Escrever a PERGUNTA antes do código, em uma frase falsificável.
   Ruim: "testar sprites". Bom: "`SPRITEMODE_TALL` com arte 16×16 renderiza?"
2. Menor probe possível: um `.c`, um comportamento observável, nada de gameplay.
   Variáveis de inspeção em endereço fixo (`__at(0xC700)`) quando for preciso
   ler estado pelo depurador.
3. Prever o resultado ANTES de rodar. Previsão errada é o achado mais valioso;
   previsão não registrada não pode ser refutada.
4. Rodar e capturar evidência real:
   ```sh
   python3 tools/sms_wrapper/capture_evidence.py --project <probe> --rom <rom.sms>
   python3 tools/sms_wrapper/screenshot_semantic_gate.py <shot.png>
   ```
5. Veredito honesto: **confirmado**, **refutado** ou **inconclusivo**.
   "Inconclusivo" é resultado legítimo; inconclusivo travestido de confirmado é
   overclaim e contamina toda técnica que dependa dele.
6. Fato pago → sobe a técnica na matriz (`01_registry_maestria_sms.json`, com
   `evidence` estruturada conforme `doc/05_technical/00_matriz_maestria_sms.md`:
   fonte/build/ROM/mídia/relatório com hashes, escopo e sessão). Executar
   `audit_mastery_registry.py --self-check` antes de auditar. Prosa e nome de
   gate não são evidência de execução. PASS verifica custódia, não domínio.
   Fato refutado → vira lição via `curation-learning.md`.

**Probe não vira jogo.** Código de laboratório não migra para projeto sem passar
pela ordem de trabalho de cena; ele provou uma pergunta, não entregou um sistema.
