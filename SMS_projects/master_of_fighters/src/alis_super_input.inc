/* Two distinct down/forward strokes at the current facing, then a fresh 1.
   A failed full-meter check falls back through the usual special reader. */
uint8_t MOF_SUPER_INPUT(uint8_t p,uint8_t keys,uint8_t face,uint8_t free)
{
    MofSuperInputState *state=&mof_super_inputs[p];
    uint8_t front=face ? MOF_DUEL_RIGHT : MOF_DUEL_LEFT;
    uint8_t dir=keys & 15u;
    if (!free || face!=state->last_face || !state->rhythm) state->gesture=0;
    state->last_face=face;
    if (state->rhythm) --state->rhythm;
    if (free && dir!=state->direction) {
        if (dir==MOF_DUEL_DOWN) { state->gesture=state->gesture==2 ? 3 : 1; state->rhythm=18; }
        else if (dir==front && (state->gesture==1 || state->gesture==3)) ++state->gesture;
        else if (dir && dir!=(front|MOF_DUEL_DOWN)) state->gesture=0;
    }
    state->direction=dir;
    return state->gesture==4 && dir==front && chapter.meter[p]==8;
}
