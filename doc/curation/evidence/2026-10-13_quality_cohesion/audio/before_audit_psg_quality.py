#!/usr/bin/env python3
"""audit_psg_quality.py — piso de qualidade musical do PSG, medido no stream.

`audit_audio.py` mede PRESENCA (peak, % ativo). Nada neste acervo media se o
que toca e MUSICA ou metralhadora — e o resultado apareceu em 2026-09-25 na
curadoria: tres projetos carregavam "musicas" de ~1 s em que os tres canais
de tone tocam a MESMA nota no MESMO frame a volume maximo, com ruido
PERIODICO (register R3 bit 2 = 1 -> assobio tonal, nao percussao) colado por
baixo. Structuralmente e o que se ouve como "ruido pessimo": sem ritmo, sem
dinamica, sem registro, sem loop.

Este gate le os .psg (formato PSGlib, confirmado em
sdk/devkitSMS-upstream/PSGlib/src/PSGlib.c: latch>=0x80, bit4=volume,
dados 0x40..0x7F, 0x38=fim de frame, 0x39..=hold extra, 0x00=PSGEnd,
0x01=loop point; nibble de volume = ATENUACAO, 0 mais alto / 15 mudo;
ruido: latch 0xE0|fb|per, fb=1 -> periodico) e cobra seis clausulas:

  M1 ritmo      - nota nova a cada >= 2 frames por canal ativo
                  (troca a cada frame = 16 Hz = chiado, nao melodia;
                  arpeggio ultrarrapido legitimo roda em ~2 frames/nota)
  M2 dinamica   - cada canal com >= 8 notas usa >= 2 atenuacoes != 15
                  (volume constante = buzina de orgao; envelope e o que
                  da ataque e eco ao SN76489)
  M3 registro   - quadros com >= 2 canais na MESMA periodo <= 50%
                  (unison total e o defeito do gerador compartilhado)
  M4 ruido      - se ch3 tem >= 8 eventos, maioria branca (mode & 4 == 0)
                  e com envelope (>= 2 atenuacoes); percussao branca e
                  caixa/prato; periodico e metalico de SFX, nao bateria
  M5 loop       - duracao >= 250 frames (5 s a 50 Hz)
  M6 canais     - >= 2 canais de tone soando (PSG ao minimo = 1 canal e
                  desperdicio; arpejo multiplexado ajuda, nao substitui)
  M7 andamento- pelo menos um canal de tone ativo segura notas por
                  >= 8 frames (160 ms a 50 Hz). Arpejo em 2 frames e
                  legitimo como CAMADA, mas se NENHUMA camada respira o
                  ouvinte so ouve granulado — foi a queixa humana de
                  2026-09-25 ('soa acelerada') em streams que passavam
                  no M1: compasso de 16 frames = semineas a 80 ms.

SFX:
  S1 decaimento - termina mais baixo do que comeca (ou vai a mudo)
  S2 duracao    - <= 45 frames (0,9 s); SFX longo pisa no proximo evento

Uso: audit_psg_quality.py --project <p> [--json out]
     audit_psg_quality.py --psg <a.psg> [...] [--music|--sfx forcar classe]
Exit: 0 tudo passa | 1 ha violacao | 3 uso/arquivo ausente
"""
import argparse
import glob
import hashlib
import json
import os
import sys

WAIT, END, LOOPPT = 0x38, 0x00, 0x01

GAP_MIN = 2.0          # frames por nota (M1)
VOL_VARIETY = 2        # atenuacoes distintas != 15 (M2)
UNISON_MAX = 0.50      # fracao de frames multi-canal em mesma periodo (M3)
WHITE_MIN = 0.50       # fracao de eventos de ruido brancos (M4)
LOOP_MIN = 250         # frames de duracao minima de musica (M5)
CH_MIN = 2             # canais de tone soando (M6)
BREATH_MIN = 8.0       # frames por nota na camada que respira (M7)
ACTIVE_NOTES = 8       # abaixo disso o canal e jingle: aviso, nao blocker
SFX_MAX_FRAMES = 45    # S2


