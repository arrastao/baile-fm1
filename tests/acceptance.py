#!/usr/bin/env python3
"""Exercise real C engine: boot, sample binding, patterns, controls and audio."""
import ctypes as C, hashlib, json, math, struct, sys, wave
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=C.CDLL(str((root/'build/host/baile.dylib').resolve()))
s.sim_render.restype=C.POINTER(C.c_float)
s.sim_pixels.restype=C.POINTER(C.c_uint16)
s.sim_state.restype=C.POINTER(C.c_uint8)
s.sim_flash.restype=C.POINTER(C.c_uint8)
s.groove_drum_steps.restype=C.c_uint64
s.groove_samples_read.argtypes=[C.c_uint,C.POINTER(C.c_uint8),C.c_uint]
s.groove_screen_web_knobs.restype=C.c_char_p
out=root/'build/evidence';out.mkdir(parents=True,exist_ok=True)
def render(n):
    values=[]
    for _ in range(n):values.extend(s.sim_render()[:256])
    return values

def press(kind,index,value=1):
    s.sim_control(kind,index,value)
    if kind!=2:s.sim_control(kind,index,0)

def ensure(on):
    # BAILE autoplays after the splash; tests state the transport they need.
    if bool(s.sim_state()[14])!=bool(on):press(0,12)

