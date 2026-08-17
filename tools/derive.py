#!/usr/bin/env python3
"""全局计数唯一真相源 + 附录派生校验（QUALITY.md 一.4，全书计数禁止手写）。

用法: python3 tools/derive.py
C1 派生并断言全局不变量（缺页时列差异）→ 写 tools/derived-counts.json
C2 校验正文「全书 N 个」类声称与派生值一致
C3 生成 appendix-interview.html（仅全部 16 章齐备时；否则跳过并提示）
C4 校验 appendix-cards.html（人工撰写页，存在时才校验；否则跳过并提示）
退出码 0=全部一致，1=有差异或缺失（页面未建齐时失败是预期的构建中状态）。
"""
import sys, json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHAPTERS = [f"ch{n:02d}.html" for n in range(1, 17)]
LEVELS = [f"level{n}.html" for n in range(1, 5)]
BODY_CARD_NOS = [f"{n:02d}" for n in range(1, 15)]
APPENDIX_CARD_NOS = [f"{n:02d}" for n in range(1, 18)]

CASE_NO_RE = re.compile(r'class="case-no">病历卡 No\.(\d{2})</span>')
CARD_NAME_RE = re.compile(r'<div class="case-head">\s*<h3>(.*?)</h3>')
IQ_RE = re.compile(r'<div class="iq">\s*<b>(.*?)</b>\s*<span class="ans">(.*?)</span>', re.S)


def derive_counts():
    counts = {}
    problems = []

    missing_ch = [f for f in CHAPTERS if not (ROOT / f).exists()]
    counts["chapters"] = len(CHAPTERS) - len(missing_ch)
    if missing_ch:
        problems.append(f"章节页缺失 {len(missing_ch)} 个：{', '.join(missing_ch)}")

    missing_lv = [f for f in LEVELS if not (ROOT / f).exists()]
    counts["levels"] = len(LEVELS) - len(missing_lv)
    if missing_lv:
        problems.append(f"关卡页缺失 {len(missing_lv)} 个：{', '.join(missing_lv)}")

    sim_dir = ROOT / "assets"
    sim_files = sorted(sim_dir.glob("sim-*.js")) if sim_dir.exists() else []
    counts["sims"] = len(sim_files)
    if counts["sims"] != 6:
        problems.append(f"模拟器数 {counts['sims']} ≠ 6")
    missing_sim = [f"assets/sim-{n}.js" for n in range(1, 7) if not (sim_dir / f"sim-{n}.js").exists()]
    if missing_sim:
        problems.append(f"模拟器文件缺失 {len(missing_sim)} 个：{', '.join(missing_sim)}")
    for sf in sim_files:
        m = re.match(r"sim-(\d+)\.js$", sf.name)
        if not m:
            problems.append(f"模拟器文件名无法解析：{sf.name}")
            continue
        if not list((ROOT / "tools").glob(f"sim{m.group(1)}-*model-test.js")):
            problems.append(f"{sf.name} 缺少对应 tools/sim{m.group(1)}-*model-test.js")

    body_defs = []
    for f in CHAPTERS:
        p = ROOT / f
        if p.exists():
            body_defs += CASE_NO_RE.findall(p.read_text(encoding="utf-8"))
    counts["cards_body"] = len(body_defs)
    if len(body_defs) != 14:
        problems.append(f"正文病历卡定义 {len(body_defs)} 张 ≠ 14")
    dup = sorted({n for n in body_defs if body_defs.count(n) > 1})
    if dup:
        problems.append(f"正文病历卡编号重复：{dup}")

    app_path = ROOT / "appendix-cards.html"
    app_defs = CASE_NO_RE.findall(app_path.read_text(encoding="utf-8")) if app_path.exists() else []
    counts["cards_total"] = len(app_defs)
    if not app_path.exists():
        problems.append("appendix-cards.html 缺失（附录 17 张无法派生）")
    elif len(app_defs) != 17:
        problems.append(f"附录病历卡定义 {len(app_defs)} 张 ≠ 17")

    interview = quiz = lessons = 0
    for f in CHAPTERS:
        p = ROOT / f
        if p.exists():
            html = p.read_text(encoding="utf-8")
            interview += len(re.findall(r'class="iq"', html))
            quiz += len(re.findall(r'class="quiz"', html))
            lessons += len(re.findall(r'class="li"', html))
    counts["interview"] = interview
    counts["quiz"] = quiz
    counts["lessons"] = lessons
    if interview != 48:
        problems.append(f"面试追问总数 {interview} ≠ 48（16 章 × 3）")
    if quiz != 64:
        problems.append(f"自测题总数 {quiz} ≠ 64（16 章 × 4）")
    if lessons != 48:
        problems.append(f"教训总数 {lessons} ≠ 48（16 章 × 3）")
    return counts, problems


