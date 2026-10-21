from pathlib import Path
import json, sys, hashlib, subprocess, wave, importlib.util
import numpy as np
ROOT=Path('/tmp/smsforge-curation-20261013/audio')
WS=Path('/mnt/sdcard/Projects/SMSForge')
sys.path.insert(0,str(WS/'tools/sms_wrapper'))
import audit_psg_quality as aq
import make_psg_assets as mp
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(name,data):
    p=ROOT/name;p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');return p
tests=[]
for mode in range(8):
    blob=aq._enc([(aq._noise(mode,2 if i%2 else 5),7) for i in range(8)])
    p=ROOT/f'fixture_noise_mode{mode}.psg';p.write_bytes(blob)
    e,d=aq.decode(blob);v,w,m=aq.analyze(e,250)
    expected=float(bool(mode&4));assert m['ruido_branco']==expected
    assert any('M4 ruido:' in x for x in v)==(not bool(mode&4))
    tests.append({'name':f'mode{mode}','sha256':sha(p),'white_fraction':m['ruido_branco'],'violations':v})
# Corrupt feedback predicate and prove public self-check rejects regression.
src=(WS/'tools/sms_wrapper/audit_psg_quality.py').read_text()
mutant=ROOT/'mutant_audit_inverted_noise.py'
mutant.write_text(src.replace('white = sum(1 for _, mode in noise_ctl if mode & 0x04)',
                              'white = sum(1 for _, mode in noise_ctl if not (mode & 0x04))'))
p=subprocess.run([sys.executable,str(mutant),'--self-check'],text=True,capture_output=True)
assert p.returncode==1
put('negative_inverted_feedback.json',{'argv':[str(mutant),'--self-check'],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
# API and CLI both block compression before quality/preview claims.
compressed=ROOT/'fixture_compressed.psg';compressed.write_bytes(bytes([0x08,0x80,0x00,0x38,0x00]))
r=aq.audit_one(str(compressed));assert r['veredito']=='reprova' and 'FORMAT' in r['violacoes'][0]
put('negative_compressed_format.json',r)
dest=ROOT/'compressed_must_not_exist.wav'
try:mp.render_wav(str(dest),compressed.read_bytes())
except ValueError:pass
else:raise AssertionError('compressed rendered')
assert not dest.exists()
# Deterministic feedback preview; requested mode remains visible in saved bytes.
wav_tests=[]
for mode in range(8):
    blob=mp.stream([mp.tone(254,2,15)+mp.noise(mode,2)]+[[]]*49)
    files=[]
    for suffix in ['a','b']:
        dest=ROOT/f'preview_mode{mode}_{suffix}.wav'
        seconds=mp.render_wav(str(dest),blob,rate=44100,fps=50)
        with wave.open(str(dest),'rb') as w:
            assert w.getnframes()==44100 and w.getframerate()==44100
            pcm=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
            assert np.max(np.abs(pcm))>0
        files.append({'path':str(dest),'sha256':sha(dest),'seconds':seconds})
    assert files[0]['sha256']==files[1]['sha256']
    wav_tests.append({'mode':mode,'files':files,'nominal_step_hz':mp._noise_step_hz(mode,254)})
for i in range(4):assert wav_tests[i]['files'][0]['sha256']!=wav_tests[i+4]['files'][0]['sha256']
# A4 preview frequency derives from divisor32, not the old octave error.
tone=ROOT/'preview_a4.wav';mp.render_wav(str(tone),mp.stream([mp.tone(mp._hz_to_period(440),0,2)]+[[]]*49))
with wave.open(str(tone),'rb') as w:pcm=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
freq=np.fft.rfftfreq(len(pcm),1/44100)[np.argmax(np.abs(np.fft.rfft(pcm))[1:])+1]
assert abs(freq-440)<2
put('preview_regressions.json',{'scope':'Approximate offline mono model; no emulator, hardware/cycle/filter/DC certification','mode_tests':wav_tests,'a4_period':mp._hz_to_period(440),'a4_peak_fft_hz':float(freq),'a4_sha256':sha(tone)})
# Corpus paths frozen BEFORE edits; zero assets are rewritten.
before=json.loads((ROOT/'corpus_before.json').read_text());after=[];delta=[]
for old in before['results']:
    p=Path(old['path']);assert sha(p)==old['sha256']
    r=aq.audit_one(str(p));after.append({'path':str(p),'sha256':sha(p),'audit':r})
    if old['audit']['veredito']!=r['veredito'] or old['audit']['violacoes']!=r['violacoes']:
        delta.append({'path':str(p),'sha256':sha(p),'before':old['audit']['violacoes'],'after':r['violacoes']})
put('corpus_after.json',{'count':len(after),'results':after,'read_only_all_hashes_unchanged':True})
put('corpus_delta.json',delta)
selfchecks=[]
for name in ['audit_psg_quality.py','make_psg_assets.py']:
    p=subprocess.run([sys.executable,str(WS/'tools/sms_wrapper'/name),'--self-check'],text=True,capture_output=True)
    assert p.returncode==0
    selfchecks.append({'tool':name,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
put('selfchecks.json',selfchecks)
sources=[WS/p for p in ['tools/sms_wrapper/audit_psg_quality.py','tools/sms_wrapper/make_psg_assets.py','tools/sms_wrapper/.agent/skills/sms-psg-composition.md','tools/sms_wrapper/.agent/skills/sms-psg-audio.md','sdk/devkitSMS/PSGlib/PSGlib.h','sdk/devkitSMS-upstream/PSGlib/src/PSGlib.c','out/blastem_downloads/blastem-source-1.0.0/blastem-2b2a182f4522/psg.c','out/blastem_downloads/blastem-source-1.0.0/blastem-2b2a182f4522/sms.c']]
summary={'status':'passed_focused_audio_source_and_regression_checks','sources':[{ 'path':str(p),'sha256':sha(p)} for p in sources],
 'hardware_feedback':'noise bit2=1 white;0 periodic;low2=3 nominal tone2 source',
 'corpus_streams':len(after),'before_failed':sum(x['audit']['veredito']=='reprova' for x in before['results']),
 'after_failed':sum(x['audit']['veredito']=='reprova' for x in after),'delta_streams':len(delta),
 'changed_source_files':list(map(str,sources[:4])),'project_assets_unchanged':True,'no_emulator_fullsuite_or_saas':True,
 'limits':['Policy over uncompressed event streams, not audible musical quality/AAA','Noise preview model nominal Sega16-bit LFSR; not shared counter/cycle/analog fidelity','SFX predicate is a legacy attenuation heuristic, not waveform click detection','Current game assets retain old authored bytes and may now fail corrected M4; do not regenerate or relabel automatically']}
put('result.json',summary)
print(json.dumps(summary,indent=2))
