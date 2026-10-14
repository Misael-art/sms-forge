#!/usr/bin/env python3
"""emulicious_dap.py — cliente DAP do servidor `-remotedebug` do Emulicious.

BIBLIOTECA (isenta do sweep do validate_measurement_tools, como png_io):
quem MEDE e decide e o measure_runtime_probe.py.

FATOS PAGOS contra Emulicious.jar 2026-03-27, sessao real de 2026-09-04
(L035, §23 — nao "melhore" nenhum deles sem re-pagar contra o emulador):

  1. O protocolo da porta e DAP com framing Content-Length. initialize,
     attach, threads, continue, pause e evaluate respondem.
  2. attach pausa na entry (evento stopped, reason=entry). NAO existe
     configurationDone: envia-lo mata a thread do adaptador.
  3. LEITURA de memoria e pelo avaliador de expressoes (Expressions.txt do
     emulador): `@0xC7F0` le byte; `word.ram@@0xC7F0` le word little-endian;
     o resultado vem como "EXPR = $HEX". Um numero solto (`0xC7F0`) avalia a
     ele mesmo — foi isso que a L010 registrou como "$0 para qualquer
     endereco" e condenou o canal inteiro por sintaxe errada.
  4. UM pedido nao-suportado MATA a thread do adaptador ("Unhandled request"
     no log do emulador) e todo pedido seguinte pende sem resposta. A
     whitelist abaixo e FECHADA por isso, e toda espera tem timeout.
  5. Este build NAO TEM rota de escrita: supportsReadMemoryRequest,
     supportsSetVariable e supportsSetExpression sao false, e `=` no
     evaluate e comparacao (readback intocado provou). Input por memoria e
     impossivel neste build; input segue por teclado com eco em probe_keys.
  6. stackTrace/scope expoem registradores, PSG, VDP e a variavel "Input" —
     leitura util, tambem apenas de observacao.
  7. Sessao estabelecida ANTES do boot da ROM fica stale: initialize/attach
     respondem, mas o evaluate pende para sempre. Padrao vivo: conectar com
     a ROM ja rodando, um ciclo continue -> pause, e um canario @addr como
     teste — sem resposta, fechar e reconectar (reconectar e seguro: o
     attach novo pausa e o continue retoma). E quem conduz a sessao que
     ordena os passos; start_session() so cobre initialize+attach.
"""
import json
import socket
import time

PORT = 4901

# Fato 4: fechado. Qualquer pedido fora desta lista mata a sessao.
_WHITELIST = ("initialize", "attach", "threads", "continue", "pause",
              "evaluate")


