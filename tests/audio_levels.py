#!/usr/bin/env python3
"""Check rendered kit consistency and worst-case dry sample summation."""
import ctypes as C, json, math, wave, struct, hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[1];s=C.CDLL(str(r/'build/host/baile.dylib'))
s.sim_render.restype=C.POINTER(C.c_float);s.groove_drum_steps.restype=C.c_uint64
out=r/'build/evidence';report={'kits':{},'hardware_tested':False}
def render(n):
 result=[]
 for _ in range(n):result.extend(s.sim_render()[:256])
 return result
def play():
 s.sim_control(0,12,1);s.sim_control(0,12,0)
def levels(x):
 assert all(math.isfinite(v) for v in x)
 return {'rms_dbfs':10*math.log10(sum(v*v for v in x)/len(x)), 'peak_dbfs':20*math.log10(max(map(abs,x)))}
for kit,name in enumerate(['tamborzao','voltmix','bolha']):
 s.sim_boot(3);render(1500);s.sim_preset(kit);render(100);play();audio=render(3200)
 report['kits'][name]=levels(audio)
 assert max(map(abs,audio))<.95
 with wave.open(str(out/(name+'-normalized.wav')),'wb') as w:
  w.setparams((2,2,44100,0,'NONE',''));w.writeframes(struct.pack('<%dh'%len(audio),*[round(v*32767) for v in audio]))
 play();render(10)
 for part in range(4):
  mask=s.groove_drum_steps(0,part)
  for step in range(16):
   if not (mask>>step)&1:s.baile_step(step)
  s.baile_encoder(1,1)
 play();stress=render(3200)
 assert max(map(abs,stress))<.95
 report['kits'][name]['all_pads_every_step']=levels(stress)
spread=max(v['rms_dbfs'] for v in report['kits'].values())-min(v['rms_dbfs'] for v in report['kits'].values())
assert spread<3,spread
report['kit_rms_spread_db']=spread
for item in json.loads((r/'assets/audio/normalization.json').read_text())['samples']:
 assert hashlib.sha256((r/'assets/audio'/item['file']).read_bytes()).hexdigest()==item['original_sha256']
 assert item['decoded_after']['peak_dbfs']<=-2.98
(out/'audio-levels.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
