"""Compilador de expressoes MUGEN -> bytecode da VM (ver opcodes.py).

Cobre a sintaxe de triggers/parametros usada por personagens reais:
precedencia MUGEN, intervalos `= [a,b]`, `animelem = n[, op t]`, `timemod = m, r`,
`command = "x"`, `statetype = S`, `const(...)` resolvido em compilacao,
`vel x` / `p2bodydist x`, `ifelse`, `var(n)`, `gethitvar(fall.yvel)`.

Nada e silenciosamente descartado: identificadores nao suportados viram UNSUPPORTED
(avaliam 0) e sao listados em `CompiledExpr.unsupported` para o relatorio de fidelidade.
"""
from __future__ import annotations

import math
import re
import struct
from dataclasses import dataclass, field

from . import opcodes as O

_TOKEN = re.compile(
    r"\s*(?:(?P<num>\d+\.\d*|\.\d+|\d+)|(?P<str>\"[^\"]*\")|(?P<id>[A-Za-z_][A-Za-z0-9_.]*)"
    r"|(?P<op>:=|\*\*|\|\||&&|\^\^|!=|<=|>=|[-+*/%=<>!~&|^()\[\],]))"
)


class ExprError(ValueError):
    pass


@dataclass
class CompiledExpr:
    code: bytes
    unsupported: list[str] = field(default_factory=list)
    constant: float | None = None    # valor se a expressao for constante
    gate: list[int] | None = None    # comandos sem os quais a expressao e sempre falsa (None = sem portao)
    tgate: tuple[int, int] | None = None   # (1, N): exige time == N ; (2, N): exige inicio do elemento N


@dataclass
class Ctx:
    commands: dict[str, int]                 # nome minusculo -> indice
    constants: dict[str, dict[str, str]]     # secoes [Data]/[Size]/... do cns
    anims: set[int]                          # actions existentes (selfanimexist)


# --------------------------------------------------------------------- AST
@dataclass
class N:
    kind: str
    val: object = None
    kids: list = field(default_factory=list)


def field_key(n: N):
    """Nome estavel do campo alvo de um redirect; None quando nao e um campo nomeado."""
    if n.kind == "id":
        return n.val
    if n.kind == "call":
        a = n.kids[0].val if n.kids and n.kids[0].kind in ("name", "num", "id") else "?"
        return f"{n.val}({a})"
    return None


def term_text(n: N) -> str:
    """Renderizacao estavel de um termo de uma lista de valores, para o gap declarado."""
    if n.kind == "id":
        return n.val
    if n.kind == "num":
        v = n.val
        return str(int(v)) if float(v).is_integer() else str(v)
    if n.kind == "str":
        return f'"{n.val}"'
    if n.kind == "call":
        return f"{n.val}({', '.join(term_text(a) for a in n.kids)})"
    return f"<{n.kind}>"


