/* Sim-5 · 一致性哈希模拟器（第 8 章） */
/* 与 tools/sim5-hashring-model-test.js 逻辑必须一致。 */
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
  if(redraw&&lastResult){
    try{draw(lastResult);}catch(e){}
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

var DT=0.5;
var DEF={nodes:4,vnodes:150,keyCount:10000,mode:'modulo',hotspot:false};
var S,lastResult;
function hash32(text){
  var h=0x811c9dc5;
  for(var i=0;i<text.length;i++){
    h^=text.charCodeAt(i);
    h=Math.imul(h,0x01000193);
  }
  h^=h>>>16;
  h=Math.imul(h,0x85ebca6b);
  h^=h>>>13;
  return h>>>0;
}
function buildRing(nodes,vnodes){
  var ring=[];
  for(var node=0;node<nodes;node++){
    for(var v=0;v<vnodes;v++)ring.push({point:hash32('node:'+node+':vnode:'+v),node:node});
  }
  ring.sort(function(a,b){return a.point-b.point||a.node-b.node;});
  return ring;
}
function ringOwner(hash,ring){
  var lo=0,hi=ring.length;
  while(lo<hi){var mid=(lo+hi)>>>1;if(ring[mid].point<hash)lo=mid+1;else hi=mid;}
  return ring[lo===ring.length?0:lo].node;
}
function ownerFor(key,nodes,vnodes,mode,ring){
  var h=hash32(key);
  return mode==='modulo'?h%nodes:ringOwner(h,ring||buildRing(nodes,vnodes));
}
function assignments(nodes,vnodes,mode,keyCount){
  var ring=mode==='consistent'?buildRing(nodes,vnodes):null;
  var owners=new Array(keyCount);
  for(var i=0;i<keyCount;i++)owners[i]=ownerFor('key:'+i,nodes,vnodes,mode,ring);
  return owners;
}
function migrationRatio(nodes,vnodes,mode,keyCount){
  var before=assignments(nodes,vnodes,mode,keyCount);
  var after=assignments(nodes+1,vnodes,mode,keyCount);
  var moved=0;
  for(var i=0;i<keyCount;i++)if(before[i]!==after[i])moved++;
  return moved/keyCount;
}
function snapshot(nodes,vnodes,mode,keyCount,hotspot){
  var owners=assignments(nodes,vnodes,mode,keyCount);
  var loads=Array(nodes).fill(0);
  for(var i=0;i<keyCount;i++)loads[owners[i]]+=hotspot?0.7:1;
  if(hotspot)loads[owners[42]]+=keyCount*0.3;
  var total=loads.reduce(function(a,b){return a+b;},0),avg=total/nodes,max=Math.max.apply(null,loads);
  return {owners:owners,loads:loads,total:total,avg:avg,max:max,maxOverAvg:max/avg};
}
function makeState(overrides){return Object.assign({t:0,running:true,lastMigration:null},DEF,overrides||{});}
function modelTick(S){
  S.t+=DT;
  var snap=snapshot(S.nodes,S.vnodes,S.mode,S.keyCount,S.hotspot);
  return {loads:snap.loads,maxOverAvg:snap.maxOverAvg,migration:S.lastMigration,owners:snap.owners,avg:snap.avg};
}
function expand(S){
  if(S.nodes>=8)return null;
  S.lastMigration=migrationRatio(S.nodes,S.vnodes,S.mode,S.keyCount);
  S.nodes++;
  return S.lastMigration;
}

function reset(){
  S=makeState();lastResult=null;
  document.getElementById('sl-nodes').value=DEF.nodes;
  document.getElementById('sl-vnodes').value=DEF.vnodes;
  document.getElementById('tg-mode').checked=false;
  document.getElementById('tg-hotspot').checked=false;
  document.getElementById('btn-pause').textContent='暂停';
  document.getElementById('log').innerHTML='';
  syncLabels();logLine('10,000 个 key 已按取模分到 4 台节点。');
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
  lastResult=modelTick(S);draw(lastResult);readouts(lastResult);
}
function readouts(r){
  document.getElementById('clock').textContent=clockStr();
  document.getElementById('m-mode').textContent=S.mode==='modulo'?'取模':'一致性哈希';
  document.getElementById('m-migration').textContent=r.migration===null?'尚未扩容':(r.migration*100).toFixed(1)+'%';
  document.getElementById('m-imbalance').textContent=r.maxOverAvg.toFixed(2)+'×';
  document.getElementById('m-hot').textContent=S.hotspot?'30% 单 key':'关闭';
}
function draw(r){
  ctx.clearRect(0,0,W,H);
  var colors=['rgba(63,210,199,0.95)','rgba(255,180,84,0.95)','rgba(255,92,92,0.95)','rgba(76,195,138,0.95)','rgba(138,148,169,0.95)','rgba(220,227,242,0.95)','rgba(63,210,199,0.65)','rgba(255,180,84,0.65)'];
  var cx=W*0.25,cy=H/2,rad=Math.min(180,H*0.37),i;
  ctx.strokeStyle='rgba(138,148,169,0.35)';ctx.lineWidth=3;ctx.beginPath();ctx.arc(cx,cy,rad,0,Math.PI*2);ctx.stroke();
  /* key 密度：固定抽样，不使用随机数。 */
  for(i=0;i<240;i++){
    var kh=hash32('key:'+(i*41%S.keyCount)),ka=kh/4294967296*Math.PI*2-Math.PI/2;
    ctx.fillStyle='rgba(138,148,169,0.38)';ctx.beginPath();ctx.arc(cx+Math.cos(ka)*(rad-10),cy+Math.sin(ka)*(rad-10),1.5,0,Math.PI*2);ctx.fill();
  }
  var ring=S.mode==='consistent'?buildRing(S.nodes,S.vnodes):null;
  if(ring){
    for(i=0;i<ring.length;i+=Math.max(1,Math.floor(ring.length/280))){
      var ra=ring[i].point/4294967296*Math.PI*2-Math.PI/2;
      ctx.fillStyle=colors[ring[i].node];ctx.fillRect(cx+Math.cos(ra)*(rad+2)-1,cy+Math.sin(ra)*(rad+2)-1,3,3);
    }
  }
  for(i=0;i<S.nodes;i++){
    var a=(i/S.nodes)*Math.PI*2-Math.PI/2;
    ctx.fillStyle=colors[i];ctx.beginPath();ctx.arc(cx+Math.cos(a)*rad,cy+Math.sin(a)*rad,8,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='rgba(220,227,242,0.92)';ctx.font='18px monospace';ctx.fillText('N'+(i+1),cx+Math.cos(a)*(rad+28)-12,cy+Math.sin(a)*(rad+28)+6);
  }
  /* 右侧负载柱状图。 */
  var x0=W*0.54,areaW=W*0.42,barGap=18,barW=(areaW-barGap*(S.nodes-1))/S.nodes;
  var maxLoad=Math.max.apply(null,r.loads.concat([r.avg*1.15]));
  ctx.strokeStyle='rgba(138,148,169,0.60)';ctx.lineWidth=2;ctx.setLineDash([9,7]);
  var avgY=H-45-r.avg/maxLoad*(H-90);ctx.beginPath();ctx.moveTo(x0,avgY);ctx.lineTo(x0+areaW,avgY);ctx.stroke();ctx.setLineDash([]);
  for(i=0;i<S.nodes;i++){
    var bh=r.loads[i]/maxLoad*(H-90),bx=x0+i*(barW+barGap),by=H-45-bh;
    ctx.fillStyle=colors[i];ctx.fillRect(bx,by,barW,bh);
    ctx.fillStyle='rgba(220,227,242,0.92)';ctx.font='17px monospace';ctx.fillText('N'+(i+1),bx+barW/2-12,H-16);
  }
}
function syncLabels(){
  document.getElementById('lb-nodes').textContent=S.nodes+' 台';
  document.getElementById('lb-vnodes').textContent=S.vnodes+' / 节点';
}
document.getElementById('sl-nodes').addEventListener('input',function(e){S.nodes=Number(e.target.value);S.lastMigration=null;syncLabels();});
document.getElementById('sl-vnodes').addEventListener('input',function(e){S.vnodes=Number(e.target.value);S.lastMigration=null;syncLabels();});
document.getElementById('tg-mode').addEventListener('change',function(e){
  S.mode=e.target.checked?'consistent':'modulo';S.lastMigration=null;
  logLine(S.mode==='consistent'?'🔄 切到一致性哈希环。':'🔢 切到取模分片。');
});
document.getElementById('tg-hotspot').addEventListener('change',function(e){
  S.hotspot=e.target.checked;logLine(S.hotspot?'🔥 单个 key 现在承载总流量的 30%。':'热点流量已移除。');
});
document.getElementById('btn-expand').addEventListener('click',function(){
  var moved=expand(S);
  if(moved===null){logLine('节点已到上限 8 台。');return;}
  document.getElementById('sl-nodes').value=S.nodes;syncLabels();
  logLine('➕ 扩容到 '+S.nodes+' 台，迁移 '+(moved*100).toFixed(1)+'% key。');
});
document.getElementById('btn-pause').addEventListener('click',function(){S.running=!S.running;this.textContent=S.running?'暂停':'继续';});
document.getElementById('btn-reset').addEventListener('click',function(){reset();});

reset();
setInterval(tick,500);
})();
