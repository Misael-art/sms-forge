# skill: sms-z80-sdcc-gotchas

## Assumir como suspeita até pagar com build
- `int` = 16-bit signed (SDCC z80). Overflow silencioso em contagens grandes.
- Multiplicação/divisão caras: tabelas lookup, Q8.8, deslocamentos.
- float/double: software float — PROIBIDOS em runtime quente.
- RAM 8KB: sem malloc/free; pools estáticos por entidade; stack pequena.
- `__z88dk_fastcall` / `__sdcc_call(1)`: convenções do header mandam, não a intuição.
- Locais recarregam via IX; ponteiros `static` no hot path.
- Espelhar tile em runtime (bitrev) troca ROM por CPU. Curva paga
  (STREAM_BYTES): 32→59.5 fps, 64→58.3, 96→57.5, 128→55.5, 256→40 (L045).

## Build canônico (devkitSMS)
```
sdcc -c -mz80 main.c
sdcc -o game.ihx -mz80 --no-std-crt0 --data-loc 0xC000 crt0_sms.rel main.rel SMSlib.lib PSGlib.lib
makesms game.ihx game.sms
```
crt0 SEMPRE primeiro; libs DEPOIS do código. Só o wrapper monta isso.

## ABI e diagnóstico (L004/L009)

Se o link reclamar de `sdcccall` incompatível ou a chamada parecer corrompida,
confronte o compilador usado, o header e a biblioteca efetivamente linkada.
O procedimento canônico `tools/sms_wrapper/ensure_toolchain.sh` recompila
SMSlib/PSGlib a partir das fontes e executa smoke compile→link→ROM. Não remova
atributos do header para fazer uma biblioteca antiga passar. O smoke de build
não substitui execução da ROM em sessão privada.

Marcadores de diagnóstico em RAM com `__at()` precisam de `volatile`; confirme
o endereço no mapa pós-link e rode `audit_debug_markers.py`. Não escolher um
endereço livre por aparência: confrontar buffers, stack e demais símbolos.
Antes de interpretar leitura DAP, conferir o formato: `$C800`/`$00` são
hexadecimais, não texto inválido a transformar silenciosamente em zero.
Magic/schema, SHA da ROM e avanço do probe distinguem leitura válida de
campo errado ou sessão errada; use `measure_runtime_probe.py`.