def check_claims(counts):
    problems = []
    fixed = [(r"全书 (\d+) 个模拟器", counts["sims"]), (r"共 (\d+) 章", counts["chapters"])]
    for p in sorted(ROOT.glob("*.html")):
        html = p.read_text(encoding="utf-8")
        for m in re.finditer(r"(\d+) 张病历卡", html):
            n = int(m.group(1))
            if n not in (counts["cards_body"], counts["cards_total"]):
                ctx = html[max(0, m.start() - 20):m.end() + 20].replace("\n", " ").strip()
                problems.append(f"{p.name} 声称「{m.group(0)}」与派生值（正文 {counts['cards_body']} / 附录 {counts['cards_total']}）不符 · {ctx[:30]}")
        for pat, expected in fixed:
            for m in re.finditer(pat, html):
                n = int(m.group(1))
                if n != expected:
                    ctx = html[max(0, m.start() - 20):m.end() + 20].replace("\n", " ").strip()
                    problems.append(f"{p.name} 声称「{m.group(0)}」≠ 派生值 {expected} · {ctx[:30]}")
    return problems


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return s.replace("&", "&amp;").replace("<", "&lt;").strip()


def generate_interview():
    missing = [f for f in CHAPTERS if not (ROOT / f).exists()]
    if missing:
        print(f"[C3] 跳过生成 appendix-interview.html：缺 {len(missing)} 个章节页 → {', '.join(missing)}")
        return []
    problems = []
    rows = []
    for i, f in enumerate(CHAPTERS, start=1):
        html = (ROOT / f).read_text(encoding="utf-8")
        iqs = IQ_RE.findall(html)
        if len(iqs) != 3:
            problems.append(f"{f} 的 .interview 提取到 {len(iqs)} 个 .iq（期望 3）")
        for q, a in iqs:
            rows.append((i, strip_tags(q), strip_tags(a)))
    tbody = "\n".join(
        f'<tr><td>第 {i} 章</td><td>{q}</td><td>{a}</td>'
        f'<td><a href="ch{i:02d}.html">第 {i} 章 →</a></td></tr>'
        for i, q, a in rows)
    n_q = len(rows)
    n_ch = len(rows) // 3
    page = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>附录 B · 面试映射总表 | 系统是被打出来的</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<!-- 本文件由 tools/derive.py 生成，禁止手工编辑 -->
<header>
  <div class="book-bar"><span><b>系统是被打出来的</b> · 系统设计实战手册</span><nav aria-label="章节导航"><a href="appendix-cards.html">← 上一章</a><a href="index.html">目录</a><a href="#" aria-disabled="true">下一章 →</a></nav></div>
  <div class="chapter-head">
    <div class="eyebrow">附录 B</div>
    <h1>面试映射总表<br>{n_ch} 章 × 3 问，一共 {n_q} 个高频追问</h1>
    <p class="h1-sub">上半部分（{n_q} 问总表）由 tools/derive.py 从 {n_ch} 章的 .interview 区块派生，禁止手工编辑；节奏表、评分尺与计时 mock 是固定模板，同样只能改脚本、不能手改产出。</p>
  </div>
</header>
<div class="wrap">
<p class="lead">这页现在是三段：先看下面这张 {n_q} 问总表建地图；再用节奏表和评分尺练「怎么答」与「答得够不够」；最后用 3 道计时 mock 练「没见过的题目怎么办」。</p>
<div class="tbl-wrap">
<table class="tbl">
<thead>
<tr><th>章节</th><th>高频追问</th><th>答题骨架</th><th>锚点链接</th></tr>
</thead>
<tbody>
{tbody}
</tbody>
</table>
</div>

