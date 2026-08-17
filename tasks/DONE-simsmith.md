Sim-1 ✅ 10 passed
  - 规格修正：原式 `cap = 并发数 / 服务耗时` 与“保持同一负载、并发翻倍后吞吐不变且 P99 不降”矛盾；模型显式加入固定下游有效并行度，超出的连接槽按比例增加实际服务耗时，以表达“槽位不是服务能力”。
Sim-3 ✅ 12 passed
Sim-4 ✅ 9 passed
Sim-5 ✅ 10 passed
  - 实验约束说明：30% 单 key 热点在完全均匀的 4 节点系统中理论上最多形成 `1.9×` 平均负载，无法满足 `>2`；热点实验固定用 5 节点执行，两种模式均严格超过 `2×`，热点占比仍为 30%。
Sim-6 ✅ 10 passed
ALL DONE

## 章节写作

ch09 ✅ 454 行 | 09·1,2,3,4,5,6,7 | No.11 / No.12 | 引用第 10 / 11 章
  - `python3 tools/validate.py .`：FAIL（仓库基线仍缺 ch08/index/ch10/appendix 等导航目标，且全书病历卡集合与附录尚未完成；ch09 结构、计数、id、片段一致性均通过）。
ch10 ✅ 471 行 | 10·1,2,3,5,6,7 | 引用 No.03 / 04–06 / 13（无新增） | 引用第 4 / 5 / 11 / 12 章
  - `python3 tools/validate.py .`：FAIL（仓库仍缺 index/ch11/appendix 等导航目标，且全书病历卡集合与附录尚未完成；ch10 结构、计数、id 与绝对化词复核通过）。
ch11 ✅ 465 行 | 11·1,2,3,5,6,7 | No.13 | 引用第 7 / 9 / 15 章
  - `python3 tools/validate.py .`：FAIL（仓库仍缺 index/ch12/appendix 等导航目标，且全书病历卡集合与附录尚未完成；ch11 结构、计数与 id 通过；2 个绝对化提示分别是任务书要求的核心句“唯一 ID”和面试主题“唯一索引”，已按技术语境复核）。
ch13 ✅ 474 行 | 13·1,2,3,5,6,7 | 引用 No.09 / 附录 No.15（无新增） | 引用第 7 / 14 章
  - `python3 tools/validate.py .`：FAIL（仓库仍缺 ch12/index/ch14/appendix 等导航目标，且全书病历卡集合与附录尚未完成；ch13 结构、计数、id 与绝对化词复核通过）。
ch14 ✅ 458 行 | 14·1,2,3,5,6,7 | 引用 No.07 / 11 / 附录 No.15（无新增） | 引用第 7 / 9 / 16 章
  - `python3 tools/validate.py .`：FAIL（仓库仍缺 index/ch15/appendix 等导航目标，且全书病历卡集合与附录尚未完成；ch14 结构、计数、id 与绝对化词复核通过）。
ch15 ✅ 472 行 | 15·1,2,3,5,6,7 | No.14 | 引用第 3 / 11 章、附录 No.17 / 关卡四
  - `python3 tools/validate.py .`：FAIL（仓库仍缺 index/level4/appendix 等导航目标，且附录尚未完成；ch15 结构、计数、id 与绝对化词复核通过）。

最终复核：六章契约自检 0 failed；Sim-6 片段与 `tasks/sim-6-block.html` 逐字一致。最终 `python3 tools/validate.py .` 仍为 FAIL，仅因本轮禁改或尚未提供的 `index.html`、`ch12.html`、`level4.html`、`appendix-cards.html` 等导航目标缺失；本轮六章无其他结构错误。ch11 的 2 个绝对化提示是契约原句“唯一 ID”和面试题“唯一索引”，已按要求保留。

CHAPTERS ALL DONE

## 附录 A · 病历卡图鉴

appendix-cards ✅ 609 行 | 6 个症状形状分组 | 病历卡 No.01–17 | 17 张卡均为完整五行结构并带展开章节/附录新增链接
  - 专项契约自检：0 failed（编号与分组顺序、名称与 BIBLE 症状形状、五行标签、链接、案例来源边界、禁用组件全部通过）。
  - `python3 tools/validate.py .`：PASS（退出码 0，`appendix-cards.html` 为 `[ok]`）。唯一绝对化提示来自 FACTS-cases.md C1 要求逐字保留的“所有客户端”，其成立条件与官方来源已在事实表核实。

APPENDIX CARDS DONE
