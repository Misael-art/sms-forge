#!/usr/bin/env python3
"""Heuristicas de composicao para streams PSGlib simples, nao qualidade auditiva.

Formato latches/dados, WAIT 0x38..0x3F, END 0x00 e loop point 0x01.
SN76489: atenuacao 0=alto/15=mudo; R3 bit2=1 ruido branco,
bit2=0 ruido periodico. Bits 1..0 selecionam a taxa; 3 usa tone ch2.
PSGlib.c confirma o transporte, BlastEm psg.c confirma o feedback.

Politica M1..M7: gap medio entre escritas de periodo >=2 frames, variedade
 de atenuacoes, estados de eventos sem unissono excessivo, maioria de comandos
 de ruido branco com variedade de volume, >=250 frames, >=2 canais com oito
 escritas de periodo e algum gap medio >=8 frames. Limiares sao escolhas do
 projeto; nao leis musicais. Comando de periodo repetido nao e nota nova,
 cardinalidade de volumes nao prova envelope e PASS nao prova musica/AAA.
 SFX: politica de atenuacao inicial/final e duracao <=45 frames.

Um frame e uma chamada PSGFrame, nao Hz fixos. Se o driver chama uma vez por
VBlank, taxas sao 50/60 Hz conforme PAL/NTSC. Medir a cadencia real e ouvir a
captura isolada continuam necessarios. O decodificador nao expande substrings
comprimidas; elas sao recusadas, sem resultado de qualidade sobre bytes crus.

Uso: audit_psg_quality.py --project <p> [--json out]
     audit_psg_quality.py --psg <a.psg> [...]
Exit: 0 passa politica | 1 violacao ou formato nao suportado | 3 uso/arquivo
"""
import argparse
import glob
import hashlib
import json
import os
import sys

WAIT, END, LOOPPT = 0x38, 0x00, 0x01

GAP_MIN = 2.0          # gap medio entre escritas de periodo (M1)
VOL_VARIETY = 2        # atenuacoes distintas != 15 (M2)
UNISON_MAX = 0.50      # instantes de eventos multi-canal, nao duracao (M3)
WHITE_MIN = 0.50       # fracao de eventos de ruido brancos (M4)
LOOP_MIN = 250         # frames de duracao minima de musica (M5)
CH_MIN = 2             # canais de tone soando (M6)
BREATH_MIN = 8.0       # gap medio entre escritas de periodo (M7)
ACTIVE_NOTES = 8       # elegibilidade da politica, nao identificacao de jingle
SFX_MAX_FRAMES = 45    # S2


def decode(blob):
    """Decodifica um fluxo PSGlib.

    Retorna (events, duration): events e lista de (t, kind, ch, valor),
    kind em {f, v, nctl}; t conta chamadas PSGFrame. Tone exige low+high
    contiguos; high-only e data apos volume/noise sao recusados.
    """
    ev, t = [], 0
    i = 0
    while i < len(blob):
        b = blob[i]
        if b >= 0x80:
            ch = (b >> 5) & 3
            if b & 0x10:
                ev.append((t, 'v', ch, b & 0x0F))
                i += 1
            elif ch == 3:
                ev.append((t, 'nctl', 3, b & 0x07))
                i += 1
            else:
                # Subconjunto suportado: low latch + high data contiguos.
                # Low-only e data apos volume podem ser escritas PSG reais,
                # mas nao pertencem a esta gramatica/driver preview simplificado.
                if i + 1 >= len(blob) or not 0x40 <= blob[i + 1] <= 0x7F:
                    raise ValueError('tone latch no offset %d exige high-data '
                                     '0x40..0x7F imediatamente; low-only nao suportado' % i)
                ev.append((t, 'f', ch, ((blob[i + 1] & 0x3F) << 4) | (b & 0x0F)))
                i += 2
        elif 0x40 <= b <= 0x7F:
            raise ValueError('PSG data no offset %d sem tone-pair contiguo; '
                             'data apos volume/noise ou high-only nao suportado' % i)
        elif WAIT <= b <= 0x3F:
            t += 1 + (b & 0x07 if b > WAIT else 0)
            i += 1
        elif b == END:
            break
        elif b == LOOPPT:
            i += 1  # Politica avalia a primeira passagem, nao o loop ouvido.
        else:
            raise ValueError('PSGlib comando 0x%02X no offset %d nao suportado; '
                             'substring comprimida exige expansao antes da analise' % (b, i))
    return ev, t


