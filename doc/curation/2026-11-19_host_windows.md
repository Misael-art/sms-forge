# Construção e telemetria do SMSForge no Windows

Auditoria do wrapper e da cadeia que liga a construção à evidência de ROM.
Base local `19f33a81ae2ef3505faa96962fb7039c62bdc1b0`. O PR 4 estava
em `6d91608a`. Os dois commits locais intermediários pertencem ao parser
MUGEN. O checkout também contém alterações de produção dos consumidores.

| Área | Achado e ação | Prova que ainda falta |
|---|---|---|
| Diagnóstico do host | O import global de `fcntl` impedia abrir o bootstrap no Windows. O doctor nativo agora consulta o mesmo resolvedor do build e tem recibo próprio. | Instalação completa da cadeia nativa. |
| Recursos | O doctor Linux registrava espaço e carga. O novo comando mede memória e paginação, CPU, I/O, filesystem e sensores, com inventário de processos opcional. No Linux usa PSI e deltas de swap. | Coleta em host Linux vivo após a mudança. |
| Construção | O padrão anterior era dois jobs, com quatro permitidos. O ambiente do wrapper começa com um, aceita até dois e dispõe de temporários privados. O build registra tempo por processo e totais de compilação, link e empacotamento. | Perfil de tempo de uma construção real com esta revisão. |
| Windows nativo | Foram corrigidos o sufixo dos executáveis, dependências com letras de unidade/espaços e a identidade de insumos em outro volume. O SDK privado usa a receita compartilhada de smoke. | Compilar as bibliotecas, gerar uma candidata e reconciliar seus hashes no Windows. |
| WSL e QA | O despacho explícito conserva os argumentos e o código de saída. O isolamento de Emulicious usa recursos Linux, inclusive identificação via procfs, locks e rota privada de áudio. | Executar a ponte em distribuição preparada e abrir a ROM candidata em sessão privada. |
| Consumidor | No rev2, o histórico distingue ROM nominal, provas de pose e builds diagnósticas. O backlog ainda pede identidade AIR na ROM, contato, orçamento de composição e VBlank sob carga completa. | Validar o trecho emulado no SHA atual com input, pior frame, áudio e piso funcional por janela. |

## Evidência deste Windows

- O registro Linux em `.runtime/doctor.json` é histórico. O doctor atual
  registrou `.runtime/doctor-windows.json`, ausência de SDCC nativo na rota
  pesquisada e código 2. O WSL listou apenas Debian, parado, registrado como
  DeckMaintenance. A validação da passagem de argumentos usou um teste local.
- O recibo de três amostras é
  `.runtime/host-resources-windows-20261119-final.jsonl`. CPU em 100% nas três,
  RAM disponível de 7,07 para 6,55 GiB, 2.029–3.356 páginas de entrada/s,
  zero páginas de saída/s. Destino Btrfs e temporários NTFS são volumes
  distintos. A estimativa usada para exercitar o cálculo foi de 512 MiB de
  RAM, 64 MiB de saída e 128 MiB de staging. O pico da compilação permanece
  por medir.
- O provedor ACPI direto retornou acesso negado. O contador de desempenho
  leu 53,85 °C em TZ01, e o evento Kernel-Power 125 do boot identificou
  99,85 °C como trip passivo dessa zona. O sensor direto de CPU retornou
  um valor inválido na sessão. O inventário retornou 243 processos, 124 com
  comando legível. O recibo compartilhável omite os comandos.
- Passaram os self-checks de bootstrap e build, o teste com contadores Linux
  de fixture, a descoberta do compilador, a passagem de argumentos WSL e os
  gates de sincronia documental e de captura de lições. A suíte de sessão
  privada depende do backend Linux. As suítes integrais de selftest e de
  ferramentas de medição continuam pendentes.
- O pacote SDCC x64 de 9.398.041 bytes está no cache privado de downloads.
  O SHA-256 confere com o lock e com o manifesto WinGet. O índice do arquivo
  contém as ferramentas Z80, includes e biblioteca. A segunda série, em
  `.runtime/host-resources-windows-20261119-sdk.jsonl`, avaliou o staging no
  próprio volume do checkout. A CPU permaneceu saturada e as leituras de
  páginas continuaram elevadas. A extração e a compilação foram adiadas.

## Retomada

Quando as novas amostras mostrarem margem, preparar o SDK nativo e executar
o smoke conforme o [guia do host](../continuity/20261024-start-here.md).
Usar o consumidor de laboratório em destino novo sob `out/candidates` e
conferir o recibo da ROM antes de testar o rev2. Completar a bateria de
curadoria no ambiente Linux gerenciado e conferir o estado do PR antes de
publicar. O roteiro operacional está na
[skill de monitoramento](../../tools/sms_wrapper/.agent/skills/host-build-monitoring.md).
