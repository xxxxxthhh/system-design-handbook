/* Sim-3 · 限流算法对比模拟器（第 6 章） */
/* 与 tools/sim3-ratelimit-model-test.js 逻辑必须一致。 */
(function(){
"use strict";
var cv = document.getElementById('chart');
if (!cv) return;
var ctx = cv.getContext('2d');
var W = cv.width, H = cv.height;
var WINDOW = 20;

var DT = 0.1;
var DEF = { multiplier:5, baseQps:80, limit:100, burst:100 };
var S;
function makeState(overrides){
  var cfg = Object.assign({},DEF,overrides||{});
  return Object.assign({
    t:0,running:true,burstUntil:0,tokens:cfg.burst,leakQueue:0,
    swBuckets:Array(10).fill(0),swIndex:0,hist:[]
  },cfg);
}
function injectBurst(S){ S.burstUntil=Math.max(S.burstUntil,S.t+0.5); }

function modelTick(S){
  S.t += DT;
  var arrivalQps = S.t <= S.burstUntil ? S.baseQps*S.multiplier : S.baseQps;
  var arrivals = arrivalQps*DT;

  S.tokens = Math.min(S.burst,S.tokens+S.limit*DT);
  var tokenAllowed = Math.min(arrivals,S.tokens);
  S.tokens -= tokenAllowed;
  var tokenRejected = arrivals-tokenAllowed;

  var leakCapacity = Math.max(S.burst*4,S.limit*DT);
  var leakAdmitted = Math.min(arrivals,Math.max(0,leakCapacity-S.leakQueue));
  var leakRejected = arrivals-leakAdmitted;
  S.leakQueue += leakAdmitted;
  var leakAllowed = Math.min(S.leakQueue,S.limit*DT);
  S.leakQueue -= leakAllowed;

  S.swIndex = (S.swIndex+1)%10;
  S.swBuckets[S.swIndex] = 0;
  var windowUsed = S.swBuckets.reduce(function(a,b){return a+b;},0);
  var windowLeft = Math.max(0,S.limit-windowUsed);
  var windowAllowed = Math.min(arrivals,windowLeft);
  S.swBuckets[S.swIndex] = windowAllowed;
  var windowRejected = arrivals-windowAllowed;

  return {
    arrivalQps:arrivalQps,
    tokenQps:tokenAllowed/DT,leakQps:leakAllowed/DT,windowQps:windowAllowed/DT,
    tokenRejectedQps:tokenRejected/DT,leakRejectedQps:leakRejected/DT,
    windowRejectedQps:windowRejected/DT
  };
}

function reset(){
  S=makeState();
  document.getElementById('sl-multiplier').value=DEF.multiplier;
  document.getElementById('sl-base').value=DEF.baseQps;
  document.getElementById('sl-limit').value=DEF.limit;
  document.getElementById('sl-burst').value=DEF.burst;
  document.getElementById('btn-pause').textContent='暂停';
  document.getElementById('log').innerHTML='';
  syncLabels();
  logLine('三条通道已就绪，等待同一波突发。');
}
function clockStr(){
  var base=2*3600+47*60, s=Math.floor(base+S.t);
  var hh=Math.floor(s/3600)%24,mm=Math.floor(s/60)%60,ss=s%60;
  function p(n){return (n<10?'0':'')+n;}
  return p(hh)+':'+p(mm)+':'+p(ss);
}
function logLine(msg){
  var el=document.getElementById('log'),d=document.createElement('div');
  d.innerHTML='<span class="tt">'+clockStr()+'</span>'+msg;
  el.insertBefore(d,el.firstChild);
  while(el.children.length>40) el.removeChild(el.lastChild);
}
function tick(){
  if(!S.running) return;
  var r=modelTick(S);
  S.hist.push(Object.assign({t:S.t,limit:S.limit},r));
  while(S.hist.length&&S.hist[0].t<S.t-WINDOW) S.hist.shift();
  draw(); readouts(r);
}
function readouts(r){
  document.getElementById('clock').textContent=clockStr();
  document.getElementById('m-arrival').textContent=Math.round(r.arrivalQps)+' QPS';
  document.getElementById('m-token').textContent=Math.round(r.tokenQps)+' QPS';
  document.getElementById('m-leak').textContent=Math.round(r.leakQps)+' QPS';
  document.getElementById('m-window').textContent=Math.round(r.windowQps)+' QPS';
  document.getElementById('m-rejected').textContent=Math.round(r.tokenRejectedQps+r.leakRejectedQps+r.windowRejectedQps)+' QPS';
}
function draw(){
  ctx.clearRect(0,0,W,H);
  var pad=10,x0=S.t-WINDOW,maxQ=Math.max(S.baseQps*S.multiplier,S.limit,S.burst/DT,1),i;
  function X(t){return (t-x0)/WINDOW*W;}
  function Y(v){return H-pad-Math.min(1,v/maxQ)*(H-pad*2);}
  ctx.strokeStyle='rgba(138,148,169,0.12)';ctx.lineWidth=1;
  for(i=1;i<4;i++){ctx.beginPath();ctx.moveTo(0,H*i/4);ctx.lineTo(W,H*i/4);ctx.stroke();}
  function line(key,color,width,dash){
    ctx.strokeStyle=color;ctx.lineWidth=width;ctx.setLineDash(dash||[]);ctx.beginPath();
    for(var j=0;j<S.hist.length;j++){
      var h=S.hist[j],x=X(h.t),y=Y(h[key]);
      if(j===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
    }
    ctx.stroke();ctx.setLineDash([]);
  }
  line('limit','rgba(138,148,169,0.75)',2,[10,8]);
  line('arrivalQps','rgba(220,227,242,0.70)',2);
  line('tokenQps','rgba(255,180,84,0.95)',3);
  line('leakQps','rgba(63,210,199,0.95)',3);
  line('windowQps','rgba(255,92,92,0.95)',3);
  line('tokenRejectedQps','rgba(255,180,84,0.70)',1.5,[6,6]);
  line('leakRejectedQps','rgba(63,210,199,0.70)',1.5,[6,6]);
  line('windowRejectedQps','rgba(255,92,92,0.70)',1.5,[6,6]);
}
function syncLabels(){
  document.getElementById('lb-multiplier').textContent=S.multiplier+'×';
  document.getElementById('lb-base').textContent=S.baseQps+' QPS';
  document.getElementById('lb-limit').textContent=S.limit+' QPS';
  document.getElementById('lb-burst').textContent=S.burst+' tokens';
}
function bindSlider(id,key){
  document.getElementById(id).addEventListener('input',function(e){
    S[key]=Number(e.target.value);
    if(key==='burst') S.tokens=Math.min(S.tokens,S.burst);
    syncLabels();
  });
}
bindSlider('sl-multiplier','multiplier');
bindSlider('sl-base','baseQps');
bindSlider('sl-limit','limit');
bindSlider('sl-burst','burst');
document.getElementById('btn-burst').addEventListener('click',function(){
  injectBurst(S); logLine('⚡ 注入 '+S.multiplier+'× 突发：观察三条曲线的形状。');
});
document.getElementById('btn-pause').addEventListener('click',function(){S.running=!S.running;this.textContent=S.running?'暂停':'继续';});
document.getElementById('btn-reset').addEventListener('click',function(){reset();});

reset();
setInterval(tick,100);
})();
