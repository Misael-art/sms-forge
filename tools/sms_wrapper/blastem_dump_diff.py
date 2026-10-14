#!/usr/bin/env python3
"""Compare two audited SMS snapshots; net changes are not writes, timing or causality."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from audit_blastem_sms import audit, fixture
from blastem_diagnostics import palette_codes
from blastem_sms import sha, write_json

LOADED_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

def save_report(output, result, session, protected=()):
    output=Path(output).absolute();session=Path(session).resolve()
    resolved=output.resolve()
    if resolved==session or session in resolved.parents:
        raise ValueError('write diff outside immutable acquisition bundle')
    if output.exists() and (output.is_symlink() or output.stat().st_nlink>1):
        raise ValueError('output is a linked file; choose a new report path')
    for path in protected:
        if path is not None and resolved==Path(path).resolve():
            raise ValueError('report must not overwrite an analysis input')
    # Replace a newly created inode, never truncate an existing destination.
    fd,tmp=tempfile.mkstemp(prefix='.sms-diff-',dir=output.parent)
    try:
        with os.fdopen(fd,'w') as stream:stream.write(json.dumps(result,indent=2)+'\n')
        os.replace(tmp,output)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def differences(before, after, base=0):
    if len(before)!=len(after):raise ValueError('dump sizes differ')
    changed=[i for i,(b,a) in enumerate(zip(before,after)) if b!=a]
    runs=[]
    for i in changed:
        if runs and runs[-1][1]==i:runs[-1][1]=i+1
        else:runs.append([i,i+1])
    # Store full nonzero byte differences, but limit long run display to first32bytes.
    return {'changed_bytes':len(changed), 'offsets':changed,
            'runs':[{'address':base+s,'offset':s,'length':e-s,'before_prefix_hex':before[s:min(e,s+32)].hex(),
                     'after_prefix_hex':after[s:min(e,s+32)].hex(),'prefix_truncated':e-s>32} for s,e in runs]}

def labels_contract(doc, rom_sha):
    if not isinstance(doc,dict) or set(doc)!={'schema','rom_sha256','ranges'} or doc['schema']!='sms_blastem_memory_labels_v1':
        raise ValueError('invalid labels schema')
    if doc['rom_sha256']!=rom_sha:raise ValueError('labels belong to another ROM')
    if not isinstance(doc['ranges'],list) or len(doc['ranges'])>128:raise ValueError('at most128 named ranges')
    names=set()
    for r in doc['ranges']:
        if not isinstance(r,dict) or set(r)!={'name','space','address','length'}:raise ValueError('invalid label fields')
        if not isinstance(r['name'],str) or not r['name'].strip() or len(r['name'])>120 or r['name'] in names:
            raise ValueError('label names must be nonempty and unique')
        names.add(r['name'])
        if r['space'] not in ('ram','vram') or type(r['address']) is not int or type(r['length']) is not int or r['length']<=0:
            raise ValueError('invalid label space/range')
        lo,hi=(0xC000,0xE000) if r['space']=='ram' else (0,0x4000)
        if not lo<=r['address']<r['address']+r['length']<=hi:raise ValueError('label outside SMS address space')
    return doc

def compare(root, first, last, current_rom=None, historical=False, labels=None):
    if sha(__file__)!=LOADED_SHA:raise ValueError('diff tool changed since import; restart analyzer')
    root=Path(root).resolve()
    result=audit(root,current_rom,require_current_tool=not historical)
    if not result['ok']:raise ValueError('bundle audit failed: '+'; '.join(result['errors']))
    meta=json.loads((root/'session.json').read_text());bounds=meta['boundaries']
    if type(first) is not int or type(last) is not int or not 0<=first<last<len(bounds):
        raise ValueError('require ordered snapshot indices in audited timeline')
    report={'schema':'sms_blastem_dump_diff_v1','session_id':meta['session_id'],'rom_sha256':meta['rom_sha256'],
            'analyzer_sha256':LOADED_SHA,
            'session_manifest_sha256':sha(root/'session.json'),'emulator_sha256':meta['emulator_sha256'],
            'eligibility':'historical_record_only' if historical else 'current_acquisition_tools',
            'current_rom_checked':current_rom is not None,
            'first':bounds[first],'last':bounds[last],'vdp_frames_between':bounds[last]['vdp_frame']-bounds[first]['vdp_frame'],
            'scope':'net_snapshot_changes_only_not_bus_writes_unique_art_tiles_timing_or_causality','spaces':{},'source_dumps':[]}
    snapshots=[root/f'snapshots/{i:03d}' for i in (first,last)]
    payload={}
    for name,base in (('ram',0xC000),('vram',0),('vdp_regs',0),('cram_internal',0),('psg_frequency',0),('psg_volume',0)):
        paths=[p/(name+'.bin') for p in snapshots];before,after=[p.read_bytes() for p in paths]
        payload[name]=(before,after);d=differences(before,after,base)
        report['spaces'][name]=d
        for p in paths:report['source_dumps'].append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
    vr=report['spaces']['vram']
    vr['changed_32byte_blocks']=sorted({i//32 for i in vr['offsets']})
    vr['block_scope']='address blocks; includes tilemaps/SAT/nonpattern data; not unique graphics tiles or transfer bytes'
    p0,p1=map(palette_codes,payload['cram_internal'])
    report['palette_changes']=[{'slot':i,'before_sms6':a,'after_sms6':b} for i,(a,b) in enumerate(zip(p0,p1)) if a!=b]
    report['named_ranges']=[]
    if labels is not None:
        path=Path(labels).resolve();content=path.read_bytes();doc=labels_contract(json.loads(content),meta['rom_sha256'])
        report['labels']={'path':str(path),'sha256':hashlib.sha256(content).hexdigest(),'authority':'caller_declared_ranges_ROM_bound_not_authenticated_SDCC_symbols'}
        for r in doc['ranges']:
            base=0xC000 if r['space']=='ram' else 0;start=r['address']-base;end=start+r['length']
            before,after=payload[r['space']]
            report['named_ranges'].append({**r,'delta':differences(before[start:end],after[start:end],r['address'])})
    if sha(__file__)!=LOADED_SHA:raise ValueError('diff tool changed during analysis')
    return report

def self_check():
    a=bytes([1,2,3,4,5]);b=bytes([1,9,8,4,7]);d=differences(a,b,0xC000)
    assert d['changed_bytes']==3 and d['runs'][0]['address']==0xC001 and d['runs'][0]['length']==2
    assert differences(a,a)['changed_bytes']==0
    # Write/restore between observations has zero net delta; never report a write count.
    with tempfile.TemporaryDirectory() as t:
        root,meta=fixture(t)
        before=root/'snapshots/000/ram.bin';after=root/'snapshots/001/ram.bin'
        data=bytearray(after.read_bytes());data[0x700]=8;after.write_bytes(data)
        meta['files']['snapshots/001/ram.bin']={'bytes':len(data),'sha256':sha(after)};write_json(root/'session.json',meta)
        labels=Path(t)/'labels.json'
        doc={'schema':'sms_blastem_memory_labels_v1','rom_sha256':meta['rom_sha256'],
             'ranges':[{'name':'declared_fixture_byte','space':'ram','address':0xC700,'length':1}]};write_json(labels,doc)
        r=compare(root,0,1,historical=True,labels=labels)
        assert r['spaces']['ram']['changed_bytes']==1 and r['named_ranges'][0]['delta']['runs'][0]['after_prefix_hex']=='08'
        linked=Path(t)/'linked-output.json';os.link(before,linked);old=before.read_bytes()
        try:save_report(linked,r,root)
        except ValueError:pass
        else:raise AssertionError('output hardlinked to immutable snapshot accepted')
        assert before.read_bytes()==old
        save_report(Path(t)/'report.json',r,root,(labels,))
        try:save_report(labels,r,root,(labels,))
        except ValueError:pass
        else:raise AssertionError('input labels overwritten')
        for first,last in ((1,0),(0,0),(0,2)):
            try:compare(root,first,last,historical=True)
            except ValueError:pass
            else:raise AssertionError('invalid snapshot indices accepted')
        try:compare(root,0,1,historical=False)
        except ValueError:pass
        else:raise AssertionError('synthetic source eligible for current tools')
        doc['rom_sha256']='0'*64;write_json(labels,doc)
        try:compare(root,0,1,historical=True,labels=labels)
        except ValueError:pass
        else:raise AssertionError('stale labels accepted')
        data[0]^=1;after.write_bytes(data)
        try:compare(root,0,1,historical=True)
        except ValueError:pass
        else:raise AssertionError('tampered dump accepted')
    print('[SELF-CHECK OK] Snapshot net deltas, ordered windows, range identity and tamper rejection')
    return 0

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--self-check',action='store_true')
    ap.add_argument('--session');ap.add_argument('--first',type=int);ap.add_argument('--last',type=int)
    ap.add_argument('--current-rom');ap.add_argument('--historical',action='store_true');ap.add_argument('--labels');ap.add_argument('--json')
    args=ap.parse_args()
    try:
        if args.self_check:return self_check()
        if not args.session or args.first is None or args.last is None:ap.error('--session --first --last required')
        result=compare(args.session,args.first,args.last,args.current_rom,args.historical,args.labels)
        if args.json:
            save_report(args.json,result,args.session,(args.labels,args.current_rom,__file__))
        print(json.dumps(result,indent=2));return 0
    except (OSError,ValueError,KeyError) as e:
        print('[FAIL] '+str(e));return 1

if __name__=='__main__':raise SystemExit(main())
