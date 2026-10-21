# Validation results — 2026-10-21 (pre-format)

Escopo: **build/reprodutibilidade de payload** no host antigo, a partir do
clone local `bdb32e7` + tarball gerado versionado. Não é validação de emulador.

## Comando

```sh
bash SMS_projects/luta_mugem_rev2/doc/continuity/validate_after_reinstall.sh
```

Saída completa: `VALIDATION_20261021_script.log`.

## Resultado

| Build | Fonte | SHA bruto | Diff | SHA canonicalizado | Veredito |
|---|---|---|---|---|---|
| Produção | `042ba22e…` | `9873b3ff99194f40bd2baa804ca03ec0393ddee1677168366b7903414b1c44ac` | `0x7FE6`, `0x7FFA` | `087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65` | PASS |
| v043 | `eb5576ad…` | `26b305672e1c8e47ec961e099d2991ae492145a875d67f0e58fd62409c7421e6` | `0x7FE6`, `0x7FFA` | `13b78bd2435673df089ed69302522d332c9418ea74331aeff95065c85e3920c7` | PASS |

- Tamanho das duas ROMs: 851.968 B.
- Checksum: `sum(rom[:0x7FF0]) & 0xFFFF`, little-endian em `0x7FFA`.
- Data SDSC: `0x7FE6`; copiada da ROM canônica de referência.
- Nenhuma diferença fora desses offsets; o payload é idêntico.
- Toolchain: SDCC 4.6.0 #16555, `makesms` sha `617b2e79…`, Emulicious não
  usado nesta validação.

## O que continua aberto

`boot_emulador`, `gameplay`, `fps_constante`, `audio`,
`memory_bank_atualizado` (o `[BUILD OK]` lista exatamente esses eixos como
restantes). Render/SAT/§129 do SHA novo também exigem medição viva antes de
qualquer claim. **Nenhum delivery.**

## Artefatos de evidência

- `VALIDATION_20261021_script.log` — execução do script (produção + v043);
- `VALIDATION_20261021_prod.log` / `..._v043.log` — primeira execução manual;
- `post_reinstall_*_prod.log` / `..._v043.log` — logs gravados pelo script;
- `assets/tool_selfchecks.txt` — self-checks das ferramentas;
- `HOST_MANIFEST.md` — versões/SHAs do host/toolchain.
