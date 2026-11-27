/* Page setup and the per-publication environment plan. The multicart
   executes this block in the presentation bank. VDP writes stay in the
   existing fixed-ROM VBlank publisher. */
static uint8_t old_seconds,shutter;
#ifdef MOF_PORT_SKY
static uint8_t flight_clock,flight[2],scanner;
static void port_bird(uint8_t bird, uint8_t advance)
{
    uint8_t phase=flight[bird], column=phase>>2;
#if defined(MOF_PALMA_VERSIONS)
    uint8_t row=active_arena==STAGE_CLASSIC_BANK ? 3u+bird : 3u;
#elif defined(MOF_PORT_CLOUDS)
    const uint8_t row=3; /* Both birds circle in clear sky, 17 columns apart. */
#else
    uint8_t row=3u+bird;
#endif
    uint16_t tile;
    if (advance) {
        phase=(phase+1u)&127u;
        flight[bird]=phase;
        if (!(phase&3u)) chapter_cell(column,row,MOF_PORT_SKY);
        column=phase>>2;
    }
    tile=MOF_PORT_SKY+1u+((phase&3u)<<1);
    chapter_cell(column,row,tile);
    chapter_cell((column+1u)&31u,row,tile+1u);
}
#endif

PORT_ENV_ENTRY(uint8_t reset)
{
    if (reset) {
        old_seconds=255;
        shutter=0;
#ifdef MOF_PORT_SKY
        flight[0]=26;
        flight[1]=94;
        flight_clock=scanner=0;
        port_bird(0,0);
        port_bird(1,0);
#endif
        return;
    }
    if (chapter.phase==MOF_PLAY) {
#ifdef MOF_PORT_SKY
        uint8_t light=(chapter.subsecond<4 || (chapter.subsecond>=9 && chapter.subsecond<13));
        uint8_t scan=(chapter.subsecond>=32 && chapter.subsecond<43);
        if (scanner!=scan) {
            scanner=scan;
#if defined(MOF_PALMA_LIGHTS)
            chapter_cell(mof_port_scene.reader_x,mof_port_scene.reader_y,MOF_PORT_SCANNER+scan);
#elif defined(MOF_PALMA_VERSIONS)
            chapter_cell(reader_x,reader_y,MOF_PORT_SCANNER+scan);
#else
            chapter_cell(MOF_PORT_SCAN_X,MOF_PORT_SCAN_Y,MOF_PORT_SCANNER+scan);
#endif
        }
        if (!(++flight_clock&3u)) port_bird((flight_clock>>2)&1u,1);
#else
        uint8_t light=(chapter.subsecond>=17 && chapter.subsecond<29);
#endif
        if (shutter!=light) {
            shutter=light;
#if defined(MOF_PALMA_LIGHTS)
            chapter_cell(mof_port_scene.signal_x,mof_port_scene.signal_y,MOF_SIGN_TILE+light);
#elif defined(MOF_PALMA_VERSIONS)
            chapter_cell(signal_x,signal_y,MOF_SIGN_TILE+light);
#else
            chapter_cell(MOF_SIGN_X,MOF_SIGN_Y,MOF_SIGN_TILE+light);
#endif
        }
    }
    if (old_seconds!=chapter.seconds) {
        old_seconds=chapter.seconds;
#ifdef MOF_ALIS_MAGIC
        chapter_cell(15,1,MOF_DIGIT_TILE+chapter.seconds/10);
        chapter_cell(16,1,MOF_DIGIT_TILE+chapter.seconds%10);
#else
        SMS_setNextTileatXY(15,1);
        SMS_setTile(MOF_DIGIT_TILE+chapter.seconds/10);
        SMS_setTile(MOF_DIGIT_TILE+chapter.seconds%10);
#endif
    }
#ifdef MOF_PALMA_LIGHTS
    if (chapter.phase==MOF_PLAY && active_arena==STAGE_LIGHT_BANK && (flight_clock&1u))
        mof_port_lighting();
#endif
}
