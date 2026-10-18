# Plano 1 — Motor MUGEN→SMS (S0–S4) — Implementação

> **Para agentes executores:** SUB-SKILL OBRIGATÓRIO: use superpowers:executing-plans (ou subagent-driven-development) para implementar tarefa por tarefa. Passos usam checkboxes (`- [ ]`). **Este plano PARA ao final da S4** — o runtime (S5/S6) é o Plano 2, que só pode ser escrito com os números da S3.

**Goal:** construir `tools/sms_wrapper/mugen2sms/` — conversor offline, determinístico e reutilizável de MUGEN→devkitSMS — que parseia e classifica `ken_masters_adv` inteiro e gera artefatos SMS (tiles, paletas, tabelas clsn/comandos, manifest) aprovados pelos gates do workspace.

**Architecture:** espelho do `mugen2sgdk_forge` (MD): `inventory → parsers → ir → analysis → converters → generators → validate → reports`. Regras inegociáveis herdadas: **IR não conhece SMS; generators não leem MUGEN**. Parsers/IR são copiados do doador MD com renomeação de pacote e contrato de paridade testado; `analysis/converters/generators` são novos e SMS-nativos.

**Tech Stack:** Python 3 + Pillow (parse/convert), pytest (testes), SDCC/devkitSMS (só consome output na S5+ — nenhum C é escrito neste plano), gates em `tools/sms_wrapper/*.py`.

