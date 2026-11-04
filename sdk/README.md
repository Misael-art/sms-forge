# sdk/ — Toolchain do SMSForge (procedimento oficial)

**Instalação assistida em host novo (Ubuntu 24.04 x86_64 / WSL2 Ubuntu):**
```sh
bash tools/sms_wrapper/bootstrap_host.sh --install-system
```
Instala os pacotes básicos que faltarem; mantém Python/SDK/emulador/cache no
workspace e reconstrói SMSlib/PSGlib com o SDCC selecionado (>=4.2). Fontes e
binários externos têm hashes fixados no lock. PROVA compile→link→ROM com
SMSlib e PSGlib antes de registrar sucesso. Sem `--install-system`, não altera
pacotes globais. `ensure_toolchain.sh` é alias de compatibilidade.

Guia completo e recuperação dos dados ignorados:
`doc/continuity/20261024-start-here.md`. A toolchain portátil antiga continua
no backup histórico de 21/10 para reprodução; o bootstrap novo usa o SDCC da
distribuição e registra sua identidade. Build novo exige evidência nova.

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
3. **Emulador gate**: instalar **Emulicious** e/ou **openMSX** (headless p/ CI)
   em `tools/emuladores/`. Registrar caminho em `tools/emuladores/emulators.json`.

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
