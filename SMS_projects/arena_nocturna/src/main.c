/* arena_nocturna — vertical slice grafico SMSForge
 *
 * VANTA-9 encara o guardiao numa arena orbital de uma tela. O boss ocupa
 * 64x64 na tela (32x32 logicos no modo zoom), quatro vezes a massa do
 * courier, sem exceder o orcamento de sprites do VDP.
 *
 * main.c e responsavel por: init de VDP/VRAM, leitura de teclas, maquina de
 * estados e a ORDEM do frame. Nenhum outro modulo le teclas nem decide
 * quando escrever em VRAM.
 */
#include "game.h"
#include "PSGlib.h"
#include "arena_bg_tiles.h"
#include "title_bg_tiles.h"
#include "hero_tiles.h"
#include "hero_walk_tiles.h"
#include "hero_walk_0_tiles.h"
#include "hero_walk_1_tiles.h"
#include "hero_walk_2_tiles.h"
#include "hero_walk_3_tiles.h"
#include "hero_left_tiles.h"
#include "shot_tiles.h"
#include "counter_tiles.h"
#include "impact_tiles.h"
#include "impact_0_tiles.h"
#include "impact_1_tiles.h"
#include "impact_2_tiles.h"
#include "boss_tl_tiles.h"
#include "boss_tr_tiles.h"
#include "boss_bl_tiles.h"
#include "boss_br_tiles.h"
#include "boss_charge_tl_tiles.h"
#include "boss_charge_tr_tiles.h"
#include "boss_charge_bl_tiles.h"
#include "boss_charge_br_tiles.h"
#include "boss_hurt_tl_tiles.h"
#include "boss_hurt_tr_tiles.h"
#include "boss_hurt_bl_tiles.h"
#include "boss_hurt_br_tiles.h"
#include "boss_dead_tl_tiles.h"
#include "boss_dead_tr_tiles.h"
#include "boss_dead_bl_tiles.h"
#include "boss_dead_br_tiles.h"

/* O conjunto de poses vive na ROM e excede o formato de 16 KB; o cartucho
 * linear de 32 KB continua compatível com a mesma rotina de streaming VRAM. */
SMS_EMBED_SEGA_ROM_HEADER(0, 0);
SMS_EMBED_SDSC_HEADER(1, 1, 2026, 9, 25, "SMSForge", "arena_nocturna",
                                "hero contra guardiao gordo");

/* BG palette: indices da arena.png preparada pelo wrapper. */
static const unsigned char bg_palette[16] = {
    0x00, 0x3F, 0x10, 0x00, 0x11, 0x15, 0x21, 0x2A,
    0x3F, 0x0C, 0x18, 0x24, 0x30, 0x3C, 0x16, 0x06
};
static const unsigned char title_bg_palette[16] = {
    0x00, 0x3F, 0x10, 0x24, 0x20, 0x26, 0x1A, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};
/* Uma subpaleta compartilhada por hero, boss e os dois tipos de disparo. */
static const unsigned char sprite_palette[16] = {
    0x00, 0x00, 0x11, 0x36, 0x14, 0x24, 0x3C, 0x15,
    0x3F, 0x1A, 0x2F, 0x11, 0x22, 0x36, 0x17, 0x16
};

/* Marcadores sempre volatile: sao consumidos por instrumentos externos e o
 * SDCC apagaria escritas em enderecos que o programa nunca le. */
volatile unsigned int  __at(0xC7F0) probe_frame;
volatile unsigned char __at(0xC7F2) probe_hp;
volatile unsigned char __at(0xC7F3) probe_score;
volatile unsigned char __at(0xC7F4) probe_boss;
volatile unsigned char __at(0xC7F5) probe_over;
volatile unsigned char __at(0xC7F6) probe_state;
volatile unsigned char __at(0xC7F7) probe_wave;
/* Cabecalho e eco do canal de runtime (L035): o leitor recusa metrica de
 * payload nao autenticado. probe_keys espelha o byte baixo das teclas do
 * frame — prova de ponta a ponta do caminho de input (host -> IO -> ROM),
 * que o adaptador DAP deste build do Emulicious nao permite escrever. */
