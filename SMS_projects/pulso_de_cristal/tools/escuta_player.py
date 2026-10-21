#!/usr/bin/env python3
"""escuta_player.py — player local de escuta humana por faixa (M1+, teto humano).

Gera out/escuta/player.html AUTOCONTIDO (WAV embutida em base64; abre por
file:// sem servidor): <select> com TODAS as faixas emitidas, play/pause/
busca/loop, piano-roll das 4 camadas decodificado do .psg com o MESMO
decodificador do auditor (espelho em JS), ficha de metadados (nome, pro-
pósito, data de criação, bpm/tom/estrutura, bytes/sha256/duração, métricas
do gate), binding da prova quando existe (sessao/ROM/WAV) e veredito humano
por faixa com export de JSON.

Honestidade de claim: faixa SEM captura de emulador entra com WAV de
pre-escuta numpy, rotulada `pre-escuta` — o player nunca apresenta pré-
escuta como prova; `binding` só existe na fonte `emulador`.

Ajuste pós-escuta acontece SO na partitura JSON (TDD); o player registra o
veredito, nunca o aplica.

Uso:
  escuta_player.py             # gera player.html
  escuta_player.py --open      # gera e abre no navegador do host
  escuta_player.py --check     # integridade dos pares (wav hash casa com o
                               # manifest de audio; .psg decodifica igual)
Exit: 0 ok | 1 sem pares/problema | 3 uso
"""
import argparse
import base64
import datetime
import glob
import hashlib
import json
import os
import subprocess
import sys

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRAPPER = os.path.abspath(os.path.join(PROJECT, os.pardir, os.pardir,
                                      "tools", "sms_wrapper"))


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(65536), b""):
            h.update(blk)
    return h.hexdigest()


def _wav_index(esc):
    idx = {}
    for w in glob.glob(os.path.join(esc, "*.wav")):
        idx[_sha256(w)] = w
    return idx


def _preview_wav(esc, nome, blob, fps):
    """Pre-escuta numpy deterministica a partir do MESMO .psg do emissor.
    Nao e prova de emulador — o chamador rotula."""
    sys.path.insert(0, WRAPPER)
    import make_psg_assets as mpa
    path = os.path.join(esc, "preview_%s.wav" % nome)
    mpa.render_wav(path, blob, fps=fps)
    return path


def discover():
    """Cobre TODAS as partituras emitidas: para cada tools/partitura/*.json
    com .psg em res/audio, pareia a WAV do emulador (audio_<nome>.audio.json
    via wav_sha256 — verificado, nao presumido) ou gera pre-escuta numpy."""
    esc = os.path.join(PROJECT, "out", "escuta")
    os.makedirs(esc, exist_ok=True)
    wavs = _wav_index(esc)
    gates_by_file = {}
    gpath = os.path.join(PROJECT, "out", "logs", "psg_quality.json")
    if os.path.isfile(gpath):
        with open(gpath, encoding="utf-8") as f:
            for r in json.load(f).get("results", []):
                gates_by_file[r.get("arquivo")] = r
    tracks, warns = [], []
    parts = sorted(glob.glob(os.path.join(PROJECT, "tools", "partitura", "*.json")),
                   key=lambda p: (0 if os.path.basename(p).startswith("music_") else 1, p))
    for part in parts:
        with open(part, encoding="utf-8") as f:
            partitura = json.load(f)
        meta = partitura.get("meta", {})
        nome = meta.get("nome") or os.path.basename(part)[:-5]
        psg = os.path.join(PROJECT, "res", "audio", nome + ".psg")
        if not os.path.isfile(psg):
            warns.append("%s: ainda sem %s" % (nome, os.path.relpath(psg, PROJECT)))
            continue
        blob = open(psg, "rb").read()
        fps = int(meta.get("fps", 60))
        binding = None
        fonte = "pre-escuta"
        j = os.path.join(esc, "audio_%s.audio.json" % nome)
        if os.path.isfile(j):
            with open(j, encoding="utf-8") as f:
                cand = json.load(f)
            wav = wavs.get(cand.get("wav_sha256"))
            if wav:
                binding, fonte, wav_path = cand, "emulador", wav
            else:
                warns.append("%s: binding existe mas nenhuma WAV casa com wav_sha256" % nome)
        if binding is None:
            wav_path = _preview_wav(esc, nome, blob, fps)
        tracks.append({
            "nome": nome,
            "meta": meta,
            "papeis": partitura.get("papeis", {}),
            "binding": binding,
            "fonte": fonte,
            "tipo": meta.get("tipo", "music"),
            "bytes": len(blob),
            "sha256_psg": hashlib.sha256(blob).hexdigest(),
            "criado_em": datetime.datetime.fromtimestamp(
                os.path.getmtime(part)).strftime("%Y-%m-%d"),
            "gates": gates_by_file.get(nome + ".psg", {}),
            "fps": fps,
            "wav_b64": base64.b64encode(open(wav_path, "rb").read()).decode(),
            "psg_b64": base64.b64encode(blob).decode(),
        })
    return tracks, warns


