// Run from the repository root: node tests/web-panel.mjs
// Exercises the shipped browser engine and AudioWorklet, without audio hardware.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const wasm=fs.readFileSync('docs/baile.wasm');
const c=new WebAssembly.Instance(new WebAssembly.Module(wasm),{}).exports;
c._initialize(); c.sim_boot(3);
const state=()=>new Uint32Array(c.memory.buffer,c.baile_inspect(),16).slice();
const leds=()=>new Uint8Array(c.memory.buffer,c.sim_state()+168,41).slice();
const render=seconds=>{for(let i=0;i<Math.ceil(seconds*44100/128);i++)c.sim_render();};
const tap=(kind,index)=>{c.sim_control(kind,index,1);c.sim_control(kind,index,0);render(.03);};
const whites=[0,2,4,6,7,9,11,12,14,16,18,19,21,23,24,26];
render(2.5);c.sim_control(2,6,1);assert.equal(state()[0],0,'splash must ignore controls');
render(1);assert.equal(state()[8],0,'sample banks loaded');
render(.2);assert.equal(state()[13],1,'sequencer autoplays after the splash');
assert.equal(state()[5],0,'delay starts at 0%');
tap(0,12);assert.equal(state()[13],0,'PLAY stops the autoplay');render(.1);
for(let kit=0;kit<3;kit++){
  assert.equal(state()[0],kit);
  for(let part=0;part<4;part++){
    assert.equal(state()[2],part);
    const before=state()[9+part];
    for(let step=0;step<16;step++){
      assert.equal(leds()[14+whites[step]],(before>>>step)&1,'LED matches selected track');
      tap(1,whites[step]);assert.equal(state()[9+part],before^(1<<step));
      tap(1,whites[step]);assert.equal(state()[9+part],before);
    }
    tap(1,1);assert.equal(state()[9+part],before,'black keys do not edit steps');
    c.sim_control(2,1,1);render(.03);
  }
  c.sim_control(2,6,1);render(.03);
}
assert.equal(state()[0],0,'preset wraps to Tamborzao');
// SELECT sets the selected part's level in steps of 4.
const level=state()[15];c.sim_control(2,0,-1);render(.05);assert.equal(state()[15],level-4,'SELECT lowers the part level');c.sim_control(2,0,1);render(.05);assert.equal(state()[15],level);
for(const [encoder,slot,min,max] of [[2,4,0,100],[3,5,0,100],[4,6,30,300],[5,7,0,50]]){
  for(let i=0;i<3;i++)c.sim_control(2,encoder,127);
  assert.equal(state()[slot],max);
  for(let i=0;i<3;i++)c.sim_control(2,encoder,-127);
  assert.equal(state()[slot],min);
}
c.sim_control(2,4,100); // Return tempo from 30 to 130.
tap(0,12);assert.equal(state()[13],1);assert.equal(leds()[12],1);
c.sim_control(2,6,1);assert.equal(state()[0],0,'playing kit changes wait for bar boundary');
render(2);assert.equal(state()[0],1);
tap(0,12);assert.equal(state()[13],0);assert.equal(leds()[12],0);
const mask=state()[9];c.sim_control(1,0,1);c.sim_release();c.sim_control(1,0,1);c.sim_release();
assert.equal(state()[9],mask,'release allows a fresh press');
tap(0,12);
const memory=c.memory.buffer.slice(0);
const report=[];
for(const rate of [44100,48000]){
  let Processor;
  vm.runInNewContext(fs.readFileSync('docs/baile-worklet.js','utf8'),{
    WebAssembly,Float32Array,Uint8Array,Uint16Array,Uint32Array,sampleRate:rate,
    AudioWorkletProcessor:class {constructor(){this.port={postMessage:m=>{this.message=m;}};}},
    registerProcessor:(name,klass)=>{assert.equal(name,'baile');Processor=klass;}
  });
  const p=new Processor({processorOptions:{wasm,memory}}),out=[new Float32Array(128),new Float32Array(128)];
  let peak=0;
  for(let block=0;block<Math.ceil(rate*2/128);block++){
    assert.equal(p.process([], [out]),true);
    for(const channel of out)for(const sample of channel){assert(Number.isFinite(sample));peak=Math.max(peak,Math.abs(sample));}
  }
  assert(peak>.01&&peak<=1,'audible, finite, bounded output');
  assert.equal(p.message.leds.length,41);assert.equal(p.message.pixels.length,57600);
  assert.equal(p.message.state[0],1,'RAM handoff preserves kit');
  p.port.onmessage({data:{kind:3,index:0,value:0}});
  for(let block=0;block<100;block++)p.process([],[out]);
  assert(out.every(channel=>channel.every(sample=>Math.abs(sample)<1e-6)),'MASTER mutes audio');
  report.push({sampleRate:rate,peak:Number(peak.toFixed(4)),masterMute:true});
}
console.log(JSON.stringify({kits:3,tracksPerKit:4,stepsPerTrack:16,actualLEDs:true,splash:true,barBoundarySwitch:true,worklet:report},null,2));
