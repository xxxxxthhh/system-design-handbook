# 任务书 · toolsmith（校验器与派生脚本）

你只负责 `tools/` 目录下的 Python 脚本。**不要碰任何 `.html`、`assets/`、`BIBLE.md`、`TEMPLATE.md`。**

必读：`QUALITY.md`（尤其第一节第 3 条、第四节全部）、`BIBLE.md` 第 0 节和第 4/5 节、
`TEMPLATE.md`、现有的 `tools/validate.py`、参考页面 `ch05.html`。

---

## 任务 A · 扩展 `tools/validate.py`

在现有脚本基础上**增量添加**下列规则。保留已有规则，不要重写整个文件。
每条规则先在 `tools/validate_mutation_test.py` 里写一个「该规则应当抓住的错误」，
确认能抓住，再认为这条规则可信（QUALITY.md 一.3）。

### A1 七段式 `h2 .sec` 编号序列（最重要的一条）
从每个 `ch\d+\.html` 里按出现顺序抓所有 `<h2><span class="sec">(.*?)</span>`。
每个 `.sec` 文本形如 `05 · 3 病历卡`。解析出 `(章号, 段号, 段名)`。
- 章号必须与文件名一致（`ch05.html` → `05`，两位补零）
- 段号序列必须**恰好**是 `[1,2,3,4,5,6,7]`（有模拟器）或 `[1,2,3,5,6,7]`（无模拟器）
- 段名必须依次匹配：1=值班现场 2=原理 3=病历卡 4=模拟器 5=权衡 6=复盘 7=自测
  - **唯一例外**：`ch01.html` 的第 3 段段名是「基线架构图」（BIBLE.md 0.2 规定）
- 有 `<script src="assets/sim-` 引用的页面必须有第 4 段；没有则必须没有第 4 段

### A2 修掉脆弱的病历卡正则
现有的 `re.findall(r'class="case-card.*?</div>\s*</div>\s*</div>', html, re.S)` 在
`.val` 里出现嵌套 `<div>` 时会错位。改成：先用 `class="case-card` 的位置切段，
段的结束是**下一个** `class="case-card` 的位置或 `</div><!-- ` 注释或文件末尾；
更稳的做法是按 `<div class="case-head">` 到下一个 `<div class="case-head">`（或文末）切分，
再在段内检查五行标签。要求：
- 五行 `机理/症状/易发场景/处方/案例` 齐全**且顺序正确**
- 症状行含 `class="sym"`
- `病历卡 No.NN` 编号存在且为两位数字

### A3 病历卡编号唯一性（全书级）
「定义」= 页面中出现 `<span class="case-no">病历卡 No.NN</span>`（即 `.case-no` 里的编号）。
- 每个编号在**全站 `ch*.html` 中**最多被定义 1 次
- `ch*.html` 中定义的编号集合必须**恰好**是 `{01..14}`
- `appendix-cards.html` 中定义的编号集合必须**恰好**是 `{01..17}`
- `.case-ref` 里的 `<span class="no">病历卡 No.NN</span>` 是**引用**不是定义，不计入唯一性

### A4 关卡页与附录页结构检查
现有脚本只对 `ch\d+\.html` 做结构检查。补上：
- `level\d\.html`：必须含 1 个 `class="disclaimer"`；必须含 1 个 `class="sources"`；
  `.sources` 里至少 1 个 `<a href="https://`；`.lesson .li` 恰好 3 个；
  至少 2 个 `.decision`；每个 `data-d` 有对应 verdict
- `appendix-cards.html`：`.case-card` 恰好 17 个（见 A3）
- `appendix-interview.html`：`table.tbl` 的 `<tbody>` 行数恰好 48（16 章 × 3 问）

### A5 决策点规则
- 每个 `ch\d+\.html` 恰好 2 个 `class="decision"`，id 分别是 `d1` 和 `d2`
- `d2` 块内所有 `.opt` 的 `data-k` 都必须是 `mid`（权衡题没有错答案）
- `d1` 块内至少有一个 `data-k="good"`

### A6 禁止裸色值与内联样式表
- 除 `assets/` 外的任何 `.html` 里**不得**出现 `<style>` 标签
- `.html` 里不得出现裸色值：正则 `#[0-9a-fA-F]{3,8}\b`（排除在 `href="#...` 锚点中的情况）
  以及 `rgb(` / `rgba(` / `hsl(`
- 必须引用 `assets/style.css`

### A7 导航完整性
每个 `.html`（不含 `sample/`）必须：
- 含 `class="book-bar"` 且其中有 `href="index.html"`
- `book-bar` 的 nav 里的所有 `href="xxx.html"` 目标文件**必须真实存在**
- footer 里的所有 `href="xxx.html"` 目标文件必须真实存在
- `index.html` 与 `appendix-interview.html` 允许其中一侧是 `aria-disabled="true"`

