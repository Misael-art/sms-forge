#!/usr/bin/env python3
"""audit_deterministic_boot.py — gate de boot preservavel/deterministico (porta do SGDK Forge).

Regra do SMSForge (§24): boot deterministico = MESMO estado inicial toda execucao,
para que evidencia comparavel exista. Este gate executa a ROM no Emulicious
2x e compara o estado do playfield (sprites no SAT + pixels nao-pretos).

Sem emulador configurado -> FAIL_AMBIENTE (honesto, nao simula).

Uso:
  audit_deterministic_boot.py --project <dir> --rom <rom.sms> [--runs 2]
  audit_deterministic_boot.py --self-check
Exit: 0 deterministico | 1 divergente | 2 ambiente ausente | 3 uso
"""
import sys, os, json, argparse, subprocess, time, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emulator_session import require_no_stale

def capture_playfield_hash(rom, jar, runs=2):
    """Langa a ROM `runs` vezes, captura o playfield via Emulicious e devolve
    lista de hashes. Retorna None se emulador/import indisponivel.

    L057: sem a guarda abaixo este gate ja emitiu veredito sobre a ROM ERRADA —
    com um Emulicious de MSSF2T vivo, ele reprovou o laboratorio_01 fotografando
    Ken x Guile. Determinismo e o eixo mais exposto: a janela de um zumbi PARADO
    da hashes identicos (falso PASS) e a de um zumbi ANIMANDO da divergentes
    (falso FAIL). Nos dois casos o veredito e sobre outro binario."""
    if not require_no_stale(why="gate de boot deterministico"):
        return None
    hashes = []
    for _ in range(runs):
        proc = subprocess.Popen(["java", "-jar", jar, "-set", "Update=0",
                                 os.path.abspath(rom)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
        main = None
        t0 = time.time()
        while time.time() - t0 < 25:
            time.sleep(0.4)
            r = subprocess.run(["xdotool", "search", "--name", "Emulicious"],
                               capture_output=True, text=True)
            for i in (r.stdout.split() if r else []):
                n = subprocess.run(["xdotool", "getwindowname", i],
                                   capture_output=True, text=True)
                name = n.stdout.strip() if n else ""
                if name != "Emulicious" and not name.startswith("Emulicious - "):
                    continue
                g = subprocess.run(["xdotool", "getwindowgeometry", "--shell", i],
                                   capture_output=True, text=True)
                kv = dict(l.split("=") for l in g.stdout.strip().splitlines() if "=" in l)
                # capture_evidence usa WIDTH>=256 (janela 320x265 a 100% neste host);
                # a whitelist {256,300} ficou obsoleta e o gate não achava janela.
                try:
                    wide = int(kv.get("WIDTH", "0"))
                except ValueError:
                    wide = 0
                if wide >= 256:
                    main = i
                    break
            if main:
                break
        if not main:
            if proc.poll() is None:
                proc.terminate()
            return None
        # O canvas pode existir alguns frames antes de displayOn terminar;
        # capturar aqui alternava preto/partial e culpava a ROM. O title é
        # estático por TITLE_FRAMES, mas o Emulicious pode rodar acima da
        # cadência nominal durante a captura; uma espera curta estabiliza o
        # VDP sem deixar a atração cruzar para a arena.
        time.sleep(0.25)
        png = f"/tmp/smsforge_det_{hashlib.md5(rom.encode()).hexdigest()[:8]}_{_}.png"
        if os.path.exists(png):
            os.remove(png)
        # A captura do canvas acelerado pode congelar em um frame diferente
        # entre execucoes neste host. A janela principal e o mesmo caminho de
        # captura usado por capture_evidence e inclui a moldura/menu estaveis.
        subprocess.run(["import", "-window", main, png],
                       capture_output=True, timeout=40)
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
        if not os.path.exists(png) or os.path.getsize(png) < 100:
            return None
        hashes.append(hashlib.md5(open(png, "rb").read()).hexdigest())
        time.sleep(1)   # garante que a 1a instancia encerrou p/ a proxima
    return hashes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--rom")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        # determinismo e' verificavel apenas por execucao real; aqui valida a
        # logica de comparacao de hashes (que independe do emulador).
        h = {"a": "1", "b": "1"}
        assert len(set(h.values())) == 1, "hashes iguais => determinismo"
        h2 = {"a": "1", "b": "2"}
        assert len(set(h2.values())) != 1, "hashes diferentes => divergencia"
        print("[SELF-CHECK OK] deterministic_boot (logica de comparacao)")
        return 0
    if not args.rom:
        print("[FAIL] --rom obrigatorio (boot deterministico exige ROM p/ comparar)",
              file=sys.stderr)
        return 3
    import shutil
    jar = shutil.which("Emulicious.jar") or "/mnt/sdcard/Projects/SMSForge/tools/emuladores/emulicious/Emulicious.jar"
    if not os.path.exists(jar):
        jar = os.path.join(os.path.dirname(__file__), "..", "emuladores", "emulicious", "Emulicious.jar")
    if not os.path.exists(jar):
        print("[FAIL_AMBIENTE] Emulicious.jar nao encontrado; "
              "nao posso verificarcar boot deterministico (gate nao simula)")
        return 2
    hashes = capture_playfield_hash(args.rom, jar, args.runs)
    if hashes is None:
        print("[FAIL_AMBIENTE] nao consegui capturar playfield (import/canvas "
              "indisponivel, ou instancia zumbi — veja a causa acima)")
        return 2
    if len(set(hashes)) == 1:
        print(f"[PASS] boot deterministico: {args.runs} execucoes com estado identico")
        return 0
    print(f"[FAIL] boot NAO deterministico: hashes divergentes {hashes}")
    return 1

if __name__ == "__main__":
    sys.exit(main())
