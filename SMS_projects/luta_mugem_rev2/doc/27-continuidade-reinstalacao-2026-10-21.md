# 27 — Continuidade do `luta_mugem_rev2` para reinstalação do host (2026-10-21)

> **Leia este arquivo junto com:**
> 1. `doc/10-memory-bank.md` — autoridade operacional do projeto;
> 2. `doc/11-gdd.md` e `doc/13-spec-cenas.md` — escopo e budget;
> 3. `doc/continuity/20261021-host-reinstall-handoff.md` na raiz do workspace —
>    handoff geral do SMSForge (toolchain, release, outros projetos).
>
> Este documento é o recorte **específico do `luta_mugem_rev2`**: o que está no
> Git, o que está nos assets da release, como reconstruir a ROM canônica, como
> reconstruir o candidato v043 e o que **não** pode ser promovido.

**Regra final:** se não foi visto rodando no emulador, não existe. Este
documento prova **build/reprodutibilidade**; não prova boot, gameplay, 60/50
fps, áudio, render final nem delivery.

---

## 0. TL;DR

- O snapshot de workspace `bdb32e7` (tag `continuity-20261021`, branch
  `feat/luta-mugen-motor`) versiona **fonte, dados MUGEN derivados, docs,
  scripts de repro e o framework** do projeto.
- `out/` continua ignorado pelo Git. ROM canônica, ROM v043, evidências
  B.2b-3b, banks gerados e os arquivos grandes estão em
  `doc/continuity/` (versionado) e nos assets da release `continuity-20261021`.
- A build de produção e a build do v043 foram **refeitas neste host** a partir
  do clone/tarball gerado; ambas reproduzem o payload canônico após restaurar
  o byte SDSC e o checksum SEGA. Ver §5 e
  `doc/continuity/VALIDATION_20261021_script.log`.
- A produção canônica é `087df676…`; o v043 é `13b78bd2…` e **não foi
  promovido** (pacing 5033 < alvo 5745).
- O próximo passo técnico é o **v044 com lista 5/3 pré-computada**; nenhuma
  política 5/3, 6/2, híbrido ou FX está aprovada por este documento.

---

## 1. Onde está cada coisa

### 1.1 No Git (clone normal)

| Conteúdo | Caminho |
|---|---|
| Fonte canônica de produção | `SMS_projects/luta_mugem_rev2/src/main.c` |
| Headers e dados de runtime | `SMS_projects/luta_mugem_rev2/inc/`, `src/` |
| Dados MUGEN de entrada e derivados | `SMS_projects/luta_mugem_rev2/data/` |
| Docs/autoridades | `SMS_projects/luta_mugem_rev2/doc/` |
| Manifesto estrutural | `SMS_projects/luta_mugem_rev2/.mddev/project.json` |
| ROM canônica | `doc/continuity/assets/luta_mugem_rev2_canonical_087df676.sms` |
| ROM candidata v043 | `doc/continuity/assets/candidate_v043_13b78bd2435673df.sms` |
| Banks/headers gerados (tarball) | `doc/continuity/assets/ryu_ken_cross_generated_20261021.tar.gz` |
| Relatório/custódia B.2b-3b | `doc/continuity/assets/B2B3B_*`, `b2b3b_sat_policy_20261021.json` |
| Fontes dos candidatos v040–v043 | `doc/continuity/repro/main.c.*` |
| Receitas de build/medição | `doc/continuity/repro/` |
| Validação de build pós-formatação | `doc/continuity/validate_after_reinstall.sh` |
| Verificador canônico | `doc/continuity/verify_canonical.py` |
| Configs do gerador | `doc/continuity/config/` |

### 1.2 Na release (arquivos grandes/ignorados)

**Release:** **`continuity-20261021`** no repositório
`https://github.com/Misael-art/sms-forge`. Confirme os hashes em
`doc/continuity/RELEASE_ASSETS.sha256` antes de usar.

| Asset | Conteúdo | Raiz de extração |
|---|---|---|
| `luta_mugem_rev2_full_20261021.tar.zst` | projeto completo: fonte, docs, data, `out/` inteiro (ROM, evidências, logs, gerados) | `luta_mugem_rev2/` |
| `loteB2_20261021.tar.zst` | custódia temp do lote B.2b (fontes, ROMs, probes, vídeos, scripts) | `loteB2b/` |
| `sdk_20261021.tar.zst` | SDCC portátil + devkitSMS usados na build | `sdk/` |
| `emulators_20261021.tar.zst` | Emulicious/emuladores e configuração | `tools/emuladores/` |
| `qa_toolchain_20261021.tar.zst` | `bridge.jar`, fontes Java e BlastEm privado | `smsforge_bundles/`, `out/blastem_downloads/` |
| `workspace_out_20261021.tar.zst` | `out/` da raiz do workspace | `out/` |
| `workspace_untracked_nonout_20261021.tar.zst` | `_laboratorio/pnt_16bit/out` e `frame_advance_v062_private` | raiz do workspace |

