import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
vm.runInThisContext(fs.readFileSync('sdk/WebUpdate.js','utf8'));
const file=process.argv[2]||'build/BAILE-0.7-FM1.fwsc';
const bytes=fs.readFileSync(file),pkg=FM1Web.inspectPackage(bytes);
const baseline=fs.readFileSync('../../outputs/Tamborzao-FM1/Tamborzao-FM1-0.1.fwsc');
const old=FM1Web.inspectPackage(baseline);
function decipher(input,key){let out=Buffer.from(input);for(let i=0;i<out.length;i++){out[i]^=key&255;key=((key<<1)^((key&32768)?0x1021:0))&65535;}return out;}
function flash(p){let entry=decipher(p.image.subarray(64,144),65535);let start=entry.readUInt32LE(8),size=entry.readUInt32LE(12);return Buffer.from(p.image.subarray(start,start+size));}
const f=flash(pkg),before=flash(old);
assert.equal(pkg.product,'FM-1_8490170');
assert.deepEqual(f.subarray(0,16384),before.subarray(0,16384));
assert.deepEqual(pkg.loader,old.loader);
const app=fs.readFileSync('build/dx7/generated/application.bin');
let area=Buffer.alloc(f.length-0x4000);
for(let p=0;p<area.length;p+=32)decipher(f.subarray(0x4000+p,0x4000+p+32),0x980f^(p>>>2)).copy(area,p);
assert.deepEqual(area.subarray(0x120,0x120+app.length),app);
const banks={};for(const name of ['tamborzao','voltmix','bolha']){
 const bank=fs.readFileSync(`assets/audio/${name}.fm1s`);assert(app.includes(bank));banks[name]=bank.length;
}
const vmStart=area.readUInt32LE(96+4),vmBytes=area.readUInt32LE(96+8),btif=area.readUInt32LE(160+4);
const reserved=0x120+app.length+383, userAt=area.readUInt32LE(reserved+32+4),userBytes=area.readUInt32LE(reserved+32+8);
assert.equal(userBytes,405504);assert.equal(userAt,0xff000-userBytes);
assert.equal(vmStart,f.length);assert(vmBytes>=32768);assert.equal(vmStart+vmBytes,btif);assert.equal(btif+4096,userAt);
const hash=b=>createHash('sha256').update(b).digest('hex');
const report={firmware:file.split('/').pop(),package_sha256:hash(bytes),bytes:bytes.length,product:pkg.product,sdk_container_crc_checks:true,application_byte_exact:true,boot_identical_to_user_confirmed_tamborzao_01:true,boot_sha256:hash(f.subarray(0,16384)),loader_byte_identical:true,embedded_banks:banks,flash_bytes:f.length,user_at:userAt,user_bytes:userBytes,vm_bytes:vmBytes,hardware_tested:false};
fs.writeFileSync('build/dx7/generated/package-verification.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
