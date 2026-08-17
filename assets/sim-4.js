/* Sim-4 · 重试风暴模拟器（第 7 章） */
/* 与 tools/sim4-retrystorm-model-test.js 逻辑必须一致。 */
(function(){
"use strict";
var cv=document.getElementById('chart');
if(!cv)return;
var ctx=cv.getContext('2d');
var W,H;
function resizeCanvas(redraw){
  var rect=cv.getBoundingClientRect();
  if(!rect.width||!rect.height)return;
  var dpr=window.devicePixelRatio||1;
  W=rect.width;H=rect.height;
  cv.width=Math.round(W*dpr);cv.height=Math.round(H*dpr);
  ctx.setTransform(dpr,0,0,dpr,0,0);
  if(redraw&&S){
    try{draw();}catch(e){}
  }
}
resizeCanvas();
var resizeTimer=null;
function scheduleResize(){
  if(document.hidden||resizeTimer)return;
  resizeTimer=setTimeout(function(){
    resizeTimer=null;
    if(!document.hidden)resizeCanvas(true);
  },150);
}
window.addEventListener('resize',scheduleResize);
var WINDOW=20;

var DT=0.1;
var DEF={layers:3,attempts:3,backoff:false,jitter:false,failureRate:1};
var S;
function makeState(overrides){
  return Object.assign({t:0,running:true,events:[],injected:0,delivered:0,hist:[]},DEF,overrides||{});
}
function expectedAmplification(S){
  var perLayer=0;
  for(var i=0;i<S.attempts;i++)perLayer+=Math.pow(S.failureRate,i);
  return Math.pow(perLayer,S.layers);
}
function jitterFactor(comboIndex,layer){
  var x=((comboIndex+1)*1103515245+(layer+1)*12345)>>>0;
  x=(x^(x>>>16))>>>0;
  return 0.5+(x%10001)/10000;
}
function injectFailure(S){
  var total=Math.pow(S.attempts,S.layers);
  for(var combo=0;combo<total;combo++){
    var n=combo,delay=0,weight=1;
    for(var layer=0;layer<S.layers;layer++){
      var attempt=n%S.attempts;
      n=Math.floor(n/S.attempts);
      weight*=Math.pow(S.failureRate,attempt);
      if(S.backoff&&attempt>0){
        var part=(Math.pow(2,attempt)-1)*0.4;
        if(S.jitter)part*=jitterFactor(combo,layer);
        delay+=part;
      }
    }
    S.events.push({at:S.t+delay,weight:weight});
  }
  S.events.sort(function(a,b){return a.at-b.at;});
  S.injected++;
}
function modelTick(S){
  S.t+=DT;
  var terminal=0,keep=[];
  for(var i=0;i<S.events.length;i++){
    var event=S.events[i];
    if(event.at<=S.t+1e-9)terminal+=event.weight;
    else keep.push(event);
  }
  S.events=keep;
  S.delivered+=terminal;
  return {terminalQps:terminal/DT,amplification:expectedAmplification(S),cumulative:S.delivered,pending:S.events.length};
}

function reset(){
  S=makeState();
  document.getElementById('sl-layers').value=DEF.layers;
  document.getElementById('sl-retries').value=DEF.attempts;
  document.getElementById('sl-failure').value=DEF.failureRate*100;
  document.getElementById('tg-backoff').checked=DEF.backoff;
  document.getElementById('tg-jitter').checked=DEF.jitter;
  document.getElementById('btn-pause').textContent='暂停';
  document.getElementById('log').innerHTML='';
  syncLabels();logLine('重试链路就绪：默认 3 层 × 每层 3 次。');
}
function clockStr(){
  var base=2*3600+47*60,s=Math.floor(base+S.t);
  var hh=Math.floor(s/3600)%24,mm=Math.floor(s/60)%60,ss=s%60;
  function p(n){return(n<10?'0':'')+n;}
  return p(hh)+':'+p(mm)+':'+p(ss);
}
function logLine(msg){
  var el=document.getElementById('log'),d=document.createElement('div');
  d.innerHTML='<span class="tt">'+clockStr()+'</span>'+msg;
  el.insertBefore(d,el.firstChild);
  while(el.children.length>40)el.removeChild(el.lastChild);
}
function tick(){
  if(!S.running)return;
  var r=modelTick(S);
  S.hist.push({t:S.t,terminalQps:r.terminalQps,amplification:r.amplification});
  while(S.hist.length&&S.hist[0].t<S.t-WINDOW)S.hist.shift();
  draw();readouts(r);
}
function readouts(r){
  document.getElementById('clock').textContent=clockStr();
  document.getElementById('m-amplification').textContent=r.amplification.toFixed(2)+'×';
  document.getElementById('m-terminal').textContent=r.terminalQps.toFixed(1)+' QPS';
  document.getElementById('m-cumulative').textContent=r.cumulative.toFixed(1);
  document.getElementById('m-pending').textContent=String(r.pending);
}
function draw(){
  ctx.clearRect(0,0,W,H);
  var pad=10,x0=S.t-WINDOW,maxQ=10,i;
  for(i=0;i<S.hist.length;i++)maxQ=Math.max(maxQ,S.hist[i].terminalQps);
  function X(t){return(t-x0)/WINDOW*W;}
  function Yq(v){return H-pad-Math.min(1,v/maxQ)*(H-pad*2);}
  function Ya(v){return H-pad-Math.min(1,v/256)*(H-pad*2);}
  ctx.strokeStyle='rgba(138,148,169,0.12)';ctx.lineWidth=1;
  for(i=1;i<4;i++){ctx.beginPath();ctx.moveTo(0,H*i/4);ctx.lineTo(W,H*i/4);ctx.stroke();}
  function line(key,Y,color,width,dash){
    ctx.strokeStyle=color;ctx.lineWidth=width;ctx.setLineDash(dash||[]);ctx.beginPath();
    for(var j=0;j<S.hist.length;j++){
      var h=S.hist[j],x=X(h.t),y=Y(h[key]);
      if(j===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
    }
    ctx.stroke();ctx.setLineDash([]);
  }
  line('terminalQps',Yq,'rgba(255,92,92,0.95)',3);
  line('amplification',Ya,'rgba(255,180,84,0.95)',2.5,[8,6]);
}
function syncLabels(){
  document.getElementById('lb-layers').textContent=S.layers+' 层';
  document.getElementById('lb-retries').textContent=S.attempts+' 次';
  document.getElementById('lb-failure').textContent=Math.round(S.failureRate*100)+'%';
}
document.getElementById('sl-layers').addEventListener('input',function(e){S.layers=Number(e.target.value);syncLabels();});
document.getElementById('sl-retries').addEventListener('input',function(e){S.attempts=Number(e.target.value);syncLabels();});
document.getElementById('sl-failure').addEventListener('input',function(e){S.failureRate=Number(e.target.value)/100;syncLabels();});
document.getElementById('tg-backoff').addEventListener('change',function(e){
  S.backoff=e.target.checked;logLine(S.backoff?'✅ backoff 开启：重试按指数间隔错开。':'⚠️ backoff 关闭：重试恢复同刻发出。');
});
document.getElementById('tg-jitter').addEventListener('change',function(e){
  S.jitter=e.target.checked;logLine(S.jitter?'✅ jitter 开启：间隔加入 ±50% 扰动。':'jitter 已关闭。');
});
document.getElementById('btn-failure').addEventListener('click',function(){
  injectFailure(S);logLine('💥 下游故障注入：本轮期望放大 '+expectedAmplification(S).toFixed(2)+'×。');
});
document.getElementById('btn-pause').addEventListener('click',function(){S.running=!S.running;this.textContent=S.running?'暂停':'继续';});
document.getElementById('btn-reset').addEventListener('click',function(){reset();});

reset();
setInterval(tick,100);
})();