volatile unsigned char __at(0xC7E0) probe_magic0;
volatile unsigned char __at(0xC7E1) probe_magic1;
volatile unsigned char __at(0xC7E2) probe_magic2;
volatile unsigned char __at(0xC7E3) probe_magic3;
volatile unsigned char __at(0xC7E4) probe_schema;
volatile unsigned char __at(0xC7F8) probe_keys;
volatile unsigned char __at(0xC7FA) probe_px;
volatile unsigned char __at(0xC7FB) probe_py;

unsigned char g_state;
unsigned char g_demo_mode;
unsigned int  g_frame;
unsigned int  g_score;
unsigned char g_hitstop;
unsigned char g_wave;

static unsigned char player_pose_resident;
static unsigned char boss_pose_resident;
static unsigned char impact_pose_resident = 0xFF;
static unsigned char demo_warmup;

/* Frames por onda. A dificuldade progressiva e eixo congelado no GDD e ate
 * agora nao existia no codigo: o jogo tinha uma unica cadencia do inicio ao
 * fim. Uma onda a cada ~10 s aperta o intervalo de tiro do guardiao. */
#define WAVE_FRAMES 600
#define WAVE_MAX    9

static void match_reset(void) {
    g_score = 0;
    g_hitstop = 0;
    g_wave = 1;
    player_reset();
    boss_reset();
    ent_reset();
    hud_reset();
    demo_warmup = DEMO_WARMUP_FRAMES; /* boot comparavel antes da atração */
}

static void stream_active_animation_tiles(void) {
    unsigned char want_player;
    unsigned char want_boss;
    unsigned char want_impact = 0xFF;
    unsigned char i;

    /* O disparo usa a pose 3 do ciclo autoral: braco projetado, centro de
     * massa adiantado e lenço em arrasto. Ela ocupa o mesmo slot de quatro
     * tiles e funciona como ataque sem aumentar a SAT nem a VRAM ativa. */
    if (g_player.shot_on)
        want_player = 4;
    else if (g_player.facing)
        want_player = 5; /* pose authored para esquerda; sprites não flipam */
    else if (g_player.moving)
        want_player = (unsigned char)(1 + ((g_frame >> 3) & 3));
    else
        want_player = 0;
    if (g_boss.st == BOSS_TELEGRAPH) want_boss = 1;
    else if (g_boss.st == BOSS_HURT) want_boss = 2;
    else if (g_boss.st == BOSS_DEAD) want_boss = 3;
    else want_boss = 0;

    /* Uma pose por vez no slot ativo: 4 tiles do hero, 16 do boss. A ROM
     * guarda as variantes; VRAM recebe apenas a transicao observada. */
    if (want_player != player_pose_resident) {
        switch (want_player) {
        case 1: SMS_loadTiles(hero_walk_0_tiles, HERO_TILE, HERO_WALK_0_TILES_SIZE); break;
        case 2: SMS_loadTiles(hero_walk_1_tiles, HERO_TILE, HERO_WALK_1_TILES_SIZE); break;
        case 3: SMS_loadTiles(hero_walk_2_tiles, HERO_TILE, HERO_WALK_2_TILES_SIZE); break;
        case 4: SMS_loadTiles(hero_walk_3_tiles, HERO_TILE, HERO_WALK_3_TILES_SIZE); break;
        case 5: SMS_loadTiles(hero_left_tiles, HERO_TILE, HERO_LEFT_TILES_SIZE); break;
        default: SMS_loadTiles(hero_tiles, HERO_TILE, HERO_TILES_SIZE); break;
        }
        player_pose_resident = want_player;
    }
    if (want_boss != boss_pose_resident) {
        if (want_boss == 1) {
            SMS_loadTiles(boss_charge_tl_tiles, BOSS_TL_TILE, BOSS_TL_TILES_SIZE);
            SMS_loadTiles(boss_charge_tr_tiles, BOSS_TR_TILE, BOSS_TR_TILES_SIZE);
            SMS_loadTiles(boss_charge_bl_tiles, BOSS_BL_TILE, BOSS_BL_TILES_SIZE);
            SMS_loadTiles(boss_charge_br_tiles, BOSS_BR_TILE, BOSS_BR_TILES_SIZE);
        } else if (want_boss == 2) {
            SMS_loadTiles(boss_hurt_tl_tiles, BOSS_TL_TILE, BOSS_TL_TILES_SIZE);
            SMS_loadTiles(boss_hurt_tr_tiles, BOSS_TR_TILE, BOSS_TR_TILES_SIZE);
            SMS_loadTiles(boss_hurt_bl_tiles, BOSS_BL_TILE, BOSS_BL_TILES_SIZE);
            SMS_loadTiles(boss_hurt_br_tiles, BOSS_BR_TILE, BOSS_BR_TILES_SIZE);
        } else if (want_boss == 3) {
            SMS_loadTiles(boss_dead_tl_tiles, BOSS_TL_TILE, BOSS_TL_TILES_SIZE);
            SMS_loadTiles(boss_dead_tr_tiles, BOSS_TR_TILE, BOSS_TR_TILES_SIZE);
            SMS_loadTiles(boss_dead_bl_tiles, BOSS_BL_TILE, BOSS_BL_TILES_SIZE);
            SMS_loadTiles(boss_dead_br_tiles, BOSS_BR_TILE, BOSS_BR_TILES_SIZE);
        } else {
            SMS_loadTiles(boss_tl_tiles, BOSS_TL_TILE, BOSS_TL_TILES_SIZE);
            SMS_loadTiles(boss_tr_tiles, BOSS_TR_TILE, BOSS_TR_TILES_SIZE);
            SMS_loadTiles(boss_bl_tiles, BOSS_BL_TILE, BOSS_BL_TILES_SIZE);
            SMS_loadTiles(boss_br_tiles, BOSS_BR_TILE, BOSS_BR_TILES_SIZE);
        }
        boss_pose_resident = want_boss;
    }
    for (i = 0; i < MAX_FX; i++) {
        if (!g_fx[i].on) continue;
        if (g_fx[i].timer > 8) want_impact = 0;
        else if (g_fx[i].timer > 4) want_impact = 1;
        else want_impact = 2;
        break;
    }
    if (want_impact != impact_pose_resident) {
        if (want_impact == 0)
            SMS_loadTiles(impact_0_tiles, IMPACT_TILE, IMPACT_0_TILES_SIZE);
        else if (want_impact == 1)
            SMS_loadTiles(impact_1_tiles, IMPACT_TILE, IMPACT_1_TILES_SIZE);
        else if (want_impact == 2)
            SMS_loadTiles(impact_2_tiles, IMPACT_TILE, IMPACT_2_TILES_SIZE);
        impact_pose_resident = want_impact;
    }
}

