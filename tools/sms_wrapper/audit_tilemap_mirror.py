#!/usr/bin/env python3
"""audit_tilemap_mirror.py — espelhamento de tilemap no SMS1 (L130, SMS_GLOBAL §121).

Lei (corpus smspower.org/Development/TilemapMirroring): no VDP do SMS1, se o
bit 0 do registrador 2 e 0, o bit 10 do endereco VRAM da name table e forcado
a 0. As 12 linhas inferiores da tela virtual referenciam as mesmas entradas
das 12 primeiras; com Y-scroll zero em modo 192, as 8 primeiras linhas
preenchem o terco de cima e o de baixo. E invisivel no emulador-alvo SMS2/PC
e nao funciona como pretendido no VDP Genesis — por isso o corpus chama de
"a common bug in homebrew software, however, which may assume the presence of
an SMS2 VDP".

A SMSlib padrao escreve reg2 = 0xFF (bit0 = 1; VDPReg_init em
sdk/devkitSMS-upstream/SMSlib/src/SMSlib.c). O gate julga escritas custom.

Tres modos de medicao:
  --source P ...               escritas literais ao registrador 2 no codigo
                               (outp / VDPControlPort / SMS_write_to_VDPRegister).
                               Valor vindo de variavel nao e decidivel
                               estaticamente: nunca reportado como aprovado.
  --rom BIN ...                assinatura binaria Z80 `ld a,#vv / out (0xBF),a
                               / ld a,#0x82 / out (0xBF),a`. Sem assinatura:
                               nao provado (o init da SMSlib usa tabela, nao
                               imediato).
  --snapshots DIR ...          dumps vdp_regs.bin (11 bytes) de blastem_sms.py;
                               byte[2] bit0 deve ser 1. Modo autoritativo: le o
                               registrador real da ROM no emulador.

Excecao deliberada (imitar *Ys* JP): --allow-sms1-mirror "<motivo>" muda
reprovado para excecao_declarada — aprovacao com lastro, nunca silencio. O
motivo vai ao JSON e deve constar no memory bank do projeto.

Uso: audit_tilemap_mirror.py [--source P..] [--rom BIN..] [--snapshots DIR..]
     [--allow-sms1-mirror MOTIVO] [--json OUT] [--self-check]
Exit: 0 aprovado/excecao/nao-provado-estatico | 1 reprovado | 2 erro de uso
"""
import sys, os, re, json, glob, argparse, tempfile

REG2_CONTROL_BYTE = 0x82  # 0x80 | registrador 2
SNAPSHOT_REG_COUNT = 11

LITERAL = r"(0[xX][0-9A-Fa-f]+|\d+)"
IDENT = r"([A-Za-z_]\w*)"
_SOURCE_SHAPE = [
    (r"outp\s*\(\s*0[xX][bB][fF]\s*,\s*%s\s*\)\s*;\s*"
     r"outp\s*\(\s*0[xX][bB][fF]\s*,\s*0[xX]82\s*\)"),
    (r"VDPControlPort\s*=\s*%s\s*;\s*"
     r"VDPControlPort\s*=\s*0[xX]82\s*;"),
    (r"SMS_write_to_VDPRegister\s*\(\s*(?:2|0[xX]0*2)\s*,\s*%s\s*\)"),
]
# literal decidido; valor vindo de variavel e nao provado, nunca aprovado
SOURCE_PATTERNS = [re.compile(shape % LITERAL) for shape in _SOURCE_SHAPE]
SOURCE_UNDECIDABLE = [re.compile(shape % IDENT) for shape in _SOURCE_SHAPE]


def parse_int(token):
    t = token.strip()
    try:
        return int(t, 16) if t.lower().startswith("0x") else int(t, 10)
    except ValueError:
        return None


