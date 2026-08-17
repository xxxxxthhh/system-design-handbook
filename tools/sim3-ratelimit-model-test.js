#!/usr/bin/env node
/* Sim-3 限流算法对比模拟器 · 无头模型测试
   与 assets/sim-3.js 的状态机逻辑必须保持一致；任一侧改动需同步另一侧。 */
"use strict";

const DT = 0.1;
const DEF = { multiplier:5, baseQps:80, limit:100, burst:100 };
function makeState(overrides = {}){
  const cfg = Object.assign({}, DEF, overrides);
  return Object.assign({
    t:0, running:true, burstUntil:0, tokens:cfg.burst, leakQueue:0,
    swBuckets:Array(10).fill(0), swIndex:0
  }, cfg);
}
function injectBurst(S){ S.burstUntil = Math.max(S.burstUntil, S.t+0.5); }

function tick(S){
  S.t += DT;
  const arrivalQps = S.t <= S.burstUntil ? S.baseQps*S.multiplier : S.baseQps;
  const arrivals = arrivalQps*DT;

  S.tokens = Math.min(S.burst, S.tokens+S.limit*DT);
  const tokenAllowed = Math.min(arrivals, S.tokens);
  S.tokens -= tokenAllowed;
  const tokenRejected = arrivals-tokenAllowed;

  const leakCapacity = Math.max(S.burst*4, S.limit*DT);
  const leakAdmitted = Math.min(arrivals, Math.max(0, leakCapacity-S.leakQueue));
  const leakRejected = arrivals-leakAdmitted;
  S.leakQueue += leakAdmitted;
  const leakAllowed = Math.min(S.leakQueue, S.limit*DT);
  S.leakQueue -= leakAllowed;

  S.swIndex = (S.swIndex+1)%10;
  S.swBuckets[S.swIndex] = 0;
  const windowUsed = S.swBuckets.reduce((a,b)=>a+b,0);
  const windowLeft = Math.max(0, S.limit-windowUsed);
  const windowAllowed = Math.min(arrivals, windowLeft);
  S.swBuckets[S.swIndex] = windowAllowed;
  const windowRejected = arrivals-windowAllowed;

  return {
    arrivalQps:arrivalQps,
    tokenQps:tokenAllowed/DT, leakQps:leakAllowed/DT, windowQps:windowAllowed/DT,
    tokenRejectedQps:tokenRejected/DT, leakRejectedQps:leakRejected/DT,
    windowRejectedQps:windowRejected/DT
  };
}

let pass=0, fail=0;
function assert(name,cond){ cond?pass++:fail++; console.log((cond?"PASS":"FAIL")+" · "+name); }
function variance(xs){ const m=xs.reduce((a,b)=>a+b,0)/xs.length; return xs.reduce((a,b)=>a+(b-m)*(b-m),0)/xs.length; }
function warm(S,n=30){ let r; for(let i=0;i<n;i++) r=tick(S); return r; }
function burstRun(overrides){
  const S=makeState(overrides); warm(S); injectBurst(S); const rows=[];
  for(let i=0;i<30;i++) rows.push(tick(S));
  return rows;
}

assert("默认参数固定为 5× 突发 / 80 基础 QPS / 100 配额 / 100 桶深",
  DEF.multiplier===5 && DEF.baseQps===80 && DEF.limit===100 && DEF.burst===100);

/* 实验① 同一突发的三种形状。 */
const wave=burstRun({});
const burstTicks=wave.slice(0,5);
const tokenTotal=burstTicks.reduce((a,r)=>a+r.tokenQps*DT,0);
const leakTotal=burstTicks.reduce((a,r)=>a+r.leakQps*DT,0);
const tokenWave=wave.map(r=>r.tokenQps), leakWave=wave.map(r=>r.leakQps);
assert("实验①a 突发窗口内令牌桶累计放行 > 漏桶累计放行", tokenTotal>leakTotal);
assert("实验①b 令牌桶先出现高于配额的尖头，再回落到配额", Math.max(...tokenWave)>DEF.limit && tokenWave.slice(1).some(v=>Math.abs(v-DEF.limit)<1e-9));
assert("实验①c 漏桶在有积压时保持配额直线", leakWave.slice(0,15).every(v=>Math.abs(v-DEF.limit)<1e-9));
assert("实验①d 漏桶输出方差 < 令牌桶输出方差", variance(leakWave)<variance(tokenWave));
assert("实验①e 滑动窗口以离散台阶响应突发", new Set(wave.slice(0,12).map(r=>r.windowQps.toFixed(6))).size>=2);

/* 实验② 桶深决定令牌桶愿意向下游放过的尖头。 */
const small=burstRun({burst:20}), large=burstRun({burst:40});
const smallPeak=Math.max(...small.slice(0,5).map(r=>r.tokenQps));
const largePeak=Math.max(...large.slice(0,5).map(r=>r.tokenQps));
assert("实验② 桶深翻倍后令牌桶突发峰值严格上升", largePeak>smallPeak);

/* 实验③ 无突发稳态只取决于 min(到达, 配额)。 */
const steady=makeState({baseQps:150,limit:100,burst:100});
const tail=[];
for(let i=0;i<300;i++){ const r=tick(steady); if(i>=200) tail.push(r); }
function avg(key){ return tail.reduce((a,r)=>a+r[key],0)/tail.length; }
const target=Math.min(steady.baseQps,steady.limit);
assert("实验③a 令牌桶稳态放行量收敛到配额（误差 <10%）", Math.abs(avg("tokenQps")-target)/target<0.10);
assert("实验③b 漏桶稳态放行量收敛到配额（误差 <10%）", Math.abs(avg("leakQps")-target)/target<0.10);
assert("实验③c 滑动窗口稳态放行量收敛到配额（误差 <10%）", Math.abs(avg("windowQps")-target)/target<0.10);
const steadyMeans=[avg("tokenQps"),avg("leakQps"),avg("windowQps")];
assert("实验③d 三种算法稳态差异 < 10%，差别只在瞬态", (Math.max(...steadyMeans)-Math.min(...steadyMeans))/target<0.10);

/* 极端值、连点突发与长时间运行。 */
const extreme=makeState({multiplier:20,baseQps:1000,limit:1,burst:500});
let finite=true;
for(let i=0;i<2000;i++){
  if(i%3===0) injectBurst(extreme);
  const r=tick(extreme);
  finite=finite && Object.values(r).every(Number.isFinite) && Number.isFinite(extreme.tokens) && Number.isFinite(extreme.leakQueue);
}
assert("极端参数与连点突发运行 2000 tick 无 NaN/Infinity", finite);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail?1:0);