def decode(blob):
    """Decodifica um fluxo PSGlib.

    Retorna (events, duration): events e lista de (t, kind, ch, valor),
    kind em {f, v, nctl}; t e o tempo em frames VBlanks acumulados.
    """
    ev, t, last_latch = [], 0, None
    i = 0
    while i < len(blob):
        b = blob[i]
        if b >= 0x80:
            last_latch = b
            ch = (b >> 5) & 3
            if b & 0x10:
                ev.append((t, 'v', ch, b & 0x0F))
            elif ch == 3:
                ev.append((t, 'nctl', 3, b & 0x07))
            i += 1
        elif 0x40 <= b <= 0x7F and last_latch is not None:
            ch = (last_latch >> 5) & 3
            if ch < 3:
                ev.append((t, 'f', ch,
                           ((b & 0x3F) << 4) | (last_latch & 0x0F)))
            i += 1
        elif WAIT <= b <= 0x3F:
            # 0x38 = fim de frame; 0x39..0x3F = fim + (b&7) frames extras
            # (PSGlib.c: cp PSGWait / and #0x07 -> PSGMusicSkipFrames)
            t += 1 + (b & 0x07 if b > WAIT else 0)
            i += 1
        elif b == END:
            break
        else:
            i += 1
    return ev, t


def analyze(events, duration):
    """Aplica as seis clausulas. Retorna (violacoes, avisos, metricas)."""
    notes = {ch: [] for ch in range(3)}
    vols = {ch: set() for ch in range(4)}
    noise_ctl = []
    for (t, kind, ch, val) in events:
        if kind == 'f':
            notes[ch].append((t, val))
        elif kind == 'v':
            vols[ch].add(val)
        elif kind == 'nctl':
            noise_ctl.append((t, val))

    viol, warn, m = [], [], {}
    sounding = [ch for ch in range(3) if len(notes[ch]) >= ACTIVE_NOTES]
    m['canais_tone'] = sorted(
        ch for ch in range(3) if notes[ch])
    m['duracao_frames'] = duration
    m['notas'] = {ch: len(notes[ch]) for ch in range(3)}

    # M1 ritmo — usa eventos na ordem real de tempo
    gaps_by_ch = {}
    for ch in sounding:
        ts = [t for t, _ in notes[ch]]
        gaps = [b - a for a, b in zip(ts, ts[1:])]
        mean_gap = sum(gaps) / len(gaps) if gaps else 0.0
        gaps_by_ch[ch] = mean_gap
        if mean_gap < GAP_MIN:
            viol.append('M1 ritmo: ch%d troca de nota a cada %.2f frames '
                        '(< %.1f) — metralhadora de 16 Hz, nao melodia'
                        % (ch, mean_gap, GAP_MIN))
    m['gap_medio'] = {ch: round(g, 2) for ch, g in gaps_by_ch.items()}

    # M7 andamento — a camada que respira: algum canal de tone ativo
    # segura a nota por >= BREATH_MIN frames. Sem ela, ate um arranjo
    # "correto" ao ouvido e granulado ininterrompido.
    if gaps_by_ch:
        best_ch = max(gaps_by_ch, key=gaps_by_ch.get)
        best = gaps_by_ch[best_ch]
        m['camada_respira'] = {'ch': best_ch, 'gap': round(best, 2)}
        if best < BREATH_MIN:
            viol.append('M7 andamento: nenhuma camada segura nota por >= '
                        '%.0f frames (melhor gap %.2f em ch%d) — tudo em '
                        'movimento continuo soa como granulado, nao musica'
                        % (BREATH_MIN, best, best_ch))

    # M2 dinamica
    for ch in sounding:
        dy = len(vols[ch] - {15})
        if dy < VOL_VARIETY:
            viol.append('M2 dinamica: ch%d usa %d atenuacao(oes) != mudo '
                        '(min %d) — sem envelope nao ha ataque nem eco'
                        % (ch, dy, VOL_VARIETY))
    m['atenuacoes'] = {ch: sorted(v - {15}) for ch, v in vols.items() if v}

    # M3 registro — varre a linha do tempo com a nota sustentada por canal
    cur = {}
    vol_cur = {ch: 15 for ch in range(4)}
    multi = uni = 0
    by_time = {}
    for e in events:
        by_time.setdefault(e[0], []).append(e)
    for t in sorted(by_time):
        for (tt, kind, ch, val) in sorted(by_time[t],
                                          key=lambda e: e[1] != 'f'):
            if kind == 'f':
                cur[ch] = val
            elif kind == 'v':
                vol_cur[ch] = val
        sounding_now = [ch for ch in (0, 1, 2)
                        if ch in cur and vol_cur[ch] < 15]
        if len(sounding_now) >= 2:
            multi += 1
            if len({cur[ch] for ch in sounding_now}) == 1:
                uni += 1
    frac = uni / multi if multi else 0.0
    m['unison'] = round(frac, 3)
    if frac > UNISON_MAX:
        viol.append('M3 registro: %.0f%% dos frames com todos os canais '
                    'tocando tem a MESMA nota em todos — unison total e '
                    'buzzer, nao acorde' % (100 * frac))
    elif frac > 0.25:
        warn.append('M3: unison em %.0f%% dos frames (>25%%)' % (100 * frac))

    # M4 ruido
    if len(noise_ctl) >= ACTIVE_NOTES:
        white = sum(1 for _, mode in noise_ctl if not (mode & 0x04))
        wfrac = white / len(noise_ctl)
        if wfrac < WHITE_MIN:
            viol.append('M4 ruido: %.0f%% dos eventos de ch3 sao ruido '
                        'PERIODICO (R3 bit2=1 = assobio tonal); percussao '
                        'branca exige mode & 4 == 0' % (100 * (1 - wfrac)))
        m['ruido_branco'] = round(wfrac, 3)
    elif noise_ctl:
        warn.append('M4: ch3 com apenas %d eventos (jingle?)' % len(noise_ctl))
    if noise_ctl and len(vols[3] - {15}) < VOL_VARIETY:
        viol.append('M4 ruido: ch3 sem envelope de volume (%d atenuacao(oes)) '
                    '— percussao colada em volume unico e chiado'
                    % len(vols[3] - {15}))
    if not noise_ctl:
        warn.append('M4: sem canal de ruido — percussao ausente (permitido, '
                    'claim de mix completo nao)')

    # M5 loop
    if duration < LOOP_MIN:
        viol.append('M5 loop: duracao %d frames < %d (5 s a 50 Hz) — '
                    'loop de %0.1f s e tortura em batalha'
                    % (duration, LOOP_MIN, duration / 50.0))

    # M6 canais
    if len(sounding) < CH_MIN:
        if any(notes[ch] for ch in range(3)):
            viol.append('M6 canais: %d canal(is) de tone com >= %d notas — '
                        'PSG tem 3; 1 e deriva' % (len(sounding), ACTIVE_NOTES))
        else:
            viol.append('M6 canais: nenhum canal de tone ativo — jingle sem '
                        'conteudo melodico')
    return viol, warn, m