Os mesmos artefatos pequenos estão versionados em `doc/continuity/`; o tarball
gerado permite a build sem depender da release.

### 1.3 O que não está preservado

- `SMS_projects/luta_mugen/out/` (~3,3 GB): o irmão `luta_mugen` está com EIO
  pré-existente; **não** foi tocado, nem `fsck`/remount foi executado. O estado
  commitado do projeto está no Git; o `out/` desse irmão precisa de cópia
  externa antes de formatar se for necessário.
- Credenciais, chaves SSH, `~/.config/gh`, banco do agente e estado de sessão
  de emulador não estão no GitHub.
- Nenhum asset desta release promove v043, híbrido, FX ou política de SAT.

---

## 2. Estado canônico

| Item | Valor |
|---|---|
| Branch | `feat/luta-mugen-motor` |
| Tag de snapshot | `continuity-20261021` → `bdb32e7` |
| Fonte de produção | `src/main.c` sha256 `042ba22e4a0763daaa4e402b90a0a5d0d40a7b5923c17575ed012b6a89773bfe` |
| ROM canônica | `087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65` |
| Tamanho | 851.968 B (52 bancos de 16 KB; header declara `0x4C`) |
| Gerado | `out/generated/ryu_ken_cross/versus_scene_runtime.h` sha256 `19edb320…` |
| Banks gerados | `versus_scene_banks_02.bin` sha256 `3af7a307…`, 802.816 B |
| Config P1 | `doc/continuity/config/ryu_pilot_diag.json` sha256 `7aa3fb36…` |
| Config P2 | `doc/continuity/config/ken_pilot_diag.json` sha256 `22592555…` |
| Fonte v043 | `doc/continuity/repro/main.c.rowquota_v043` sha256 `eb5576ad73e5e79b3ec94a217e13b57faf38a264631ba65aaec3f7642a54cb59` |
| ROM v043 | `13b78bd2435673df089ed69302522d332c9418ea74331aeff95065c85e3920c7` |

O rebuild de produção neste host gerou
`9873b3ff99194f40bd2baa804ca03ec0393ddee1677168366b7903414b1c44ac`; após
copiar o byte de data SDSC (`0x7FE6`) e recalcular o checksum SEGA
(`0x7FFA–0x7FFB`, soma de `[0x0000,0x7FF0)`), o SHA volta a
`087df676…`. O rebuild do v043 gerou
`26b305672e1c8e47ec961e099d2991ae492145a875d67f0e58fd62409c7421e6` e
canonicaliza para `13b78bd2…`. Detalhes em §5.

---

## 3. O que o B.2b-3b provou (e o que não provou)

O lote B.2b-3b testou a política de SAT do fallback sprite-only. A custódia
completa está em `doc/continuity/assets/` e no asset `luta_mugem_rev2_full`.

| Candidato | Política | Linha/SAT real | §129 | Pacing | Resultado |
|---|---|---|---|---|---|
| v036 `7002b0ba…` | sprite-only, SAT 64 | render P2 26% | — | `smrt_frame=5745` | render fail |
| v037 `b68061ce…` | híbrido BG+SAT | render 100% | — | 3945 (−31,3%) | pacing fail |
| v040 `d998209b…` | ordem alternada | pico 14; 78/77 linhas >8 | — | 5743 | linha fail |
| v041 `3f3dce97…` | cap whole-cell | sim 39/8 | — | 2055 | pacing fail |
| v042 `44315339…` | quota 6+2 | 40 sprites; pico 8 | **FAIL** (6>5; 2<3) | 4483 (−22,0%) | rejeitado |
| v043 `13b78bd2…` | quota 5+3 | 40 sprites; pico 8; `SpriteNextFree=40` | **PASS** | **5033 (−12,4%)** | não promovido |

- **v043** é a primeira política que passa linha real **e** §129 sem híbrido.
  SAT real f002: 40 sprites (P1 15 a 3/banda + P2 25 a 5/banda); f001 é
  transição (25 do P2) e não serve para §129.
- **v043** vídeo: 600 quadros, 127 distintos, 256×192, 59,9227 Hz, fração
  máxima de células 0,1190; `vline_min=9`; sidecars par f1020/f1021 com o mesmo
  SHA (não são prova independente).
