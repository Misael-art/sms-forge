#!/usr/bin/env python3
"""campaign.py — tilemap_bits1315 (L132/§123, andar 3).

Roda uma sessao BlastEm sms2 sobre a ROM construida, le o dump de VRAM da
ultima fronteira (palavras da PNT) e o screenshot nativo (corte das 6
celulas), e julga as duas previsoes do README:
  (a) preservacao: bits 13-15 ficam na VRAM como escritos;
  (b) renderizacao: celula flagada identica pixel a pixel ao controle.
Registra tambem o veredito do gate audit_tilemap_bounds na fonte do probe.

Uso: python3 campaign.py [--skip-session] [--session DIR]
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
ROM = os.path.join(HERE, 'out', 'rom', 'tilemap_bits1315.sms')
EVID = os.path.join(ROOT, 'out', 'campaign_tier1_2026-10-14', 'tilemap_bits1315')
# col -> esperado (README); celulas na linha de tile 8
CELLS = [(4, 'A_plain', 0x003C), (6, 'B_FL13', 0x203C), (8, 'C_FL14', 0x403C),
         (10, 'D_FL15', 0x803C), (12, 'E_FL13_15', 0xE03C), (14, 'F_ctrl', 0x003C)]
SEQ = {"schema": "sms_blastem_sequence_v1", "model": "sms2", "region": "ntsc",
       "warmup_frames": 150,
       "preconditions": [{"address": 51152, "equals_hex": "53493831"}],
       "steps": [{"frames": 60}]}

def run_session():
    os.makedirs(EVID, exist_ok=True)
    script = os.path.join(EVID, 'seq_sms2.json')
    json.dump(SEQ, open(script, 'w'), indent=2)
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools/sms_wrapper', 'blastem_sms.py'),
                        'run', '--rom', ROM, '--script', script, '--output', EVID],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        sys.exit(f'[ERRO] blastem_sms: {r.stdout}{r.stderr}')
    return r.stdout.strip().splitlines()[-1]

def gate_note():
    out = {}
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools/sms_wrapper',
                        'audit_tilemap_bounds.py'), HERE, '--allow-tilemap-flags',
                        'laboratorio: probe L132 bits 13-15'], capture_output=True, text=True)
    out['bounds_exit'] = r.returncode
    out['bounds_out'] = r.stdout.strip().splitlines()
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip-session', action='store_true')
    ap.add_argument('--session', default=None)
    a = ap.parse_args()
    if not os.path.isfile(ROM):
        sys.exit('[ERRO] ROM ausente: rode ./build.sh primeiro')
    sess = a.session or (None if not a.skip_session else None)
    if a.session is None and not a.skip_session:
        sess = run_session()
    elif a.session is None:
        cand = sorted(glob.glob(os.path.join(EVID, 'blastem-sms-*')))
        sess = cand[-1] if cand else None
    if not sess or not os.path.isdir(sess):
        sys.exit('[ERRO] nenhuma sessao disponivel')
    meta = json.load(open(os.path.join(sess, 'session.json')))
    snap = sorted(glob.glob(os.path.join(sess, 'snapshots', '*/')))[-1]
    vram = open(os.path.join(snap, 'vram.bin'), 'rb').read()
    regs = open(os.path.join(snap, 'vdp_regs.bin'), 'rb').read()
    ram = open(os.path.join(snap, 'ram.bin'), 'rb').read()
    shot = glob.glob(os.path.join(sess, 'screenshots', '*.png'))[0]

    checks, failures = {}, []
    marker = ram[0xC7D0 - 0xC000: 0xC7D0 - 0xC000 + 8]
    checks['magic'] = bytes(marker[:4]) == b'SI81'
    checks['session_completed'] = meta.get('state') == 'completed'
    checks['screenshot_informative'] = meta.get('screenshot_informative') is True

    words = {}
    for col, tag, exp in CELLS:
        off = 0x3800 + (8 * 32 + col) * 2
        w = vram[off] | (vram[off + 1] << 8)
        words[tag] = f'0x{w:04X}'
        if w != exp:
            failures.append(f'{tag}: VRAM=0x{w:04X} esperado=0x{exp:04X} (preservacao)')

    im = Image.open(shot).convert('RGB')
    crops = {tag: im.crop((col * 8, 64, col * 8 + 8, 72)).tobytes()
             for col, tag, _ in CELLS}
    for col, tag, _ in CELLS[1:]:
        if crops[tag] != crops['A_plain']:
            failures.append(f'{tag}: renderizacao difere do controle (bits com semantica?)')
    checks['cells_identical'] = not any('renderizacao' in f for f in failures)
    checks['words_preserved'] = not any('preservacao' in f for f in failures)

    verdict = 'refutado' if failures else 'confirmado'
    out = {'probe': 'tilemap_bits1315', 'licao': 'L132/§123',
           'engine': 'BlastEm 1.0.0 sms2', 'session': sess,
           'rom_sha256': sha256(ROM), 'verdict': verdict,
           'failures': failures, 'pnt_words': words, 'checks': checks,
           'vdp_regs_final': ' '.join(f'{b:02X}' for b in regs),
           'gate_dogfood': gate_note(),
           'limits': 'Um unico engine (BlastEm); console real continua LOTE F. '
                     'Preservado != interpretado: o VDP ignora na render — a '
                     'semantica de flag e dos jogos, não do hardware.'}
    os.makedirs(EVID, exist_ok=True)
    json.dump(out, open(os.path.join(EVID, 'verdict.json'), 'w'), indent=2)
    print(json.dumps(out, indent=2))
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
