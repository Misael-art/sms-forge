# Reconciliação da continuidade — 2026-10-21

> Este documento fecha a diferença entre o snapshot inicial, o trabalho
> paralelo de `luta_mugem_rev2`, os assets da release e a validação feita em
> clone novo. Leia junto com `20261021-host-reinstall-handoff.md`.
>
> **Regra:** o SHA da ROM prova reprodutibilidade; ele não promove cap5 a
> delivery. Os eixos de evidência continuam sujeitos a frescor e a nova QA.

## 1. Cadeia de commits e tags

| Ref | Papel |
|---|---|
| `bdb32e7` | Snapshot inicial do workspace (5.810 arquivos, 603 MiB); tag `continuity-20261021`. |
| `dea07bf` | Continuidade específica de `luta_mugem_rev2` (docs, ROMs, validação de build). |
| `76933f9` | Separa manifesto de assets versionados dos assets da release. |
| `e3eb26b` | Alinha o manifesto ao `luta_mugem_rev2_full` efetivamente publicado (`8bb4222e…`). |
| `164b309` | Registra clone limpo do GitHub e validação pós-push do `luta_mugem_rev2`. |
| `1abf107` | Versiona o bank O3 (80 KiB) e o changelog do openbor; corrige bits executáveis de `build.sh`/`ensure_toolchain.sh`. |
| `continuity-20261021-final` | Tag do commit que contém este documento, o manifesto reconciliado e os fixes acima. |

A tag `continuity-20261021` continua apontando para `bdb32e7`: é o snapshot
histórico. Para retomar com os docs de `luta_mugem_rev2` e esta reconciliação,
use `continuity-20261021-final` (ou o HEAD do branch `feat/luta-mugen-motor`).

## 2. Assets da release

A release pública é uma só, `continuity-20261021`, mas contém dois conjuntos
produzidos em paralelo. O manifesto canônico, com SHA-256 e bytes verificados
pela API do GitHub, é `doc/continuity/20261021-release-assets.sha256`.

### 2.1 Conjunto SMSForge/openbor (deste fluxo)

| Asset | Conteúdo |
|---|---|
| `smsforge-openbor-out-20261021.tar.zst` | `SMS_projects/openbor_sms_rev1/out/` (ROM, evidência cap5, QA, build record). |
| `smsforge-untracked-large-20261021.tar.zst` | untracked grande do workspace (`out/` raiz, arte >5 MiB, tar de estudo etc.). |
| `smsforge-generated-other-20261021.tar.zst` | `out/` dos demais projetos, exceto `openbor` e `luta_mugen`. |
| `smsforge-toolchain-20261021.tar.zst` | `sdk/` + `tools/emuladores/` (também coberto por `sdk_20261021` + `emulators_20261021` do outro conjunto). |
| `smsforge-changelogs-remaining-20261021.tar.zst` | changelogs ignorados de `luta_mugen` e dos demais projetos; `_laboratorio/pnt_16bit/out`. |

O changelog do openbor **não** está nesse asset: foi versionado no Git em
`1abf107` (`changelog/roms/build_v001..v078`). O bank O3 também está no Git.

### 2.2 Conjunto `luta_mugem_rev2` (fluxo paralelo)

| Asset | Conteúdo |
|---|---|
| `luta_mugem_rev2_full_20261021.tar.zst` | projeto completo com `out/` e changelog. |
| `loteB2_20261021.tar.zst` | custódia temporária B.2b. |
| `sdk_20261021.tar.zst` | SDK usado na validação. |
| `emulators_20261021.tar.zst` | emuladores usados na validação. |
| `qa_toolchain_20261021.tar.zst` | toolchain de QA. |
| `workspace_out_20261021.tar.zst` | `out/` restante do workspace. |
| `workspace_untracked_nonout_20261021.tar.zst` | manifesto/inventário de untracked. |
| `RELEASE_ASSETS.sha256` | hashes do conjunto paralelo, alinhados em `e3eb26b`. |

## 3. Retomada mínima

```sh
git clone https://github.com/Misael-art/sms-forge.git
cd sms-forge
git fetch --tags
git checkout continuity-20261021-final
```

