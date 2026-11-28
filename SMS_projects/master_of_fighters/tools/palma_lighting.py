"""Two-byte shading changes to unique authored runway tiles, queued during combat."""
from make_duel_scene02_assets import planar
from pack_alis_magic import decode_stage

# Each exposure changes one scanline inside an existing painted patch. An
# early return to the base tone leaves quiet intervals between the pulses.
# Fields are tile X/Y, pixel row, idle/peak SMS colors and on/off times.
EXPOSURES = {
    "luz sob o trem de pouso": [
        (1,12,4,27,63,2,10), (1,12,5,27,63,3,9), (2,12,2,27,63,4,8),
        (1,12,4,27,63,15,18), (1,12,5,27,63,16,17),
        (1,12,4,27,63,41,48), (2,12,2,27,63,42,47)],
    "reflexo do casco": [
        (6,20,2,22,27,5,12), (7,20,2,22,27,6,13),
        (7,21,3,22,27,11,14), (6,20,4,22,27,43,51),
        (7,20,4,22,27,44,50), (7,22,1,22,27,49,54)],
    "baliza próxima esquerda": [
        (5,21,5,63,27,21,32), (5,21,6,63,27,22,31),
        (6,21,5,63,27,23,30), (5,22,7,63,27,26,34),
        (5,21,5,63,27,55,59)],
    "baliza distante direita": [(29,18,2,63,27,36,40)],
}
STEADY = [(2,18), (25,21), (26,21), (25,22), (26,22)]


def program(data, limits, fighters):
    entries,mapping,patterns,palette=decode_stage(data,limits,fighters)
    events=[(0,0)]*64
    for exposures in EXPOSURES.values():
        for x,y,row,idle,peak,on,off in exposures:
            idx=mapping[y*32+x]
            tile=entries[idx]
            # Direct pattern writes must affect this cell alone. A flipped or
            # reused pattern would also animate unrelated scenery.
            if tile>=448 or sum((entries[i]&511)==tile for i in mapping)!=1:
                raise ValueError(f"Aliased lighting tile at {(x,y)}")
            ink=list(patterns[idx])
            shade,glow=palette.index(idle),palette.index(peak)
            first=row*8
            if shade not in ink[first:first+8]:
                raise ValueError(f"Light missing from {(x,y,row)}")
            base=planar(ink)
            ink[first:first+8]=[glow if c==shade else c for c in ink[first:first+8]]
            lit=planar(ink)
            changed=[i for i,(a,b) in enumerate(zip(base,lit)) if a!=b]
            lo=row*4+(0 if max(changed)%4<=1 else 2)
            if any(i not in (lo,lo+1) for i in changed):
                raise ValueError("Light exceeds one queued VDP word")
            address=0x4000+tile*32+lo
            for tick,source in ((on,lit),(off,base)):
                if events[tick][0]: raise ValueError(f"Two lighting writes on tick {tick}")
                events[tick]=address,int.from_bytes(source[lo:lo+2],'little')
    return events
