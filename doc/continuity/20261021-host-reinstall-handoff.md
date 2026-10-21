# Continuidade — reinstalação do host (2026-10-21)

> **Leia este arquivo primeiro em um host novo.**
> Ele existe para que o SMSForge possa continuar a partir do GitHub depois de
> formatar o computador, sem reconstruir contexto de memória.
>
> **Repositório:** <https://github.com/Misael-art/sms-forge> (público)
> **Branch de trabalho:** `feat/luta-mugen-motor`
> **Tag de continuidade:** `continuity-20261021`
> **Snapshot anterior:** `da86de3` (branch `backup/pre-continuity-20261021`)
>
> O commit/tag exato é o que contém este arquivo. Não confie em um SHA escrito
> aqui; confirme com `git rev-parse continuity-20261021`.

---

## 1. Retomar em um host novo

```sh
git clone https://github.com/Misael-art/sms-forge.git
cd sms-forge
git fetch --tags
git checkout continuity-20261021
```

O clone normal traz **código, documentação, ROMs changelog e o framework**.
Os arquivos grandes/ignorados (`out/`, `sdk/`, emuladores e arte não versionada)
estão nos assets da release `continuity-20261021`; baixe-os antes de rodar os
gates que dependem de emulador/evidência. Veja §4.

### Toolchain

```sh
tools/sms_wrapper/ensure_toolchain.sh
```

O script é rootless, idempotente e prova a toolchain com um smoke-test real
(SDCC → devkitSMS → makesms → ROM). Ele instala SDCC portátil em
`sdk/sdcc-portable/` e devkitSMS em `sdk/devkitSMS/`.

Dependências de runtime/QA (documentadas, não todas instaláveis pelo script):

- Java (Emulicious e `session_bridge/ForgeSMS.java`);
- Xvfb, `xdotool`, `ffmpeg`/`ffprobe`, ALSA/PulseAudio (sink privado);
- Python 3 com as dependências usadas por `tools/sms_wrapper/`;
- Emulicious (jar) em `tools/emuladores/`; o SHA do jar usado no bundle cap5
  está no `bundle.json` (`db185a1e…`).
- `tools/emuladores/emulators.json` registra os caminhos esperados.

### Build e validação mínima

```sh
cd SMS_projects/openbor_sms_rev1
./build.sh
sha256sum out/rom/openbor_sms_rev1.sms
# esperado no snapshot cap5:
# 701379cc88e074f5874e161cd7e6307b04be48456c1b469172f84a58d79a6da9
```

O build rederiva `out/build_record.json` a partir do lastro real; não edite os
eixos à mão.

---

## 2. Estado exato no momento do snapshot

**Projeto:** `SMS_projects/openbor_sms_rev1`
**ROM:** `701379cc88e074f5874e161cd7e6307b04be48456c1b469172f84a58d79a6da9`
(131072 B, NTSC, cap5).
**Build record:** 7/7 (`build`, `validation_report`, `boot_emulador`,
`gameplay`, `fps_constante`, `audio`, `memory_bank_atualizado`).
**Boot determinístico:** PASS (2 execuções idênticas).
**Não é delivery:** época visual/delivery continua bloqueada.

### Evidência canônica projetada (cap5)

| Arquivo | SHA-256 |
|---|---|
| `out/evidence/evidence.json` | `a473d670d8f05e4de9a5e8c4b855c73ab3656d47e77f0089a296efcfa2947fb0` |
| `out/evidence/fps.json` | `1ccfa0af7b352be65573fb0878e66c006010ffd6ca594ec74849588271fb132c` |
| `out/evidence/audio_701379cc.wav` | `f16b48b81648b69aa40930afdca7d670139e83c4dc08b31d296daffaddf61439` |
| `out/evidence/o3_cap5_consumer_20261020/bundle.json` | `2f69939a1a3f1d83ef46998da03e691f60ee1df8d472df242da12e67cf9fbd1a` |
| `out/evidence/o3_cap5_consumption_20261020.json` | `e1af7fad1bf540bc5046655f070ca06df76c1bd8c804ca45e794700dc02af10a` |

Fontes da projeção: consumer `2f69939a…`, consumo `e1af7fad…`, MRP3
`5f7f838f…` (sessão `43d33c39…`, 59,39/59,44/59,57 fps NTSC, 1.441 frames),
QA runtime `5fe14599…` (sessão `5aeb7960…`, 2/2 PASS) e QA visual `a7662a8b…`
(sessão `37b1481d…`, 2/2 de legibilidade/integridade PASS, 5 achados).

### Achado visual aberto (não promovido)

O QA visual cap5 encontrou que a lâmina do ataque fica à **esquerda** do
jogador enquanto o inimigo está à direita: no índice 27, lâmina em x≈42–64 e
inimigo em x≈86–132. O dano é legível pela barra (80→64 px) e pela reação de
dor no índice 38, mas o golpe não toca visualmente o alvo.

Isso **não invalida** os eixos atribuídos de boot/gameplay/FPS/áudio, mas
bloqueia promoção de apresentação, época visual e delivery. A decisão é do
dono: corrigir em novo ROM/Lote C (e refazer a evidência) ou aceitar como
limite conhecido. O Lote C continua com o critério de controle atendido
(i90 < i94) e display não atendido (i102 > i94).