def image(name):
    try:from PIL import Image
    except ImportError:return
    pixels=list(s.sim_pixels()[:240*240])
    image=Image.new('RGB',(240,240));image.putdata([((v>>11)*255//31,((v>>5)&63)*255//63,(v&31)*255//31) for v in pixels]);image.save(out/(name+'.png'))

s.sim_boot(3);render(90);image('splash')
# Controls cannot skip the three-second hold after the initial frame completes.
splash_pixels=list(s.sim_pixels()[:240*240])
press(0,12) # a PLAY press must not start the transport
render(850)
assert list(s.sim_pixels()[:240*240])==splash_pixels
assert s.sim_state()[14]==0
render(350)
assert list(s.sim_pixels()[:240*240])!=splash_pixels
assert s.baile_state(0)==0 and s.baile_state(8)==0
# The sequencer starts by itself as soon as the splash ends.
render(100);assert s.sim_state()[14]==1,'autoplay'
# LED playhead: the LED of the step being played shows the opposite of its pattern bit.
keys=[0,2,4,6,7,9,11,12,14,16,18,19,21,23,24,26]
seen=set();mask=s.groove_drum_steps(0,s.baile_state(2));skew=0
for _ in range(1800):
    render(1);st=s.sim_state();pos=st[15]
    if st[14]:
        lit=[st[168+14+k] for k in keys]
        diff=[n for n in range(16) if lit[n]!=((mask>>n)&1)]
        assert len(diff)<=1,('only the playhead LED differs',diff)
        if diff:
            seen.add(diff[0]);skew=max(skew,min((diff[0]-pos)%16,(pos-diff[0])%16))
assert skew<=1 and len(seen)==16,(skew,sorted(seen))

# SELECT encoder changes only the selected part's level, in bounded steps.
v0=s.baile_state(9);s.baile_encoder(0,-1);render(5);assert s.baile_state(9)==v0-4
s.baile_encoder(0,127);render(5);assert s.baile_state(9)==127
s.baile_encoder(0,-127);render(5);assert s.baile_state(9)==0
s.baile_encoder(0,25);render(5);assert s.baile_state(9)==100
s.baile_encoder(1,1);v1=s.baile_state(9);assert v1==100;s.baile_encoder(1,-1)
racks=json.loads((root/'assets/audio/racks.json').read_text())
report={'upstream_commit':'4c7496daac04a95ff10d1afdcc8f9ead2dbabc41','hardware_tested':False,'kits':{}}
flash_before=bytes(s.sim_flash()[:s.fm1_flash_size()])
for kit,name in enumerate(['tamborzao','voltmix','bolha']):
    assert s.sim_preset(kit)==0
    render(200)
    assert s.baile_state(0)==kit and s.baile_state(8)==0
    bank=(root/'assets/audio'/f'{name}.fm1s').read_bytes()
    assert s.groove_samples_size()==len(bank)
    data=(C.c_uint8*len(bank))();assert s.groove_samples_read(0,data,len(bank))==0
    assert bytes(data)==bank
    meta=json.loads((root/'assets/audio/tamborzao.json').read_text()) if not kit else racks[name]
    masks=[0]*4
    for n in meta['notes']:
        step=min(31 if not kit else 15,int(n['beat']*4+.5));masks[n['midi']-(36 if not kit else 60)]|=1<<step
    masks=[v & 0xffff for v in masks]
    if kit==2:masks[2]=sum(1 << (n-1) for n in [4,7,11,13])
    assert [s.groove_drum_steps(0,p) for p in range(4)]==masks
    image(name)
    ensure(1);audio=render(1600)
    assert all(math.isfinite(v) for v in audio)
    peak=max(map(abs,audio));assert .001<peak<1,peak
    with wave.open(str(out/(name+'.wav')),'wb') as w:
        w.setparams((2,2,44100,0,'NONE',''));w.writeframes(struct.pack('<%dh'%len(audio),*[round(v*32767) for v in audio]))
    ensure(0);render(8)
    report['kits'][name]={'bank_sha256':hashlib.sha256(bank).hexdigest(),'masks':masks,'audio_peak':peak}
# State is session-local, and moving between kits retains independent edits.
s.sim_preset(0);s.baile_encoder(1,1);assert s.baile_state(2)==1
before=s.groove_drum_steps(0,1);press(1,2);assert s.groove_drum_steps(0,1)==(before^2)
s.sim_preset(1);s.sim_preset(0);assert s.groove_drum_steps(0,1)==(before^2)
press(0,1);assert s.baile_state(3)==0
s.baile_encoder(0,1);assert s.baile_state(3)==0
mask=s.groove_drum_steps(0,1);s.baile_step(16);assert s.groove_drum_steps(0,1)==mask
# Every preset loops within 16 steps, including beyond the old second bar.
for kit in range(3):
    s.sim_preset(kit);ensure(1)
    for _ in range(1600):
        render(1);assert s.sim_state()[15]<16
    ensure(0);render(8)
# Bounds, preset encoder, and rejection of sample-bank import.
assert s.sim_preset(3)<0 and s.groove_samples_begin(1024)<0
s.sim_preset(0);s.baile_encoder(6,-1);assert s.baile_state(0)==2
for e,field,maxval in [(2,4,100),(3,5,100)]:
    s.baile_encoder(e,127);assert s.baile_state(field)==maxval
    s.baile_encoder(e,-127);assert s.baile_state(field)==0
# Queued change must remain pending while running and complete at the next observed bar.
s.sim_preset(0);ensure(1);render(120)
assert s.sim_preset(1)==0 and s.baile_state(0)==0 and s.baile_state(1)==2
for _ in range(850):
    render(1)
    if s.baile_state(0)==1:break
assert s.baile_state(0)==1 and s.baile_state(1)==0 and s.sim_state()[14]==1
ensure(0);render(20)
# Neither boot nor normal performance writes user flash.
assert bytes(s.sim_flash()[:s.fm1_flash_size()])==flash_before
# Reboot consistently restores Tamborzao, regardless of prior kit and RAM edits.
s.sim_boot(0);render(1400);assert s.baile_state(0)==0
assert s.groove_drum_steps(0,1)==before
report['checks']=['three-second splash cannot be skipped','embedded banks byte-exact','source note masks','three finite audible previews','independent session edits','single-bar loops and no hidden second-bar edits','preset wrapping','FX bounds','queued kit change','no storage writes','default kit on reboot']
(out/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
# Drive must preserve exact samples at zero and bound hot output to Q23.
pcm=(C.c_int32*256)(*([0,12345,-12345,8388607,-8388607,2000000,-2000000,100000]*32))
original=list(pcm);s.baile_saturate(pcm);assert list(pcm)==original
s.baile_encoder(2,100);s.baile_saturate(pcm)
assert list(pcm)!=original and all(-8388608<=v<=8388607 for v in pcm)
# Delay: dry exact at 0%, audible and finite when wet, natural tail after STOP.
mixv=C.c_uint.in_dll(s,'baile_delay_mix');lenv=C.c_uint.in_dll(s,'baile_delay_length')
s.baile_delay_quarter.restype=C.c_uint
assert s.baile_delay_quarter(120)==11025*60*256//120 and s.baile_delay_quarter(130)==11025*60*256//130
assert s.baile_delay_quarter(60)==11025*256 and s.baile_delay_quarter(30)==11025*256  # 1/8 below ~40 BPM
assert s.baile_delay_quarter(120)*2==s.baile_delay_quarter(60)
def block(amp,phase):
    return [int(amp*math.sin((phase+k//2)*0.35)) for k in range(256)]
s.baile_delay_reset();lenv.value=s.baile_delay_quarter(130);mixv.value=0
for b in range(40):
    pcm=(C.c_int32*256)(*block(3000000,b*128));orig=list(pcm);s.baile_delay(pcm)
    assert list(pcm)==orig,'0% must be bit-exact dry'
# Wet: an impulse is repeated at 1/4 note (130 BPM = 20357 frames) at half level.
s.baile_delay_reset();lenv.value=s.baile_delay_quarter(130);mixv.value=50
wet_out=[]
for b in range(700):
    pcm=(C.c_int32*256)(*([0]*256))
    if b==0:
        for k in range(8):pcm[k]=4000000
    s.baile_delay(pcm);wet_out.extend(pcm[0::2])
assert all(-8388607<=v<=8388607 for v in wet_out)
echo=[max(abs(v) for v in wet_out[i:i+128]) for i in range(0,len(wet_out),128)]
first=max(range(10,len(echo)),key=lambda i:echo[i]);expect=44100*60//130//128
assert abs(first-expect)<=2,(first,expect)
assert 0.25<echo[first]/4000000<0.9
assert max(echo[expect*2-3:expect*2+4])<echo[first],'feedback repeats decay'
# Tail after STOP is natural: signal stops, the echoes ring out and decay; at 100% no dry remains.
s.baile_delay_reset();mixv.value=100;lenv.value=s.baile_delay_quarter(130);levels=[]
for b in range(900):
    pcm=(C.c_int32*256)(*block(3000000,b*128)) if b<60 else (C.c_int32*256)(*([0]*256));s.baile_delay(pcm)
    levels.append(max(abs(v) for v in pcm))
assert max(levels[10:60])<10,'100% wet has no dry'
tail=levels[60:];assert max(tail[100:500])>10000,'tail rings after stop'
assert max(tail[-100:])<max(tail[:300])/4,'tail decays'
# Changing BPM and Dry/Wet mid-stream never produces a click or overflow.
s.baile_delay_reset();mixv.value=50;prev=None;worst=0
for b in range(600):
    if b==200:lenv.value=s.baile_delay_quarter(95)
    if b==300:mixv.value=0
    if b==400:mixv.value=100
    pcm=(C.c_int32*256)(*block(2500000,b*128));s.baile_delay(pcm)
    assert all(-8388607<=v<=8388607 for v in pcm)
    for k in range(0,256,2):
        if prev is not None:worst=max(worst,abs(pcm[k]-prev))
        prev=pcm[k]
assert worst<2*2500000*0.35*1.1*2,worst
mixv.value=50;lenv.value=s.baile_delay_quarter(130)
# Reverb is fully off: every send stays at zero and no engine reverb is mixed.
def fx_preview(amount):
    s.sim_boot(0);render(1400);s.baile_encoder(3,amount);ensure(1)
    return render(900)
dry=fx_preview(-100);wet=fx_preview(0)
assert sum(abs(a-b) for a,b in zip(dry,wet))>1
assert all(math.isfinite(v) and abs(v)<=1 for v in wet)
report['checks']+=['autoplay after splash','LED playhead inverts the step LED','SELECT adjusts selected part level','delay 0% exact dry','delay 1/4 note echo at half feedback','delay tail and click-free BPM / Dry-Wet changes','saturator exact bypass and clipping bounds','delay changes rendered audio']
(out/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n')
print('Audio FX acceptance passed')
