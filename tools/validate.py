#!/usr/bin/env python3
"""全站机械校验（QUALITY.md 第四节的可运行起点）。

用法: python3 tools/validate.py [站点根目录，默认 .]
Claude Code 构建时应按 QUALITY.md 扩展本脚本，且每加一条规则先做变异测试。
"""
import sys, re, collections, pathlib
from html.parser import HTMLParser

VOID = {"meta", "br", "input", "hr", "img", "link", "source", "wbr"}
FORBIDDEN = ["localStorage", "sessionStorage", "http://", "cdn.jsdelivr", "unpkg.com", "googleapis.com"]

# A9: 绝对化词汇清单（命中后先剔除白名单误报，写入复核报告）
ABSOLUTE = ["永远", "唯一", "必然", "绝不", "所有", "一定"]
ABSOLUTE_EXCLUDE = ["不一定", "一定的", "一定程度", "一定要", "唯一真相", "唯一索引"]

# A1: 七段式段名表（ch01 的 ·3 段例外在代码里处理）
SEC_NAMES = {1: "值班现场", 2: "原理", 3: "病历卡", 4: "模拟器", 5: "权衡", 6: "复盘", 7: "自测"}
CARD_LABELS = ["机理", "症状", "易发场景", "处方", "案例"]
BODY_CARD_NOS = {f"{n:02d}" for n in range(1, 15)}      # 正文定义 01..14
APPENDIX_CARD_NOS = {f"{n:02d}" for n in range(1, 18)}  # 附录定义 01..17

CHAPTER_NO_RE = re.compile(r"^ch(\d+)\.html$")
SEC_RE = re.compile(r'<h2><span class="sec">(.*?)</span>', re.S)
SEC_TEXT_RE = re.compile(r"^(\d{2}) · (\d) (.+)$")
COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}(?![0-9a-fA-F])")
XREF_RE = re.compile(r"第 (\d+) 章")

class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errs = [], []
    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)
    def handle_endtag(self, tag):
        if not self.stack:
            self.errs.append(f"stray </{tag}>")
        elif self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errs.append(f"mismatch: expected </{self.stack[-1]}> got </{tag}>")

def div_blocks(html, class_token):
    blocks, start = [], 0
    while True:
        i = html.find("<div", start)
        if i == -1:
            break
        gt = html.find(">", i)
        if gt == -1:
            break
        open_tag = html[i:gt + 1]
        m = re.search(r'class="([^"]*)"', open_tag)
        if m and class_token in m.group(1).split():
            depth, j = 1, gt + 1
            while j < len(html) and depth > 0:
                o = html.find("<div", j)
                c = html.find("</div>", j)
                if o == -1 and c == -1:
                    break
                if o != -1 and (c == -1 or o < c):
                    depth += 1
                    j = o + 4
                else:
                    depth -= 1
                    j = c + 6
            blocks.append(html[i:j])
            start = j
        else:
            start = gt + 1
    return blocks