def analyze_sfx(events, duration):
    viol, warn = [], []
    volseq = {ch: [v for (t, k, c, v) in events if k == 'v' and c == ch]
              for ch in range(4)}
    first = next((v for ch in range(4) for v in volseq[ch] if v < 15), None)
    last = None
    for ch in range(4):
        s = [v for v in volseq[ch] if v < 15]
        if s:
            last = s[-1]
    if duration > SFX_MAX_FRAMES:
        viol.append('S2 duracao: SFX de %d frames > %d — pisa o proximo '
                    'evento' % (duration, SFX_MAX_FRAMES))
    if first is not None and last is not None and last <= first:
        viol.append('S1 decaimento: comeca na atenuacao %d e termina em %d '
                    '— sem fade o SFX corta seco e vira clique' % (first, last))
    if not any(v < 15 for ch in range(4) for v in volseq[ch]):
        viol.append('S1: SFX nunca tira canal do mudo — silencioso')
    return viol, warn


def classify(path, force=None):
    name = os.path.basename(path)
    if force:
        return force
    if name.startswith('music_'):
        return 'music'
    if name.startswith('sfx_'):
        return 'sfx'
    return 'music'


def audit_one(path, force=None):
    blob = open(path, 'rb').read()
    ev, dur = decode(blob)
    kind = classify(path, force)
    if kind == 'music':
        viol, warn, m = analyze(ev, dur)
    else:
        viol, warn = analyze_sfx(ev, dur)
        m = {'duracao_frames': dur}
    return {
        'arquivo': os.path.basename(path),
        'classe': kind,
        'bytes': len(blob),
        'sha256': hashlib.sha256(blob).hexdigest(),
        'metricas': m,
        'violacoes': viol,
        'avisos': warn,
        'veredito': 'reprova' if viol else 'passa',
    }


def report_json(root, results):
    return {
        'schema': 'psg_quality_v1',
        'tool': os.path.basename(__file__),
        'project': os.path.abspath(root) if root else None,
        'reprova': sorted(r['arquivo'] for r in results
                          if r['veredito'] == 'reprova'),
        'results': results,
    }


# ---------------------------------------------------------------- fixtures
def _enc(frames):
    """frames: lista de (lista_de_latches_ou_dados, hold_extra)."""
    out = bytearray()
    for data, hold in frames:
        out.extend(data)
        out.append(WAIT + hold if hold else WAIT)
    out.append(END)
    return bytes(out)


def _tone(ch, period):
    base = (0x80, 0xA0, 0xC0)[ch]
    return [base | (period & 0x0F), 0x40 | ((period >> 4) & 0x3F)]