/* Colisao varrida do tiro contra o boss: cobre o segmento percorrido no
 * frame, nao so o retangulo final. A 8px/frame o teste pontual deixaria o
 * tiro atravessar alvos estreitos sem registrar. */
static void check_shot_vs_boss(void) {
    if (!g_player.shot_on || g_boss.st == BOSS_DEAD) return;
    if (!((g_player.shot_x < g_boss.x + BOSS_W &&
           g_player.shot_x + SHOT_W > g_boss.x) ||
          (g_player.shot_prev_x < g_boss.x + BOSS_W &&
           g_player.shot_prev_x + SHOT_W > g_boss.x))) return;
    if (!(g_player.shot_y < g_boss.y + BOSS_H &&
          g_player.shot_y + SHOT_H > g_boss.y)) return;

    g_player.shot_on = 0;
    boss_hit();
    g_score += 10;
    /* O tiro entra pela esquerda. O burst nasce na borda de contato, não no
     * centro do boss: a primeira metade fica sobre a arena e a segunda
     * recorta a silhueta, mantendo o impacto legível mesmo em ZOOMED. */
    ent_spawn_fx(g_boss.x - 8, g_boss.y + 24);
    g_hitstop = 4;
    hud_mark();
}

static void state_play(unsigned int keys) {
    if (keys & PORT_A_KEY_1) {
        g_state = ST_PAUSE;
        hud_banner(ST_PAUSE);
        return;
    }
    /* O hitstop congela a simulacao, nunca o frame: g_frame continua
     * andando e o VBlank continua acontecendo, senao o instrumento de fps
     * mediria uma queda que o hardware nao teve. */
    if (g_hitstop) { g_hitstop--; return; }

    if ((g_frame % WAVE_FRAMES) == 0 && g_wave < WAVE_MAX) {
        g_wave++;
        hud_mark();
    }

    /* A primeira tecla humana assume o controle mesmo depois de a atração
     * ter começado. Sem esta transição explícita, o hero poderia obedecer à
     * tecla e continuar recebendo a coreografia automática no frame seguinte,
     * tornando a prova de gameplay ambígua. */
    if (g_demo_mode && keys) {
        g_demo_mode = 0;
        demo_warmup = 0;
    }
    if (g_demo_mode && !keys && demo_warmup) {
        demo_warmup--;
    } else if (g_demo_mode && !keys) {
        /* Corredor seguro entre x=44 e x=96: ida e volta com spacing de
         * 32 VBlanks, sem deixar a massa do hero colar no boss. O disparo
         * nasce em fases diferentes do passo para nao parecer preso ao pe. */
        if (g_player.x < 64) keys |= PORT_A_KEY_RIGHT;
        else if (g_player.x > 96) keys |= PORT_A_KEY_LEFT;
        if ((g_frame % 42) == 8) keys |= PORT_A_KEY_2;
    }
    player_update(keys);
    boss_update();
    ent_update();
    check_shot_vs_boss();
}

