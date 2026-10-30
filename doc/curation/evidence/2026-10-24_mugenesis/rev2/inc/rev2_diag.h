/* rev2_diag.h — contrato do consumidor SMS para o pacote versus-cut.
 *
 * ROM diagnostica de telemetria (instrumento, NAO entrega): dois atores reais
 * Ken/Ken, poses AIR completas dos slots P1/P2, streaming de pares TALL de
 * 64 B por VBlank e contagem por scanline. Omissoes declaradas: sem HUD/audio,
 * sem BG hibrido (design wave-4). Desde a wave-5a ha dano/colisao e desde a
 * wave-5b o papel vem do pad fisica (lado 0) e da IA (lado 1), ambos pelo
 * mesmo anel de input.
 *
 * A autoridade de layout e o gerador:
 * tools/sms_wrapper/mugen2sms/generators/fight_runtime_data.py (schema 5).
 * FSM hardcoded aqui NAO e interpretador CNS; e sequencia de script sobre os
 * dados gerados. Sem float, sem malloc (AGENTS.md).
 */
#ifndef REV2_DIAG_H
#define REV2_DIAG_H

/* Um pose/facing no banco de tiles: pagina do slot 2, offset e tamanho. */
typedef struct { unsigned char bank;
                 unsigned int off;
                 unsigned int size; } PoseRef;

/* Frame/Anim espelham exatamente o initializer emitido em
 * versus_scene_runtime.h: dur, pose, meta, metal, clsn, axis, width, height,
 * meta_p2, metal_p2. */
typedef struct { unsigned char dur, pose;
                 const unsigned char *meta, *metal, *clsn, *axis;
                 unsigned char width, height;
                 const unsigned char *meta_p2, *metal_p2; } Frame;

typedef struct { unsigned short id;
                 unsigned char n_frames, loop_start;
                 const Frame *frames; } Anim;

/* Comandos: codigos privados do matcher de input. Ate a wave-5a o diagnostico
 * nao lia input e os nomes existiam so para o initializer gerado compilar;
 * desde a wave-5b eles sao consumidos por src/fight_input.c. */
#define FIGHT_CMD_SPECIAL_UNSUPPORTED 1u
#define FIGHT_CMD_HP 2u
#define FIGHT_CMD_LP 3u
#define FIGHT_CMD_HK 4u
#define FIGHT_CMD_LK 5u

typedef struct { const unsigned char *pattern; unsigned char command; } CommandDef;

#define S_CONTROL   0x01
#define S_AIR       0x02
#define S_HIT       0x04
#define S_BLOCKABLE 0x08

typedef struct { unsigned short id;
                 unsigned char anim, flags;
                 signed int vel;
                 unsigned char dmg; } StateDef;

/* Ordem = REQUIRED_ROLES + close + far (fight_runtime_data.py STATE_ROLE_ORDER). */
enum { ST_IDLE, ST_WALK_F, ST_WALK_B, ST_JUMP, ST_CROUCH, ST_GUARD,
       ST_PUNCH, ST_HP, ST_SPECIAL, ST_KO, ST_KICK, ST_HK,
       ST_PUNCH_CLOSE, ST_HP_CLOSE, ST_KICK_CLOSE, ST_HK_CLOSE,
       ST_PUNCH_FAR, ST_HP_FAR, ST_KICK_FAR, ST_HK_FAR,
       ST_N_STATES };

/* 4 slots de distancia: punch, hp, kick, hk (close/far do mesmo pedido). */
#define AT_N 4

typedef struct {
    const Frame *frames;
    const Anim *anims;
    const StateDef *states;
    const CommandDef *commands;
    unsigned char command_count;
    unsigned char pose_count, pose_base, meta_max_bytes;
    unsigned short max_life;
    signed int jump_vy, gravity;
    unsigned char hitstop, hit_push, guard_push;
    const unsigned short *close_distances_q8;
    const unsigned short *far_distances_q8;
    unsigned short ground_front_q8;
} CharacterData;

/* Origem espelhada no eixo: largura arredondada para multiplo de 8 mantem o
 * mesmo pivot (mesma formula do piloto de escala do wrapper). */
#define FIGHTER_MIRRORED_ORIGIN_X(anchor_x, axis_x, width_px) \
    ((signed int)(anchor_x) - ((signed int)(axis_x) + \
     (signed int)((((unsigned int)(width_px) + 7u) & 0xFFF8u))))

#endif /* REV2_DIAG_H */
