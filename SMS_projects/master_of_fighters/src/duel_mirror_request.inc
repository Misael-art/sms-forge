/* Directory pages are indexed by the frame key in L. Entry bits 0..1 bind
   the VRAM slot. Bit 2 marks a complete packet. FF is never resident. */
static const uint8_t first_unpinned[16]={0,1,0,2,0,1,0,3,0,1,0,2,0,1,0,255};
static const uint8_t costume_bank_offset[2]={0,MOF_MIRROR_COSTUME_BANKS};
static uint8_t request_owner,request_key,request_slot,request_room,request_start,request_count;
static uint8_t *request_pins;
typedef char MirrorDirectoryLayout[sizeof(MirrorIndex)==1792 && sizeof(MirrorUpload)==5 ? 1 : -1];

static uint8_t mirror_request(uint8_t player,uint8_t key,uint8_t *pinned,uint8_t room) __naked
{
    player;key;pinned;room;
    __asm
        ld (_request_owner),a
        add a,#0xcb
        ld h,a
        ld a,l
        ld (_request_key),a
        pop bc                  ; return address
        pop de                  ; caller pin mask
        push hl                 ; preserve directory pointer
        ld hl,#2
        add hl,sp
        ld a,(hl)               ; one-byte room argument
        pop hl
        inc sp
        push bc
        ld (_request_room),a
        ld (_request_pins),de
        ld a,l
        inc a
        jp z,req_missing
        ld a,(hl)
        cp #255
        jr nz,req_bind
        ld a,(_mirror_upload_tiles)
        ld b,a
        ld a,(_request_room)
        cp b
        jp z,req_missing
        ld a,(de)
        ld l,a
        ld h,#0
        ld de,#_first_unpinned
        add hl,de
        ld a,(hl)
        cp #255
        jp z,req_missing
        ld (_request_slot),a
        call req_cache_ptr
        ld e,(hl)               ; evict previous frame from this slot
        ld a,(_request_key)
        ld (hl),a
        inc hl
        ld (hl),#0
        ld a,(_request_owner)
        add a,#0xcb
        ld h,a
        ld l,e
        ld (hl),#255
        ld a,(_request_key)
        ld l,a
        ld a,(_request_slot)
        ld (hl),a
    req_bind:
        ld b,a
        and #3
        ld (_request_slot),a
        ld e,a
        ld d,#0
        ld hl,#_mirror_slot_bits
        add hl,de
        ld a,(hl)
        ld hl,(_request_pins)
        or (hl)
        ld (hl),a
        bit 2,b
        ld a,e
        ret nz
        call req_cache_ptr
        inc hl
        ld b,(hl)               ; number of patterns already staged
        ld a,b
        ld (_request_start),a
        push hl
        ld a,(_request_key)
        ld l,a
        ld h,#0xcd
        ld a,(hl)
        sub b
        ld c,a                  ; remaining frame data
        ld a,(_mirror_upload_tiles)
        ld b,a
        ld a,(_request_room)
        sub b
        cp c
        jr c,req_fits
        ld a,c
    req_fits:
        ld (_request_count),a
        ld e,a
        add a,b
        ld (_mirror_upload_tiles),a
        pop hl
        ld a,e
        or a
        jr z,req_check
        add a,(hl)
        ld (hl),a
        ; Convert the frame packet and start offset to a contiguous VRAM job.
        ld a,(_request_key)
        ld l,a
        ld h,#0
        add hl,hl
        ld de,#0xd000
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,(_request_start)
        ld l,a
        ld h,#0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,de
        ex de,hl
        ld a,(_mirror_upload_count)
        ld l,a
        ld h,#0
        inc a
        ld (_mirror_upload_count),a
        ld c,l
        ld b,h
        add hl,hl
        add hl,hl
        add hl,bc
        ld bc,#_mirror_uploads
        add hl,bc
        ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        push hl
        ld a,(_request_owner)
        ld e,a
        ld d,#0
        ld hl,#_costume_bank_offset
        add hl,de
        ld b,(hl)
        ld a,(_request_key)
        ld l,a
        ld h,#0xcf
        ld a,(hl)
        add a,b
        pop hl
        ld (hl),a
        inc hl
        ld a,(_request_owner)
        add a,a
        add a,a
        ld b,a
        ld a,(_request_slot)
        add a,b
        rrca
        rrca
        rrca
        ld b,a
        ld a,(_request_start)
        add a,b
        ld (hl),a
        inc hl
        ld a,(_request_count)
        ld (hl),a
    req_check:
        ld a,(_request_start)
        ld b,a
        ld a,(_request_count)
        add a,b
        ld b,a
        ld a,(_request_key)
        ld l,a
        ld h,#0xcd
        ld a,(hl)
        cp b
        jr nz,req_missing
        ld a,(_request_owner)
        add a,#0xcb
        ld h,a
        ld a,(_request_slot)
        or #4
        ld (hl),a
        and #3
        ret
    req_missing:
        ld a,#255
        ret
    req_cache_ptr:
        ld l,a                  ; A = slot number
        ld a,(_request_owner)
        add a,a
        add a,a
        add a,l
        add a,a
        ld l,a
        ld h,#0
        ld de,#_mirror_cache
        add hl,de
        ret
    __endasm;
}
