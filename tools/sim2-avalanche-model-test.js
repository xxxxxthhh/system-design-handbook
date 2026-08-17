#!/usr/bin/env node
/* Sim-2 缓存雪崩模拟器 · 无头模型测试（QUALITY.md 第三节协议的参考实现）
   断言正文实验清单声称的全部现象。页面状态机逻辑变更时必须同步本文件。 */
"use strict";
function makeState(){ return { t:0,qps:10000,cap:800,jitter:false,breaker:false,cacheUp:true,w:0.99,health:1,dbDown:false,cd:0,lastBatch:0 }; }
const DT = 0.5;
function tick(S){
  S.t += DT;
  if (S.cacheUp){
    if (S.jitter){ S.w -= S.w*(0.2/60)*DT; }
    else if (S.t - S.lastBatch >= 60){ S.w *= 0.8; S.lastBatch = S.t; }
  } else S.w = 0;
  const hit = 0.995*S.w, off = S.qps*(1-hit);
  const admitted = S.breaker ? Math.min(off, S.cap*0.85) : off;
  let served = 0, load = 0;
  if (S.dbDown){
    if (admitted <= S.cap*0.9){ S.cd += DT; } else { S.cd = 0; }
    if (S.cd >= 6){ S.dbDown = false; S.health = 0.35; S.cd = 0; }
  } else {
    served = Math.min(admitted, S.cap); load = admitted/S.cap;
    if (load > 1) S.health -= Math.min(0.35,(load-1)*0.04)*DT;
    else if (load < 0.95) S.health = Math.min(1, S.health + 0.08*DT);
    if (S.health <= 0){ S.health = 0; S.dbDown = true; S.cd = 0; }
  }
  if (S.cacheUp){ S.w += (1-S.w)*(served/8000)*DT; if (S.w > 0.995) S.w = 0.995; }
  return { hit, off, load };
}
let pass = 0, fail = 0;
function assert(name, cond){ cond ? pass++ : fail++; console.log((cond?"PASS":"FAIL")+" · "+name); }

/* 实验① 同批过期产生尖刺但 DB 存活；开抖动后无尖刺 */
let S = makeState(), died = false, peak = 0;
for (let i=0;i<600;i++){ const r = tick(S); peak = Math.max(peak, r.load); if (S.dbDown) died = true; }
assert("实验①a 同批过期产生过载尖刺 (峰值负载>2x)", peak > 2);
assert("实验①b 尖刺不致命 (DB 存活)", !died);
S = makeState(); S.jitter = true; peak = 0;
for (let i=0;i<600;i++){ const r = tick(S); if (S.t > 30) peak = Math.max(peak, r.load); }
assert("实验①c 抖动摊平洪峰 (稳态负载<1)", peak < 1);

/* 实验② 缓存宕机杀死 DB；恢复冷缓存后无熔断 → 死亡螺旋 */
S = makeState(); for (let i=0;i<100;i++) tick(S);
S.cacheUp = false; S.w = 0;
for (let i=0;i<40;i++) tick(S);
assert("实验②a 缓存宕机数秒内打死 DB", S.dbDown);
S.cacheUp = true;                       // 恢复冷缓存，不开熔断
let recovered = false;
for (let i=0;i<600;i++){ tick(S); if (!S.dbDown) recovered = true; }
assert("实验②b 死亡螺旋：无熔断则 DB 永不恢复", !recovered && 0.995*S.w < 0.01);

/* 实验③ 开熔断打破螺旋：DB 重启、缓存回暖、系统恢复 */
S.breaker = true;
let restarted = false;
for (let i=0;i<1200;i++){ tick(S); if (!S.dbDown) restarted = true; }
assert("实验③a 熔断后 DB 得以重启", restarted);
assert("实验③b 缓存回暖 (命中率>93%)", 0.995*S.w > 0.93);
assert("实验③c 恢复后 DB 负载回到容量线下", S.qps*(1-0.995*S.w) < S.cap);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
