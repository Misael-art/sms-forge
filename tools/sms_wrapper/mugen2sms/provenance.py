"""Proveniencia por simbolo no schema canonico do Forge
(tools/sgdk_wrapper/schemas/asset_provenance_manifest.schema.json).

O conversor gravava `source_kind: third_party_mugen_conversion` e
`acceptance_status: technical_candidate`, que nao existem no schema. O manifesto
inteiro ficava invalido e cada simbolo virava `asset_provenance_undeclared`, e
esse falso "sem proveniencia" escondia os achados reais.

Mapeamento, sem inventar enum:
  - source_kind = procedural_composed_from_authored: o codigo so recorta,
    quantiza e paletiza arte autoral que ja existia (o pacote MUGEN); a fonte e
    o hash ficam em authored_source / authored_source_hash, como o schema exige.
  - acceptance_status = placeholder: saida de maquina nao e arte final ate
    aprovacao visual humana, e a redistribuicao de terceiros nao foi verificada.
  - license declara a permissao como NAO verificada, em vez de omiti-la.
Sons nao sao simbolos visuais (o schema nao tem WAV): vao para
doc/mugen/<id>_audio_provenance.json.

Decisao humana x metadado derivado (protecao contra reconversao):
  - `doc/mugen/provenance_annotations.json` e do HUMANO: notas, restricoes de distribuicao,
    aprovacoes (cada uma presa ao sha256 do asset) e historico. O conversor nunca reescreve o que
    esta la; so ACRESCENTA (captura de nota manual, remocao de simbolo, aprovacao que ficou velha).
  - Ao gravar, a nota escrita a mao no manifesto/audio que o conversor nao gera e capturada para
    as anotacoes ANTES de sobrescrever; a saida = nota derivada + nota humana + restricoes.
  - Aprovacao so vale se o sha256 do asset atual for o aprovado. Pixel mudou: a aprovacao nao se
    aplica (fica `stale` no historico) e o simbolo volta a placeholder. Nada e apagado.
  - Simbolo que sumiu na reconversao entra no historico como `removed` com o ultimo hash.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ANNOTATIONS = "doc/mugen/provenance_annotations.json"
ACCEPTANCE_ENUM = {"final", "placeholder", "debug_lab", "visual_lab_control"}

SOURCE_KIND = "procedural_composed_from_authored"
ACCEPTANCE = "placeholder"
LICENSE = "terceiros: uso local autorizado pelo usuario; redistribuicao NAO verificada"
PENDING = "technical_candidate: aprovacao visual humana pendente"
VISUAL_KINDS = {"IMAGE", "SPRITE", "TILESET", "TILEMAP", "MAP", "BITMAP", "PALETTE"}


def entry(symbol: str, kind: str, asset_path: str, generated_by: str,
          package: str, package_sha256: str, notes: str) -> dict:
    return {
        "res_symbol": symbol,
        "res_kind": kind,
        "asset_path": asset_path,
        "source_kind": SOURCE_KIND,
        "acceptance_status": ACCEPTANCE,
        "generated_by": generated_by,
        "authored_source": f"mugen-package:{package}",
        "authored_source_hash": f"sha256:{package_sha256}",
        "license": LICENSE,
        "notes": f"{notes}; {PENDING}",
    }


def load_annotations(project: Path) -> dict:
    path = project / ANNOTATIONS
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"schema": "mugen2sms.provenance_annotations/v1",
            "rule": "dono: humano. O conversor so acrescenta (captura/remocao/stale); nunca apaga nem reescreve.",
            "symbols": {}}


def _save_annotations(project: Path, ann: dict) -> None:
    path = project / ANNOTATIONS
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(ann, indent=2, ensure_ascii=False) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")


def _asset_sha(project: Path, asset_path: str) -> str | None:
    for base in (project / "res", project):
        f = base / asset_path
        if f.is_file():
            return hashlib.sha256(f.read_bytes()).hexdigest()
    return None


def _hist(sym: dict, event: dict) -> None:
    if event not in sym.setdefault("history", []):
        sym["history"].append(event)


def _capture(ann: dict, symbol: str, old_notes: str, derived_notes: str) -> None:
    """Texto da nota antiga que o conversor nao gera = nota humana; guarda antes de sobrescrever."""
    known = ann["symbols"].get(symbol, {})
    rendered = set(known.get("human_notes", [])) | {f"restricao: {r}" for r in known.get("restrictions", [])}
    norm = lambda t: t.strip().rstrip(".").strip()  # noqa: E731  compara sem o ponto final; guarda o texto exato
    have = {norm(x) for x in (derived_notes or "").split(";")} | {norm(x) for x in rendered}
    extra = [p.strip() for p in (old_notes or "").split(";") if norm(p) and norm(p) not in have]
    if not extra:
        return
    sym = ann["symbols"].setdefault(symbol, {})
    notes = sym.setdefault("human_notes", [])
    for p in extra:
        if p not in notes:
            notes.append(p)
            _hist(sym, {"event": "captured_from_manual_edit", "text": p})


def _apply(project: Path, ann: dict, e: dict, derived_notes: str) -> dict:
    """Saida = derivado + notas/restricoes humanas + aprovacao valida para ESTE hash."""
    sym = ann["symbols"].get(e["res_symbol"])
    if not sym:
        return e
    out = dict(e)
    extra = list(sym.get("human_notes", [])) + [f"restricao: {r}" for r in sym.get("restrictions", [])]
    if extra:
        out["notes"] = "; ".join([derived_notes] + extra)
    cur = _asset_sha(project, e["asset_path"]) if "asset_path" in e else None
    for ap in sym.get("approvals", []):
        if ap.get("status") not in ACCEPTANCE_ENUM:
            raise ValueError(f"{e['res_symbol']}: status de aprovacao fora do schema: {ap.get('status')!r}")
        if cur and ap.get("asset_sha256") == cur:
            out["acceptance_status"] = ap["status"]
        elif ap.get("asset_sha256") != cur:
            _hist(sym, {"event": "approval_stale", "status": ap.get("status"),
                        "approved_sha256": ap.get("asset_sha256"), "current_sha256": cur})
    return out


def write_visual(project: Path, prefix: str, entries: list[dict]) -> Path:
    """Troca as entradas derivadas com `prefix` pelas novas, preservando a decisao humana (anotacoes)."""
    for e in entries:
        if e["res_kind"] not in VISUAL_KINDS:
            raise ValueError(f"{e['res_symbol']}: {e['res_kind']} nao e simbolo visual")
    path = project / "doc" / "asset_provenance_manifest.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
        "schema_version": "1.0.0", "declared_at": "1970-01-01T00:00:00Z", "entries": []}
    ann = load_annotations(project)
    old = {e["res_symbol"]: e for e in data.get("entries", []) if e.get("res_symbol", "").startswith(prefix)}
    new_syms = {e["res_symbol"] for e in entries}
    for e in entries:
        if e["res_symbol"] in old:
            _capture(ann, e["res_symbol"], old[e["res_symbol"]].get("notes", ""), e["notes"])
    for sym, e in old.items():
        if sym not in new_syms:
            _hist(ann["symbols"].setdefault(sym, {}), {"event": "removed", "asset_path": e.get("asset_path"),
                                                        "last_notes": e.get("notes", "")})
    data["project_name"] = project.name
    data["entries"] = [e for e in data.get("entries", []) if not e.get("res_symbol", "").startswith(prefix)]
    data["entries"].extend(_apply(project, ann, e, e["notes"]) for e in entries)
    _save_annotations(project, ann)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def write_audio(project: Path, cid: str, package: str, package_sha256: str, sounds: list[dict]) -> Path:
    path = project / "doc" / "mugen" / f"{cid}_audio_provenance.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    ann = load_annotations(project)
    if path.exists():
        prev = {s["res_symbol"]: s for s in json.loads(path.read_text(encoding="utf-8")).get("sounds", [])}
        for s in sounds:
            if s["res_symbol"] in prev:
                _capture(ann, s["res_symbol"], prev[s["res_symbol"]].get("notes", ""), s["notes"])
        for sym, s in prev.items():
            if sym not in {x["res_symbol"] for x in sounds}:
                _hist(ann["symbols"].setdefault(sym, {}), {"event": "removed", "asset_path": s.get("asset_path"),
                                                            "last_notes": s.get("notes", "")})
    out = []
    for s in sounds:
        sym = ann["symbols"].get(s["res_symbol"], {})
        extra = list(sym.get("human_notes", [])) + [f"restricao: {r}" for r in sym.get("restrictions", [])]
        out.append(dict(s, notes="; ".join([s["notes"]] + extra)) if extra else s)
    _save_annotations(project, ann)
    path.write_text(json.dumps({
        "schema": "mugen2sms.audio_provenance/v1",
        "package": package, "package_sha256": package_sha256, "license": LICENSE,
        "sounds": out,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def migrate(project: Path) -> dict:
    """Converte entradas antigas do conversor (enums fora do schema) sem reconverter.

    A fonte e o hash vem dos relatorios de conversao do proprio projeto; entradas
    WAV saem do manifesto visual para o arquivo de audio do personagem.
    """
    path = project / "doc" / "asset_provenance_manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    reports = {}
    for rep in (project / "doc" / "mugen").glob("*_conversion_report.json"):
        r = json.loads(rep.read_text(encoding="utf-8"))
        cid = r.get("character", {}).get("id") or rep.name.split("_conversion_report")[0]
        reports[cid] = r["input"]
    kept, audio, changed = [], {}, 0
    for e in data.get("entries", []):
        if e.get("source_kind") != "third_party_mugen_conversion":
            kept.append(e)
            continue
        sym = e["res_symbol"]
        cid = "hud" if sym.startswith("mg_hud_") else sym[3:].split("_", 1)[0]
        src = reports.get(cid)
        if src is None:
            raise ValueError(f"{sym}: sem relatorio de conversao para '{cid}'")
        if e["res_kind"] == "WAV":
            audio.setdefault(cid, (src, []))[1].append(
                {"res_symbol": sym, "asset_path": e["asset_path"], "notes": e.get("notes", "")})
            changed += 1
            continue
        notes = e.get("notes", "").split("; redistribuicao")[0].split("; uso local")[0]
        kept.append(entry(sym, e["res_kind"], e["asset_path"], e["generated_by"],
                          src["package"], src["sha256"], notes))
        changed += 1
    data["entries"] = kept
    data["project_name"] = project.name
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for cid, (src, sounds) in audio.items():
        write_audio(project, cid, src["package"], src["sha256"], sounds)
    return {"migrated": changed, "audio_files": sorted(audio)}
