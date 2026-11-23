typedef struct {
    uint16_t address;
    uint8_t backdrop;
} MofDuelPntCell;
typedef char MofDuelPntCellLayout[sizeof(MofDuelPntCell) == 3u ? 1 : -1];

static const MofDuelPntCell * volatile rep_pnt_stream;
static volatile uint8_t rep_pnt_length, rep_pnt_first;

/* Stream precomputed addresses only from the VBlank submission path.
   The high byte of every tile ID is 1 because all these tiles are 256..337. */
static void rep_send_pnt(void) __naked
{
    __asm
        ld hl, (_rep_pnt_stream)
        ld a, (_rep_pnt_length)
        ld b, a
        ld a, (_rep_pnt_first)
        ld c, a
        di
    mof_pnt_entry:
        ld a, (hl)
        inc hl
        out (#0xbf), a
        ld a, (hl)
        inc hl
        out (#0xbf), a
        ld a, c
        or a
        jr nz, mof_pnt_overlay
        ld a, (hl)
        jr mof_pnt_write
    mof_pnt_overlay:
        inc c
    mof_pnt_write:
        inc hl
        out (#0xbe), a
        ld a, #1
        out (#0xbe), a
        djnz mof_pnt_entry
        ei
        ret
    __endasm;
}
