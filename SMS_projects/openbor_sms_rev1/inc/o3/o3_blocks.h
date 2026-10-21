/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */
/* bloco da pose = count*64 bytes, lido em 0x8000+addr apos
   SMS_mapROMBank(bank); banco 7 = reserva (D1) */
typedef struct { unsigned char bank; unsigned int addr; } o3_block;
const o3_block o3_ax_blocks[32] = {{2,0},{2,1472},{2,2944},{2,4032},{2,5120},{2,6208},{2,7296},{2,8768},{2,10240},{2,11776},{2,13312},{2,14784},{3,0},{3,1408},{3,2816},{3,4160},{3,5504},{3,6912},{3,8320},{3,9536},{3,10752},{3,12224},{3,13696},{3,14976},{4,0},{4,1344},{4,2688},{4,3968},{4,5248},{4,6464},{4,7680},{4,8832}};
#define O3_AX_BLOCK_COUNT 32
const o3_block o3_long_blocks[28] = {{4,9984},{4,11264},{4,12544},{4,13760},{4,14976},{5,0},{5,1152},{5,2432},{5,3712},{5,5440},{5,7168},{5,8960},{5,10752},{5,11904},{5,13056},{5,14400},{6,0},{6,1216},{6,2432},{6,3520},{6,4608},{6,6080},{6,7552},{6,8768},{6,9984},{6,11008},{6,12032},{6,13248}};
#define O3_LONG_BLOCK_COUNT 28
#define O3_BLOCK_BYTES_PER_CELL 64
#define O3_BANK_FIRST 2
#define O3_BANK_COUNT 5