def analyze(events, duration):
    """Aplica politicas M1..M7 sobre eventos; nao avalia som nem qualidade."""
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
    m['notas'] = {ch: len(notes[ch]) for ch in range(3)}  # chave legada: escritas
    m['escopo'] = 'heuristica_eventos_psglib_simples_primeira_passagem'
    m['contagem_notas_significa'] = 'escritas_periodo; nao notas distintas/ataques'
    m['unison_denominador'] = 'instantes_com_eventos_multicanal; nao frames sustentados'

    # M1 ritmo — usa eventos na ordem real de tempo
    gaps_by_ch = {}
    for ch in sounding:
        ts = [t for t, _ in notes[ch]]
        gaps = [b - a for a, b in zip(ts, ts[1:])]
        mean_gap = sum(gaps) / len(gaps) if gaps else 0.0
        gaps_by_ch[ch] = mean_gap
        if mean_gap < GAP_MIN:
            viol.append('M1 ritmo: ch%d troca de nota a cada %.2f frames '
                        '(< %.1f) — abaixo da politica de espacamento; nao mede Hz'
                        % (ch, mean_gap, GAP_MIN))
    m['gap_medio'] = {ch: round(g, 2) for ch, g in gaps_by_ch.items()}

    # M7 espacamento medio — proxy de densidade, nao nota sustentada/escuta.
    if gaps_by_ch:
        best_ch = max(gaps_by_ch, key=gaps_by_ch.get)
        best = gaps_by_ch[best_ch]
        m['camada_respira'] = {'ch': best_ch, 'gap': round(best, 2)}
        if best < BREATH_MIN:
            viol.append('M7 andamento: nenhum canal tem gap medio >= '
                        '%.0f frames (melhor gap %.2f em ch%d) — '
                        'escritas abaixo da politica de espacamento medio'
                        % (BREATH_MIN, best, best_ch))

    # M2 dinamica
    for ch in sounding:
        dy = len(vols[ch] - {15})
        if dy < VOL_VARIETY:
            viol.append('M2 dinamica: ch%d usa %d atenuacao(oes) != mudo '
                        '(min %d) — abaixo da politica de variedade; nao prova envelope'
                        % (ch, dy, VOL_VARIETY))
    m['atenuacoes'] = {ch: sorted(v - {15}) for ch, v in vols.items() if v}

    # M3 registro — amostra estados nos instantes de eventos, sem ponderar duracao
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
        viol.append('M3 registro: %.0f%% dos instantes de eventos multicanal '
                    'tem o mesmo periodo — acima da politica de unissono' % (100 * frac))
    elif frac > 0.25:
        warn.append('M3: unison em %.0f%% dos instantes de eventos (>25%%)' % (100 * frac))

    # M4 ruido
    if len(noise_ctl) >= ACTIVE_NOTES:
        white = sum(1 for _, mode in noise_ctl if not (mode & 0x04))
        wfrac = white / len(noise_ctl)
        if wfrac < WHITE_MIN:
            viol.append('M4 ruido: %.0f%% dos eventos de ch3 sao ruido '
                        'PERIODICO (R3 bit2=0); politica de maioria branca '
                        'exige mode & 4 != 0; nao e lei de percussao' % (100 * (1 - wfrac)))
        m['ruido_branco'] = round(wfrac, 3)
    elif noise_ctl:
        warn.append('M4: ch3 com apenas %d eventos (abaixo da elegibilidade)' % len(noise_ctl))
    if noise_ctl and len(vols[3] - {15}) < VOL_VARIETY:
        viol.append('M4 ruido: ch3 sem envelope de volume (%d atenuacao(oes)) '
                    '— abaixo da politica de variedade; nao prova envelope'
                    % len(vols[3] - {15}))
    if not noise_ctl:
        warn.append('M4: sem comandos de ruido; permitido, nao permite inferir '
                    'presenca/ausencia de percussao ou qualidade do mix')

    # M5 loop
    if duration < LOOP_MIN:
        viol.append('M5 loop: primeira passagem %d frames < %d — '
                    'politica de comprimento; nao mede loop audivel/segundos'
                    % (duration, LOOP_MIN))

    # M6 canais
    if len(sounding) < CH_MIN:
        if any(notes[ch] for ch in range(3)):
            viol.append('M6 canais: %d canal(is) de tone com >= %d notas — '
                        'abaixo da politica de densidade; nao mede canais audiveis' % (len(sounding), ACTIVE_NOTES))
        else:
            viol.append('M6 canais: nenhum canal de tone ativo — jingle sem '
                        'escritas de periodo suficientes para esta politica')
    return viol, warn, m


