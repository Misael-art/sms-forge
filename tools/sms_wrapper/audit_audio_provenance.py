#!/usr/bin/env python3
"""audit_audio_provenance.py — asset de audio (.psg) tem procedencia declarada (L058/L059/§47).

audit_provenance cobre so PNG — e por esse furo um .psg entrou na ROM sem
entrada no manifest (music_ken_stage.psg, MSSF2T, 2026-09-07). Este gate
aplica o mesmo principio a res/audio/:

- COBERTURA: todo *.psg em <project>/res/audio/ precisa de entrada em
  doc/audio_provenance_manifest.json ({"assets": [...]}, campo "file" e o
  path relativo, ex.: "res/audio/x.psg"). Orfao reprova (L058).
- INTEGRIDADE: para cada entrada, o arquivo existe; sha256 e bytes
  declarados batem com o blob real em disco (L058).
- REFERENCIA DE PORT: origin contendo "transcri", "port" ou "arranjo"
  (case-insensitive) exige "reference" (dict) com "file" existente e
  "sha256" batendo com o arquivo referenciado (L059). Entrada autoral
  pura nao precisa de reference.

Aditivo: audit_psg_channel_binding le "file"/"channels" deste mesmo
manifest e continua valido.

Uso:
  audit_audio_provenance.py --project DIR
  audit_audio_provenance.py --self-check
Exit: 0 ok/skip | 1 reprova | 3 uso
"""
import argparse, hashlib, json, os, shutil, sys, tempfile

PORT_HINTS = ("transcri", "port", "arranjo")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(65536), b""):
            h.update(blk)
    return h.hexdigest()


def _psg_on_disk(project):
    out = []
    audio_dir = os.path.join(project, "res", "audio")
    if not os.path.isdir(audio_dir):
        return out
    for dirpath, _, files in os.walk(audio_dir):
        for fn in sorted(files):
            if fn.endswith(".psg"):
                rel = os.path.relpath(os.path.join(dirpath, fn), project)
                out.append(rel.replace(os.sep, "/"))
    return sorted(out)


