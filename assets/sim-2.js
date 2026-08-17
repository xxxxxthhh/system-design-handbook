/* Sim-2 · 缓存雪崩模拟器（第 5 章）· 逐字抽取自样章，仅包裹为独立 IIFE。
   与 tools/sim2-avalanche-model-test.js 的状态机逻辑必须保持一致；任一侧改动需同步另一侧。 */
(function(){
"use strict";
/* ---------- 模拟器 ---------- */
var cv = document.getElementById('chart');
if (!cv) return;
var ctx = cv.getContext('2d');
var W = cv.width, H = cv.height;
var WINDOW = 240;            /* 图表时间窗（模拟秒） */
var DT = 0.5;                /* 每 tick 前进的模拟秒 */

var DEF = { qps:10000, cap:800 };
var S;

function reset(){
  S = { t:0, running:true, qps:DEF.qps, cap:DEF.cap,
        jitter:false, breaker:false, cacheUp:true,
        w:0.99, health:1, dbDown:false, cd:0, lastBatch:0, hist:[] };
  document.getElementById('sl-qps').value = DEF.qps;
  document.getElementById('sl-cap').value = DEF.cap;
  document.getElementById('tg-jitter').checked = false;
  document.getElementById('tg-breaker').checked = false;
  var bc = document.getElementById('btn-crash');
  bc.textContent = '💥 缓存集群宕机'; bc.className = 'btn danger';
  document.getElementById('log').innerHTML = '';
  syncLabels();
  logLine('模拟开始。一切正常——真的吗？');
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
  S.t += DT;

  /* 过期模型 */
  if (S.cacheUp){
    if (S.jitter){
      S.w -= S.w * (0.2/60) * DT;               /* 同样的过期总量，摊平成细流 */
    } else if (S.t - S.lastBatch >= 60){
      S.w *= 0.8;                                /* 一批同 TTL 的 key 集体过期 */
      S.lastBatch = S.t;
      logLine('⏰ 一批同 TTL 的 key 集体过期（约 20% 失效）');
    }
  } else {
    S.w = 0;
  }

  var hit = 0.995 * S.w;
  var off = S.qps * (1 - hit);                   /* 砸向 DB 的流量 */
  var admitted = S.breaker ? Math.min(off, S.cap*0.85) : off;
  var shed = off - admitted;
  var served = 0, failDb = 0, load = 0;

  if (S.dbDown){
    failDb = admitted;
    if (admitted <= S.cap*0.9){ S.cd += DT; } else { S.cd = 0; }
    if (S.cd >= 6){
      S.dbDown = false; S.health = 0.35; S.cd = 0;
      logLine('🔄 数据库重启成功（脆弱状态，health 35%）');
    }
  } else {
    served = Math.min(admitted, S.cap);
    failDb = admitted - served;
    load = admitted / S.cap;
    if (load > 1){
      S.health -= Math.min(0.35, (load-1)*0.04) * DT;
    } else if (load < 0.95){
      S.health = Math.min(1, S.health + 0.08*DT);
    }
    if (S.health <= 0){
      S.health = 0; S.dbDown = true; S.cd = 0;
      logLine('💀 数据库过载崩溃——全部 DB 请求失败');
    }
  }

  /* 回填：只有 DB 真正服务了 miss，缓存才会变热 */
  if (S.cacheUp){
    S.w += (1 - S.w) * (served/8000) * DT;
    if (S.w > 0.995) S.w = 0.995;
  }

  var err = S.qps > 0 ? (shed + failDb) / S.qps : 0;
  var p99;
  if (S.dbDown){ p99 = 10000; }
  else if (load >= 1){ p99 = Math.min(9999, Math.round(1200 + (load-1)*900)); }
  else {
    p99 = 45*(1 + load*load*2) + (load > 0.8 ? (load-0.8)*2500 : 0);
    p99 = Math.round(p99 * (2 - S.health));
  }

  S.hist.push({ t:S.t, off:off, hit:hit*100, err:err*100, down:S.dbDown?1:0 });
  while (S.hist.length && S.hist[0].t < S.t - WINDOW) S.hist.shift();

  draw();
  readouts(hit, off, load, p99, err);
}

function readouts(hit, off, load, p99, err){
  document.getElementById('clock').textContent = clockStr();
  document.getElementById('m-hit').textContent = (hit*100).toFixed(1)+'%';
  document.getElementById('m-db').textContent = Math.round(off).toLocaleString();
  document.getElementById('m-p99').textContent = p99 >= 10000 ? '超时' : p99+'ms';
  document.getElementById('m-p99').style.color = p99 > 800 ? 'var(--red)' : (p99 > 200 ? 'var(--amber)' : 'var(--text)');
  document.getElementById('m-err').textContent = (err*100).toFixed(1)+'%';
  var st = document.getElementById('m-state'), label;
  if (S.dbDown) label = '宕机';
  else if (load > 1) label = '过载';
  else if (load > 0.8) label = '承压';
  else label = '健康';
  st.textContent = label + (S.dbDown ? '' : ' '+Math.round(S.health*100)+'%');
  st.className = 'v state-' + label;
}

function draw(){
  ctx.clearRect(0,0,W,H);
  var padB = 8, padT = 8;
  var x0 = S.t - WINDOW;
  function X(t){ return (t - x0)/WINDOW * W; }
  function Yq(v){ return H - padB - Math.min(H-padT-padB, (v/S.cap)*(0.30*(H-padT-padB))); }
  function Yp(p){ return H - padB - (p/100)*(H-padT-padB); }

  /* DB 宕机区间底色 */
  ctx.fillStyle = 'rgba(255,92,92,0.10)';
  var i, runStart = null;
  for (i=0;i<S.hist.length;i++){
    if (S.hist[i].down && runStart===null) runStart = S.hist[i].t;
    if ((!S.hist[i].down || i===S.hist.length-1) && runStart!==null){
      var end = S.hist[i].down ? S.hist[i].t : S.hist[i].t;
      ctx.fillRect(X(runStart), 0, Math.max(2, X(end)-X(runStart)), H);
      runStart = null;
    }
  }

  /* 网格 */
  ctx.strokeStyle = 'rgba(138,148,169,0.12)'; ctx.lineWidth = 1;
  for (i=1;i<4;i++){ ctx.beginPath(); ctx.moveTo(0, H*i/4); ctx.lineTo(W, H*i/4); ctx.stroke(); }

  /* 容量虚线 */
  ctx.strokeStyle = 'rgba(138,148,169,0.75)'; ctx.lineWidth = 2; ctx.setLineDash([10,8]);
  ctx.beginPath(); ctx.moveTo(0, Yq(S.cap)); ctx.lineTo(W, Yq(S.cap)); ctx.stroke();
  ctx.setLineDash([]);

  function line(key, Y, color, width){
    ctx.strokeStyle = color; ctx.lineWidth = width; ctx.beginPath();
    var started = false;
    for (var j=0;j<S.hist.length;j++){
      var h = S.hist[j], x = X(h.t), y = Y(h[key]);
      if (!started){ ctx.moveTo(x,y); started = true; } else { ctx.lineTo(x,y); }
    }
    ctx.stroke();
  }
  line('err', Yp, 'rgba(255,92,92,0.95)', 2.5);
  line('hit', Yp, 'rgba(63,210,199,0.95)', 3);
  line('off', Yq, 'rgba(255,180,84,0.95)', 3);
}

/* ---------- 控件 ---------- */
function syncLabels(){
  document.getElementById('lb-qps').textContent = Number(S.qps).toLocaleString()+' QPS';
  document.getElementById('lb-cap').textContent = Number(S.cap).toLocaleString()+' QPS';
}
document.getElementById('sl-qps').addEventListener('input', function(e){
  S.qps = Number(e.target.value); syncLabels();
});
document.getElementById('sl-cap').addEventListener('input', function(e){
  S.cap = Number(e.target.value); syncLabels();
});
document.getElementById('tg-jitter').addEventListener('change', function(e){
  S.jitter = e.target.checked;
  logLine(S.jitter ? '✅ 已开启 TTL 随机抖动：过期洪峰被摊平' : '⚠️ 已关闭 TTL 抖动：key 恢复同批过期');
});
document.getElementById('tg-breaker').addEventListener('change', function(e){
  S.breaker = e.target.checked;
  logLine(S.breaker ? '🛡️ 熔断限流开启：网关按 DB 容量 85% 放行，超出快速失败' : '⚠️ 熔断限流关闭：全部 miss 直达 DB');
});
document.getElementById('btn-crash').addEventListener('click', function(){
  var b = document.getElementById('btn-crash');
  if (S.cacheUp){
    S.cacheUp = false; S.w = 0;
    b.textContent = '🧊 恢复缓存集群'; b.className = 'btn primary';
    logLine('💥 缓存集群宕机：内存数据全部丢失，命中率 → 0');
  } else {
    S.cacheUp = true;
    b.textContent = '💥 缓存集群宕机'; b.className = 'btn danger';
    logLine('🧊 缓存集群已恢复——注意：进程活了，数据是冷的');
  }
});
document.getElementById('btn-pause').addEventListener('click', function(){
  S.running = !S.running;
  this.textContent = S.running ? '暂停' : '继续';
});
document.getElementById('btn-reset').addEventListener('click', function(){ reset(); });

reset();
setInterval(tick, 100);
})();