<h2 id="pace">45 分钟怎么分配</h2>
<p class="lead">系统设计面试通常给 45 分钟，多一分钟都没有。下面是一份可执行的节奏表——不是死规矩，是给你一个默认锚点，防止在某一段里超支到收不了尾。</p>
<div class="tbl-wrap">
<table class="tbl">
<thead><tr><th>阶段</th><th>建议分钟数</th><th>这一段要产出什么</th></tr></thead>
<tbody>
<tr><td>需求澄清</td><td>5 分钟</td><td>功能范围 + 非功能约束（QPS 量级、延迟目标、一致性要求）+ 明确说一句「这次不做什么」。</td></tr>
<tr><td>容量估算</td><td>5 分钟</td><td>DAU/QPS/存储量级 + 峰值倍数，说出假设，不用算到小数点。</td></tr>
<tr><td>API 与数据模型</td><td>7 分钟</td><td>2–3 个核心接口签名 + 关键实体和它们的索引/分片键。</td></tr>
<tr><td>总体架构</td><td>10 分钟</td><td>组件框图 + 数据流箭头，边画边讲每个组件的职责一句话。</td></tr>
<tr><td>瓶颈深挖</td><td>10 分钟</td><td>面试官追问的那一个点讲透——通常是缓存、分片、一致性或削峰里的一个，不用四个都展开。</td></tr>
<tr><td>可靠性与故障</td><td>5 分钟</td><td>指出架构里的单点，给出降级/兜底动作。</td></tr>
<tr><td>收尾</td><td>3 分钟</td><td>权衡总结一句话 + 主动说一条「我知道但没时间展开」的短板。</td></tr>
</tbody>
</table>
</div>

<h2 id="rubric">5 维评分尺</h2>
<p class="lead">下面这把尺子不是给面试官用的，是给你自己练完一题后回看用的。每一档写的是<strong>可观察的行为</strong>，不是形容词——你应该能对照自己刚才说的话，逐条打勾。<br><br><strong>怎么定档</strong>：必须<strong>同时满足本档及所有更低档</strong>的行为才算达到该档——命中一句「优秀」但漏掉「良好」的条目，仍然只算「够用」。如果某道题根本没触发某个维度（比如题面里没有失败场景），该维记 <strong>N/A</strong>，不要记 0，也不要用它拉低整体判断。</p>
<div class="tbl-wrap">
<table class="tbl">
<thead><tr><th>维度</th><th>够用</th><th>良好</th><th>优秀</th></tr></thead>
<tbody>
<tr><td>需求与约束</td><td>说出了功能范围和大致 QPS 量级，没有主动问延迟或一致性要求。</td><td>主动追问了非功能约束（延迟、一致性、可用性），并明确说出了「这次不做什么」。</td><td>把约束翻译成了后续设计的判据（例如「读多写少、能容忍秒级新鲜度，所以后面允许用缓存」），并在设计里真的用上了这句话。</td></tr>
<tr><td>估算与容量</td><td>算出了 QPS 量级，用乘法得出结果，但没检查数量级是否合理。</td><td>给出 DAU → QPS → 峰值倍数 → 机器数区间的完整链条，并说明了每一步的假设。</td><td>指出了哪个假设最敏感（换一个数量级，结果会差多少），并说明了下一步用什么压测去缩小这个不确定性。</td></tr>
<tr><td>架构与数据流</td><td>画出了组件，但无法从入口开始逐条边走到最终的读/写结果；至少有一条关键边没有说明协议、数据或状态变化。</td><td>边画边讲清楚了完整数据流，并标出了读路径和写路径的差异。</td><td>主动标出了架构里当前最可能先倒下的那条边，并说明了为什么先怀疑它而不是别的组件。</td></tr>
<tr><td>失败与恢复</td><td>提到了「要限流」「要重试」这类通用词，没有映射到架构里的具体组件。</td><td>针对架构图里某个具体依赖，说清楚了它变慢/挂掉会发生什么，以及第一层兜底动作。</td><td>讲出了故障传播路径——哪个下游变慢会拖垮哪个上游——并给出了阻断点，而不是给每个组件逐个贴创可贴。</td></tr>
<tr><td>权衡表达</td><td>选出了方案，但答案里没有为至少一个<strong>未选</strong>方案写出具体代价（不依赖面试官是否追问——自己主动写才算）。</td><td>对每个候选方案都说出了具体代价（不是「更贵」这种模糊词，而是一句可核实的账单）。</td><td>说出了「什么事实一变，这个选择就会反过来」——翻转变量式的表达，而不是记住一个固定偏好。</td></tr>
</tbody>
</table>
</div>

