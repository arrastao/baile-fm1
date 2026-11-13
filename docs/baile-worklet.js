/* BAILE C engine: 44.1 kHz stereo, converted to the browser's output rate. */
class BaileProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super(); const o=options.processorOptions;
    this.c=new WebAssembly.Instance(new WebAssembly.Module(o.wasm),{}).exports;
    this.c._initialize();
    const extra=(o.memory.byteLength-this.c.memory.buffer.byteLength)/65536;
    if(extra>0)this.c.memory.grow(extra);
    new Uint8Array(this.c.memory.buffer).set(new Uint8Array(o.memory));
    this.frame=128; this.phase=0; this.tick=0;this.a=null;this.b=null;
    this.port.onmessage=({data:m})=>{if(m.release)this.c.sim_release();else this.c.sim_control(m.kind,m.index,m.value);};
  }
  next() {
    if(this.frame>=128){this.block=new Float32Array(this.c.memory.buffer,this.c.sim_render(),256);this.frame=0;}
    const at=this.frame++*2;return [this.block[at],this.block[at+1]];
  }
  process(inputs,outputs) {
    const out=outputs[0],c=this.c;if(!out?.length)return true;
    if(!this.a){this.a=this.next();this.b=this.next();}
    for(let i=0;i<out[0].length;i++){
      for(let ch=0;ch<out.length;ch++)out[ch][i]=this.a[ch]+(this.b[ch]-this.a[ch])*this.phase;
      this.phase+=44100/sampleRate;
      while(this.phase>=1){this.phase-=1;this.a=this.b;this.b=this.next();}
    }
    if((this.tick+=out[0].length)>=sampleRate/30){
      this.tick=0;
      const pixels=new Uint16Array(c.memory.buffer,c.sim_pixels(),57600).slice();
      const state=new Uint32Array(c.memory.buffer,c.baile_inspect(),16).slice();
      const leds=new Uint8Array(c.memory.buffer,c.sim_state()+168,41).slice();
      this.port.postMessage({pixels,state,leds},[pixels.buffer,state.buffer,leds.buffer]);
    }
    return true;
  }
}
registerProcessor('baile',BaileProcessor);
