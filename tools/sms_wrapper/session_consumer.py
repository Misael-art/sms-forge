#!/usr/bin/env python3
"""session_consumer.py — API comum para scripts automatizados sobre sessao privada Emulicious (§93/L057).

Todo consumidor automatizado: identifica ROM+SHA, cria UMA sessao, passa o MESMO ID a comandos,
leituras, capturas e medicoes, e encerra com close_session em finally (aguardando a limpeza).
Nao ha fallback ao desktop: faltando dependencia/isolamento, levanta SessionUnavailable.
Eixos separados: ack (ponte recebeu), portas (estado das portas emuladas, no ACK), ROM (leitura de RAM),
gameplay (veredito do consumidor). Duracao de comando = frames do VDP, nunca sleep.
"""
import hashlib, json, sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_bridge import isolated as I

U, D, L, R, B1, B2 = 1, 2, 4, 8, 16, 32          # mascaras de porta SMS (P1/P2)


class SessionUnavailable(RuntimeError):
    pass


class Session:
    def __init__(self, root):
        self.root = Path(root)
        meta = I.load(self.root)[1]
        self.id, self.rom_sha256 = meta["session_id"], meta["rom_sha256"]
        self.acks = []                                   # trilha de ACKs para o relatorio

    # -- comandos (ACK da ponte) ------------------------------------------
    def _req(self, op, *a):
        r = I.request(self.root, op, *a)
        self.acks.append({"op": op, "args": list(a), "seq": r.get("seq"), "frame": r.get("frame"),
                          "p1": r.get("p1"), "p2": r.get("p2"), "emulator_input": r.get("emulator_input")})
        return r

    def hold(self, p1=0, p2=0, frames=0):
        """Segura as portas durante exatamente `frames` frames do VDP e deixa pausado com as mascaras ativas."""
        r = self._req("input", p1, p2, 0)
        if frames:
            r = self._req("step", frames)
        return r

    def release(self):
        return self._req("input", 0, 0, 0)

    def step(self, frames):
        return self._req("step", frames)

    def sequence(self, steps):
        r = I.sequence(self.root, steps)
        self.acks.append({"op": "sequence", "steps": steps, "seq": r.get("seq")})
        return r

    def status(self):
        return self._req("status")

    # -- observacao da ROM -------------------------------------------------
    def read(self, addr, n):
        return list(self._req("read", addr, n)["ram"])

    def byte(self, addr):
        return self.read(addr, 1)[0]

    def word(self, addr):
        b = self.read(addr, 2)
        return b[0] | b[1] << 8

    def capture(self, name="frame.png"):
        return I.capture(self.root, name)


@contextmanager
def private_session(rom, **kw):
    rom = Path(rom)
    if not rom.is_file():
        raise SessionUnavailable(f"ROM ausente: {rom}")
    try:
        root = I.start(rom, **kw)
    except Exception as e:                                # sem fallback silencioso ao desktop
        raise SessionUnavailable(f"sessao privada indisponivel: {e}") from e
    s = Session(root)
    try:
        yield s
    finally:
        try:
            s.release()
        except Exception:
            pass
        I.close_session(root)


def rom_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def self_check():
    import tempfile
    try:
        with private_session(Path(tempfile.gettempdir()) / "nao_existe.sms"):
            return 1
    except SessionUnavailable:
        pass
    assert (U, D, L, R, B1, B2) == (1, 2, 4, 8, 16, 32)
    print("self-check session_consumer: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(self_check() if "--self-check" in sys.argv else 2)
