# README — projeto modelo SMSForge

Projeto esqueleto herdado por `new_project.sh`. Comandos (do diretório do projeto):

Comece pela rota de produção em [.agent/README.md](.agent/README.md).
Preencha o GDD e os beats e casos do primeiro trecho em
[doc/12-roteiro.md](doc/12-roteiro.md). Os comandos técnicos abaixo permitem
conferir a toolchain assim que o projeto nasce.

```sh
./build.sh   # delega ao wrapper: pre-gates -> sdcc -> makesms
./clean.sh
./run.sh     # exige ROM buildada + emulador configurado
```

Nada de lógica de build aqui. Nada de API inventada: confira `SMSlib.h`.
Ordem de trabalho de cena está no AGENTS.md da raiz do workspace.
