/* BAILE portable FM1 C engine, hosted on the browser audio thread. */
class BaileProcessor extends AudioWorkletProcessor {
 constructor(options){super();this.c=new WebAssembly.Instance(new WebAssembly.Module(options.processorOptions.wasm),{}).exports;
 new Uint8Array(this.c.memory.buffer).set(new Uint8Array(options.processorOptions.snapshot));this.n=0;
 this.port.onmessage=e=>{try{const m=e.data;if(m.type==='control'){this.c.sim_control(...m.args);if(m.args[0]<2)this.c.sim_control(m.args[0],m.args[1],0);}else if(m.type==='preset')this.c.sim_preset(m.value);else if(m.type==='step')this.c.sim_step(m.value,1);this.frame();}catch(error){this.port.postMessage({error:String(error)});}};
 }
 frame(){const c=this.c;this.port.postMessage({state:new Uint32Array(c.memory.buffer,c.baile_state(),17).slice(),pixels:new Uint16Array(c.memory.buffer,c.sim_pixels(),57600).slice()});}
 process(inputs,outputs){const c=this.c,o=outputs[0],p=new Float32Array(c.memory.buffer,c.sim_render(),256);for(let i=0;i<128;i++){o[0][i]=p[i*2];o[1][i]=p[i*2+1];}if(++this.n%16===0)this.frame();return true;}
}
registerProcessor('baile',BaileProcessor);