<h2 id="mock">3 道计时 mock</h2>
<p class="lead">下面 3 题只给初始需求，答案不会被保存，刷新即失——这是刻意的：现实中的面试也不会让你带答案进场。每题分两阶段：先按给定的分钟数写方案，点开揭晓看基准答案；基准答案里会带出下一阶段的追问，写完追问的方案再展开第二次揭晓。三题覆盖三种题型，练的是方法能不能迁移，而不是记住某一道题的答案。</p>

<h3>Mock 1 · 秒杀类</h3>
<div class="exercise">
  <span class="exercise-tag">交卷 E1 · 阶段一 · 20 分钟</span>
  <h3>某演唱会平台开票：总票量 5,000 张，同一时刻约 80,000 人尝试购买，购票窗口只开放 60 秒。</h3>
  <p>先只交两样：① 你会问的 3 个澄清问题；② 整体架构草图（组件 + 数据流，用文字箭头写，不用画图）。</p>
  <textarea class="ex-input" rows="8" placeholder="① 澄清问题…&#10;② 架构草图：用户 → … → …"></textarea>
  <p class="ex-hint">写不出来也要写下卡在哪一步——那本身就是有用的诊断。答案不会被保存，刷新即失。</p>
  <button class="btn primary ex-reveal">我写完了，展开基准答案</button>
  <p class="ex-warn">你还没写。先写下来再看——再点一次仍会展开。</p>
  <div class="ex-model">
    <h4>基准答案 · 一份合格答案长什么样</h4>
    <p>澄清问题至少覆盖：库存是否分场次/分区、是否要求先到先得还是允许摇号、超卖的容忍度是多少。架构骨架：入口限流/排队 → 静态化详情页/CDN → 库存原子扣减（DB 条件更新或 Redis Lua）→ 订单异步落库 → 支付与出票。</p>
    <h4>自评：你的答案里有没有这几样</h4>
    <ul>
      <li>问出了「超卖能不能容忍」这类决定后续架构复杂度的约束，而不是先问技术选型</li>
      <li>架构草图里有明确的「裁决点」——谁说了算库存还剩多少</li>
      <li>提到了异步化（订单/通知不卡在扣减库存这条同步路径上）</li>
    </ul>
    <h4>追问（阶段二 · 15 分钟）</h4>
    <p>运营现在要求：同一个用户最多买 4 张；且要支持「先到先得」和「随机摇号」两种放票模式随时切换。你的架构要改哪里？</p>
  </div>
</div>

<div class="exercise">
  <span class="exercise-tag">交卷 E1 · 阶段二 · 15 分钟</span>
  <h3>阶段二 · 追问（题目见上一块基准答案末尾的「追问」段）</h3>
  <p>看完阶段一的基准答案和追问段后再写。只交修改点，不用重写整个架构：哪些组件要动、为什么。</p>
  <textarea class="ex-input" rows="6" placeholder="① 要改的地方…&#10;② 为什么…"></textarea>
  <p class="ex-hint">答案不会被保存，刷新即失。</p>
  <button class="btn primary ex-reveal">我写完了，展开基准答案</button>
  <p class="ex-warn">你还没写。先写下来再看——再点一次仍会展开。</p>
  <div class="ex-model">
    <h4>基准答案 · 一份合格答案长什么样</h4>
    <p>限购通常在库存裁决点旁边加一次「用户已购数」的原子检查，和扣减库存放进同一个原子操作，不能拆成先查后扣两步。先到先得的裁决点是「谁先完成原子扣减」；摇号模式的裁决点变成「谁被抽中」——差别在于扣减库存<em>之前</em>要不要插入一次批量抽签，扣减本身的原子性要求不变。</p>
    <h4>自评：你的答案里有没有这几样</h4>
    <ul>
      <li>限购检查和库存扣减在同一个原子操作里，没有拆成「先查后扣」两步</li>
      <li>说清楚了两种模式共享同一个「扣减」裁决点，区别只是抽签发生在扣减前还是不发生</li>
      <li>提到了模式切换本身也要有开关和审计，不能运营口头说切就切</li>
    </ul>
  </div>
