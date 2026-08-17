# Pane A · 完工报告

范围：`assets/**` + `tools/sim*-model-test.js`。未触碰任何其他文件。

## A1 · canvas 移动端各向异性拉伸

**改法**：6 个 `assets/sim-*.js` 顶部原来的 `var W = cv.width, H = cv.height;`（固定读
HTML 里写死的 `1760×500`）改成运行时按容器实际 CSS 尺寸 + `devicePixelRatio` 重设
canvas 缓冲区，`W`/`H` 从此代表 **CSS 像素**尺寸而不是缓冲区像素尺寸：

```js
var W, H;
function resizeCanvas(){
  var rect = cv.getBoundingClientRect();
  if (!rect.width || !rect.height) return;
  var dpr = window.devicePixelRatio || 1;
  W = rect.width; H = rect.height;
  cv.width = Math.round(W*dpr); cv.height = Math.round(H*dpr);
  ctx.setTransform(dpr,0,0,dpr,0,0);
}
resizeCanvas();
var resizeTimer = null;
function scheduleResize(){
  if (document.hidden || resizeTimer) return;
  resizeTimer = setTimeout(function(){
    resizeTimer = null;
    if (!document.hidden) resizeCanvas();
  }, 150);
}
window.addEventListener('resize', scheduleResize);
```

（sim-4/5/6 用无空格的压缩风格插入，匹配各文件原有代码风格；sim-5 无 `WINDOW` 常量，
插在 `var DT=0.5;` 前。）

- 缓冲区尺寸 = CSS 显示尺寸 × dpr，二者比例恒等，不再各向异性拉伸；`ctx.setTransform`
  把绘图坐标系换算回 CSS 像素单位，`ctx.lineWidth=3` 之类的线宽值不用改，视觉上始终是
  3 个 CSS px 宽，不会被 dpr 放大失控。
- `draw()`/`line()`/`X()`/`Y...()` 等函数全部通过闭包读外层的 `W`/`H` 变量（grep 确认
  6 个文件里 `W`/`H` 只在 `draw()` 内使用），resize 后这些函数自动用新值，**没有改
  `tick()`/`modelTick()` 里的任何算术**。
- resize 用 `setTimeout` 节流 150ms；`document.hidden` 时既不进入节流队列、执行前也
  再查一次，标签页在后台时不会做无用的 resize/redraw。
- 没有强制在 resize 后立刻 `draw()`——sim-1/2/3/4/6 每 100ms tick 一次、sim-5 每 500ms
  一次，本来就会在极短时间内自然重绘到新尺寸，避免了给 sim-5 的 `draw(r)`（需要上一次
  的结果对象 `r`）单独写重绘触发逻辑，改动更小。

**验证**：起本地 server，用 Chrome 把 ch05.html 开到一个窄视口实测（本环境
`resize_window` 只把 viewport 钉在 220×790，但足以复现"窄屏"场景）：

```json
{"innerWidth":220,"rectWidth":134,"rectHeight":250,
 "bufferWidth":268,"bufferHeight":500,
 "bufferAspect":0.536,"rectAspect":0.536}
```

`bufferWidth/bufferHeight`（268/500）严格等于 `rectWidth/rectHeight × dpr`
（134×2/250×2），`bufferAspect === rectAspect`，不再有拉伸。又用 `getImageData` 确认
resize 后画布上有真实绘制内容（134000 像素中 3151 个非背景色像素），不是空白/报错。
本环境的自动化窗口 `outerWidth` 恒为 0，无法真正验证"运行中拖动窗口触发 resize 监听
器"这条动态路径，但该路径复用的是同一份已验证正确的 `resizeCanvas()`，逻辑上没有
额外风险。

```
$ node --check assets/*.js
（无输出，全部通过）
$ python3 tools/sim-drift-check.py .
...
6 simulators · no drift
$ for f in tools/sim*-model-test.js; do node "$f"; done
（6 个文件全部 PASS，用例数与改动前一致）
```

## A2 · `--faint` 对比度不达 WCAG AA

