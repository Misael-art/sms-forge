/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */
/* frame = indice no pose set; pose = frame*2 + facing (0=left,1=right);
   land = 0xFF quando nao ha landframe; delays em frames NTSC */
typedef struct { unsigned char frame; unsigned char delay; } o3_aframe;
typedef struct { const o3_aframe *frames; unsigned char count; unsigned char loop; unsigned char land; } o3_anim;
typedef struct { signed char x, y; unsigned char w, h, dmg, pause, depth, first, last; } o3_attack;
const o3_aframe o3_ax_anim_idle[] = {{0,5}};
const o3_aframe o3_ax_anim_walk[] = {{1,7},{2,7}};
const o3_aframe o3_ax_anim_attack1[] = {{3,3},{4,3},{5,3},{6,3},{7,9}};
const o3_aframe o3_ax_anim_jump[] = {{8,21},{9,255}};
const o3_aframe o3_ax_anim_pain2[] = {{10,5},{11,30}};
const o3_aframe o3_ax_anim_fall2[] = {{12,255},{13,5},{14,5},{13,5},{14,1}};
const o3_aframe o3_ax_anim_rise[] = {{14,33},{15,12}};
const o3_aframe o3_ax_anim_death[] = {{14,1}};
#define O3_AX_ANIM_IDLE 0
#define O3_AX_ANIM_WALK 1
#define O3_AX_ANIM_ATTACK1 2
#define O3_AX_ANIM_JUMP 3
#define O3_AX_ANIM_PAIN2 4
#define O3_AX_ANIM_FALL2 5
#define O3_AX_ANIM_RISE 6
#define O3_AX_ANIM_DEATH 7
#define O3_AX_ANIM_COUNT 8
const o3_anim o3_ax_anims[8] = {{o3_ax_anim_idle},1,1,255},{o3_ax_anim_walk},2,1,255},{o3_ax_anim_attack1},5,0,255},{o3_ax_anim_jump},2,0,255},{o3_ax_anim_pain2},2,0,255},{o3_ax_anim_fall2},5,0,1},{o3_ax_anim_rise},2,0,255},{o3_ax_anim_death},1,0,255}};
const o3_attack o3_ax_attack = {0,-62,44,62,7,15,15,1,3};
const o3_aframe o3_long_anim_idle[] = {{0,5}};
const o3_aframe o3_long_anim_walk[] = {{1,7},{2,7}};
const o3_aframe o3_long_anim_attack1[] = {{3,3},{4,3},{5,3},{6,9}};
const o3_aframe o3_long_anim_pain2[] = {{7,5},{8,30}};
const o3_aframe o3_long_anim_fall2[] = {{9,255},{10,5},{11,5},{10,5},{11,1}};
const o3_aframe o3_long_anim_rise[] = {{11,33},{12,12}};
const o3_aframe o3_long_anim_death[] = {{11,5},{13,1},{11,5},{13,1},{11,5},{13,1},{11,4},{13,2},{11,4},{13,2},{11,4},{13,2},{11,3},{13,3},{11,3},{13,3},{11,3},{13,3},{11,2},{13,4},{11,2},{13,4},{11,2},{13,4},{11,1},{13,5},{11,1},{13,5},{11,1},{13,5},{13,30}};
#define O3_LONG_ANIM_IDLE 0
#define O3_LONG_ANIM_WALK 1
#define O3_LONG_ANIM_ATTACK1 2
#define O3_LONG_ANIM_PAIN2 3
#define O3_LONG_ANIM_FALL2 4
#define O3_LONG_ANIM_RISE 5
#define O3_LONG_ANIM_DEATH 6
#define O3_LONG_ANIM_COUNT 7
const o3_anim o3_long_anims[7] = {{o3_long_anim_idle},1,1,255},{o3_long_anim_walk},2,1,255},{o3_long_anim_attack1},4,0,255},{o3_long_anim_pain2},2,0,255},{o3_long_anim_fall2},5,0,1},{o3_long_anim_rise},2,0,255},{o3_long_anim_death},31,0,255}};
const o3_attack o3_long_attack = {0,-46,40,46,5,10,15,1,2};
