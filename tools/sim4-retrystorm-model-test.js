#!/usr/bin/env node
/* Sim-4 重试风暴模拟器 · 无头模型测试
   与 assets/sim-4.js 的状态机逻辑必须保持一致；任一侧改动需同步另一侧。 */
"use strict";

const DT=0.1;
const DEF={layers:3,attempts:3,backoff:false,jitter:false,failureRate:1};
function makeState(overrides={}){
  return Object.assign({t:0,running:true,events:[],injected:0,delivered:0},DEF,overrides);
}
function expectedAmplification(S){
  let perLayer=0;
  for(let i=0;i<S.attempts;i++) perLayer+=Math.pow(S.failureRate,i);
  return Math.pow(perLayer,S.layers);
}
function jitterFactor(comboIndex,layer){
  let x=((comboIndex+1)*1103515245+(layer+1)*12345)>>>0;
  x=(x^(x>>>16))>>>0;
  return 0.5+(x%10001)/10000;
}
function injectFailure(S){
  const total=Math.pow(S.attempts,S.layers);
  for(let combo=0;combo<total;combo++){
    let n=combo,delay=0,weight=1;
    for(let layer=0;layer<S.layers;layer++){
      const attempt=n%S.attempts;
      n=Math.floor(n/S.attempts);
      weight*=Math.pow(S.failureRate,attempt);
      if(S.backoff&&attempt>0){
        let part=(Math.pow(2,attempt)-1)*0.4;
        if(S.jitter) part*=jitterFactor(combo,layer);
        delay+=part;
      }
    }
    S.events.push({at:S.t+delay,weight:weight});
  }
  S.events.sort((a,b)=>a.at-b.at);
  S.injected++;
}
function tick(S){
  S.t+=DT;
  let terminal=0,keep=[];
  for(const event of S.events){
    if(event.at<=S.t+1e-9) terminal+=event.weight;
    else keep.push(event);
  }
  S.events=keep;
  S.delivered+=terminal;
  return {terminalQps:terminal/DT,amplification:expectedAmplification(S),cumulative:S.delivered,pending:S.events.length};
}

let pass=0,fail=0;
function assert(name,cond){cond?pass++:fail++;console.log((cond?"PASS":"FAIL")+" · "+name);}
function runWave(overrides,ticks=200){
  const S=makeState(overrides);injectFailure(S);const qps=[];let r;
  for(let i=0;i<ticks;i++){r=tick(S);qps.push(r.terminalQps);}
  return {S,r,qps,total:S.delivered,peak:Math.max(...qps)};
}

assert("默认参数固定为 3 层 / 每层 3 次尝试 / backoff 关 / jitter 关 / 故障率 100%",
  DEF.layers===3&&DEF.attempts===3&&!DEF.backoff&&!DEF.jitter&&DEF.failureRate===1);

/* 实验① 重试放大是各层尝试次数的乘积。 */
const amp1=expectedAmplification(makeState({layers:1,attempts:3}));
const amp2=expectedAmplification(makeState({layers:2,attempts:3}));
const amp3=expectedAmplification(makeState({layers:3,attempts:3}));
assert("实验①a 1 层 × 3 次尝试的放大倍数 ≈ 3（误差 <5%）",Math.abs(amp1-3)/3<0.05);
assert("实验①b 2 层 × 3 次尝试的放大倍数 ≈ 9（误差 <5%）",Math.abs(amp2-9)/9<0.05);
assert("实验①c 3 层 × 3 次尝试的放大倍数 ≈ 27（误差 <5%）",Math.abs(amp3-27)/27<0.05);
assert("实验①d 层数 1 且每层 1 次尝试时放大倍数 = 1",expectedAmplification(makeState({layers:1,attempts:1}))===1);

/* 实验② backoff 改波形，不改总量。 */
const noBackoff=runWave({layers:3,attempts:3,backoff:false,jitter:false});
const backoff=runWave({layers:3,attempts:3,backoff:true,jitter:false});
assert("实验②a backoff 前后累计请求数变化 <10%",Math.abs(backoff.total-noBackoff.total)/noBackoff.total<0.10);
assert("实验②b backoff 使峰值下降 >40%",backoff.peak<noBackoff.peak*0.60);

/* 实验③ jitter 打散同刻重发。 */
const jittered=runWave({layers:3,attempts:3,backoff:true,jitter:true});
assert("实验③ jitter 使峰值再次严格下降",jittered.peak<backoff.peak);

/* 极端参数、连点注入与长时间运行。 */
const extreme=makeState({layers:4,attempts:4,backoff:true,jitter:true,failureRate:1});
let finite=true;
for(let i=0;i<2000;i++){
  if(i%100===0) injectFailure(extreme);
  const r=tick(extreme);
  finite=finite&&Object.values(r).every(Number.isFinite)&&extreme.events.every(e=>Number.isFinite(e.at)&&Number.isFinite(e.weight));
}
assert("极端参数与连点注入运行 2000 tick 无 NaN/Infinity",finite);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail?1:0);
