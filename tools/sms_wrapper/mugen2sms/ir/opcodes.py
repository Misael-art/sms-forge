"""Contrato unico de bytecode entre o compilador (Python) e a VM do runtime (C).

generators/c_runtime_spec.py gera `mg_ops.h` a partir destas tabelas; nunca editar o .h a mao.
Valores numericos da VM: s32 em ponto fixo 24.8 (FX = 256). Sem float no runtime.
"""
from __future__ import annotations

FX_SHIFT = 8
FX = 1 << FX_SHIFT

# --- opcodes (u8) -----------------------------------------------------------
OPS = [
    "END",          # fim do programa; resultado = topo da pilha
    "PUSH8",        # s8 inteiro
    "PUSH16",       # s16 inteiro (big-endian)
    "PUSHFX",       # s32 ja em 24.8 (big-endian)
    "TRG",          # u8 trigger sem argumento (ver TRIGGERS)
    "TRGA",         # u8 trigger com 1 argumento tirado da pilha (ver TRIGGERS_ARG)
    "CMD",          # u8 indice do comando; empurra 1 se ativo
    "ANIMELEMTIME", # arg na pilha: elemento (1-based); empurra ticks desde o inicio do elemento (<0 se ainda nao chegou)
    "NEG", "NOT", "BNOT", "ABS", "FLOOR",
    "ADD", "SUB", "MUL", "DIV", "MOD", "POW",
    "EQ", "NE", "LT", "LE", "GT", "GE",
    "BAND", "BOR", "BXOR",
    "LAND", "LOR", "LXOR",
    "INRANGE",      # u8 flags (bit0 = incl. min, bit1 = incl. max); pilha: v min max
    "IFELSE",       # pilha: c a b -> (c ? a : b)
    "UNSUPPORTED",  # u8 id do motivo (so para diagnostico); empurra 0
    "ANDJ",         # u16 salto: se topo == 0 salta (mantem 0); senao descarta o topo
    "ORJ",          # u16 salto: se topo != 0 troca por 1 e salta; senao descarta o topo
    "BOOL",         # normaliza topo para 0/1
]
OP = {name: i for i, name in enumerate(OPS)}

# --- triggers sem argumento ---------------------------------------------------
TRIGGERS = [
    "time", "animtime", "stateno", "prevstateno", "statetype", "movetype", "ctrl", "anim",
    "movecontact", "movehit", "moveguarded", "movereversed", "hitcount",
    "power", "powermax", "life", "lifemax", "alive",
    "vel_x", "vel_y", "pos_x", "pos_y",
    "p2bodydist_x", "p2bodydist_y", "p2dist_x", "p2dist_y",
    "p2life", "p2stateno", "p2statetype", "p2movetype", "p2ctrl",
    "facing", "random", "roundstate", "matchover", "winko", "win", "lose",
    "frontedgebodydist", "frontedgedist", "backedgebodydist", "backedgedist",
    "hitshakeover", "hitover", "hitfall", "canrecover", "inguarddist",
    "animelemno_cur",  # elemento atual (1-based) -- usado quando animelemno(0)
    "gametime", "roundno", "numenemy", "ailevel", "numhelper", "numexplod", "ishelper",
]
TRIGGER = {n: i for i, n in enumerate(TRIGGERS)}

# --- triggers com argumento (argumento avaliado na pilha) -------------------------
TRIGGERS_ARG = [
    "var", "fvar", "sysvar", "sysfvar",
    "animelemno",        # elemento que estara ativo daqui a N ticks
    "numprojid", "projcontacttime", "projhittime", "projguardedtime",
    "gethitvar",         # argumento = id de GETHITVARS
    "animexist",
    "numhelper",
]
TRIGGER_ARG = {n: i for i, n in enumerate(TRIGGERS_ARG)}

GETHITVARS = [
    "xvel", "yvel", "fall.yvel", "fall", "hittime", "slidetime", "ctrltime", "animtype",
    "groundtype", "airtype", "damage", "hitshaketime", "hitcount", "yaccel", "isbound",
    "recovertime", "fall.recover", "fall.damage", "fall.xvel",
]
GETHITVAR = {n: i for i, n in enumerate(GETHITVARS)}

# Constantes simbolicas (codigos ASCII para ficar legivel em debug no runtime)
SYMBOLS = {"s": ord("S"), "c": ord("C"), "a": ord("A"), "l": ord("L"),
           "i": ord("I"), "h": ord("H"), "u": ord("U")}

# Aliases de nomes MUGEN para nomes da tabela
ALIASES = {
    "vel x": "vel_x", "vel y": "vel_y", "pos x": "pos_x", "pos y": "pos_y",
    "p2bodydist x": "p2bodydist_x", "p2bodydist y": "p2bodydist_y",
    "p2dist x": "p2dist_x", "p2dist y": "p2dist_y",
    "selfanimexist": "animexist",
}