def _vol(ch, att):
    return [0x90 | (ch << 5) | (att & 0x0F)]


def _noise(mode, att):
    return [0xE0 | (mode & 0x07), 0xF0 | (att & 0x0F)]


def _arena_style():
    """O defeito real medido em arena_nocturna/hamoopig: 3 canais em unisono,
    nota nova todo frame, volume 1 em tudo, ruido periodico colado."""
    fr = []
    for p in (0x0A0, 0x0B8, 0x0D0, 0x0E8) * 8:   # 32 frames < 125
        fr.append((_tone(0, p) + _vol(0, 1)
                   + _tone(1, p) + _vol(1, 1)
                   + _tone(2, p) + _vol(2, 1)
                   + _noise(0x04, 1), 0))
    return _enc(fr)


def _arranjo():
    """Conformidade: lead com envelope, baixo em outra oitava, percussao
    branca gateada, ~14 frames por compasso -> loop de 392 frames."""
    mel = (0x1F4, 0x280, 0x240, 0x1C2)
    bass = (0x3E8, 0x3A0, 0x300, 0x348)   # >>1 nunca coincide com mel
    fr = []
    for bar in range(28):
        p_mel, p_bass = mel[bar % 4], bass[bar % 4]
        fr.append((_tone(0, p_mel) + _vol(0, 2)
                   + _tone(2, p_bass) + _vol(2, 4)
                   + _noise(0x02, 3), 3))
        fr.append((_vol(0, 5) + _vol(2, 6) + _vol(3, 15), 3))
        fr.append((_tone(2, p_bass >> 1) + _vol(2, 3)
                   + _vol(0, 7) + _noise(0x03, 4), 2))
        fr.append((_vol(0, 9) + _vol(2, 15) + _vol(3, 15), 2))
    return _enc(fr)


def _sfx_bom():
    return _enc([(_tone(2, 0x0C0) + _vol(2, 1), 0),
                 (_tone(2, 0x090) + _vol(2, 5), 0),
                 (_tone(2, 0x060) + _vol(2, 9), 0),
                 (_tone(2, 0x050) + _vol(2, 14), 0)])


def _granulado():
    """O furo M7 (queixa humana 2026-09-25): arranjo tecnicamente correto —
    sem unissono, com envelope, ruido branco, loop longo — mas NENHUMA camada
    segura a nota por >= 8 frames. Passava no piso antigo inteiro; so M7."""
    mel = (0x1F4, 0x22C, 0x274, 0x238)
    bass = (0x3E8, 0x3A0, 0x300, 0x348)
    arp = (0x280, 0x2D0, 0x320)
    fr = []
    for i in range(70):                       # 4 frames/passo -> 280 frames
        fr.append((_tone(0, mel[i % 4]) + _vol(0, 2 if i % 2 else 4)
                   + _tone(2, bass[i % 4]) + _vol(2, 3 if i % 2 else 5)
                   + _noise(0x02 if i % 2 else 0x00, 3 if i % 2 else 6), 1))
        fr.append((_tone(1, arp[i % 3]) + _vol(1, 6 if i % 2 else 8), 1))
    return _enc(fr)


def _sfx_clique():
    return _enc([(_tone(2, 0x0C0) + _vol(2, 1), 7),
                 (_tone(2, 0x0C0) + _vol(2, 1), 7),
                 (_tone(2, 0x0C0) + _vol(2, 1), 7),
                 (_tone(2, 0x0C0) + _vol(2, 1), 7),
                 (_tone(2, 0x0C0) + _vol(2, 1), 7),
                 (_tone(2, 0x0C0) + _vol(2, 1), 7),
                 (_tone(2, 0x0C0) + _vol(2, 1), 7)])


def _sfx_longo():
    return _enc([(_tone(2, 0x0C0) + _vol(2, v % 12 + 1), 0)
                 for v in range(60)])


