/* Leitura da Porta A; a logica CMD/tier fica isolada em input.c. */
#include "SMSlib.h"
#include "input.h"

unsigned char input_read(void) {
    unsigned int held = SMS_getKeysHeld() &
        (PORT_A_KEY_UP | PORT_A_KEY_DOWN | PORT_A_KEY_LEFT |
         PORT_A_KEY_RIGHT | PORT_A_KEY_1 | PORT_A_KEY_2);
    unsigned char keys = 0;
    if (held & PORT_A_KEY_UP) keys |= INPUT_UP;
    if (held & PORT_A_KEY_DOWN) keys |= INPUT_DOWN;
    if (held & PORT_A_KEY_LEFT) keys |= INPUT_LEFT;
    if (held & PORT_A_KEY_RIGHT) keys |= INPUT_RIGHT;
    if (held & PORT_A_KEY_1) keys |= INPUT_KEY1;
    if (held & PORT_A_KEY_2) keys |= INPUT_KEY2;
    return keys;
}
