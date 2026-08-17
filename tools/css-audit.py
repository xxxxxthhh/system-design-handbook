#!/usr/bin/env python3
"""渲染面静态审计（替代逐页目检的可运行部分）。

QUALITY.md 要求发布前做「深色模式逐页目检、移动端宽度目检」。目检需要浏览器；
本脚本把其中**可以静态判定**的部分自动化，覆盖目检最容易发现的几类缺陷：

  1. 用了但没定义的 class —— 会渲染成完全无样式的裸元素（深色模式下通常是刺眼的白底黑字）
  2. HTML 里的裸色值 —— 绕过设计令牌，深色模式下大概率失控
  3. 缺少 style.css / book.js 引用 —— 整页失去样式或交互
  4. 宽内容没有横向滚动容器 —— 移动端会把 body 撑出横向滚动条
  5. 模拟器页面的 canvas / 控件 id 与 sim 脚本是否对得上
  6. 定义了但全站没用过的 class —— 死 CSS（仅提示）

用法: python3 tools/css-audit.py [站点根目录，默认 .]
"""
import sys, re, pathlib, collections

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
CSS = ROOT / "assets" / "style.css"

errs, warns, notes = [], [], []

css_text = CSS.read_text(encoding="utf-8")
# 去掉注释再抓选择器
css_nc = re.sub(r"/\*.*?\*/", "", css_text, flags=re.S)
defined = set(re.findall(r"\.([A-Za-z_][\w-]*)", css_nc))

# 伪类/伪元素与状态类不会出现在静态 HTML 里，属于脚本运行时添加
RUNTIME_CLASSES = {
    "show", "picked-good", "picked-bad",
    # sim-2.js 在 tick 中赋值：st.className = 'v state-' + label
    "state-健康", "state-承压", "state-过载", "state-宕机",
}

# 纯 JS 钩子类：只用于 querySelector 定位，样式由同元素上的其它 class 提供。
# 它们**不应该**有 CSS 定义——在这里登记，避免审计器把「故意没有样式」误报成缺失。
JS_HOOK_CLASSES = {
    "ex-reveal",   # book.js：交卷按钮，视觉由 .btn.primary 提供
}

used = collections.defaultdict(set)          # class -> {页面}
pages = sorted(p for p in ROOT.glob("*.html"))
if not pages:
    print("no html pages found"); sys.exit(1)

for p in pages:
    html = p.read_text(encoding="utf-8")

    for attr in re.findall(r'class="([^"]+)"', html):
        for c in attr.split():
            used[c].add(p.name)

    # 2 裸色值（排除 href="#..." 锚点）
    stripped = re.sub(r'href="#[^"]*"', "", html)
    bare = re.findall(r"#[0-9a-fA-F]{3,8}\b", stripped) + \
           re.findall(r"\b(?:rgb|rgba|hsl|hsla)\(", stripped)
    if bare:
        errs.append(f"{p.name}: HTML 内出现裸色值 {sorted(set(bare))[:4]}")

    # 3 资源引用
    if 'href="assets/style.css"' not in html:
        errs.append(f"{p.name}: 未引用 assets/style.css")
    if 'src="assets/book.js"' not in html:
        errs.append(f"{p.name}: 未引用 assets/book.js")
    if "<style" in html:
        errs.append(f"{p.name}: 页面内出现 <style> 块")

    # 4 宽内容的横向滚动容器
    n_table = len(re.findall(r"<table", html))
    n_wrap = len(re.findall(r'class="tbl-wrap"', html))
    if n_table > n_wrap:
        errs.append(f"{p.name}: {n_table} 个 <table> 但只有 {n_wrap} 个 .tbl-wrap 横向滚动容器")
    for m in re.finditer(r'class="arch"', html):
        pass  # .arch 自带 overflow-x:auto，见 style.css

    # 5 模拟器 id 对齐
    sim = re.search(r'src="assets/(sim-\d+)\.js"', html)
    if sim:
        js = (ROOT / "assets" / f"{sim.group(1)}.js").read_text(encoding="utf-8")
        need = set(re.findall(r"getElementById\('([^']+)'\)", js))
        have = set(re.findall(r'id="([^"]+)"', html))
        miss = need - have
        if miss:
            errs.append(f"{p.name}: {sim.group(1)}.js 读取的 id 在页面中缺失: {sorted(miss)}")
        if "<canvas" not in html:
            errs.append(f"{p.name}: 引用了模拟器脚本但页面没有 <canvas>")

# 1 用了但没定义
for c, where in sorted(used.items()):
    if c not in defined and c not in RUNTIME_CLASSES and c not in JS_HOOK_CLASSES:
        errs.append(f"class .{c} 被使用但 style.css 中无定义 → 会渲染成无样式元素（{sorted(where)[:3]}）")

# 6 死 CSS（仅提示）
unused = sorted(defined - set(used) - RUNTIME_CLASSES - JS_HOOK_CLASSES)
if unused:
    notes.append(f"style.css 中定义但全站未使用的 class（{len(unused)}）: {unused}")

# 令牌完整性：EXTENDED 段不得引入 BASE 未定义的变量
declared = set(re.findall(r"(--[\w-]+)\s*:", css_nc))
referenced = set(re.findall(r"var\((--[\w-]+)", css_nc))
missing_var = referenced - declared
if missing_var:
    errs.append(f"style.css 引用了未定义的 CSS 变量: {sorted(missing_var)}")

print("=" * 66)
for e in errs:
    print("ERROR:", e)
for w in warns:
    print("warn :", w)
for n in notes:
    print("note :", n)
print("=" * 66)
print(f"{len(pages)} pages · {len(errs)} errors, {len(warns)} warnings")
sys.exit(1 if errs else 0)
