#!/usr/bin/env python3
"""build_inner.py — FONTE UNICA de logica de build do SMSForge.

Nenhum projeto tem logica propria: os shims build.sh/bat delegam AQUI.

Pipeline:
  1. valida esqueleto (.mddev/project.json)
  2. pre-gates: recursos (res/) + procedencia
  3. toolchain: sdcc >= 4.2 + devkitSMS (SMSlib.lib, PSGlib.lib, crt0_sms.rel)
     ausente -> FAIL_AMBIENTE (exit 2) com instrucao. NUNCA simula.
  4. compila src/*.c -> linka (crt0 primeiro, libs depois) -> makesms
  5. registra out/build_record.json + changelog/roms/build_vNNN/rom.sms
  6. SMS_EVIDENCE=1 -> capture_evidence.py

Exit: 0 build | 1 reprovação (gate ou compilador) | 2 ambiente ausente
"""
import sys, os, json, glob, shutil, subprocess, argparse, shlex, tempfile, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SMS_SINGLE_SPRITE_GEOMETRIES = {(8, 8), (8, 16), (16, 16)}

def fail(msg, code):
    print(f"[BUILD {('FAIL_AMBIENTE' if code == 2 else 'FAIL')}] {msg}")
    return code

def resource_kind_for_path(project, path):
    """Classify SMS resources before the indexed-PNG contract is audited.

    `res/sprites/` may hold either one hardware-sized graphic or a larger
    8x8-aligned metasprite/animation sheet. Large images are sheets; the
    independent sprite-mode gate checks their actual SMS metasprite use.
    """
    rel = os.path.relpath(path, project).replace(os.sep, "/")
    if not rel.startswith("res/sprites/"):
        return "bg"
    from png_io import png_size
    try:
        size = png_size(path)
    except (OSError, Exception):
        # Let check_png report corrupt/unsupported bytes; do not treat them as
        # a valid physical sprite based on an unreadable header.
        return "sheet"
    return "sprite" if size in SMS_SINGLE_SPRITE_GEOMETRIES else "sheet"

def self_check_resource_routing():
    """Valid single sprites/sheets route correctly; an off-grid sheet fails."""
    import tempfile, shutil
    from png_io import write_indexed_png
    from audit_validate_resources import check_png
    root = tempfile.mkdtemp(prefix="smsbuild_resource_route_")
    try:
        cases = (
            ("single_8x8.png", 8, 8, "sprite", True),
            ("single_8x16.png", 8, 16, "sprite", True),
            ("single_16x16.png", 16, 16, "sprite", True),
            ("pose_sheet_80x80.png", 80, 80, "sheet", True),
            ("bad_sheet_18x80.png", 18, 80, "sheet", False),
        )
        palette = [(0, 0, 0), (85, 85, 85)]
        for name, w, h, expected_kind, should_pass in cases:
            path = os.path.join(root, "res", "sprites", name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            write_indexed_png(path, w, h, palette, [bytes([1] * w) for _ in range(h)])
            kind = resource_kind_for_path(root, path)
            assert kind == expected_kind, (name, kind, expected_kind)
            errors = check_png(path, kind)
            if should_pass:
                assert not errors, f"{name} deveria passar em {kind}: {errors}"
            else:
                assert any("grid 8x8 violado" in e for e in errors), \
                    f"{name} off-grid deveria reprovar: {errors}"
        print("[SELF-CHECK OK] build resource routing: 8x8/8x16/16x16 sprites, 80x80 sheet and off-grid rejection")
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)

