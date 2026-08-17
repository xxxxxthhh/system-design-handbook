# Pane C 完工报告

范围：`ch02.html` `ch05.html` `ch06.html` `ch07.html` `ch08.html` `ch09.html`。
未触碰任何其他文件。未 `git commit`。

## C1 · 6 章「模型边界」卡

按共同规格的统一格式，插入在每章 `.experiments` 块的实验清单 `</ol>` 之后、`</div>` 之前，
内容取自 `tasks/idea-depth.md`「6 个模拟器：应显式标注的教学性简化」一节，未自行发明结论。

| 章 | 模拟器 | 条数 |
|---|---|---|
| ch02.html | Sim-1 排队论 | 3 条：P50/P99 启发式常数、`usefulConcurrency=10` 预写死「加池不增吞吐」、忽略突发/分布/队首阻塞 |
| ch05.html | Sim-2 缓存雪崩 | 3 条：单一「温度」标量压缩全部 key、过期率/衰减/回暖是剧情参数、「重启救不活」只在当前参数+无保护下成立 |
| ch06.html | Sim-3 限流算法 | 4 条：100ms 单机流体计数、burst×4/固定 10 桶是可比设定、「三路合计拒绝」是反事实求和非真实指标、不模拟分布式计数误差与公平性 |
| ch07.html | Sim-4 重试风暴 | 3 条：小数 weight 非离散请求、固定失败率+无 deadline/熔断/预算反馈、backoff 因预生成机制而必然只改波形不改总量 |
| ch08.html | Sim-5 一致性哈希 | 4 条：迁移比例只数 key 个数不计字节/QPS、30% 热点是单一合成 key、150 虚拟节点下 <1.30 是这组样本的结果、只演示了虚拟节点这一种均匀化手段 |
| ch09.html | Sim-6 消息积压 | 3 条：总消费能力线性公式忽略分区/下游/毒消息、不模拟毒消息与重试、「永不追平」是按当前速率的条件外推非对未来的预测 |

未新增 CSS、未使用裸色值，全部复用现有 `<h3>` `<ul>` `<li>` `<code>` `<strong>` `<em>` 与内联 `style` 变量（`var(--muted)`）。

## C2 · ch05 绝对化承诺（逐条对照）

只改了不成立的绝对断言本身，未重写段落、未改结构、未动数字、未碰模拟器部分（Sim-2 的模型边界卡是 C1 任务，加在实验清单之后，与 D2/自测的这三处改动是两件事）。

**1) D2 verdict A（互斥回源）**
- 原文：`DB 绝对安全，数据始终新鲜。`
- 改后：`锁能拿到、回源能成功时，DB 不会被同一 key 的并发击穿，数据也是新鲜的。`
- 为什么原文不成立：分布式互斥锁会失效或超时，回源请求本身也会失败；一旦发生，DB 并不「绝对安全」，数据也不「始终新鲜」。改后把结论挂在其成立的前提上，紧接的「账单」句已经在讲这把锁本身就是新引入的依赖，逻辑衔接不变。

**2) D2 verdict B（逻辑过期）**
- 原文：`用户永远无等待，DB 永远只有一个异步刷新请求。`
- 改后：`用户读路径不需要等待，只要刷新触发也做了并发保护，DB 通常只会收到一个异步刷新请求。`
- 为什么原文不成立：「用户无等待」这部分结构上成立（读路径永远先返回旧值），但「DB 永远只有一个异步刷新请求」不成立——如果刷新触发本身没有并发保护（比如没有做 singleflight），多个并发请求发现数据过期时会各自触发一次刷新；异步刷新还可能失败，导致「永远陈旧」（这一点后半句「账单」里已经提到了兜底任务，保留未动）。改后把「只有一个」限定在「刷新触发也做了并发保护」的前提下。

**3) 自测 q4 verdict**
- 原文：`锁死这个循环的唯一钥匙在流量入口，不在存储层。`
- 改后：`打破这个循环最快能拧动的钥匙在流量入口，不在存储层；预热、扩容或旁路缓存也能打破它，只是更慢。`
- 为什么原文不成立：预热、扩容、旁路缓存都能打破「冷缓存-死DB-全量流量」这个循环，流量入口限流不是唯一手段，只是「秒抢」当下最快能拧动的那一个。保留了原句「不在存储层」的定位判断（这是本题真正要考的点：别指望从存储层解），只去掉「唯一/锁死」的绝对化。

三处改动都只替换了同一句话内的措辞，未触及前后文的账单句、时间线、模拟器脚本或数字。

## C3 · ch07「重试次数」口径统一

全章统一为「尝试次数」口径，数值不变（仍是 27）：

1. `07 · 2 原理` 段（27 倍公式之后）：补一句点破「重试 N 次」歧义的坑——
   > 说"重试 3 次"时先问清楚是 3 次还是 4 次——工程惯例里"重试 3 次"常指首次 + 3 次重试 = 4 次尝试，三层最坏是 4³=64，不是 27；差一层就是 27 与 64 的区别。
2. `07 · 4 模拟器` 段引言：`重试次数在末端相乘` → `尝试次数在末端相乘`。
3. `07 · 6 复盘` 教训壹：`重试次数要按链路算。` → `尝试次数要按链路算。`（`.lesson .li` 计数未变，仍是 3 条）

未改动的「重试次数」实例：D2 verdict A 里的「末端放大容易计算，**重试次数**、deadline 和用户反馈集中治理」——这里指的是「作为治理参数集中管理重试次数」，不是在做次数相乘的口径声明，与本任务要统一的歧义无关，保留原样。

pane A 会同步 `assets/sim-4.js` 的变量口径（未由本 pane touch）。

## 完工前全绿验证（实际输出）

```
$ python3 tools/validate.py .
...
[ok] ch02.html
    warn : absolute wording ×1 — 见 tools/absolute-review.md
[ok] ch05.html
    warn : absolute wording ×12 — 见 tools/absolute-review.md
[ok] ch06.html
[ok] ch07.html
    warn : absolute wording ×1 — 见 tools/absolute-review.md
[ok] ch08.html
    warn : absolute wording ×1 — 见 tools/absolute-review.md
[ok] ch09.html
    warn : absolute wording ×1 — 见 tools/absolute-review.md
...
exit=0
```
（warn 非 error，不影响退出码；ch05 剩余 12 处绝对化词命中属于本次 C2 范围之外的既有文本，未动）

```
$ python3 tools/css-audit.py .
23 pages · 0 errors, 0 warnings
exit=0

$ python3 tools/bible-check.py .
warn : B ch05: 未出现 BIBLE 规定的用户量「20 万」——请人工确认表述
0 errors, 1 warnings
exit=0
```
（该 warn 在改动前用 `git stash` 验证过已预先存在，与本 pane 改动无关）

```
$ python3 tools/sim-drift-check.py .
sim-1 ... sim-6 全部 ✅ 状态演进一致
6 simulators · no drift
exit=0

$ python3 tools/derive.py .
[C1]...[C4] 全部不变量一致。
exit=0
```
（`derive.py` 运行会重新生成 `appendix-interview.html`，其中一行随 ch16.html 的文案变化而更新——这是 pane B 改动驱动的派生结果，不是本 pane 手改；已用 `git diff appendix-interview.html` 确认）

```
$ for f in tools/sim*-model-test.js; do node "$f"; done
59 passed, 0 failed（10+8+12+9+10+10）

$ node --check assets/*.js
ok
```

全部命令绿色通过。

## 需要 lead 协调的事项

无。C1/C2/C3 均在本 pane 独占文件内完成，未越界。
