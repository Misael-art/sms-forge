#include "engine.h"

static const unsigned char pal_bg[16] = {
    RGB(0,0,0), RGB(3,3,3), RGB(0,1,2), RGB(1,2,3),
    RGB(0,0,1), RGB(2,1,0), RGB(0,2,1), RGB(3,2,0),
    RGB(3,0,0), RGB(0,3,0), RGB(0,0,3), RGB(3,3,1),
    RGB(2,2,2), RGB(1,1,1), RGB(3,1,0), RGB(0,0,0)
};

static const unsigned char pal_sp[16] = {
    RGB(0,0,0), RGB(0,0,0), RGB(3,3,3), RGB(3,2,1),
    RGB(2,1,0), RGB(3,3,1), RGB(2,2,0), RGB(3,1,0),
    RGB(2,0,0), RGB(1,2,0), RGB(0,1,0), RGB(2,2,1),
    RGB(0,1,3), RGB(3,3,0), RGB(3,0,0), RGB(1,1,1)
};

static const char charset[] = CHARSET_STR;

void gfx_clear_nametable(void)
{
    unsigned int i;
    SMS_setNextTileatXY(0, 0);
    for (i = 0; i < 32u * 24u; i++) {
        SMS_setTile(0);
    }
}

void gfx_boot(void)
{
    static const unsigned char tile_blank[32] = {0};
    SMS_loadBGPalette(pal_bg);
    SMS_loadSpritePalette(pal_sp);
    SMS_setBackdropColor(0);
    SMS_loadTiles(tile_blank, 0, 32);
    SMS_load1bppTiles(font_1bpp, TILE_FONT, FONT_1BPP_SIZE, 0, 1);
    SMS_loadTiles(tile_floor, TILE_FLOOR, 32);
    SMS_loadTiles(tile_bar_hp, TILE_BAR_HP, 32);
    SMS_loadTiles(tile_bar_sp, TILE_BAR_SP, 32);
    SMS_loadTiles(tile_bar_empty, TILE_BAR_EMPTY, 32);
}

static unsigned char glyph_of(char c)
{
    unsigned char i;
    if (c >= 'a' && c <= 'z') {
        c = (char)(c - 32);
    }
    for (i = 0; i < FONT_GLYPHS; i++) {
        if (charset[i] == c) {
            return (unsigned char)(TILE_FONT + i);
        }
    }
    return TILE_FONT;
}

void text_at(unsigned char col, unsigned char row, const char *s)
{
    SMS_setNextTileatXY(col, row);
    while (*s) {
        SMS_setTile(glyph_of(*s));
        s++;
    }
}

void text_num(unsigned char col, unsigned char row, unsigned char v)
{
    char buf[4];
    buf[0] = (char)('0' + (v / 100));
    buf[1] = (char)('0' + ((v / 10) % 10));
    buf[2] = (char)('0' + (v % 10));
    buf[3] = 0;
    if (buf[0] == '0') {
        buf[0] = ' ';
        if (buf[1] == '0') {
            buf[1] = ' ';
        }
    }
    text_at(col, row, buf);
}

void text_clear(unsigned char col, unsigned char row, unsigned char n)
{
    unsigned char i;
    SMS_setNextTileatXY(col, row);
    for (i = 0; i < n; i++) {
        SMS_setTile(0);
    }
}
