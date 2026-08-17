#!/usr/bin/env python3
"""BIBLE.md 一致性横切检查（QUALITY.md 发布前「全站横切检查」的可运行部分）。

validate.py 查的是页面结构；本脚本查的是**内容与连续性圣经是否一致**：
  A 病历卡：定义在正确的章、症状形状逐字一致、编号全书唯一
  B 成长刻度：每章出现 BIBLE 第 2 节规定的用户量与人数
  C 契约级公式/核心句：每章出现 BIBLE 第 3 节指定的那一句
  D 必写跨章引用：BIBLE 第 3 节「必写引用」里的章号确实出现
  E 模拟器：分配到模拟器的章确实引用了对应 sim 脚本，且无模拟器的章没有

用法: python3 tools/bible-check.py [站点根目录，默认 .]
"""
import sys, re, pathlib, collections

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")

# ---- A. 病历卡：编号 → (定义章, 症状形状)  取自 BIBLE.md 第 4 节 ----
CARDS = {
    "01": ("ch02", "▁▂▅███"),
    "02": ("ch03", "▁▁▃▁▁█▁"),
    "03": ("ch04", "▁▁▁▁▁"),
    "04": ("ch05", "▁▂▂▃▃▄▄"),
    "05": ("ch05", "▁▁▁█▁▁▁"),
    "06": ("ch05", "███▁▁▁▁"),
    "07": ("ch07", "▁▂▄█████"),
    "08": ("ch07", "▁▁█▁▁█▁"),
    "09": ("ch07", "███▇▅▃▁"),
    "10": ("ch08", "▁▁▁█▁▁"),
    "11": ("ch09", "▁▂▃▄▅▆▇"),
    "12": ("ch09", "▁▁▁▁▁"),
    "13": ("ch11", "▁▁█▁▁"),
    "14": ("ch15", "██‖██"),
    "15": ("appendix-cards", "▇▇▇▇"),
    "16": ("appendix-cards", "▁█████"),
    "17": ("appendix-cards", "▁▁↕▁▁"),
}

# ---- B. 成长刻度表（BIBLE 第 2 节）: 章 → 用户量关键串 ----
SCALE = {
    "ch02": ["3 千"], "ch03": ["1 万"], "ch04": ["5 万"], "ch05": ["20 万"],
    "ch06": ["50 万"], "ch07": ["100 万"], "ch08": ["180 万"], "ch09": ["300 万"],
    "ch10": ["500 万"], "ch11": ["700 万"], "ch12": ["1000 万"], "ch13": ["2000 万"],
    "ch14": ["4000 万"], "ch15": ["7000 万"], "ch16": ["1.2 亿"],
}

# ---- C. 契约级公式 / 核心句（BIBLE 第 3 节），用一个高辨识度子串代表 ----
CORE = {
    "ch01": ["峰值 QPS", "86,400"],
    "ch02": ["利用率"],
    "ch03": ["复制延迟"],
    "ch04": ["不一致窗口"],
    "ch05": ["总流量 × ( 1 − 命中率 )"],
    "ch06": ["配额"],
    "ch07": ["27"],
    "ch08": ["一致性哈希"],
    "ch09": ["生产速率", "消费速率"],
    "ch10": ["真相"],
    "ch11": ["幂等键"],
    "ch12": ["通过率"],
    "ch13": ["可用率"],
    "ch14": ["traces", "logs"],
    "ch15": ["多数派"],
    "ch16": ["演练"],
}

# ---- D. 必写跨章引用（BIBLE 第 3 节） ----
XREF = {
    "ch01": [16], "ch02": [6, 7], "ch03": [15], "ch04": [5, 10],
    "ch05": [8, 10], "ch06": [7, 12], "ch07": [5, 14], "ch08": [5, 12],
    "ch09": [10, 11], "ch10": [5, 11, 12], "ch11": [7, 15], "ch12": [10, 16],
    "ch13": [7, 14], "ch14": [16], "ch15": [3, 11], "ch16": [1],
}

# ---- E. 模拟器分配（BIBLE 第 5 节） ----
SIMS = {"ch02": 1, "ch05": 2, "ch06": 3, "ch07": 4, "ch08": 5, "ch09": 6}

errs, warns = [], []


def read(stem):
    p = ROOT / f"{stem}.html"
    return p.read_text(encoding="utf-8") if p.exists() else None


# ===== A =====
defined_at = collections.defaultdict(list)
for no, (chap, shape) in CARDS.items():
    html = read(chap)
    if html is None:
        errs.append(f"A 病历卡 No.{no}: 定义页 {chap}.html 不存在")
        continue
    if f'class="case-no">病历卡 No.{no}<' not in html:
        errs.append(f"A 病历卡 No.{no}: 未在 {chap}.html 中找到 .case-no 定义")
    if shape not in html:
        errs.append(f"A 病历卡 No.{no}: 症状形状 {shape} 未在 {chap}.html 中逐字出现")