def find_toolchain():
    """Retorna dict com caminhos ou None com motivo."""
    import shutil as sh
    sdk = os.path.normpath(os.path.join(HERE, "..", "..", "sdk"))
    sdcc = sh.which("sdcc") or os.path.join(sdk, "sdcc-portable", "bin", "sdcc")
    if not os.path.exists(sdcc):
        return None, ("sdcc nao encontrado no PATH nem em " + sdk +
                      "/sdcc-portable/bin | Rode tools/sms_wrapper/ensure_toolchain.sh")
    ver_out = subprocess.run([sdcc, "--version"], capture_output=True, text=True).stdout
    import re
    m = re.search(r"(\d+)\.\d+\.\d+", ver_out)
    major = int(m.group(1)) if m else 0
    if major < 4:
        return None, f"sdcc {major}.x < 4.2 requerido ({ver_out.splitlines()[0][:60]})"
    root = os.environ.get("SMS_DEVKITSMS") or os.path.normpath(os.path.join(
        HERE, "..", "..", "sdk", "devkitSMS"))
    need = {
        "SMSlib.h": os.path.join(root, "SMSlib", "SMSlib.h"),
        "SMSlib.lib": os.path.join(root, "SMSlib", "SMSlib.lib"),
        "PSGlib.h": os.path.join(root, "PSGlib", "PSGlib.h"),
        "PSGlib.lib": os.path.join(root, "PSGlib", "PSGlib.lib"),
        "crt0_sms.rel": os.path.join(root, "crt0", "crt0_sms.rel"),
    }
    missing = [n for n, p in need.items() if not os.path.exists(p)]
    if missing:
        return None, ("devkitSMS incompleto em " + root +
                      "; faltam: " + ", ".join(missing) +
                      ". Siga sdk/README.md")
    makesms = sh.which("makesms")
    if not makesms:
        cand = os.path.join(root, "tools", "makesms")
        if os.path.exists(cand):
            makesms = cand
        else:
            return None, "makesms nao encontrado (rode ensure_toolchain.sh)"
    return {"sdcc": sdcc, "makesms": makesms,
            "inc": [os.path.dirname(need["SMSlib.h"]),
                    os.path.dirname(need["PSGlib.h"])],
            "peep": os.path.join(root, "peep-rules.txt"),
            **need}, None

def pre_gates(project):
    from audit_validate_resources import check_png
    from audit_provenance import audit as provenance_audit
    from audit_sprite_mode import (analyze as sprite_mode_analyze, declared_mode,
                                   uses_metasprite, collect_sprites)
    errors = []
    pngs = sorted(glob.glob(os.path.join(project, "res", "**", "*.png"), recursive=True))
    for p in pngs:
        kind = resource_kind_for_path(project, p)
        errors += [f"recursos/{os.path.relpath(p, project)}: {e}"
                   for e in check_png(p, kind)]
    errors += ["procedencia: " + e for e in provenance_audit(project)]
    # §25/L006: geometria de sprite (modo declarado no fonte vs largura do asset)
    srcs = sorted(glob.glob(os.path.join(project, "src", "*.c")))
    probs, _ = sprite_mode_analyze(declared_mode(srcs),
                                   collect_sprites(project, []),
                                   uses_metasprite(srcs))
    errors += ["geometria de sprite: " + e for e in probs]
    # L009: marcador __at() sem volatile pode ser apagado pelo SDCC — a leitura
    # dele nao e evidencia e o diagnostico se inverte.
    from audit_debug_markers import audit as markers_audit
    errors += ["marcador de depuracao: " + e for e in markers_audit(project)]
    # L011: coordenada literal fora das 24 linhas renderizadas. XYtoADDR nao
    # checa limite: y=26 escreve na cauda nao renderizada da PNT (invisivel) e
    # y>=28 invade a SAT (corrompe sprites).
    from audit_tilemap_bounds import check_source as tilemap_check
    for c in srcs:
        f, _ = tilemap_check(open(c, encoding="utf-8", errors="replace").read(), c)
        errors += [f"name table: {os.path.relpath(p, project)}:{ln} {mc} — {why}"
                   for p, ln, mc, why in f]
    return errors

# Eixo de runtime -> artefato que o sustenta (relativo ao projeto).
# `None` = qualquer .wav em out/evidence (audit_audio.py e quem julga o conteudo).
AXIS_EVIDENCE = {
    "boot_emulador": "out/evidence/evidence.json",
    "gameplay": "out/evidence/evidence.json",
    "fps_constante": "out/evidence/fps.json",
    "audio": None,
    "memory_bank_atualizado": "doc/10-memory-bank.md",
}

