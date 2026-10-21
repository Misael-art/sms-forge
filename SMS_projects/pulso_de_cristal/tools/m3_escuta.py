#!/usr/bin/env python3
"""m3_escuta.py — cabine de escuta das JANELAS DO RUNTIME M3 (não das faixas).

O player do M2 (escuta_player.py) escuta faixas completas com piano-roll do
.psg. Aqui o objeto é outro: uma janela curta do ROM real, com a cena
comprovada por sonda (probe_state), contadores de arbitração e o veredito do
gate de áudio. Roll de partitura não serve: a janela não é a faixa inteira.

Três modos:
  python3 tools/m3_escuta.py --open         # gera a cabine e abre
  python3 tools/m3_escuta.py --verify       # confere byte a byte o que a cabine serve
  python3 tools/m3_escuta.py --collect      # ingere o veredito exportado pelo navegador
Exit: 0 ok | 1 sem janelas / veredito divergente | 2 self-check reprovado | 3 uso
"""
import argparse, base64, datetime, glob, hashlib, json, os, re, subprocess, sys

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESC = os.path.join(PROJECT, "out", "escuta")

# rótulo + fato verificado de cada janela (o que o humano deve conferir)
# ordem = como se escuta: cena, depoisPause/reprise, depois o par do caso 4.
JANELAS = [
    ("w1_attract_continuous", "Cena 01 · atração desde o boot (12 s)",
     "inclui o piano-forte pedido no roteiro (att 12→0 em 120 f); "
     "state=0 na captura. Conferir: o ataque é crescente, não constante. "
     "Ganho do host estava BAIXO nesta tomada (peak 2937) — comparar com w2/w3, "
     "não com w4/w6."),
    ("w2_dawn_continuous", "Cena 02 · aurora contínua (4 s)",
     "probe_state=2 na ENTRADA e na SAÍDA (a cena é realmente a aurora); "
     "track=1 playing=1. Conferir: nível e timbre depois do conserto da atenuação."),
    ("w5_dawn_silent", "Cena 02 · Pause (SILENT) — silêncio autoral (4 s)",
     "Pause FÍSICO acionado ANTES da janela e zero input dentro dela: peak=0 / "
     "rms=0 / 0% ativo enquanto probe_frame vai 476→920 (+444 f) e probe_state "
     "fica 2. Conferir: é SILÊNCIO mesmo, não emulador congelado — o núcleo "
     "rodou a janela inteira."),
    ("w6_dawn_reprise", "Cena 02 · retomada pós-Pause (4 s)",
     "bordas de Pause antes da janela (liga/desliga, 240 f cada) e então 4 s "
     "sem input: peak 5673 / rms 1120 / 63,2% ativo. Conferir com o ouvido o "
     "que a métrica não diz: a reprise CONTINUA do ponto ou REINICIA a faixa? "
     "doc/17 exige 'repreendida, não reiniciada'."),
    ("w4_dawn_mix", "Cena 02 · caso 4 — SELECT sobre a música (4 s)",
     "dois SELECT em f60 e f164 por roteiro de frames; cnt_sfx_crystal 0→2. "
     "Conferir: ouve-se o cristal *por cima* da música, sem sumir a música."),
    ("w4b_dawn_control", "Cena 02 · controle do caso 4 (4 s)",
     "MESMO roteiro de frames, SELECT sempre 0; cnt_sfx_crystal=0. "
     "Conferir: é a mesma música, sem os dois transientes. "
     "Ouça w4 e w4b SEGUIDOS — a arbitração PSGlib substitui o canal 1, então a "
     "diferença de energia é ~0 (Δ máx +0,080 medido) e só o ouvido separa "
     "timbre de nível."),
    ("w3_dawn_select", "Cena 02 · caso 4 com presses de PAREDE (4 s)",
     "dois SELECT por `input`+`run` interleavados (1 s/1 s), cnt_sfx_crystal "
     "0→2. Conferir: a fase da música varia entre corridas, então esta janela "
     "não é o par limpo do controle — valeu como diagnóstico, não como prova."),
    ("w3b_dawn_control", "Cena 02 · controle dos presses de parede (4 s)",
     "mesma janela e mesmos tempos, zero presses; cnt_sfx_crystal=0. Par de w3."),
]

