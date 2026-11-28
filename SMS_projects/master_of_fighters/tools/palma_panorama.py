"""Fit the Palma arena and panning window into resident SMS patterns."""
from collections import Counter
from functools import lru_cache

import numpy as np
from PIL import Image


def fit_window(card, frames, offsets, palette, limit=448):
    # Compare all four VDP orientations in native CRAM RGB space. Only scenery can
    # lose a pattern. A frequent silhouette costs more to change than a rare glint.
    @lru_cache(None)
    def orientations(raw):
        tile = Image.frombytes("L", (8,8), raw)
        return (raw, tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes(),
                tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes(),
                tile.transpose(Image.Transpose.ROTATE_180).tobytes())

    @lru_cache(None)
    def key(raw):
        return min(orientations(raw))

    def tiles(image):
        for y in range(0,image.height,8):
            for x in range(0,image.width,8):
                yield x,y,image.crop((x,y,x+8,y+8)).tobytes()

    plain = card.point(lambda value: value & 15)
    protected = {key(raw) for _,_,raw in tiles(plain)}
    occurrences = Counter()
    bands = [frame.crop((16,88,160,168)) for frame in frames]
    for band,left in zip(bands,offsets):
        for x,y,raw in tiles(band):
            k = key(raw)
            occurrences[k] += 1
            if 72 <= x+left <= 104 and 42 <= y <= 72:
                protected.add(k)  # Passport officer and scanner, in panorama space.
    keys = sorted(protected | occurrences.keys())
    if len(keys) <= limit:
        return
    if len(protected) > limit:
        raise ValueError("Protected portraits, names and officer exceed the card budget")
    colors = np.array([[(c >> s) & 3 for s in (0,2,4)] for c in palette],dtype=np.int16)
    error = ((colors[:,None]-colors[None,:])**2).sum(axis=2).astype(np.uint8)
    variants = np.frombuffer(b"".join(v for k in keys for v in orientations(k)),np.uint8)
    variants = variants.reshape(len(keys),4,64)
    costs = np.empty((len(keys),len(keys)),np.int32)
    best_flip = np.empty(costs.shape,np.uint8)
    for i,k in enumerate(keys):
        distances = error[variants[i,0],variants].sum(axis=2,dtype=np.int32)
        best_flip[i] = distances.argmin(axis=1)
        costs[i] = distances.min(axis=1)
    np.fill_diagonal(costs, 1000000)
    live = np.ones(len(keys),dtype=bool)
    editable = np.array([k not in protected for k in keys])
    weight = np.array([occurrences[k] for k in keys],dtype=np.int64)
    for _ in range(len(keys)-limit):
        closest = costs[:,live].min(axis=1)
        loss = np.where(editable & live, weight * closest, np.iinfo(np.int64).max)
        live[loss.argmin()] = False
    remaining = np.flatnonzero(live)
    replacements = {}
    for i in np.flatnonzero(~live):
        j = remaining[costs[i,remaining].argmin()]
        target = orientations(keys[j])[best_flip[i,j]]
        for a,b in zip(orientations(keys[i]),orientations(target)):
            replacements[a] = Image.frombytes("L",(8,8),b)
    for frame,band in zip(frames,bands):
        for x,y,raw in tiles(band):
            if raw in replacements:
                frame.paste(replacements[raw],(16+x,88+y))


def fit_apron(counts, fixed, vram_ids, palette, sky, ridge, view_limit):
    """Choose authored motifs by total visible error, including the distant ridge."""
    keys = list(dict.fromkeys([*counts, *fixed]))
    colors = np.asarray(palette,dtype=np.int16)//85
    errors = ((colors[:,None]-colors[None,:])**2).sum(axis=2).astype(np.int16)
    # The single red CRAM step separating the two planes carries the skyline.
    # Its loss is much more visible than an equally small change in the pavement.
    role = np.arange(len(colors))
    red = palette.index((255,0,0))
    hull_shadow = palette.index((85,0,0))
    for color,penalty in ((sky,5),(ridge,10),(red,12),(hull_shadow,6)):
        errors += penalty * ((role==color)[:,None] != (role==color)[None,:])
    tiles = np.frombuffer(b''.join(keys),np.uint8).reshape(-1,64)
    boundary = np.full((8,8),2,dtype=np.int16)
    boundary[[0,7],:] = 3
    boundary[:,[0,7]] = 3
    views = tiles.reshape(-1,8,8)
    def distances_to(orientation):
        flat = orientation.reshape(-1,64)
        return np.array([(errors[t,flat]*boundary.ravel()).sum(axis=1,dtype=np.int32) for t in tiles])
    # Flag order in a Mode 4 name-table entry: none, horizontal, vertical, both.
    costs = np.stack([distances_to(view) for view in
                      (views, views[:,:,::-1], views[:,::-1,:], views[:,::-1,::-1])],axis=1)
    distances = costs.min(axis=1)
    weights = np.array([counts[k] for k in keys],np.int32)
    pool = list(fixed)
    # Fixed patterns include every cloud, the officer, the names and pavement.
    selected = [keys.index(raw) for raw in pool]
    best = distances[:,selected].min(axis=1)
    while len(pool) < len(vram_ids):
        improvement = np.maximum(best[:,None]-distances,0)
        next_index = int((weights @ improvement).argmax())
        if not improvement[:,next_index].any():
            break
        pool.append(keys[next_index])
        selected.append(next_index)
        best = np.minimum(best,distances[:,next_index])
    choices = np.take(costs,selected,axis=2)
    upright = choices[:,0,:]
    best = upright.min(axis=1)
    entries = np.take(vram_ids,upright.argmin(axis=1))
    flips = choices[:,1:,:].reshape(len(keys),-1)
    for _ in range(max(0,view_limit-len(pool))):
        gain = np.maximum(best[:,None]-flips,0)
        j = int((weights @ gain).argmax())
        better = gain[:,j]>0
        if not better.any():
            break
        orientation,slot = divmod(j,len(pool))
        entries[better] = vram_ids[slot] | ((orientation+1)<<9)
        best[better] = flips[better,j]
    return pool,dict(zip(keys,entries.tolist()))