**决策**：按 fix-A.md 指示——BASE 段不能碰，若要达标就在 EXTENDED 段追加覆盖规则。
用 WCAG 相对亮度公式复核了 `--faint`(#5A657D) 与 `--muted`(#8A94A9) 对三种背景的对比度
（与 idea-craft.md 审计数字一致）：

| | vs --bg | vs --panel | vs --panel-2 |
|---|---|---|---|
| --faint | 3.30 | 3.03 | 3.15 |
| --muted | 6.34 | 5.82 | 6.04 |

`--faint` 全部低于正文 4.5:1 门槛，`--muted` 全部达标，直接复用 `--muted`，
**没有引入任何新裸色值**。

**覆盖了哪些选择器、为什么**：

在文件末尾新增一段 `/* ---------- A2 ... ---------- */` 注释块 + 11 条覆盖规则，
把以下 **定义在 BASE 段、但用于读者需要阅读的正文性质小字** 的选择器文字色从
`--faint` override 成 `--muted`（BASE 段本身一个字节没动，`git diff` 已核对）：

`.book-bar`（书眉）、`h2 .sec`（章节序号标签）、`.pager-body .g`（值班现场终端摘要
文本，如"15 分钟前，运维群最后一条消息"）、`.metric .k`（指标标签）、`.opt .tag`
（决策点/自测选项字母 A/B/C/D）、`.case-no`（病历卡编号）、`.case-alias`（病历卡
别名）、`.case-row .lbl`（病历卡五行标签：机理/症状/易发场景/处方/案例）、
`.sim-metric .k`（模拟器指标标签）、`.sim-log .tt`（模拟器日志时间戳前缀）、
`.foot-in`（页脚链接行）。

另外 7 处 `--faint` 用法**本来就在 EXTENDED 段**，直接改（不需要 override 技巧）：
`.case-ref .no`、`.arch-node .nd`、`.srcref`、`table.tbl th`、`table.tbl td.ch`、
`.toc-num`、`.tag-pill`（未加 `.sim`/`.card` 修饰时的默认色；`.tag-pill.sim`/
`.tag-pill.card` 各自的 `color` 声明特异性更高，不受影响，已用浏览器实测确认）。

**故意没覆盖、保留 `--faint` 的三处**（均为装饰性/非文本，或有 WCAG 例外）：

- `.book-bar a[aria-disabled="true"]`——禁用态链接（如 ch01 的"上一章"）。WCAG 对
  非激活（inactive）UI 控件的文字没有最低对比度要求，保留低对比度本身也是一种
  "已禁用"的视觉提示。
- `.case-ref{border-left:3px solid var(--faint)}`——纯装饰性分隔线，不是文字。
- `.arch-arrow{color:var(--faint)}`——只用来给箭头符号 `→` 上色（grep 确认全站
  `.arch-arrow` 里只有 `<span>→</span>`，没有描述性文字），属于图形符号，适用的是
  WCAG 非文本对比度门槛 3:1，`--faint` 在其所在的 `.arch`（`--panel-2` 背景）下是
  3.15，达标。

**验证**：Chrome 实测 `.case-no`/`.case-row .lbl`/`h2 .sec` 的 `getComputedStyle().color`
均为 `rgb(138, 148, 169)` = `#8A94A9` = `--muted`，覆盖生效。

```
$ python3 tools/css-audit.py .
23 pages · 0 errors, 0 warnings
```

## A3 · sim-4「重试次数」口径

**用的口径**：把 `retries` 统一改名为 `attempts`（尝试次数），语义口径为
**「尝试次数 = 每层实际发起的请求次数，不是 retries=3 表示首次+3次重试」**，即当前
UI 上"3 次"仍然是循环里真实跑 3 次（不是 4 次），只是变量名和描述从"重试 3 次"
的歧义改成"尝试 3 次"的准确口径。**数值行为完全没变**——默认仍是 3 层 × 3 次 = 27
倍放大，`sim-drift-check.py` 和全部模型测试断言（含数值断言 ≈3/≈9/≈27）都还是原样
通过。

**改了什么**：

- `assets/sim-4.js`：`DEF.retries` → `DEF.attempts`，`S.retries` 的全部读写
  （`expectedAmplification`、`injectFailure`、`reset`、`syncLabels`、滑块事件监听）
  改成 `S.attempts`。
- `tools/sim4-retrystorm-model-test.js`：`DEF.retries`/`S.retries` 同步改成
  `DEF.attempts`/`S.attempts`；断言名称里补了"尝试"二字（如"3 次" →"3 次尝试"）
  让断言描述和口径对齐。

**没改的**：DOM 元素 id 字符串 `getElementById('sl-retries')` / `getElementById('lb-retries')`
**保持不变**——这两个 id 定义在 `ch07.html`（pane C 的文件），我不能改。JS 内部变量名
换了，但去读取/写入的 DOM 元素 id 字符串原样保留，功能不受影响（不管 C 那边最终
决定要不要把 HTML 里的 id/可见文案也改成"尝试"相关的措辞，现在的 JS 都能正常工作）。
日志提示文案（如"重试链路就绪""backoff 开启：重试按指数间隔错开"）没有改，因为
它们描述的是"重试"这个机制本身（retry mechanism），不是"重试次数"这个被消歧的
计数口径，两者不冲突。

**需要 C 配合的事项**：ch07 正文如果提到"重试 3 次"「retries=3」这类表述，建议
统一成"3 次尝试/attempts"的口径，与这里的变量名和断言描述对齐，避免正文说
"重试 3 次"（可能被读者理解成首次+3次重试=4次）而模拟器状态是"尝试 3 次"
（=3 次总请求）产生数值对不上的错觉。HTML 侧 `sl-retries`/`lb-retries` 这两个 id
是否要重命名为 `sl-attempts`/`lb-attempts`，由 C 决定；只要 id 字符串不变，我这边
的 JS 不需要跟着再改。

## 完工前全绿输出

```
$ python3 tools/validate.py .
23 pages 全部 [ok]（仅有的 warn 是既有的"绝对化表述"提醒和不属于我范围的正文，
与本次改动无关，改动前后一致）

$ python3 tools/css-audit.py .
23 pages · 0 errors, 0 warnings

$ python3 tools/bible-check.py .
0 errors, 1 warnings（既有的 ch05 "20 万" 提醒，与本次改动无关）

$ python3 tools/sim-drift-check.py .
6 simulators · no drift

$ python3 tools/derive.py .
全部不变量一致。

$ for f in tools/sim*-model-test.js; do node "$f"; done
6 个文件全部 PASS（sim4 用例数不变，断言描述已同步 attempts 口径）

$ node --check assets/*.js
（无输出，全部通过）
```

## 改动文件清单

- `assets/sim-1.js` `assets/sim-2.js` `assets/sim-3.js` `assets/sim-4.js`
  `assets/sim-5.js` `assets/sim-6.js`：A1 响应式 canvas；sim-4 额外含 A3 改名。
- `assets/style.css`：A2，仅 EXTENDED 段（BASE 段 0 处改动，已用 `git diff` 核对）。
- `tools/sim4-retrystorm-model-test.js`：A3 同步改名。
- `assets/book.js`：未改动（其"职责仅一项"的单一用途注释与 canvas resize 无关，
  没有把 resize 逻辑抽到这里，6 个 sim 文件各自独立持有一份，符合"改动最小化"和
  各 sim 文件本就相互独立的既有代码风格）。