def check_page(path: pathlib.Path, all_names):
    html = path.read_text(encoding="utf-8")
    errs, warns = [], []
    extra = {"abs": [], "xref": []}

    ids = re.findall(r'id="([^"]+)"', html)
    dup = [i for i, c in collections.Counter(ids).items() if c > 1]
    if dup:
        errs.append(f"duplicate ids: {dup}")

    p = TagChecker(); p.feed(html)
    errs += p.errs
    if p.stack:
        errs.append(f"unclosed tags: {p.stack}")

    for d in set(re.findall(r'data-d="(\d+)"', html)):
        if f'id="v-d{d}"' not in html:
            errs.append(f"decision d{d} missing verdict #v-d{d}")
    for q in set(re.findall(r'data-q="(q\d+)"', html)):
        if f'id="v-{q}"' not in html:
            errs.append(f"quiz {q} missing verdict #v-{q}")

    # A11 v2 条件翻转：每个 data-f="N" 必须有对应的 #v-fN
    for f in set(re.findall(r'data-f="([\w-]+)"', html)):
        if f'id="v-f{f}"' not in html:
            errs.append(f"flip f{f} missing verdict #v-f{f}")

    # A12 v2 交卷练习：.exercise 必须齐备三件套，否则交互失效
    n_ex = len(re.findall(r'class="exercise"', html))
    if n_ex:
        for cls, name in (("ex-input", "输入框"), ("ex-reveal", "揭晓按钮"), ("ex-model", "基准答案块")):
            n = len(re.findall(rf'class="[^"]*\b{cls}\b', html))
            if n < n_ex:
                errs.append(f".exercise {n_ex} 个，但 .{cls}（{name}）只有 {n} 个")

    for word in FORBIDDEN:
        if word in html:
            errs.append(f"forbidden token: {word}")

    # A6 禁止裸色值与内联样式表
    if re.search(r"<style\b", html):
        errs.append("style: 页面禁止 <style> 标签（样式只能来自 assets/style.css）")
    stripped = re.sub(r'href="#[^"]*"', "", html)
    stripped = re.sub(r"&[#0-9a-zA-Z]+;", "", stripped)
    for m in COLOR_RE.finditer(stripped):
        errs.append(f"color: 裸色值 {m.group(0)}（改用 assets/style.css 令牌）")
    for tok in ("rgb(", "rgba(", "hsl("):
        if tok in html:
            errs.append(f"color: 裸色值 {tok}（改用 assets/style.css 令牌）")
    if "assets/style.css" not in html:
        errs.append("css: 未引用 assets/style.css")

    # A7 导航完整性
    if 'class="book-bar"' not in html:
        errs.append('book-bar: 缺少 class="book-bar"')
    nav_m = re.search(r"<nav[^>]*>(.*?)</nav>", html, re.S)
    if nav_m:
        nav_html = nav_m.group(1)
        if 'href="index.html"' not in nav_html:
            errs.append('book-bar: nav 缺少 href="index.html"')
        for tgt in re.findall(r'href="([^"]+\.html)"', nav_html):
            if tgt not in all_names:
                errs.append(f"missing nav target (nav): {tgt}")
        disabled = nav_html.count('aria-disabled="true"')
        if disabled:
            if path.name not in ("index.html", "appendix-interview.html"):
                errs.append("nav: 非 index/appendix-interview 页面出现 aria-disabled")
            elif disabled > 1:
                errs.append("nav: index/appendix-interview 只允许一侧 aria-disabled")
    elif 'class="book-bar"' in html:
        errs.append("book-bar: 缺少 <nav>")
    foot_m = re.search(r"<footer>(.*?)</footer>", html, re.S)
    if foot_m:
        for tgt in re.findall(r'href="([^"]+\.html)"', foot_m.group(1)):
            if tgt not in all_names:
                errs.append(f"missing nav target (footer): {tgt}")

    # A8 章间引用章号合法性（明细报告在 main 里写盘）
    for m in XREF_RE.finditer(html):
        n = int(m.group(1))
        ctx = html[max(0, m.start() - 20):m.end() + 20].replace("\n", " ").strip()
        extra["xref"].append((n, ctx))
        if not (1 <= n <= 16):
            errs.append(f"xref: 引用「第 {n} 章」超出 1–16（上下文：{ctx[:30]}）")

    # A9 绝对化词汇（warn，命中明细写 tools/absolute-review.md）
    ex_spans = []
    for ex in ABSOLUTE_EXCLUDE:
        for em in re.finditer(re.escape(ex), html):
            ex_spans.append(em.span())
    for word in ABSOLUTE:
        for m in re.finditer(re.escape(word), html):
            if any(s <= m.start() < e for s, e in ex_spans):
                continue
            ctx = html[max(0, m.start() - 30):m.end() + 30].replace("\n", " ").strip()
            extra["abs"].append((word, ctx))
    if extra["abs"]:
        warns.append(f"absolute wording ×{len(extra['abs'])} — 见 tools/absolute-review.md")

    # A1/A2/A5/A10 章节页结构检查
    m_ch = CHAPTER_NO_RE.match(path.name)
    if m_ch:
        file_ch = m_ch.group(1)

        # A1 七段式 h2 .sec 编号序列
        secs = []
        for t in SEC_RE.findall(html):
            sm = SEC_TEXT_RE.match(t.strip())
            secs.append((sm.group(1), int(sm.group(2)), sm.group(3).strip()) if sm else None)
        if any(s is None for s in secs):
            errs.append("sec: 存在无法解析的编号（应为 NN · N 段名）")
        else:
            has_sim = '<script src="assets/sim-' in html
            expected = [1, 2, 3, 4, 5, 6, 7] if has_sim else [1, 2, 3, 5, 6, 7]
            nums = [s[1] for s in secs]
            for ch_no, n, _name in secs:
                if ch_no != file_ch:
                    errs.append(f"sec: 章号 {ch_no} 与文件名 {file_ch} 不一致")
            if nums != expected:
                errs.append(f"sec: 段号序列 {nums} ≠ 期望 {expected}")
            else:
                for ch_no, n, name in secs:
                    expect_name = "基线架构图" if (path.name == "ch01.html" and n == 3) else SEC_NAMES[n]
                    if name != expect_name:
                        errs.append(f"sec: 第 {n} 段段名「{name}」应为「{expect_name}」")
            if has_sim and 4 not in nums:
                errs.append("sec: 页面引用 assets/sim-* 却缺少第 4 段（模拟器）")
            if not has_sim and 4 in nums:
                errs.append("sec: 页面未引用 assets/sim-* 却存在第 4 段（模拟器）")

        # A2 病历卡五行（按 case-head 切分，不用脆弱的嵌套 div 正则）
        for part in html.split('<div class="case-head">')[1:]:
            labels = re.findall(r'<div class="lbl">(机理|症状|易发场景|处方|案例)</div>', part)
            if labels != CARD_LABELS:
                errs.append(f"case-card: 五行标签缺失或顺序错误：{labels}")
            else:
                segs = re.split(r'<div class="lbl">', part)
                if len(segs) >= 6 and 'class="sym"' not in segs[2]:
                    errs.append("case-card: 症状行缺少形状符号 (.sym)")
            if not re.search(r'class="case-no">病历卡 No\.\d{2}</span>', part):
                errs.append('case-card: 缺少两位编号「病历卡 No.NN」(.case-no)')

        # A5 决策点：恰好 d1/d2；D2 全 mid；D1 有 good
        decisions = div_blocks(html, "decision")
        d_ids = []
        for blk in decisions:
            m = re.search(r'<div[^>]*\sid="(d\d+)"', blk[:200])
            d_ids.append(m.group(1) if m else None)
        if len(decisions) != 2 or d_ids != ["d1", "d2"]:
            errs.append(f"decision: .decision 数量/顺序 {d_ids} ≠ 恰好 2 个（d1, d2）")
        else:
            for blk, did in zip(decisions, d_ids):
                ks = re.findall(r'data-k="(\w+)"', blk)
                if did == "d2" and any(k != "mid" for k in ks):
                    errs.append('decision: D2 的所有 .opt 必须 data-k="mid"')
                if did == "d1" and "good" not in ks:
                    errs.append('decision: D1 至少一个 .opt data-k="good"')

        # A10 硬计数：quiz=4 / iq=3 / li=3，data-q 只能 q1–q4
        quiz_n = len(re.findall(r'class="quiz"', html))
        if quiz_n != 4:
            errs.append(f"自测题数量 {quiz_n} ≠ 4")
        iq_n = len(re.findall(r'class="iq"', html))
        if iq_n != 3:
            errs.append(f"面试映射问题数量 {iq_n} ≠ 3")
        li_n = len(re.findall(r'class="li"', html))
        if li_n != 3:
            errs.append(f"教训条目数量 {li_n} ≠ 3")
        for q in re.findall(r'data-q="([^"]+)"', html):
            if q not in ("q1", "q2", "q3", "q4"):
                errs.append(f'quiz-opt: data-q="{q}" 超出 q1–q4')

    # A4 关卡页与附录页结构检查
    elif re.match(r"^level\d+\.html$", path.name):
        if html.count('class="disclaimer"') != 1:
            errs.append('level: class="disclaimer" 应为恰好 1 个')
        if html.count('class="sources"') != 1:
            errs.append('level: class="sources" 应为恰好 1 个')
        src_m = re.search(r'<div class="sources">(.*?)</div>', html, re.S)
        if src_m and '<a href="https://' not in src_m.group(1):
            errs.append('level: .sources 里至少 1 个 <a href="https://')
        if len(re.findall(r'class="li"', html)) != 3:
            errs.append("level: .lesson .li 应为恰好 3 个")
        if len(re.findall(r'class="decision"', html)) < 2:
            errs.append("level: .decision 至少 2 个")
    elif path.name == "appendix-cards.html":
        n_cards = len(re.findall(r'class="case-card', html))
        if n_cards != 17:
            errs.append(f"appendix-cards: .case-card 数量 {n_cards} ≠ 17")
    elif path.name == "appendix-interview.html":
        rows = 0
        tbl_m = re.search(r'<table[^>]*class="[^"]*tbl[^"]*"[^>]*>(.*?)</table>', html, re.S)
        if tbl_m:
            body_m = re.search(r"<tbody>(.*?)</tbody>", tbl_m.group(1), re.S)
            rows = (len(re.findall(r"<tr\b", body_m.group(1))) if body_m
                    else len(re.findall(r"<tr\b", tbl_m.group(1))))
        if rows != 48:
            errs.append(f"appendix-interview: table.tbl 行数 {rows} ≠ 48（16 章 × 3 问）")

    return errs, warns, extra

