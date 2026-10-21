/* input_pad.h — palavra do pad (SMS_getKeysHeld) -> niveis K_* de um ator.
 *
 * A porta fisica pertence a `main.c` (Porta A = P1, Porta B = P2); este modulo
 * so traduz bits e por isso compila e e testado no host sem SMSlib
 * (tools/sms_wrapper/mugen2sms/tests/test_input_pad_c.py confere, bit a bit,
 * contra o header do devkitSMS — a autoridade, nao a memoria).
 *
 * SMSlib.h:296-302 (autoridade #8):
 *   PORT_A_KEY_UP/DOWN/LEFT/RIGHT/KEY_1/KEY_2 = 0x01 0x02 0x04 0x08 0x10 0x20
 *   PORT_B_* = os mesmos seis bits seis posicoes acima (0x40 .. 0x0800)
 *   PORT_A_TH 0x4000 / PORT_B_TH 0x8000 = luz da pistola, nao e input de luta.
 * A coincidencia com os bits K_* de inc/input.h e o que faz a tradugao sair de
 * uma mascara de seis bits; o teste acima e que garante que ela continua
 * valendo. START e alias de KEY_1 (SMSlib.h:302,309) — nao ganha semantico
 * proprio: comeca round/resultado pela mesma tecla do soco, como ja era.
 */
#ifndef INPUT_PAD_H
#define INPUT_PAD_H

#define PAD_LEVEL_MASK  0x3Fu    /* os seis bits de um pad; fora disso e pistola */
#define PAD_B_SHIFT     6u       /* PORT_B_* mora seis posicoes acima de PORT_A_* */

/* held: a palavra inteira de SMS_getKeysHeld(). port: 0 = A (P1), 1 = B (P2).
 * Retorno: apenas bits K_UP|K_DOWN|K_LEFT|K_RIGHT|K_LP|K_HP — nunca K_GUARD
 * (guarda e Down+Tras) nem K_SPECIAL (comando de movimento). */
unsigned char input_pad_levels(unsigned int held, unsigned char port);

#endif /* INPUT_PAD_H */
