"""Modelo de filas de patterns; nao mede tempo de VBlank nem apresenta sprites.

O runtime autoritativo continua NA ROM; este modulo e' o modelo de fila que
permite pre-validar tamanho de chunk, residencia e pico de pool ANTES de
tocar o binario. Sem numeros inventados: toda constante abaixo tem fonte.

Fatos com fonte:
- Par TALL = 2 tiles = 64 B; pool de 128 pares = 8192 B
  (main.c:42 ``#define POOL_PAIRS 128u`` com o comentario "8192 B / 64 B por
  par TALL"; o stream endereca ``(base_pair + loaded_pairs) * 64``,
  main.c:340-358).
- O default conserva o modelo historico v033: um par por turno alternado e
  descarte/eviccao do adversario. Nao representa o perfil atual do rev2.
- O perfil explicito ``rev2_b2_cancel_v1`` modela oito pares por lado, ambos
  servidos no tick, sem desalojar o oponente, e cancela pedido em voo quando
  a pose desejada volta a ser a residente. A ROM precisa de prova propria.
- Alocador first-fit por extensoes: candidatos {0} U {fim de cada slot vivo}
  (main.c:276-310).

Uso:
    python -m mugen2sms.runtime.commit_budget --events eventos.json
    python -m mugen2sms.runtime.commit_budget --self-check

``eventos.json``: {"policy": {...}, "preloads": [{"side","pose","pairs"}],
"events": [{"frame","side","pose","pairs"}]}

Exit: 0 modelo rodou sem erro de contrato | 1 violacao declarada | 3 uso.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from math import ceil
from pathlib import Path

PAIR_BYTES = 64         # 2 tiles TALL x 32 B (main.c:42)
POOL_PAIRS = 128        # main.c:42
SIDES = 2


@dataclass(frozen=True)
class Policy:
    pairs_per_upload: int = 1      # stream_pending nao-boot sobe 1 par
    alternate_sides: bool = True   # historico v033: stream_pending(frames & 1)
    preserve_opponent: bool = False
    cancel_on_resident: bool = False

    @classmethod
    def rev2_b2_cancel_v1(cls) -> "Policy":
        return cls(pairs_per_upload=8, alternate_sides=False,
                   preserve_opponent=True, cancel_on_resident=True)

    def upload_sides(self, frame: int) -> list[int]:
        if self.alternate_sides:
            return [frame & 1]
        return list(range(SIDES))


@dataclass
class Slot:
    pose: int | None = None
    base_pair: int = 0
    n_pairs: int = 0
    loaded_pairs: int = 0

    @property
    def live(self) -> bool:
        return self.pose is not None

    @property
    def resident(self) -> bool:
        return self.live and self.loaded_pairs >= self.n_pairs


@dataclass
class SimResult:
    totals: dict
    timeline: list          # (frame, side, pairs_subidos)
    completions: list       # (frame, side, pose) — promocao pending->current


def check_pose_fit(n_pairs: int, pool_pairs: int = POOL_PAIRS) -> tuple[list, list]:
    """(erros, avisos) de encaixe de UMA pose no pool."""
    errors, warnings = [], []
    if n_pairs <= 0:
        errors.append("pose com %d pares" % n_pairs)
    if n_pairs > pool_pairs:
        errors.append(
            "pose de %d pares > pool de %d (nunca fica residente; o memo de "
            "falha so gera stall)" % (n_pairs, pool_pairs))
    elif n_pairs * 2 > pool_pairs:
        warnings.append(
            "pose de %d pares nao coexiste com uma segunda do mesmo tamanho "
            "(%d*2 > %d): a consequencia depende da politica de cache"
            % (n_pairs, n_pairs, pool_pairs))
    return errors, warnings


def resident_frames(n_pairs: int, policy: Policy = Policy()) -> int:
    """Turnos de upload ate a pose ficar residente (1 par/turno por padrao).

    Com ``alternate_sides`` cada lado tem um turno a cada 2 frames; o numero
    devolvido e' o pior caso a partir do pedido (frame do pedido no inicio do
    turno do lado). Nao substitui a timeline: use ``simulate`` como oraculo.
    """
    turns = ceil(n_pairs / policy.pairs_per_upload)
    return turns * 2 if policy.alternate_sides else turns


def parse_policy(raw: dict) -> tuple[Policy, str]:
    if not isinstance(raw, dict):
        raise ValueError("policy deve ser um objeto")
    allowed = {"profile", "pairs_per_upload", "alternate_sides",
               "preserve_opponent", "cancel_on_resident"}
    if set(raw) - allowed:
        raise ValueError("campos de policy desconhecidos")
    profile = raw.get("profile")
    if profile == "rev2_b2_cancel_v1":
        if set(raw) != {"profile"}:
            raise ValueError("perfil nomeado nao aceita overrides silenciosos")
        return Policy.rev2_b2_cancel_v1(), profile
    if profile is not None:
        raise ValueError("perfil de politica desconhecido")
    pairs = raw.get("pairs_per_upload", 1)
    if isinstance(pairs, bool) or not isinstance(pairs, int) or pairs < 1 or pairs > POOL_PAIRS:
        raise ValueError("pairs_per_upload deve ser inteiro entre 1 e 128")
    bools = {name: raw.get(name, default) for name, default in
             (("alternate_sides", True), ("preserve_opponent", False),
              ("cancel_on_resident", False))}
    if any(not isinstance(value, bool) for value in bools.values()):
        raise ValueError("opcoes booleanas da politica devem ser true/false")
    policy = Policy(pairs_per_upload=pairs, **bools)
    return policy, "legacy_v033" if policy == Policy() else "custom_unbound"


class Simulator:
    def __init__(self, policy: Policy | None = None):
        self.policy = policy or Policy()
        self.cur = [Slot(), Slot()]
        self.pend = [Slot(), Slot()]
        self.pool_epoch = 0
        self.fail_epoch: list[int | None] = [None, None]
        self.fail_size: list[int | None] = [None, None]
        self.stats = {
            "requests": 0, "cache_hits": 0, "uploaded_pairs": 0,
            "boot_pairs": 0, "stalls": 0, "memo_stalls": 0,
            "evictions": 0, "dropped_pending": 0, "alloc_fail": 0,
            "superseded_pending": 0,
        }
        self.completions: list = []
        self.timeline: list = []
        self.peak_used = 0              # pico transitorio de pares vivos

    # -- espelho de main.c -------------------------------------------------
    def _slots(self) -> list[Slot]:
        return [self.cur[0], self.cur[1], self.pend[0], self.pend[1]]

    def used_pairs(self) -> int:
        return sum(s.n_pairs for s in self._slots() if s.live)

    def _note_peak(self) -> None:
        """Pico apos uma mutacao: o estado final NAO e' o pico.

        A alocacao transitoria (pend vivos) pode encher o pool e depois ceder
        por completude/eviccao; medir so' o estado final subestima o pico que o
        hardware de fato hospeda (§49/L061: folga nao medida e' timidez).
        """
        self.peak_used = max(self.peak_used, self.used_pairs())

    def _invalidate(self, s: Slot) -> None:
        if s.live:
            self.pool_epoch += 1
            s.n_pairs = 0
        s.pose = None
        s.loaded_pairs = 0

    def _alloc(self, n: int) -> int | None:
        slots = self._slots()
        candidates = [0] + [s.base_pair + s.n_pairs for s in slots if s.live]
        best = None
        for c in sorted(set(candidates)):
            if c + n > POOL_PAIRS:
                continue
            if any(s.live and c < s.base_pair + s.n_pairs
                   and s.base_pair < c + n for s in slots):
                continue
            best = c
            break
        return best

    def _place(self, side: int, pose: int, base: int, n: int) -> None:
        self.pend[side] = Slot(pose=pose, base_pair=base, n_pairs=n,
                               loaded_pairs=0)

    def request(self, side: int, pose: int, n_pairs: int) -> None:
        self._request(side, pose, n_pairs)
        self._note_peak()

    def _request(self, side: int, pose: int, n_pairs: int) -> None:
        self.stats["requests"] += 1
        if not (0 < n_pairs <= POOL_PAIRS):
            raise ValueError("n_pairs %d fora de 1..%d" % (n_pairs, POOL_PAIRS))
        if self.cur[side].pose == pose:
            if self.policy.cancel_on_resident and self.pend[side].live:
                self._invalidate(self.pend[side])
                self.stats["superseded_pending"] += 1
            self.stats["cache_hits"] += 1
            return
        if self.pend[side].pose == pose:
            self.stats["cache_hits"] += 1
            return
        if (self.fail_epoch[side] == self.pool_epoch
                and self.fail_size[side] == n_pairs):
            self.stats["stalls"] += 1
            self.stats["memo_stalls"] += 1
            return
        if self.pend[side].live:
            self.stats["superseded_pending"] += 1
        self._invalidate(self.pend[side])
        base = self._alloc(n_pairs)
        if base is not None:
            self._place(side, pose, base, n_pairs)
            return
        self.stats["alloc_fail"] += 1
        if self.policy.preserve_opponent:
            self.fail_epoch[side] = self.pool_epoch
            self.fail_size[side] = n_pairs
            self.stats["stalls"] += 1
            return
        if self.pend[side ^ 1].live:
            self._invalidate(self.pend[side ^ 1])
            self.stats["dropped_pending"] += 1
            base = self._alloc(n_pairs)
            if base is not None:
                self._place(side, pose, base, n_pairs)
                return
        if self.cur[side ^ 1].live:
            self._invalidate(self.cur[side ^ 1])
            self.stats["evictions"] += 1
            base = self._alloc(n_pairs)
            if base is not None:
                self._place(side, pose, base, n_pairs)
                return
        self.fail_epoch[side] = self.pool_epoch
        self.fail_size[side] = n_pairs
        self.stats["stalls"] += 1

    def stream(self, frame: int) -> int:
        moved = 0
        for side in self.policy.upload_sides(frame):
            slot = self.pend[side]
            budget = self.policy.pairs_per_upload
            while (budget and slot.live
                   and slot.loaded_pairs < slot.n_pairs):
                slot.loaded_pairs += 1
                self.stats["uploaded_pairs"] += 1
                budget -= 1
                moved += 1
            if slot.live and slot.loaded_pairs >= slot.n_pairs:
                self._invalidate(self.cur[side])
                self.cur[side] = slot
                self.pend[side] = Slot()
                self.completions.append((frame, side, slot.pose))
        if moved:
            self.timeline.append((frame, moved))
        self._note_peak()
        return moved

    def boot_preload(self, side: int, pose: int, n_pairs: int) -> None:
        """Boot com display OFF: request + upload_all, promovido direto.

        Equivale a ``request_pose`` seguido de ``stream_pending(side, 1)``
        (main.c:1118/1127) executados fora do laco: a pose termina em
        ``current`` sem passar pela alternancia de turnos.
        """
        if not (0 < n_pairs <= POOL_PAIRS):
            raise ValueError("n_pairs %d fora de 1..%d" % (n_pairs, POOL_PAIRS))
        if self.cur[side].pose == pose or self.pend[side].pose == pose:
            self.stats["cache_hits"] += 1
            return
        self._invalidate(self.pend[side])
        base = self._alloc(n_pairs)
        if base is None:
            raise ValueError(
                "preload nao cabe no pool: lado %d pose %d n=%d (pool %d)"
                % (side, pose, n_pairs, POOL_PAIRS))
        self.cur[side] = Slot(pose=pose, base_pair=base, n_pairs=n_pairs,
                              loaded_pairs=n_pairs)
        self.stats["uploaded_pairs"] += n_pairs
        self.stats["boot_pairs"] += n_pairs
        self._note_peak()


def simulate(events: list[dict], policy: Policy | None = None,
             preloads: list[dict] | None = None) -> SimResult:
    """Roda a timeline: em cada frame, requests primeiro, stream depois.

    A simulacao NAO para no ultimo evento: continua ate' o stream quiescer
    (nenhum pending vivo), senao a conclusao de uma pose pedida no fim seria
    truncada e o relatorio mentiria por omissao. O limite duro existe so' para
    policy degenerada (``pairs_per_upload`` < 1) — vira ValueError de contrato.
    """
    sim = Simulator(policy)
    for item in preloads or []:
        sim.boot_preload(int(item["side"]), int(item["pose"]),
                         int(item["pairs"]))
    ordered = sorted(enumerate(events), key=lambda p: (p[1]["frame"], p[0]))
    last_frame = ordered[-1][1]["frame"] if ordered else -1
    by_frame: dict[int, list[dict]] = {}
    for _, ev in ordered:
        f = int(ev["frame"])
        if f < 0:
            raise ValueError("frame negativo em events")
        by_frame.setdefault(f, []).append(ev)
    hard_stop = last_frame + 2 * POOL_PAIRS + 4
    frame = 0
    while frame <= last_frame or any(s.live for s in sim.pend):
        if frame > hard_stop:
            raise ValueError(
                "stream nao quiesce apos %d frames (pairs_per_upload=%d)"
                % (hard_stop, sim.policy.pairs_per_upload))
        for ev in by_frame.get(frame, []):
            sim.request(int(ev["side"]), int(ev["pose"]), int(ev["pairs"]))
        sim.stream(frame)
        frame += 1
    totals = dict(sim.stats)
    totals["max_used_pairs"] = sim.peak_used
    return SimResult(totals=totals, timeline=sim.timeline,
                     completions=sim.completions)


def plan_problems(payload: dict) -> list[str]:
    """Erros de contrato do pedido: poses que nao cabem / nao coexistem."""
    problems: list[str] = []
    items = list(payload.get("preloads", [])) + list(payload.get("events", []))
    for item in items:
        errors, warnings = check_pose_fit(int(item["pairs"]))
        for e in errors:
            problems.append("pose %s: %s" % (item.get("pose"), e))
        for w in warnings:
            problems.append("pose %s (aviso): %s" % (item.get("pose"), w))
    return problems


def _check(ok: bool, cond, detail) -> bool:
    """Acumula um caso sem virar tupla (``ok &= a, b`` e' TypeError).

    Mantem o valor observado no diagnostico quando o caso falha.
    """
    if not cond:
        print("  [XX] caso falhou, obtido: %r" % (detail,))
    return ok and bool(cond)


def self_check() -> int:
    ok = True

    # 1. Residencia alternada: pedido no frame 0, 1 par a cada 2 frames.
    r = simulate([{"frame": 0, "side": 0, "pose": 1, "pairs": 3}])
    ok = _check(ok, r.completions == [(4, 0, 1)], r.completions)
    ok = _check(ok, r.timeline == [(0, 1), (2, 1), (4, 1)], r.timeline)
    ok &= r.totals["stalls"] == 0 and r.totals["evictions"] == 0
    ok &= resident_frames(3) == 6          # pior caso: 3 turnos x 2 frames

    # 2. Sem espaco: evicta o current do adversario e o plano segue.
    r = simulate(
        [{"frame": 0, "side": 0, "pose": 12, "pairs": 16}],
        preloads=[{"side": 0, "pose": 10, "pairs": 60},
                  {"side": 1, "pose": 11, "pairs": 60}])
    ok = _check(ok, r.totals["evictions"] == 1, r.totals)
    ok &= r.totals["stalls"] == 0 and r.totals["dropped_pending"] == 0

    # 3. Sem espaco algum: stall e o memo de (epoch, size) evita retentar.
    r = simulate(
        [{"frame": 0, "side": 1, "pose": 21, "pairs": 1},
         {"frame": 1, "side": 1, "pose": 21, "pairs": 1}],
        preloads=[{"side": 1, "pose": 20, "pairs": 128}])
    ok = _check(ok, r.totals["stalls"] == 2 and r.totals["memo_stalls"] == 1,
                r.totals)
    ok &= r.totals["evictions"] == 0 and r.totals["alloc_fail"] == 1

    # 4. Descartar o pending do adversario libera espaco antes da eviccao.
    r = simulate(
        [{"frame": 0, "side": 1, "pose": 50, "pairs": 16},
         {"frame": 2, "side": 0, "pose": 33, "pairs": 48}],
        preloads=[{"side": 0, "pose": 30, "pairs": 40},
                  {"side": 1, "pose": 31, "pairs": 40}])
    ok = _check(ok, r.totals["dropped_pending"] == 1, r.totals)
    ok &= r.totals["evictions"] == 0 and r.totals["stalls"] == 0
    # A pose 50 foi descartada ainda pendente: nunca completa.
    ok = _check(ok, all(c[2] != 50 for c in r.completions), r.completions)

    # 5. Cache hit nao re-pede: as DUAS requisicoes batem no current
    #    pre-carregado (nenhuma vira pend nem sobe nada).
    r = simulate(
        [{"frame": 0, "side": 0, "pose": 10, "pairs": 60},
         {"frame": 5, "side": 0, "pose": 10, "pairs": 60}],
        preloads=[{"side": 0, "pose": 10, "pairs": 60}])
    ok = _check(ok, r.totals["cache_hits"] == 2
                and r.totals["requests"] == 2, r.totals)
    ok = _check(ok, r.completions == [] and r.totals["alloc_fail"] == 0,
                r.completions)

    # 6. Enc aixe de pose.
    ok &= check_pose_fit(64)[0] == [] and check_pose_fit(64)[1] == []
    ok &= check_pose_fit(65)[1] != [] and check_pose_fit(65)[0] == []
    ok &= check_pose_fit(129)[0] != []

    # 7. Boot acima do pool nao passa.
    try:
        simulate([], preloads=[{"side": 0, "pose": 1, "pairs": 64},
                               {"side": 1, "pose": 2, "pairs": 65}])
        ok = False
    except ValueError:
        pass

    # 8. Timeline de par subido nao mente: 60 B sao 1 par por frame alternado.
    r = simulate([{"frame": 0, "side": 1, "pose": 7, "pairs": 2}])
    ok = _check(ok, [t[1] for t in r.timeline] == [1, 1], r.timeline)
    ok &= r.timeline[0][0] == 1          # lado 1 so' e' servido em frames impares
    ok &= r.totals["uploaded_pairs"] == 2

    # 9. Pico transitorio medido no momento certo: 60+60 pre-carregados +
    #    pedido de 8 pares = 128/128 momentaneo; depois cede (completude em
    #    f14 e novo pend de 16 no buraco de 0x0) e o estado final NAO e' o
    #    pico. Simulacao de ponta a ponta + verificacao direta do pico.
    r = simulate(
        [{"frame": 0, "side": 0, "pose": 12, "pairs": 8},
         {"frame": 20, "side": 1, "pose": 13, "pairs": 16}],
        preloads=[{"side": 0, "pose": 10, "pairs": 60},
                  {"side": 1, "pose": 11, "pairs": 60}])
    ok = _check(ok, r.totals["max_used_pairs"] == 128, r.totals)
    # 8 pares no lado 0 a partir de f0 completam em f14; os 16 do lado 1
    # pedidos em f20 (base 0, buraco deixado pelo primeiro) completam em f51.
    ok = _check(ok, r.completions == [(14, 0, 12), (51, 1, 13)], r.completions)

    sim = Simulator()
    sim.boot_preload(0, 10, 60)
    sim.boot_preload(1, 11, 60)
    sim.request(0, 12, 8)
    ok &= sim.used_pairs() == 128 and sim.peak_used == 128
    for f in range(0, 15):
        sim.stream(f)
    sim.request(1, 13, 16)
    ok &= sim.used_pairs() == 84 and sim.peak_used == 128

    # Atual: voltar a current cancela somente o proprio upload; overflow nao
    # sacrifica a imagem do adversario. E modelo, nao leitura de ROM/VDP.
    sim = Simulator(Policy.rev2_b2_cancel_v1())
    sim.boot_preload(0, 1, 40)
    sim.boot_preload(1, 2, 40)
    sim.request(0, 3, 16)
    sim.stream(0)
    sim.request(0, 1, 40)
    ok &= not sim.pend[0].live and sim.cur[0].pose == 1
    ok &= sim.cur[1].pose == 2 and sim.stats["superseded_pending"] == 1
    sim.request(0, 4, 64)
    ok &= sim.cur[1].pose == 2 and sim.stats["evictions"] == 0
    ok &= sim.stats["alloc_fail"] == 1

    print("self-check commit_budget:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--events", type=Path, default=None)
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args(argv)
    if args.self_check:
        return self_check()
    if args.events is None:
        ap.error("informe --events eventos.json ou use --self-check")
    payload = json.loads(args.events.read_text(encoding="utf-8"))
    problems = plan_problems(payload)
    policy = Policy()
    profile = "invalid"
    try:
        policy, profile = parse_policy(payload.get("policy", {}))
        result = simulate(payload.get("events", []), policy,
                          payload.get("preloads", []))
    except ValueError as exc:
        # Contrato violado nao derruba o relatorio com traceback: vira
        # problema declarado no schema (exit 1), como os de plan_problems.
        problems.append("simulacao: %s" % exc)
        empty = Simulator(policy)
        totals = dict(empty.stats)
        totals["max_used_pairs"] = empty.peak_used
        result = SimResult(totals=totals, timeline=[], completions=[])
    report = {
        "schema": "mugen2sms.commit-budget/v1",
        "ok": not problems,
        "scope": "queue_model_only_not_rom_or_vblank_timing",
        "policy": {"profile": profile, "pairs_per_upload": policy.pairs_per_upload,
                   "alternate_sides": policy.alternate_sides,
                   "preserve_opponent": policy.preserve_opponent,
                   "cancel_on_resident": policy.cancel_on_resident},
        "problems": problems,
        "totals": result.totals,
        "completions": result.completions,
        "timeline": result.timeline,
    }
    if args.json:
        args.json.write_text(json.dumps(report, indent=1) + "\n",
                             encoding="utf-8")
    for p in problems:
        print("[PROBLEMA] " + p)
    t = result.totals
    print("[commit-budget] requests=%d hits=%d pares_subidos=%d "
          "(boot %d) eviccoes=%d descartes_pending=%d stalls=%d (memo %d) "
          "pico=%d/%d"
          % (t["requests"], t["cache_hits"], t["uploaded_pairs"],
             t["boot_pairs"], t["evictions"], t["dropped_pending"],
             t["stalls"], t["memo_stalls"], t["max_used_pairs"], POOL_PAIRS))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
