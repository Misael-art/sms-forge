# README — projeto modelo SMSForge

Projeto esqueleto herdado por `new_project.sh`. Comandos (do diretório do projeto):

```sh
./build.sh   # delega ao wrapper: pre-gates -> sdcc -> makesms
./clean.sh
./run.sh     # exige ROM buildada + emulador configurado
```

Nada de lógica de build aqui. Nada de API inventada: confira `SMSlib.h`.
Ordem de trabalho de cena está no AGENTS.md da raiz do workspace.
