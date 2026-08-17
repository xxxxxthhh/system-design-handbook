#!/usr/bin/env node
/* Sim-1 排队论模拟器 · 无头模型测试
   与 assets/sim-1.js 的状态机逻辑必须保持一致；任一侧改动需同步另一侧。 */
"use strict";

const DT = 0.1;
const DEF = { qps:80, serviceMs:100, concurrency:10, timeoutMs:10000, usefulConcurrency:10 };
function makeState(overrides = {}){
  return Object.assign({
    t:0, qps:DEF.qps, serviceMs:DEF.serviceMs, concurrency:DEF.concurrency,
    timeoutMs:DEF.timeoutMs, usefulConcurrency:DEF.usefulConcurrency,
    backlog:0, running:true
  }, overrides);
}

function tick(S){
  S.t += DT;

  /* 超过下游有效并行度后，额外槽位只制造争用，不增加服务能力。 */
  const contention = Math.max(1, S.concurrency / S.usefulConcurrency);
  const effectiveServiceMs = S.serviceMs * contention;
  const cap = S.concurrency / (effectiveServiceMs / 1000);
  const rho = cap > 0 ? S.qps / cap : 1e6;

  const overflow = Math.max(0, S.qps - cap) * DT;
  S.backlog += overflow;
  const maxBacklog = Math.max(0, cap * S.timeoutMs / 1000);
  const expired = Math.max(0, S.backlog - maxBacklog);
  S.backlog -= expired;

  let queueMs;
  if (rho < 1){
    queueMs = effectiveServiceMs * rho / Math.max(0.001, 1 - rho);
    S.backlog = Math.max(0, S.backlog - (cap - S.qps) * DT);
  } else {
    queueMs = cap > 0 ? S.backlog / cap * 1000 : S.timeoutMs;
  }
  const rawP50 = effectiveServiceMs + 0.7 * queueMs;
  const rawP99 = effectiveServiceMs + 4 * queueMs;
  const timeoutRate = rawP99 > S.timeoutMs ? Math.min(1, 1 - S.timeoutMs / rawP99) : 0;
  const errorRate = Math.min(1, Math.max(timeoutRate, S.qps > 0 ? expired / (S.qps * DT) : 0));
  const p50 = Math.min(rawP50, Math.max(effectiveServiceMs, S.timeoutMs * 0.7));
  const p99 = Math.min(rawP99, Math.max(effectiveServiceMs, S.timeoutMs * 0.9));
  /* 吞吐计已处理请求：成功和超时都会完成生命周期并释放槽位。 */
  const throughput = Math.min(S.qps, cap);

  return { cap, rho, queueMs, p50, p99, rawP99, errorRate, throughput, effectiveServiceMs };
}

let pass = 0, fail = 0;
function assert(name, cond){ cond ? pass++ : fail++; console.log((cond ? "PASS" : "FAIL")+" · "+name); }
function steady(overrides, ticks = 600){
  const S = makeState(overrides); let r;
  for (let i=0;i<ticks;i++) r = tick(S);
  return { S, r };
}

assert("默认参数固定为 80 QPS / 100ms / 10 并发 / 10000ms 超时",
  DEF.qps === 80 && DEF.serviceMs === 100 && DEF.concurrency === 10 && DEF.timeoutMs === 10000);

/* 实验① ρ 线性上升，而 P99 在 ρ→1 时起飞。 */
const a50 = steady({ qps:50 }).r;
const a80 = steady({ qps:80 }).r;
const a95 = steady({ qps:95 }).r;
assert("实验①a ρ 三点准确落在 50% / 80% / 95%",
  Math.abs(a50.rho-0.5)<1e-9 && Math.abs(a80.rho-0.8)<1e-9 && Math.abs(a95.rho-0.95)<1e-9);
assert("实验①b P99 随 ρ 单调上升", a50.p99 < a80.p99 && a80.p99 < a95.p99);
assert("实验①c P99(0.95) > 4 × P99(0.5)", a95.p99 > 4*a50.p99);

/* 实验② 下游有效并行度不变时，加大连接池只增加争用。 */
const b10 = steady({ qps:95, concurrency:10 }).r;
const b20 = steady({ qps:95, concurrency:20 }).r;
assert("实验②a 并发翻倍后稳态吞吐变化 < 10%",
  Math.abs(b20.throughput-b10.throughput)/b10.throughput < 0.10);
assert("实验②b 并发翻倍后 P99 不下降", b20.p99 >= b10.p99);
assert("实验②c 并发翻倍后排队更深", b20.queueMs > b10.queueMs);

/* 实验③ 超时是止损单：更多快速失败，换取存活请求延迟。 */
const cWide = steady({ qps:95, timeoutMs:3000 }).r;
const cNarrow = steady({ qps:95, timeoutMs:300 }).r;
assert("实验③a 超时 3000ms→300ms 后错误率上升", cNarrow.errorRate > cWide.errorRate);
assert("实验③b 存活请求 P99 下降 > 50%", cNarrow.p99 < cWide.p99*0.5);

/* 极端参数与长时间运行。 */
const extreme = makeState({ qps:1000, serviceMs:2000, concurrency:1, timeoutMs:50 });
let finite = true;
for (let i=0;i<2000;i++){
  const r = tick(extreme);
  finite = finite && Object.values(r).every(Number.isFinite) && Number.isFinite(extreme.backlog) && extreme.backlog >= 0;
}
assert("极端参数运行 2000 tick 无 NaN/Infinity", finite);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
