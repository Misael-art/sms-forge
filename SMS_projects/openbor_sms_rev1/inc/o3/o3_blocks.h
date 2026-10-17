/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */
/* bloco da pose = count*64 bytes, lido em 0x8000+addr apos
   SMS_mapROMBank(bank); banco 7 = reserva (D1) */
typedef struct { unsigned char bank; unsigned int addr; } o3_block;
const o3_block o3_ax_blocks[32] = {{2,0},{2,1472},{2,2944},{2,4032},{2,5120},{2,6208},{2,7296},{2,8768},{2,10240},{2,12096},{2,13952},{3,0},{3,1600},{3,3008},{3,4416},{3,5760},{3,7104},{3,8512},{3,9920},{3,11136},{3,12352},{3,13824},{4,0},{4,1280},{4,2560},{4,3904},{4,5248},{4,6528},{4,7808},{4,9024},{4,10240},{4,11392}};
#define O3_AX_BLOCK_COUNT 32
const o3_block o3_long_blocks[28] = {{4,12544},{4,13824},{4,15104},{5,0},{5,1216},{5,2368},{5,3520},{5,4800},{5,6080},{5,7808},{5,9536},{5,11328},{5,13120},{5,14272},{6,0},{6,1344},{6,2688},{6,3904},{3,15296},{6,5120},{6,6208},{6,7680},{6,9152},{6,10368},{6,11584},{6,12608},{6,13632},{6,14848}};
#define O3_LONG_BLOCK_COUNT 28
#define O3_BLOCK_BYTES_PER_CELL 64
#define O3_BANK_FIRST 2
#define O3_BANK_COUNT 5