int main(void) {
    /* Estado inicial vazio: o primeiro toque humano no title precisa gerar
     * uma borda real; 0xFFFF fazia o primeiro botão ser descartado. */
    unsigned int keys, prev_keys = 0, edge;

    SMS_init();
    /* Zoom e recurso real do VDP: hero 32x32 e boss 64x64 na tela. Trocar
     * este modo obriga a refazer TODA a geometria de metasprite e de
     * colisao — ver o bloco de geometria em game.h. */
    SMS_setSpriteMode(SPRITEMODE_ZOOMED);
    SMS_loadBGPalette(title_bg_palette);
    SMS_loadSpritePalette(sprite_palette);
    SMS_autoSetUpTextRenderer();

    /* Toda carga grande acontece com display desligado e antes do laco. */
    SMS_displayOff();
    SMS_useFirstHalfTilesforSprites(1);
    SMS_loadTiles(title_bg_tiles, TITLE_BG_TILE_BASE, TITLE_BG_TILE_BYTES);
    SMS_loadTiles(hero_tiles, HERO_TILE, HERO_TILES_SIZE);
    SMS_loadTiles(shot_tiles, SHOT_TILE, SHOT_TILES_SIZE);
    SMS_loadTiles(counter_tiles, COUNTER_TILE, COUNTER_TILES_SIZE);
    SMS_loadTiles(impact_tiles, IMPACT_TILE, IMPACT_TILES_SIZE);
    SMS_loadTiles(boss_tl_tiles, BOSS_TL_TILE, BOSS_TL_TILES_SIZE);
    SMS_loadTiles(boss_tr_tiles, BOSS_TR_TILE, BOSS_TR_TILES_SIZE);
    SMS_loadTiles(boss_bl_tiles, BOSS_BL_TILE, BOSS_BL_TILES_SIZE);
    SMS_loadTiles(boss_br_tiles, BOSS_BR_TILE, BOSS_BR_TILES_SIZE);
    SMS_loadTileMapArea(0, 0, title_bg_map, 32, 24);
    SMS_setBackdropColor(1);
    /* Trava o scroll horizontal das duas primeiras linhas de tile: e onde a
     * HUD vive. Sem isso o plano inteiro escorrega e o contador de frames
     * — instrumento de medicao — muda por deslocamento, nao por contagem. */
    SMS_VDPturnOnFeature(VDPFEATURE_LOCKHSCROLL);
    SMS_displayOn();

    player_pose_resident = 0;
    boss_pose_resident = 0;

    audio_init();
    match_reset();
    /* Autenticacao do canal de runtime: sem este cabecalho o leitor recusa
     * o payload como probe de outro binario (§26 na direcao contrario — o
     * consumidor que valida a origem, nao so o selador). */
    probe_magic0 = 'S';
    probe_magic1 = 'M';
    probe_magic2 = 'R';
    probe_magic3 = 'T';
    probe_schema = 1;
    /* A cena abre em title nativa, mas entra sozinha na atração para que
     * hero, boss, tiro, contra-ataque e impacto sejam vistos sem depender de
     * um mapa de teclado externo. */
    g_demo_mode = 1;
    g_state = ST_TITLE;
    g_frame = 0;
    audio_music_title();
    SMS_printatXY(12, 8, (const unsigned char *)"VANTA-9");
    SMS_printatXY(9, 17, (const unsigned char *)"NIGHT CORE");
    hud_banner(ST_TITLE);

    for (;;) {
        keys = SMS_getKeysStatus();
        /* Borda de subida: manter o botao 1 pressionado nao pode alternar
         * pausa 60 vezes por segundo. */
        edge = keys & ~prev_keys;
        prev_keys = keys;

        switch (g_state) {
        case ST_TITLE:
            /* Titulo aceita os DOIS botoes. O mapeamento de teclado do
             * emulador nao e o mesmo em toda instalacao, e uma tela de
             * atracao que so responde a um botao vira uma tela travada
             * para quem tem o outro mapeado. */
            if (edge & (PORT_A_KEY_1 | PORT_A_KEY_2)) {
                SMS_displayOff();
                SMS_loadBGPalette(bg_palette);
                SMS_loadTiles(arena_bg_tiles, ARENA_BG_TILE_BASE, ARENA_BG_TILE_BYTES);
                SMS_loadTileMapArea(0, 0, arena_bg_map, 32, 24);
                SMS_displayOn();
                match_reset();
                audio_music(1);
                g_state = ST_PLAY;
                hud_banner(ST_PLAY);
            } else if (g_demo_mode && g_frame >= TITLE_FRAMES) {
                SMS_displayOff();
                SMS_loadBGPalette(bg_palette);
                SMS_loadTiles(arena_bg_tiles, ARENA_BG_TILE_BASE, ARENA_BG_TILE_BYTES);
                SMS_loadTileMapArea(0, 0, arena_bg_map, 32, 24);
                SMS_displayOn();
                match_reset();
                audio_music(1);
                g_state = ST_PLAY;
                hud_banner(ST_PLAY);
            }
            break;
        case ST_PAUSE:
            if (edge & PORT_A_KEY_1) {
                g_state = ST_PLAY;
                hud_banner(ST_PLAY);
            }
            break;
        case ST_OVER:
            if (edge & PORT_A_KEY_1) {
                match_reset();
                audio_music(1);
                g_state = ST_PLAY;
                hud_banner(ST_PLAY);
            }
            break;
        default: {
            unsigned char was = g_state;
            /* ST_PLAY consome o nivel das teclas de movimento, mas a pausa
             * pela borda; por isso recebe keys e testa a borda aqui. */
            if (edge & PORT_A_KEY_1) {
                g_state = ST_PAUSE;
                hud_banner(ST_PAUSE);
                break;
            }
            state_play(keys & ~PORT_A_KEY_1);
            if (g_state == ST_OVER && was == ST_PLAY) {
                /* O estado de fim mantém a cama musical: a captura de áudio
                 * não pode terminar em silêncio antes de provar o mix, e a
                 * tela de derrota/vitória continua com fechamento sonoro. */
                hud_banner(ST_OVER);
            }
            break;
        }
        }

        g_frame++;
        probe_frame = g_frame;
        probe_keys  = (unsigned char)keys;
        probe_px    = (unsigned char)g_player.x;
        probe_py    = (unsigned char)g_player.y;
        probe_hp    = g_player.hp;
        probe_score = (unsigned char)g_score;
        probe_boss  = g_boss.hp;
        probe_over  = (g_state == ST_OVER) ? 1 : 0;
        probe_state = g_state;
        probe_wave  = g_wave;

        SMS_waitForVBlank();
        /* Janela pos-VBlank: e AQUI, e so aqui, que se escreve em VRAM. */
        stream_active_animation_tiles();
        audio_frame();
        /* A arena é estática nesta fatia: manter o BG em zero preserva a
         * HUD/instrumento em qualquer implementação de VDP, inclusive as
         * que não simulam LOCKHSCROLL durante a captura. Movimento visual vem
         * do hero, boss, projéteis e FX. */
        SMS_setBGScrollX(0);
        if (g_state != ST_TITLE) hud_draw();
        SMS_initSprites();
        /* A title e BG-only: nenhum sprite da luta pode vazar para a tela de
         * abertura. Na arena, a ordem de composição também é a prioridade da
         * SAT; o boss entra primeiro para preservar a leitura do alvo. */
        if (g_state != ST_TITLE) {
            /* No SMS, a entrada anterior da SAT vence quando sprites se
             * sobrepõem. FX/projéteis vêm primeiro para que o burst fique
             * na frente do boss; o hero continua por último, preservando a
             * leitura do jogador sem fazer o tiro atravessar o alvo. */
            ent_draw();
            boss_draw();
            player_draw();
        }
        SMS_copySpritestoSAT();
    }
}
