# FACTS-cases.md · 正文病历卡「案例」栏中涉及真实公司的陈述 · 核对清单

> QUALITY.md 二.1 把「病历卡案例栏」与四个关卡并列为最高优先级红线。
> 本表覆盖**正文章节内**引用真实公司的陈述。「秒抢」剧情属虚构，不在此表。

## 规则

1. 病历卡案例栏**优先写「秒抢」虚构剧情**。只有当某个故障模式的真实案例本身具有
   不可替代的教学价值时，才引用真实事故，且必须先在此表登记。
2. 引用真实事故必须满足：**官方复盘可查** + **五要素逐条核对** + **数字带「约」**。
3. 无法定位官方一手来源的传闻（媒体转述、会议 PPT、二手博客）→ **改写为「秒抢」剧情或删除**。
4. 不指名批评，不虚构引语。

---

## C1 · ch05 病历卡 No.06 缓存雪崩 · 案例栏 · Facebook 2010 ✅ 已核实

**页面现有表述**（`ch05.html`，样章已验收）：

> 「Facebook 在 2010 年的一次著名故障中，因配置校验逻辑的错误，所有客户端将缓存值判为无效
> 并同时涌向数据库集群，最终不得不整站下线才恢复，全程约两个半小时（官方复盘公开）。」

**来源**：Robert Johnson，*More Details on Today's Outage*，Facebook Engineering，2010-09-23
https://engineering.fb.com/2010/09/23/uncategorized/more-details-on-today-s-outage/

**逐要素核对**：

| 页面陈述 | 官方原文 | 判定 |
|---|---|---|
| 因配置校验逻辑的错误 | "An automated system for verifying configuration values ended up causing much more damage than it fixed." | ✅ 相符 |
| 客户端将缓存值判为无效 | "Every time a client got an error attempting to query one of the databases it interpreted it as an invalid value, and deleted the corresponding cache key" | ✅ 相符 |
| 同时涌向数据库集群 | "Because the fix involves making a query to a cluster of databases, that cluster was quickly overwhelmed by hundreds of thousands of queries a second." | ✅ 相符 |
| 不得不整站下线才恢复 | "The way to stop the feedback cycle was quite painful – we had to stop all traffic to this database cluster, which meant turning off the site." | ✅ 相符 |
| 全程约两个半小时 | "Facebook was down or unreachable for many of you for approximately 2.5 hours." | ✅ 相符（官方即用 approximately，页面用「约」） |

**结论**：五要素全部与官方一手复盘相符，**样章表述保持不变**。

**附注（不改，仅备案）**：页面用了「所有客户端」，官方原文是 "Every time a client got an error…"。
二者语义一致（凡是遇错的客户端都会这么做，且规模足以逼停整站），但「所有」属于
QUALITY.md 一.2 的绝对化词表。因该表述有官方事实支撑且成立条件明确（"每一个查询报错的客户端"），
**判定为已挂旗、无需改写**。

**附注 2**：这次故障的机制是**反馈循环**——错误 → 判缓存无效 → 删 key → 更多回源 → 更多错误。
它同时也是附录 **No.16 亚稳态故障**的经典案例（触发消失后系统仍停在坏状态）。
附录 No.16 卡的案例栏可复用本条，**引用同一来源**。

## C2 · ch05 病历卡 No.05 缓存击穿 · 案例栏 · 微博 ⚠️ 已确认为安全表述

**页面现有表述**：

> 「微博曾多次在明星突发事件时服务异常（公开报道），是『热点数据 + 瞬时读放大』这一类故障
> 最出名的反复上演——热点问题在第 8 章（热点分片）还会以另一副面孔回来。」

**判定**：该表述**不含**任何可证伪的具体事实断言——无日期、无时长、无损失数字、无机制归因，
且已用「（公开报道）」明确标注信息层级。属于对**广为人知的公开现象**的概括性引用，
不构成 QUALITY.md 二.1 意义上的"事实性陈述"。**保持不变。**

**红线**：后续章节（尤其 ch08 热点分片）如需再次引用该现象，
**不得**升级为带日期／时长／量级的具体断言——除非先找到官方一手来源并登记到本表。

## C3 · 其余章节的案例栏 · 规则

`ch01`–`ch16` 中除 C1、C2 外，病历卡案例栏**一律使用「秒抢」虚构剧情**。
若某章作者认为必须引用真实事故，须先在本表增加条目并完成逐要素核对，**否则视为构建失败**。

四个实战关卡的真实事故另见：
`FACTS-level1.md`（GitLab 2017）／`FACTS-level2.md`（AWS S3 2017）／
`FACTS-level3.md`（Knight Capital 2012）／`FACTS-level4.md`（GitHub 2018）。
