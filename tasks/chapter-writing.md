# 任务书 · 章节写作（所有章节作者共用）

## 必读顺序（一次读完，之后每章开工前重看 BIBLE 对应格）

1. `CLAUDE.md` —— 七段式模板、文风、交互约定
2. `BIBLE.md` —— **连续性圣经，最高优先级**。第 0 节结构规则、第 2 节成长刻度表、
   第 3 节逐章契约表、第 4 节病历卡总表、第 8 节文风红线
3. `TEMPLATE.md` A 节 —— 逐字照抄的 HTML 骨架
4. `ch05.html` —— **唯一视觉与内容基准**。写之前完整读一遍，写完对照它检查语气密度
5. `QUALITY.md` —— 一.1（攻击可运行示例）、一.2（绝对化挂旗）、一.6（改一个错先 grep 变体）

## 你要交付什么

一个 `chNN.html`，纯静态，`<link rel="stylesheet" href="assets/style.css">`，
末尾 `<script src="assets/book.js"></script>`（有模拟器的章节再加 `<script src="assets/sim-N.js"></script>`）。
**页面里不许有 `<style>` 块，不许有裸色值（`#xxxxxx` / `rgb()` / `rgba()`）。**
内联 `style="..."` 只在 TEMPLATE.md 已示范的几处使用，且只用 `var(--xxx)`。

## 不可协商的硬约束

| 项 | 要求 |
|---|---|
| `h2 .sec` 序列 | `NN·1..7`，无模拟器则跳过 `·4`（BIBLE 0.1） |
| 段名 | 1 值班现场 / 2 原理 / 3 病历卡 / 4 模拟器 / 5 权衡 / 6 复盘 / 7 自测 |
| `.decision` | 恰好 2 个，id `d1`（在 ·1 段末）和 `d2`（在 ·5 段） |
| D2 选项 | 全部 `data-k="mid"` |
| `.quiz` | 恰好 4 个，id `q1`–`q4`，verdict id `v-q1`–`v-q4` |
| `.iq` | 恰好 3 个，在正文最后的 `.interview` 块里 |
| `.lesson .li` | 恰好 3 个，编号 `壹 貳 叁` |
| 病历卡 | 只能定义 BIBLE 第 4 节分配给本章的编号，五行顺序 机理/症状/易发场景/处方/案例 |
| 症状行 | 必须有 `<span class="sym">形状</span>`，形状**逐字**取自 BIBLE 第 4 节 |
| 用户量/人数 | 逐字取自 BIBLE 第 2 节，禁止自行发明 |
| 跨章引用 | 章号必须与 BIBLE 第 3 节「必写引用」一致，写成「第 N 章」 |
| 核心公式 | 必须出现 BIBLE 第 3 节指定的公式/核心句，并**代入具体数字演示一遍** |
| id 唯一 | 页内 id 不得重复 |
| 禁用 | localStorage / sessionStorage / `http://` / 外部 CDN / 任何网络请求 |

## 内容质量要求（这是审稿会重点看的）

1. **值班现场必须信息量足够**。读者要能只凭你给的 `.pager` 告警 + `.metrics` 指标卡
   做出 D1 的判断。少给一个关键数字，这一段就废了。时间精确到分钟。
2. **D1 的四个选项都要像真的**。错误选项必须是「真实工程师会做的本能反应」，
   verdict 要说清**为什么这个本能是错的**（照抄 ch05 D1 的写法：A 的问题是时间／B 会让事情更糟／
   D 方向没错但救不了现在）。
3. **·2 原理段必须有一次数字代入**。不是把公式写出来就完事——像 ch05 那样，
   用 `.metrics` 卡片把「参数变一点、结果变几倍」摆出来。数字要自己算对。
4. **D2 三个选项都是对的**，每个给「优点 + <strong>账单：</strong>代价 + 适合什么场景」，
   最后一段给「秒抢」的选择及理由（带 `style="border-top:1px solid var(--line);padding-top:12px;margin-top:14px"`）。
5. **·6 复盘的 timeline 顺序本身是知识**。4 条左右，每条带时刻 + 动作 + 指标怎么变。
6. **自测 4 题**：必含 1 道「看症状形状诊断」型、1 道数字计算型。
   每题 verdict 必须解释**为什么那个诱人的错误选项是错的**，不能只说「B 对」。
7. **面试映射给骨架不给全文**，用 `→` 串步骤，像 ch05 那样。允许留一个「反直觉加分点」。
8. **文风**：值班现场故事化、紧张、具体；原理段精确、不煽情。比喻取材系统世界本身
   （契约 / 账单 / 止血 / 病历 / 护栏 / 死亡螺旋）。
9. **绝对化词**（永远/唯一/必然/绝不/所有/一定）出现即自检：补成立条件，或改限定表述。

## 长度基准

对齐 `ch05.html`：约 450–650 行 HTML。比它明显短 = 内容不够。
不要靠堆砌短段落凑长度，要靠**具体的数字、具体的场景、具体的取舍**。

## 有模拟器的章节

`·4 模拟器` 段**不要自己写**。到 `tasks/sim-N-block.html` 取现成片段**逐字粘贴**
（N 见 BIBLE 第 5 节）。若该文件还不存在，先跳过这一章，去写下一章。
粘贴后确认：`.wrap` 在模拟器段前 `</div>` 闭合、段后重新 `<div class="wrap">` 打开
（照 ch05.html 第 289 / 292 / 346 / 348 行的写法）。

## 写完自查（逐条打勾再报完成）

```bash
python3 - <<'PY'
import re,sys,pathlib
f=sys.argv[1] if len(sys.argv)>1 else 'chNN.html'
h=pathlib.Path(f).read_text(encoding='utf-8')
print('sec:', re.findall(r'<span class="sec">([^<]+)</span>', h))
print('quiz:', h.count('class="quiz"'), '| iq:', h.count('class="iq"'),
      '| li:', h.count('class="li"'), '| decision:', h.count('class="decision"'))
print('bare色值:', re.findall(r'#[0-9a-fA-F]{3,8}\b', h)[:5], '| style块:', '<style>' in h)
ids=re.findall(r'id="([^"]+)"', h); import collections
print('dup ids:', [i for i,c in collections.Counter(ids).items() if c>1])
print('引用章号:', sorted(set(re.findall(r'第 (\d+) 章', h)), key=int))
PY
python3 tools/validate.py .
```

## 报完成

每写完一章，追加到你自己的 `tasks/DONE-<你的名字>.md`：
`chNN ✅ 行数 | sec序列 | 定义的病历卡 | 引用的章号`。
遇到 BIBLE 与 SKELETON 冲突、或规格里有你认为写不下去的地方，**不要自行发明**，
写到 DONE 文件里的 `⚠️ 待裁决` 段落，然后继续下一章。