def check():
    sys.path.insert(0, WRAPPER)
    import audit_psg_quality as aq
    tracks, warns = discover()
    if warns:
        for w in warns:
            print("[AVISO] %s" % w)
    if not tracks:
        print("[FAIL] nenhum par WAV+.psg escutavel em out/escuta")
        return 1
    for t in tracks:
        blob = base64.b64decode(t["psg_b64"])
        ev, dur = aq.decode(blob)
        g = t.get("gates", {})
        gdur = g.get("metricas", {}).get("duracao_frames")
        assert dur > 0 and (gdur is None or dur == gdur), \
            "%s: decodificador do player diverge do gate (%d vs %s)" % (
                t["nome"], dur, gdur)
        print("[CHECK OK] %s: wav hash casa, psg decode == gate (dur=%df)" % (
            t["nome"], dur))
    return 0


def generate(open_browser):
    tracks, warns = discover()
    if warns:
        for w in warns:
            print("[AVISO] %s" % w)
    if not tracks:
        print("[FAIL] nada para escutar — emita as partituras (gen_pulso_music --all) primeiro")
        return 1
    out = os.path.join(PROJECT, "out", "escuta", "player.html")
    payload = json.dumps({"tracks": tracks}, ensure_ascii=False)
    payload = payload.replace("</", "<\\/")  # seguro dentro de <script>
    html = TEMPLATE.replace("__DATA_JSON__", payload)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("[PASS] player: %s (%d faixa(s), %.1f MB)" % (
        out, len(tracks), os.path.getsize(out) / 1e6))
    if open_browser:
        try:
            subprocess.Popen(["xdg-open", out],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            print("[ABERTO] xdg-open -> navegador do host")
        except OSError as e:
            print("[AVISO] xdg-open indisponivel (%s) — abra o arquivo a mao" % e)
    return 0


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Pulso de Cristal — cabine de escuta</title>
<style>
:root{--bg:#0b0f16;--panel:#121a26;--ink:#dbe7f3;--dim:#8296ad;--cyan:#6ec6ff;
--gold:#ffd166;--violet:#c792ea;--lime:#9ef01a;--red:#ff5d5d;--line:#233246}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font-family:"Cantarell","Segoe UI",system-ui,sans-serif}
header{padding:18px 24px 10px;border-bottom:1px solid var(--line)}
h1{margin:0;font-size:20px;letter-spacing:.5px}
h1 b{color:var(--cyan)}
.picker{display:flex;gap:12px;align-items:center;margin-top:12px;flex-wrap:wrap}
select#sel{background:var(--panel);color:var(--ink);border:1px solid var(--line);
border-radius:10px;padding:9px 14px;font-size:15px;font-family:inherit;min-width:260px}
select#sel:focus{outline:2px solid var(--cyan)}
.badge.emu{border-color:var(--lime);color:var(--lime)}
.badge.prev{border-color:var(--gold);color:var(--gold)}
main{padding:16px 24px;max-width:1240px;margin:0 auto}
.ident{background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:12px 16px;margin-bottom:12px;font-size:13px;line-height:1.5}
.ident .k{color:var(--dim)}
.badges{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.badge{font-size:12px;padding:3px 10px;border-radius:999px;border:1px solid var(--line);color:var(--dim)}
.badge.pass{border-color:var(--lime);color:var(--lime)}
.controls{display:flex;align-items:center;gap:12px;margin:12px 0;flex-wrap:wrap}
button.play{width:52px;height:52px;border-radius:50%;border:none;cursor:pointer;
background:var(--cyan);color:#08131f;font-size:20px;font-weight:900}
button.play.pause{background:var(--gold)}
input[type=range]{flex:1;min-width:220px;accent-color:var(--cyan)}
.t{font-variant-numeric:tabular-nums;color:var(--dim);font-size:13px;min-width:96px}
label.loop{font-size:13px;color:var(--dim);display:flex;gap:6px;align-items:center}
#scroller{overflow-x:auto;border:1px solid var(--line);border-radius:12px;
background:var(--panel);position:relative}
#tlwrap{position:relative}
canvas{display:block}
#playhead{position:absolute;top:0;bottom:0;width:2px;background:var(--red);
pointer-events:none;left:0}
#playhead::after{content:"";position:absolute;top:0;left:-4px;
border:5px solid transparent;border-top-color:var(--red)}
.lanes{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 0;font-size:12px;color:var(--dim)}
.chip{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}
@media(max-width:900px){.grid2{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 16px;font-size:13px}
.card h3{margin:0 0 8px;font-size:13px;color:var(--cyan);text-transform:uppercase;letter-spacing:1px}
table{border-collapse:collapse;width:100%}
td,th{padding:3px 6px;text-align:left;border-bottom:1px solid var(--line);font-size:12px}
th{color:var(--dim);font-weight:600}
code{font-family:ui-monospace,monospace;font-size:11px;color:var(--violet);word-break:break-all}
.verdict .row{display:flex;gap:10px;margin-bottom:10px;flex-wrap:wrap}
.verdict button.v{padding:10px 18px;border-radius:10px;border:1px solid var(--line);
background:transparent;color:var(--ink);cursor:pointer;font-size:14px}
.verdict button.v.ok.on{background:var(--lime);color:#08131f;border-color:var(--lime);font-weight:800}
.verdict button.v.no.on{background:var(--red);color:#14060a;border-color:var(--red);font-weight:800}
textarea{width:100%;min-height:88px;background:#0d1420;color:var(--ink);
border:1px solid var(--line);border-radius:10px;padding:10px;font-family:inherit;font-size:13px;resize:vertical}
.export{margin-top:10px;padding:10px 16px;border-radius:10px;border:none;cursor:pointer;
background:var(--gold);color:#1a1408;font-weight:800;font-size:14px}
.saved{color:var(--lime);font-size:12px;margin-left:10px}
.hint{color:var(--dim);font-size:12px;margin-top:10px;line-height:1.5}
</style>
</head>
<body>
<header>
  <h1><b>PULSO DE CRISTAL</b> — cabine de escuta (veredito humano por faixa)</h1>
  <div class="picker">
    <label for="sel" style="color:var(--dim);font-size:13px">faixa:</label>
    <select id="sel"></select>
    <span class="badge" id="fonte-badge"></span>
    <span class="badge" id="dur-badge"></span>
  </div>
</header>
<main>
  <div class="ident" id="ident"></div>
  <div class="controls">
    <button class="play" id="btn">▶</button>
    <input type="range" id="seek" min="0" max="100" step="0.01" value="0">
    <span class="t" id="time">0.0 / 0.0 s</span>
    <label class="loop"><input type="checkbox" id="loop"> loop</label>
  </div>
  <div id="scroller"><div id="tlwrap"><canvas id="cv"></canvas><div id="playhead"></div></div></div>
  <div class="lanes">
    <span><i class="chip" style="background:var(--gold)"></i>ch0 — <span id="r0"></span></span>
    <span><i class="chip" style="background:var(--cyan)"></i>ch1 — <span id="r1"></span></span>
    <span><i class="chip" style="background:var(--violet)"></i>ch2 — <span id="r2"></span></span>
    <span><i class="chip" style="background:var(--lime)"></i>ch3 — <span id="r3"></span></span>
  </div>
  <div class="grid2">
    <div class="card" style="grid-column:1/-1"><h3>Ficha da faixa</h3><div id="ficha"></div></div>
    <div class="card"><h3>Piso medido (audit_psg_quality)</h3><div id="gates"></div></div>
    <div class="card"><h3>Prova da gravação</h3><div id="proof"></div></div>
    <div class="card verdict" style="grid-column:1/-1"><h3>Seu veredito — escuta humana</h3>
      <div class="row">
        <button class="v ok" id="bok">Aprovada ✔</button>
        <button class="v no" id="bno">Ajustar ✎</button>
        <span class="saved" id="saved"></span>
      </div>
      <textarea id="notes" placeholder="O que você ouviu? (ex.: 'a quinta inicial some no arpejo', 'o bumbo entra tarde', 'volume do baixo baixo demais')"></textarea>
      <button class="export" id="exp">Exportar veredito (JSON)</button>
      <div class="hint">Clique na linha do tempo para buscar. O veredito fica salvo neste
      navegador; <b>exporte o JSON</b> e cole/coloque o arquivo no projeto. Ajuste é feito
      SÓ na partitura (<code>tools/partitura/&lt;faixa&gt;.json</code>) e regenerado — nunca no emissor.</div>
    </div>
  </div>
</main>
<script type="application/json" id="data">__DATA_JSON__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const PPS=30, WAIT=0x38, END=0x00;
const COLORS=['#ffd166','#6ec6ff','#c792ea','#9ef01a'];
const NAMES=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
function b2u(b64){const s=atob(b64),u=new Uint8Array(s.length);for(let i=0;i<s.length;i++)u[i]=s.charCodeAt(i);return u;}
// ESPELHO JS de audit_psg_quality.decode — mesma gramatica PSGlib
function decodePSG(bytes){let ev=[],t=0,last=null,i=0;
 while(i<bytes.length){const b=bytes[i];
  if(b>=0x80){last=b;const ch=(b>>5)&3;
   if(b&0x10)ev.push([t,'v',ch,b&0x0F]);
   else if(ch===3)ev.push([t,'n',3,b&7]);
   i++;}
  else if(b>=0x40&&b<=0x7F&&last!==null){const ch=(last>>5)&3;
   if(ch<3)ev.push([t,'f',ch,((b&0x3F)<<4)|(last&0x0F)]);i++;}
  else if(b>=WAIT&&b<=0x3F){t+=1+(b>WAIT?(b&7):0);i++;}
  else if(b===END)break;else i++;}
 return{ev,dur:t};}
function midiOf(period){const hz=3579545/(16*period);
 return 69+12*Math.log2(hz/440);}
function noteName(period){const m=Math.round(midiOf(period));
 return NAMES[((m%12)+12)%12]+(Math.floor(m/12)-1);}
function segments(track){const {ev,dur}=decodePSG(b2u(track.psg_b64));
 const byCh=[[],[],[],[]];for(const e of ev)byCh[e[2]].push(e);
 const lanes=[];
 for(let ch=0;ch<4;ch++){const es=byCh[ch].sort((a,b)=>a[0]-b[0]);
  let period=null,att=15,t0=0,blocks=[];
  const close=(t1)=>{if(att<15&&t1>t0)blocks.push({a:t0,b:t1,att,
    label:ch<3&&period!=null?noteName(period):'',
    _m:ch<3&&period!=null?midiOf(period):0});};
  let i=0;
  while(i<es.length){const t=es[i][0];
   while(i<es.length&&es[i][0]===t){const[,k,,v]=es[i];
    if(k==='f')period=v;else if(k==='v')att=v;i++;}
   close(t);t0=t;}
  close(dur);lanes.push(blocks);}
 return{lanes,dur};}
const cv=document.getElementById('cv'),scroller=document.getElementById('scroller'),
playheadEl=document.getElementById('playhead'),seek=document.getElementById('seek'),
timeEl=document.getElementById('time'),btn=document.getElementById('btn'),
loopEl=document.getElementById('loop'),sel=document.getElementById('sel');
let audio=new Audio(),cur=0,scene=null,fps=60;
function load(n){cur=n;const tr=D.tracks[n];fps=tr.fps||60;
 scene=segments(tr);
 sel.value=n;
 const secs=scene.dur/fps;
 const fb=document.getElementById('fonte-badge');
 fb.className='badge '+(tr.fonte==='emulador'?'emu':'prev');
 fb.textContent=tr.fonte==='emulador'?'captura do emulador':'pré-escuta numpy — não é prova';
 document.getElementById('dur-badge').textContent=secs.toFixed(1)+' s ('+scene.dur+' frames)';
 document.getElementById('ident').innerHTML=
  '<div><span class="k">propósito:</span> '+(tr.meta.cena||'—')+'</div>'+
  '<div><span class="k">identidade:</span> '+(tr.meta.identidade||'—')+'</div>'+
  '<div class="badges"><span class="badge">bpm '+(tr.meta.bpm||'?')+'</span>'+
  '<span class="badge">'+(tr.meta.tom||'?')+'</span>'+
  (tr.gates&&tr.gates.veredito==='passa'?'<span class="badge pass">piso M1–M7: PASS</span>':'<span class="badge">gate: —</span>')+'</div>';
 ['lead','arpejo','baixo','percussao'].forEach((d,i)=>{
  const role=tr.papeis['ch'+i];document.getElementById('r'+i).textContent=role||d;});
 draw();audio.src='data:audio/wav;base64,'+tr.wav_b64;audio.loop=loopEl.checked;
 audio.currentTime=0;
 const m=tr.gates&&tr.gates.metricas||{};
 const rows=Object.keys(m).map(k=>'<tr><td>'+k+'</td><td>'+JSON.stringify(m[k])+'</td></tr>').join('');
 const viol=(tr.gates&&tr.gates.violacoes||[]).map(v=>'<tr><td colspan=2 style="color:var(--red)">'+v+'</td></tr>').join('');
 const warn=(tr.gates&&tr.gates.avisos||[]).map(v=>'<tr><td colspan=2 style="color:var(--gold)">aviso: '+v+'</td></tr>').join('');
 document.getElementById('gates').innerHTML='<table><tr><th>métrica</th><th>medido</th></tr>'+rows+viol+warn+'</table>';
 const f=[['nome',tr.nome],['papel',tr.meta.cena||'—'],['tipo',tr.tipo],
  ['estrutura',tr.meta.estrutura||'—'],['tom',tr.meta.tom||'—'],
  ['bpm',tr.meta.bpm||'?'],['frames do loop',scene.dur],['fps da partitura',fps],
  ['duração',secs.toFixed(2)+' s'],['criada em',tr.criado_em||'—'],
  ['stream',tr.bytes+' bytes'],['sha256 do stream','<code>'+tr.sha256_psg+'</code>'],
  ['fonte do áudio',tr.fonte]];
 document.getElementById('ficha').innerHTML='<table>'+
  f.map(r=>'<tr><th>'+r[0]+'</th><td>'+r[1]+'</td></tr>').join('')+'</table>';
 const b=tr.binding;
 document.getElementById('proof').innerHTML=b?
  '<table><tr><th>campo</th><th>valor</th></tr>'+
  '<tr><td>sessao Emulicious</td><td><code>'+b.session_id+'</code></td></tr>'+
  '<tr><td>ROM sha256</td><td><code>'+b.rom_sha256+'</code></td></tr>'+
  '<tr><td>WAV sha256</td><td><code>'+(b.wav_sha256||'—')+'</code></td></tr>'+
  '<tr><td>duração efetiva</td><td>'+(b.effective_seconds||'?')+' s</td></tr>'+
  '<tr><td>claim</td><td>'+b.claim+'</td></tr></table>':
  '<div class="hint">Sem WAV do emulador para esta faixa ainda — o áudio aqui é '+
  'render numpy do mesmo stream .psg (sha256 na ficha). Serve para opinar melodia/'+
  'harmonia/dinâmica; o <b>timbre definitivo e o gate de entrega vêm da captura '+
  'isolada do emulador</b> (ROM jukebox, botão 1 troca de faixa, botão 2 dispara SFX).</div>';
 loadVerdict(tr);}
function draw(){const secs=scene.dur/fps,W=Math.max(Math.ceil(secs*PPS)+24,scroller.clientWidth-2),
 LANE=[96,96,96,52],TOP=26;
 cv.width=W;cv.height=TOP+LANE.reduce((a,b)=>a+b,0)+8;
 const g=cv.getContext('2d');g.fillStyle='#0d1420';g.fillRect(0,0,cv.width,cv.height);
 g.strokeStyle='#233246';g.fillStyle='#8296ad';g.font='11px sans-serif';
 for(let s=0;s<=secs;s++){const x=s*PPS;if(s%5===0){g.beginPath();g.moveTo(x+.5,0);g.lineTo(x+.5,cv.height);g.stroke();g.fillText(s+'s',x+3,14);}else{g.beginPath();g.moveTo(x+.5,TOP);g.lineTo(x+.5,TOP+2);g.stroke();}}
 let y=TOP;
 for(let ch=0;ch<4;ch++){const h=LANE[ch],blks=scene.lanes[ch];
  g.fillStyle='#8296ad';g.fillText('ch'+ch,4,y+11);
  let lo=57,hi=76;
  if(ch===3){lo=0;hi=0;}
  else{const mm=blks.map(b=>b._m);
   if(mm.length){lo=Math.min(...mm)-1;hi=Math.max(...mm)+1;}}
  const rows=Math.max(1,hi-lo),rh=h/Math.max(rows,6);
  for(const b of blks){const x=b.a*PPS,w=Math.max((b.b-b.a)*PPS,2);
   const alpha=Math.max(.18,1-b.att/15);
   if(ch===3){g.globalAlpha=alpha;g.fillStyle=COLORS[3];
    g.fillRect(x,y+h-10,w,8);g.globalAlpha=1;}
   else{const row=hi-b._m;const bh=Math.max(4,rh-2);
    const yy=y+2+row*(h-6)/Math.max(rows,6);
    g.globalAlpha=alpha;g.fillStyle=COLORS[ch];
    g.fillRect(x,yy,w,bh);
    if(w>22){g.globalAlpha=1;g.fillStyle='#0b0f16';g.font='9px monospace';
     g.fillText(b.label,x+2,yy+8);g.font='11px sans-serif';}
    g.globalAlpha=1;}}
  y+=h;}
}
btn.onclick=()=>{audio.paused?audio.play():audio.pause();};
audio.onplay=()=>{btn.textContent='⏸';btn.classList.add('pause');};
audio.onpause=()=>{btn.textContent='▶';btn.classList.remove('pause');};
loopEl.onchange=()=>audio.loop=loopEl.checked;
seek.oninput=()=>{audio.currentTime=seek.value/100*(audio.duration||0);};
cv.addEventListener('click',e=>{const x=e.offsetX;audio.currentTime=x/PPS;});
function tick(){const d=audio.duration||0,t=audio.currentTime;
 timeEl.textContent=t.toFixed(1)+' / '+d.toFixed(1)+' s';
 seek.value=d?100*t/d:0;
 const px=t*PPS;playheadEl.style.left=px+'px';
 if(!audio.paused){const want=px-scroller.clientWidth*0.45;
  if(Math.abs(scroller.scrollLeft-want)>40)scroller.scrollLeft=want;}
 requestAnimationFrame(tick);}
requestAnimationFrame(tick);
function vk(){return 'pdc_escuta_'+D.tracks[cur].nome;}
function loadVerdict(tr){const bok=document.getElementById('bok'),
 bno=document.getElementById('bno'),nt=document.getElementById('notes');
 let v=null;try{v=JSON.parse(localStorage.getItem('pdc_escuta_'+tr.nome)||'null');}catch(e){}
 bok.classList.toggle('on',v&&v.veredito==='aprovada');
 bno.classList.toggle('on',v&&v.veredito==='ajustar');
 nt.value=(v&&v.notas)||'';
 document.getElementById('saved').textContent=v?('salvo '+v.registrado_em):'';
 bok.onclick=()=>save('aprovada');bno.onclick=()=>save('ajustar');
 function save(kind){const o={projeto:'pulso_de_cristal',faixa:tr.nome,
  veredito:kind==='aprovada'?'aprovada':'ajustar',notas:nt.value,
  fonte:tr.fonte,wav_sha256:(tr.binding||{}).wav_sha256||null,
  rom_sha256:(tr.binding||{}).rom_sha256||null,
  psg_sha256:tr.sha256_psg,
  registrado_em:new Date().toISOString()};
  localStorage.setItem('pdc_escuta_'+tr.nome,JSON.stringify(o));
  loadVerdict(tr);}
 document.getElementById('exp').onclick=()=>{const o={projeto:'pulso_de_cristal',faixa:tr.nome,
  veredito:(v&&v.veredito)||'pendente',notas:nt.value,
  fonte:tr.fonte,wav_sha256:(tr.binding||{}).wav_sha256||null,
  rom_sha256:(tr.binding||{}).rom_sha256||null,
  psg_sha256:tr.sha256_psg,
  registrado_em:new Date().toISOString()};
  const bl=new Blob([JSON.stringify(o,null,1)],{type:'application/json'});
  const a=document.createElement('a');a.href=URL.createObjectURL(bl);
  a.download='escuta_verdict_'+tr.nome+'.json';a.click();};}
D.tracks.forEach((tr,i)=>{const o=document.createElement('option');o.value=i;
 o.textContent=tr.nome+(tr.tipo!=='music'?' (sfx)':'')+
  (tr.fonte==='emulador'?' — emulador':' — pré-escuta');
 sel.appendChild(o);});
sel.onchange=()=>load(+sel.value);
load(0);
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", action="store_true", help="abre no navegador (xdg-open)")
    ap.add_argument("--check", action="store_true", help="valida integridade dos pares")
    a = ap.parse_args()
    if a.check:
        return check()
    return generate(a.open)


if __name__ == "__main__":
    sys.exit(main())
