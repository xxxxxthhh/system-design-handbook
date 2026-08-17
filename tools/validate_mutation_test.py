#!/usr/bin/env python3
"""validate.py 变异测试：对 A1–A10 每条规则注入一个它应当抓住的错误并断言被抓住。

用法: python3 tools/validate_mutation_test.py
每个用例：干净页面断言「不报该 ERROR」（防误伤），注入错误后断言「确实报 ERROR」。
只依赖标准库（subprocess / tempfile / pathlib）。退出码 0=全过，1=有失败。
"""
import sys, re, tempfile, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
VALIDATE = ROOT / "tools" / "validate.py"

SEC_NAMES = {1: "值班现场", 2: "原理", 3: "病历卡", 4: "模拟器", 5: "权衡", 6: "复盘", 7: "自测"}
LEVEL_SOURCES = ('<div class="sources"><h3>原始来源</h3><ol>'
                 '<li><a href="https://example.com/official">官方复盘</a></li></ol></div>')


def run_validate(tmp):
    r = subprocess.run([sys.executable, str(VALIDATE), str(tmp)],
                       capture_output=True, text=True, cwd=str(ROOT))
    return r.stdout + "\n" + r.stderr


def with_tmp(files, fn):
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        for name, content in files.items():
            (tmp / name).write_text(content, encoding="utf-8")
        return fn(tmp)


def first(out, needle):
    for line in out.splitlines():
        if needle in line:
            return line.strip()
    return ""


def base_ch05():
    secs = "\n".join(f'<h2><span class="sec">05 · {n} {SEC_NAMES[n]}</span>小节</h2>'
                     for n in (1, 2, 3, 4, 5, 6, 7))
    card = ('<div class="case-card"><div class="case-head"><h3>缓存穿透</h3>'
            '<span class="case-no">病历卡 No.04</span></div><div class="case-body">'
            '<div class="case-row"><div class="lbl">机理</div><div class="val">机理内容</div></div>'
            '<div class="case-row"><div class="lbl">症状</div><div class="val"><span class="sym">▁▂▃▄▅</span> 症状内容</div></div>'
            '<div class="case-row"><div class="lbl">易发场景</div><div class="val">场景内容</div></div>'
            '<div class="case-row"><div class="lbl">处方</div><div class="val">处方内容</div></div>'
            '<div class="case-row"><div class="lbl">案例</div><div class="val">案例内容</div></div>'
            '</div></div>')
    d1 = ('<div class="decision" id="d1"><span class="decision-tag">决策点 D1</span><h3>问题</h3>'
          '<button class="opt" data-d="1" data-k="bad"><span class="tag">A</span>错</button>'
          '<button class="opt" data-d="1" data-k="good"><span class="tag">B</span>对</button>'
          '<div class="verdict" id="v-d1"><p>解析</p></div></div>')
    d2 = ('<div class="decision" id="d2"><span class="decision-tag">决策点 D2</span><h3>问题</h3>'
          '<button class="opt" data-d="2" data-k="mid"><span class="tag">A</span>甲</button>'
          '<button class="opt" data-d="2" data-k="mid"><span class="tag">B</span>乙</button>'
          '<div class="verdict" id="v-d2"><p>解析</p></div></div>')
    quizzes = "\n".join(
        f'<div class="quiz" id="q{n}"><h3>Q{n}</h3><p class="stem">题干</p>'
        f'<div class="q-opts"><button class="opt" data-q="q{n}" data-k="bad">A</button>'
        f'<button class="opt" data-q="q{n}" data-k="good">B</button></div>'
        f'<div class="verdict" id="v-q{n}"><p>解析</p></div></div>'
        for n in (1, 2, 3, 4))
    iqs = "\n".join(f'<div class="iq"><b>「问题{n}？」</b><span class="ans">骨架{n}</span></div>'
                    for n in (1, 2, 3))
    lesson = ('<div class="lesson">' + "".join(
        f'<div class="li"><span class="num">{c}</span><div>教训</div></div>'
        for c in ("壹", "貳", "叁")) + '</div>')
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>第 5 章 · 缓存三兄弟 | 系统是被打出来的</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header>
  <div class="book-bar"><span><b>系统是被打出来的</b> · 系统设计实战手册</span><nav aria-label="章节导航"><a href="ch04.html">← 上一章</a><a href="index.html">目录</a><a href="ch06.html">下一章 →</a></nav></div>