</div>

<h3>Mock 2 · 非交易高读类</h3>
<div class="exercise">
  <span class="exercise-tag">交卷 E2 · 阶段一 · 20 分钟</span>
  <h3>短视频 App 的「实时热榜」：全站 5,000 万 DAU，热榜每 30 秒刷新一次、展示当前热度 Top 100 视频；读 QPS 峰值约 200,000，写（点赞/播放等互动事件）QPS 约 80,000。</h3>
  <p>先只交两样：① 3 个澄清问题；② 一次点赞事件到榜单更新的数据路径草图。</p>
  <textarea class="ex-input" rows="8" placeholder="① 澄清问题…&#10;② 路径：点赞 → … → 榜单"></textarea>
  <p class="ex-hint">答案不会被保存，刷新即失。</p>
  <button class="btn primary ex-reveal">我写完了，展开基准答案</button>
  <p class="ex-warn">你还没写。先写下来再看——再点一次仍会展开。</p>
  <div class="ex-model">
    <h4>基准答案 · 一份合格答案长什么样</h4>
    <p>澄清问题至少覆盖：热度分数怎么算（播放/点赞/转发的权重）、榜单允许多陈旧（30 秒是硬指标还是可以再宽松）、要不要防刷分。路径骨架：互动事件 → 消息队列削峰 → 流式聚合更新分数（内存计数器或近似 Top-K 结构）→ 每 30 秒把结果落一份快照到缓存 → 读请求只打这份快照，不直接查明细表。</p>
    <h4>自评：你的答案里有没有这几样</h4>
    <ul>
      <li>意识到 200,000 QPS 的读不能实时算榜单，必须读一份预先算好的快照</li>
      <li>写路径和读路径分开：写用队列削峰 + 流式聚合，读只碰快照，两条路径互不阻塞</li>
      <li>问到了热度分数的定义和防刷分——这决定了聚合逻辑的复杂度</li>
    </ul>
    <h4>追问（阶段二 · 15 分钟）</h4>
    <p>运营要求：不同城市要看到不同的热榜（同城内容优先），且不能让一线城市的大流量把三四线城市的小众热点淹没。你的方案要改哪里？</p>
  </div>
</div>

<div class="exercise">
  <span class="exercise-tag">交卷 E2 · 阶段二 · 15 分钟</span>
  <h3>阶段二 · 追问（题目见上一块基准答案末尾的「追问」段）</h3>
  <p>看完阶段一的基准答案和追问段后再写。只交修改点：哪里要按维度切分、切分之后原来的瓶颈会不会转移。</p>
  <textarea class="ex-input" rows="6" placeholder="① 要改的地方…&#10;② 原来的瓶颈会不会转移…"></textarea>
  <p class="ex-hint">答案不会被保存，刷新即失。</p>
  <button class="btn primary ex-reveal">我写完了，展开基准答案</button>
  <p class="ex-warn">你还没写。先写下来再看——再点一次仍会展开。</p>
  <div class="ex-model">
    <h4>基准答案 · 一份合格答案长什么样</h4>
    <p>把「全国一个热度分数」改成「按城市独立聚合、独立生成快照」——每个城市是一条独立的计数与排序流水线，而不是先算全国榜再筛选。这样一线城市事件量再大，也只占用它自己那条流水线，不挤占其他城市的聚合资源。城市粒度太细会导致长尾城市数据稀疏，通常还要给「城市」加一层兜底：数据不足时退化到大区或全国榜垫底。</p>
    <h4>自评：你的答案里有没有这几样</h4>
    <ul>
      <li>说的是「独立流水线」而不是「在全国榜基础上按城市过滤」——后者没有解决大城市抢占聚合资源的问题</li>
      <li>提到了长尾城市数据稀疏时的兜底策略，而不是假设每个城市数据都够用</li>
      <li>指出了这个改动让分片数量变多，需要重新核算聚合层的资源分配</li>
    </ul>
  </div>
