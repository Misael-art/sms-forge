# SMSForge — continuidade 2026-10-21

Snapshot de recuperação para reinstalação do host. O código, a documentação e
as ROMs de changelog estão no Git; os arquivos grandes/ignorados estão nos
assets desta release.

## Fonte

- Repositório: <https://github.com/Misael-art/sms-forge>
- Branch: `feat/luta-mugen-motor`
- Snapshot inicial: tag `continuity-20261021` (`bdb32e7`)
- Retomada recomendada: tag `continuity-20261021-final`
- Leia primeiro: `doc/continuity/20261021-host-reinstall-handoff.md` e
  `doc/continuity/20261021-reconciliation.md`

## Assets

Este release tem dois conjuntos, produzidos em paralelo:

- **SMSForge/openbor:** `smsforge-openbor-out`, `smsforge-untracked-large`,
  `smsforge-generated-other`, `smsforge-toolchain`,
  `smsforge-changelogs-remaining`.
- **luta_mugem_rev2:** `luta_mugem_rev2_full`, `loteB2`, `sdk`, `emulators`,
  `qa_toolchain`, `workspace_out`, `workspace_untracked_nonout`,
  `RELEASE_ASSETS.sha256`.

O manifesto canônico combinado é
`doc/continuity/20261021-release-assets.sha256` no Git; o manifesto do fluxo
paralelo é `SMS_projects/luta_mugem_rev2/doc/continuity/RELEASE_ASSETS.sha256`.

## Retomada mínima do openbor

```sh
git clone https://github.com/Misael-art/sms-forge.git
cd sms-forge
git fetch --tags
git checkout continuity-20261021-final
gh release download continuity-20261021 -p 'smsforge-openbor-out-*'
gh release download continuity-20261021 -p 'smsforge-untracked-large-*'
gh release download continuity-20261021 -p 'smsforge-toolchain-*'
tar -xf smsforge-openbor-out-20261021.tar.zst
tar -xf smsforge-untracked-large-20261021.tar.zst
tar -xf smsforge-toolchain-20261021.tar.zst
cd SMS_projects/openbor_sms_rev1
./build.sh
sha256sum out/rom/openbor_sms_rev1.sms
# 701379cc88e074f5874e161cd7e6307b04be48456c1b469172f84a58d79a6da9
```

O bank O3 e o `changelog/roms/` do openbor já estão no Git. Um rebuild em data
posterior reproduz a ROM, mas rebaixa os eixos de evidência por frescor; para
o registro histórico cap5 use o `out/` restaurado sem rebuild, e para um claim
novo refaça a QA de emulador/áudio.

## Limites honestos

- `SMS_projects/luta_mugen/out/` (3,3 GB) e `.mimosa/` (727 MB) não foram
  arquivados.
- 25 docs de `luta_mugen/doc/` estavam com EIO; as versões do último commit
  continuam no Git; alterações não lidas não puderam ser salvas.
- Cap5 do openbor continua candidato, não delivery: direção do ataque/Lote C,
  PAL, regressão de gameplay e época visual `delivery` seguem pendentes.
- `luta_mugem_rev2` segue para v044; nenhuma política 5/3, 6/2, híbrida ou FX
  está aprovada.

**Regra final:** se não foi visto rodando no emulador, não existe. Este
snapshot preserva o que foi medido; não promove o que ainda está bloqueado.