def tokenize(s: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    s = s.strip()
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m or m.end() == pos:
            raise ExprError(f"caractere inesperado '{s[pos:pos+10]}'")
        pos = m.end()
        for k in ("num", "str", "id", "op"):
            if m.group(k) is not None:
                out.append((k, m.group(k)))
                break
    return out


# precedencia binaria MUGEN (maior = liga mais forte)
BINARY = {
    "||": 1, "^^": 2, "&&": 3, "|": 4, "^": 5, "&": 6,
    "=": 7, "!=": 7, "<": 8, "<=": 8, ">": 8, ">=": 8,
    "+": 9, "-": 9, "*": 10, "/": 10, "%": 10, "**": 11,
}
TWO_WORD = {"vel", "pos", "p2bodydist", "p2dist", "screenpos", "p2pos", "rootdist", "parentdist"}

# Escopos MUGEN escritos com virgula (`enemynear, life`). Re-derivado do VM deste
# runtime (opcodes.TRIGGER), nao herdado do texto do doador MD (L093): so ha
# equivalente onde existe campo TRG real, e o runtime nao tem helpers nem time,
# entao `root,X` e o proprio lutador. O que nao tem gemeo vira id sintetico e cai
# no UNSUPPORTED declarado do Emitter — nunca silencio e nunca abort.
SCOPE = {"root", "enemy", "enemynear", "enemyleader", "target", "helper", "parent", "child",
         "playerid", "friend", "allies", "summon", "nothitby", "partner", "assistant", "triggerno"}
ENEMY_FIELDS = {"life": "p2life", "stateno": "p2stateno", "statetype": "p2statetype",
                "movetype": "p2movetype", "ctrl": "p2ctrl"}


class Parser:
    def __init__(self, toks):
        self.t, self.i = toks, 0
        self.in_args = 0    # virgula dentro de parenteses de funcao separa argumentos, nao valores

    def peek(self, k=0):
        j = self.i + k
        return self.t[j] if j < len(self.t) else ("eof", "")

    def take(self, val=None):
        tok = self.peek()
        if val is not None and tok[1] != val:
            raise ExprError(f"esperado '{val}', obtido '{tok[1]}'")
        self.i += 1
        return tok

    def parse(self):
        n = self.expr(0)
        if self.peek()[0] != "eof":
            raise ExprError(f"token sobrando '{self.peek()[1]}'")
        return n

    def expr(self, minp):
        left = self.unary()
        while True:
            k, v = self.peek()
            if k != "op" or v not in BINARY or BINARY[v] < minp:
                return left
            p = BINARY[v]
            self.take()
            if v in ("=", "!=") and self.peek()[1] in ("[", "("):
                rng = self.try_interval()
                if rng is not None:
                    left = N("range", (v == "=", rng[0]), [left, rng[1], rng[2]])
                    continue
            right = self.expr(p + (0 if v == "**" else 1))
            node = self.special_compare(v, left, right)
            # `X = v1, v2, ...`: lista de valores MUGEN na comparacao. So aqui, nunca
            # dentro de argumentos de funcao (la a virgula separa parametros).
            if v in ("=", "!=") and node.kind == "bin" and node.val == v \
                    and not self.in_args and self.peek()[1] == ",":
                vals = [node.kids[1]]
                while self.peek()[1] == ",":
                    self.take(",")
                    vals.append(self.expr(p + 1))
                node = N("attrlist", v, [node.kids[0]] + vals)
            left = node

    def try_interval(self):
        save = self.i
        open_ = self.take()[1]
        try:
            a = self.expr(1)
            if self.peek()[1] != ",":
                raise ExprError("nao e intervalo")
            self.take(",")
            b = self.expr(1)
            close = self.take()[1]
            if close not in ("]", ")"):
                raise ExprError("intervalo mal fechado")
        except ExprError:
            self.i = save
            return None
        flags = (1 if open_ == "[" else 0) | (2 if close == "]" else 0)
        return flags, a, b

    def special_compare(self, op, left, right):
        # animelem = n [, op t]  |  timemod = m, r
        if left.kind == "id" and left.val in ("animelem", "timemod") and op in ("=", "!="):
            if left.val == "animelem":
                cmp_op, rhs = "=", N("num", 0)
                n = None
                if self.peek()[1] == ",":
                    self.take(",")
                    k, v = self.peek()
                    if k == "op" and v in ("=", "!=", "<", "<=", ">", ">="):
                        self.take()
                        cmp_op = v
                        rhs = self.expr(9)
                        n = N("bin", cmp_op, [N("animelemtime", None, [right]), rhs])
                    elif v in ("[", "("):
                        interval = self.try_interval()
                        if interval is not None:
                            n = N("range", (True, interval[0]),
                                   [N("animelemtime", None, [right]), interval[1], interval[2]])
                        else:
                            raise ExprError("intervalo invalido na clausula animelem")
                    else:
                        rhs = self.expr(9)
                        n = N("bin", cmp_op, [N("animelemtime", None, [right]), rhs])
                if n is None:
                    n = N("bin", cmp_op, [N("animelemtime", None, [right]), rhs])
                return n if op == "=" else N("un", "!", [n])
            self.take(",")
            r = self.expr(9)
            n = N("bin", "=", [N("bin", "%", [N("id", "time"), right]), r])
            return n if op == "=" else N("un", "!", [n])
        return N("bin", op, [left, right])

    def unary(self):
        k, v = self.peek()
        if k == "op" and v in ("!", "-", "~", "+"):
            self.take()
            operand = self.unary()
            return operand if v == "+" else N("un", v, [operand])
        return self.postfix()

    def postfix(self):
        k, v = self.take()
        if k == "num":
            return N("num", float(v) if "." in v else int(v))
        if k == "str":
            return N("str", v[1:-1])
        if k == "op" and v == "(":
            n = self.expr(0)
            self.take(")")
            return n
        if k == "id":
            name = v.lower()
            if name in SCOPE:
                r = self.try_redirect(name)
                if r is not None:
                    return r
            nk, nv = self.peek()
            if name in TWO_WORD and nk == "id" and nv.lower() in ("x", "y"):
                self.take()
                return N("id", f"{name} {nv.lower()}")
            if nk == "op" and nv == "(":
                self.take("(")
                args = []
                if self.peek()[1] != ")":
                    self.in_args += 1
                    try:
                        args.append(self.raw_or_expr(name))
                        while self.peek()[1] == ",":
                            self.take(",")
                            args.append(self.raw_or_expr(name))
                    finally:
                        self.in_args -= 1
                self.take(")")
                return N("call", name, args)
            return N("id", name)
        raise ExprError(f"token inesperado '{v}'")

    def try_redirect(self, who):
        """`escopo[, (idx)], campo`: devolve o no do campo no escopo, ou None se nao e redirect."""
        save = self.i                      # o id do escopo ja foi consumido
        idx = ""
        if self.peek()[1] == "(":
            depth = 0
            while True:
                k, tok = self.take()
                if k == "eof":
                    self.i = save
                    return None
                if tok == "(":
                    depth += 1
                elif tok == ")":
                    depth -= 1
                    if depth == 0:
                        break
                elif depth == 1:
                    idx += tok
        if self.peek()[1] != ",":
            self.i = save
            return None
        self.take(",")
        inner = self.postfix()
        key = field_key(inner)
        if key is None:
            self.i = save
            return None
        if who == "root" and not idx:
            return inner
        if who in ("enemy", "enemynear") and idx in ("", "0"):
            if key in ENEMY_FIELDS:
                return N("id", ENEMY_FIELDS[key])
        label = f"{who}({idx}),{key}" if idx and who in ("enemy", "enemynear") else f"{who},{key}"
        return N("id", label)

    def raw_or_expr(self, fn):
        # const(velocity.walk.fwd.x) e gethitvar(fall.yvel) recebem um nome, nao expressao
        if fn in ("const", "gethitvar") and self.peek()[0] == "id":
            return N("name", self.take()[1].lower())
        return self.expr(0)


# ------------------------------------------------------------------ emissao
class Emitter:
    def __init__(self, ctx: Ctx):
        self.ctx, self.out, self.unsupported = ctx, bytearray(), []

    def op(self, name, *args):
        self.out.append(O.OP[name])
        self.out.extend(args)

    def push_num(self, x):
        if isinstance(x, float) and not x.is_integer():
            self.op("PUSHFX")
            self.out.extend(struct.pack(">i", int(round(x * O.FX))))
            return
        x = int(x)
        if -128 <= x <= 127:
            self.op("PUSH8", x & 0xFF)
        elif -32768 <= x <= 32767:
            self.op("PUSH16")
            self.out.extend(struct.pack(">h", x))
        else:
            self.op("PUSHFX")
            self.out.extend(struct.pack(">i", max(-(1 << 31), min((1 << 31) - 1, x * O.FX))))

    def unsupported_(self, what):
        self.unsupported.append(what)
        self.op("UNSUPPORTED", min(len(self.unsupported), 255))

    def const_value(self, name):
        for sec in ("data", "size", "velocity", "movement"):
            d = self.ctx.constants.get(sec, {})
            key = name.split(".", 1)[1] if name.startswith(sec + ".") else name
            if key in d:
                raw = d[key].split(",")
                idx = 0
                for suffix, i in ((".x", 0), (".y", 1)):
                    if key.endswith(suffix) and key[: -len(suffix)] in d:
                        raw, idx = d[key[: -len(suffix)]].split(","), i
                try:
                    return float(raw[idx])
                except (ValueError, IndexError):
                    return None
            # velocity.run.back.x -> chave "run.back" com par x,y
            for suffix, i in ((".x", 0), (".y", 1)):
                if key.endswith(suffix) and key[: -len(suffix)] in d:
                    try:
                        return float(d[key[: -len(suffix)]].split(",")[i])
                    except (ValueError, IndexError):
                        return None
        return None

    def emit(self, n: N):
        k = n.kind
        if k == "num":
            self.push_num(n.val)
        elif k == "str":
            self.unsupported_(f"string solta \"{n.val}\"")
        elif k == "id":
            self.emit_id(n.val)
        elif k == "un":
            self.emit(n.kids[0])
            self.op({"-": "NEG", "!": "NOT", "~": "BNOT"}[n.val])
        elif k == "bin":
            self.emit_bin(n)
        elif k == "range":
            eq, flags = n.val
            for kid in n.kids:
                self.emit(kid)
            self.op("INRANGE", flags)
            if not eq:
                self.op("NOT")
        elif k == "animelemtime":
            self.emit(n.kids[0])
            self.op("ANIMELEMTIME")
        elif k == "attrlist":
            self.emit_attrlist(n)
        elif k == "call":
            self.emit_call(n)
        else:
            self.unsupported_(f"no {k}")

    def emit_attrlist(self, n):
        """Lista de valores MUGEN (`X = v1, v2, ...`): sem campo na VM, vira UM gap
        declarado que avalia 0. Expandir para OR/AND inventaria semantica que o
        runtime nao tem; descartar valores em silencio e proibido pelo contrato."""
        campo, valores = term_text(n.kids[0]), ", ".join(term_text(v) for v in n.kids[1:])
        self.unsupported_(f"{campo} {n.val} {valores} (lista de valores sem campo na VM)")

    def emit_bin(self, n):
        a, b = n.kids
        # command = "x"
        if a.kind == "id" and a.val == "command" and b.kind == "str":
            idx = self.ctx.commands.get(b.val.lower())
            if idx is None:
                self.unsupported_(f"comando inexistente \"{b.val}\"")
            else:
                self.op("CMD", idx)
            if n.val == "!=":
                self.op("NOT")
            return
        # && / || com curto-circuito (a VM do 68000 nao pode avaliar tudo a cada tick)
        if n.val in ("&&", "||"):
            self.emit(a)
            self.op("ANDJ" if n.val == "&&" else "ORJ")
            at = len(self.out)
            self.out.extend(b"\0\0")
            self.emit(b)
            self.op("BOOL")
            rel = len(self.out) - (at + 2)
            self.out[at:at + 2] = struct.pack(">H", rel)
            return
        # statetype = S etc.: simbolos no lado direito
        if b.kind == "id" and b.val in O.SYMBOLS and a.kind == "id":
            self.emit(a)
            self.push_num(O.SYMBOLS[b.val])
        else:
            self.emit(a)
            self.emit(b)
        names = {"=": "EQ", "!=": "NE", "<": "LT", "<=": "LE", ">": "GT", ">=": "GE",
                 "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD", "**": "POW",
                 "&": "BAND", "|": "BOR", "^": "BXOR", "&&": "LAND", "||": "LOR", "^^": "LXOR"}
        self.op(names[n.val])

    def emit_id(self, name):
        name = O.ALIASES.get(name, name)
        if name in O.TRIGGER:
            self.op("TRG", O.TRIGGER[name])
        elif name in O.SYMBOLS:
            self.push_num(O.SYMBOLS[name])
        elif name == "animelemno":
            self.op("TRG", O.TRIGGER["animelemno_cur"])
        else:
            self.unsupported_(f"trigger '{name}'")

    def emit_call(self, n):
        fn, args = O.ALIASES.get(n.val, n.val), n.kids
        if fn == "const" and args and args[0].kind == "name":
            v = self.const_value(args[0].val)
            if v is None:
                self.unsupported_(f"const({args[0].val})")
            else:
                self.push_num(v)
            return
        if fn == "ifelse" and len(args) == 3:
            for a in args:
                self.emit(a)
            self.op("IFELSE")
            return
        if fn in ("abs", "floor", "ceil") and len(args) == 1:
            self.emit(args[0])
            self.op("ABS" if fn == "abs" else "FLOOR")
            if fn == "ceil":
                self.unsupported.append("ceil aproximado por floor")
            return
        if fn == "animexist" and len(args) == 1 and args[0].kind == "num":
            self.push_num(1 if int(args[0].val) in self.ctx.anims else 0)
            return
        if fn == "gethitvar" and args and args[0].kind == "name":
            gid = O.GETHITVAR.get(args[0].val)
            if gid is None:
                self.unsupported_(f"gethitvar({args[0].val})")
            else:
                self.push_num(gid)
                self.op("TRGA", O.TRIGGER_ARG["gethitvar"])
            return
        if fn in O.TRIGGER_ARG and len(args) == 1:
            self.emit(args[0])
            self.op("TRGA", O.TRIGGER_ARG[fn])
            return
        self.unsupported_(f"funcao '{fn}'")


def fold(n: N):
    """Avalia constantes para parametros simples (ex.: damage = 130)."""
    if n.kind == "num":
        return n.val
    if n.kind == "un" and n.val == "-":
        v = fold(n.kids[0])
        return None if v is None else -v
    if n.kind == "bin" and n.val in "+-*/":
        a, b = fold(n.kids[0]), fold(n.kids[1])
        if a is None or b is None:
            return None
        if n.val == "/":
            return None if b == 0 else a / b
        return {"+": a + b, "-": a - b, "*": a * b}[n.val]
    return None


def command_gate(n: N, ctx: Ctx) -> set[int] | None:
    """Conjunto G tal que: nenhum comando de G ativo => expressao falsa. Exato por construcao:
    A && B -> portao de qualquer lado (o menor); A || B -> uniao (so se ambos tiverem portao)."""
    if n.kind == "bin" and n.val == "=" and n.kids[0].kind == "id" and n.kids[0].val == "command" \
            and n.kids[1].kind == "str":
        idx = ctx.commands.get(n.kids[1].val.lower())
        return {idx} if idx is not None else None
    if n.kind == "bin" and n.val == "&&":
        a, b = command_gate(n.kids[0], ctx), command_gate(n.kids[1], ctx)
        cands = [g for g in (a, b) if g is not None]
        return min(cands, key=len) if cands else None
    if n.kind == "bin" and n.val == "||":
        a, b = command_gate(n.kids[0], ctx), command_gate(n.kids[1], ctx)
        return a | b if a is not None and b is not None else None
    return None


def time_gate(n: N) -> tuple[int, int] | None:
    """Condicao necessaria barata: 'time = N' ou 'animelem = N' (inicio do elemento) em conjuncao."""
    if n.kind == "bin" and n.val == "=":
        a, b = n.kids
        if a.kind == "id" and a.val == "time" and b.kind == "num" and isinstance(b.val, int):
            return (1, b.val)
        if a.kind == "animelemtime" and a.kids[0].kind == "num" and b.kind == "num" and b.val == 0:
            return (2, int(a.kids[0].val))
    if n.kind == "bin" and n.val == "&&":
        return time_gate(n.kids[0]) or time_gate(n.kids[1])
    if n.kind == "bin" and n.val == "||":
        a, b = time_gate(n.kids[0]), time_gate(n.kids[1])
        return a if a is not None and a == b else None
    return None


def compile_expr(text: str, ctx: Ctx) -> CompiledExpr:
    ast = Parser(tokenize(text)).parse()
    em = Emitter(ctx)
    em.emit(ast)
    em.op("END")
    c = fold(ast)
    return CompiledExpr(bytes(em.out), em.unsupported, None if c is None or math.isnan(c) else c)


def compile_condition(triggerall: list[str], groups: dict[int, list[str]], ctx: Ctx) -> CompiledExpr:
    """(all && ...) && ((g1a && g1b) || (g2a) || ...) -- grupos devem ser consecutivos desde 1 (regra MUGEN)."""
    def conj(items):
        return " && ".join(f"({x})" for x in items)
    parts = []
    if triggerall:
        parts.append(conj(triggerall))
    ordered, i = [], 1
    while i in groups:
        ordered.append(f"({conj(groups[i])})")
        i += 1
    unsupported = []
    if len(ordered) != len(groups):
        unsupported.append(f"triggers fora de sequencia ignorados: {sorted(set(groups) - set(range(1, i)))}")
    if not ordered:
        return CompiledExpr(bytes([O.OP["PUSH8"], 0, O.OP["END"]]), unsupported + ["sem trigger1"], 0)
    parts.append(" || ".join(ordered))
    text = " && ".join(f"({p})" for p in parts)
    ce = compile_expr(text, ctx)
    ast = Parser(tokenize(text)).parse()
    g = command_gate(ast, ctx)
    ce.gate = sorted(g) if g is not None and len(g) <= 16 else None
    tg = time_gate(ast)
    ce.tgate = tg if tg is not None and 0 <= tg[1] <= 32767 else None
    ce.unsupported = unsupported + ce.unsupported
    return ce
