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
    <p class="h1-sub">每一行都由 tools/derive.py 从对应章节的 .interview 区块派生，禁止手工编辑。</p>
  </div>
</header>
<div class="wrap">
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
</div><!-- /wrap -->
<footer>
  <div class="foot-in">
    <span><a href="appendix-cards.html">← 附录 A · 病历卡图鉴</a></span>
    <span>tools/derive.py 生成 · {n_ch} 章 × 3 问</span>
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
