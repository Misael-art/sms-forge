static uint8_t magic_last_keys[2];

/* On a held direction, only the gesture timeout changes. Keep the normal
   input reader live, including its weak/strong hold and release edges. */
static inline void magic_wait_gesture(uint8_t p)
{
    MofCaster *c=&mof_magic.caster[p];
    mof_magic.locked[p]=0;
    if (c->window) {
        if (duel.fighters[p].state!=MOF_DUEL_READY || duel.body[p].y_offset || duel.body[p].jump_pending)
            c->window=0;
        else --c->window;
    }
}

/* Fixed ROM bridge. The caller executes in ROM slots 0/1 during mapper changes. */
void mof_magic_hurt(const MofDuel *d,uint8_t p,MofDuelBox *box)
{
    SMS_mapROMBank(MOF_RULE_BANK);
    mof_duel_hurt_box(d,p,box);
    SMS_mapROMBank(MOF_MAGIC_BANK);
}

uint8_t mof_magic_contact(MofDuel *d,uint8_t p,uint8_t damage,uint8_t flags)
{
    uint8_t result;
    SMS_mapROMBank(MOF_RULE_BANK);
    result=mof_duel_effect_contact(d,p,damage,flags);
    SMS_mapROMBank(MOF_MAGIC_BANK);
    return result;
}

void mof_magic_publish(void)
{
    uint8_t i;
    for (i=0;i<mof_magic.count;++i) {
        const MofMagicTile *t=&mof_magic.next[i];
        if (mof_magic.upload[i]) {
            SMS_mapROMBank(t->bank);
            UNSAFE_SMS_loadNTiles((const void *)t->address,MOF_BANNER_TILE+i,1);
        }
    }
    for (i=0;i<mof_magic.write_count;++i) {
        SMS_setNextTileatLoc(mof_magic.writes[i].cell);
        SMS_setTile(mof_magic.writes[i].tile);
    }
}

/* Reuse the ordinary dirty HUD packet, so flashing a low bar never
   demands an extra pass over the players during VBlank. */
static void magic_prepare_life(void)
{
    static uint8_t last_phase[2];
    uint8_t p,k,amount,phase,tile,end;
    for (p=0;p<2;++p) {
        amount=current_life[p];
        phase=amount && amount<=25 && (chapter.subsecond&8);
        if (last_phase[p]==phase && (!phase || !hud_count[p])) continue;
        last_phase[p]=phase;
        end=hud_count[p] ? hud_first[p]+hud_count[p] : 0;
        hud_first[p]=0;
        hud_count[p]=end<3 ? 3 : end;
        for (k=0;k<hud_count[p];++k) {
            tile=health_tile(amount);
            if (phase && tile) tile=tile==5 ? 30 : tile+7;
            hud_tiles[p][k]=tile;
            amount=amount>10 ? amount-10 : 0;
        }
    }
}
