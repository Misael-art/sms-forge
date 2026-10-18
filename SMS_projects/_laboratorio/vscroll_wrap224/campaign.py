#!/usr/bin/env python3
"""campaign.py — vscroll_wrap224 (L131/§122, andar 3).

Sete sessoes BlastEm sms2 sobre a mesma ROM; a ROM avança de fase sozinha a
cada 60 frames VDP e o roteiro decide em qual janela cada sessao termina
(screenshot = estado vivo). Por sessao: marcador em RAM + byte 9 do
vdp_regs.bin provam qual valor cru foi escrito no reg9. Julgamento pelas
igualdades do README: 240==16, 224==0, 255==31, e controle 240!=192.

Uso: python3 campaign.py [--only idx,idx,..]
Exit: 0 confirmado | 1 refutado | 2 erro/inconclusivo
"""
import json, os, subprocess, sys, glob, argparse
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
def find_root():
    d = HERE
    while d != '/' and not os.path.isdir(os.path.join(d, 'tools', 'sms_wrapper')):
        d = os.path.dirname(d)
    return d if os.path.isdir(os.path.join(d, 'tools', 'sms_wrapper')) else None
ROOT = find_root()
ROM = os.path.join(HERE, 'out', 'rom', 'vscroll_wrap224.sms')
EVID = os.path.join(ROOT, 'out', 'campaign_tier1_2026-10-14', 'vscroll_wrap224')
PHASES = [0, 16, 192, 224, 240, 255, 223, 31]
# idx -> warmup tal que (warmup + 2) caia no meio da janela de fase idx
WARMUP = {0: 510, 1: 570, 2: 150, 3: 210, 4: 270, 5: 330, 7: 450}
TARGETS = [0, 1, 2, 3, 4, 5, 7]
PAIRS = [(4, 1, '240==16'), (3, 0, '224==0'), (5, 7, '255==31')]
CONTROL_DIFF = (4, 2, '240!=192')

def run_session(idx):
    seq = {"schema": "sms_blastem_sequence_v1", "model": "sms2", "region": "ntsc",
           "warmup_frames": WARMUP[idx],
           "preconditions": [{"address": 51152, "equals_hex": "53495631"}],
           "steps": [{"frames": 2}]}
    d = os.path.join(EVID, f'idx{idx}_val{PHASES[idx]}')
    os.makedirs(d, exist_ok=True)
    script = os.path.join(d, 'seq.json')
    json.dump(seq, open(script, 'w'), indent=2)
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools/sms_wrapper', 'blastem_sms.py'),
                        'run', '--rom', ROM, '--script', script, '--output', d],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        sys.exit(f'[ERRO] sessao idx{idx}: {r.stdout}{r.stderr}')
    return r.stdout.strip().splitlines()[-1]

def read_session(sess, idx):
    meta = json.load(open(os.path.join(sess, 'session.json')))
    snap = sorted(glob.glob(os.path.join(sess, 'snapshots', '*/')))[-1]
    ram = open(os.path.join(snap, 'ram.bin'), 'rb').read()
    regs = open(os.path.join(snap, 'vdp_regs.bin'), 'rb').read()
    marker = ram[0xC7D0 - 0xC000: 0xC7D0 - 0xC000 + 8]
    shot = glob.glob(os.path.join(sess, 'screenshots', '*.png'))[0]
    ok = (meta.get('state') == 'completed' and meta.get('screenshot_informative') is True
          and bytes(marker[:4]) == b'SIV1' and marker[4] == idx
          and marker[5] == PHASES[idx] and regs[9] == PHASES[idx])
    return {'ok': ok, 'marker': list(marker), 'reg9': regs[9],
            'frame_final': meta.get('boundaries', [{}])[-1].get('vdp_frame'),
            'pixels': Image.open(shot).convert('RGB').tobytes(),
            'shot': shot}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=None)
    a = ap.parse_args()
    if not os.path.isfile(ROM):
        sys.exit('[ERRO] ROM ausente: rode ./build.sh primeiro')
    targets = TARGETS if not a.only else [int(x) for x in a.only.split(',')]
    os.makedirs(EVID, exist_ok=True)
    results = {}
    for idx in targets:
        sess = run_session(idx)
        results[idx] = read_session(sess, idx)
        r = results[idx]
        print(f'idx{idx} valor={PHASES[idx]}: ok={r["ok"]} '
              f'marker=fase {r["marker"][4]} valor {r["marker"][5]} reg9={r["reg9"]}')
    if not all(results[i]['ok'] for i in results):
        bad = [i for i in results if not results[i]['ok']]
        print(f'[INCONCLUSIVO] fronteira/fase divergente em idx {bad} '
              f'(marcador ou reg9 nao batem com o alvo)')
        return 2
    if not all(i in results for i in TARGETS):
        print('[PARCIAL] faltam alvos; rode as sessoes que faltam')
        return 2
    diffs = {}
    for x, y, tag in PAIRS + [CONTROL_DIFF]:
        same = results[x]['pixels'] == results[y]['pixels']
        diffs[tag] = same
        print(f'{tag}: {"IDENTICO" if same else "DIFERENTE"}')
    failures = []
    for x, y, tag in PAIRS:
        if not diffs[tag]:
            failures.append(f'wrap nao reproduzido: {tag} renderizou diferente')
    if diffs[CONTROL_DIFF[2]]:
        failures.append('controle falhou: 240 identico a 192 (periodicidade?)')
    verdict = 'confirmado' if not failures else 'refutado'
    out = {'probe': 'vscroll_wrap224', 'licao': 'L131/§122',
           'engine': 'BlastEm 1.0.0 sms2', 'verdict': verdict,
           'failures': failures, 'diffs': diffs,
           'sessions': {str(i): {'value': PHASES[i], 'ok': True,
                                 'reg9': results[i]['reg9'],
                                 'frame_final': results[i]['frame_final'],
                                 'shot': results[i]['shot']} for i in TARGETS},
           'rom_sha256': sha256(ROM),
           'limits': 'Mede o wrap do reg9 no BlastEm (janela de render); nao '
                     'mede leitura-unica-por-frame (raster Y) nem console. '
                     'Segunda engine (Emulicious) fica como checagem de '
                     'divergencia; LOTE F conserva a pergunta de silicio.'}
    json.dump(out, open(os.path.join(EVID, 'verdict.json'), 'w'), indent=2)
    print(f'[VEREDITO] {verdict}')
    return 0 if verdict == 'confirmado' else 1

def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(65536), b''):
            h.update(blk)
    return h.hexdigest()

if __name__ == '__main__':
    sys.exit(main())
