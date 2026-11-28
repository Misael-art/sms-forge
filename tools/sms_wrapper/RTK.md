# RTK — convenção portátil do SMSForge

Prefixe comandos de shell com `rtk`. Para saída sem filtragem, use
`rtk proxy <comando>`. A instalação usa `rtk-ai/rtk` e confere o SHA-256
fixado em `host_dependencies.lock.json`; não altera hooks globais.

Em host novo, antes de RTK existir, execute a instalação com bash:

```sh
bash tools/sms_wrapper/bootstrap_host.sh --install-system
```

Depois use `tools/sms_wrapper/run_host.sh rtk ...`, que ativa somente o
ambiente deste checkout. Não depende de `/home/misael` nem altera `.bashrc`.
