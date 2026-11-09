#!/usr/bin/env python3
"""Normalize from preserved source WAVs; constant gain, no compression/EQ.

Target strongest 50 ms RMS -16 dBFS, peak ceiling -3 dBFS, maximum boost
18 dB. Decode the final SEA data and enforce the peak ceiling after encoding.
These are measurable level references, not a psychoacoustic loudness guarantee.
"""
import array, hashlib, json, math, struct, subprocess, wave, zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'assets/audio'; O=A/'normalized'; O.mkdir(exist_ok=True)
B=ROOT/'build/normalization';B.mkdir(parents=True,exist_ok=True)
codec=B/'encode_audio'
subprocess.run(['clang','-O2','-I'+str(ROOT/'web/synth'),'-I'+str(ROOT/'sdk/include'),str(ROOT/'tools/encode_audio.c'),str(ROOT/'web/synth/sea_decode.c'),'-o',str(codec)],check=True)
def metrics(x):
 n=min(len(x),1600);acc=sum(v*v for v in x[:n]);best=acc
 for i in range(n,len(x)):
  acc+=x[i]*x[i]-x[i-n]*x[i-n];best=max(best,acc)
 return {'peak_dbfs':20*math.log10(max(map(abs,x))/32768),'attack_rms_dbfs':10*math.log10(best/n/32768**2)}
report={'method':'constant gain; max 50 ms RMS','target_dbfs':-16,'peak_ceiling_dbfs':-3,'max_boost_db':18,'samples':[]}
for kit in ['tamborzao','voltmix','bolha']:
 original=A/'original-banks'/f'{kit}.fm1s';original.parent.mkdir(exist_ok=True)
 if not original.exists():original.write_bytes((A/f'{kit}.fm1s').read_bytes())
 bank=bytearray(original.read_bytes())
 for pad,p in enumerate(sorted(A.glob(kit+'-*.wav'))):
  with wave.open(str(p)) as w:
   assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,32000)
   x=array.array('h',w.readframes(w.getnframes()))
  m=metrics(x);gain=min(-16-m['attack_rms_dbfs'],-3-m['peak_dbfs'],18)
  for attempt in range(4):
   y=array.array('h',(round(v*10**(gain/20)) for v in x));(B/'input.pcm').write_bytes(y.tobytes())
   subprocess.run([str(codec),str(B/'input.pcm'),str(B/'output.sea'),str(B/'decoded.pcm')],check=True)
   decoded=array.array('h');decoded.frombytes((B/'decoded.pcm').read_bytes());after=metrics(decoded)
   if after['peak_dbfs']<=-3+.02:break
   gain-=after['peak_dbfs']+3+.05
  assert after['peak_dbfs']<=-2.98 and len(decoded)==len(x)
  assert max(map(abs,decoded))<32767
  with wave.open(str(O/p.name),'wb') as w:
   w.setparams((1,2,32000,len(y),'NONE','not compressed'));w.writeframes(y.tobytes())
  offset,frames,size=struct.unpack_from('<3I',bank,32+pad*28)
  encoded=(B/'output.sea').read_bytes();assert frames==len(x) and len(encoded)==size
  bank[offset:offset+size]=encoded
  report['samples'].append({'file':p.name,'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'gain_db':gain,'before':m,'decoded_after':after})
 struct.pack_into('<I',bank,12,zlib.crc32(bank[:12]+bytes(8)+bank[20:]))
 (A/f'{kit}.fm1s').write_bytes(bank)
(A/'normalization.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
