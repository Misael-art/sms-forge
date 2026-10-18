#!/usr/bin/env python3
"""campaign.py — reg2_bit0_mirror (L130/§121, andar 3).

Quatro sessoes BlastEm sobre a MESMA ROM: modelo sms1/sms2 x clique no
botao 1 (escreve reg2=0xFE) / sem clique (controle, reg2=0xFF). A lei
diz: com bit0=0 o VDP SMS1 forca bit10=0 no endereco VRAM da consulta da
name table — linhas 16..23 alias das 0..7 — e o SMS2 nao. Julgamento:
banda de pixels y=128..191 identica a y=0..63. O gate
audit_tilemap_mirror.py e rodado nos tres modos na fonte/ROM viva e sua
saida e gravada como evidencia.

Uso: python3 campaign.py
Exit: 0 confirmado | 1 refutado | 2 erro/inconclusivo
"""
import json, os, subprocess, sys, glob
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
def find_root():
    d = HERE
    while d != '/' and not os.path.isdir(os.path.join(d, 'tools', 'sms_wrapper')):
        d = os.path.dirname(d)
    return d if os.path.isdir(os.path.join(d, 'tools', 'sms_wrapper')) else None
ROOT = find_root()
ROM = os.path.join(HERE, 'out', 'rom', 'reg2_bit0_mirror.sms')
SRC = os.path.join(HERE, 'src', 'main.c')
EVID = os.path.join(ROOT, 'out', 'campaign_tier1_2026-10-14', 'reg2_bit0_mirror')
MAGIC = '53494D31'  # 'SIM1'
KEY_B = 16          # bit4 = 'b' = PORT_A_KEY_1

def seq(model, press):
    steps = [{'frames': 3, 'p1': KEY_B}, {'frames': 60}] if press else [{'frames': 60}]
    return {"schema": "sms_blastem_sequence_v1", "model": model, "region": "ntsc",
            "warmup_frames": 120,
            "preconditions": [{"address": 0xC7D0, "equals_hex": MAGIC}],
            "steps": steps}

def run_session(model, press):
    tag = f'{model}_{"press" if press else "control"}'
    d = os.path.join(EVID, tag)
    os.makedirs(d, exist_ok=True)
    script = os.path.join(d, 'seq.json')
    json.dump(seq(model, press), open(script, 'w'), indent=2)
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools/sms_wrapper', 'blastem_sms.py'),
                        'run', '--rom', ROM, '--script', script, '--output', d],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        sys.exit(f'[ERRO] sessao {tag}: {r.stdout}{r.stderr}')
    return tag, r.stdout.strip().splitlines()[-1]

def read_session(sess, press):
    meta = json.load(open(os.path.join(sess, 'session.json')))
    snap = sorted(glob.glob(os.path.join(sess, 'snapshots', '*/')))[-1]
    ram = open(os.path.join(snap, 'ram.bin'), 'rb').read()
    regs = open(os.path.join(snap, 'vdp_regs.bin'), 'rb').read()
    marker = ram[0xC7D0 - 0xC000: 0xC7D0 - 0xC000 + 8]
    shot = Image.open(glob.glob(os.path.join(sess, 'screenshots', '*.png'))[0]).convert('RGB')
    top = shot.crop((0, 0, 256, 64)).tobytes()      # linhas 0..7  (solido claro)
    bottom = shot.crop((0, 128, 256, 192)).tobytes()  # linhas 16..23 (listrado OU espelhado)
    want_reg = 0xFE if press else 0xFF
    ok = (meta.get('state') == 'completed' and meta.get('screenshot_informative') is True
          and bytes(marker[:4]) == b'SIM1' and marker[4] == want_reg
          and (marker[5] >= 1) == press and regs[2] == want_reg)
    return {'ok': ok, 'marker': list(marker), 'reg2': hex(regs[2]),
            'mirrored': top == bottom,
            'frame_final': meta.get('boundaries', [{}])[-1].get('vdp_frame'),
            'shot': glob.glob(os.path.join(sess, 'screenshots', '*.png'))[0]}