- **v043** pacing: `smrt_frame=5033`, `vovf=2506`, `worst_done=1`,
  `vbl_exit_max=255`, `sat_om_p1=28094`, `sat_om_p2=51482`,
  `stage_slice_max=214`, `add_total_max=70`. O alvo de 5745 não foi pago.
- **v042** tem captura pareada suspeita: f1020/f1021 com mesmo SHA
  `ccdd51c5…` e lado cheio oposto ao shadow SAT; o veredito visual usa vídeo +
  shadow, não o par. `present=65535` sob quota significa omissão declarada, não
  corpo ausente nem overflow do SAT-64.
- A lição do bankmask do BlastEm é **L139**; L137 é silhueta; L138 é projeção
  SHA. A menção antiga no B.2b foi corrigida.
- **Nenhum candidato foi promovido.** A produção restaurada é
  `087df676…` / `042ba22e…`.

### 3.1 Próximo candidato — v044

Implementar a **lista limitada 5/3 pré-computada por pose/lado**, com seleção
espacial contígua/central, para remover o custo por célula e as listras:

1. gerar a lista 5/3 por pose (P1 15, P2 25 no teto) sem varredura por célula;
2. emitir a lista pronta; medir `smrt_frame` no selo de 300 s;
3. medir SAT real/linha e §129 nas duas atribuições (f002, não f001);
4. capturar vídeo 256×192 e revisar listras/poses;
5. se pacing ≥5745, levar a política 5/3 à aprovação humana; se não, declarar
   o teto do sprite-only e decidir entre híbrido row-batched ou omissão 5/3
   com custo medido.

Sem promoção silenciosa. A política 5/3, o gerador da lista, o empacotamento
1 MB, a guarda BlastEm+L139 e o destino dos FX continuam **pendentes de
aprovação humana**.

---

## 4. Retomar em um host novo

```sh
git clone https://github.com/Misael-art/sms-forge.git
cd sms-forge
git fetch --tags

# Para ter o doc/27, doc/continuity e o commit de continuidade do projeto:
git checkout feat/luta-mugen-motor

# Alternativa mínima: checkout da tag; o asset "full" contém docs/out.
# git checkout continuity-20261021
```

Baixe os assets (exemplo; ajuste o diretório):

```sh
mkdir -p /mnt/sdcard/continuity_release
cd /mnt/sdcard/continuity_release
gh release download continuity-20261021 \
  --pattern 'sdk_20261021.tar.zst' \
  --pattern 'emulators_20261021.tar.zst' \
  --pattern 'qa_toolchain_20261021.tar.zst' \
  --pattern 'luta_mugem_rev2_full_20261021.tar.zst' \
  --pattern 'loteB2_20261021.tar.zst' \
  --pattern 'workspace_out_20261021.tar.zst' \
  --pattern 'workspace_untracked_nonout_20261021.tar.zst'
sha256sum -c RELEASE_ASSETS.sha256   # copie o manifesto do repo para cá
```

Extraia a toolchain na raiz do clone:

```sh
cd /path/to/sms-forge
tar -I zstd -xf /mnt/sdcard/continuity_release/sdk_20261021.tar.zst
tar -I zstd -xf /mnt/sdcard/continuity_release/emulators_20261021.tar.zst
tar -I zstd -xf /mnt/sdcard/continuity_release/qa_toolchain_20261021.tar.zst
# A toolchain também pode ser reinstalada com:
# tools/sms_wrapper/ensure_toolchain.sh
```

O `sdk` portátil contém SDCC 4.6.0, devkitSMS, SMSlib/PSGlib e `makesms`.
O `build_inner.py` encontra o SDK em `sdk/sdcc-portable/bin/sdcc`; não é
necessário `sdcc` no PATH. O host antigo não tinha `javac`; por isso o
`bridge.jar` pré-compilado está no asset de QA.

### 4.1 Validar a build (sem emulador)

```sh
cd /path/to/sms-forge
bash SMS_projects/luta_mugem_rev2/doc/continuity/validate_after_reinstall.sh
```

O script:

- verifica os SHAs da fonte canônica, da fonte v043 e do tarball gerado;
- copia o projeto para um diretório temporário (não toca no `out/` real);
- extrai `out/generated` do tarball e roda `build.sh`;
- canonicaliza o ROM de produção e compara com `087df676…`;
- repete com a fonte v043 e compara com `13b78bd2…`;
- grava logs em `doc/continuity/post_reinstall_*.log`;
- **não** inicia emulador e **não** declara delivery.

