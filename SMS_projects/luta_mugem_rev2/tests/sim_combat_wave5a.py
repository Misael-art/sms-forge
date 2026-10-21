#!/usr/bin/env python3
"""Simulador de comportamento da wave-5a (M2) sobre o pacote gerado.

Reproduz frame-a-frame o loop de src/main.c (script de 12 passos de 150
frames, facing_step, advance_actor, combat_step, pusher_step) usando
EXCLUSIVAMENTE os dados em out/generated/ryu_ken_cross, e reporta os
contadores que as sondas 0xC826..0xC83A deveriam mostrar, mais diagnostico
de alcance por passo S_HIT. O numero de frames e o mesmo do contador `frames`
da ROM (passo 1 em frames%150==0, comecando de 1), portanto a janela usada na
prova deve ser passada como argumento: `python3 tests/sim_combat_wave5a.py
<probe_frame da ROM>`. Ferramenta de QA do consumidor (nao e logica de build).
Nao julga qualidade.
"""
import re, struct, sys

BASE = "out/generated/ryu_ken_cross"
VS = open(f"{BASE}/versus_scene_runtime.h").read()
FRD = open(f"{BASE}/fight_runtime_data.h").read()

S_CONTROL, S_AIR, S_HIT, S_BLOCKABLE = 1, 2, 4, 8
DIAG_FLOOR, X_MIN, X_MAX = 160, 16 * 256, 240 * 256
STEP = 150
NFRAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 1920
SENT = -32767
# script_roles de main.c por indice de estado (ST_*):
SCRIPT = [0, 1, 3, 4, 5, 6, 7, 10, 11, 8, 2, 9]
# vida/jump/gravidade/hitstop/push por lado (characters[2] lido acima):
CHAR = [{"jump_vy": 2355, "gravity": 102, "hitstop": 12, "hit_push": 5, "guard_push": 5, "life": 1000},
        {"jump_vy": 2304, "gravity": 110, "hitstop": 11, "hit_push": 5, "guard_push": 5, "life": 1000}]

anim_ids = {m.group(1): int(m.group(2))
            for m in re.finditer(r"#define (P\d_CUT_ANIM_\w+) (\d+)", VS)}

clsn_bytes = {}
for m in re.finditer(r"const unsigned char (\w+_CLSN)\[(\d+)\] = \{(.*?)\};", VS, re.S):
    clsn_bytes[m.group(1)] = bytes(int(x, 16) for x in re.findall(r"0x([0-9a-fA-F]{2})", m.group(3)))
alias = {m.group(1): m.group(2) for m in re.finditer(r"#define (\w+_CLSN) (\w+_CLSN)", VS)}
def resolve(sym):
    while sym in alias:
        sym = alias[sym]
    return clsn_bytes[sym]

def load(side):
    s = str(side)
    m = re.search(rf"static const Frame p{s}_frames_all\[\w+\] = \{{(.*?)\n\}};", VS, re.S)
    frames = []
    for dur, clsn in re.findall(r"\{\s*(\d+),\s*\d+,\s*\w+_META,\s*\w+_METAL,\s*(\w+_CLSN|0),", m.group(1)):
        frames.append({"dur": int(dur),
                       "clsn": None if clsn == "0" else resolve(clsn)})
    m = re.search(rf"static const Anim p{s}_anims\[12\] = \{{(.*?)\}};", VS, re.S)
    anims = []
    for n, ls, off in re.findall(r"\{\s*\d+,\s*(\d+),\s*(\d+),\s*p\d_frames_all \+ (\d+)\s*\}", m.group(1)):
        anims.append({"n": int(n), "loop": int(ls), "off": int(off)})
    m = re.search(rf"static const StateDef p{s}_states\[ST_N_STATES\] = \{{(.*?)\}};", FRD, re.S)
    states = []
    for anim, flags, vel, dmg in re.findall(
            r"\{\s*65535,\s*(P\d_CUT_ANIM_\w+),\s*([0-9A-Za-z_| ()]+),\s*(-?\d+),\s*(\d+)\s*\}", m.group(1)):
        f = flags.replace(" ", "")
        f = (f.replace("S_CONTROL", "1").replace("S_BLOCKABLE", "8")
              .replace("S_AIR", "2").replace("S_HIT", "4"))
        states.append({"anim": anim_ids[anim], "flags": eval(f), "vel": int(vel), "dmg": int(dmg)})
    return frames, anims, states[:12]