def _sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def rom_birth_mtime(project, rom):
    """Data de NASCIMENTO deste executavel, nao a do ultimo `sdcc`.

    Recompilar sem mudar uma linha reescreve a ROM com conteudo identico e
    mtime novo. Toda checagem por data passa a ver a evidencia como velha e
    rebaixa eixos sem que nada tenha mudado — foi o que reprovou o eixo de
    audio num rebuild no vazio. O §26 ja comparava conteudo na democao; aqui a
    correcao vai a RAIZ, para que todo consumidor de mtime (inclusive o
    reconcile_claims, que e outro processo) fique correto de graca.

    As copias em changelog/roms/ sao feitas com shutil.copy2, que preserva a
    data. A copia MAIS ANTIGA com o mesmo sha256 e o instante em que este
    binario passou a existir. E mais honesto que a data do compilador.
    """
    try:
        sha = _sha256(rom)
    except OSError:
        return None
    times = [os.path.getmtime(c)
             for c in glob.glob(os.path.join(project, "changelog", "roms",
                                             "*", "rom.sms"))
             if _sha256(c) == sha]
    return min(times) if times else None

def uses_code_size_optimization(toolchain, source_relative):
    """Allow selected modules to use SDCC size opts without slowing every hot path.

    `optimization=code_size` remains the project-wide switch. Projects may
    instead name a small set of source paths in `code_size_sources`; paths are
    relative to the project root and normalized to `/` on every host.
    """
    if toolchain.get("optimization") == "code_size":
        return True
    wanted = {str(p).replace("\\", "/") for p in
              (toolchain.get("code_size_sources") or [])}
    source = str(source_relative).replace("\\", "/")
    return source in wanted


def reserve_candidate_dir(project, destination):
    """Reserve a new build directory without touching the nominal output."""
    root = os.path.realpath(os.path.join(project, "out", "candidates"))
    target = os.path.realpath(os.path.abspath(destination))
    if target == root or os.path.commonpath((root, target)) != root:
        raise ValueError("build candidato deve ficar em out/candidates/<nome>")
    if os.path.lexists(destination) or os.path.lexists(target):
        raise ValueError("diretorio candidato ja existe; escolha outro destino")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    os.mkdir(target)
    return target


def project_include_dirs(project, manifest):
    """Resolve declared project include directories without leaving its root."""
    project = os.path.realpath(project)
    dirs = []
    inc = os.path.join(project, "inc")
    if os.path.isdir(inc):
        dirs.append(inc)
    values = manifest.get("toolchain", {}).get("include_dirs", [])
    if not isinstance(values, list) or any(not isinstance(p, str) or not p for p in values):
        raise ValueError("toolchain.include_dirs deve ser uma lista de caminhos")
    for value in values:
        path = os.path.realpath(os.path.join(project, value))
        if os.path.isabs(value) or os.path.commonpath((project, path)) != project:
            raise ValueError("include_dir deve ficar dentro do projeto")
        if not os.path.isdir(path):
            raise ValueError("include_dir ausente: " + value)
        dirs.append(path)
    return dirs


