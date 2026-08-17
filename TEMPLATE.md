# TEMPLATE.md · 页面骨架（照抄，不要重新发明）

视觉唯一基准是 `sample/ch05-cache-brothers.html` 与已转换的 `ch05.html`。
所有样式都在 `assets/style.css`，**页面里不许再写 `<style>` 块**，
只允许极少量 `style="..."` 内联微调，且**只能使用已有 CSS 变量**（如 `style="color:var(--amber)"`）。
禁止裸色值（`#xxxxxx` / `rgb()` 一律不许出现在 HTML 里）。

---

## A. 章节页骨架（ch01–ch16）

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>第 N 章 · 章节标题 | 系统是被打出来的</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header>
  <div class="book-bar"><span><b>系统是被打出来的</b> · 系统设计实战手册</span><nav aria-label="章节导航"><a href="上一页.html">← 上一章</a><a href="index.html">目录</a><a href="下一页.html">下一章 →</a></nav></div>
  <div class="chapter-head">
    <div class="eyebrow">PART X · 分部名 · 第 N 章</div>
    <h1>主标题<br>副标题</h1>
    <p class="h1-sub">一句 40–70 字的引子：本章会打你哪一下、你会学到什么。</p>
  </div>
</header>

<div class="wrap">

<!-- ========== ·1 值班现场 ========== -->
<h2><span class="sec">NN · 1 值班现场</span>时间点，一句现场白描</h2>
<p class="lead">…第二人称开场，交代你是谁、在干什么…</p>

<div class="pager" aria-label="P0 告警">
  <div class="pager-top"><span class="dot" aria-hidden="true"></span>PagerDuty · P0 · 触发于 HH:MM:SS</div>
  <div class="pager-body">
[<span class="r">CRITICAL</span>] …<br>
[<span class="a">WARNING</span>] &nbsp;…<br>
<span class="g">──────────────────────────────────────</span><br>
<span class="g">…上下文线索…</span><br>
<span class="t">「…群里最后一条消息…」</span>
  </div>
</div>

<div class="metrics">
  <div class="metric"><div class="k">指标名</div><div class="v">数值</div><div class="d up">▲ 平时约 …</div></div>
  <!-- 4 张左右；.d 的修饰类：up(红) / down(青) / warn(黄) -->
</div>

<p>…把线索串成判断，信息量必须足够读者自己做决定…</p>

<div class="decision" id="d1">
  <span class="decision-tag">决策点 D1</span>
  <h3>此刻是 HH:MM。你的第一个动作是什么？</h3>
  <button class="opt" data-d="1" data-k="bad"><span class="tag">A</span>…</button>
  <button class="opt" data-d="1" data-k="good"><span class="tag">B</span>…</button>
  <button class="opt" data-d="1" data-k="bad"><span class="tag">C</span>…</button>
  <button class="opt" data-d="1" data-k="mid"><span class="tag">D</span>…</button>
  <div class="verdict" id="v-d1">
    <p><b class="good">B 是教科书答案：…</b>…</p>
    <p><b class="bad">A 的问题是…</b>…</p>
    <p><b class="bad">C 会让事情更糟。</b>…</p>
    <p><b class="mid">D 方向没错，但…</b>…</p>
  </div>
</div>

<!-- ========== ·2 原理 ========== -->
<h2><span class="sec">NN · 2 原理</span>本章机制的一句话命名</h2>
<p>…</p>

<!-- 契约级公式：用无告警色的 pager 做公式牌 -->
<div class="pager" style="border-color:var(--line)">
  <div class="pager-body" style="font-size:15px;text-align:center">
公式原文
  </div>
</div>

<p>…代入具体数字演示…</p>
<div class="metrics" style="grid-template-columns:repeat(auto-fit,minmax(120px,1fr))">
  <div class="metric"><div class="k">条件</div><div class="v" style="color:var(--green)">结果</div><div class="d">单位</div></div>
</div>

<div class="kicker">一句把本章拔高的话。</div>

<!-- ========== ·3 病历卡 ========== -->
<h2><span class="sec">NN · 3 病历卡</span>本章的死法</h2>

