/* Sim-6 · 积压水位模拟器（第 9 章） */
/* 与 tools/sim6-backlog-model-test.js 逻辑必须一致。 */
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
var WINDOW=120,ALERT=5000;

var DT=1;
var DEF={produce:100,consumeEach:95,consumers:1};
var S;
function makeState(overrides){
  return Object.assign({t:0,running:true,backlog:0,floodUntil:0,hist:[]},DEF,overrides||{});
}
function injectFlood(S){S.floodUntil=Math.max(S.floodUntil,S.t+20);}
function modelTick(S){
  S.t+=DT;
  var activeProduce=S.t<=S.floodUntil?S.produce*5:S.produce;
  var capacity=S.consumeEach*S.consumers;
  var available=S.backlog+activeProduce*DT;
  var consumed=Math.min(available,capacity*DT);
  S.backlog=Math.max(0,available-consumed);
  var netCatchup=capacity-activeProduce;
  var catchupSeconds=S.backlog===0?0:(netCatchup>0?S.backlog/netCatchup:null);
  return {backlog:S.backlog,produceQps:activeProduce,consumeCapacity:capacity,throughput:consumed/DT,catchupSeconds:catchupSeconds};
}

function reset(){
  S=makeState();
  document.getElementById('sl-produce').value=DEF.produce;
  document.getElementById('sl-consume').value=DEF.consumeEach;
  document.getElementById('sl-consumers').value=DEF.consumers;
  document.getElementById('btn-pause').textContent='暂停';
  document.getElementById('log').innerHTML='';
  syncLabels();logLine('队列开始运行：消费能力只有生产速率的 95%。');
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
  S.hist.push({t:S.t,backlog:r.backlog,produceQps:r.produceQps,consumeCapacity:r.consumeCapacity});
  while(S.hist.length&&S.hist[0].t<S.t-WINDOW)S.hist.shift();
  draw();readouts(r);
}
function catchupLabel(v){
  if(v===null)return'永不追平';
  if(v===0)return'已清零';
  if(v<60)return Math.ceil(v)+' 秒';
  if(v<3600)return(v/60).toFixed(1)+' 分钟';
  return(v/3600).toFixed(1)+' 小时';
}
function readouts(r){
  document.getElementById('clock').textContent=clockStr();
  document.getElementById('m-backlog').textContent=Math.round(r.backlog).toLocaleString();
  document.getElementById('m-produce').textContent=Math.round(r.produceQps)+' /s';
  document.getElementById('m-consume').textContent=Math.round(r.consumeCapacity)+' /s';
  document.getElementById('m-throughput').textContent=Math.round(r.throughput)+' /s';
  document.getElementById('m-catchup').textContent=catchupLabel(r.catchupSeconds);
  document.getElementById('m-catchup').style.color=r.catchupSeconds===null?'var(--red)':(r.backlog>0?'var(--amber)':'var(--green)');
}
function draw(){
  ctx.clearRect(0,0,W,H);
  var pad=10,x0=S.t-WINDOW,maxBacklog=ALERT*1.2,maxRate=1,i;
  for(i=0;i<S.hist.length;i++){
    maxBacklog=Math.max(maxBacklog,S.hist[i].backlog);
    maxRate=Math.max(maxRate,S.hist[i].produceQps,S.hist[i].consumeCapacity);
  }
  function X(t){return(t-x0)/WINDOW*W;}
  function Yb(v){return H-pad-Math.min(1,v/maxBacklog)*(H-pad*2);}
  function Yr(v){return H-pad-Math.min(1,v/maxRate)*(H-pad*2);}
  ctx.strokeStyle='rgba(138,148,169,0.12)';ctx.lineWidth=1;
  for(i=1;i<4;i++){ctx.beginPath();ctx.moveTo(0,H*i/4);ctx.lineTo(W,H*i/4);ctx.stroke();}
  ctx.strokeStyle='rgba(255,92,92,0.75)';ctx.lineWidth=2;ctx.setLineDash([10,8]);
  ctx.beginPath();ctx.moveTo(0,Yb(ALERT));ctx.lineTo(W,Yb(ALERT));ctx.stroke();ctx.setLineDash([]);
  function line(key,Y,color,width){
    ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();
    for(var j=0;j<S.hist.length;j++){
      var h=S.hist[j],x=X(h.t),y=Y(h[key]);
      if(j===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
    }
    ctx.stroke();
  }
  line('backlog',Yb,'rgba(255,180,84,0.95)',3.5);
  line('produceQps',Yr,'rgba(255,92,92,0.95)',2.5);
  line('consumeCapacity',Yr,'rgba(63,210,199,0.95)',2.5);
}
function syncLabels(){
  document.getElementById('lb-produce').textContent=S.produce+' /s';
  document.getElementById('lb-consume').textContent=S.consumeEach+' /s';
  document.getElementById('lb-consumers').textContent=S.consumers+' 个';
}
document.getElementById('sl-produce').addEventListener('input',function(e){S.produce=Number(e.target.value);syncLabels();});
document.getElementById('sl-consume').addEventListener('input',function(e){S.consumeEach=Number(e.target.value);syncLabels();});
document.getElementById('sl-consumers').addEventListener('input',function(e){S.consumers=Number(e.target.value);syncLabels();});
document.getElementById('btn-flood').addEventListener('click',function(){
  injectFlood(S);logLine('🎫 开票洪峰：生产速率暂时升到 '+(S.produce*5)+' /s。');
});
document.getElementById('btn-pause').addEventListener('click',function(){S.running=!S.running;this.textContent=S.running?'暂停':'继续';});
document.getElementById('btn-reset').addEventListener('click',function(){reset();});

reset();
setInterval(tick,100);
})();