Depois baixe os assets necessários da release `continuity-20261021` com
`gh release download` e confira contra `20261021-release-assets.sha256`.
Para o openbor:

```sh
tar -xf smsforge-openbor-out-20261021.tar.zst          # out/ + evidência cap5
tar -xf smsforge-untracked-large-20261021.tar.zst      # untracked grande
tar -xf smsforge-toolchain-20261021.tar.zst            # sdk/ + emuladores
cd SMS_projects/openbor_sms_rev1
./build.sh
sha256sum out/rom/openbor_sms_rev1.sms
# 701379cc88e074f5874e161cd7e6307b04be48456c1b469172f84a58d79a6da9
```

O build usa `res/o3/banks/o3_pose_blocks_20261017.bin` e o
`changelog/roms/`; ambos agora estão no Git. Não é mais necessário copiar
arquivo ignorado para compilar.

### Frescor das evidências

Um rebuild em data posterior reproduz a ROM, mas o gate de frescor compara a
data do ROM recém-gerado com a data das evidências e **rebaixa** boot,
gameplay, FPS e áudio. Isso é esperado e não invalida o SHA. Para o registro
histórico cap5, use o `out/` restaurado **sem rebuild** (o asset já contém o
build record 7/7). Para um claim novo, refaça a QA de emulador e o áudio na
data corrente; não reutilize o claim antigo como se fosse medição nova.

## 4. Validação feita

- Build local do snapshot: `BUILD OK`, ROM
  `701379cc88e074f5874e161cd7e6307b04be48456c1b469172f84a58d79a6da9`,
  131.072 bytes, eixos 7/7 no `build_record.json` na mesma sessão.
- Clone **parcial a partir do GitHub** do commit `1abf107`, com sparse
  checkout de `SMS_projects/openbor_sms_rev1`, `tools/sms_wrapper` e
  `doc/continuity`: `./build.sh` executou (bit +x confirmado), ROM com o mesmo
  SHA; os eixos de evidência foram rebaixados por frescor (3/7) porque o
  rebuild é posterior às evidências cap5. O SHA prova a reprodutibilidade; a
  QA nova ainda é necessária para promoção.
- Validação do `luta_mugem_rev2` no fluxo paralelo: clone limpo do GitHub,
  build/produção e v043 revalidados; ver
  `SMS_projects/luta_mugem_rev2/doc/continuity/VALIDATION_RESULTS.md` e os
  logs `VALIDATION_20261021_github_clone.log`.
- Os assets publicados foram conferidos por digest da API do GitHub no
  manifesto reconciliado.

## 5. O que **não** está preservado

- `SMS_projects/luta_mugen/out/` — 3,3 GB, gerado; não foi arquivado.
- `.mimosa/` — 727 MB, estado de hooks/sessão do agente; não é fonte.
- `SMS_projects/luta_mugen/doc/` — 25 arquivos com `Erro de entrada/saída`
  (EIO) no armazenamento no momento do snapshot. As versões do último commit
  continuam em `bdb32e7`/`continuity-20261021`; as alterações não lidas não
  puderam ser estagiadas. O ledger está em `20261021-deleted-paths.txt`.
- `SMS_Engines/*/build/`, `SMS_Engines/*/*.sms`, `SMS_Engines/devkitSMS/`,
  `SMS_Engines/smslib/` — builds/cópias de toolchain ignoradas; o SDK e os
  emuladores estão nos assets; os fontes de engine versionados estão no Git.
- `SMS_projects/*/out/` de projetos fora do openbor/luta_mugem_rev2 estão no
  asset `smsforge-generated-other`; `luta_mugen/out` é a exceção acima.

## 6. Continuidade de desenvolvimento

Cap5 do openbor continua **candidato**, não delivery: ataque ainda pode sair
para a esquerda com inimigo à direita; Lote C/PAL/regressão de gameplay e
época visual `delivery` seguem pendentes. O próximo passo seguro é decidir
entre corrigir a direção do ataque/Lote C ou declarar o limite conhecido, e
medir PAL versus declarar NTSC-only. O `luta_mugem_rev2` segue para v044 com
lista 5/3 pré-computada; nenhuma política 5/3, 6/2, híbrida ou FX está
aprovada. Nada disso é promovido por este snapshot.
