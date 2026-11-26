#include "../inc/alis_magic.h"
static const uint8_t magic_rest_cue[]={0xc2,0x4a,0xd6,0x39,0xc5,0x47,0xd5,0x39,0xc1,0x44,0xd8,0x3a,0xdf,0xff,0};
static const uint8_t magic_wing_cue[]={0xe5,0xf5,0xc4,0x52,0xd7,0x39,0xfb,0xc1,0x47,0x39,0xe4,0xf5,0x39,0xfc,0x39,0xdf,0xff,0};

void mof_magic_sound(void)
{
    uint8_t event=mof_magic.audio;
    const uint8_t *cue=mof_sfx_special;
    if (event==REST || event==CHAT || event==STUN) cue=magic_rest_cue;
    else if (event==MYAU) cue=magic_wing_cue;
    else if (event==MIRROR) cue=mof_sfx_guard;
    else if (event==SLASH || event==SABER) cue=mof_sfx_blade_hit;
    else if (event==GUARDIANS) cue=mof_sfx_palma;
    mof_magic.audio=0;
    PSGSFXPlay((void *)cue,SFX_CHANNELS2AND3);
}