def sha(p):
    return sha_bytes(open(p, "rb").read())

def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()

def current_rom_sha():
    rom = os.path.join(PROJECT, "out", "rom", "pulso_de_cristal.sms")
    return sha(rom) if os.path.isfile(rom) else None

HTML = os.path.join(ESC, "m3_escuta.html")

def payload_from_html():
    """Relê o que a cabine SERVE, em vez de confiar no que ela deveria servir."""
    if not os.path.isfile(HTML):
        return None
    raw = open(HTML, encoding="utf-8").read()
    m = re.search(r'<script type="application/json" id="data">(.*?)</script>',
                  raw, re.S)
    if not m:
        return "sem-blob"
    return json.loads(m.group(1))

def collect():
    rom = os.path.join(PROJECT, "out", "rom", "pulso_de_cristal.sms")
    rom_sha = sha(rom) if os.path.isfile(rom) else None
    itens = []
    for nome, rotulo, nota in JANELAS:
        wav = os.path.join(ESC, nome + ".wav")
        if not os.path.isfile(wav):
            print("[AVISO] sem %s.wav — pulando" % nome)
            continue
        binding = {}
        jb = os.path.join(ESC, nome + ".audio.json")
        if os.path.isfile(jb):
            with open(jb, encoding="utf-8") as f:
                cand = json.load(f)
            binding = {k: cand.get(k) for k in
                       ("session_id", "rom_sha256", "peak", "samples",
                        "effective_seconds", "claim", "audio_route")}
        binding["wav_sha256"] = sha(wav)
        binding["wav"] = os.path.relpath(wav, PROJECT)
        # frescor: julgar wav de outra ROM é o erro que o selo existe para evitar
        binding["rom_atual"] = bool(rom_sha) and binding.get("rom_sha256") == rom_sha
        gate = os.path.join(PROJECT, "out", "logs", "audit_audio_%s.txt" % nome)
        itens.append({"nome": nome, "rotulo": rotulo, "nota": nota,
                      "binding": binding,
                      "gate": open(gate, encoding="utf-8").read().strip()
                              if os.path.isfile(gate) else "não registrado",
                      "wav_b64": base64.b64encode(open(wav, "rb").read()).decode()})
    return {"gerado_em": datetime.datetime.now().isoformat(timespec="seconds"),
            "rom_arquivo": os.path.relpath(rom, PROJECT),
            "rom_sha256": rom_sha,
            "itens": itens}

VEREDITOS = ("aprovado", "ajustar", "reprovado", "pendente")
DEFAULT_VERDICT = os.path.join(PROJECT, "out", "logs", "m3_escuta_verdict.json")

def cmd_verify(verbose=True):
    """A cabine é o instrumento do gate humano: se ela serve outro byte, o
    veredito é sobre outra evidência. Compara o html com o disco, não com a intenção."""
    data = payload_from_html()
    if data is None:
        print("[FAIL] cabine ausente — rode tools/m3_escuta.py --open")
        return 1
    if data == "sem-blob":
        print("[FAIL] html sem blob de dados (arquivo truncado?)")
        return 1
    rom = current_rom_sha()
    falhas = []
    if data.get("rom_sha256") != rom:
        falhas.append("cabine anuncia ROM %s, disco tem %s" % (data.get("rom_sha256"), rom))
    nomes = [i["nome"] for i in data["itens"]]
    falt = [n for n, _, _ in JANELAS if n not in nomes]
    if falt:
        falhas.append("janelas ausentes na cabine: %s" % ", ".join(falt))
    for it in data["itens"]:
        n, b = it["nome"], it["binding"]
        h = sha_bytes(base64.b64decode(it["wav_b64"]))
        esc = os.path.join(ESC, n + ".wav")
        ev = os.path.join(PROJECT, "out", "evidence", n + ".wav")
        if not os.path.isfile(esc) or h != sha(esc):
            falhas.append("%s: audio embutido != out/escuta/%s.wav" % (n, n))
            continue
        if not os.path.isfile(ev):
            falhas.append("%s: nao publicada em out/evidence/ (o eixo de audio nao le esta janela)" % n)
        elif h != sha(ev):
            falhas.append("%s: copia em out/evidence/ diverge do que a cabine serve" % n)
        if b.get("rom_sha256") != rom:
            falhas.append("%s: binding aponta ROM %s (nao a entregue)" % (n, b.get("rom_sha256")))
        jb = os.path.join(ESC, n + ".audio.json")
        if os.path.isfile(jb):
            atual = json.load(open(jb, encoding="utf-8"))
            for k in ("peak", "session_id", "rom_sha256", "effective_seconds"):
                if atual.get(k) != b.get(k):
                    falhas.append("%s: %s da cabine (%r) != .audio.json atual (%r)"
                                  % (n, k, b.get(k), atual.get(k)))
        gt = os.path.join(PROJECT, "out", "logs", "audit_audio_%s.txt" % n)
        if not os.path.isfile(gt):
            falhas.append("%s: sem gate audit_audio registrado" % n)
        elif open(gt, encoding="utf-8").read().strip() != it["gate"]:
            falhas.append("%s: gate da cabine esta velho vs out/logs/audit_audio_%s.txt" % (n, n))
        if verbose and not falhas:
            print("[ok] %-24s peak=%-5s b64==escuta==evidence rom=%s" %
                  (n, b.get("peak"), str(b.get("rom_sha256"))[:8]))
    for f in falhas:
        print("[FAIL] " + f)
    if falhas:
        print("[FAIL] cabine M3: %d divergencias" % len(falhas))
        return 1
    print("[PASS] cabine M3: %d janelas byte-identicas a out/escuta e out/evidence, "
          "ROM %s, gate por janela" % (len(data["itens"]), rom[:12]))
    return 0

