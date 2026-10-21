/* gerado por luta_mugen_gen_stage_hud.py; coordenadas literais para o gate da PNT.
 * O índice vai para a name table como palavra pronta. Somar 256 a um
 * byte virava `inc d` no SDCC e, com D igual ao índice da célula, o
 * bit 8 caía nas células ímpares. */
static const unsigned int hud_tile_word[29] = { 0x0100, 0x0101, 0x0102, 0x0103, 0x0104, 0x0105, 0x0106, 0x0107, 0x0108, 0x0109, 0x010A, 0x010B, 0x010C, 0x010D, 0x010E, 0x010F, 0x0110, 0x0111, 0x0112, 0x0113, 0x0114, 0x0115, 0x0116, 0x0117, 0x0118, 0x0119, 0x011A, 0x011B, 0x011C };
static void hud_put_cell(unsigned char i, unsigned char off) {
    unsigned int tile = hud_tile_word[off];
    switch (i) {
    case 0: SMS_setTileatXY(1, 0, tile); break;
    case 1: SMS_setTileatXY(2, 0, tile); break;
    case 2: SMS_setTileatXY(3, 0, tile); break;
    case 3: SMS_setTileatXY(4, 0, tile); break;
    case 4: SMS_setTileatXY(5, 0, tile); break;
    case 5: SMS_setTileatXY(6, 0, tile); break;
    case 6: SMS_setTileatXY(7, 0, tile); break;
    case 7: SMS_setTileatXY(8, 0, tile); break;
    case 8: SMS_setTileatXY(23, 0, tile); break;
    case 9: SMS_setTileatXY(24, 0, tile); break;
    case 10: SMS_setTileatXY(25, 0, tile); break;
    case 11: SMS_setTileatXY(26, 0, tile); break;
    case 12: SMS_setTileatXY(27, 0, tile); break;
    case 13: SMS_setTileatXY(28, 0, tile); break;
    case 14: SMS_setTileatXY(29, 0, tile); break;
    case 15: SMS_setTileatXY(30, 0, tile); break;
    case 16: SMS_setTileatXY(15, 0, tile); break;
    case 17: SMS_setTileatXY(16, 0, tile); break;
    case 18: SMS_setTileatXY(2, 1, tile); break;
    case 19: SMS_setTileatXY(29, 1, tile); break;
    case 20: SMS_setTileatXY(12, 1, tile); break;
    case 21: SMS_setTileatXY(13, 1, tile); break;
    case 22: SMS_setTileatXY(14, 1, tile); break;
    case 23: SMS_setTileatXY(15, 1, tile); break;
    case 24: SMS_setTileatXY(16, 1, tile); break;
    default: break;
    }
}
