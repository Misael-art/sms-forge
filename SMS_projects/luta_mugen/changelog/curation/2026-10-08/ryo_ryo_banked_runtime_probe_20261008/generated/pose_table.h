/* gerado por mugen2sms/generators/pose_table.py - nao editar */
#ifndef POSE_TABLE_H
#define POSE_TABLE_H
typedef struct { unsigned char bank; unsigned int off; unsigned char meta_bank;
                 unsigned int meta_r_off, meta_l_off, rows_r_off, rows_l_off; } PoseTiles;
#define POSE_INDEX_RECORD_BYTES 11u
#define POSE_CACHE_RECORD_BYTES 12u
#define KEN_POSE_META_BANK 41u
#define KEN_POSE_BASE 0
#define RYU_POSE_META_BANK 42u
#define RYU_POSE_BASE 94
#define KEN_POSE_MAX_PIECES 35u
#define KEN_POSE_PAIR_IDS 35u
#define KEN_POSE_COUNT 94u
#define KEN_POSE_INDEX_BANK 43u
#define KEN_POSE_INDEX_OFF 0u
#define RYU_POSE_MAX_PIECES 35u
#define RYU_POSE_PAIR_IDS 35u
#define RYU_POSE_COUNT 94u
#define RYU_POSE_INDEX_BANK 43u
#define RYU_POSE_INDEX_OFF 1034u
#endif
