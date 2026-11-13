'use strict';
// Panel coordinates follow the physical FM-1 diagram in Felucca/docs/controls.jpg.
// Matrix mapping also checked against joakimeriksson/fm1-emu panel.rs.
const $=id=>document.getElementById(id),device=$('device');
const names=[['BUMBO','ATAQUE','CONGA SLAP','CONGA GRAVE'],['BUMBO','CAIXA','CHIMBAL','ARO'],['BUMBO','CAIXA','BRILHANTE','RITMADA']];
const kits=['Tamborzão','Voltmix','Beat Bolha'];
const white=[0,2,4,6,7,9,11,12,14,16,18,19,21,23,24,26];
const black=[[1,0],[3,1],[5,2],[8,4],[10,5],[13,7],[15,8],[17,9],[20,11],[22,12],[25,14]];
const knobSpecs=[
 {name:'MASTER',hint:'Volume',x:7.2,y:15,px:13.5,py:11.6,kind:3,index:0,min:0,max:1023,value:1023},
 {name:'SELECT',hint:'Volume da trilha',x:18.1,y:15,px:32.5,py:11.6,kind:2,index:0,min:0,max:127,value:0},
 {name:'PRESETS',hint:'Kit',x:7.2,y:33,px:13.5,py:20.7,kind:2,index:6,min:0,max:2,value:0,cyclic:true},
 {name:'ALGORITHM',hint:'Trilha',x:18.1,y:33,px:32.5,py:20.7,kind:2,index:1,min:0,max:3,value:0,cyclic:true},
 ...['Saturação','Delay','BPM','Swing'].map((hint,i)=>({name:'KNOB'+(i+1),hint,x:58+i*11.4,y:15,px:19.9+i*22.33,py:39.5,kind:2,index:i+2,min:i===2?30:0,max:[100,100,300,50][i],value:i===2?130:0,state:i+4}))
];
let core,wasm,engine,audio,starting,timer,transferring=false,ready=false,queue=[],state=new Uint32Array(16);
const pointers=new Map(),held=new Map(),matrix=new Map();
const ctx=$('lcd').getContext('2d'),bitmap=ctx.createImageData(240,240);
// Each control has a landscape box and a portrait box (percent of the device); CSS animates between them.
function place(el,land,port){
 ['l','t','w','h'].forEach((n,i)=>{if(land[i]!==undefined)el.style.setProperty('--'+n,land[i]+'%');});
 ['pl','pt','pw','ph'].forEach((n,i)=>{if(port[i]!==undefined)el.style.setProperty('--'+n,port[i]+'%');});
}
let half=0;const keyEls=[];
function layoutKeys(){
 for(const k of keyEls)place(k.el,[],[k.px(half),k.py,10,k.ph]);
 if(minimap)minimap.style.setProperty('--half',half);
}
let minimap=null,minimapCells=[];
function mode(){
 const small=Math.min(innerWidth,innerHeight)<=600;
 // Desktop (mouse + hover) always keeps the landscape device, however narrow the window is.
 const desktop=matchMedia('(hover:hover) and (pointer:fine)').matches;
 const mobile=matchMedia('(pointer:coarse)').matches||(small&&!desktop);
 const portrait=mobile&&innerHeight>innerWidth;
 const wasPortrait=document.documentElement.classList.contains('portrait-mode');
 document.documentElement.classList.toggle('instrument-mode',mobile);
 document.documentElement.classList.toggle('portrait-mode',portrait);
  if(wasPortrait!==portrait){releaseAll();fullscreenTried=false;}
}
let fullscreenTried=false;
function fullscreen(){
 if(fullscreenTried||!document.documentElement.classList.contains('instrument-mode')||innerHeight>innerWidth)return;
 fullscreenTried=true;
 if(!document.fullscreenElement&&document.documentElement.requestFullscreen)
   document.documentElement.requestFullscreen({navigationUI:'hide'}).catch(()=>{});
}
let orientationLocked=false;
function announce(text){$('announcer').textContent=text;}
function failure(text){$('boot-status').hidden=false;$('boot-status').textContent=text;}
function command(kind,index,value){
 if(!ready)return;
 const m={kind,index,value};
 if(transferring)queue.push(m);
 else if(engine)engine.port.postMessage(m);
 else{core.sim_control(kind,index,value);read(core);}
}
function hold(el,on){
 const key=el.dataset.kind+':'+el.dataset.index,n=held.get(key)||0;
 if(on){held.set(key,n+1);if(!n)command(+el.dataset.kind,+el.dataset.index,1);}
 else if(n){if(n===1){held.delete(key);command(+el.dataset.kind,+el.dataset.index,0);}else held.set(key,n-1);}
 el.classList.toggle('held',held.has(key));
}
function releaseAll(){
 for(const p of pointers.values())if(p.el)p.el.classList.remove('held');
 pointers.clear();held.clear();
 if(!ready)return;
 if(transferring)queue.push({release:true});else if(engine)engine.port.postMessage({release:true});else core.sim_release();
}
function activate(){fullscreen();enableAudio().catch(()=>failure('Toque novamente para ativar o áudio.'));}
function bindButton(el,kind,index){
 el.dataset.kind=kind;el.dataset.index=index;
 el.addEventListener('pointerdown',e=>{
  if(!ready||e.button>0)return;e.preventDefault();activate();
  pointers.set(e.pointerId,{el,button:true});el.setPointerCapture(e.pointerId);hold(el,true);
 });
 const up=e=>{const p=pointers.get(e.pointerId);if(!p?.button)return;hold(p.el,false);pointers.delete(e.pointerId);};
 el.addEventListener('pointerup',up);el.addEventListener('pointercancel',up);el.addEventListener('lostpointercapture',up);
 // Keyboard and assistive-technology activation; pointer clicks already use down/up.
 el.addEventListener('click',e=>{if(e.detail===0&&ready){activate();hold(el,true);hold(el,false);}});
}
function knobView(k){
 const angle=k.index===0&&k.kind===2?k.turn||0:-135+270*(k.value-k.min)/(k.max-k.min);
 k.el.style.setProperty('--angle',angle+'deg');k.el.setAttribute('aria-valuenow',k.value);
 let text=k.value;
 if(k.kind===3)text=Math.round(k.value/1023*100)+'%';
 else if(k.index===6)text=kits[k.value];else if(k.index===1)text=names[state[0]||0][k.value];
 else if(k.index===0)text='Vol '+(state[15]||0);
 k.el.setAttribute('aria-valuetext',String(text));k.output.textContent=text;
}
function turn(k,delta){
 if(!delta)return;
 if(k.kind===3){k.value=Math.max(k.min,Math.min(k.max,k.value+delta*8));command(3,0,k.value);}
 else{command(2,k.index,Math.max(-127,Math.min(127,delta)));k.turn=(k.turn||0)+delta*12;}
 knobView(k);
}
for(const k of knobSpecs){
 const el=document.createElement('div');el.className='knob-control';el.tabIndex=0;
 place(el,[k.x,k.y,9,18],[k.px,k.py,16,9.5]);
 el.setAttribute('role','slider');el.setAttribute('aria-label',k.name+' · '+k.hint);el.setAttribute('aria-valuemin',k.min);el.setAttribute('aria-valuemax',k.max);el.title=k.name+' · '+k.hint+' — arraste ou use as setas';
 el.innerHTML='<span class="knob-label"></span><span class="knob" aria-hidden="true"></span><output class="knob-value" aria-hidden="true"></output>';
 el.querySelector('.knob-label').textContent=k.name;k.el=el;k.output=el.querySelector('output');$('knobs').append(el);knobView(k);
 el.addEventListener('pointerdown',e=>{
  if(!ready||e.button>0)return;e.preventDefault();activate();el.focus({preventScroll:true});
  pointers.set(e.pointerId,{el,k,x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY,acc:0,moved:false});el.setPointerCapture(e.pointerId);el.classList.add('held');
 });
 el.addEventListener('pointermove',e=>{
  const p=pointers.get(e.pointerId);if(!p?.k)return;
  const dx=e.clientX-p.x,dy=p.y-e.clientY;p.x=e.clientX;p.y=e.clientY;
  if(Math.hypot(e.clientX-p.startX,e.clientY-p.startY)>3)p.moved=true;
  p.acc+=Math.abs(dy)>=Math.abs(dx)?dy:dx;
  const detent=5,delta=Math.trunc(p.acc/detent);if(delta){p.acc-=delta*detent;turn(k,delta);}
 });
 const finish=e=>{const p=pointers.get(e.pointerId);if(!p?.k)return;
  if(e.type==='pointerup'&&!p.moved){const r=el.getBoundingClientRect();turn(k,e.clientX<r.left+r.width/2?-1:1);}
  pointers.delete(e.pointerId);el.classList.remove('held');
 };
 el.addEventListener('pointerup',finish);el.addEventListener('pointercancel',finish);el.addEventListener('lostpointercapture',finish);
 el.addEventListener('keydown',e=>{const d={ArrowUp:1,ArrowRight:1,ArrowDown:-1,ArrowLeft:-1}[e.key];if(d){e.preventDefault();activate();turn(k,d);}});
 el.addEventListener('wheel',e=>{if(!ready)return;e.preventDefault();turn(k,e.deltaY<0?1:-1);},{passive:false});
}
const labels=['OCT−','OCT+','FX','SCL','ENV','LFO','EDIT','GLO','HOME','SAVE','ARP','SEQ','PLAY / STOP','REC'];
for(let i=0;i<14;i++){
 const el=document.createElement('button');el.type='button';el.className='panel-button'+(i===12?' play-button':'');el.textContent=labels[i];el.id='button-'+i;
 el.setAttribute('aria-label',labels[i]+(i===12?' · iniciar ou parar':i<2?' · um compasso': ' · sem função no BAILE 0.8'));
 if(i<2)place(el,[4.1+i*8.5,43.3,7.7,5.4],[5.4+i*18.5,26.7,16.7,5.3]);else{const c=(i-2)%6,r=Math.floor((i-2)/6);place(el,[54.7+c*6.75,28.6+r*10.9,5.8,8.8],[8+c*14.1,46.8+r*6.4,12.3,5.4]);}
 bindButton(el,0,i);matrix.set(i,el);$('buttons').append(el);
}
function note(n,x,y,h,caption,px,py,ph){
 const el=document.createElement('button');el.type='button';el.className='note-key';el.id='key-'+n;place(el,[x,y,5.8,h],[px(0),py,10,ph]);keyEls.push({el,px,py,ph});
 const step=white.indexOf(n);el.setAttribute('aria-label',step<0?'Tecla '+n+' · sem função no BAILE 0.8':'Passo '+(step+1));
 el.innerHTML='<span class="key-cap"></span><span class="key-caption">'+caption+'</span>';bindButton(el,1,n);matrix.set(n+14,el);$('keys').append(el);
}
white.forEach((n,i)=>note(n,2.8+i*5.86,79.2,16.2,String(i+1),h=>7.5+(i-8*h)*10.64,79.9,14.8));
black.forEach(([n,after],i)=>note(n,2.8+(after+.5)*5.86,61.5,15.4,['OP1','OP2','OP3','OP4','OP5','OP6','PIT','MOD','MONO','POLY',''][i],h=>7.5+(after+.5-8*h)*10.64,68.5,10.8));
// Portrait shows eight steps at a time; the strip above the keys shows and picks the half.
minimap=document.createElement('div');minimap.className='minimap';minimap.setAttribute('role','group');minimap.setAttribute('aria-label','Passos 1–8 ou 9–16');
white.forEach((_,i)=>{const c=document.createElement('i');c.style.left=(i*6.25+.5)+'%';minimapCells.push(c);minimap.append(c);});
minimap.append(document.createElement('b'));
minimap.addEventListener('pointerdown',e=>{e.preventDefault();const r=minimap.getBoundingClientRect();half=e.clientX-r.left<r.width/2?0:1;layoutKeys();});
device.append(minimap);layoutKeys();
function paint(pixels,s,leds){
 state=s;
 for(let i=0;i<pixels.length;i++){const p=pixels[i],j=i*4;bitmap.data[j]=(p>>11)*255/31;bitmap.data[j+1]=((p>>5)&63)*255/63;bitmap.data[j+2]=(p&31)*255/31;bitmap.data[j+3]=255;}
 ctx.putImageData(bitmap,0,0);
 // Read actual firmware LED outputs, including startup and transport. No synthetic playhead.
 minimapCells.forEach((c,i)=>c.classList.toggle('on',!!leds[14+white[i]]));
 matrix.forEach((el,i)=>{el.classList.toggle('lit',!!leds[i]);if(i>=14||i===12)el.setAttribute('aria-pressed',String(!!leds[i]));});
 for(const k of knobSpecs){
  if(k.state!==undefined)k.value=s[k.state];else if(k.kind===2&&k.index===6)k.value=s[1]?s[1]-1:s[0];else if(k.kind===2&&k.index===1)k.value=s[2];knobView(k);
 }
 $('lcd').setAttribute('aria-label',kits[s[0]]+' · '+names[s[0]][s[2]]+' · '+s[6]+' BPM · '+(s[13]?'tocando':'parado'));
 if(s[8])failure('Não foi possível carregar o kit. Recarregue a página.');
}
function read(c){paint(new Uint16Array(c.memory.buffer,c.sim_pixels(),57600),new Uint32Array(c.memory.buffer,c.baile_inspect(),16).slice(),new Uint8Array(c.memory.buffer,c.sim_state()+168,41));}
function startTimer(){clearInterval(timer);timer=setInterval(()=>{for(let i=0;i<10;i++)core.sim_render();read(core);},29);}
async function enableAudio(){
 if(!ready)return;
 if(starting)return starting;
 if(audio&&engine){await audio.resume();return;}
 transferring=true;clearInterval(timer);
 starting=(async()=>{
  try{
   audio=new AudioContext({sampleRate:44100});await audio.resume();await audio.audioWorklet.addModule('baile-worklet.js?v=3');
   engine=new AudioWorkletNode(audio,'baile',{numberOfInputs:0,numberOfOutputs:1,outputChannelCount:[2],processorOptions:{wasm,memory:core.memory.buffer.slice(0)}});
   engine.port.onmessage=({data:m})=>paint(m.pixels,m.state,m.leds);
   engine.onprocessorerror=()=>failure('O áudio parou. Recarregue a página.');
   engine.connect(audio.destination);for(const m of queue)engine.port.postMessage(m);queue=[];
   $('boot-status').hidden=true;
  }catch(e){
   if(audio)await audio.close();audio=null;engine=null;
   for(const m of queue){if(m.release)core.sim_release();else core.sim_control(m.kind,m.index,m.value);}queue=[];startTimer();throw e;
  }finally{transferring=false;starting=null;}
 })();return starting;
}
window.addEventListener('blur',releaseAll);
document.addEventListener('visibilitychange',()=>{if(document.hidden)releaseAll();});
window.addEventListener('resize',mode);window.visualViewport?.addEventListener('resize',mode);
document.addEventListener('fullscreenchange',()=>{
 if(!document.fullscreenElement&&orientationLocked){
  try{screen.orientation.unlock();}catch{}
  orientationLocked=false;
 }
 mode();
});
mode();
(async()=>{
 try{const r=await fetch('baile.wasm?v=0.8');if(!r.ok)throw Error(r.status);wasm=await r.arrayBuffer();core=new WebAssembly.Instance(new WebAssembly.Module(wasm),{}).exports;core._initialize();core.sim_boot(3);ready=true;device.setAttribute('aria-busy','false');$('boot-status').hidden=true;startTimer();}
 catch(e){failure('Não foi possível carregar o BAILE. Recarregue a página.');}
})();
