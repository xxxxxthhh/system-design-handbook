#!/usr/bin/env node
/* Sim-5 一致性哈希模拟器 · 无头模型测试
   与 assets/sim-5.js 的状态机逻辑必须保持一致；任一侧改动需同步另一侧。 */
"use strict";

const DT=0.5;
const DEF={nodes:4,vnodes:150,keyCount:10000,mode:"modulo",hotspot:false};
function hash32(text){
  let h=0x811c9dc5;
  for(let i=0;i<text.length;i++){
    h^=text.charCodeAt(i);
    h=Math.imul(h,0x01000193);
  }
  h^=h>>>16;
  h=Math.imul(h,0x85ebca6b);
  h^=h>>>13;
  return h>>>0;
}
function buildRing(nodes,vnodes){
  const ring=[];
  for(let node=0;node<nodes;node++){
    for(let v=0;v<vnodes;v++) ring.push({point:hash32(`node:${node}:vnode:${v}`),node});
  }
  ring.sort((a,b)=>a.point-b.point||a.node-b.node);
  return ring;
}
function ringOwner(hash,ring){
  let lo=0,hi=ring.length;
  while(lo<hi){const mid=(lo+hi)>>>1;if(ring[mid].point<hash)lo=mid+1;else hi=mid;}
  return ring[lo===ring.length?0:lo].node;
}
function ownerFor(key,nodes,vnodes,mode,ring){
  const h=hash32(key);
  return mode==="modulo"?h%nodes:ringOwner(h,ring||buildRing(nodes,vnodes));
}
function assignments(nodes,vnodes,mode,keyCount){
  const ring=mode==="consistent"?buildRing(nodes,vnodes):null;
  const owners=new Array(keyCount);
  for(let i=0;i<keyCount;i++) owners[i]=ownerFor(`key:${i}`,nodes,vnodes,mode,ring);
  return owners;
}
function migrationRatio(nodes,vnodes,mode,keyCount){
  const before=assignments(nodes,vnodes,mode,keyCount);
  const after=assignments(nodes+1,vnodes,mode,keyCount);
  let moved=0;
  for(let i=0;i<keyCount;i++)if(before[i]!==after[i])moved++;
  return moved/keyCount;
}
function snapshot(nodes,vnodes,mode,keyCount,hotspot){
  const owners=assignments(nodes,vnodes,mode,keyCount);
  const loads=Array(nodes).fill(0);
  for(let i=0;i<keyCount;i++)loads[owners[i]]+=hotspot?0.7:1;
  if(hotspot)loads[owners[42]]+=keyCount*0.3;
  const total=loads.reduce((a,b)=>a+b,0),avg=total/nodes,max=Math.max(...loads);
  return {owners,loads,total,avg,max,maxOverAvg:max/avg};
}
function makeState(overrides={}){return Object.assign({t:0,running:true,lastMigration:null},DEF,overrides);}
function tick(S){
  S.t+=DT;
  const snap=snapshot(S.nodes,S.vnodes,S.mode,S.keyCount,S.hotspot);
  return {loads:snap.loads,maxOverAvg:snap.maxOverAvg,migration:S.lastMigration,owners:snap.owners,avg:snap.avg};
}
function expand(S){
  if(S.nodes>=8)return null;
  S.lastMigration=migrationRatio(S.nodes,S.vnodes,S.mode,S.keyCount);
  S.nodes++;
  return S.lastMigration;
}

let pass=0,fail=0;
function assert(name,cond){cond?pass++:fail++;console.log((cond?"PASS":"FAIL")+" · "+name);}

assert("默认参数固定为 4 节点 / 150 虚拟节点 / 10000 key / 取模模式 / 无热点",
  DEF.nodes===4&&DEF.vnodes===150&&DEF.keyCount===10000&&DEF.mode==="modulo"&&!DEF.hotspot);

/* 实验① 4→5 的迁移量级差。 */
const moduloMove=migrationRatio(4,150,"modulo",10000);
const ringMove=migrationRatio(4,150,"consistent",10000);
assert("实验①a 取模 4→5 迁移比例位于 [0.75, 0.85]",moduloMove>=0.75&&moduloMove<=0.85);
assert("实验①b 一致性哈希（150 虚拟节点）4→5 迁移比例位于 [0.12, 0.30]",ringMove>=0.12&&ringMove<=0.30);

/* 实验② 虚拟节点修复天然不均匀。 */
const one=snapshot(4,1,"consistent",10000,false);
const many=snapshot(4,150,"consistent",10000,false);
assert("实验②a 虚拟节点 1→150 后最大负载/平均严格下降",many.maxOverAvg<one.maxOverAvg);
assert("实验②b 150 虚拟节点时最大负载/平均 < 1.30",many.maxOverAvg<1.30);

/* 实验③ 30% 单 key 热点击穿两种分片方式。 */
const hotModulo=snapshot(5,150,"modulo",10000,true);
const hotRing=snapshot(5,150,"consistent",10000,true);
assert("实验③a 取模下注入热点后最热分片/平均 > 2",hotModulo.maxOverAvg>2);
assert("实验③b 一致性哈希下注入热点后最热分片/平均 > 2",hotRing.maxOverAvg>2);

/* 确定性、可复现与极端参数。 */
assert("哈希函数确定性：同一 key 两次结果一致",hash32("same-key")===hash32("same-key"));
const reproA=snapshot(5,150,"consistent",10000,true);
const reproB=snapshot(5,150,"consistent",10000,true);
assert("测试可复现且 key 归属不依赖随机数",JSON.stringify(reproA.loads)===JSON.stringify(reproB.loads));
const extreme=makeState({nodes:8,vnodes:200,keyCount:10000,mode:"consistent",hotspot:true});
let finite=true;
for(let i=0;i<20;i++){
  const r=tick(extreme);
  finite=finite&&Number.isFinite(r.maxOverAvg)&&r.loads.every(Number.isFinite)&&r.loads.every(v=>v>=0);
}
assert("极端参数运行无 NaN/Infinity",finite);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail?1:0);
