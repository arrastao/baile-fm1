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

def image(name):
    from PIL import Image
    pixels=list(s.sim_pixels()[:240*240])
    image=Image.new('RGB',(240,240));image.putdata([((v>>11)*255//31,((v>>5)&63)*255//63,(v&31)*255//31) for v in pixels]);image.save(out/(name+'.png'))

s.sim_boot(3);render(90);image('splash');render(500)
assert s.baile_state(0)==0 and s.baile_state(8)==0
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
    if kit:masks=[v|(v<<16) for v in masks]
    assert [s.groove_drum_steps(0,p) for p in range(4)]==masks
    image(name)
    press(0,12);audio=render(1600)
    assert all(math.isfinite(v) for v in audio)
    peak=max(map(abs,audio));assert .001<peak<1,peak
    with wave.open(str(out/(name+'.wav')),'wb') as w:
        w.setparams((2,2,44100,0,'NONE',''));w.writeframes(struct.pack('<%dh'%len(audio),*[round(v*32767) for v in audio]))
    press(0,12);render(8)
    report['kits'][name]={'bank_sha256':hashlib.sha256(bank).hexdigest(),'masks':masks,'audio_peak':peak}
# State is session-local, and moving between kits retains independent edits.
s.sim_preset(0);s.baile_encoder(1,1);assert s.baile_state(2)==1
before=s.groove_drum_steps(0,1);press(1,2);assert s.groove_drum_steps(0,1)==(before^2)
s.sim_preset(1);s.sim_preset(0);assert s.groove_drum_steps(0,1)==(before^2)
press(0,1);assert s.baile_state(3)==1
press(1,0);assert s.groove_drum_steps(0,1)==((before^2)^(1<<16))
# Bounds, preset encoder, and rejection of sample-bank import.
assert s.sim_preset(3)<0 and s.groove_samples_begin(1024)<0
s.baile_encoder(6,-1);assert s.baile_state(0)==2
for e,field,maxval in [(2,4,100),(3,5,15)]:
    s.baile_encoder(e,127);assert s.baile_state(field)==maxval
    s.baile_encoder(e,-127);assert s.baile_state(field)==0
# Queued change must remain pending while running and complete at the next observed bar.
s.sim_preset(0);press(0,12);render(120)
assert s.sim_preset(1)==0 and s.baile_state(0)==0 and s.baile_state(1)==2
for _ in range(850):
    render(1)
    if s.baile_state(0)==1:break
assert s.baile_state(0)==1 and s.baile_state(1)==0 and s.sim_state()[14]==1
press(0,12);render(20)
# Neither boot nor normal performance writes user flash.
assert bytes(s.sim_flash()[:s.fm1_flash_size()])==flash_before
# Reboot consistently restores Tamborzao, regardless of prior kit and RAM edits.
s.sim_boot(0);render(500);assert s.baile_state(0)==0
assert s.groove_drum_steps(0,1)==before
report['checks']=['embedded banks byte-exact','source note masks','three finite audible previews','independent session edits','both bars editable','preset wrapping','FX bounds','queued kit change','no storage writes','default kit on reboot']
(out/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
# Drive must preserve exact samples at zero and bound hot output to Q23.
pcm=(C.c_int32*256)(*([0,12345,-12345,8388607,-8388607,2000000,-2000000,100000]*32))
original=list(pcm);s.baile_saturate(pcm);assert list(pcm)==original
s.baile_encoder(2,100);s.baile_saturate(pcm)
assert list(pcm)!=original and all(-8388608<=v<=8388607 for v in pcm)
# Reverb is audible, not merely a changing UI counter.
def fx_preview(amount):
    s.sim_boot(0);render(150);s.baile_encoder(3,amount);press(0,12)
    return render(900)
dry=fx_preview(0);wet=fx_preview(15)
assert sum(abs(a-b) for a,b in zip(dry,wet))>1
assert all(math.isfinite(v) and abs(v)<=1 for v in wet)
report['checks']+=['saturator exact bypass and clipping bounds','reverb changes rendered audio']
(out/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n')
print('Audio FX acceptance passed')
