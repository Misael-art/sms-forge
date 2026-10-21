#!/usr/bin/env python3
"""m3_caso4_diff.py — o SFX ouve-se SOBRE a música? Comparação diferencial.

Duas capturas da MESMA sessão/rota/cena: uma com N presses de SELECT, outra
sem press nenhum (controle). Como `music_dawn` é determinística, a diferença
entre as curvas de energia só pode vir do SFX — MAS as duas corridas entram na
cena em frames diferentes, então alinha-se primeiro por correlação de energia e
só depois se mede o delta. Sem alinhamento, o próprio defasamento da música
aparece como "falso SFX" (visto em 2026-10-14: delta de +1053 em t=0 sem
press nenhum).

Estatística robusta: a linha de base do delta é a mediana + MAD de todas as
janelas; um press é "ouvido" quando a janela dele passa de `--z` MADs.
Uso:
  python3 tools/m3_caso4_diff.py out/escuta/w3_dawn_select.wav \
      out/escuta/w3b_dawn_control.wav --hops 0.2,2.6,4.0,4.6
Exit: 0 = todo press acima da linha de base | 1 = pelo menos um invisível
"""
import sys, wave, argparse
import numpy as np

def curve(path, hop):
    w = wave.open(path); sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float)
    m = a.size // hop
    return np.array([np.sqrt((a[i*hop:(i+1)*hop] ** 2).mean()) for i in range(m)]), sr

def self_check():
    """Prova da própria ferramenta: ruído injetado + defasamento conhecido.

    Sem isto o delta poderia ser a música fora de fase (o erro que esta
    ferramenta existe para não cometer).
    """
    import tempfile, os, subprocess
    sr = 44100; dur = 4.0
    t = np.arange(int(sr * dur)) / sr
    # envelope com estrutura (ataques + pausas): sem isso a fase não é
    # identificável e o self-check só provaria o pior caso da ferramenta.
    env = np.ones_like(t)
    for i in range(int(dur / 0.25)):
        if i % 4 == 3:
            env[int(i * 0.25 * sr):int((i + 1) * 0.25 * sr)] = 0.0      # pausa
        else:
            env[int(i * 0.25 * sr):int((i + 1) * 0.25 * sr)] *= (
                0.4 + 0.6 * np.abs(np.sin(np.pi * (t[int(i * 0.25 * sr):
                                 int((i + 1) * 0.25 * sr)] * 4))))
    base = 2000 * np.sin(2 * np.pi * 220 * t) * env
    shifted = np.roll(base, int(0.3 * sr))                 # defasagem conhecida
    burst = shifted.copy()
    i0 = int(1.5 * sr); i1 = i0 + int(0.25 * sr)
    rng = np.random.default_rng(7)
    burst[i0:i1] += rng.normal(0, 9000, i1 - i0)           # "SFX" sobre a música
    d = tempfile.mkdtemp()
    paths = []
    for name, data in (("control", base), ("sfx", burst)):
        p = os.path.join(d, name + ".wav"); w = wave.open(p, "w")
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(np.clip(data, -32768, 32767).astype('<i2').tobytes()); w.close()
        paths.append(p)
    # deve PASSAR com o press real, e a defasagem conhecida tem de ser recuperada
    ok = subprocess.run([sys.executable, __file__, paths[1], paths[0],
                         "--hops", "1.5"], capture_output=True, text=True)
    bad = subprocess.run([sys.executable, __file__, paths[1], paths[0],
                          "--hops", "2.8"], capture_output=True, text=True)
    print(ok.stdout.strip())
    assert ok.returncode == 0, "self-check: burst injetado não foi detectado"
    assert bad.returncode != 0, "self-check: delta falso-positivo (sem burst) passou"
    # o shift é recuperado módulo a periodicidade do padrão musical (−0,7 ≡ +0,3
    # num compasso de 1 s), então a prova é a QUALIDADE do encaixe, não o valor.
    alin = ok.stdout.split("[alinhe]")[1].split("\n")[0]
    rob = float(alin.split("|d|mediana=")[1].split(" ")[0])
    rob0 = float(alin.split("(sem alinhar ")[1].split(")")[0])
    assert rob < 0.1 * rob0, f"self-check: encaixe fraco ({rob} vs {rob0})"
    # contagem de transientes: um burst injetado deve dar exatamente 1 evento,
    # e pedir 2 deve reprovar (a contagem não pode ser generosa consigo mesma)
    cnt = subprocess.run([sys.executable, __file__, paths[1], paths[0],
                          "--expect", "1"], capture_output=True, text=True)
    cnt_bad = subprocess.run([sys.executable, __file__, paths[1], paths[0],
                              "--expect", "2"], capture_output=True, text=True)
    print(cnt.stdout.strip())
    assert cnt.returncode == 0, "self-check: contagem não viu o único burst"
    assert cnt_bad.returncode != 0, "self-check: contagem aceitou 2 eventos inexistentes"
    print("[SELF-CHECK OK] alinhamento + detecção por z + contagem conferidos")
    return 0