<!-- 定义新卡：五行固定顺序 机理/症状/易发场景/处方/案例 -->
<div class="case-card">
  <div class="case-head"><h3>卡名</h3><span class="case-no">病历卡 No.NN</span></div>
  <div class="case-alias">English Name · 一句话定性</div>
  <div class="case-body">
    <div class="case-row"><div class="lbl">机理</div><div class="val">…</div></div>
    <div class="case-row"><div class="lbl">症状</div><div class="val"><span class="sym">▁▂▅███</span>　形状名。…</div></div>
    <div class="case-row"><div class="lbl">易发场景</div><div class="val">…</div></div>
    <div class="case-row"><div class="lbl">处方</div><div class="val">① <strong>…</strong>：…；② <strong>…</strong>：…；③ …</div></div>
    <div class="case-row"><div class="lbl">案例</div><div class="val">…（「秒抢」剧情或明确标注的公开报道）</div></div>
  </div>
</div>
<!-- 卡片配色：第 1 张默认(青)，第 2 张加 class="case-card no5"(黄)，第 3 张 class="case-card no6"(红) -->

<!-- 引用既有卡（本章无新增卡时用；.fwd = 前向预告尚未定义的卡） -->
<div class="case-ref fwd">
  <span class="no">病历卡 No.09</span><span class="nm">级联故障</span><span class="sym">███▇▅▃▁</span>
  一句话说明它和本章的关系。<a href="ch07.html">第 7 章定义 →</a>
</div>

<!-- ========== ·4 模拟器（无模拟器的章节整段删除，编号跳到 ·5） ========== -->
</div><!-- /wrap -->
<div class="wide" style="padding:0 22px">
<h2><span class="sec">NN · 4 模拟器</span>小标题</h2>
<p style="max-width:760px">…一句话说明这个模型在模拟什么…</p>

<div class="sim" id="sim">
  <div class="sim-head">
    <span class="sim-title">XXX SIMULATOR · 秒抢监控大盘</span>
    <span class="sim-clock" id="clock">HH:MM:SS</span>
  </div>
  <canvas id="chart" width="1760" height="500" role="img" aria-label="…"></canvas>
  <div class="legend"><span><i style="background:var(--amber)"></i>…</span></div>
  <div class="sim-grid">
    <div class="sim-metric"><div class="k">…</div><div class="v" id="m-x">—</div></div>
  </div>
  <div class="controls">
    <button class="btn danger" id="btn-x">…</button>
    <label class="toggle"><input type="checkbox" id="tg-x">…</label>
    <span style="flex:1"></span>
    <button class="btn" id="btn-pause">暂停</button>
    <button class="btn" id="btn-reset">重置</button>
  </div>
  <div class="sliders">
    <div class="slider"><label>名称 <span id="lb-x">值</span></label>
      <input type="range" id="sl-x" min="" max="" step="" value=""></div>
  </div>
  <div class="sim-log" id="log" aria-live="polite"></div>
</div>

<div class="experiments" style="max-width:760px;margin-left:auto;margin-right:auto">
  <h3>🧪 N 个实验（按顺序做）</h3>
  <ol>
    <li><strong>实验名。</strong>操作步骤 → 你会看到什么 → <strong>教学结论</strong>。</li>
  </ol>
</div>
</div><!-- /wide -->
<div class="wrap">

<!-- ========== ·5 权衡 ========== -->
<h2><span class="sec">NN · 5 权衡</span>没有正确答案，只有代价</h2>
<p>…把场景摆清楚…<strong>每一个都是对的，每一个都有账单。</strong></p>

<div class="decision" id="d2">
  <span class="decision-tag">决策点 D2</span>
  <h3>问题句？</h3>
  <button class="opt" data-d="2" data-k="mid"><span class="tag">A</span>…</button>
  <button class="opt" data-d="2" data-k="mid"><span class="tag">B</span>…</button>
  <button class="opt" data-d="2" data-k="mid"><span class="tag">C</span>…</button>
  <div class="verdict" id="v-d2">
    <p><b class="mid">A · 名称</b>：优点。<strong>账单：</strong>代价…适合…的场景。</p>
    <p><b class="mid">B · 名称</b>：…</p>
    <p><b class="mid">C · 名称</b>：…</p>
    <p style="border-top:1px solid var(--line);padding-top:12px;margin-top:14px">「秒抢」的选择：… 理由 …</p>
  </div>
