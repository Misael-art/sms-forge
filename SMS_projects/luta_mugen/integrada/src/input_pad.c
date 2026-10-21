/* input_pad.c — ver inc/input_pad.h. Traducao de bits, sem hardware e sem estado.
 *
 * `unsigned int` no SDCC Z80 tem 16 bits (mesmo tamanho da palavra do pad),
 * entao a palavra inteira cabe no argumento sem estourar.
 */
#include "input_pad.h"

unsigned char input_pad_levels(unsigned int held, unsigned char port) {
    unsigned int bits = port ? (held >> PAD_B_SHIFT) : held;
    return (unsigned char)(bits & PAD_LEVEL_MASK);
}
