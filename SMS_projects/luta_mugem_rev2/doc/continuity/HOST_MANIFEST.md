# Host manifest — captura em 2026-10-21

Registro do host que gerou/validou a continuidade do `luta_mugem_rev2` antes da
formatação. Serve para comparar o host novo e para reinstalar a mesma
toolchain; **não** é prova de que a ROM roda no emulador.

## Sistema

| Item | Valor |
|---|---|
| Distro | BigLinux based on Manjaro Linux (rolling) |
| Kernel | Linux 6.18.49-1-MANJARO x86_64 |
| Sessão | Wayland (`XDG_SESSION_TYPE=wayland`), `WAYLAND_DISPLAY=wayland-0`, `DISPLAY=:0` |
| Python | 3.14.7 |
| Java | OpenJDK 17.0.20.1 2026-08-18 |
| `javac` | ausente (por isso o `bridge.jar` pré-compilado é preservado) |
| Git | 2.55.0 |
| GitHub CLI | 2.100.0 |
| ffmpeg/ffprobe | 9.0.1 |
| zstd | 1.5.7 |
| Xvfb | `/usr/sbin/Xvfb` |
| xdotool | `/usr/sbin/xdotool` |
| kdotool | `/usr/sbin/kdotool` |
| ydotool | `/home/misael/.local/bin/ydotool` |
| spectacle | `/usr/sbin/spectacle` |

Módulos Python: Pillow 12.3.0, numpy 2.5.2, pytest 9.1.0, PyYAML 6.0.3,
requests 2.34.2. O módulo `zstandard` do Python não estava instalado; os
arquivos `.tar.zst` usam o CLI `zstd`.

## Toolchain

| Item | Caminho/SHA |
|---|---|
| SDCC | `sdk/sdcc-portable/bin/sdcc` — SDCC 4.6.0 #16555 |
| SHA do `sdcc` | `09dbddb81fd724efe18bc83c48dbad1d6a50b33964f9a5520a1c9fd7445be564` |
| devkitSMS `makesms` | `sdk/devkitSMS/tools/makesms` |
| SHA do `makesms` | `617b2e794af50841ce14b40e4085abe6292f829581451b0423e28e117517b346` |
| `sdk/env.sh` | `a4f46201c7310a71bae266cceed13bd65005086baa1d10fb5b50e702e6755ce6` |
| Emulicious | `tools/emuladores/emulicious/Emulicious.jar` |
| SHA do Emulicious | `db185a1ed0af3bdab5ebdeb254612d02d3848bac155dbc89333d1b04e21c371d` |
| `bridge.jar` | no asset `qa_toolchain_20261021.tar.zst` |
| SHA do `bridge.jar` | `a283b54202112434927ed8f83bb292376a2d6f74830dde6f04f9589da377333a` |
| BlastEm 1.0.0 (tar) | `out/blastem_downloads/blastem64-1.0.0.tar.gz` |
| SHA do tar BlastEm | `9e47b68a555e24db5ef5bd77e67967124ac3e28ae04ae32e9f3af3eaecf31860` |

O `sdcc` **não** está no PATH global; o `build_inner.py` encontra o portátil.
O SDK é rootless e pode ser reinstalado por `tools/sms_wrapper/ensure_toolchain.sh`.

## Arquivos de continuidade do projeto

Os hashes por arquivo estão em `ASSETS.sha256` (versionado) e os hashes dos
assets da release em `RELEASE_ASSETS.sha256`. Pontos fixos:

| Artefato | SHA-256 |
|---|---|
| ROM canônica | `087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65` |
| ROM v043 | `13b78bd2435673df089ed69302522d332c9418ea74331aeff95065c85e3920c7` |
| Tarball gerado | `aa6ea4ef769fee0d9f36088848a198c7c217da6f0057f58c0344e2249f5d8915` |
| Fonte de produção | `042ba22e4a0763daaa4e402b90a0a5d0d40a7b5923c17575ed012b6a89773bfe` |
| Fonte v043 | `eb5576ad73e5e79b3ec94a217e13b57faf38a264631ba65aaec3f7642a54cb59` |

## Builds observadas neste host

| Build | SHA bruto | Canonicalizado |
|---|---|---|
| produção | `9873b3ff99194f40bd2baa804ca03ec0393ddee1677168366b7903414b1c44ac` | `087df676…` |
| v043 | `26b305672e1c8e47ec961e099d2991ae492145a875d67f0e58fd62409c7421e6` | `13b78bd2…` |

O único delta aceito é `0x7FE6` (data SDSC) + `0x7FFA` (checksum SEGA). Ver
`doc/continuity/verify_canonical.py` e `doc/27`, §5.