**Spec:** `SMS_projects/luta_mugen/doc/11-gdd.md` (autoridade #2 — lido junto com este plano; se conflito, o GDD vence e a tarefa para).

## Global Constraints

- Acervo `/mnt/sdcard/Projects/Mugenesis/Base de Estudo/` é **somente leitura**; derivados reais vivem em `SMS_projects/luta_mugen/out/local_study/` e **nunca** entram no Git; fixtures de teste são sintéticos.
- Zero caminho absoluto do outro workspace em material ativo depois da S0 (higiene): depois do cópia+manifest, nada referencia `Sgdk Forge`.
- Números de Mega Drive nunca como lei do SMS — constantes SMS citadas do header devkitSMS (autoridade #8): `sms/devkitSMS/SMSlib/SMSlib.h` (`SPRITEMODE_TALL`, `SMS_addMetaSprite` SMSlib.h:215, `METASPRITE_END` SMSlib.h:214) e `sdk/README.md`.
- Python dos módulos novos: sem floats em tabela gerada (Q8.8 como inteiros), output determinístico (byte-idêntico entre execuções), `--self-check` em toda ferramenta que gera número de medição (§19).
- Todo commit: escopo de arquivo explícito (`git add <paths>`), nunca `git add -A` — árvore pode conter WIP de outro projeto (MSSF2T tem `fight.c` WIP: **não tocar, não stagear**).
- Status: nada é declarado "pronto" sem teste rodado neste plano; gate de emulador só existe no Plano 2.

---

### Task 1: S0 — Baseline do projeto + cópia doada com contrato de paridade

**Files:**
- Create: `tools/sms_wrapper/mugen2sms/` (pacote: `__init__.py`, `__main__.py`, `inventory.py`, `source.py`, `character.py`, `palette_contract.py`, `provenance.py`, `parsers/{__init__,ini,air,sff,cns,cmd,snd,stage}.py`, `ir/{__init__,expr,opcodes,controllers,vm}.py`, `analysis/__init__.py`, `converters/__init__.py`, `generators/__init__.py`, `validate/__init__.py`, `reports/.gitkeep`)
- Create: `SMS_projects/luta_mugen/doc/doacao_md_mugen2sms.json` (manifest da cópia: caminho relativo-no-doador → caminho local → SHA-256 do arquivo doador **antes** da renomeação)
- Create: `tools/sms_wrapper/mugen2sms/tests/test_donation_parity.py`
- Modify: `SMS_projects/luta_mugen/.gitignore` (criar com `out/local_study/`, `__pycache__/`, `*.pyc`)

**Interfaces:**
- Produz: pacote importável `mugen2sms` (`python3 -m mugen2sms` a partir de `tools/sms_wrapper/`), com `mugen2sms.inventory`, `mugen2sms.character.load`, `mugen2sms.source` nas assinaturas do doador.
- Consome: doador em `/mnt/sdcard/Projects/Sgdk Forge/tools/mugen2sgdk_forge/mugen2sgdk_forge/` (referência de cópia **desta tarefa apenas**).

- [ ] **Step 1: Commit do baseline existente** (projetos template + GDD aprovado)

```bash
cd /mnt/sdcard/Projects/SMSForge
git status --short SMS_projects/luta_mugen | head
git add SMS_projects/luta_mugen tools/sms_wrapper/.agent 2>/dev/null || git add SMS_projects/luta_mugen
git commit -m "feat(luta_mugen): bootstrap do projeto + GDD S0-S6 travado (motor MUGEN->SMS)"
```

- [ ] **Step 2: Copiar os arquivos do doador listados em Files, renomeando o pacote**

```bash
SRC="/mnt/sdcard/Projects/Sgdk Forge/tools/mugen2sgdk_forge/mugen2sgdk_forge"
DST="tools/sms_wrapper/mugen2sms"
mkdir -p $DST/{parsers,ir,analysis,converters,generators,validate,reports}
for f in __init__.py __main__.py inventory.py source.py character.py palette_contract.py provenance.py \
         parsers/__init__.py parsers/ini.py parsers/air.py parsers/sff.py parsers/cns.py parsers/cmd.py parsers/snd.py parsers/stage.py \
         ir/__init__.py ir/expr.py ir/opcodes.py ir/controllers.py ir/vm.py; do
  cp "$SRC/$f" "$DST/$f"
done
grep -rl "mugen2sgdk_forge" $DST | xargs sed -i 's/mugen2sgdk_forge/mugen2sms/g'
# subpacotes SMS-nativos (existem no doador só como dir de código MD, que NAO copiamos):
touch $DST/analysis/__init__.py $DST/converters/__init__.py $DST/generators/__init__.py $DST/validate/__init__.py
```

Se `grep -rl "mugen2sgdk_forge" $DST` ainda listar algo depois do sed → Pare: renomeação incompleta.

- [ ] **Step 3: Escrever o teste de paridade** (conteúdo local ≡ conteúdo doador normalizado pelo nome do pacote; e o manifest confere)

```python
# tools/sms_wrapper/mugen2sms/tests/test_donation_parity.py
import json, hashlib
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]          # .../mugen2sms
MANIFEST = ROOT.parents[2] / "SMS_projects/luta_mugen/doc/doacao_md_mugen2sms.json"
DONOR_TOKEN = "mugen2sgdk_forge"

def _norm(text: str) -> str:
    return text.replace(DONOR_TOKEN, "mugen2sms")

def _files():
    yield from sorted(p for p in ROOT.rglob("*.py")
                      if "tests" not in p.parts and "__pycache__" not in p.parts)

def test_manifest_exists_with_sha():
    assert MANIFEST.exists(), "rode o passo de registro da doação"
    entries = json.loads(MANIFEST.read_text())["files"]
    assert len(entries) >= 20

@pytest.mark.parametrize("local", list(_files()))
def test_local_file_is_donor_plus_rename(local):
    rel = str(local.relative_to(ROOT))
    entry = next((e for e in json.loads(MANIFEST.read_text())["files"]
                  if e["local"] == rel), None)
    assert entry, f"{rel} sem registro no manifest"
    if "donor_abspath_at_copy_time" not in entry:   # modulo novo do fork SMS
        assert local.read_text() == "", f"{rel} novo deve comecar vazio"
        return
    donor = Path(entry["donor_abspath_at_copy_time"])
    if not donor.exists():
        pytest.skip("doador ausente neste host — SHA do manifest basta")
    sha_donor = hashlib.sha256(donor.read_bytes()).hexdigest()
    assert sha_donor == entry["donor_sha256"], "doador mudou pós-cópia: re-verificar na mão"
    assert _norm(donor.read_text()) == local.read_text(), \
        f"{rel} diverge do doador além do rename"
```

⚠️ `donor_abspath_at_copy_time` vive só no manifest (documentação da origem), nunca em código — é o único lugar onde o caminho do vizinho é permitido, como registro histórico.

- [ ] **Step 4: Gerar o manifest da doação**

```bash
python3 - <<'EOF'
import hashlib, json
from pathlib import Path
SRC = Path("/mnt/sdcard/Projects/Sgdk Forge/tools/mugen2sgdk_forge/mugen2sgdk_forge")
DST = Path("tools/sms_wrapper/mugen2sms")
entries = []
for f in sorted(DST.rglob("*.py")):
    if "tests" in f.parts or "__pycache__" in f.parts: continue
    donor = SRC / f.relative_to(DST)
    if not donor.exists(): continue          # módulos novos (analysis/... ainda vazios)
    entries.append({"local": str(f.relative_to(DST)),
                    "donor_abspath_at_copy_time": str(donor),
                    "donor_sha256": hashlib.sha256(donor.read_bytes()).hexdigest()})
out = {"origin": "mugen2sgdk_forge (SGDK Forge, branch de E3) — cópia em 2026-09-25",
       "policy": "uso local; redistribuicao dos derivados bloqueada no GDD",
       "files": entries}
Path("SMS_projects/luta_mugen/doc/doacao_md_mugen2sms.json").write_text(json.dumps(out, indent=2))
print(len(entries), "arquivos registrados")
EOF
```

- [ ] **Step 5: Rodar testes; importar o pacote**

Run: `cd tools/sms_wrapper && python3 -m pytest -q mugen2sms/tests/test_donation_parity.py && python3 -c "import sys; sys.path.insert(0,'.'); import mugen2sms.inventory, mugen2sms.character; print('import ok')"`
Expected: PASS + `import ok` (se Pillow faltar no ambiente, `pip list | grep -i pillow` e reportar bloqueio — não improvisar dependência fora do wrapper)

- [ ] **Step 6: Commit**

```bash
git add tools/sms_wrapper/mugen2sms SMS_projects/luta_mugen/doc/doacao_md_mugen2sms.json SMS_projects/luta_mugen/.gitignore
git commit -m "feat(mugen2sms): S0 copia doada do mugen2sgdk_forge com contrato de paridade testado"
```

---

### Task 2: S1 — Inventory do acervo, determinístico, com `--self-check`

**Files:**
- Modify: `tools/sms_wrapper/mugen2sms/inventory.py` (herdado; adicionar CLI `--self-check` no estilo dos gates do workspace)
- Create: `tools/sms_wrapper/mugen2sms/tests/test_inventory_selfcheck.py`
- Create (output, gitignored): `SMS_projects/luta_mugen/out/local_study/s1_inventory.json`

**Interfaces:**
- Produz: `mugen2sms.inventory.main(["<Base de Estudo>", "--out", "<json>"])` → exit 0, JSON com `entries[]` (path, formato, sha256, tamanho) e `summary` — schema do doador.
- Produz: `python3 -m mugen2sms.inventory --self-check` → exit 0 auto-validado com fixture sintético em tempdir.

- [ ] **Step 1: Teste falho do self-check**

```python
# tests/test_inventory_selfcheck.py
import subprocess, sys
from pathlib import Path
PKG_ROOT = Path(__file__).resolve().parents[1]

def test_selfcheck_passes():
    r = subprocess.run([sys.executable, "-m", "mugen2sms.inventory", "--self-check"],
                       cwd=PKG_ROOT.parent, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "SELF-CHECK OK" in r.stdout
```

- [ ] **Step 2: Rodar → FAIL** (`python3 -m pytest -q mugen2sms/tests/test_inventory_selfcheck.py`)

- [ ] **Step 3: Implementar `--self-check`** em `inventory.py`: construir em `tempfile.mkdtemp` um zip sintético com um `.def` mínimo (parser doador já lê `[Info]`), rodar `inspect_zip`+`summarize`, afirmar contagens exatas (1 zip, ≥1 entry, sha estável entre duas leituras) e imprimir `[SELF-CHECK OK] inventory`. Modelo a seguir: bloco `--self-check` de `tools/sms_wrapper/audit_specialization.py` (mesma convenção de exit codes 0/1/3).

- [ ] **Step 4: Teste passa; validar contra a ferramenta-mãe**

Run: `python3 tools/sms_wrapper/validate_measurement_tools.py` e registrar se `mugen2sms/inventory.py` precisa entrar na lista de ferramentas de medição do workspace (curadoria — se a lista for fechada, anotar pendência no memory bank em vez de editar a lista).

- [ ] **Step 5: Rodar o inventário real (somente leitura)**

```bash
cd tools/sms_wrapper && python3 -m mugen2sms.inventory "/mnt/sdcard/Projects/Mugenesis/Base de Estudo" \
  --out ../SMS_projects/luta_mugen/out/local_study/s1_inventory.json
```

Expected: exit 0; conferir `summary` contra o achado MD da E1 (proporções: maioria SFF v1/PCX; `.def` de chars ≈22). Divergência estrutural grande = investigar antes de prosseguir (pode ser acervo diferente do MD).

- [ ] **Step 6: Commit (só código/teste — JSON fica gitignored)**

```bash
git add tools/sms_wrapper/mugen2sms/inventory.py tools/sms_wrapper/mugen2sms/tests/test_inventory_selfcheck.py
git commit -m "feat(mugen2sms): S1 inventory com --self-check; acervo inventariado (output local)"
```

---

### Task 3: S2 — Ken parseia inteiro (IR de ponta a ponta) + fixtures sintéticos no Git

**Files:**
- Create: `tools/sms_wrapper/mugen2sms/tests/fixtures/` (`mini.def/air/sff/act/cmd/cns` gerados por builder em `make_fixtures.py`)
- Create: `tools/sms_wrapper/mugen2sms/tests/make_fixtures.py`
- Create: `tools/sms_wrapper/mugen2sms/tests/test_synthetic_character.py`
- Create: `tools/sms_wrapper/mugen2sms/ken_full_parse.py` (script de estudo local; output em `out/local_study/ken_ir.json`)
- Create: `tools/sms_wrapper/mugen2sms/tests/test_ken_full_parse.py` (pula com aviso se acervo ausente)

**Interfaces:**
- Consumes: `mugen2sms.character.load(src, def_name) -> Character` (doador, character.py:96), `mugen2sms.source.Source`.
- Produz: `Character` completo de `ken_masters_adv` serializável a JSON (`dataclasses.asdict` sem perdas — imagens como referência a arquivo+hash, não bytes no JSON).

- [ ] **Step 1: Builder de fixtures sintéticos** (personagem mínimo legal: 1 sprite 16×16 PCX-equivalente em memória, 1 animação 2 frames, clsn, 1 comando, 1 stateline) — arte sintética só aqui, nunca Ken no Git.

- [ ] **Step 2: Teste falho do pipeline sintético**

```python
# tests/test_synthetic_character.py
def test_synthetic_character_loads_and_serializes():
    from mugen2sms.character import load
    from mugen2sms.source import Source
    import dataclasses, json
    root = build_synthetic_char(tmp_path)     # do make_fixtures
    ch = load(Source(root))
    d = dataclasses.asdict(ch)
    json.dumps(d, default=str)                # serializável sem exceção
    assert d["animations"], "sem animacoes"
    assert ch.sprites, "sem sprites"
```

- [ ] **Step 3: Rodar → FAIL; implementar o que faltar na camada copiada** (esperado: só ajustes de interface de `Source`/paths; se a correção tocar lógica de parse, documentar desvio do doador no docstring + commit separado — o teste de paridade da Task 1 vai acusar e precisa ser atualizado conscientemente).

- [ ] **Step 4: `ken_full_parse.py`**: extrai `Base de Estudo/chars/street-fighter/ken_masters_adv.zip` para `out/local_study/ken_masters_adv/`, roda `character.load`, despeja `ken_ir.json` com `{n_sprites, n_animations, n_frames, n_clsn_entries, n_commands, n_states, parse_erros: []}`.

- [ ] **Step 5: Rodar contra Ken de verdade.** Expected: `parse_erros == []` e contagens > 0 em todos os campos. Qualquer erro de parse: corrigir no parser **com teste sintético que reproduz o formato do erro** (regra: bug vira fixture).

- [ ] **Step 6: Prova de canal de input (escopo deste plano = self-check only)**

Run: `python3 tools/sms_wrapper/emulator_input.py --self-check`
Expected: PASS. A prova de input **vivo** fica no Plano 2 (precisa de ROM; foi o eixo que reprovou MSSF2T — lá é o primeiro gate da S5).

- [ ] **Step 7: Testes verdes + commit**

```bash
python3 -m pytest -q mugen2sms/tests
git add tools/sms_wrapper/mugen2sms/tests tools/sms_wrapper/mugen2sms/ken_full_parse.py
git commit -m "feat(mugen2sms): S2 ken_masters_adv parseia inteiro; fixtures sinteticos no repo"
```

---

### Task 4: S3 — Analysis SMS: Ken medido contra o VDP (o número ANTES da arte)

**Files:**
- Create: `tools/sms_wrapper/mugen2sms/analysis/sms_budget.py`
- Create: `tools/sms_wrapper/mugen2sms/analysis/fidelity.py` (classes `direct|approximate|manual|unsupported` por recurso)
- Create: `tools/sms_wrapper/mugen2sms/tests/test_sms_budget_synthetic.py`
- Create (output local): `SMS_projects/luta_mugen/out/local_study/s3_fidelity_ken.json`
- Modify: `SMS_projects/luta_mugen/doc/15-tdd.md` (preencher com os números medidos — pools de RAM/VRAM layout entram no Plano 2 com base aqui)

**Interfaces:**
- Produz: `classify_character(char: Character, limits: SmsLimits) -> FidelityReport` com `per_element[]` (id, classe, motivo) e `totals{direct,approximate,manual,unsupported}`.
- Produz: `SmsLimits(sprites_per_line=8, sat_max=64, tiles_visible_per_frame=..., subpalette_colors=15, vram_bytes=16384, ram_bytes=8192)` — **cada campo com comentário citando header/README (autoridade #8)**; nada de número MD (L001/`audit_hardware_constants`).

- [ ] **Step 1: Testes falhos com casos-limite sintéticos** — sprite de 9 tiles de largura numa linha → `approximate` com motivo `"scanline>8"`; 33 cores usadas → `manual` `"paleta>15uteis"`; pose que cabe tudo → `direct`. Nomes exatos de campo: `classe`, `motivo`.

```python
def test_pose_within_limits_is_direct():
    rep = classify_character(synthetic_char(one_pose_4x8_tiles), SmsLimits.defaults())
    el = rep.by_id["anim:stand.0"]
    assert el.classe == "direct"

def test_wide_pose_classified_approximate():
    rep = classify_character(synthetic_char(wide_pose), SmsLimits.defaults())
    assert rep.by_id["anim:jump.3"].motivo.startswith("scanline")
```

- [ ] **Step 2: FAIL → implementar `sms_budget.py`** (tile-cover por pose: bitmap→grade 8×8, dedup de tiles idênticos, contagem de sprites/scanline no pior par de poses adversário+ego) e `fidelity.py` (walk do Character, um registro por sprite/anim/frame/clsn/cmd/sound).

- [ ] **Step 3: Rodar contra Ken real** e escrever `s3_fidelity_ken.json`. Expected honesto: maioria `approximate`/`unsupported` em sons (PCM→PSG) — o veredito não é negociável, é o dado de entrada do Plano 2.

- [ ] **Step 4: Escrever `doc/15-tdd.md` (rascunho S3)**: pools RAM nomeados com bytes, orçamento VRAM por cena (tiles de Ken dedupados = N × 32 B — número do relatório), estimativa de ROM (32 KB vs necessário → banking Sega mapper como no padrão MSSF2T), e a decisão explícita sobre o que entra no corte jogável (ex.: poses `unsupported` viram `manual` reautorado ou ficam fora).

- [ ] **Step 5: `--self-check` do analysis (mesmo padrão da Task 2, caso-limite embutido) + commit**

```bash
git add tools/sms_wrapper/mugen2sms/analysis tools/sms_wrapper/mugen2sms/tests/test_sms_budget_synthetic.py SMS_projects/luta_mugen/doc/15-tdd.md
git commit -m "feat(mugen2sms): S3 analysis de fidelidade/orcamento — Ken medido contra o VDP"
```

---

### Task 5: S4 — Converters + generators SMS: Ken → artefatos que passam nos gates

**Files:**
- Create: `tools/sms_wrapper/mugen2sms/converters/sms_tiles.py` (bitmap+paleta → tileset 8×8/8×16 com dedup e flip H/V; index 0 transparente)
- Create: `tools/sms_wrapper/mugen2sms/converters/sms_clsn.py` (caixas MUGEN → tabelas int16 Q8-like de hurt/hitbox por frame)
- Create: `tools/sms_wrapper/mugen2sms/converters/sms_cmd.py` (listas de comando → patterns de buffer p/ interpretador do Plano 2)
- Create: `tools/sms_wrapper/mugen2sms/converters/sms_sound.py` (classifica `.snd`→PSG: `direct` só se já mapeável; senão `manual` com esboço de evento PSGlib)
- Create: `tools/sms_wrapper/mugen2sms/generators/smsdev.py` (C arrays `const uint8_t`, `#define X_SIZE`, headers idempotentes, manifest SHA por símbolo)
- Create: `tools/sms_wrapper/mugen2sms/tests/test_converters_golden.py` (casos pequenos com saída tile-exata conhecida)
- Create: `SMS_projects/luta_mugen/inc/ken_*.h` **gerados no build de estudo local** — no Git entram só os *testes*; headers reais de arte Ken ficam em `out/local_study/generated/` (política de licença)

**Interfaces:**
- Consumes: `Character` (IR) + `FidelityReport` (S3) — só elementos `direct|approximate` viram artefato; `manual/unsupported` viram linha no relatório.
- Produz: `generate(character, fidelity, out_dir) -> GenerationManifest{entries:[{symbol, size_bytes, source_files_sha256}], generated_sha256}` — o formato casa com `audit_rom_asset_binding.py` e `audit_symbol_size_sync.py` (consume na S5+).

- [ ] **Step 1: Testes falhos de conversão com saída conhecida**

```python
def test_8x8_checkerboard_dedups_to_2_tiles():
    ts = to_sms_tiles(pose_from_bitmap(checker_bitmap()))
    assert ts.unique_tiles == 2 and ts.flips_used >= 1

def test_define_size_matches_array_len():
    h = render_header(gen)
    assert array_len(h["KEN_STAND_TILES"]) == int(h["KEN_STAND_TILES_SIZE"])
```

- [ ] **Step 2: FAIL → implementar `sms_tiles.py` primeiro** (é o coração: quantização às 2 subpaletas 6-bit com delta-E via `palette_contract` herdado, index 0, 8×16 quando `SPRITEMODE_TALL` reduz tiles).

- [ ] **Step 3: `sms_clsn`, `sms_cmd`, `sms_sound`, `generators/smsdev.py`** na mesma cadência teste→fail→implement.

- [ ] **Step 4: Gates do workspace sobre o output gerado (sintético, commitável)** — cena metasprite em JSON aprovada por `audit_sprite_line_sim.py` (≤8/linha com os piores frames de Ken contados na S3), `audit_validate_resources.py`, `audit_provenance.py` (source_kind correto: `photo_or_render_derived`? Não — MUGEN original é arte de terceiros autorizada p/ uso local; declarar no manifest com a política da Task 1).

- [ ] **Step 5: Rodada Ken completa local** (`out/local_study/generated/`) + `validate_measurement_tools.py` no conjunto novo de ferramentas + relatório final `s4_generation_report.json`.

- [ ] **Step 6: Commit (código+testes+relatório sintético; derivados Ken fora)**

```bash
git add tools/sms_wrapper/mugen2sms
git commit -m "feat(mugen2sms): S4 converters/generators SMS com golden tests e gates do harness"
```

---

## Fim do Plano 1 — entrega e ponte para o Plano 2

Entregue: motor capaz de transformar um arquivo MUGEN em artefatos SMS auditados, com Ken medido (S3) e gerado (S4). Ao fechar: atualizar `doc/10-memory-bank.md` do projeto com status REAL (documentado/implementado/buildado — **sem ROM ainda, nenhum eixo de emulador**), e escrever o Plano 2 (runtime: FSM interpretador + cena 01→03 + gates de emulador: boot determinístico, input vivo, fps, worst-frame, evidence bundle).

**Requisito de honestidade do plano:** se S3 mostrar que Ken não cabe (ex.: >8 sprites/scanline mesmo após recorte em poses críticas), o Plano 2 nasce com contrato de escala re-travado (canvas menor/limite de poses) — e isso é decisão humana registrada no GDD, não ajuste silencioso.
