/* Entrada do pad e leitura dos blobs CMD versionados emitidos pelo conversor. */
#ifndef INPUT_H
#define INPUT_H

#define INPUT_BUF 16u
#define INPUT_BUF_MASK (INPUT_BUF - 1u)

/* Mesmo contrato de bits do fight.h, sem dependência de SMSlib no anel host. */
#define INPUT_UP     0x01u
#define INPUT_DOWN   0x02u
#define INPUT_LEFT   0x04u
#define INPUT_RIGHT  0x08u
#define INPUT_KEY1   0x10u
#define INPUT_KEY2   0x20u
#define INPUT_GUARD  0x40u

void input_init(void);
void input_set_thresholds(unsigned char slot, unsigned char key1,
                          unsigned char key2);
unsigned char input_read(void);
unsigned char input_tick(unsigned char slot, unsigned char keys,
                         unsigned char facing);
unsigned char input_pattern_hit(unsigned char slot,
                                const unsigned char *pattern);
unsigned char input_take_command_dirty(unsigned char slot);
void input_flush(unsigned char slot);

#endif /* INPUT_H */