def candidate_inputs(project, manifest, tc, srcs, manifest_path=None):
    """Hash actual SDCC includes, linked libraries and explicit mapper banks.

    SDCC's dependency output follows the preprocessor and includes generated
    headers. The manifest's -mbank arguments are makesms inputs, not SDCC
    includes. A second snapshot after linking detects a changed input; it is
    not an atomic filesystem snapshot.
    """
    files = {os.path.join(project, ".mddev", "project.json"), __file__,
             tc["sdcc"], tc["makesms"], tc["SMSlib.lib"], tc["PSGlib.lib"],
             tc["crt0_sms.rel"]}
    if manifest_path:
        files.add(manifest_path)
    if os.path.isfile(tc.get("peep", "")):
        files.add(tc["peep"])
    search = subprocess.run([tc["sdcc"], "-mz80", "--print-search-dirs"],
                            cwd=project, capture_output=True, text=True)
    if search.returncode:
        raise ValueError("falha ao identificar componentes da toolchain SDCC")
    sections = {"programs": [], "libdir": []}
    current = None
    for line in search.stdout.splitlines():
        if line.endswith(":"):
            current = line[:-1] if line[:-1] in sections else None
        elif current and line.strip():
            sections[current].append(line.strip())
    for section, names in (("programs", ("sdcc", "sdcpp", "sdasz80", "sdldz80")),
                           ("libdir", ("z80.lib",))):
        for name in names:
            path = next((os.path.join(d, name) for d in sections[section]
                         if os.path.isfile(os.path.join(d, name))), None)
            if path is None:
                raise ValueError("componente SDCC nao identificado: " + name)
            files.add(path)
    toolchain_config = manifest.get("toolchain", {})
    if toolchain_config.get("link_extra"):
        raise ValueError("link_extra ainda nao possui custodia de entradas para candidato")
    for src in srcs:
        relative = os.path.relpath(src, project)
        command = [tc["sdcc"], "-mz80", "-M"]
        if uses_code_size_optimization(toolchain_config, relative):
            command.append("--opt-code-size")
        command += ["-I" + inc for inc in tc.get("inc", [])]
        command += ["-I" + inc for inc in project_include_dirs(project, manifest)]
        command.append(relative)
        result = subprocess.run(command, cwd=project, capture_output=True, text=True)
        if result.returncode:
            raise ValueError("falha ao identificar includes SDCC: " + result.stderr.strip())
        _, sep, dependencies = result.stdout.replace("\\\n", " ").partition(":")
        if not sep:
            raise ValueError("saida de dependencias SDCC invalida")
        for dependency in shlex.split(dependencies):
            files.add(os.path.join(project, dependency))
    extra = list(toolchain_config.get("makesms_extra") or [])
    i = 0
    while i < len(extra):
        option = extra[i]
        if option == "-mbank":
            if i + 1 >= len(extra):
                raise ValueError("-mbank sem arquivo de entrada")
            bank_spec = extra[i + 1].rsplit(":", 3)
            if len(bank_spec) != 4 or not bank_spec[0]:
                raise ValueError("-mbank deve identificar arquivo e tres campos")
            files.add(os.path.join(project, bank_spec[0]))
            i += 2
        elif option == "-pm":
            i += 1
        else:
            raise ValueError("opcao makesms sem custodia de entradas: " + str(option))
    inputs = {}
    for path in sorted(os.path.realpath(path) for path in files):
        if not os.path.isfile(path):
            raise ValueError("entrada de build ausente: " + path)
        inputs[os.path.relpath(path, project)] = _sha256(path)
    return inputs