</div>

<!-- ========== ·6 复盘 ========== -->
<h2><span class="sec">NN · 6 复盘</span>那一次后来怎么样了</h2>
<p>回放正确剧本——留意每个动作的<strong>顺序</strong>：</p>
<div class="timeline">
  <div class="tl"><span class="tt">HH:MM</span><p><strong>动作名。</strong>做了什么，指标怎么变。</p></div>
  <!-- 4 条左右 -->
</div>
<div class="lesson">
  <div class="li"><span class="num">壹</span><div><strong>教训一句话。</strong>展开。</div></div>
  <div class="li"><span class="num">貳</span><div><strong>…</strong>…</div></div>
  <div class="li"><span class="num">叁</span><div><strong>…</strong>…</div></div>
</div>

<!-- ========== ·7 自测 ========== -->
<h2><span class="sec">NN · 7 自测</span>小标题</h2>
<div class="quiz" id="q1">
  <h3>Q1 · 看形状诊断</h3>
  <p class="stem">题干…</p>
  <div class="q-opts">
    <button class="opt" data-q="q1" data-k="bad"><span class="tag">A</span>…</button>
    <button class="opt" data-q="q1" data-k="good"><span class="tag">B</span>…</button>
    <button class="opt" data-q="q1" data-k="bad"><span class="tag">C</span>…</button>
    <button class="opt" data-q="q1" data-k="bad"><span class="tag">D</span>…</button>
  </div>
  <div class="verdict" id="v-q1"><p><b class="good">B。</b>解析：为什么对 + <em>为什么诱人的错误项是错的</em>。</p></div>
</div>
<!-- q2 q3 q4 同构；id 依次 q2/q3/q4，verdict id 依次 v-q2/v-q3/v-q4 -->

<!-- ========== 面试映射（不占 sec 编号） ========== -->
<div class="interview">
  <h3>🎯 面试映射 · 本章直接覆盖的高频追问</h3>
  <div class="iq"><b>「问题一？」</b><span class="ans">答题骨架：给结构不给全文，用 → 串起步骤。</span></div>
  <div class="iq"><b>「问题二？」</b><span class="ans">…</span></div>
  <div class="iq"><b>「问题三？」</b><span class="ans">…</span></div>
</div>

</div><!-- /wrap -->

<footer>
  <div class="foot-in">
    <span><a href="上一页.html">← 第 N-1 章 · 标题</a></span>
    <span><a href="appendix-cards.html">病历卡 No.NN 已收录于附录图鉴</a></span>
    <span><a href="下一页.html">第 N+1 章 · 标题 →</a></span>
  </div>
</footer>

<script src="assets/book.js"></script>
<!-- 有模拟器的章节追加：<script src="assets/sim-N.js"></script> -->
</body>
</html>
```

### 章节页硬性检查（写完自查一遍）

- [ ] `h2 .sec` 序列 = `1,2,3,4,5,6,7` 或 `1,2,3,5,6,7`（无模拟器）
- [ ] 恰好 4 个 `.quiz`、3 个 `.iq`、3 个 `.lesson .li`、2 个 `.decision`
- [ ] 每个 `data-d="N"` 有 `id="v-dN"`；每个 `data-q="qN"` 有 `id="v-qN"`
- [ ] D2 的所有 `.opt` 都是 `data-k="mid"`
- [ ] 页内 id 全局唯一
- [ ] 无 `<style>` 块、无裸色值、无 `localStorage`/`sessionStorage`/`http://`/外链
- [ ] 跨章引用的章号与 `BIBLE.md` 第 3 节一致
- [ ] `.wrap` / `.wide` 的开合配平（模拟器段会打断 `.wrap`）

---

## B. 关卡页骨架（level1–level4）

关卡页**不用**七段式。结构固定为：