</div>

<h3>Mock 3 · 异步协作类</h3>
<div class="exercise">
  <span class="exercise-tag">交卷 E3 · 阶段一 · 20 分钟</span>
  <h3>电商平台的「订单履约通知」：下单后依次触发库存锁定、支付确认、仓库拣货、物流发货、短信/推送通知；每一步都可能失败或超时，全链路平均耗时从几分钟到几小时不等。</h3>
  <p>先只交两样：① 3 个澄清问题；② 这条链路的编排方式草图（谁触发下一步、状态存在哪）。</p>
  <textarea class="ex-input" rows="8" placeholder="① 澄清问题…&#10;② 编排：下单 → … → 通知"></textarea>
  <p class="ex-hint">答案不会被保存，刷新即失。</p>
  <button class="btn primary ex-reveal">我写完了，展开基准答案</button>
  <p class="ex-warn">你还没写。先写下来再看——再点一次仍会展开。</p>
  <div class="ex-model">
    <h4>基准答案 · 一份合格答案长什么样</h4>
    <p>澄清问题至少覆盖：某一步失败了是重试还是回滚前面的步骤、超时算多久、这条链路要不要支持人工介入。编排骨架：用一张订单状态表记录当前所处阶段，而不是让每个服务自己猜上一步有没有做完；每一步完成后发一条事件，下一个服务订阅事件触发自己那一步；每一步都写幂等键，允许安全重放。</p>
    <h4>自评：你的答案里有没有这几样</h4>
    <ul>
      <li>状态存在一个各方都能查的地方（订单状态表），而不是分散在各个服务自己的日志里</li>
      <li>每一步都提到了幂等——因为消息可能重复投递（第 9/11 章的病历卡就是这个）</li>
      <li>问到了失败后是重试还是回滚，这决定了要不要做补偿事务</li>
    </ul>
    <h4>追问（阶段二 · 15 分钟）</h4>
    <p>运营要求：某一步失败超过 3 次要自动转人工，但转人工之前不能让用户以为订单卡死了——要有中间态展示。你的方案要改哪里？</p>
  </div>
</div>

<div class="exercise">
  <span class="exercise-tag">交卷 E3 · 阶段二 · 15 分钟</span>
  <h3>阶段二 · 追问（题目见上一块基准答案末尾的「追问」段）</h3>
  <p>看完阶段一的基准答案和追问段后再写。只交修改点：状态机要加什么状态、用户端读到的是什么。</p>
  <textarea class="ex-input" rows="6" placeholder="① 要新增的状态…&#10;② 用户端读到的是哪张表…"></textarea>
  <p class="ex-hint">答案不会被保存，刷新即失。</p>
  <button class="btn primary ex-reveal">我写完了，展开基准答案</button>
  <p class="ex-warn">你还没写。先写下来再看——再点一次仍会展开。</p>
  <div class="ex-model">
    <h4>基准答案 · 一份合格答案长什么样</h4>
    <p>状态机里加一个「处理中（重试计数 N/3）」和「待人工处理」两个中间状态，而不是失败了就直接把订单标记成失败。计数器随每次重试自增，第 3 次失败后状态转「待人工」并生成一张工单，同时把该订单从自动重试队列摘除。用户端读到的仍然是订单状态表里的这个中间状态，展示成「正在处理，请稍候」，不暴露内部的失败/重试细节。</p>
    <h4>自评：你的答案里有没有这几样</h4>
    <ul>
      <li>重试计数和「待人工」是状态机里的正式状态，不是日志里的旁注</li>
      <li>转人工之后原来的自动重试要停掉，不能人工和自动同时改同一个状态</li>
      <li>用户端展示的字段和内部状态机是分开的两件事——用户不需要看到「重试 3/3」</li>
    </ul>
  </div>