def expand_source_paths(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += [os.path.join(r, f) for r, _, fs in os.walk(p) for f in fs
                      if f.endswith((".c", ".h", ".asm"))]
        elif os.path.isfile(p):
            files.append(p)
        else:
            raise OSError("caminho inexistente: %s" % p)
    return sorted(files)


def scan_source(paths):
    findings = []     # (arquivo, linha, valor, bit0)
    undecided = []    # (arquivo, linha, expressao)
    for f in expand_source_paths(paths):
        try:
            src = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for rx in SOURCE_PATTERNS:
            for m in rx.finditer(src):
                v = parse_int(m.group(1))
                if v is None or not 0 <= v <= 0xFF:
                    continue
                line = src.count("\n", 0, m.start()) + 1
                findings.append((f, line, v, v & 1))
        for rx in SOURCE_UNDECIDABLE:
            for m in rx.finditer(src):
                line = src.count("\n", 0, m.start()) + 1
                undecided.append((f, line, m.group(1)))
    return findings, undecided


def scan_rom_file(path):
    data = open(path, "rb").read()
    hits, i = [], 0
    while True:
        j = data.find(b"\x3e", i)
        if j < 0 or j + 8 > len(data):
            break
        if (data[j + 2:j + 4] == b"\xd3\xbf" and data[j + 4] == 0x3e
                and data[j + 5] == REG2_CONTROL_BYTE
                and data[j + 6:j + 8] == b"\xd3\xbf"):
            hits.append((j, data[j + 1], data[j + 1] & 1))
        i = j + 1
    return hits


def scan_snapshots_dir(dirpath):
    out = []
    candidates = sorted(glob.glob(os.path.join(dirpath, "*", "vdp_regs.bin")))
    if not candidates:
        candidates = sorted(glob.glob(os.path.join(dirpath, "vdp_regs.bin")))
    if not candidates:
        out.append((os.path.join(dirpath, "-"), None, None))
        return out
    for p in candidates:
        with open(p, "rb") as fh:
            blob = fh.read()
        if len(blob) != SNAPSHOT_REG_COUNT:
            raise OSError("vdp_regs.bin com %d bytes (esperado %d): %s"
                          % (len(blob), SNAPSHOT_REG_COUNT, p))
        out.append((p, blob[2], blob[2] & 1))
    return out


def audit(source=None, rom=None, snapshots=None, allow_reason=None):
    report = {"findings": [], "unproven": [], "verdict": "aprovado",
              "exception": None}
    bad = False
    for p in source or []:
        found, undec = scan_source([p])
        for f, line, v, bit0 in found:
            report["findings"].append({"modo": "source", "arquivo": f,
                                       "linha": line, "valor_reg2": hex(v),
                                       "bit0": bit0})
            bad = bad or bit0 == 0
        for f, line, expr in undec:
            report["unproven"].append({"modo": "source", "arquivo": f,
                                       "linha": line, "expressao": expr,
                                       "motivo": "valor da escrita ao reg2 nao "
                                       "e literal — nao decidivel estaticamente"})
    for p in rom or []:
        hits = scan_rom_file(p)
        if not hits:
            report["unproven"].append({"modo": "rom", "arquivo": p,
                                       "motivo": "sem assinatura imediata de "
                                       "escrita ao reg2; o init da SMSlib usa "
                                       "tabela — exigir --snapshots"})
        for off, v, bit0 in hits:
            report["findings"].append({"modo": "rom", "arquivo": p,
                                       "offset": off, "valor_reg2": hex(v),
                                       "bit0": bit0})
            bad = bad or bit0 == 0
    for d in snapshots or []:
        for p, v, bit0 in scan_snapshots_dir(d):
            if v is None:
                report["findings"].append({"modo": "snapshots", "diretorio": d,
                                           "erro": "nenhum vdp_regs.bin"})
                bad = True
                continue
            report["findings"].append({"modo": "snapshots", "arquivo": p,
                                       "valor_reg2": hex(v), "bit0": bit0})
            bad = bad or bit0 == 0
    if bad:
        if allow_reason:
            report["verdict"] = "excecao_declarada"
            report["exception"] = allow_reason.strip()
        else:
            report["verdict"] = "reprovado_espelhamento_sms1"
    elif report["unproven"]:
        report["verdict"] = ("nao_provado_estatico" if not report["findings"]
                             else "aprovado_com_nao_provado")
    return report


def self_check():
    ok = True
    def check(label, cond):
        nonlocal ok
        print(("  [OK] " if cond else "  [XX] ") + label)
        ok = ok and cond
    with tempfile.TemporaryDirectory(prefix="mirror_selfcheck_") as tmp:
        bad_c = os.path.join(tmp, "bad.c")
        open(bad_c, "w").write(
            "void setup(void){ outp(0xBF, 0x7E); outp(0xBF, 0x82); }\n")
        check("source outp 0x7E/0x82 reprovado",
              audit(source=[bad_c])["verdict"] == "reprovado_espelhamento_sms1")
        mixed_c = os.path.join(tmp, "mixed.c")
        open(mixed_c, "w").write(
            "void a(void){ SMS_write_to_VDPRegister(2, 0xFF); }\n"
            "void b(void){ VDPControlPort = 0xFE; VDPControlPort = 0x82; }\n")
        r = audit(source=[mixed_c])
        check("source: macro 0xFF aprovado coexiste com par 0xFE reprovado "
              "(veredito global reprova, ambos achados reportados)",
              r["verdict"] == "reprovado_espelhamento_sms1"
              and any(f["valor_reg2"] == "0xfe" and f["modo"] == "source"
                      for f in r["findings"])
              and any(f["valor_reg2"] == "0xff" and f["bit0"] == 1
                      for f in r["findings"]))
        only_good = os.path.join(tmp, "good.c")
        open(only_good, "w").write(
            "void setup(void){ SMS_write_to_VDPRegister(2, 0xFF); }\n")
        check("source apenas 0xFF aprovado",
              audit(source=[only_good])["verdict"] == "aprovado")
        var_c = os.path.join(tmp, "var.c")
        open(var_c, "w").write(
            "void setup(unsigned char v){ outp(0xBF, v); outp(0xBF, 0x82); }\n")
        r = audit(source=[var_c])
        check("source com variavel: nao_provado_estatico, nunca aprovado",
              r["verdict"] == "nao_provado_estatico" and r["unproven"]
              and not r["findings"])
        rom_bad = os.path.join(tmp, "bad.bin")
        open(rom_bad, "wb").write(b"\x00\x3e\x7e\xd3\xbf\x3e\x82\xd3\xbf\x00")
        check("rom 3E 7E D3 BF 3E 82 D3 BF reprovada",
              audit(rom=[rom_bad])["verdict"] == "reprovado_espelhamento_sms1")
        rom_ok = os.path.join(tmp, "ok.bin")
        open(rom_ok, "wb").write(b"\x00\x3e\xff\xd3\xbf\x3e\x82\xd3\xbf\x00")
        check("rom 3E FF ... aprovada",
              audit(rom=[rom_ok])["verdict"] == "aprovado")
        rom_none = os.path.join(tmp, "none.bin")
        open(rom_none, "wb").write(bytes(range(64)))
        r = audit(rom=[rom_none])
        check("rom sem assinatura = nao_provado_estatico com motivo",
              r["verdict"] == "nao_provado_estatico" and r["unproven"])
        snap_root = os.path.join(tmp, "sessao")
        sdir = os.path.join(snap_root, "snapshots")
        for name in ("000", "001"):
            d = os.path.join(sdir, name)
            os.makedirs(d)
            open(os.path.join(d, "vdp_regs.bin"), "wb").write(
                bytes([0x86, 0x44, 0xFE]) + bytes(8))
        check("snapshot reg2=0xFE reprovado",
              audit(snapshots=[sdir])["verdict"] == "reprovado_espelhamento_sms1")
        r = audit(snapshots=[sdir],
                  allow_reason="projeto imita *Ys* JP; mirroring declarado no "
                  "GDD e no memory bank")
        check("excecao com motivo vira excecao_declarada",
              r["verdict"] == "excecao_declarada" and r["exception"])
        for name in ("000", "001"):
            open(os.path.join(sdir, name, "vdp_regs.bin"), "wb").write(
                bytes([0x86, 0x44, 0xFF]) + bytes(8))
        check("snapshot reg2=0xFF aprovado",
              audit(snapshots=[sdir])["verdict"] == "aprovado")
        open(os.path.join(sdir, "000", "vdp_regs.bin"), "wb").write(b"\x01")
        try:
            audit(snapshots=[sdir])
            check("vdp_regs.bin truncado levanta OSError", False)
        except OSError:
            check("vdp_regs.bin truncado levanta OSError", True)
        empty = os.path.join(tmp, "empty")
        os.makedirs(empty)
        check("diretorio sem dumps e reprovado",
              audit(snapshots=[empty])["verdict"]
              == "reprovado_espelhamento_sms1")
    print("SELFCHECK audit_tilemap_mirror.py: " + ("VERDE" if ok else "VERMELHO"))
    return 0 if ok else 1


def main():
    if "--self-check" in sys.argv:
        sys.exit(self_check())
    ap = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]))
    ap.add_argument("--source", nargs="+", metavar="P")
    ap.add_argument("--rom", nargs="+", metavar="BIN")
    ap.add_argument("--snapshots", nargs="+", metavar="DIR")
    ap.add_argument("--allow-sms1-mirror", metavar="MOTIVO")
    ap.add_argument("--json", metavar="OUT")
    args = ap.parse_args()
    if not (args.source or args.rom or args.snapshots):
        print("erro: use --source, --rom ou --snapshots (ou --self-check)",
              file=sys.stderr)
        sys.exit(2)
    if args.allow_sms1_mirror is not None and not args.allow_sms1_mirror.strip():
        print("erro: --allow-sms1-mirror exige motivo nao vazio",
              file=sys.stderr)
        sys.exit(2)
    try:
        report = audit(source=args.source, rom=args.rom,
                       snapshots=args.snapshots,
                       allow_reason=args.allow_sms1_mirror)
    except OSError as e:
        print("erro: %s" % e, file=sys.stderr)
        sys.exit(2)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print(text)
    sys.exit(1 if report["verdict"] == "reprovado_espelhamento_sms1" else 0)


if __name__ == "__main__":
    main()
