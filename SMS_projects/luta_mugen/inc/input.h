/* input.h — pad físico (Porta A) -> bits K_* + buffer temporal de comandos.
 *
 * Contrato (Plano 2, Task 5):
 *  - input_read(): bits de NÍVEL K_* (fight.h); fight_step calcula as
 *    arestas por keys_prev. O pad de 2 botoes guarda segurando BAIXO+TRAS;
 *    K_GUARD segue como atalho sintetico do roteiro, nao e botao fisico.
 *  - input_tick(): registra a amostra do frame no buffer circular de 16,
 *    ja relativa ao LADO (F=para o oponente, B=para tras), na mesma
 *    codificacao do blob CMD gerado por converters/sms_cmd.py:
 *    nibble baixo = direcional (U1 D2 B4 F8), nibble alto = botao (a1 s2).
 *  - input_pattern_hit(): varredura do buffer do passo mais novo para tras,
 *    janela = byte 1 do blob; flag hold(1) exige o direcional ainda baixo na
 *    amostra corrente; flag release(2) exige o contrario. Passo de direcional
 *    ignora botao e vice-versa (semantica de token unico do MUGEN).
 */
#ifndef INPUT_H
#define INPUT_H

#define INPUT_BUF 16

void input_init(void);
unsigned char input_read(void);
void input_tick(unsigned char keys, unsigned char facing);
unsigned char input_pattern_hit(const unsigned char *pattern);

#endif /* INPUT_H */
