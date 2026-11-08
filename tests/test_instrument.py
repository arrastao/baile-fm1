from pathlib import Path
import ctypes as C, math, json, sys
s=C.CDLL(str(Path(sys.argv[1]).resolve()));s.baile_state.restype=C.POINTER(C.c_uint32);s.sim_render.restype=C.POINTER(C.c_float);s.sim_project_name.restype=C.c_char_p
state=lambda:list(s.baile_state()[:17])
def enc(i,n):s.sim_control(2,i,n)
def button(i):s.sim_control(0,i,1);s.sim_control(0,i,0)
def render(n):
 peak=0
 for _ in range(n):
  a=s.sim_render()[:256];assert all(math.isfinite(v) for v in a);peak=max(peak,max(map(abs,a)))
 return peak
s.sim_boot(1);a=state();assert a[:8]==[0,0,0,0,0,0,130,0],a
assert sum(bin(x).count("1") for x in a[9:13])==22
original=a[9:13];enc(1,2);s.sim_step(5,1);edited=state()[11];assert edited==original[2]^(1<<5)
assert state()[9:11]==original[:2]
enc(4,10);enc(5,12);enc(2,23);enc(3,7)
report={'boot':'Tamborzao','original_hits':22,'isolated_step_edit':True,'kits':[]}
for kit in [1,2,3,0]:
 assert s.sim_preset(kit)==0
 a=state();assert a[0]==kit and a[6]==140 and a[7]==12 and a[4]==23 and a[5]==7,a
 button(12);peak=render(350);button(12);render(5)
 assert 0.001<peak<1,(kit,peak)
 report['kits'].append({'index':kit,'peak':peak})
assert state()[11]==edited
# Reset and check the actual physical key map / page 2.
s.sim_boot(1);enc(1,1);button(1);before=state()[10];s.sim_control(1,0,1);s.sim_control(1,0,0);assert state()[10]==before^(1<<16)
# Quantization: pending stays through the first bar, latest request wins; current cancels.
s.sim_boot(1);button(12);render(40);s.sim_preset(1);assert state()[0:2]==[0,2]
s.sim_preset(2);assert state()[0:2]==[0,3];s.sim_preset(0);assert state()[0:2]==[0,0]
s.sim_preset(3);render(100);assert state()[0:2]==[0,4]
for i in range(900):
 render(1)
 if state()[0]==3:break
else:raise AssertionError('preset never changed')
assert state()[14] in [16,17],state()
# Stop with pending should apply immediately; global tempo persists.
s.sim_preset(1);button(12);render(10);assert state()[0:2]==[1,0]
# Wet/drive alter the output and remain finite at maximum.
s.sim_boot(1);button(12);dry=render(800);s.sim_boot(1);enc(2,100);enc(3,15);button(12);wet=render(1200);assert abs(wet-dry)>.005 and wet<1
report.update(session_edits_preserved=True,tempo_preserved=True,page2_key_verified=True,pending_cancel_and_latest_wins=True,bar_switch_step=16,saturation_and_reverb={'dry_peak':dry,'wet_peak':wet},hardware_tested=False)


# The complete instrument must not rely on any samples in writable storage.
import hashlib
bank=Path('assets/audio/tamborzao.fm1s').read_bytes()
s.sim_flash.restype=C.POINTER(C.c_uint8)
s.groove_samples_read.argtypes=[C.c_uint,C.POINTER(C.c_uint8),C.c_uint]
s.sim_boot(1)
flash=s.sim_flash();flash_bytes=s.fm1_flash_size()
assert flash_bytes==405504
assert bytes(flash[:flash_bytes])==b'\xff'*flash_bytes
assert s.groove_samples_status()==2 and s.groove_samples_size()==len(bank)==65036
restored=bytearray()
for offset in range(0,len(bank),64):
 n=min(64,len(bank)-offset);chunk=(C.c_uint8*n)()
 assert s.groove_samples_read(offset,chunk,n)==0
 restored.extend(chunk)
assert restored==bank
assert s.groove_samples_read(len(bank)-1,(C.c_uint8*2)(),2)!=0
assert s.groove_samples_read(0,(C.c_uint8*65)(),65)!=0
button(12);blank_peak=render(800)
assert .001<blank_peak<1
assert bytes(flash[:flash_bytes])==b'\xff'*flash_bytes
# Existing, unrelated sample data must not replace the factory Tamborzao.
C.memset(flash,0,flash_bytes);s.sim_boot(0)
assert s.groove_samples_status()==2 and state()[0]==0
button(12);polluted_peak=render(800)
assert polluted_peak==blank_peak
assert bytes(flash[:flash_bytes])==b'\x00'*flash_bytes
report.update(embedded_bank_bytes=len(bank),embedded_bank_sha256=hashlib.sha256(bank).hexdigest(),writable_flash_bytes=flash_bytes,blank_flash_boot_and_audio=True,blank_flash_remains_blank=True,unrelated_flash_ignored=True,bank_export_exact=True,blank_flash_peak=blank_peak)
Path('build/host/verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
