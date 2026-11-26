/* A pose with no background cells only needs the two sprite directories.
   Keep the active slot and both forecasts pinned while allocating a miss. */
static uint8_t mirror_pins[2];
static const uint8_t slot_pin[8]={1,2,4,8,1,2,4,8};

static uint8_t mirror_take(uint8_t owner,uint8_t key,uint8_t room)
{
    uint8_t tag;
    if (key==MIRROR_EMPTY) return MIRROR_EMPTY;
    tag=mirror_index.slots[owner][key];
    if (tag<8u && (tag&4u)) return tag&3u;
    return mirror_request(owner,key,&mirror_pins[owner],room);
}

static void mirror_sprite_plan(uint8_t priority,uint8_t first)
{
    uint8_t p,i,room,tag,slot;
    for (i=0;i<2;++i) {
        p=i^first;
        mirror_pins[p]=SLOT_BIT(mirror_live_slot[p]);
        tag=mirror_index.slots[p][mirror_next[p]];
        if (tag<8u) mirror_pins[p]|=slot_pin[tag];
        tag=mirror_index.slots[p][mirror_later[p]];
        if (tag<8u) mirror_pins[p]|=slot_pin[tag];
        slot=mirror_take(p,mirror_wanted[p].frame,MIRROR_UPLOAD_BUDGET);
        mirror_submit[p]=mirror_wanted[p];
        if (slot==MIRROR_EMPTY) {
            mirror_submit[p].frame=mirror_display[p].frame;
            slot=mirror_live_slot[p];
            ++mof_repertoire_delayed;
        } else {
            mirror_pins[p]|=SLOT_BIT(slot);
            if (p==priority && duel.tested_pose[p]<2 && mirror_wanted[p].y)
                mirror_take(p,mirror_next[p],MIRROR_UPLOAD_BUDGET);
        }
        mirror_submit_slot[p]=slot;
    }
    if (mirror_display[0].frame!=mirror_submit[0].frame || mirror_display[1].frame!=mirror_submit[1].frame) {
        mirror_sat_dirty=1;
        mirror_build_sat();
    } else if (mirror_display[0].x!=mirror_submit[0].x || mirror_display[0].y!=mirror_submit[0].y ||
               mirror_display[1].x!=mirror_submit[1].x || mirror_display[1].y!=mirror_submit[1].y) {
        mirror_sat_dirty=1;
        mirror_translate_sat();
    }
    room=mirror_sat_dirty ? MIRROR_UPLOAD_BUDGET : MIRROR_PRELOAD_BUDGET;
    if (!mirror_sat_dirty && mirror_upload_tiles<room) {
        if (mirror_submit[first].frame!=mirror_wanted[first].frame) mirror_take(first,mirror_wanted[first].frame,room);
        p=first^1u;
        if (mirror_submit[p].frame!=mirror_wanted[p].frame) mirror_take(p,mirror_wanted[p].frame,room);
    }
    if (mirror_upload_tiles<room) {
        mirror_take(first,mirror_next[first],room);
        p=first^1u;
        mirror_take(p,mirror_next[p],room);
        if (mirror_upload_tiles<room) {
            mirror_take(first,mirror_later[first],room);
            mirror_take(p,mirror_later[p],room);
        }
    }
}