</header>
<div class="wrap">
{secs}
<p>这个难题要等第 10 章会正面解决。</p>
{card}
{d1}
{d2}
{quizzes}
<div class="interview">
{iqs}
</div>
{lesson}
</div>
<footer>
  <div class="foot-in">
    <span><a href="ch04.html">← 上一章</a></span>
    <span><a href="appendix-cards.html">附录</a></span>
    <span><a href="ch06.html">下一章 →</a></span>
  </div>
</footer>
<script src="assets/book.js"></script>
<script src="assets/sim-2.js"></script>
</body>
</html>'''


def base_level():
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="book-bar"><span><b>系统是被打出来的</b> · 系统设计实战手册</span><nav aria-label="章节导航"><a href="index.html">目录</a></nav></div>
<div class="wrap">
<div class="disclaimer"><b>关于本页的事实边界：</b>根据官方公开复盘改编。</div>
<h2><span class="sec">关卡 1 · 1 现场</span>现场</h2>
<div class="decision" id="d1"><span class="decision-tag">决策点 D1</span><h3>问题</h3><button class="opt" data-d="1" data-k="good">A</button><div class="verdict" id="v-d1"><p>解析</p></div></div>
<div class="decision" id="d2"><span class="decision-tag">决策点 D2</span><h3>问题</h3><button class="opt" data-d="2" data-k="mid">A</button><div class="verdict" id="v-d2"><p>解析</p></div></div>
<div class="lesson">
<div class="li"><span class="num">壹</span><div>教训一</div></div>
<div class="li"><span class="num">貳</span><div>教训二</div></div>
<div class="li"><span class="num">叁</span><div>教训三</div></div>
</div>
{LEVEL_SOURCES}
</div>
</body>
</html>'''


def base_cards(n):
    cards = "\n".join(
        f'<div class="case-card"><div class="case-head"><h3>卡{i:02d}</h3>'
        f'<span class="case-no">病历卡 No.{i:02d}</span></div><div class="case-body">'
        f'<div class="case-row"><div class="lbl">机理</div><div class="val">x</div></div>'
        f'<div class="case-row"><div class="lbl">症状</div><div class="val"><span class="sym">▁▂▃</span>y</div></div>'
        f'<div class="case-row"><div class="lbl">易发场景</div><div class="val">x</div></div>'
        f'<div class="case-row"><div class="lbl">处方</div><div class="val">x</div></div>'
        f'<div class="case-row"><div class="lbl">案例</div><div class="val">x</div></div>'
        f'</div></div>'
        for i in range(1, n + 1))
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="book-bar"><span><b>系统是被打出来的</b> · 系统设计实战手册</span><nav aria-label="章节导航"><a href="index.html">目录</a></nav></div>
<div class="wrap">
{cards}
</div>
</body>
</html>'''


def base_interview(rows):
    tr = '<tr><td>第 1 章</td><td>追问</td><td>骨架</td><td><a href="ch01.html">ch01</a></td></tr>'
    body = "\n".join(tr for _ in range(rows))
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="book-bar"><span><b>系统是被打出来的</b> · 系统设计实战手册</span><nav aria-label="章节导航"><a href="index.html">目录</a></nav></div>
<div class="wrap">
<div class="tbl-wrap"><table class="tbl"><thead><tr><th>章节</th><th>高频追问</th><th>答题骨架</th><th>锚点</th></tr></thead><tbody>
{body}
</tbody></table></div>
</div>
</body>
</html>'''