def main(root="."):
    root = pathlib.Path(root)
    pages = sorted(root.glob("*.html"))
    if not pages:
        print("no html pages found"); sys.exit(1)
    all_names = {p.name for p in pages}
    failed = False
    abs_hits, xref_rows, body_defs = [], [], collections.Counter()
    for p in pages:
        errs, warns, extra = check_page(p, all_names)
        abs_hits += [(p.name, w, c) for w, c in extra["abs"]]
        xref_rows += [(p.name, n, c) for n, c in extra["xref"]]
        if CHAPTER_NO_RE.match(p.name):
            for n in re.findall(r'class="case-no">病历卡 No\.(\d{2})</span>', p.read_text(encoding="utf-8")):
                body_defs[n] += 1
        status = "FAIL" if errs else "ok"
        if errs:
            failed = True
        print(f"[{status}] {p.name}")
        for e in errs:
            print(f"    ERROR: {e}")
        for w in warns:
            print(f"    warn : {w}")

    # A3 病历卡编号唯一性（全书级）
    for n, c in sorted(body_defs.items()):
        if c > 1:
            failed = True
            print(f"    ERROR: card-no 病历卡 No.{n} 在正文 ch*.html 中定义 {c} 次（必须 ≤ 1 次）")
    if set(body_defs) != BODY_CARD_NOS:
        failed = True
        print(f"    ERROR: card-no 正文定义的编号集合 {sorted(set(body_defs))} ≠ {sorted(BODY_CARD_NOS)}（应恰好 14 张）")
    app_path = root / "appendix-cards.html"
    if app_path.exists():
        app_nos = re.findall(r'class="case-no">病历卡 No\.(\d{2})</span>', app_path.read_text(encoding="utf-8"))
        if len(app_nos) != 17 or set(app_nos) != APPENDIX_CARD_NOS:
            failed = True
            print(f"    ERROR: card-no 附录定义的编号集合 {sorted(set(app_nos))}（共 {len(app_nos)} 个）≠ {sorted(APPENDIX_CARD_NOS)}")
    else:
        failed = True
        print("    ERROR: card-no appendix-cards.html 缺失，无法校验附录编号集合")

    # A8 章间引用清单（tools/xref-report.md，供人工抽查）
    tools_dir = root / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    with open(tools_dir / "xref-report.md", "w", encoding="utf-8") as f:
        f.write("# 章间引用「第 N 章」清单（tools/validate.py 自动生成 · A8）\n\n")
        f.write("供人工抽查：被引章号必须落在 1–16，且与 BIBLE.md 第 3 节主题一致。\n")
        if not xref_rows:
            f.write("\n（本次运行无任何「第 N 章」引用）\n")
        cur = None
        for page, n, ctx in xref_rows:
            if page != cur:
                f.write(f"\n## {page}\n\n")
                cur = page
            f.write(f"- {page} → 第 {n} 章 → {ctx[:40]}\n")

    # A9 绝对化词汇复核清单（tools/absolute-review.md，warn 不是 error）
    with open(tools_dir / "absolute-review.md", "w", encoding="utf-8") as f:
        f.write("# 绝对化词汇复核清单（tools/validate.py 自动生成 · A9）\n\n")
        f.write("命中「永远/唯一/必然/绝不/所有/一定」（已剔除：不一定/一定的/一定程度/一定要/唯一真相/唯一索引）。")
        f.write("这是 warn 不是 error；QUALITY.md 一.2 要求逐条自检：要么补成立条件，要么改限定表述。\n")
        if not abs_hits:
            f.write("\n（本次运行无命中）\n")
        cur = None
        for page, word, ctx in abs_hits:
            if page != cur:
                f.write(f"\n## {page}\n\n")
                cur = page
            f.write(f"- 「{word}」：…{ctx}…\n")

    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
