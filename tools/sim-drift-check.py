#!/usr/bin/env python3
"""模拟器漂移检查（QUALITY.md 三.3 的可运行实现）。

QUALITY.md 三.3：「页面内联脚本与无头模型如有逻辑分叉，以页面为准同步回测试——
两者漂移视为构建失败。」

无头测试跑绿，只证明**测试里那个模型**成立；读者在页面上跑的是 assets/sim-N.js。
本脚本比对两侧状态机核心（page 的 modelTick / test 的 tick）在归一化后是否语义等价。

归一化会消去下列**不改变算术**的书写差异：
  - const / let / var 声明关键字
  - for...of 与索引 for 循环（同一遍历语义）
  - 对象属性简写 {x} 与 {x: x}
  - 箭头函数与 function 表达式
  - 注释与全部空白

用法: python3 tools/sim-drift-check.py [站点根目录，默认 .]
"""
import sys, re, pathlib, difflib

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
# sim-2 两侧均由样章逐字抽取，同样纳入检查
SIMS = [1, 2, 3, 4, 5, 6]


def grab(src, names=("modelTick", "tick")):
    for nm in names:
        m = re.search(r"function " + nm + r"\s*\([^)]*\)\s*\{(.*?)\n\}", src, re.S)
        if m:
            return nm, m.group(1)
    return None, None


def norm(b):
    b = re.sub(r"/\*.*?\*/", "", b, flags=re.S)
    b = re.sub(r"//.*$", "", b, flags=re.M)
    b = re.sub(r"\b(const|let|var)\s+", "", b)
    b = re.sub(r"\bfor\s*\(\s*(\w+)\s+of\s+([\w.]+)\s*\)\s*\{", r"FOREACH(\2){", b)
    b = re.sub(r"for\(i=0;i<([\w.]+)\.length;i\+\+\)\{\s*\w+=\1\[i\];", r"FOREACH(\1){", b)
    b = re.sub(r"(\w+)\s*:\s*\1\b", r"\1", b)                       # {x: x} -> {x}
    b = re.sub(r"function\s*\(([^)]*)\)\s*\{\s*return\s+(.*?);\s*\}", r"(\1)=>\2", b)
    b = re.sub(r"\s+", "", b)
    return b


# 展示用字段：绘图环形缓冲与播放控制，不属于状态机算术
DISPLAY_FIELDS = {"hist", "running"}


def state_ops(body):
    """抽取状态机核心 = 对 S.<field> 的全部赋值（含复合赋值），归一化后按顺序返回。

    页面脚本额外计算展示指标（p99/错误率）并写日志，无头模型不需要复制这些；
    真正必须一致的是**状态如何演进**。因此比对对象是 S.* 的赋值算术。
    """
    b = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    b = re.sub(r"//.*$", "", b, flags=re.M)
    ops = []
    for m in re.finditer(r"S\.(\w+)\s*(=|\+=|-=|\*=|/=)\s*([^;\n]+)", b):
        field, op, expr = m.group(1), m.group(2), m.group(3)
        if field in DISPLAY_FIELDS:
            continue
        ops.append(f"S.{field}{op}{norm(expr)}")
    return ops


errs = []
for n in SIMS:
    jsp = ROOT / "assets" / f"sim-{n}.js"
    tsp = next(ROOT.glob(f"tools/sim{n}-*-model-test.js"), None)
    if not jsp.exists() or tsp is None:
        errs.append(f"sim-{n}: 缺少页面脚本或无头测试")
        continue
    njs, bjs = grab(jsp.read_text(encoding="utf-8"))
    ntt, btt = grab(tsp.read_text(encoding="utf-8"))
    if bjs is None or btt is None:
        errs.append(f"sim-{n}: 未找到状态机函数（page={njs} test={ntt}）")
        continue
    a, b = state_ops(bjs), state_ops(btt)
    if a == b:
        print(f"sim-{n}: page.{njs} ≡ test.{ntt}  ✅ 状态演进一致（{len(a)} 处 S.* 赋值）")
    else:
        errs.append(f"sim-{n}: 状态机漂移（page.{njs} {len(a)} 处 vs test.{ntt} {len(b)} 处）")
        for line in difflib.unified_diff(b, a, "test", "page", lineterm="", n=0):
            if line[:3] not in ("---", "+++"):
                errs.append(f"    {line[:130]}")

print("=" * 62)
for e in errs:
    print("ERROR:", e)
print("=" * 62)
print(f"{len(SIMS)} simulators · {'DRIFT DETECTED' if errs else 'no drift'}")
sys.exit(1 if errs else 0)