def stub_page():
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="book-bar"><span>stub</span><nav aria-label="章节导航"><a href="index.html">目录</a></nav></div>
</body>
</html>'''


def case_a1():
    base = base_ch05()
    clean = with_tmp({"ch05.html": base}, run_validate)
    if "sec:" in clean:
        return False, "clean page 误报: " + first(clean, "sec:")
    mut = base.replace('<h2><span class="sec">05 · 5 权衡</span>小节</h2>', "")
    out = with_tmp({"ch05.html": mut}, run_validate)
    if "sec:" not in out:
        return False, "缺失第 5 段未被抓住"
    return True, ""


def case_a2():
    base = base_ch05()
    clean = with_tmp({"ch05.html": base}, run_validate)
    if "case-card:" in clean:
        return False, "clean page 误报: " + first(clean, "case-card:")
    mut = base.replace('<div class="lbl">案例</div>', '<div class="lbl">处方</div>')
    out = with_tmp({"ch05.html": mut}, run_validate)
    if "case-card:" not in out:
        return False, "五行顺序错乱未被抓住"
    return True, ""


def case_a3():
    base = base_ch05()
    clean = with_tmp({"ch05.html": base}, run_validate)
    if "定义 2 次" in clean:
        return False, "clean page 误报: " + first(clean, "定义 2 次")
    out = with_tmp({"ch05.html": base, "ch06.html": base}, run_validate)
    if "定义 2 次" not in out:
        return False, "编号重复定义未被抓住"
    return True, ""


def case_a4():
    clean = with_tmp({"level1.html": base_level()}, run_validate)
    if "level:" in clean:
        return False, "level clean 误报: " + first(clean, "level:")
    out = with_tmp({"level1.html": base_level().replace(LEVEL_SOURCES, "")}, run_validate)
    if "level:" not in out:
        return False, "level 缺 .sources 未被抓住"
    clean = with_tmp({"appendix-cards.html": base_cards(17)}, run_validate)
    if "appendix-cards:" in clean:
        return False, "appendix-cards clean 误报: " + first(clean, "appendix-cards:")
    out = with_tmp({"appendix-cards.html": base_cards(16)}, run_validate)
    if "appendix-cards:" not in out:
        return False, "附录卡数量 ≠ 17 未被抓住"
    clean = with_tmp({"appendix-interview.html": base_interview(48)}, run_validate)
    if "appendix-interview:" in clean:
        return False, "appendix-interview clean 误报: " + first(clean, "appendix-interview:")
    out = with_tmp({"appendix-interview.html": base_interview(47)}, run_validate)
    if "appendix-interview:" not in out:
        return False, "面试表行数 ≠ 48 未被抓住"
    return True, ""


def case_a5():
    base = base_ch05()
    clean = with_tmp({"ch05.html": base}, run_validate)
    if "decision:" in clean:
        return False, "clean page 误报: " + first(clean, "decision:")
    mut = base.replace('<button class="opt" data-d="2" data-k="mid"><span class="tag">A</span>甲</button>',
                       '<button class="opt" data-d="2" data-k="bad"><span class="tag">A</span>甲</button>')
    out = with_tmp({"ch05.html": mut}, run_validate)
    if "decision:" not in out:
        return False, "D2 选项非 mid 未被抓住"
    return True, ""


def case_a6():
    base = base_ch05()
    clean = with_tmp({"ch05.html": base}, run_validate)
    for marker in ("style:", "color:", "css:"):
        if marker in clean:
            return False, f"clean page 误报 {marker}: " + first(clean, marker)
    out = with_tmp({"ch05.html": base.replace("</head>", "<style>body{}</style></head>")}, run_validate)
    if "style:" not in out:
        return False, "<style> 标签未被抓住"
    color_mut = base.replace('<div class="val">机理内容</div>',
                             '<div class="val">机理内容<span style="color:#ff0000">红</span></div>')
    out = with_tmp({"ch05.html": color_mut}, run_validate)
    if "color:" not in out:
        return False, "裸色值 #ff0000 未被抓住"
    out = with_tmp({"ch05.html": base.replace("assets/style.css", "assets/other.css")}, run_validate)
    if "css:" not in out:
        return False, "未引用 assets/style.css 未被抓住"
    return True, ""


def case_a7():
    base = base_ch05()
    stubs = {name: stub_page() for name in ("index.html", "ch04.html", "ch06.html", "appendix-cards.html")}
    clean = with_tmp({"ch05.html": base, **stubs}, run_validate)
    if "missing nav target" in clean:
        return False, "clean page 误报: " + first(clean, "missing nav target")
    mut = base.replace('<a href="ch06.html">下一章 →</a>', '<a href="ch99.html">下一章 →</a>')
    out = with_tmp({"ch05.html": mut, **stubs}, run_validate)
    if "missing nav target" not in out:
        return False, "导航目标缺失未被抓住"
    return True, ""


def case_a8():
    base = base_ch05()
    clean = with_tmp({"ch05.html": base}, run_validate)
    if "xref:" in clean:
        return False, "clean page 误报: " + first(clean, "xref:")
    out = with_tmp({"ch05.html": base.replace("第 10 章会正面解决", "第 99 章会正面解决")}, run_validate)
    if "xref:" not in out:
        return False, "章号越界未被抓住"
    return True, ""


def case_a9():
    base = base_ch05()
    clean = with_tmp({"ch05.html": base}, run_validate)
    if "absolute wording" in clean:
        return False, "clean page 误报: " + first(clean, "absolute wording")
    mut = base.replace('<p class="stem">题干</p>',
                       '<p class="stem">题干：永远要复现故障，但唯一真相只有一个。</p>')

    def check(tmp):
        out = run_validate(tmp)
        report = (tmp / "tools" / "absolute-review.md").read_text(encoding="utf-8")
        return out, report

    out, report = with_tmp({"ch05.html": mut}, check)
    if "absolute wording" not in out:
        return False, "命中未被上报为 warn"
    if "「永远」：" not in report:
        return False, "报告缺少「永远」命中"
    if "「唯一」：" in report:
        return False, "「唯一真相」白名单被误报"
    return True, ""


def case_a10():
    base = base_ch05()
    clean = with_tmp({"ch05.html": base}, run_validate)
    if "quiz-opt:" in clean:
        return False, "clean page 误报: " + first(clean, "quiz-opt:")
    mut = base.replace('<button class="opt" data-q="q1" data-k="bad">A</button>',
                       '<button class="opt" data-q="q5" data-k="bad">A</button>')
    out = with_tmp({"ch05.html": mut}, run_validate)
    if "quiz-opt:" not in out:
        return False, "data-q 超出 q1–q4 未被抓住"
    return True, ""


CASES = [
    ("A1 段号序列缺失第 5 段被抓住", case_a1),
    ("A2 病历卡五行顺序错乱被抓住", case_a2),
    ("A3 病历卡编号重复定义被抓住", case_a3),
    ("A4 关卡页与附录页结构错误被抓住", case_a4),
    ("A5 D2 选项非 mid 被抓住", case_a5),
    ("A6 style 标签与裸色值被抓住", case_a6),
    ("A7 导航目标缺失被抓住", case_a7),
    ("A8 章引用越界被抓住", case_a8),
    ("A9 绝对化词汇命中且白名单不误报", case_a9),
    ("A10 data-q 超出 q1–q4 被抓住", case_a10),
]


def main():
    if not VALIDATE.exists():
        print(f"FAIL · validate.py 不存在: {VALIDATE}")
        sys.exit(1)
    passed = failed = 0
    for name, fn in CASES:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, f"异常: {type(e).__name__}: {e}"
        if ok:
            passed += 1
            print(f"PASS · {name}")
        else:
            failed += 1
            print(f"FAIL · {name}")
            if detail:
                print(f"      {detail}")
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
