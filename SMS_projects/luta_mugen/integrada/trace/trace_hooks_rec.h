/* trace_hooks_rec.h — versao do produtor de trilha. Substitui inc/trace_hooks.h SO na copia isolada. */
#ifndef TRACE_HOOKS_H
#define TRACE_HOOKS_H
extern unsigned char trace_pad(unsigned char who, unsigned char real);
extern void trace_record(void);
#define TRACE_PAD(who, real) trace_pad((who), (real))
#define TRACE_RECORD()       trace_record()
#endif
