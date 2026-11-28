# Capacidade do host e construção

Use antes de bootstrap, build, suíte integral ou sessão de emulador. Para
investigar fluidez observada no jogo, consulte também `sms-runtime-optimization.md`.

1. Na raiz, rode `python -B tools/sms_wrapper/host_bootstrap.py --self-check`.
   Use `python3` no Linux. O coletor requer apenas a biblioteca padrão e os
   provedores do sistema. No Windows, comece pelo PowerShell do host físico.
   Antes de iniciar WSL confira as margens do host. Dentro da distribuição,
   confira também PSI, swap e o filesystem do checkout e dos temporários.
2. Use `host_bootstrap.py resources --processes` para inspecionar localmente
   os comandos completos e RSS dos concorrentes, inclusive builds em espera.
   Colete o recibo compartilhável em outra chamada, omitindo `--processes`.
   Selecione o diretório real de saída com `--root DIRETORIO` **antes** de
   `resources` e o staging existente com `--temp DIRETORIO` depois dele.
3. Informe os MiB adicionais estimados em `--peak-mib`, `--output-mib` e
   `--staging-mib`. O campo `budget` desconta as duas escritas quando o
   dispositivo é compartilhado e contabiliza tmpfs na RAM. Confira a reserva
   de RAM (maior entre 4 GiB e 25%) e 10 GiB no disco persistente. Complete
   a decisão com a atividade de paginação, CPU, I/O e a temperatura/trip
   do sensor relevante. Um campo nulo, uma zona vazia ou um erro de provedor
   exige outra fonte antes de uma carga pesada. Páginas lidas pelo Windows
   incluem arquivos mapeados e não quantificam sozinhas o uso do pagefile.
4. Durante a operação, use `resources --samples 30 --interval 20` em outro
   terminal. Cada linha JSON recebe timestamp UTC, inclusive se o processo
   for interrompido após uma amostra. Preserve o recibo com as estimativas
   realmente usadas. Reavalie a operação a cada 15–30 s conforme as regras
   do host. Encerre apenas a carga própria se for seguro interrompê-la.
5. Confira `host_bootstrap.py doctor` no ambiente que executará a carga.
   O recibo Windows identifica executáveis nativos. A pasta `.venv/bin` e
   os binários Linux preservados pertencem à distribuição que os preparou.
   Para comparar uma build use `build_inner.py --project ... --build-dir ...`
   com destino novo em `out/candidates/`. Para QA, siga a sessão privada
   Emulicious e vincule cada evidência ao SHA do candidato.

Ao investigar uma construção lenta, examine `host_stage_elapsed_seconds`
em `build_record.json`. Ele soma o tempo decorrido dos processos de
compilação, link e empacotamento. Cada invocação também registra tempo e
saída em `logs_build.txt`, inclusive quando o comando retorna erro.

O recibo do host contextualiza o ensaio. O FPS funcional vem do probe da ROM
em execução contínua. Registre cada janela, input, apresentação e pior frame
segundo SMS_GLOBAL §133.
