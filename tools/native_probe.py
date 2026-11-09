#!/usr/bin/env python3
from pathlib import Path
import os,subprocess,sys,re,json,hashlib,struct
root=Path(__file__).resolve().parents[1]
ROOT=root.parents[1]
tc=root.parent/'jieli-linux-toolchains-20260730.1';build=root/'build/dx7';gen=build/'generated';obj=build/'obj'
for d in [gen,obj]:d.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,BLINK_OVERLAYS=str(ROOT/'work/linux-root')+':/',LD_LIBRARY_PATH=str(ROOT/'work/linux-root/lib/x86_64-linux-gnu')+':'+str(ROOT/'work/linux-root/usr/lib/x86_64-linux-gnu'))
blink=str(ROOT/'work/blink/o/blink/blink')
# Native ELF build via the same macOS/Blink + JieLi Linux route used for Tamborzao 0.1.
# Package with build_macos.py; this is separate from the Windows 2.5.3 toolchain.
# SDK files retain their upstream hashes. Linux toolchain is separately identified in the report.
manifest=json.loads((root/'sdk/manifest.json').read_text())
for file,digest in manifest['files'].items():
 assert hashlib.sha256((root/file).read_bytes()).hexdigest()==digest,file
print('SDK payload hashes verified',flush=True)
def run(tool,args,cwd=build):
 p=subprocess.run([blink,'-m','-j',str(tc/'pi32v2/bin'/tool),*args],cwd=cwd,env=env,capture_output=True,text=True)
 if p.returncode: print(p.stdout+p.stderr,flush=True);raise RuntimeError(tool+' failed')
 if p.stderr.strip():print(p.stderr,flush=True)
 return p.stdout
flags=['-target','pi32v2','-integrated-as','-mcpu=r3','-mfprev1','-Wuninitialized','-Wno-invalid-noreturn','-fno-common','-flto','-fallow-pointer-null','-fprefer-gnu-section','-femulated-tls','-Wno-shift-negative-value','-Wframe-larger-than=2560','-fms-extensions','-fno-unwind-tables','-ffunction-sections','-fdata-sections','-fmessage-length=0','-cl-single-precision-constant','-mllvm','-pi32v2-large-program=true','-D__GCC_PI32V2__','-O2']
for d in ['sdk/include','sdk/include/libc','app/synth','sdk/config','app','app/board']:flags+=['-I'+str(root/d)]
sources=sorted(p for p in (root/'app').rglob('*') if p.suffix in ['.c','.S'] and 'synth' not in p.relative_to(root/'app').parts)
objects=[]
for i,s in enumerate(sources):
 rel=str(s.relative_to(root));output='obj/'+str(i)+'_'+s.stem+'.o';opts=flags.copy()
 if rel in ['app/screen.c','app/transfer.c','app/midi_router.c']:opts+=['-fno-lto']
 if rel=='app/board/panel.c':opts+=['-fno-lto','-fno-pic']
 opts+=['-fwrapv','-fno-fast-math','-ffp-contract=off']
 if rel in ['app/project.c','app/transfer.c','app/samples.c','app/screen.c','app/presets.c','app/midi_router.c','app/fm_factory.c','app/fm_library.c']:opts+=['-Oz']
 if rel=='app/screen.c':opts+=['-fno-inline-functions']
 print('Compile',rel,flush=True)
 run('clang',opts+['-c',str(s),'-o',output])
 objects.append(output)
h=hashlib.sha256()
for p in sorted((root/'app').rglob('*')):
 if p.is_file():h.update(str(p.relative_to(root)).encode()+b':'+p.read_bytes())
ident=h.digest();product=re.search(r'#define FM1_UPDATE_PRODUCT \"([^\"]+)\"',(root/'app/version.h').read_text()).group(1)
(gen/'build_identity.c').write_text('#include "layout.h"\nconst struct fm1_firmware_layout fm1_layout={405504U,7U};\nconst unsigned char fm1_build_id[32]={'+','.join(map(str,ident))+'};\nconst unsigned char fm1_update_identity[27]="'+product+'";\n')
run('clang',flags+['-c','generated/build_identity.c','-o','obj/build_identity.o']);objects+=['obj/build_identity.o']
ld=(root/'sdk/config/linker.ld.in').read_text().replace('@SBC_DECODER@','sbc_decoder\n').replace('@ACL_TX_EXTRA@',' + 1024').replace('@ACL_RX_EXTRA@',' + 4096');(gen/'linker').write_text(ld)
link=['--plugin',str(tc/'pi32v2/bin/LLVMgold.so'),'-o','sdk.elf',*objects,'-flto','--plugin-opt=-pi32v2-always-use-itblock=false','--plugin-opt=-enable-ipra=true','--plugin-opt=-pi32v2-merge-max-offset=4096','--plugin-opt=-pi32v2-enable-simd=true','--plugin-opt=mcpu=r3','--plugin-opt=-global-merge-on-const','--plugin-opt=-inline-threshold=5','--plugin-opt=-inline-max-allocated-size=32','--plugin-opt=-inline-normal-into-special-section=true','--plugin-opt=-dont-used-symbol-list=malloc,free,sprintf,printf,puts,putchar','--plugin-opt=-pi32v2-enable-rep-memop','--plugin-opt=-emulated-tls','--sort-common','--plugin-opt=-pi32v2-large-program=true','--plugin-opt=-pi32v2-csync-before-rti=true','--start-group','--whole-archive','../../sdk/lib/libfm1_engine.a','--no-whole-archive','../../sdk/lib/libc.a','../../sdk/lib/libcompiler_rt.a','--end-group','--gc-sections','-Tgenerated/linker','-M=sdk.map','--undefined=connectivity_wl82_bluetooth_start','--undefined=audio_app_bluetooth_open','--undefined=bt_get_local_name','--undefined=bt_get_mac_addr']
link += ['--undefined='+name for name in ['fm1_ble_scan','fm1_ble_connect','fm1_ble_disconnect','fm1_ble_get_status','fm1_ble_get_device','fm1_bluetooth_get_status']]
print('Link',flush=True);run('ld',link)
elf=(build/'sdk.elf').read_bytes();assert int.from_bytes(elf[24:28],'little')==0x02000120
syms=run('nm',['--print-size','sdk.elf']);(gen/'symbols.txt').write_text(syms)
app=b''
for name in ['text','data','ram0_data','cache_ram_data']:
 out='generated/'+name+'.bin';run('objcopy',['-O','binary','-j','.'+name,'sdk.elf',out]);app+=(build/out).read_bytes()
(gen/'application.bin').write_bytes(app)
limit=0xff000-405504-4096-32768-0x4000-0x120-383-64
report=dict(app_bytes=len(app),limit=limit,fits=len(app)<=limit,build_id=ident.hex(),product=product,toolchain='JieLi Linux 20260730.1 / PI32v2 clang 4.0.1 r3 via Blink on macOS',toolchain_sha256=hashlib.sha256((tc/'pi32v2/bin/clang').read_bytes()).hexdigest(),hardware_validated=False)
(gen/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
