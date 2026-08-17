#!/usr/bin/env node
/* Sim-6 积压水位模拟器 · 无头模型测试
   与 assets/sim-6.js 的状态机逻辑必须保持一致；任一侧改动需同步另一侧。 */
"use strict";

const DT=1;
const DEF={produce:100,consumeEach:95,consumers:1};
function makeState(overrides={}){
  return Object.assign({t:0,running:true,backlog:0,floodUntil:0},DEF,overrides);
}
function injectFlood(S){S.floodUntil=Math.max(S.floodUntil,S.t+20);}
function tick(S){
  S.t+=DT;
  const activeProduce=S.t<=S.floodUntil?S.produce*5:S.produce;
  const capacity=S.consumeEach*S.consumers;
  const available=S.backlog+activeProduce*DT;
  const consumed=Math.min(available,capacity*DT);
  S.backlog=Math.max(0,available-consumed);
  const netCatchup=capacity-activeProduce;
  const catchupSeconds=S.backlog===0?0:(netCatchup>0?S.backlog/netCatchup:null);
  return {backlog:S.backlog,produceQps:activeProduce,consumeCapacity:capacity,throughput:consumed/DT,catchupSeconds};
}

let pass=0,fail=0;
function assert(name,cond){cond?pass++:fail++;console.log((cond?"PASS":"FAIL")+" · "+name);}

assert("默认参数固定为生产 100/s / 单消费者 95/s / 1 个消费者",
  DEF.produce===100&&DEF.consumeEach===95&&DEF.consumers===1);

/* 实验① 只差 5% 也会线性积压且不自愈。 */
const slow=makeState({produce:100,consumeEach:95,consumers:1,backlog:100});
const levels=[slow.backlog];
for(let i=0;i<600;i++)levels.push(tick(slow).backlog);
assert("实验①a 消费为生产 95% 时 backlog 600 tick 单调不减",levels.every((v,i)=>i===0||v>=levels[i-1]));
assert("实验①b 600 tick 后末值 > 初值 ×5",levels[levels.length-1]>levels[0]*5);
const rises=levels.slice(1).map((v,i)=>v-levels[i]);
assert("实验①c 水位以恒定斜率线性上涨，不会自行回落",rises.every(v=>Math.abs(v-rises[0])<1e-9)&&rises[0]>0);

/* 实验② 洪峰后消费者翻倍，追平时间可由净消费速率计算。 */
const recovery=makeState();injectFlood(recovery);
for(let i=0;i<20;i++)tick(recovery);
const B=recovery.backlog;
recovery.consumers=2;
const predicted=B/(recovery.consumeEach*recovery.consumers-recovery.produce);
let elapsed=0;
while(recovery.backlog>0&&elapsed<10000){tick(recovery);elapsed+=DT;}
assert("实验②a 开票洪峰确实制造正积压",B>0);
assert("实验②b 消费者翻倍后的实测追平时间与公式误差 <10%",Math.abs(elapsed-predicted)/predicted<0.10);

/* 实验③ 超额消费先清零，随后吞吐受生产速率限制。 */
const drain=makeState({produce:100,consumeEach:100,consumers:3,backlog:1000});
let nonnegative=true;
for(let i=0;i<20;i++){tick(drain);nonnegative=nonnegative&&drain.backlog>=0;}
assert("实验③a 消费 > 生产时 backlog 收敛到 0 且不为负",drain.backlog===0&&nonnegative);
const three=makeState({produce:100,consumeEach:100,consumers:3,backlog:1000});
const five=makeState({produce:100,consumeEach:100,consumers:5,backlog:1000});
const t3=three.backlog/(three.consumeEach*three.consumers-three.produce);
const t5=five.backlog/(five.consumeEach*five.consumers-five.produce);
while(three.backlog>0)tick(three);const post3=tick(three).throughput;
while(five.backlog>0)tick(five);const post5=tick(five).throughput;
assert("实验③b 消费者从 3 倍加到 5 倍后追平时间下降",t5<t3);
assert("实验③c 积压清零后继续加消费者，吞吐不再上升",post3===three.produce&&post5===five.produce&&post3===post5);

/* 极端参数、连点洪峰与长时间运行。 */
const extreme=makeState({produce:1000,consumeEach:1,consumers:1});
let finite=true;
for(let i=0;i<2000;i++){
  if(i%3===0)injectFlood(extreme);
  const r=tick(extreme);
  finite=finite&&Number.isFinite(r.backlog)&&Number.isFinite(r.produceQps)&&Number.isFinite(r.consumeCapacity)&&Number.isFinite(r.throughput)&&(r.catchupSeconds===null||Number.isFinite(r.catchupSeconds))&&r.backlog>=0;
}
assert("极端参数与连点洪峰运行 2000 tick 无 NaN/Infinity",finite);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail?1:0);
