#!/usr/bin/env python3
"""SMS diagnostic event contracts and decoded dump viewers (not game art)."""
import argparse
import json
from pathlib import Path
import re
import struct
import tempfile
import wave
import zlib

def normalize_apng(data):
    """Repair only the pinned upstream acTL CRC finalization bug; retain raw file."""
    if data[:8]!=b'\x89PNG\r\n\x1a\n': raise ValueError('not PNG')
    output=bytearray(data);pos=8;repaired=0;declared=None;frames=0;ended=False
    while pos<len(data):
        if pos+12>len(data): raise ValueError('truncated PNG chunk')
        size=struct.unpack_from('>I',data,pos)[0];end=pos+12+size
        if end>len(data): raise ValueError('truncated PNG payload')
        tag=data[pos+4:pos+8];payload=data[pos+8:pos+8+size]
        got=struct.unpack_from('>I',data,pos+8+size)[0];expected=zlib.crc32(tag+payload)
        if tag==b'acTL':
            if size!=8 or declared is not None: raise ValueError('invalid APNG control')
            declared=struct.unpack_from('>I',payload)[0]
        if tag==b'fcTL':frames+=1
        if got!=expected:
            # end_apng patches frame count but leaves the CRC for zero frames.
            initial=zlib.crc32(tag+bytes(4)+payload[4:])
            if tag!=b'acTL' or got!=initial or repaired: raise ValueError('unexpected PNG corruption')
            output[pos+8+size:end]=struct.pack('>I',expected);repaired+=1
        pos=end
        if tag==b'IEND':
            if size or pos!=len(data):raise ValueError('invalid PNG terminator')
            ended=True
    if not ended or declared!=frames or not frames:raise ValueError('APNG frame coverage differs')
    return bytes(output),repaired

def validate_features(doc):
    features = doc.get('diagnostics', {})
    if not isinstance(features, dict) or set(features) - {'cpu_watches', 'vdp_io_breakpoints', 'record_av', 'vgm'}:
        raise ValueError('unknown diagnostics contract')
    for key in ('record_av', 'vgm'):
        if type(features.get(key, False)) is not bool:
            raise ValueError(key + ' must be boolean')
    watches = features.get('cpu_watches', [])
    ports = features.get('vdp_io_breakpoints', [])
    if not isinstance(watches, list) or len(watches) > 8 or not isinstance(ports, list) or len(ports) > 8:
        raise ValueError('at most eight CPU watches and eight VDP I/O sites')
    for w in watches:
        if not isinstance(w, dict) or set(w) != {'address', 'size'} or type(w['address']) is not int or type(w['size']) is not int:
            raise ValueError('CPU watch requires integer address and size')
        if w['size'] not in (1, 2) or not 0xC000 <= w['address'] <= 0xE000-w['size']:
            raise ValueError('CPU write watch outside SMS RAM')
    for p in ports:
        if not isinstance(p, dict) or set(p) != {'pc', 'opcode_hex'} or type(p['pc']) is not int or not 0 <= p['pc'] < 0x3FFF:
            raise ValueError('VDP I/O breakpoint must be in fixed ROM bank')
        # Immediate OUT only: address and port are verifiable without guessing BC/banks.
        if p['opcode_hex'] not in ('d3be', 'd3bf'):
            raise ValueError('qualified VDP I/O opcode is OUT (BE/BF),A')
    return features

def instrumentation(features, rom):
    """Native breakpoint command lists auto-continue; ACK goes after block end."""
    commands = []
    definitions = []
    for w in features.get('cpu_watches', []):
        definitions.append(('cpu_write', w['address'], f'watchpoint {w["address"]} {w["size"]}', f'[{w["address"]}]'))
    for p in features.get('vdp_io_breakpoints', []):
        if rom[p['pc']:p['pc']+2].hex() != p['opcode_hex']:
            raise ValueError('VDP I/O breakpoint opcode differs from frozen ROM')
        definitions.append(('vdp_io_before_out', p['pc'], f'breakpoint {p["pc"]}', '(af >> 8)'))
    for i, (kind, address, create, value) in enumerate(definitions):
        commands += [create, f'variable sms_hits_{i} 0',
            f'commands {i}\nset sms_hits_{i} sms_hits_{i}+1\nprintf "SMSFORGE_EVENT {i} %d %d %d\\n" frame pc {value}\ncontinue\nend']
    return commands, [{'index': i, 'kind': d[0], 'address': d[1],
                       'value_scope': 'debugger_observation_at_trap_not_committed_bus_write'} for i, d in enumerate(definitions)]

