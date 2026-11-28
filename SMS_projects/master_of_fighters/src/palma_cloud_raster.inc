/* The high byte is the cloud displacement. An eighth of a pixel per VDP
   frame makes the sky drift even with both fighters in guard. */
static volatile uint16_t port_cloud_phase;

static void port_raster(void) __naked
{
    __asm
        in a,(#0x7e)
        add a,#8
        and #0xf0
        cp #0x20
        jr z,palma_cloud_band
        cp #0x30
        jr z,palma_apron_band
        cp #0xa0
        jr z,palma_runway_band
        cp #0x60
        jr z,palma_fixed_band
        cp #0xc0
        ret nz
    palma_fixed_band:
        xor a
        jr palma_write_scroll
    palma_cloud_band:
        ld hl,(_port_cloud_phase)
        ld de,#0xffe0
        add hl,de
        ld (_port_cloud_phase),hl
        ld a,(_port_apron_scroll)
        sra a
        add a,h
        jr palma_write_scroll
    palma_apron_band:
        ld a,(_port_apron_scroll)
        jr palma_write_scroll
    palma_runway_band:
        ld a,(_port_runway_scroll)
    palma_write_scroll:
        out (#0xbf),a
        ld a,#0x88
        out (#0xbf),a
        ret
    __endasm;
}
