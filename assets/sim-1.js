/* Sim-1 · 排队论模拟器（第 2 章） */
/* 与 tools/sim1-queue-model-test.js 逻辑必须一致。 */
(function(){
"use strict";
var cv = document.getElementById('chart');
if (!cv) return;
var ctx = cv.getContext('2d');
var W, H;
function resizeCanvas(redraw){
  var rect = cv.getBoundingClientRect();
  if (!rect.width || !rect.height) return;
  var dpr = window.devicePixelRatio || 1;
  W = rect.width; H = rect.height;
  cv.width = Math.round(W*dpr); cv.height = Math.round(H*dpr);
  ctx.setTransform(dpr,0,0,dpr,0,0);
  if (redraw && S){
    try { draw(); } catch (e) {}
  }
}
resizeCanvas();
var resizeTimer = null;
function scheduleResize(){
  if (document.hidden || resizeTimer) return;
  resizeTimer = setTimeout(function(){
    resizeTimer = null;
    if (!document.hidden) resizeCanvas(true);
  }, 150);
}
window.addEventListener('resize', scheduleResize);
var WINDOW = 60;

var DT = 0.1;
var DEF = { qps:80, serviceMs:100, concurrency:10, timeoutMs:10000, usefulConcurrency:10 };
var S;

function makeState(overrides){
  return Object.assign({
    t:0, qps:DEF.qps, serviceMs:DEF.serviceMs, concurrency:DEF.concurrency,
    timeoutMs:DEF.timeoutMs, usefulConcurrency:DEF.usefulConcurrency,
    backlog:0, running:true, hist:[]
  }, overrides || {});
}

function modelTick(S){
  S.t += DT;

  /* 超过下游有效并行度后，额外槽位只制造争用，不增加服务能力。 */
  var contention = Math.max(1, S.concurrency / S.usefulConcurrency);
  var effectiveServiceMs = S.serviceMs * contention;
  var cap = S.concurrency / (effectiveServiceMs / 1000);
  var rho = cap > 0 ? S.qps / cap : 1e6;

  var overflow = Math.max(0, S.qps - cap) * DT;
  S.backlog += overflow;
  var maxBacklog = Math.max(0, cap * S.timeoutMs / 1000);
  var expired = Math.max(0, S.backlog - maxBacklog);
  S.backlog -= expired;

  var queueMs;
  if (rho < 1){
    queueMs = effectiveServiceMs * rho / Math.max(0.001, 1 - rho);
    S.backlog = Math.max(0, S.backlog - (cap - S.qps) * DT);
  } else {
    queueMs = cap > 0 ? S.backlog / cap * 1000 : S.timeoutMs;
  }
  var rawP50 = effectiveServiceMs + 0.7 * queueMs;
  var rawP99 = effectiveServiceMs + 4 * queueMs;
  var timeoutRate = rawP99 > S.timeoutMs ? Math.min(1, 1 - S.timeoutMs / rawP99) : 0;
  var errorRate = Math.min(1, Math.max(timeoutRate, S.qps > 0 ? expired / (S.qps * DT) : 0));
  var p50 = Math.min(rawP50, Math.max(effectiveServiceMs, S.timeoutMs * 0.7));
  var p99 = Math.min(rawP99, Math.max(effectiveServiceMs, S.timeoutMs * 0.9));
  /* 吞吐计已处理请求：成功和超时都会完成生命周期并释放槽位。 */
  var throughput = Math.min(S.qps, cap);

  return { cap:cap, rho:rho, queueMs:queueMs, p50:p50, p99:p99, rawP99:rawP99,
    errorRate:errorRate, throughput:throughput, effectiveServiceMs:effectiveServiceMs };
}

function reset(){
  S = makeState();
  document.getElementById('sl-qps').value = DEF.qps;
  document.getElementById('sl-service').value = DEF.serviceMs;
  document.getElementById('sl-concurrency').value = DEF.concurrency;
  document.getElementById('sl-timeout').value = DEF.timeoutMs;
  document.getElementById('btn-pause').textContent = '暂停';
  document.getElementById('log').innerHTML = '';
  syncLabels();
  logLine('模拟开始：连接池与下游有效并行度均为 10。');
}

function clockStr(){
  var base = 2*3600 + 47*60;
  var s = Math.floor(base + S.t);
  var hh = Math.floor(s/3600)%24, mm = Math.floor(s/60)%60, ss = s%60;
  function p(n){ return (n<10?'0':'')+n; }
  return p(hh)+':'+p(mm)+':'+p(ss);
}

function logLine(msg){
  var el = document.getElementById('log');
  var d = document.createElement('div');
  d.innerHTML = '<span class="tt">'+clockStr()+'</span>'+msg;
  el.insertBefore(d, el.firstChild);
  while (el.children.length > 40) el.removeChild(el.lastChild);
}

function tick(){
  if (!S.running) return;
  var r = modelTick(S);
  S.hist.push({ t:S.t, p50:r.p50, p99:r.p99, rho:Math.min(2,r.rho)*50, err:r.errorRate*100 });
  while (S.hist.length && S.hist[0].t < S.t-WINDOW) S.hist.shift();
  draw();
  readouts(r);
}

function readouts(r){
  document.getElementById('clock').textContent = clockStr();
  document.getElementById('m-p50').textContent = Math.round(r.p50).toLocaleString()+'ms';
  document.getElementById('m-p99').textContent = Math.round(r.p99).toLocaleString()+'ms';
  document.getElementById('m-rho').textContent = (r.rho*100).toFixed(1)+'%';
  document.getElementById('m-error').textContent = (r.errorRate*100).toFixed(1)+'%';
  document.getElementById('m-throughput').textContent = r.throughput.toFixed(1)+' QPS';
  document.getElementById('m-p99').style.color = r.p99 > 1000 ? 'var(--red)' : (r.p99 > 300 ? 'var(--amber)' : 'var(--text)');
}

function draw(){
  ctx.clearRect(0,0,W,H);
  var pad = 10, x0 = S.t-WINDOW, i;
  function X(t){ return (t-x0)/WINDOW*W; }
  function Yms(v){ return H-pad-Math.min(1,v/10000)*(H-pad*2); }
  function Ypct(v){ return H-pad-Math.min(100,v)/100*(H-pad*2); }
  ctx.strokeStyle = 'rgba(138,148,169,0.12)'; ctx.lineWidth = 1;
  for (i=1;i<4;i++){ ctx.beginPath(); ctx.moveTo(0,H*i/4); ctx.lineTo(W,H*i/4); ctx.stroke(); }
  ctx.strokeStyle = 'rgba(255,92,92,0.72)'; ctx.lineWidth = 2; ctx.setLineDash([10,8]);
  ctx.beginPath(); ctx.moveTo(0,Yms(1000)); ctx.lineTo(W,Yms(1000)); ctx.stroke(); ctx.setLineDash([]);
  function line(key,Y,color,width){
    ctx.strokeStyle=color; ctx.lineWidth=width; ctx.beginPath();
    for (var j=0;j<S.hist.length;j++){
      var h=S.hist[j], x=X(h.t), y=Y(h[key]);
      if (j===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    }
    ctx.stroke();
  }
  line('p50',Yms,'rgba(63,210,199,0.95)',2.5);
  line('p99',Yms,'rgba(255,180,84,0.95)',3);
  line('rho',Ypct,'rgba(220,227,242,0.95)',2.5);
  line('err',Ypct,'rgba(255,92,92,0.95)',2.5);
}

function syncLabels(){
  document.getElementById('lb-qps').textContent = S.qps+' QPS';
  document.getElementById('lb-service').textContent = S.serviceMs+' ms';
  document.getElementById('lb-concurrency').textContent = S.concurrency+' 槽';
  document.getElementById('lb-timeout').textContent = S.timeoutMs+' ms';
}
function bindSlider(id,key){
  document.getElementById(id).addEventListener('input',function(e){
    S[key]=Number(e.target.value); syncLabels();
  });
}
bindSlider('sl-qps','qps');
bindSlider('sl-service','serviceMs');
bindSlider('sl-concurrency','concurrency');
bindSlider('sl-timeout','timeoutMs');
document.getElementById('btn-pause').addEventListener('click',function(){
  S.running=!S.running; this.textContent=S.running?'暂停':'继续';
});
document.getElementById('btn-reset').addEventListener('click',function(){ reset(); });

reset();
setInterval(tick,100);
})();