### Pendências registradas

- regressão de gameplay: dano, whiff, profundidade, queda, morte, bordas,
  scroll e áudio concorrente; MWF de ataque scriptado do jogador;
- PAL não medido; decidir PAL ou declarar NTSC-only;
- Lote C / direção do golpe: decisão do dono;
- `audit_render_glitch` sem oráculo full-frame independente;
- 46/47 contatos e altura 200 não alcançados (limites de cobertura);
- archive/version e commit/push adicionais só com autorização explícita.

O documento autoritativo do projeto continua sendo
`SMS_projects/openbor_sms_rev1/doc/10-memory-bank.md`; este handoff é o mapa de
continuidade do host, não substitui o memory bank.

---

## 3. O que está no Git (clone normal)

- Todo o histórico e as 31+ commits que estavam à frente do remoto;
- alterações rastreadas pendentes de todos os projetos (incluindo as remoções
  de curadoria do `master_of_fighters`; o conteúdo removido continua no
  histórico do Git);
- fontes, documentos, artefatos de documentação e arte pequena (<5 MB por
  arquivo) dos projetos;
- `doc/artifact_registry.json`, `doc/artifacts/` do openbor e o registro do
  snapshot;
- `AGENTS.md`, `README.md`, `.gitignore`, `tools/sms_wrapper/`.

Arquivos removidos intencionalmente podem ser recuperados do commit anterior
com `git log --diff-filter=D -- <path>` e `git show <commit>^:<path>`.

## 4. O que está nos assets da release `continuity-20261021`

Baixe com:

```sh
gh release download continuity-20261021 --dir /tmp/smsforge-continuity
```

Os nomes previstos são:

- `smsforge-openbor-out-20261021.tar.zst` — `SMS_projects/openbor_sms_rev1/out/`
  inteiro: ROM cap5, evidence, bundle, QA, build record e logs;
- `smsforge-untracked-large-20261021.tar.zst` — arquivos não rastreados que
  ficaram fora do Git por tamanho (arte grande, `out/` da raiz, arquivos
  >5 MB; inclui o tar de curadoria de `luta_mugen`);
- `smsforge-toolchain-20261021.tar.zst` — `sdk/` e `tools/emuladores/`;
- `smsforge-generated-other-20261021.tar.zst` — `out/` gerado dos outros
  projetos, exceto `luta_mugen/out` (3,3 GB, gerado e reproduzível; veja §5);
- manifesto de hashes em `doc/continuity/20261021-assets.sha256`.

Extraia sempre preservando os caminhos relativos:

```sh
mkdir -p /tmp/smsforge-restore
tar -C /tmp/smsforge-restore -xf smsforge-openbor-out-20261021.tar.zst
# copie o conteúdo para o clone, ex.:
rsync -a /tmp/smsforge-restore/SMS_projects/openbor_sms_rev1/out/ \
  SMS_projects/openbor_sms_rev1/out/
```

## 5. O que NÃO foi preservado (gerado/efêmero)

Estes diretórios são saídas geradas ou estado de ferramenta; não são fonte e
podem ser reconstruídos. Eles **não** entram na release por tamanho/tempo:

- `SMS_projects/luta_mugen/out/` (~3,3 GB);
- `SMS_projects/*/out/` dos outros projetos (o subconjunto menor vai no asset
  `generated-other`; `luta_mugen/out` fica de fora);
- `.mimosa/` (~727 MB, hooks/estado de sessão do agente);
- caches `__pycache__/`, `.pytest_cache/`, temporários;
- `sdk/` e `tools/emuladores/` **são** arquivados, mas também podem ser
  reinstalados por `ensure_toolchain.sh`/download oficial.

Se você precisa de `luta_mugen/out` ou de outro `out/` integral, copie-o para
um disco externo **antes** de formatar; ele não está nesta release.

## 6. Segurança e credenciais

O repositório é público. Nada de token, chave SSH, `.env` ou estado de sessão
foi incluído no snapshot. Depois da reinstalação:

```sh
gh auth login
# reconfigurar git user/email e chave SSH se for usar SSH
```

O antigo `~/.config/gh`, chaves SSH, `~/.ai-memory`/banco de memória do agente
e configurações locais **não** estão no GitHub. Se você precisa deles, faça
backup separado antes de formatar. O contexto durável do projeto está no
memory bank e neste handoff.

## 7. Ordem sugerida de retomada

1. Clonar e checkout da tag; rodar `ensure_toolchain.sh`.
2. Restaurar `openbor/out` da release; conferir os SHAs da §2.
3. Ler `doc/10-memory-bank.md` (autoridade #1) e este handoff.
4. Decidir o achado de direção do golpe/Lote C e PAL/NTSC.
5. Rodar a regressão de gameplay no ROM atual; se houver correção de
   apresentação, gerar novo SHA e refazer consumer/QA/projeção.
6. Só então archive/version e commit/push adicionais.

---

**Regra final:** se não foi visto rodando no emulador, não existe. Este
snapshot preserva o que foi medido; não promove o que ainda está bloqueado.