```html
<header>
  <div class="book-bar">…nav…</div>
  <div class="chapter-head">
    <div class="eyebrow">🔥 实战关卡 N · 真实事故</div>
    <h1>公司 年份<br>一句话标题</h1>
    <p class="h1-sub">…</p>
  </div>
</header>
<div class="wrap">

<div class="disclaimer">
  <b>关于本页的事实边界：</b>本页根据官方公开复盘改编，细节经过叙事化处理。
  技术事实、时间线与决策链均取自页末所列官方原始文档；氛围与心理描写为叙事化补充，
  <b>不代表当事人的真实言行</b>。本页不指名批评任何个人——与各家官方复盘的 blameless 精神一致。
</div>

<h2><span class="sec">关卡 N · 1 现场</span>…</h2>
…（第一人称或值班视角推演；每个事实句后面挂 <span class="srcref">[S1]</span> 指向来源清单）

<div class="beat">
  <div class="b"><span class="bt">HH:MM</span><p>…</p></div>
  <div class="b safe"><span class="bt">HH:MM</span><p>…（本可以刹车的时刻用 .safe）</p></div>
</div>

<h2><span class="sec">关卡 N · 2 决策点</span>…</h2>
<div class="decision" id="d1">…同章节页…</div>
<div class="decision" id="d2">…</div>
<div class="decision" id="d3">…</div>   <!-- 关卡的决策点数量按 SKELETON 各自规定 -->

<h2><span class="sec">关卡 N · 3 教训</span>…</h2>
<div class="lesson">…3 条…</div>

<h2><span class="sec">关卡 N · 4 带回「秒抢」</span>…</h2>
…把教训映射回主线：哪一章的哪张病历卡、「秒抢」该改什么…

<div class="sources">
  <h3>📄 原始来源（本页全部事实性陈述的出处）</h3>
  <ol>
    <li id="s1"><b>[S1]</b> 官方标题 —— <a href="https://…">https://…</a></li>
  </ol>
  <p class="srcref">逐句核对清单见构建仓库 <code>sources/FACTS-levelN.md</code>。</p>
</div>

</div><!-- /wrap -->
<footer>…</footer>
<script src="assets/book.js"></script>
```

关卡页红线：
- 所有数字带「约」，除非原文给出精确值且直接引用语境明确。
- 不给真实人物编造台词。
- 事实只能来自 `sources/FACTS-levelN.md`，写作者不得自行补充。

---

## C. 组件速查

| 用途 | class |
|---|---|
| 告警终端 | `.pager` + `.pager-top`/`.pager-body`，色 span：`.r` 红 `.a` 黄 `.t` 青 `.g` 灰 |
| 指标卡组 | `.metrics` > `.metric` > `.k`/`.v`/`.d`（`.d` 加 `.up`/`.down`/`.warn`） |
| 决策点 | `.decision` > `.decision-tag` + `.opt`(data-d/data-k) + `.verdict#v-dN` |
| 病历卡 | `.case-card`（第 2/3 张加 `.no5`/`.no6`）五行 `.case-row` |
| 引用卡 | `.case-ref`（前向预告加 `.fwd`） |
| 模拟器 | `.sim` … `.experiments` |
| 时间线 | `.timeline` > `.tl` > `.tt` + `<p>` |
| 教训 | `.lesson` > `.li` > `.num`(壹貳叁) + `<div>` |
| 自测 | `.quiz` > `h3` + `.stem` + `.q-opts` + `.verdict#v-qN` |
| 面试 | `.interview` > `.iq` > `<b>` + `.ans` |
| 引言块 | `.kicker` |
| 架构图 | `.arch` > `.arch-title` + `.arch-flow`(`.arch-node`/`.arch-arrow`) + `.arch-note` |
| 关卡时间线 | `.beat` > `.b`(可加 `.safe`) > `.bt` + `<p>` |
| 来源清单 | `.sources` + 正文里的 `.srcref` |
| 表格 | `.tbl-wrap` > `table.tbl` |
| 目录 | `.toc` > `.toc-part` + `a.toc-item`(`.toc-num`/`.toc-t`/`.toc-d`/`.toc-tags`) |
