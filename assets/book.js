/* 全站共用交互脚本 · 逐字抽取自样章 sample/ch05-cache-brothers.html
   职责仅一项：决策点（data-d）与自测题（data-q）的选项揭示。
   禁止在此引入任何存储（localStorage / sessionStorage）或网络请求。 */
(function(){
"use strict";
/* ---------- 决策点与自测交互 ---------- */
document.querySelectorAll('.opt').forEach(function(btn){
  btn.addEventListener('click', function(){
    var group = btn.parentElement;
    group.querySelectorAll('.opt').forEach(function(b){ b.classList.remove('picked-good','picked-bad'); });
    btn.classList.add(btn.dataset.k === 'bad' ? 'picked-bad' : 'picked-good');
    var id = btn.dataset.d ? 'v-d'+btn.dataset.d : 'v-'+btn.dataset.q;
    var v = document.getElementById(id);
    if (v) v.classList.add('show');
  });
});
})();