def run_gate_evidence():
    """Roda o gate em codigo vivo nos tres modos e grava saida + exit code."""
    allow = 'laboratorio: probe L130/§121 — reprodutibilidade do mirror SMS1'
    modes = {'gate_source_reprova': ['--source', SRC],
             'gate_source_excecao': ['--source', SRC, '--allow-sms1-mirror', allow],
             'gate_rom': ['--rom', ROM]}
    out = {}
    for name, args in modes.items():
        r = subprocess.run([sys.executable,
                            os.path.join(ROOT, 'tools/sms_wrapper', 'audit_tilemap_mirror.py')] + args,
                           capture_output=True, text=True)
        path = os.path.join(EVID, f'{name}.txt')
        open(path, 'w').write(r.stdout + r.stderr)
        out[name] = {'exit': r.returncode, 'output': path,
                     'summary': (r.stdout + r.stderr).strip().splitlines()[-1:] }
    return out

def main():
    if not os.path.isfile(ROM):
        sys.exit('[ERRO] ROM ausente: rode ./build.sh primeiro')
    os.makedirs(EVID, exist_ok=True)
    results = {}
    for model in ('sms1', 'sms2'):
        for press in (True, False):
            tag, sess = run_session(model, press)
            results[tag] = read_session(sess, press)
            r = results[tag]
            print(f'{tag}: ok={r["ok"]} reg2={r["reg2"]} espelhado={r["mirrored"]} '
                  f'marker={r["marker"][:6]}')
    if not all(r['ok'] for r in results.values()):
        bad = [t for t, r in results.items() if not r['ok']]
        print(f'[INCONCLUSIVO] fronteira/marcador divergente em {bad}')
        return 2

    m1 = results['sms1_press']['mirrored']
    m2 = results['sms2_press']['mirrored']
    c1 = results['sms1_control']['mirrored']
    c2 = results['sms2_control']['mirrored']
    failures = []
    if c1 or c2:
        failures.append('controle (reg2=0xFF) espelha em algum modelo — a lei erra')
    if m2:
        failures.append('sms2 espelha com bit0=0 — a lei erra')
    if failures:
        verdict = 'refutado'
    elif m1:
        verdict = 'confirmado'
    else:
        verdict = 'inconclusivo_cenario_C'
    print(f'press: sms1 espelha={m1}, sms2 espelha={m2} | '
          f'control: sms1={c1}, sms2={c2}')

    gates = run_gate_evidence()
    out = {'probe': 'reg2_bit0_mirror', 'licao': 'L130/§121',
           'engine': 'BlastEm 1.0.0 sms1/sms2', 'verdict': verdict,
           'failures': failures,
           'sessions': {t: {'reg2': r['reg2'], 'mirrored': r['mirrored'],
                            'marker': r['marker'], 'frame_final': r['frame_final'],
                            'shot': r['shot']} for t, r in results.items()},
           'gate_evidence': gates,
           'rom_sha256': sha256(ROM),
           'finding_gate_bypass': 'audit_tilemap_mirror.py --source exige o identificador '
                                  'nu VDPControlPort na adjacencia; a unica porta exposta pela '
                                  'SMSlib vendorada e SMS_VDPControlPort (prefixada), que ESCAPA '
                                  'do padrao --source. O modo --rom ainda pega (ver '
                                  'gate_rom.txt). Proposta de patch exige aprovacao humana.',
           'limits': 'Mede apenas se o BlastEm modela o mirror SMS1; nao mede console real. '
                     'Se cenrio C, L130 permanece documentado sem reproducao em simulador '
                     'deste host; NENHUM upgrade de matriz de maestria/compatibilidade e '
                     'reivindicado. Segunda engine (Emulicious) fica em LOTE F.'}
    json.dump(out, open(os.path.join(EVID, 'verdict.json'), 'w'), indent=2, ensure_ascii=False)
    print(f'[VEREDITO] {verdict}')
    return {'confirmado': 0, 'refutado': 1}.get(verdict, 2)

def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(65536), b''):
            h.update(blk)
    return h.hexdigest()

if __name__ == '__main__':
    sys.exit(main())