</div>

</div><!-- /wrap -->
<footer>
  <div class="foot-in">
    <span><a href="appendix-cards.html">← 附录 A · 病历卡图鉴</a></span>
    <span>tools/derive.py 生成 · {n_ch} 章 × 3 问 + 节奏表/评分尺/3 道 mock</span>
    <span><a href="#" aria-disabled="true">下一章 →</a></span>
  </div>
</footer>
<script src="assets/book.js"></script>
</body>
</html>'''
    (ROOT / "appendix-interview.html").write_text(page, encoding="utf-8")
    print(f"[C3] 已生成 appendix-interview.html（{n_q} 行）")
    return problems


def card_name_in(html, no):
    m = re.search(rf'<span class="case-no">病历卡 No\.{no}</span>', html)
    if not m:
        return None
    head = html.rfind('<div class="case-head">', 0, m.start())
    if head == -1:
        return None
    nm = CARD_NAME_RE.search(html, head, m.start())
    return nm.group(1).strip() if nm else None


def body_card_name(no):
    for f in CHAPTERS:
        p = ROOT / f
        if not p.exists():
            continue
        name = card_name_in(p.read_text(encoding="utf-8"), no)
        if name is not None:
            return name
    return None


def check_cards():
    app_path = ROOT / "appendix-cards.html"
    if not app_path.exists():
        print("[C4] 跳过校验 appendix-cards.html：文件不存在（人工撰写页，页面齐备后再校验）")
        return []
    problems = []
    html = app_path.read_text(encoding="utf-8")
    app_defs = CASE_NO_RE.findall(html)
    if len(app_defs) != 17:
        problems.append(f"附录卡 {len(app_defs)} 张 ≠ 17")
    dup = sorted({n for n in app_defs if app_defs.count(n) > 1})
    if dup:
        problems.append(f"附录卡编号重复：{dup}")
    missing = [n for n in APPENDIX_CARD_NOS if n not in app_defs]
    if missing:
        problems.append(f"附录卡缺失编号：{missing}")
    for part in html.split('<div class="case-head">')[1:]:
        m = CASE_NO_RE.search(part)
        if not m:
            problems.append("存在无编号的病历卡")
            continue
        no = m.group(1)
        links = re.findall(r'href="(ch\d+\.html)"', part)
        if not links:
            problems.append(f"No.{no} 缺少「展开章节」链接（ch*.html）")
        for tgt in links:
            if not (ROOT / tgt).exists():
                problems.append(f"No.{no} 的展开章节链接 {tgt} 不存在")
    for no in BODY_CARD_NOS:
        app_name = card_name_in(html, no)
        body_name = body_card_name(no)
        if app_name is None or body_name is None:
            problems.append(f"No.{no} 卡名无法比对（附录 {app_name!r} / 正文 {body_name!r}）")
        elif app_name != body_name:
            problems.append(f"No.{no} 卡名不一致：附录「{app_name}」≠ 正文「{body_name}」")
    return problems


def main():
    counts, problems = derive_counts()
    print("[C1] 派生值: " + json.dumps(counts, ensure_ascii=False))
    claims = check_claims(counts)
    print(f"[C2] 「全书 N 个」类声称校验：{len(claims)} 处不一致")
    problems += claims
    problems += generate_interview()
    card_problems = check_cards()
    if (ROOT / "appendix-cards.html").exists():
        print(f"[C4] 校验 appendix-cards.html（17 张编号/展开链接/卡名与正文逐字一致）："
              f"{len(card_problems)} 处不一致")
    problems += card_problems
    (ROOT / "tools").mkdir(parents=True, exist_ok=True)
    (ROOT / "tools" / "derived-counts.json").write_text(
        json.dumps(counts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if problems:
        print("\n差异明细：")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print("全部不变量一致。")
    sys.exit(0)


if __name__ == "__main__":
    main()
