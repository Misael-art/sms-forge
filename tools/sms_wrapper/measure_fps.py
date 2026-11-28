#!/usr/bin/env python3
"""measure_fps.py — F2 do PLANO_CONTINUACAO: amostra o FPS reportado pelo
próprio emulador no título da janela principal ("Emulicious - NN% (NN fps)").

Uso: measure_fps.py [--samples 6] [--interval 1.0] [-o saida.json] [--self-check]
Exit: 0 com JSON | 2 janela nao encontrada
"""
import sys, os, json, time, argparse, subprocess, re

# F2 exige >=5 amostras para o eixo fps_constante fechar.
MIN_SAMPLES = 5

def parse_title(title):
    """Extrai (fps, pct) do titulo da janela. Funcao PURA — testavel sem emulador."""
    m = re.search(r"\((\d+)\s*fps\)", title or "")
    pct = re.search(r"-\s*(\d+)%", title or "")
    return (int(m.group(1)) if m else None,
            int(pct.group(1)) if pct else None)

def verdict(samples):
    """Deriva o veredito a partir das amostras. Funcao PURA — testavel."""
    fps_vals = [s["fps"] for s in samples if s.get("fps") is not None]
    return {"fps_min": min(fps_vals) if fps_vals else None,
            "evidence_scope": "emulator_title_only_not_ROM_functional_FPS",
            "implementation_accepted": False,
            "fps_max": max(fps_vals) if fps_vals else None,
            "fps_media": round(sum(fps_vals) / len(fps_vals), 1) if fps_vals else None,
            "amostras_validas": len(fps_vals),
            "amostras_suficientes": len(fps_vals) >= MIN_SAMPLES,
            "constante_50_60": (bool(fps_vals)
                                and len(fps_vals) >= MIN_SAMPLES
                                and all(50 <= v <= 60 for v in fps_vals))}

def self_check():
    # parsing do titulo real do Emulicious
    assert parse_title("Emulicious - 100% (60 fps)") == (60, 100), "parse do titulo falhou"
    assert parse_title("sem informacao") == (None, None), "titulo sem fps deveria dar None"
    # veredito positivo: 6 amostras dentro de 50-60
    ok = verdict([{"fps": v} for v in (58, 59, 60, 59, 58, 60)])
    assert ok["constante_50_60"] and ok["fps_media"] == 59.0, f"veredito bom errado: {ok}"
    # REPROVA: fps fora da faixa
    bad = verdict([{"fps": v} for v in (30, 31, 29, 30, 30)])
    assert not bad["constante_50_60"], "30fps nao pode passar como constante_50_60"
    # REPROVA: amostras insuficientes (F2 exige >=5)
    few = verdict([{"fps": 60}, {"fps": 60}])
    assert not few["constante_50_60"], "2 amostras nao podem fechar o eixo"
    assert not few["amostras_suficientes"]
    # REPROVA: nenhuma leitura valida
    assert not verdict([{"fps": None}])["constante_50_60"], "sem leitura nao pode passar"
    print("[SELF-CHECK OK] measure_fps (parse de titulo + veredito: "
          "reprova fps fora da faixa, amostras insuficientes e leitura vazia)")
    return 0

def xdotool(*args):
    r = subprocess.run(["xdotool", *args], capture_output=True, text=True)
    return r if r.returncode == 0 else None

def find_main_window():
    r = xdotool("search", "--class", "Emulicious")
    ids = r.stdout.split() if r else []
    for i in ids:
        nm = xdotool("getwindowname", i)
        if nm and "fps" in nm.stdout.lower():
            return i, nm.stdout.strip()
    return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=6)
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("-o", "--out")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()

    if a.self_check:
        return self_check()

    wid, title = find_main_window()
    if not wid:
        print("[FAIL_AMBIENTE] janela do Emulicious com fps no titulo nao encontrada",
              file=sys.stderr)
        return 2
    samples = []
    t_start = time.time()
    for n in range(a.samples):
        _, t = find_main_window()
        fps, pct = parse_title(t)
        samples.append({"t": round(time.time() - t_start, 2),
                        "fps": fps, "pct": pct})
        print(f"[{n+1}/{a.samples}] {t}", flush=True)
        if n < a.samples - 1:
            time.sleep(a.interval)
    out = {"tool": "emulicious-window-title", "window": title, "samples": samples}
    out.update(verdict(samples))
    txt = json.dumps(out, indent=2)
    print(txt)
    if a.out:
        json.dump(out, open(a.out, "w"), indent=2)
        print(f"[OK] salvo em {a.out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