def demote_stale_axes(project, rom, axes, prev_sha=None):
    """Eixo de runtime so sobrevive a um build novo se a evidencia for POSTERIOR
    a ROM recem-linkada. Binario novo invalida prova de binario velho (§seal).

    Sem isto o merge de eixos carrega para a frente provas de outro executavel —
    foi assim que a entrega F6 do laboratorio_01 acabou sustentada por capturas
    6h mais VELHAS que a ROM entregue.
    """
    # NAO ha atalho por sha aqui. Havia: quando o rebuild produzia binario
    # identico, a funcao retornava PRESERVADO e pulava a democao inteira. O
    # motivo era legitimo na epoca — recompilar renovava o mtime da ROM e
    # rebaixava eixos a cada build no vazio — mas essa causa foi corrigida na
    # RAIZ por rom_birth_mtime, que devolve a data de nascimento do executavel
    # antes desta checagem. O atalho virou um segundo remendo para um problema
    # que ja nao existia, e passou a deixar passar evidencia genuinamente velha:
    # em 07/09/2026 os eixos boot_emulador, fps_constante e memory_bank do
    # MSSF2T ficaram TRUE sustentados por artefatos 8h MAIS VELHOS que a ROM,
    # porque o sha nao tinha mudado entre dois builds.
    #
    # Com o mtime de nascimento restaurado, a comparacao por data ja da o
    # resultado certo sozinha: evidencia gravada depois que este executavel
    # surgiu sobrevive ao rebuild identico; evidencia anterior a ele cai.
    rom_mtime = os.path.getmtime(rom)
    notes = []
    for axis, rel in AXIS_EVIDENCE.items():
        if not axes.get(axis):
            continue
        if rel is None:
            cands = glob.glob(os.path.join(project, "out", "evidence", "*.wav"))
            newest = max((os.path.getmtime(c) for c in cands), default=None)
        else:
            p = os.path.join(project, rel)
            newest = os.path.getmtime(p) if os.path.exists(p) else None
        if newest is None:
            axes[axis] = False
            notes.append(("REBAIXADO", f"{axis}: sem artefato de evidencia"))
        elif newest < rom_mtime:
            axes[axis] = False
            notes.append(("REBAIXADO", f"{axis}: evidencia ANTERIOR a esta ROM "
                          f"({rel or 'audio .wav'})"))
    return notes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=os.getcwd())
    ap.add_argument("--skip-pre-gates", action="store_true",
                    help="apenas para depurar o compilador; NUNCA em entrega")
    ap.add_argument("--build-dir", help="novo diretorio sob PROJECT/out/candidates; "
                    "preserva ROM, recibo e changelog nominais")
    ap.add_argument("--manifest", help="manifesto alternativo dentro do projeto; "
                    "somente com --build-dir")
    ap.add_argument("--self-check", action="store_true",
                    help="prova o roteamento sprite/sheet com casos válidos e inválidos")
    args = ap.parse_args()
    if args.self_check:
        return self_check_resource_routing()
    project = os.path.abspath(args.project)

    if not os.path.exists(os.path.join(project, ".mddev", "project.json")):
        return fail(f"{project} nao e um projeto (falta .mddev/project.json)", 1)
    nominal_manifest_path = os.path.join(project, ".mddev", "project.json")
    try:
        with open(nominal_manifest_path, "rb") as f:
            nominal_manifest_bytes = f.read()
        nominal_manifest = json.loads(nominal_manifest_bytes)
    except (OSError, ValueError) as e:
        return fail("manifesto nominal invalido: " + str(e), 1)
    if not isinstance(nominal_manifest, dict):
        return fail("manifesto nominal deve ser um objeto", 1)
    manifest_path = nominal_manifest_path
    manifest_bytes = nominal_manifest_bytes
    if args.manifest:
        if not args.build_dir:
            return fail("--manifest exige --build-dir", 1)
        manifest_path = os.path.realpath(os.path.abspath(args.manifest))
        if os.path.commonpath((os.path.realpath(project), manifest_path)) != os.path.realpath(project):
            return fail("manifesto candidato deve ficar dentro do projeto", 1)
        try:
            with open(manifest_path, "rb") as f:
                manifest_bytes = f.read()
            manifest = json.loads(manifest_bytes)
        except (OSError, ValueError) as e:
            return fail("manifesto candidato invalido: " + str(e), 1)
        if not isinstance(manifest, dict) or manifest.get("name") != nominal_manifest.get("name"):
            return fail("manifesto candidato pertence a outro projeto", 1)
    else:
        manifest = nominal_manifest
    if not isinstance(manifest.get("toolchain", {}), dict):
        return fail("toolchain do manifesto deve ser um objeto", 1)
    name = manifest.get("name") or os.path.basename(project)
    candidate = bool(args.build_dir)
    if candidate and (os.path.basename(name) != name or name in (".", "..")):
        return fail("nome de projeto invalido para build candidato", 1)
    if candidate and os.environ.get("SMS_EVIDENCE") == "1":
        return fail("SMS_EVIDENCE automatico nao seleciona ROM candidata; use --session", 1)
    try:
        project_includes = project_include_dirs(project, manifest)
    except ValueError as e:
        return fail(str(e), 1)
    try:
        build_dir = reserve_candidate_dir(project, args.build_dir) if candidate else os.path.join(project, "out")
    except (OSError, ValueError) as e:
        return fail(str(e), 1)
    obj_dir = os.path.join(build_dir, "obj")
    log_path = os.path.join(build_dir, "logs_build.txt")
    os.makedirs(obj_dir, exist_ok=True)
    record = {"project": name, "date": "", "steps": {}, "axes": {}}

    # SMS_STRICT=1: checagens de WORKSPACE (caras, ~3s) — nao rodam a cada build.
    # Obrigatorias antes de entrega: ver workflow release-rom.md.
    if os.environ.get("SMS_STRICT") == "1":
        for tool, label in (("validate_measurement_tools.py", "§19 ferramentas de medicao"),
                            ("audit_doc_sync.py", "sincronia doc<->repo"),
                            # L001: sem rodar em lugar nenhum, o gate de grandezas
                            # nao pegou uma regressao introduzida no proprio
                            # AGENTS.md horas depois de ser escrito.
                            ("audit_hardware_constants.py", "grandezas de hardware"),
                            ("audit_learning_capture.py", "captura de licao")):
            r = subprocess.run([sys.executable, os.path.join(HERE, tool)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print(r.stdout + r.stderr, end="")
                return fail(f"modo estrito: {label} reprovou", 1)
        print("[STRICT] ferramentas de medicao provadas + doc sincronizada")

    if not args.skip_pre_gates:
        errs = pre_gates(project)
        if errs:
            for e in errs:
                print(f"[FAIL] {e}")
            return 1
        record["steps"]["pre_gates"] = "pass"

    tc, why = find_toolchain()
    if tc is None:
        return fail(why + " | Instale seguindo sdk/README.md. "
                    "O gate NAO simula build.", 2)
    record["steps"]["toolchain"] = "ok"

    srcs = sorted(glob.glob(os.path.join(project, "src", "*.c")))
    if not srcs:
        return fail("nenhum .c em src/", 1)
    if candidate:
        try:
            inputs_before = candidate_inputs(project, manifest, tc, srcs, manifest_path)
        except (OSError, ValueError) as e:
            return fail("identidade das entradas: " + str(e), 1)
        for path, content in ((nominal_manifest_path, nominal_manifest_bytes),
                              (manifest_path, manifest_bytes)):
            key = os.path.relpath(os.path.realpath(path), project)
            if inputs_before.get(key) != hashlib.sha256(content).hexdigest():
                return fail("manifesto mudou durante preparacao; candidato nao registrado", 1)
    objs, logs = [], []
    for src_abs in srcs:
        base = os.path.splitext(os.path.basename(src_abs))[0]
        obj_rel = os.path.relpath(os.path.join(obj_dir, base + ".rel"), project)
        cmd = [tc["sdcc"], "-c", "-mz80", "-o", obj_rel]
        # Projetos com ROM linear no teto podem declarar a troca de objetivo
        # do compilador no manifesto. O custo de fps continua sendo medido no
        # emulador; esta flag nunca substitui o gate de worst-frame.
        toolchain_config = manifest.get("toolchain", {})
        if uses_code_size_optimization(toolchain_config,
                                       os.path.relpath(src_abs, project)):
            cmd.append("--opt-code-size")
        if os.path.exists(tc.get("peep", "")):
            cmd += ["--peep-file", tc["peep"]]
        for inc in tc.get("inc", []):
            cmd += ["-I" + inc]
        cmd += ["-I" + inc for inc in project_includes]
        cmd.append(os.path.relpath(src_abs, project))
        r = subprocess.run(cmd, cwd=project, capture_output=True, text=True)
        logs.append(f"$ {' '.join(cmd)}\n{r.stdout}{r.stderr}")
        if r.returncode != 0:
            open(log_path, "w").write("\n".join(logs))
            return fail(f"compilacao de {src_abs} falhou (log: {log_path})", 1)
        objs.append(obj_rel)
    record["steps"]["compile"] = f"{len(objs)} objeto(s)"

    ihx = os.path.relpath(os.path.join(obj_dir, name + ".ihx"), project)
    link_extra = list(manifest.get("toolchain", {}).get("link_extra") or [])
    link_cmd = ([tc["sdcc"], "-o", ihx, "-mz80", "--no-std-crt0", "--data-loc", "0xC000"]
                + link_extra +
                [tc["crt0_sms.rel"]] +
                objs +
                [tc["SMSlib.lib"], tc["PSGlib.lib"]])
    r = subprocess.run(link_cmd, cwd=project, capture_output=True, text=True)
    logs.append("$ " + " ".join(link_cmd) + f"\n{r.stdout}{r.stderr}")
    open(log_path, "w").write("\n".join(logs))
    if r.returncode != 0 or not os.path.exists(os.path.join(project, ihx)):
        return fail(f"link falhou (log: {log_path})", 1)

    rom_dir = os.path.join(build_dir, "rom")
    os.makedirs(rom_dir, exist_ok=True)
    rom = os.path.join(rom_dir, name + ".sms")
    ms_extra = list(manifest.get("toolchain", {}).get("makesms_extra") or [])
    makesms_cmd = ([tc["makesms"]] + ms_extra +
                   [ihx, os.path.relpath(rom, project)])
    r = subprocess.run(makesms_cmd, cwd=project, capture_output=True, text=True)
    makesms_output = r.stdout + r.stderr
    logs.append("$ " + " ".join(makesms_cmd) + f"\n{makesms_output}")
    open(log_path, "w").write("\n".join(logs))
    if r.returncode != 0 or not os.path.exists(rom):
        detail = makesms_output.strip() or "sem diagnóstico"
        return fail(f"makesms falhou: {detail[:200]} (log: {log_path})", 1)
    size = os.path.getsize(rom)
    record["steps"]["rom"] = f"{rom} ({size} bytes)"

    # higiene: artefatos de compilacao (asm/lst/sym) vazam para a raiz do projeto;
    # move-os para out/obj para nao poluir o arvore.
    if not candidate:
        for ext in (".asm", ".lst", ".sym"):
            leak = os.path.join(project, name + ext)
            if os.path.exists(leak):
                shutil.move(leak, os.path.join(obj_dir, name + ext))

    if candidate:
        if srcs != sorted(glob.glob(os.path.join(project, "src", "*.c"))):
            return fail("lista de fontes mudou durante o build; candidato nao registrado", 1)
        try:
            inputs_after = candidate_inputs(project, manifest, tc, srcs, manifest_path)
        except (OSError, ValueError) as e:
            return fail("identidade das entradas apos build: " + str(e), 1)
        if inputs_before != inputs_after:
            return fail("entradas mudaram durante o build; candidato nao registrado", 1)
        version = subprocess.run([tc["sdcc"], "--version"], capture_output=True, text=True)
        record.update({
            "schema": "smsforge.candidate_build/v1",
            "profile": "candidate_unpromoted",
            "input_sha256": inputs_before,
            "sdcc_version": version.stdout.strip(),
            "rom_sha256": _sha256(rom),
            "rom_mtime": os.path.getmtime(rom),
            "axes": {"build": True, "validation_report": record["steps"].get("pre_gates") == "pass",
                     "boot_emulador": False, "gameplay": False, "fps_constante": False,
                     "audio": False, "memory_bank_atualizado": False},
        })
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=build_dir,
                                             prefix=".build_record_", delete=False) as f:
                tmp_path = f.name
                json.dump(record, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            # No replacement: an unexpected existing record must be preserved.
            os.link(tmp_path, os.path.join(build_dir, "build_record.json"))
        except OSError as e:
            return fail("publicacao do recibo candidato: " + str(e), 1)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        print(f"[BUILD CANDIDATE OK] {rom} ({size}B) | eixos de runtime nao avaliados")
        return 0

    n = 1
    chg = os.path.join(project, "changelog", "roms")
    while os.path.exists(os.path.join(chg, f"build_v{n:03d}")):
        n += 1
    dest = os.path.join(chg, f"build_v{n:03d}", "rom.sms")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(rom, dest)
    record["changelog"] = dest

    # validation_report so e verdadeiro se os pre-gates REALMENTE rodaram e
    # passaram: --skip-pre-gates nao pode produzir registro afirmando validacao.
    record["axes"] = {"build": True,
                      "validation_report": record["steps"].get("pre_gates") == "pass",
                      "boot_emulador": False, "gameplay": False,
                      "fps_constante": False, "audio": False,
                      "memory_bank_atualizado": False}
    prev = os.path.join(project, "out", "build_record.json")
    prev_sha, prev_mtime = None, None
    if os.path.exists(prev):
        try:
            old = json.load(open(prev))
            prev_sha = old.get("rom_sha256")
            prev_mtime = old.get("rom_mtime")
        except (json.JSONDecodeError, OSError):
            pass
    # Binario IDENTICO = o mesmo artefato. Recompilar renova o mtime sem mudar
    # uma linha do executavel, e toda checagem por data passa a ver a evidencia
    # como "velha" — foi o que reprovou o eixo de audio num rebuild sem
    # alteracao nenhuma. O §26 ja tinha sido corrigido para comparar conteudo;
    # devolver o mtime anterior corrige na RAIZ, e de quebra e mais honesto:
    # a data passa a dizer quando este executavel surgiu, nao quando o
    # compilador rodou de novo.
    born = rom_birth_mtime(project, rom)
    if born and born < os.path.getmtime(rom):
        os.utime(rom, (born, born))

    # Eixos de runtime sao DERIVADOS da evidencia, nunca herdados do registro
    # anterior. A heranca nao tinha como comecar: o build inicializa tudo em
    # false e so copiava true de um registro anterior, entao o primeiro true de
    # qualquer projeto so podia ter vindo de edicao a mao do build_record.json —
    # o que o runbook release-rom.md proibe. A derivacao usa os MESMOS
    # predicados de reconcile_claims.axis_support, para que quem grava e quem
    # confere nao possam divergir.
    #
    # Roda DEPOIS de devolver o mtime de nascimento da ROM: o lastro de audio
    # compara a data do .wav com a da ROM, e derivar antes faria um rebuild
    # byte a byte identico invalidar a propria evidencia que acabou de valer.
    import reconcile_claims
    for axis, (supported, _why) in reconcile_claims.axis_support(
            project, record).items():
        if axis in AXIS_EVIDENCE:
            record["axes"][axis] = supported

    # Segunda barreira, e nao redundante: axis_support le o CONTEUDO do json
    # (informative=true, constante_50_60=true), enquanto demote_stale_axes olha
    # a DATA do arquivo. Um evidence.json afirmando informative=true, porem
    # gravado antes desta ROM, passa no primeiro e cai aqui.
    demoted = demote_stale_axes(project, rom, record["axes"], prev_sha)
    record["rom_sha256"] = _sha256(rom)
    record["rom_mtime"] = os.path.getmtime(rom)
    for tag, n in demoted:
        print(f"[EIXO {tag}] {n}")
    json.dump(record, open(os.path.join(project, "out", "build_record.json"), "w"),
              indent=2)

    # Pos-gate: o registro que acabamos de escrever tem lastro nos artefatos?
    from reconcile_claims import reconcile
    probs, _ = reconcile(project)
    if probs:
        for p in probs:
            print(f"[FAIL] conciliacao: {p}")
        return fail("build_record afirma eixo sem lastro no artefato", 1)

    print(f"[BUILD OK] {rom} ({size}B) | eixos restantes para entrega: "
          f"{[k for k, v in record['axes'].items() if not v]}")
    if os.environ.get("SMS_EVIDENCE") == "1":
        import capture_evidence as ev
        rc = ev.capture(project, rom)
        if rc != 0:
            return rc
    return 0

if __name__ == "__main__":
    sys.exit(main())