def find_export(path):
    cands = []
    if path:
        cands.append(os.path.expanduser(path))
    dl = os.path.join(os.path.expanduser("~"), "Downloads", "m3_escuta_verdict.json")
    cands += [dl, DEFAULT_VERDICT]
    cands += sorted(glob.glob(os.path.join(PROJECT, "m3_escuta_verdict*.json")))
    for c in cands:
        if os.path.isfile(c):
            return c
    print("[FAIL] veredito nao encontrado — exporte o botao da cabine (download "
          "m3_escuta_verdict.json) e rode --collect <caminho>")
    return None

def ingest(src, dest=None, quiet=False):
    """Casa o veredito com a cabine que o produziu: ROM, timestamps e SHA de cada
    wav. Um veredito de outra tomada nao pode fechar este milestone."""
    data = payload_from_html()
    if not isinstance(data, dict):
        return (None, "cabine ausente ou sem blob")
    try:
        v = json.load(open(src, encoding="utf-8"))
    except (OSError, ValueError) as e:
        return (None, "veredito ilegivel: %s" % e)
    rom = current_rom_sha()
    erros = []
    if v.get("rom_sha256") != rom:
        erros.append("veredito aponta ROM %s, entregue e %s" % (v.get("rom_sha256"), rom))
    if v.get("gerado_em") != data.get("gerado_em"):
        erros.append("veredito gerado na cabine %s, cabine atual e %s (stale)"
                     % (v.get("gerado_em"), data.get("gerado_em")))
    by_name = {i["nome"]: i for i in data["itens"]}
    itens = []
    for it in v.get("itens", []):
        n = it.get("nome")
        if n not in by_name:
            erros.append("janela desconhecida no veredito: %r" % n)
            continue
        if it.get("wav_sha256") != by_name[n]["binding"]["wav_sha256"]:
            erros.append("%s: wav_sha256 do veredito != o que a cabine serve" % n)
        if it.get("veredito") not in VEREDITOS:
            erros.append("%s: veredito invalido %r" % (n, it.get("veredito")))
        itens.append({"nome": n, "rotulo": by_name[n]["rotulo"],
                      "veredito": it.get("veredito", "pendente"),
                      "nota": it.get("nota", ""),
                      "wav_sha256": it.get("wav_sha256"),
                      "peak": by_name[n]["binding"].get("peak"),
                      "gate": by_name[n]["gate"]})
    for n in by_name:
        if n not in {i["nome"] for i in itens}:
            erros.append("%s: sem linha no veredito (janela nao julgada)" % n)
    if erros:
        return (None, "; ".join(erros))
    out = {"fonte_export": {"path": src, "sha256": sha(src)},
           "ingerido_em": datetime.datetime.now().isoformat(timespec="seconds"),
           "rom_sha256_verificada": rom,
           "cabine_gerado_em": data.get("gerado_em"),
           "itens": itens,
           "julgadas": sum(1 for i in itens if i["veredito"] != "pendente"),
           "total": len(itens)}
    dest = dest or DEFAULT_VERDICT
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    json.dump(out, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if not quiet:
        for i in itens:
            print("  %-9s %s" % (i["veredito"], i["rotulo"])
                  + (("  | " + i["nota"]) if i["nota"] else ""))
        print("[PASS] veredito ingerido: %d/%d julgadas | %s (ROM %s)" %
              (out["julgadas"], out["total"], dest, rom[:12]))
    return (out, None)

def cmd_collect(path=None, dest=None):
    src = find_export(path)
    if not src:
        return 1
    out, err = ingest(src, dest)
    if err:
        print("[FAIL] %s" % err)
        return 1
    return 0

def cmd_selfcheck():
    """--self-check nao toca em out/logs: usa a cabine real so para leitura e
    vereditos sinteticos em tmpdir. Reprva se qualquer rejeicao nao acontecer."""
    print("[self] 1/4 integridade da cabine no disco")
    rc = cmd_verify(verbose=False)
    if rc:
        print("[self] [FAIL] a propria cabine nao passa em --verify")
        return 2
    data = payload_from_html()
    import tempfile
    tmp = tempfile.mkdtemp(prefix="m3_escuta_selfcheck_")
    bom = {"rom_sha256": data["rom_sha256"], "gerado_em": data["gerado_em"],
           "itens": [{"nome": i["nome"], "rotulo": i["rotulo"],
                      "veredito": "aprovado", "nota": "sintetico",
                      "wav_sha256": i["binding"]["wav_sha256"],
                      "rom_atual": True} for i in data["itens"]]}
    casos = [("aceita veredito integro", bom, False),
             ("recusa ROM divergente", dict(bom, rom_sha256="0" * 64), True),
             ("recusa cabine stale", dict(bom, gerado_em="2000-01-01T00:00:00"), True)]
    tam = dict(bom, itens=[dict(x) for x in bom["itens"]])
    tam["itens"][0]["wav_sha256"] = "f" * 64
    casos.append(("recusa wav trocado", tam, True))
    falta = dict(bom, itens=bom["itens"][:-1])
    casos.append(("recusa janela nao julgada", falta, True))
    ruim = dict(bom)
    ruim["itens"] = [dict(x, veredito="mais ou menos") for x in bom["itens"]]
    casos.append(("recusa veredito fora do vocabulario", ruim, True))
    rc = 0
    for rotulo, payload, deve_falhar in casos:
        src = os.path.join(tmp, "verdict.json")
        json.dump(payload, open(src, "w", encoding="utf-8"))
        out, err = ingest(src, dest=os.path.join(tmp, "out.json"), quiet=True)
        falhou = out is None
        ok = falhou == deve_falhar
        print("[self] %s %s (%s)" % ("[ok]" if ok else "[FAIL]", rotulo,
                                     (err or "aceito")[:70]))
        if not ok:
            rc = 2
    print("[self] vereditos sinteticos em %s (fora de out/: nao sao evidencia)" % tmp)
    print("[SELF-CHECK %s] m3_escuta.py" % ("FAIL" if rc else "PASS"))
    return rc

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", action="store_true", help="gera e abre a cabine")
    ap.add_argument("--generate", action="store_true", help="so gera o html")
    ap.add_argument("--verify", action="store_true",
                    help="confere o que a cabine serve contra o disco")
    ap.add_argument("--collect", nargs="?", const="", default=None,
                    metavar="CAMINHO", help="ingere o veredito exportado")
    ap.add_argument("--dest", default=None)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return cmd_selfcheck()
    if a.verify:
        return cmd_verify()
    if a.collect is not None:
        return cmd_collect(a.collect or None, a.dest)
    data = collect()
    if not data["itens"]:
        print("[FAIL] nenhuma janela capturada — rode tools/m3_audio_windows.sh")
        return 1
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out = HTML
    with open(out, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.replace("__DATA__", payload))
    print("[PASS] cabine M3: %s (%d janela(s), %.1f MB) | ROM %s" % (
        out, len(data["itens"]), os.path.getsize(out) / 1e6, data["rom_sha256"]))
    if a.open:
        try:
            subprocess.Popen(["xdg-open", out], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        except OSError as e:
            print("[AVISO] xdg-open indisponível (%s)" % e)

TEMPLATE = r"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Pulso de Cristal — cabine M3 (janelas do runtime)</title><style>
:root{--bg:#0b0f16;--panel:#121a26;--ink:#dbe7f3;--dim:#8296ad;--cyan:#6ec6ff;
--gold:#ffd166;--lime:#9ef01a;--red:#ff5d5d;--line:#233246}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font-family:"Cantarell","Segoe UI",system-ui,sans-serif;padding:20px}
h1{font-size:19px;margin:0 0 4px}h1 b{color:var(--cyan)}
.sub{color:var(--dim);font-size:12px;margin-bottom:16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:14px 16px;margin-bottom:14px}
.card h2{margin:0 0 6px;font-size:15px;color:var(--cyan)}
.nota{font-size:13px;color:var(--ink);line-height:1.5;margin:6px 0}
.fato{font-size:12px;color:var(--dim);font-family:monospace;margin-top:6px}
audio{width:100%;margin-top:8px}
.v{display:flex;gap:14px;margin-top:10px;font-size:13px;flex-wrap:wrap}
.v label{display:flex;gap:5px;align-items:center;cursor:pointer}
button{background:var(--cyan);color:#08131f;border:none;border-radius:9px;
padding:9px 16px;font-weight:800;cursor:pointer;font-size:13px}
</style></head><body>
<h1>Pulso de Cristal — <b>cabine M3</b>: janelas do runtime real</h1>
<div class="sub" id="sub"></div>
<div id="cards"></div>
<div class="card"><button id="exp">exportar veredito (JSON)</button>
<span class="fato" id="hint">nada é aplicado automaticamente; o veredito só
registra sua decisão.</span></div>
<script type="application/json" id="data">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
document.getElementById('sub').textContent=
 `ROM ${D.rom_sha256} · gerado ${D.gerado_em} · ${D.itens.length} janela(s)`;
const cards=document.getElementById('cards');
D.itens.forEach((it,i)=>{const c=document.createElement('div');c.className='card';
const b=it.binding;
c.innerHTML=`<h2>${it.rotulo}</h2><div class="nota">${it.nota}</div>
<div class="fato">sessao ${b.session_id||'—'} · rom ${b.rom_sha256||'—'} ·
peak ${b.peak??'—'} · ${b.effective_seconds??'—'} s · wav ${b.wav_sha256||'—'}
${b.rom_atual?'':' · <b style="color:var(--red)">ROM DIFERENTE DA ENTREGUE</b>'}</div>
<div class="fato">gate audit_audio: ${it.gate}</div>
<audio controls preload="none" src="data:audio/wav;base64,${it.wav_b64}"></audio>
<div class="v"><span>veredito:</span>
<label><input type="radio" name="v${i}" value="aprovado">aprovado</label>
<label><input type="radio" name="v${i}" value="ajustar">ajustar</label>
<label><input type="radio" name="v${i}" value="reprovado">reprovado</label>
<input id="n${i}" placeholder="nota do ouvido" style="flex:1;min-width:180px;
background:var(--bg);color:var(--ink);border:1px solid var(--line);
border-radius:7px;padding:6px 8px">
</div>`;cards.appendChild(c);});
document.getElementById('exp').onclick=()=>{const out={rom_sha256:D.rom_sha256,
gerado_em:D.gerado_em,itens:[]};
D.itens.forEach((it,i)=>{const r=document.querySelector(`input[name=v${i}]:checked`);
out.itens.push({nome:it.nome,rotulo:it.rotulo,veredito:r?r.value:'pendente',
nota:document.getElementById('n'+i).value,
wav_sha256:it.binding.wav_sha256,rom_atual:it.binding.rom_atual});});
const blob=new Blob([JSON.stringify(out,null,2)],{type:'application/json'});
const a=document.createElement('a');a.href=URL.createObjectURL(blob);
a.download='m3_escuta_verdict.json';a.click();};
</script></body></html>"""

if __name__ == "__main__":
    sys.exit(main())
