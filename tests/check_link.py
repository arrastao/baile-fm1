from pathlib import Path
import re,json,struct,hashlib
root=Path(__file__).resolve().parents[1];build=root/'build/dx7';ps=(root/'sdk/Build.ps1').read_text();text=(build/'generated/symbols.txt').read_text();symbols={}
for line in text.splitlines():
 m=re.match(r'^([0-9a-fA-F]+)\s+(?:([0-9a-fA-F]+)\s+)?([A-Za-z])\s+(.+)$',line)
 if m:symbols[m[4]]=dict(address=int(m[1],16),size=int(m[2],16) if m[2] else 0,kind=m[3])
def req(name):assert name in symbols,'missing '+name;return symbols[name]
def quotes(txt):return re.findall(r"'([A-Za-z_][A-Za-z0-9_.$]*)'",txt)
registrations=[]
for name,minsize,stride in re.findall(r"@\('([a-z_]+)',(\d+),(\d+)\)",ps):
 a='_'+name+'_begin';b='_'+name+'_end'
 if a not in symbols:a=name+'_begin';b=name+'_end'
 size=req(b)['address']-req(a)['address'];assert size>=int(minsize) and size%int(stride)==0,(name,size)
 if name=='vfs_ops':assert size==120
 registrations.append(name)
start=ps.index("$required = @(");end=ps.index('foreach ($name in $required)',start)
for name in quotes(ps[start:end]):req(name)
for name in ['CurrentTCB','highCurrentTCB','xIdleTaskHandle']:assert req(name)['size']==4
for name,size in [('fm1_build_id',32),('fm1_update_identity',27)]:assert req(name)['size']==size
for name in ['sdp_send_cmd_iotl','sdp_master_packet_handler','gatt_client_discover_primary_services_by_uuid128']:assert req(name)['size']>16
for name in symbols:
 assert not name.startswith('lv_')
 assert not re.match(r'^(__fat_|fat_sdfile_fat_ops$|jl_fat_vfs_ops$|nor_sdfile_vfs_ops$|sdfile_ext_vfs_ops$)',name),name
pool={d:req('acl_'+d+'_pool_end')['address']-req('acl_'+d+'_pool')['address'] for d in ['tx','rx']};assert pool['tx']>=1024 and pool['rx']>=4096
mp=(build/'sdk.map').read_text();m=re.search(r'0x([0-9a-fA-F]+)[^\r\n]*_MALLOC_SIZE\s*=',mp);assert m,'heap absent';heap=int(m[1],16);assert heap>=49152,heap
synth=json.loads((root/'sdk/synth.json').read_text())
start=ps.index('$callbacks = @(');end=ps.index('foreach ($name in @($synth.sram_optional)',start);callbacks=quotes(ps[start:end])
start=ps.index('$extra = @(');end=ps.index('[IO.Directory]::CreateDirectory',start);callbacks+=quotes(ps[start:end])
callbacks+=synth['sram_required']
callbacks += [n for n in synth['sram_optional']+synth['native_sram_optional'] if n in symbols]
callbacks+=['cpu_enter_sfc_critical','cpu_exit_sfc_critical','enter_spi_code','exit_spi_code','fm1_r_da3931a5b7a8','sfc_drop_cache','fm1_r_0aa010fe1de1','fm1_r_33d5e5b63b6b','fm1_input_tick','fm1_panel_irq','fm1_scan_decode','fm1_key_pin','fm1_encoder_pin','fm1_quadrature']
for name in set(callbacks):assert 0x1c00000<=req(name)['address']<0x1c80000,('not SRAM',name,req(name))
b=(build/'sdk.elf').read_bytes();assert b[:6]==b'\x7fELF\x01\x01';entry=struct.unpack_from('<I',b,24)[0];assert entry==req('_start')['address']==req('_text_rodata_begin')['address']==0x2000120
shoff=struct.unpack_from('<I',b,32)[0];stride,count,si=struct.unpack_from('<HHH',b,46);headers=[struct.unpack_from('<10I',b,shoff+i*stride) for i in range(count)];st=headers[si];strings=b[st[4]:st[4]+st[5]];sections=[]
for h in headers:
 if h[2]&2 and h[5]:
  name=strings[h[0]:].split(b'\0')[0].decode();assert name in ['.text','.data','.bss','.ram0_data','.ram0_bss','.boot_info','.cache_ram_data','.cache_ram_bss'],name
  if h[1]!=8:assert h[4]+h[5]<=len(b)
  sections.append(dict(name=name,address=h[3],bytes=h[5],nobits=h[1]==8))
report=dict(passed=True,entry=hex(entry),runtime_heap_bytes=heap,acl_pools=pool,registration_tables=registrations,audio_and_panel_sram_symbols_checked=len(set(callbacks)),sections=sections,sdk_payload_hashes_verified=True,toolchain='JieLi Linux 20260730.1 / clang 4.0.1, r3, original official flags; portable Blink interpreter',hardware_validated=False)
(build/'generated/structural-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