def wait_port(port=PORT, timeout_s=60.0, host="127.0.0.1"):
    """Bloqueia ate o servidor aceitar conexao. None se estourar."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            return EmuliciousDap(host=host, port=port)
        except OSError:
            time.sleep(0.5)
    return None


def parse_eval_value(result):
    """"$EXPR = $29A" -> 666 | "$EXPR = $0" -> 0 | erro -> None. PURA.

    $0 e valor legitimo (probe_keys=0, hp=0) — o erro da L010 foi tomar o
    $0 de uma expressao mal formada por resposta universal. Aqui o contrato
    e: so ha numero quando o avaliador devolveu "= $hex" no fim; qualquer
    outra coisa ("Unknown variable...") e None e o chamador reporta o texto
    bruto que evaluate() devolveu.
    """
    if not isinstance(result, str) or "=" not in result:
        return None
    raw = result.rsplit("=", 1)[1].strip()
    if raw.startswith("$"):
        raw = raw[1:]
        try:
            return int(raw, 16)
        except ValueError:
            return None
    try:
        return int(raw, 10)
    except ValueError:
        return None


def fps_from_window(delta_frames, running_s):
    """fps de uma janela de execucao. PURA. None se janela invalida."""
    if running_s is None or running_s <= 0 or delta_frames is None \
            or delta_frames < 0:
        return None
    return round(delta_frames / running_s, 2)


def fps_constant(fps_list, min_fps=50.0, max_fps=60.0, spread=2.0):
    """(constante?, spread medido). PURA.

    Duas janelas na faixa 50..60 e concordantes: eixo fps_CONSTANTE, nao
    fps medio (§36). Um único valor repetido em todas as janelas vale.
    """
    import math
    vals = fps_list
    if (not isinstance(vals, list) or len(vals) < 2 or
        any(type(f) not in (int, float) or not math.isfinite(f) for f in vals)):
        return False, None
    sp = round(max(vals) - min(vals), 2)
    ok = all(min_fps <= f <= max_fps for f in vals) and sp <= spread
    return ok, sp


def magic_ok(header_bytes, magic=b"SMRT", schema=1):
    """Cabecalho do probe autentica? PURA. header_bytes = lista de ints."""
    if header_bytes is None or len(header_bytes) < len(magic) + 1:
        return False
    return (tuple(header_bytes[:len(magic)]) == tuple(magic)
            and header_bytes[len(magic)] == schema)


class EmuliciousDap:
    """Sessao DAP de requests somente da whitelist (fato 4)."""

    def __init__(self, host="127.0.0.1", port=PORT, timeout=6.0):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.buf = b""
        self.seq = 0
        self.last_raw = None

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass

    def _read_frames(self):
        self.sock.settimeout(0.4)
        try:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("servidor fechou a conexao")
            self.buf += chunk
        except socket.timeout:
            pass

    def _parse(self):
        out = []
        while True:
            i = self.buf.find(b"\r\n\r\n")
            if i < 0:
                break
            head = self.buf[:i].decode(errors="replace")
            n = None
            for line in head.split("\r\n"):
                if line.lower().startswith("content-length:"):
                    n = int(line.split(":", 1)[1].strip())
            if n is None:
                self.buf = self.buf[i + 4:]
                continue
            s = i + 4
            if len(self.buf) < s + n:
                break
            out.append(json.loads(self.buf[s:s + n]))
            self.buf = self.buf[s + n:]
        return out

    def send(self, command, args=None):
        assert command in _WHITELIST, \
            f"pedido '{command}' fora da whitelist (fato 4 de L035)"
        self.seq += 1
        msg = {"seq": self.seq, "type": "request", "command": command,
               "arguments": args if args is not None else {}}
        data = json.dumps(msg).encode()
        self.sock.sendall(b"Content-Length: %d\r\n\r\n" % len(data) + data)
        return self.seq

    def wait(self, seq, max_wait=6.0):
        deadline = time.time() + max_wait
        events = []
        while time.time() < deadline:
            try:
                self._read_frames()
            except (ConnectionError, OSError) as e:
                return {"_error": str(e)}, events
            for m in self._parse():
                if m.get("type") == "response" and m.get("request_seq") == seq:
                    return m, events
                events.append(m)
        return None, events

    def request(self, command, args=None, max_wait=6.0):
        s = self.send(command, args)
        resp, _ = self.wait(s, max_wait)
        return resp

    # ---- sessao padrao -------------------------------------------------
    def start_session(self):
        r = self.request("initialize", {
            "adapterID": "smsforge", "clientID": "smsforge-probe",
            "clientName": "SMSForge", "locale": "en",
            "linesStartAt1": True, "columnsStartAt1": True,
            "pathFormat": "path"}, max_wait=10)
        if not (r and r.get("success")):
            raise ConnectionError("initialize sem resposta (fato 4?)")
        r = self.request("attach", {}, max_wait=8)
        if not (r and r.get("success")):
            raise ConnectionError("attach sem resposta")
        return r

    def cont(self, thread_id=1):
        return self.request("continue", {"threadId": thread_id})

    def pause(self, thread_id=1):
        return self.request("pause", {"threadId": thread_id})

    # ---- leitura via avaliador (fato 3) --------------------------------
    def evaluate(self, expr, context="watch", frame_id=0):
        """Texto bruto do avaliador ("EXPR = $9A"). None se pend/servidor morto."""
        r = self.request("evaluate", {"expression": expr, "frameId": frame_id,
                                      "context": context}, max_wait=5)
        if not (r and r.get("success")):
            return None
        self.last_raw = r.get("body", {}).get("result", "")
        return self.last_raw

    def eval_int(self, expr, context="watch"):
        """Valor inteiro da expressao; None se o avaliador recusar."""
        return parse_eval_value(self.evaluate(expr, context=context))

    def read_byte(self, addr):
        """Byte da RAM do SMS (@addr)."""
        return self.eval_int(f"@0x{addr:X}")

    def read_word(self, addr):
        """Word little-endian da RAM (word.ram@@addr)."""
        return self.eval_int(f"word.ram@@0x{addr:X}")

    def read_block(self, addr, n):
        """n bytes consecutivos (n evaluates; so para n pequeno)."""
        out = []
        for i in range(n):
            v = self.read_byte(addr + i)
            if v is None:
                return None
            out.append(v)
        return out
