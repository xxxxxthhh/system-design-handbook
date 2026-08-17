# 任务 · 实测并修复目录页 tag-pill 布局（先量，后改）

工作目录 `/Users/kyx/Documents/sd-handbook-build-pack-v1`。站点已上线：
https://xxxxxthhh.github.io/system-design-handbook/

## 现象（用户实拍）

`index.html` 目录区，**同时含两个 `.tag-pill` 的行**排布异常。从截图测到的像素关系是：

- 第 7 章行：`病历卡 No.07–09` 与 `Sim-4 重试风暴`
- 第 8 章行：`病历卡 No.10` 与 `Sim-5 一致性哈希`
- 第 9 章行：`病历卡 No.11–12` 与 `Sim-6 积压水位`

三行都表现为：**第二个 pill 的水平起点 ≈ 第一个 pill 的右边缘 + gap，但垂直位置低了约一个行高。**

而 `level2.html` 那行的三个 pill（真实事故 / 官方复盘改编 / 3 个决策点）**排布完全正常**，
在同一行左对齐。两者 HTML 结构完全相同（都是 `.toc-tags` 里并排的 `<span class="tag-pill">`）。

**注意**：标准 flexbox 不会产生「第二项换行且缩进」的布局。所以 lead 的静态推理走不下去了——
必须实测。

## 你的任务：先量，后改

### 第一步 · 实测（这一步不许跳过，也不许用推理代替）

pane 跑在用户真实 shell 里，**不受沙箱限制**，可以起本地服务、可以访问 localhost。
请自己判断用什么手段做真实渲染测量，可选（按你判断的可行性挑）：

- 起 `python3 -m http.server`，用可用的无头浏览器（puppeteer / playwright / chrome --headless）
  载入 index.html，在多个视口宽度下 `getBoundingClientRect()` 量 `.toc-tags` 及其子元素
- 若无无头浏览器，检查是否有 node + jsdom（注意 jsdom **不做布局**，量不出几何，
  只能用来验证 DOM 结构与 CSS 解析——**不要用它冒充布局测量**）
- 其它你认为可靠的办法

**必须测到的数据**（至少覆盖 375px / 768px / 1280px 三个视口）：

1. `.toc-tags` 的 computed `display` / `flex-wrap` / `align-items` / `gap` / `row-gap` / `column-gap`
2. 两个 pill 各自的 `getBoundingClientRect()`（x / y / width / height）与 computed `display`
3. `.toc-tags` 容器自身的宽度
4. 对比组：`level2.html` 那行（三个 pill，正常）的同样数据

**如果测下来两个 pill 的 y 相同**（即其实在同一行），就说明是读图误判，
请如实报告「现象不成立」并停止——不要为了交差硬改。

### 第二步 · 定位成因

用实测数据说明**到底为什么**会这样。可疑方向（自行验证，别照抄）：
`gap` 在某些浏览器 flex 布局下的支持、`.toc-item>*{min-width:0}` 的影响、
`line-height` 与 `vertical-align`、字体回退导致 pill 实际宽度远超预期、
或者根本是别的原因。

### 第三步 · 修复

只改 `assets/style.css` 的 **EXTENDED 段**（BASE 段禁止修改）。禁止裸色值。改动最小。
修完**用同样的测量方法复测**，证明三个视口下两个 pill 都在同一行且左对齐。

## 验收

```bash
python3 tools/validate.py . && python3 tools/css-audit.py . && python3 tools/bible-check.py .
```

## 交付

写入 `tasks/UI-MEASURE-REPORT.md`：
1. 你用的测量手段（以及为什么可靠）
2. **三个视口的原始测量数据**（贴表）
3. 根因结论 + 依据
4. 改动 diff 与修复后的复测数据
5. 如果结论是「现象不成立」，直接写明并说明 lead 的读图错在哪

**不要 commit、不要 push。**