def analyze_sfx(events, duration):
    viol, warn = [], []
    # Timeline estavel: primeiro tempo, depois ordem de escrita dentro do frame.
    volumes = [e for e in sorted(events, key=lambda e: e[0]) if e[1] == 'v']
    audible_start = next((i for i, e in enumerate(volumes) if e[3] < 15), None)
    if duration > SFX_MAX_FRAMES:
        viol.append('S2 duracao: SFX de %d frames > %d — acima da politica '
                    'de duracao' % (duration, SFX_MAX_FRAMES))
    if audible_start is None:
        viol.append('S1: nenhuma atenuacao !=15 declarada — nao prova som')
    else:
        first, last = volumes[audible_start][3], volumes[-1][3]
        if last <= first:
            viol.append('S1 decaimento: primeira atenuacao nao muda %d e '
                        'ultima escrita %d — sem crescimento liquido na '
                        'politica temporal; nao mede waveform/clique' % (first, last))
        if len({e[2] for e in volumes[audible_start:]}) > 1:
            warn.append('S1 multicanal: compara escritas inicial/final globalmente; '
                        'nao prova fade de cada canal nem mix silencioso')
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
    kind = classify(path, force)
    try:
        ev, dur = decode(blob)
    except ValueError as error:
        return {'arquivo': os.path.basename(path), 'classe': kind,
                'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest(),
                'metricas': {'escopo': 'formato_nao_suportado'},
                'violacoes': ['FORMAT: ' + str(error)], 'avisos': [],
                'veredito': 'reprova'}
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
        'claim_ceiling': 'heuristicas_de_eventos; nao som, musica_aprovada ou AAA',
        'noise_feedback': 'R3 bit2: 1=white, 0=periodic',
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
                   + _noise(0x00, 1), 0))
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
                   + _noise(0x06, 3), 3))
        fr.append((_vol(0, 5) + _vol(2, 6) + _vol(3, 15), 3))
        fr.append((_tone(2, p_bass >> 1) + _vol(2, 3)
                   + _vol(0, 7) + _noise(0x07, 4), 2))
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
                   + _noise(0x06 if i % 2 else 0x04, 3 if i % 2 else 6), 1))
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
    # Feedback de todos os modos: bit2=1 branco; bits1..0 nao alteram classe.
    ev, dur = decode(_arena_style())
    w = [v for (t, k, c, v) in ev if k == 'nctl']
    ok.append(('nctl capturado com modo', all(v == 0x00 for v in w)))
    for mode in range(8):
        noise_events, noise_dur = decode(_enc([
            (_noise(mode, 2 if i % 2 else 5), 7) for i in range(8)]))
        nv, _nw, nm = analyze(noise_events, max(noise_dur, LOOP_MIN))
        expected_white = 1.0 if mode & 4 else 0.0
        noise_policy_failure = any('M4 ruido:' in x for x in nv)
        ok.append(('modo %d branco=%s (bit2)' % (mode, bool(mode & 4)),
                   nm['ruido_branco'] == expected_white and
                   noise_policy_failure == (expected_white == 0.0)))
    for modes, expected in (((0, 1, 2, 3, 4, 5, 6, 7), 0.5),
                            ((0, 1, 2, 3, 0, 1, 4, 5), 0.25)):
        ne, nd = decode(_enc([(_noise(mode, 2 if i % 2 else 5), 7)
                             for i, mode in enumerate(modes)]))
        nv, _nw, nm = analyze(ne, LOOP_MIN)
        ok.append(('mistura branco %.2f e limiar M4' % expected,
                   nm['ruido_branco'] == expected and
                   any('M4 ruido:' in x for x in nv) == (expected < WHITE_MIN)))
    # Compressed bytes cannot be silently treated as literal PSG commands.
    try:
        decode(bytes([0x08, 0x80, 0x00, 0x38, 0x00]))
        ok.append(('substring PSGlib recusada sem expansao', False))
    except ValueError:
        ok.append(('substring PSGlib recusada sem expansao', True))
    for name, blob in (('tone low seguido WAIT', bytes([0x80, WAIT, END])),
                       ('volume latch seguido data', bytes([0x90, 0x42, WAIT, END])),
                       ('tone low truncado', bytes([0x80])),
                       ('data sem latch', bytes([0x42, WAIT, END]))):
        original = bytes(blob)
        try:
            decode(blob)
            ok.append((name + ' recusado', False))
        except ValueError:
            ok.append((name + ' recusado sem alterar bytes', blob == original))
    temporal = [(0, 'v', 3, 1), (1, 'v', 0, 14)]
    ok.append(('SFX canais nao invertem ordem temporal',
               analyze_sfx(temporal, 2)[0] == []))
    ok.append(('SFX ordem temporal contraria reprova',
               any('S1' in x for x in analyze_sfx([(0, 'v', 0, 14),
                                                  (1, 'v', 3, 1)], 2)[0])))
    ok.append(('SFX ultima escrita mudo permite decay',
               analyze_sfx([(0, 'v', 2, 1), (1, 'v', 2, 15)], 2)[0] == []))
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
    print('[psg-quality] %d/%d streams reprovados na politica de eventos'
          % (len(fails), len(results)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