def decode_events(log, definitions):
    events = []
    for idx, frame, pc, value in re.findall(r'SMSFORGE_EVENT (\d+) (\d+) (\d+) (\d+)', log):
        i = int(idx)
        if i >= len(definitions):
            raise ValueError('unknown native breakpoint event')
        events.append({'index': i, 'vdp_frame': int(frame), 'pc': int(pc), 'value': int(value)})
    return events

def palette_codes(data):
    if len(data) != 64:
        raise ValueError('expected 32 internal CRAM words')
    # Inverse of vdp.c write_cram's SMS branch. Do not interpret as MD RGB.
    inverse = {((c << 1) & 0xE) | ((c << 2) & 0xE0): c for c in range(64)}
    words = struct.unpack('<32H', data)
    if any(w not in inverse for w in words):
        raise ValueError('CRAM representation not in qualified SMS encoding')
    return [inverse[w] for w in words]

def render_views(folder):
    from PIL import Image
    folder = Path(folder)
    vram = (folder/'vram.bin').read_bytes()
    regs = (folder/'vdp_regs.bin').read_bytes()
    if len(vram) != 16384 or len(regs) != 11 or not regs[0]&4 or regs[1]&0x18:
        raise ValueError('viewers require SMS Mode4 192-line snapshot')
    codes = palette_codes((folder/'cram_internal.bin').read_bytes())
    colors = [(85*(c&3), 85*((c>>2)&3), 85*((c>>4)&3)) for c in codes]
    palette = Image.new('RGB', (256, 32))
    for i, rgb in enumerate(colors):
        palette.paste(rgb, ((i%16)*16, (i//16)*16, (i%16+1)*16, (i//16+1)*16))
    palette.save(folder/'palette_sms.png')
    def pixel(tile, x, y):
        a = tile*32+y*4
        return sum(((vram[a+p] >> (7-x))&1)<<p for p in range(4))
    for bank in (0, 1):
        atlas = Image.new('RGB', (256, 128))
        for tile in range(512):
            for y in range(8):
                for x in range(8):
                    atlas.putpixel(((tile%32)*8+x, (tile//32)*8+y), colors[bank*16+pixel(tile,x,y)])
        atlas.save(folder/f'tiles_palette_{bank}.png')
    # Name table image without scroll, sprites, backdrop or raster effects.
    plane = Image.new('RGB', (256, 224))
    base = (regs[2]&0x0E)<<10
    for row in range(28):
        for col in range(32):
            a = (base+(row*32+col)*2)&0x3FFF
            entry = vram[a] | (vram[(a+1)&0x3FFF]<<8)
            for y in range(8):
                for x in range(8):
                    idx = pixel(entry&511, 7-x if entry&512 else x, 7-y if entry&1024 else y)
                    plane.putpixel((col*8+x, row*8+y), colors[((entry>>11)&1)*16+idx])
    plane.save(folder/'name_table_unscrolled.png')
    info = {'schema': 'sms_blastem_decoded_views_v1', 'palette_codes': codes,
            'vram_addressing': 'native debugger logical SMS addresses; no second swizzle',
            'palette_rgb': 'digital 0/85/170/255 reference; not emulator DAC display colors',
            'name_table_base': base, 'scope': 'diagnostic_views_not_framebuffer_or_art'}
    (folder/'decoded_views.json').write_text(json.dumps(info, indent=2)+'\n')
    return info

def media_summary(root):
    from PIL import Image, ImageChops
    root = Path(root)
    result = {}
    apng = root/'media/native.apng'
    if apng.exists():
        decoded, repaired=normalize_apng(apng.read_bytes())
        normalized=root/'media/decoded.apng'
        if normalized.exists() and normalized.read_bytes()!=decoded:
            raise ValueError('derived APNG differs from raw native capture')
        if not normalized.exists():normalized.write_bytes(decoded)
        with Image.open(normalized) as im:
            n = getattr(im, 'n_frames', 1)
            if im.size != (256,192) or n < 2:
                raise ValueError('native APNG must contain multiple SMS 256x192 frames')
            first = im.convert('RGB'); changed = 0; durations = []
            for i in range(n):
                im.seek(i);durations.append(im.info.get('duration', 0))
                changed += ImageChops.difference(first, im.convert('RGB')).getbbox() is not None
            result['apng'] = {'frames': n, 'size': [256,192], 'different_from_first': changed,
                              'container_duration_ms': sum(durations), 'clock': 'nominal_60Hz_not_realtime_FPS',
                              'raw_preserved':True,'derived_acTL_crc_repairs':repaired}
        with wave.open(str(root/'media/native.wav'), 'rb') as w:
            if w.getsampwidth()!=2 or w.getnchannels()!=2 or w.getnframes()==0:
                raise ValueError('native WAVE is empty or has unqualified format')
            data = w.readframes(w.getnframes())
            peak = max(abs(n[0]) for n in struct.iter_unpack('<h', data))
            result['wave'] = {'sample_rate': w.getframerate(), 'channels': 2, 'sample_frames': w.getnframes(),
                              'duration_seconds': w.getnframes()/w.getframerate(), 'peak': peak,
                              'scope': 'asynchronous_native_mixer_not_frame_locked_or_music_quality'}
    vgm = root/'media/native.vgm'
    if vgm.exists():
        data=vgm.read_bytes()
        if len(data)<0x40 or data[:4]!=b'Vgm ':
            raise ValueError('invalid native VGM')
        result['vgm'] = {'bytes': len(data), 'scope': 'PSG register log_not_audible_mix'}
    return result

def self_check():
    enc = [((c<<1)&14)|((c<<2)&224) for c in range(64)]
    assert len(set(enc))==64
    assert palette_codes(struct.pack('<32H', *enc[:32]))==list(range(32))
    assert palette_codes(struct.pack('<32H', *enc[32:]))==list(range(32,64))
    for bad in ({'cpu_watches':[{'address':0xE000,'size':1}]}, {'record_av':1},
                {'vdp_io_breakpoints':[{'pc':32,'opcode_hex':'d300'}]}, {'raw_commands':'quit'}):
        try: validate_features({'diagnostics':bad})
        except ValueError: pass
        else: raise AssertionError('invalid diagnostics accepted')
    good={'cpu_watches':[{'address':0xC705,'size':1}], 'vdp_io_breakpoints':[{'pc':32,'opcode_hex':'d3bf'}]}
    commands, defs=instrumentation(validate_features({'diagnostics':good}),bytes(32)+bytes.fromhex('d3bf'))
    assert len(defs)==2 and commands[-1].endswith('\nend')
    assert decode_events('SMSFORGE_EVENT 0 123 456 7',defs)[0]['value']==7
    try: instrumentation(good,bytes(34))
    except ValueError: pass
    else: raise AssertionError('stale VDP site accepted')
    with tempfile.TemporaryDirectory() as t:
        f=Path(t);(f/'vram.bin').write_bytes(bytes(16384));(f/'vdp_regs.bin').write_bytes(bytes([4])+bytes(10))
        (f/'cram_internal.bin').write_bytes(bytes(64))
        assert render_views(f)['scope']=='diagnostic_views_not_framebuffer_or_art'
    print('[SELF-CHECK OK] SMS diagnostic watch contracts, 64-color inversion and decoded viewers')
    return 0

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--self-check',action='store_true');ap.add_argument('--snapshot')
    args=ap.parse_args()
    if args.self_check: raise SystemExit(self_check())
    if not args.snapshot: ap.error('--snapshot required')
    print(json.dumps(render_views(args.snapshot),indent=2))
