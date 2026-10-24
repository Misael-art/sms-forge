# sdk/ — Toolchain do SMSForge (procedimento oficial)

**Host vazio:** siga [o runbook de 24/10](../doc/continuity/20261024-new-host.md).

```sh
bash tools/sms_wrapper/bootstrap_host.sh --apply --system-packages --profile full
source tools/sms_wrapper/host_env.sh
```

`ensure_toolchain.sh` agora delega ao perfil build do instalador pinado; não
instala pacotes do SO implicitamente. SDK e compilador usam a mesma cápsula
ABI; o smoke-test prova compile/link/header, não execução no emulador.
Instalações existentes divergentes são preservadas. Receitas manuais abaixo
são referência; o caminho reproduzível usa o wrapper e seus hashes.

**Autoridade de API = os headers abaixo. Nenhum agente inventa função.**

```
sdk/devkitSMS/
├── SMSlib/SMSlib.h        ← autoridade #8 da hierarquia de verdade (SMS/GG)
├── PSGlib/PSGlib.h        ← áudio PSG
├── crt0/crt0_sms.rel      ← runtime inicial (sempre o PRIMEIRO objeto no link)
└── tools/{makesms,assets2banks,ihx2sms}
```

## Instalação (host Linux ou Windows)

1. **SDCC ≥ 4.2.0** (componentes: include files + Z80 library).
   - Linux: `sudo apt install sdcc` ou build dos sources.
   - Windows: instalador oficial em sdcc.sourceforge.net.
   - Verificar: `sdcc --version` ≥ 4.2.0.
2. **devkitSMS**: clonar `https://github.com/sverx/devkitSMS`.
   - Copiar `makesms(.exe)` e `assets2banks(.exe)` para a pasta `bin` do SDCC
     (`ihx2sms` legado opcional).
   - Copiar para este diretório:
     - `SMSlib/src/SMSlib.h`, `SMSlib/SMSlib.lib` → `sdk/devkitSMS/SMSlib/`
     - `PSGlib/src/PSGlib.h`, `PSGlib/PSGlib.lib` → `sdk/devkitSMS/PSGlib/`
     - `crt0/crt0_sms.rel` → `sdk/devkitSMS/crt0/`
3. **Emulador gate**: instalar **Emulicious** (sessões privadas de produção/QA)
   em `tools/emuladores/`. openMSX não suporta SMS; BlastEm é diagnóstico complementar. Registrar caminho em `tools/emuladores/emulators.json`.

## Comandos canônicos de compilação (fonte: README do devkitSMS)

```sh
# compile
sdcc -c -mz80 --peep-file peep-rules.txt main.c

# link (crt0 SEMPRE primeiro; libs DEPOIS do código)
sdcc -o game.ihx -mz80 --no-std-crt0 --data-loc 0xC000 \
    crt0_sms.rel main.rel SMSlib.lib PSGlib.lib

# ROM final (.sms, tamanho múltiplo de 16KB, checksum SEGA)
makesms game.ihx game.sms
```

Bancos acima de 48KB: dados com `--constseg BANKn` + `-Wl-b_BANKn=0x{n}4000`
e troca via macro `SMS_mapROMBank(n)`; código bancado usa `__banked`
(`--codeseg BANKn`, slot 0x4000). Código não-bancado restrito aos primeiros 32KB.

## Regra anti-alucinação

Antes de usar qualquer função/macro de SMSlib/PSGlib: **abrir o header e confirmar
assinatura**. Se o header não está instalado, o gate de build falha com instrução —
isso é comportamento correto, não bug. Nunca contorne.