def self_check():
    ok = []
    ev, dur = decode(_arena_style())
    ok.append(('arena-estilo reprova em ritmo',
               any('M1' in x for x in analyze(ev, dur)[0])))
    ok.append(('arena-estilo reprova em unisono',
               any('M3' in x for x in analyze(ev, dur)[0])))
    ok.append(('arena-estilo reprova em ruido periodico',
               any('M4' in x for x in analyze(ev, dur)[0])))
    ok.append(('arena-estilo reprova em loop',
               any('M5' in x for x in analyze(ev, dur)[0])))
    ok.append(('arena-estilo reprova em dinamica',
               any('M2' in x for x in analyze(ev, dur)[0])))
    ev, dur = decode(_arranjo())
    viol, warn, m = analyze(ev, dur)
    ok.append(('arranjo passa (viol=%s)' % viol[:1], viol == []))
    ok.append(('arranjo tem loop valido', dur >= LOOP_MIN))
    # M7: o granulado correto — passava no piso antigo inteiro; so M7 pega
    ev, dur = decode(_granulado())
    viol, _w, m7 = analyze(ev, dur)
    ok.append(('granulado reprova exclusivamente M7',
               len(viol) == 1 and 'M7' in viol[0]))
    ok.append(('granulado nao reprovava M1..M6', dur >= LOOP_MIN
               and m7['unison'] <= UNISON_MAX))
    ev, dur = decode(_sfx_bom())
    ok.append(('sfx com decay passa', analyze_sfx(ev, dur)[0] == []))
    ev, dur = decode(_sfx_clique())
    ok.append(('sfx sem decay reprova',
               any('S1' in x for x in analyze_sfx(ev, dur)[0])))
    ev, dur = decode(_sfx_longo())
    ok.append(('sfx longo reprova',
               any('S2' in x for x in analyze_sfx(ev, dur)[0])))
    # round-trip do decodificador: latch+dados viram o period esperado
    ev, _ = decode(_enc([(_tone(1, 0x123), 0)]))
    periods = [v for (t, k, c, v) in ev if k == 'f']
    ok.append(('round-trip de periodo', periods == [0x123]))
    # hold > WAIT avanca o relogio corretamente
    ev, dur = decode(_enc([(_tone(0, 0x80), 3), (_tone(0, 0x90), 0)]))
    ts = [t for (t, k, c, v) in ev if k == 'f']
    ok.append(('hold de 3 frames conta no tempo', ts[1] - ts[0] == 4
               and dur == 5))
    # canal 3 com periodicos viram fracao correta
    ev, dur = decode(_arena_style())
    w = [v for (t, k, c, v) in ev if k == 'nctl']
    ok.append(('nctl capturado com modo', all(v == 0x04 for v in w)))
    # audit_one de ponta a ponta — foi aqui que o unpack de SFX quebrou uma
    # vez: o self-check chamava analyze_sfx direto, nunca a entrada publica.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p_sfx = os.path.join(td, 'sfx_x.psg')
        p_mus = os.path.join(td, 'music_x.psg')
        open(p_sfx, 'wb').write(_sfx_bom())
        open(p_mus, 'wb').write(_arena_style())
        r1 = audit_one(p_sfx)
        r2 = audit_one(p_mus)
        ok.append(('audit_one sfx classes e decide',
                   r1['classe'] == 'sfx' and r1['veredito'] == 'passa'))
        ok.append(('audit_one music reprovada',
                   r2['classe'] == 'music'
                   and r2['veredito'] == 'reprova'))
    for nome, bom in ok:
        print('  %-48s %s' % (nome, 'ok' if bom else 'FALHOU'))
    if not all(b for _, b in ok):
        print('[SELF-CHECK FAIL] audit_psg_quality')
        return 1
    print('[SELF-CHECK OK] audit_psg_quality')
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project')
    ap.add_argument('--psg', nargs='*')
    ap.add_argument('--json', dest='json_out')
    ap.add_argument('--self-check', action='store_true')
    args = ap.parse_args()
    if args.self_check:
        return self_check()

    paths = list(args.psg or [])
    root = args.project
    if root:
        paths += sorted(glob.glob(os.path.join(root, 'res', 'audio', '*.psg')))
    if not paths:
        print('[FAIL_USO] informe --project ou --psg')
        return 3
    results = []
    for p in paths:
        if not os.path.isfile(p):
            print('[FAIL_ARQUIVO] %s' % p)
            return 3
        results.append(audit_one(p))
    rep = report_json(root, results)
    if args.json_out:
        with open(args.json_out, 'w', encoding='utf-8') as f:
            json.dump(rep, f, indent=1)
    fails = rep['reprova']
    for r in results:
        mark = 'X ' if r['veredito'] == 'reprova' else '. '
        print('%s%-24s %s %dB dur=%df' % (mark, r['arquivo'], r['classe'],
                                          r['bytes'],
                                          r['metricas'].get('duracao_frames', 0)))
        for v in r['violacoes']:
            print('    VIOLACAO %s' % v)
        for w in r['avisos']:
            print('    aviso    %s' % w)
    print('[psg-quality] %d/%d streams reprovados no piso de qualidade'
          % (len(fails), len(results)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