# 全书唯一性：正文页里每个编号最多定义一次
for p in sorted(ROOT.glob("ch*.html")):
    for no in re.findall(r'class="case-no">病历卡 No\.(\d+)<', p.read_text(encoding="utf-8")):
        defined_at[no].append(p.stem)
for no, pages in defined_at.items():
    if len(pages) > 1:
        errs.append(f"A 病历卡 No.{no} 在正文中被定义 {len(pages)} 次: {pages}")
    expected = CARDS.get(no, (None, None))[0]
    if expected and pages and pages[0] != expected:
        errs.append(f"A 病历卡 No.{no} 定义在 {pages[0]}，BIBLE 规定为 {expected}")

# ===== B / C / D / E =====
for n in range(1, 17):
    stem = f"ch{n:02d}"
    html = read(stem)
    if html is None:
        errs.append(f"{stem}.html 缺失")
        continue

    for tok in SCALE.get(stem, []):
        if tok not in html:
            warns.append(f"B {stem}: 未出现 BIBLE 规定的用户量「{tok}」——请人工确认表述")

    for tok in CORE.get(stem, []):
        if tok not in html:
            errs.append(f"C {stem}: 契约级核心内容缺失，未找到「{tok}」")

    found = set(int(x) for x in re.findall(r"第 (\d+) 章", html))
    for want in XREF.get(stem, []):
        if want not in found:
            errs.append(f"D {stem}: BIBLE 要求的跨章引用「第 {want} 章」未出现")

    simn = SIMS.get(stem)
    has_ref = f'assets/sim-{simn}.js' in html if simn else False
    any_sim = re.search(r'assets/sim-(\d+)\.js', html)
    if simn and not has_ref:
        errs.append(f"E {stem}: 应引用 assets/sim-{simn}.js，未找到")
    if not simn and any_sim:
        errs.append(f"E {stem}: 不应有模拟器，却引用了 {any_sim.group(0)}")

# ===== 附录 =====
apx = read("appendix-cards")
if apx is None:
    errs.append("appendix-cards.html 缺失")
else:
    nos = re.findall(r'class="case-no">病历卡 No\.(\d+)<', apx)
    if sorted(nos) != sorted(CARDS.keys()):
        errs.append(f"附录 A 编号集合 {sorted(set(nos))} ≠ 01–17")
    dup = [n for n, c in collections.Counter(nos).items() if c > 1]
    if dup:
        errs.append(f"附录 A 编号重复: {dup}")
    for no, (chap, shape) in CARDS.items():
        if shape not in apx:
            errs.append(f"附录 A: No.{no} 的症状形状 {shape} 未逐字出现")

# ===== F. 导航链顺序（BIBLE 第 7 节）=====
# validate.py 的 A7 只校验 nav 目标文件存在；这里校验**顺序**与骨架一致。
CHAIN = ["index", "ch01", "ch02", "ch03", "level1", "ch04", "ch05", "ch06", "ch07",
         "level2", "ch08", "ch09", "ch10", "ch11", "ch12", "level3", "ch13", "ch14",
         "ch15", "level4", "ch16", "appendix-cards", "appendix-interview"]

pos = {name: i for i, name in enumerate(CHAIN)}
for i, name in enumerate(CHAIN):
    html = read(name)
    if html is None:
        errs.append(f"F 导航链: {name}.html 缺失")
        continue
    nav = re.search(r'<nav[^>]*>(.*?)</nav>', html, re.S)
    if not nav:
        errs.append(f"F {name}: book-bar 中没有 <nav>")
        continue
    hrefs = re.findall(r'href="([^"]+)"', nav.group(1))
    hrefs = [h for h in hrefs if h.endswith(".html")]
    want_prev = CHAIN[i - 1] + ".html" if i > 0 else None
    want_next = CHAIN[i + 1] + ".html" if i < len(CHAIN) - 1 else None
    # nav 结构固定为 [上一页, 目录, 下一页]；首/末页其中一侧为 aria-disabled 的 #
    got_prev = hrefs[0] if hrefs else None
    got_next = hrefs[-1] if hrefs else None
    if want_prev and got_prev != want_prev and got_prev != "index.html":
        errs.append(f"F {name}: nav 上一页 = {got_prev}，BIBLE 第 7 节要求 {want_prev}")
    if want_next and got_next != want_next:
        errs.append(f"F {name}: nav 下一页 = {got_next}，BIBLE 第 7 节要求 {want_next}")
    if "index.html" not in hrefs:
        errs.append(f"F {name}: nav 缺少回目录链接")

print("=" * 62)
for e in errs:
    print("ERROR:", e)
for w in warns:
    print("warn :", w)
print("=" * 62)
print(f"{len(errs)} errors, {len(warns)} warnings")
sys.exit(1 if errs else 0)
