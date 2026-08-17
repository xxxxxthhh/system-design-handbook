# DONE-toolsmith.md · 执行记录

## 任务 A · 扩展 tools/validate.py（A1–A10）

命令：`python3 tools/validate.py .`（2016-08-17）

实际命令输出的最后 3 行：

```
    warn : absolute wording ×13 — 见 tools/absolute-review.md
    ERROR: card-no 正文定义的编号集合 ['02', '04', '05', '06'] ≠ ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14']（应恰好 14 张）
    ERROR: card-no appendix-cards.html 缺失，无法校验附录编号集合
```

备注：此刻站内只有 ch03.html / ch05.html，`missing nav target` 报错为预期（页面未建齐）；
A3 编号集合与 appendix-cards 缺失报错同样为预期。A1/A2/A5/A6/A7/A8/A10 对现存页面零报错。
副产品：`tools/xref-report.md`（A8）、`tools/absolute-review.md`（A9）已生成。

## 任务 B · tools/validate_mutation_test.py（变异测试）

命令：`python3 tools/validate_mutation_test.py`（2016-08-17）

实际命令输出的最后 3 行：

```
PASS · A9 绝对化词汇命中且白名单不误报
PASS · A10 data-q 超出 q1–q4 被抓住
10 passed, 0 failed
```

备注：A1–A10 十条规则各一个变异用例，全部 0 failed（无 FAIL，无需修改 validate.py 规则）。

## 任务 C · tools/derive.py（全局计数派生 + 附录派生）

命令：`python3 tools/derive.py`（2016-08-17，半成品站点：7 章 + 6 模拟器已建）

实际命令输出的最后 3 行：

```
  - 自测题总数 28 ≠ 64（16 章 × 4）
  - 教训总数 21 ≠ 48（16 章 × 3）
exit code: 1
```

备注：C1 差异明细清楚列出缺失页（9 章节 + 4 关卡 + appendix-cards）；C2 零不一致；
C3/C4 在页面未齐时跳过并打印提示，无崩溃。`tools/derived-counts.json` 已写入实际派生值。