def audit_project(project):
    errors = []
    man_path = os.path.join(project, "doc", "audio_provenance_manifest.json")
    on_disk = _psg_on_disk(project)
    if not os.path.isfile(man_path):
        if on_disk:
            return ["doc/audio_provenance_manifest.json ausente mas existem "
                    ".psg em res/audio/ (L058)"], None
        return [], "skip: sem res/audio/ e sem manifest de audio"
    try:
        man = json.load(open(man_path, encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return [f"manifest de audio invalido: {e}"], None
    entries = {}
    for a in man.get("assets") or []:
        f = str(a.get("file") or "").replace("\\", "/")
        if f:
            entries[f] = a
    for f in on_disk:
        if f not in entries:
            errors.append(f"{f}: .psg orfao — sem entrada no manifest de "
                          f"procedencia de audio (L058)")
    for f, a in entries.items():
        fp = os.path.join(project, f)
        if not os.path.isfile(fp):
            errors.append(f"{f}: declarado no manifest mas ausente em disco")
            continue
        want_sha = str(a.get("sha256") or "")
        if not want_sha:
            errors.append(f"{f}: sem sha256 declarado no manifest")
        elif want_sha != _sha256(fp):
            errors.append(f"{f}: sha256 divergente do blob em disco (L058)")
        want_bytes = a.get("bytes")
        got_bytes = os.path.getsize(fp)
        if want_bytes is None:
            errors.append(f"{f}: sem bytes declarado no manifest")
        elif want_bytes != got_bytes:
            errors.append(f"{f}: bytes declarados ({want_bytes}) divergem do "
                          f"arquivo ({got_bytes}) (L058)")
        origin = str(a.get("origin") or "").lower()
        if any(hint in origin for hint in PORT_HINTS):
            ref = a.get("reference")
            if not isinstance(ref, dict):
                errors.append(f"{f}: origin declara port/transcricao/arranjo "
                              f"sem reference hasheada (L059)")
                continue
            rfile = str(ref.get("file") or "")
            rpath = os.path.join(project, rfile)
            if not rfile or not os.path.isfile(rpath):
                errors.append(f"{f}: reference '{rfile}' nao existe (L059)")
                continue
            rsha = str(ref.get("sha256") or "")
            if rsha != _sha256(rpath):
                errors.append(f"{f}: sha256 da reference '{rfile}' divergente "
                              f"do arquivo referenciado (L059)")
    return errors, None


def _self_check():
    d = tempfile.mkdtemp(prefix="smsaudioprov_")
    try:
        os.makedirs(os.path.join(d, "res", "audio"))
        os.makedirs(os.path.join(d, "doc", "referencias"))
        open(os.path.join(d, "res", "audio", "autoral.psg"), "wb").write(b"AUTORAL-1")
        open(os.path.join(d, "res", "audio", "port.psg"), "wb").write(b"PORT-1")
        open(os.path.join(d, "doc", "referencias", "trilha_original.psg"),
             "wb").write(b"REF-ORIGINAL")
        sha_autoral = _sha256(os.path.join(d, "res", "audio", "autoral.psg"))
        sha_port = _sha256(os.path.join(d, "res", "audio", "port.psg"))
        sha_ref = _sha256(
            os.path.join(d, "doc", "referencias", "trilha_original.psg"))
        man_path = os.path.join(d, "doc", "audio_provenance_manifest.json")

        def write(man):
            json.dump(man, open(man_path, "w"))

        def base():
            return {"assets": [
                {"file": "res/audio/autoral.psg",
                 "origin": "stream autoral sintetizado para PSGlib",
                 "sha256": sha_autoral, "bytes": 9},
                {"file": "res/audio/port.psg",
                 "origin": "transcricao do tema de referencia comercial",
                 "sha256": sha_port, "bytes": 6,
                 "reference": {"file": "doc/referencias/trilha_original.psg",
                               "sha256": sha_ref}},
            ]}

        # 1. .psg orfao reprovado (entradas integrais continuam de pe)
        man = base()
        write(man)
        open(os.path.join(d, "res", "audio", "orphan.psg"), "wb").write(b"ORFAO")
        e, skip = audit_project(d)
        assert any("orfao" in x and "orphan.psg" in x for x in e), \
            f"faltou reprovar orfao: {e}"
        assert not any("autoral.psg" in x or "port.psg" in x for x in e), e

        # 2. entrada declarada ausente em disco
        os.remove(os.path.join(d, "res", "audio", "orphan.psg"))
        os.remove(os.path.join(d, "res", "audio", "port.psg"))
        e, _ = audit_project(d)
        assert any("port.psg" in x and "ausente em disco" in x for x in e), e
        open(os.path.join(d, "res", "audio", "port.psg"), "wb").write(b"PORT-1")

        # 3. sha256 e bytes divergentes
        man = base()
        man["assets"][0]["sha256"] = "0" * 64
        man["assets"][0]["bytes"] = 999
        write(man)
        e, _ = audit_project(d)
        assert any("sha256 divergente" in x and "autoral.psg" in x for x in e), e
        assert any("bytes declarados" in x and "autoral.psg" in x for x in e), e

        # 4. port sem reference reprovado
        man = base()
        del man["assets"][1]["reference"]
        write(man)
        e, _ = audit_project(d)
        assert any("port.psg" in x and "reference hasheada" in x for x in e), \
            f"faltou reprovar port sem reference: {e}"

        # 5. reference com hash divergente reprovado
        man["assets"][1]["reference"] = {
            "file": "doc/referencias/trilha_original.psg", "sha256": "0" * 64}
        write(man)
        e, _ = audit_project(d)
        assert any("reference" in x and "divergente" in x for x in e), e

        # 6. port com reference hasheada + autoral pura: aprovados
        man = base()
        write(man)
        e, skip = audit_project(d)
        assert not e, f"fixture integra nao deveria reprovar: {e}"

        # 7. projeto sem audio e sem manifest = skip
        f2 = tempfile.mkdtemp(prefix="smsaudioprov2_")
        try:
            e, skip = audit_project(f2)
            assert not e and skip and skip.startswith("skip:"), \
                f"projeto sem audio deveria skip: {e}/{skip}"
        finally:
            shutil.rmtree(f2, ignore_errors=True)

        # 8. manifest ausente com .psg em disco reprova
        os.remove(man_path)
        e, skip = audit_project(d)
        assert not skip and any("manifest" in x and "ausente" in x for x in e), e
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] audio_provenance (orfao, entrada ausente, "
          "sha256/bytes divergentes, port sem reference, reference "
          "divergente, autoral+port integrais aprovados)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()
    errors, skip = audit_project(os.path.abspath(a.project))
    if skip and not errors:
        print(f"[PASS] {skip}")
        return 0
    if errors:
        for e in errors:
            print(f"[FAIL] {e}")
        print(f"[FAIL] {len(errors)} problema(s) de procedencia de audio "
              "(L058/L059).")
        return 1
    print("[PASS] procedencia de audio integral (cobertura, integridade, "
          "referencia de port)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
