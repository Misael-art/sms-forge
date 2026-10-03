/* trace_hooks.h — ganchos do produtor de trilha (doc/21 item 3, L097).
 *
 * Na ROM canonica os dois macros sao identidade/vazio: o codigo gerado nao muda (verificado por SHA, ver
 * tools/sms_wrapper/luta_mugen_trace_dap.py --check-canonical). O produtor substitui ESTE header por
 * trace/trace_hooks_rec.h numa copia isolada e acrescenta trace/trace_rec.c.
 */
#ifndef TRACE_HOOKS_H
#define TRACE_HOOKS_H
#define TRACE_PAD(who, real) (real)
#define TRACE_RECORD()       ((void)0)
#endif
