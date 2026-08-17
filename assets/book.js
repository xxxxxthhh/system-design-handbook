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
    var id = btn.dataset.d ? 'v-d'+btn.dataset.d
           : btn.dataset.f ? 'v-f'+btn.dataset.f
           : 'v-'+btn.dataset.q;
    var v = document.getElementById(id);
    if (v) v.classList.add('show');
  });
});

/* ---------- 交卷练习：先写下来，再看基准答案 ---------- */
document.querySelectorAll('.ex-reveal').forEach(function(btn){
  btn.addEventListener('click', function(){
    var box = btn.closest('.exercise');
    if (!box) return;
    var ta = box.querySelector('.ex-input');
    var warn = box.querySelector('.ex-warn');
    /* 空着就想看答案：先拦一次。再点一次才放行——不做强制，只做摩擦。 */
    if (ta && !ta.value.trim() && btn.dataset.armed !== '1'){
      btn.dataset.armed = '1';
      if (warn) warn.classList.add('show');
      return;
    }
    var model = box.querySelector('.ex-model');
    if (model) model.classList.add('show');
    btn.disabled = true;
    btn.textContent = '基准答案已展开';
  });
});
})();