def main():
    p = argparse.ArgumentParser()
    p.add_argument("with_sfx", nargs="?", default=""); p.add_argument("control", nargs="?", default="")
    p.add_argument("--hop", type=float, default=0.025, help="janela de RMS em s")
    p.add_argument("--max-shift", type=float, default=3.0)
    p.add_argument("--z", type=float, default=6.0)
    p.add_argument("--hops", default="", help="tempos (s) dos presses, lista vírgula")
    p.add_argument("--expect", type=int, default=0,
                   help="contar transientes e exigir exatamente este número")
    p.add_argument("--self-check", action="store_true")
    a = p.parse_args()
    if a.self_check: return self_check()
    if not a.with_sfx or not a.control:
        print("uso: m3_caso4_diff.py WITH_SFX.wav CONTROL.wav --hops t1,t2 | --self-check")
        return 2

    step = int(a.hop * 44100)
    ra, sr = curve(a.with_sfx, step)
    rb, _ = curve(a.control, step)
    # loudness por MEDIANA das janelas, não por RMS global: um SFX alto é
    # exatamente o outlier que descalibraria a normalização e faria nenhum shift
    # bater (visto no --self-check com burst 4× a música).
    def norm(c):
        pos = c[c > 0]
        return c / (np.median(pos) if pos.size else 1.0)
    ra = norm(ra); rb = norm(rb)

    def cost(k):                                     # ra adiantado de k janelas
        x = ra[max(k, 0):]; y = rb[max(-k, 0):]
        L = min(x.size, y.size)
        diff = np.abs(x[:L] - y[:L])
        # mediana, não média: o SFX é exatamente o outlier que a média engoliria
        # (visto no --self-check: com burst grande o mse nunca cai e a fase
        # parece "não identificável" por causa do próprio fenômeno medido)
        return float(np.median(diff)), float(np.mean(diff ** 2)), L

    kmax = int(a.max_shift / a.hop)
    mad0, err0, _ = cost(0)
    best = min(((cost(k)[0], k) for k in range(-kmax, kmax + 1)))
    rob, k = best
    m_rob, err, L = cost(k)
    # identificabilidade: com envelope quase plano todo shift empata e o argmin
    # vira ajuste de ruído (visto no --self-check: shift −1,5 s inventado).
    identificado = rob < 0.5 * mad0
    if not identificado:
        k = 0; m_rob, err, L = cost(0)
    m = max(k, 0)
    x = ra[m:m + L]; y = rb[max(-k, 0):max(-k, 0) + L]
    d = x - y

    med = float(np.median(d)); mad = float(np.median(np.abs(d - med))) or 1e-9
    print(f"[alinhe] shift={k * a.hop:+.3f}s |d|mediana={m_rob:.4f} "
          f"(sem alinhar {mad0:.4f}) mse={err:.4f} "
          f"identificavel={'sim' if identificado else 'NAO'} janelas={L} "
          f"hop={a.hop * 1000:.0f}ms")
    print(f"[linha de base] delta mediana={med:+.3f} MAD={mad:.3f} "
          f"p95={np.percentile(d, 95):+.3f} max={d.max():+.3f}")
    presses = [float(v) for v in a.hops.split(",") if v.strip()]
    if not presses and a.expect:
        z = (d - med) / mad
        hot = z >= a.z
        events = []; i = 0
        while i < L:
            if not hot[i]: i += 1; continue
            j = i
            while j + 1 < L and (hot[j + 1] or (j + 3 < L and hot[j + 2])):
                j += 1
            k = int(np.argmax(d[i:j + 1])) + i
            events.append(((i + m) * a.hop, (j - i + 1) * a.hop, d[k], z[k]))
            i = j + 1
        print(f"[eventos] {len(events)} transiente(s) acima de z={a.z} MAD")
        for t0, dur, pk, zk in events:
            print(f"   t={t0:5.2f}s dur={dur:.2f}s delta={pk:+.3f} z={zk:.1f}")
        ok = len(events) == a.expect
        print(f"[veredito] {'PASS' if ok else 'FAIL'} — esperado {a.expect} "
              f"press(es), observado {len(events)} transiente(s)")
        return 0 if ok else 1
    if not presses:
        top = np.argsort(d)[::-1][:6]
        print("[sem --hops] maiores deltas (relógio do with_sfx):")
        for j in sorted(top):
            print(f"   {(j + m) * a.hop:5.2f}s delta={d[j]:+.3f} z={(d[j] - med) / mad:.1f}")
        print("[veredito] N/A — rode com --hops para afirmar audibilidade por press")
        return 0
    if not identificado:
        print("[veredito] NAO PROVADE — fase entre as duas corridas não é "
              "identificável; o delta não separa SFX de música fora de fase")
        return 1
    verdict_all = True
    for t in presses:
        j0 = int(round(t / a.hop)) - m               # relógio do with_sfx → alinhado
        if not (0 <= j0 < L):
            print(f"[press {t:.2f}s] fora da janela alinhada"); verdict_all = False; continue
        win = d[max(j0 - 2, 0):j0 + 12]              # SFX ≈ 19–29 f = 0,3–0,5 s
        j = int(np.argmax(win)) + max(j0 - 2, 0)
        z = (d[j] - med) / mad
        ok = z >= a.z
        verdict_all &= ok
        print(f"[press {t:.2f}s] pico delta={d[j]:+.3f} z={z:.1f} MAD "
              f"({'OUVIDO' if ok else 'INVISIVEL'}) em {(j + m) * a.hop:.2f}s "
              f"(controle ali: rms={y[j]:.3f})")
    print(f"[veredito] {'PASS' if verdict_all else 'FAIL'} — "
          "cada press precisa estar acima da linha de base do delta")
    return 0 if verdict_all else 1

sys.exit(main())