Se o SDK não estiver presente, o script para e manda extrair
`sdk_20261021.tar.zst` ou rodar `ensure_toolchain.sh`.

### 4.2 Gerador MUGEN (reprodutibilidade do `out/generated`)

O comando exato foi revalidado em 2026-10-21: gerou
`versus_scene_runtime.h` e os 50 banks byte-idênticos aos do projeto; apenas o
caminho do manifesto de saída diferiu.

```sh
cd /path/to/sms-forge
rm -rf /tmp/ryu_ken_cross_check
PYTHONPATH=tools/sms_wrapper python3 -m mugen2sms versus-cut \
  --p1-source SMS_projects/luta_mugem_rev2/data/source_mugen/ryu/ryu.zip \
  --p1-config SMS_projects/luta_mugem_rev2/doc/continuity/config/ryu_pilot_diag.json \
  --p2-source SMS_projects/luta_mugem_rev2/data/source_mugen/ken/Ken_Majik_.zip \
  --p2-config SMS_projects/luta_mugem_rev2/doc/continuity/config/ken_pilot_diag.json \
  --out /tmp/ryu_ken_cross_check
sha256sum /tmp/ryu_ken_cross_check/versus_scene_runtime.h
# esperado: 19edb320606f660a6a13c67933b99a3d5d19e0501acd2995e2250370cac98949
```

O tarball versionado (`doc/continuity/assets/ryu_ken_cross_generated_20261021.tar.gz`)
é a fonte de verdade para a build; o gerador é para auditoria/regeneração.
Os ZIPs de origem estão versionados em `data/source_mugen/`:
`ryu.zip` sha256 `6db7e29d…`, `Ken_Majik_.zip` sha256 `b244ec9a…`.

### 4.3 Emulador e os eixos que faltam

Com os assets extraídos e uma sessão privada de emulador (leia
`tools/sms_wrapper/.agent/workflows/emulator-isolated-session.md`):

```sh
SMS_projects/luta_mugem_rev2/run.sh
```

O `run.sh` é do projeto; a sessão de QA/automação deve usar
`tools/sms_wrapper/emulator_session.py` e controles privados. Não rode build
com sessão de emulador viva. Depois da build:

1. boot determinístico;
2. gameplay com input scriptado;
3. FPS/frame advance no emulador;
4. áudio isolado/mix;
5. render/fidelidade no framebuffer/evidência;
6. SAT real/linha e §129 no SHA novo;
7. atualizar `doc/10` e os manifests antes de qualquer claim.

Os eixos `boot_emulador`, `gameplay`, `fps_constante`, `audio` e
`memory_bank_atualizado` continuam abertos após a validação de build; o
`[BUILD OK]` lista exatamente esses eixos como restantes.

---

## 5. Validação feita neste host e no clone remoto

Executada em 2026-10-21, no host BigLinux/Manjaro, a partir do clone local
(`bdb32e7`) e do tarball gerado versionado:

| Build | SHA bruto | Diff vs canônico | SHA canonicalizado | Veredito |
|---|---|---|---|---|
| produção (`042ba22e…`) | `9873b3ff…` | `0x7FE6`, `0x7FFA` | `087df676…` | **PASS canonicalizable** |
| v043 (`eb5576ad…`) | `26b30567…` | `0x7FE6`, `0x7FFA` | `13b78bd2…` | **PASS canonicalizable** |

O diff é exatamente o byte de data do header SDSC (`0x7FE6`) e o checksum SEGA
(`0x7FFA`/`0x7FFB`), que depende da data. O payload `[0x0000,0x7FE4)` e o
restante do ROM são idênticos. O checksum é `sum(rom[:0x7FF0]) & 0xFFFF`,
little-endian em `0x7FFA`. O script `verify_canonical.py` implementa e testa
essa normalização; ele recusa qualquer diferença fora desses offsets.

Logs versionados:

- `doc/continuity/VALIDATION_20261021_script.log` — execução completa do
  `validate_after_reinstall.sh`;
- `doc/continuity/VALIDATION_20261021_prod.log` e
  `..._v043.log` — primeira execução manual;
- `doc/continuity/post_reinstall_*.log` — logs da execução do script;
- `doc/continuity/assets/tool_selfchecks.txt` — self-checks das ferramentas.