### A8 章间引用章号合法性
抓全站 `第 (\d+) 章`，N 必须在 1–16。输出一份「第 N 章」引用清单到
`tools/xref-report.md`（格式：来源文件 → 被引章号 → 上下文 40 字），供人工抽查。

### A9 绝对化词汇复核清单
- `ABSOLUTE` 列表改为 `["永远","唯一","必然","绝不","所有","一定"]`（补上「所有」）
- **排除误报**：命中前先剔除 `不一定`、`一定的`、`一定程度`、`一定要`、`唯一真相`
  （最后一个是 BIBLE 指定的核心句，白名单）
- 不再只打印计数，而是把**每一处命中 + 前后各 30 字上下文**写入 `tools/absolute-review.md`，
  按文件分组。控制台只打印每页命中数。这是 warn 不是 error。

### A10 硬计数（章节页）
保留现有的 quiz=4 / iq=3 / li=3，并补上：`.opt` 里每个 `data-q="qN"` 的 N 必须是 q1–q4。

---

## 任务 B · `tools/validate_mutation_test.py`（变异测试）

对 A1–A10 每条规则各写一个变异用例：把 `ch05.html`（或一个内嵌的最小合法页面字符串）
复制到临时目录，注入一个该规则应当抓住的错误，跑 `validate.py`，断言**它确实报了 ERROR**；
再跑一次未注入的原件，断言**不报该 ERROR**（防止规则误伤）。

输出格式：
```
PASS · A1 段号序列缺失第 5 段被抓住
FAIL · ...
N passed, M failed
```
`sys.exit(1 if failed else 0)`。用标准库即可（`tempfile`、`shutil`、`subprocess`）。

---

## 任务 C · `tools/derive.py`（全局计数程序派生 + 附录派生）

QUALITY.md 一.4：全书计数禁止手写。本脚本是唯一真相源。

### C1 派生并断言全局不变量
扫描站点根目录，统计并断言：
- 章节页数 = 16（`ch01.html`…`ch16.html` 全部存在）
- 关卡页数 = 4
- 模拟器数 = 6（统计 `assets/sim-*.js` 文件数，且每个都有对应 `tools/sim*-model-test.js`）
- 病历卡：正文定义 14 张、附录 17 张
- 面试追问总数 = 48（16 × 3）
- 自测题总数 = 64（16 × 4）
- 教训总数 = 48（16 × 3）
任一不符 → 非零退出并打印差异明细。
把结果写成 `tools/derived-counts.json`，形如
`{"chapters":16,"levels":4,"sims":6,"cards_body":14,"cards_total":17,"interview":48,"quiz":64,"lessons":48}`。

### C2 校验正文里的「全书 N 个」类声称
全站 grep 形如 `全书 (\d+) 个模拟器`、`(\d+) 张病历卡`、`共 (\d+) 章` 的表述，
与 C1 的派生值比对，不一致就报错。

### C3 生成 `appendix-interview.html`
从每个 `ch*.html` 的 `.interview` 区块提取 3 个 `.iq`：`<b>` 里是问题，`.ans` 里是答题骨架。
生成一张 `table.tbl`，列为：`章节` / `高频追问` / `答题骨架` / 锚点链接。
锚点链接指向 `chNN.html`（页面级即可）。**整页由脚本生成并直接写盘**，
页面骨架（head/header/book-bar/footer/script）按 `TEMPLATE.md` 的规范拼装，
`<link rel="stylesheet" href="assets/style.css">`，nav 的上一页是 `appendix-cards.html`、
下一页位置写 `<a href="#" aria-disabled="true">下一章 →</a>`。
脚本顶部注释写明「本文件由 tools/derive.py 生成，禁止手工编辑」，
生成的 HTML 里也加一行 HTML 注释说明。

### C4 校验（**不生成**）`appendix-cards.html`
`appendix-cards.html` 由人工撰写（判断型页面，QUALITY.md 一.5）。
本脚本只校验：17 张卡编号齐全无重复；每张卡的「展开章节」链接目标文件存在；
No.01–14 的卡名与正文定义页的卡名**逐字一致**（打印不一致清单）。

---

## 工作顺序与交付

1. 任务 A → 跑 `python3 tools/validate.py .`（此刻站内只有 ch05.html，允许其它页面缺失导致的
   导航目标不存在报错；把这类报错分类为 `ERROR: missing nav target` 即可，不要为了让它变绿而删规则）
2. 任务 B → 跑 `python3 tools/validate_mutation_test.py`，必须 **0 failed**
3. 任务 C → 跑 `python3 tools/derive.py`（此刻会因页面未建齐而失败，这是**预期**的，
   只要错误信息清楚列出缺哪些页面即可；C3 生成动作在页面齐备前跳过并提示）

每完成一步，追加一行到 `tasks/DONE-toolsmith.md`，写明步骤名 + 实际命令输出的最后 3 行。
全部完成后写 `ALL DONE`。

**不要为了让脚本"通过"而放宽或删除规则。** 校验器的价值就是它会报错。
