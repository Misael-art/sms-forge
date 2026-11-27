/* Shared chapter navigation for both the fixed and the banked presentation. */
static void options(void)
{
    uint8_t row=0, edge;
    menu_page(MOF_PAGE_OPTIONS);
    for (;;) {
        SMS_waitForVBlank();
        SMS_setTileatXY(2,8,row ? 0 : 1);
        SMS_setTileatXY(2,14,row ? 1 : 0);
        SMS_setTileatXY(5,10,chapter.music ? 2 : 0);
        SMS_setTileatXY(18,10,chapter.music ? 0 : 2);
        SMS_setTileatXY(5,16,chapter.target==1 ? 2 : 0);
        SMS_setTileatXY(18,16,chapter.target==2 ? 2 : 0);
        do { edge=menu_input(); } while (!edge);
        if (edge & MOF_DUEL_TWO) return;
        if (edge & (MOF_DUEL_UP|MOF_DUEL_DOWN)) row^=1u;
        else if (edge & (MOF_DUEL_LEFT|MOF_DUEL_RIGHT|MOF_DUEL_ONE)) {
            if (row) chapter.target=3u-chapter.target;
            else {
                chapter.music^=1u;
                menu_opening();
            }
        }
    }
}

void MENU_ENTRY(void)
{
    uint8_t selected=0, previous, edge;
    if (!chapter.target) {
        chapter.target=2;
        chapter.music=1;
        menu_opening();
        menu_title();
    } else menu_opening();
    menu_page(MOF_PAGE_MENU);
    for (;;) {
        SMS_waitForVBlank();
        SMS_setTileatXY(3,16+2*selected,1);
        do { edge=menu_input(); } while (!edge);
        previous=selected;
        if (edge & MOF_DUEL_UP) selected=selected ? selected-1u : 2u;
        else if (edge & MOF_DUEL_DOWN) selected=selected==2 ? 0 : selected+1u;
        else if (edge & MOF_DUEL_ONE) {
            if (selected<2) {
                chapter.story=!selected;
                if (chapter.story) menu_intro();
                return;
            }
            options();
            menu_page(MOF_PAGE_MENU);
        }
        SMS_waitForVBlank();
        SMS_setTileatXY(3,16+2*previous,0);
    }
}