**Pós-push (GitHub):** um clone esparso direto do remoto, no commit
`e3eb26b` da branch `feat/luta-mugen-motor`, passou
`sha256sum -c doc/continuity/ASSETS.sha256` e repetiu produção + v043 com os
mesmos resultados (`9873b3ff…`→`087df676…`, `26b30567…`→`13b78bd2…`). O SDK
usado foi o mesmo binário do asset `sdk_20261021.tar.zst`; a extração do asset
deve ser repetida no host novo. Log:
`VALIDATION_20261021_github_clone.log`.

**Limite honesto:** isso prova build/reprodutibilidade de payload. Não prova
que a ROM boota neste host novo, nem gameplay/fps/áudio. A regra de ferro
continua.

---

## 6. Checklist pós-formatação

### Antes de formatar (host atual)

- [x] Fonte, dados, docs e scripts no Git (`bdb32e7` + commit de continuidade).
- [x] ROM canônica, ROM v043, relatório/custódia B.2b-3b e tarball gerado em
  `doc/continuity/`.
- [x] Assets grandes preparados (`/mnt/sdcard/continuity_release/`).
- [x] Build de produção e v043 revalidada neste host.
- [x] Gerador MUGEN revalidado byte a byte.
- [ ] Upload da release e verificação de hashes (executar e registrar).
- [ ] Cópia externa de `luta_mugen/out` se esse irmão for necessário.
- [ ] Backup de credenciais/SSH/estado do agente, se necessário.

### Depois de formatar

- [ ] `git clone` + `git checkout feat/luta-mugen-motor` (ou tag + full asset).
- [ ] `gh auth login` e configurar git user/email/chave.
- [ ] Baixar assets e `sha256sum -c RELEASE_ASSETS.sha256`.
- [ ] Extrair SDK/emuladores/QA na raiz.
- [ ] Rodar `validate_after_reinstall.sh` e conferir PASS/PASS.
- [ ] Ler `doc/10`, `doc/27` e o handoff da raiz.
- [ ] Rodar a regressão viva no emulador; só então claim de delivery.
- [ ] Atualizar `doc/10` com o resultado do host novo.

---

## 7. Próximas decisões humanas (não tomadas por este documento)

1. **v044**: aprovar a lista 5/3 pré-computada (gerador, seleção espacial e
   custo) ou declarar o teto do sprite-only.
2. **Híbrido**: investir no writer row-batched/contíguo (≤66 T/célula) ou
   manter o sprite-only.
3. **FX**: BG, SAT ou adiado; o híbrido libera SAT mas custou 27–31% no v037.
4. **Empacotamento 1 MB**: header `0x4C` vs arquivo de 52 bancos; aprovação
   explícita antes de promover.
5. **Guarda BlastEm + L139**: auto-padding/limite de máscara; aprovação.
6. **doc/15, manifest, `engine_quality_contract.json`, CRAM P0/P1/P2,
   reancoragem D2/G, `vram_plan.py`**: pendências de fechamento.
7. **Áudio/rodadas/HUD**: ainda não implementados; nenhum claim de áudio.

Nenhuma dessas decisões foi promovida neste snapshot.

---

## 8. EIO do irmão `luta_mugen`

- `SMS_projects/luta_mugen` apresenta EIO pré-existente no working tree;
  `git status` mostra deletes aparentes. **Não** foram stageados; **não** foi
  executado `fsck`, remount ou cópia forçada.
- O estado commitado do irmão existe no Git; `bdb32e7` contém 206 caminhos do
  projeto. O `out/` de ~3,3 GB não está na release; se for necessário, copie
  para disco externo antes de formatar, sem tentar reparar o EIO.
- O snapshot de workspace e o handoff da raiz documentam o ocorrido; este
  projeto não depende do `luta_mugen` para buildar.

---

## 9. Comandos de emergência

```sh
# Onde está o commit que contém este doc?
git log -1 --format='%H %s' -- SMS_projects/luta_mugem_rev2/doc/27-continuidade-reinstalacao-2026-10-21.md

# Confirmar tag e branch
git rev-parse continuity-20261021
git rev-parse feat/luta-mugen-motor

# Verificação rápida da ROM canônica
sha256sum SMS_projects/luta_mugem_rev2/doc/continuity/assets/luta_mugem_rev2_canonical_087df676.sms
# 087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65

# Build + canonicalização (sem emulador)
bash SMS_projects/luta_mugem_rev2/doc/continuity/validate_after_reinstall.sh

# Se o SDK não estiver presente
tools/sms_wrapper/ensure_toolchain.sh
```

Se algo divergir, **pare**: não promova, não sobrescreva `out/rom` canônico e
não trate narrativa como evidência. Compare com os hashes acima e leia o
relatório B.2b-3b antes de qualquer mudança.