DATA = [load(1), load(2)]

def boxes(blob, sec):
    """int16 quads da secao: sec=0 hit (cursor 0), sec=1 hurt (apos 1a sentinela)."""
    ints = list(struct.unpack("<" + "h" * (len(blob) // 2), blob))
    k = 0
    if sec == 1:
        while ints[k] != SENT:
            k += 4
        k += 1
    out = []
    while ints[k] != SENT:
        out.append(tuple(ints[k:k + 4]))
        k += 4
    return out

def to_screen(q, face, fx, fy):
    """Mesma transformada de mugen_to_screen(): espelha x pelo facing e
    usa y do AIR negativo para cima (t = fy + y1, b = fy + y2)."""
    x1, y1, x2, y2 = q
    if not face:
        return (fx + x1, fy + y1, fx + x2, fy + y2)
    return (fx - x2, fy + y1, fx - x1, fy + y2)

def overlap(fa, sa, fb, sb, xa, xb, ya, yb, a_sec):
    ca, cb = fa["clsn"], fb["clsn"]
    if not ca or not cb:
        return False
    fya, fyb = DIAG_FLOOR - (ya >> 8), DIAG_FLOOR - (yb >> 8)
    for qa in boxes(ca, a_sec):
        al, at, ar, ab = to_screen(qa, sa, xa >> 8, fya)
        for qb in boxes(cb, 1):
            bl, bt, br, bb = to_screen(qb, sb, xb >> 8, fyb)
            if al <= br and bl <= ar and at <= bb and bt <= ab:
                return True
    return False

class Actor:
    def __init__(self, side):
        self.side, self.x, self.y, self.vy = side, (96 if side == 0 else 160) * 256, 0, 0
        self.role, self.fidx, self.tick, self.stop = 0, 0, 0, 0
        self.hit_done, self.life = 0, CHAR[side]["life"]
        self.face = side
    def frames(self):
        fr, an, st = DATA[self.side]
        a = an[st[self.role]["anim"]]
        return fr[a["off"] + self.fidx], a, st[self.role]

def set_role(f, role):
    f.role, f.fidx, f.tick, f.hit_done = role, 0, 0, 0
    fr, an, st = DATA[f.side]
    if st[role]["flags"] & S_AIR and f.y == 0:
        f.vy = CHAR[f.side]["jump_vy"]

def advance(f):
    fr, an, st = DATA[f.side]
    frame, a, s = f.frames()
    if f.stop:
        f.stop -= 1
        ev["hitstop"] += 1
        return frame, True
    vel = s["vel"]
    if vel and f.y == 0:
        nx = f.x + (-vel if f.face else vel)
        f.x = max(X_MIN, min(X_MAX, nx))
    if f.y or f.vy:
        ny = f.y + f.vy
        f.vy -= CHAR[f.side]["gravity"]
        if ny <= 0:
            ny, f.vy = 0, 0
        f.y = ny
    if frame["dur"] != 255:
        f.tick += 1
        if f.tick >= frame["dur"]:
            f.tick = 0
            if f.fidx + 1 < a["n"]:
                f.fidx += 1
            elif a["loop"] != 255:
                f.fidx = a["loop"]
    return f.frames()[0], False

F = [Actor(0), Actor(1)]
F[1].face = 1                     # boot da ROM: face 0 / face 1, ambos IDLE
ev = dict(hits=0, guards=0, dmg=[0, 0], checks=0, hitstop=0, pusher=0, ko=0, flips=0)
punchlog = {}
for fr in range(1, NFRAMES + 1):
    if fr % STEP == 0:
        step = fr // STEP
        set_role(F[0], SCRIPT[step % 12])
        set_role(F[1], SCRIPT[(step + 1) % 12])
    # facing_step (mesma regra da ROM): so vira no chao, empate de x nao vira
    for s in (0, 1):
        if F[s].y == 0 and F[1 - s].x != F[s].x:
            want = 1 if F[1 - s].x < F[s].x else 0
            if want != F[s].face:
                F[s].face = want
                ev["flips"] += 1
    fn = [advance(F[0])[0], advance(F[1])[0]]
    # combat_step
    for a in (0, 1):
        d = 1 - a
        frame, _, s = F[a].frames()
        if F[a].hit_done or not (s["flags"] & S_HIT) or F[d].life == 0:
            continue
        ev["checks"] += 1
        key = fr // STEP
        if key not in punchlog:
            punchlog[key] = dict(min_gap=None, null_c=[0, 0])
        hb = boxes(fn[a]["clsn"], 0) if fn[a]["clsn"] else []
        hu = boxes(fn[d]["clsn"], 1) if fn[d]["clsn"] else []
        if not fn[a]["clsn"] or not fn[d]["clsn"]:
            punchlog[key]["null_c"][a] += 1
        else:
            gap = None
            for qa in hb:
                al, _, ar, _ = to_screen(qa, F[a].face, F[a].x >> 8, DIAG_FLOOR)
                for qb in hu:
                    bl, _, br, _ = to_screen(qb, F[d].face, F[d].x >> 8, DIAG_FLOOR)
                    g = max(0, bl - ar) if ar <= br else max(0, al - br)
                    gap = g if gap is None else min(gap, g)
            if gap is not None:
                mn = punchlog[key]["min_gap"]
                punchlog[key]["min_gap"] = gap if mn is None else min(mn, gap)
        if overlap(fn[a], F[a].face, fn[d], F[d].face, F[a].x, F[d].x, F[a].y, F[d].y, 0):
            F[a].hit_done = 1
            hs = CHAR[a]["hitstop"]
            if hs:
                F[0].stop = F[1].stop = hs
            if DATA[d][2][F[d].role]["flags"] & S_BLOCKABLE:
                ev["guards"] += 1
                push = CHAR[a]["guard_push"]
            else:
                ev["hits"] += 1
                taken = min(s["dmg"], F[d].life)
                F[d].life -= taken
                ev["dmg"][d] += taken
                if F[d].life == 0:
                    ev["ko"] += 1
                    set_role(F[d], 9)
                push = CHAR[a]["hit_push"]
            # afastar o defensor do atacante pela ordem de x (cross-up), nao por lado
            sign = 1 if F[d].x >= F[a].x else -1
            F[d].x = max(X_MIN, min(X_MAX, F[d].x + sign * (push << 8)))
    # pusher_step
    if F[0].y == 0 and F[1].y == 0 and \
       overlap(fn[0], F[0].face, fn[1], F[1].face, F[0].x, F[1].x, 0, 0, 1):
        ev["pusher"] += 1
        x0, x1 = F[0].x, F[1].x
        if x0 <= x1:
            x0 -= 256; x1 += 256
        else:
            x0 += 256; x1 -= 256
        F[0].x, F[1].x = max(X_MIN, min(X_MAX, x0)), max(X_MIN, min(X_MAX, x1))

print(f"frames={NFRAMES} checks={ev['checks']} hits={ev['hits']} guards={ev['guards']} "
      f"ko={ev['ko']} hitstop_frames={ev['hitstop']} pusher_frames={ev['pusher']} "
      f"face_flips={ev['flips']} "
      f"dmg_p1={ev['dmg'][0]} dmg_p2={ev['dmg'][1]} life={F[0].life},{F[1].life} "
      f"x={F[0].x >> 8},{F[1].x >> 8} face={F[0].face},{F[1].face}")
for k, v in sorted(punchlog.items()):
    print(f"step {k}: min_gap(px)={v['min_gap']} frames_sem_clsn={v['null_c']}")
