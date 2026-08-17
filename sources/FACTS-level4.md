# FACTS-level4.md · GitHub 2018-10-21 四十三秒与二十四小时 · 逐句核对清单

> QUALITY.md 第二节协议。level4.html 的每个事实性陈述都必须能在本表找到行号。

## 来源

| 代号 | 文档 | URL | 本地留档 |
|---|---|---|---|
| S1 | GitHub 官方 *October 21 post-incident analysis*（Jason Warner，2018-10-30 发布，2021-12-19 更新） | https://github.blog/news-insights/company-news/oct21-post-incident-analysis/ | `sources/raw/github-2018-post-incident.txt` |

**只有 S1。** SKELETON 提到的备选案例 Facebook 2021 BGP 不启用——GitHub 案例与第 15 章的
**数据分叉恢复问题形成对照**（注意：不是同一种成因，见下方定性边界），
且官方复盘的决策链完整，教学价值更高。

---

## A. 43 秒

| # | 陈述 | S1 原文依据 |
|---|---|---|
| A1 | **2018 年 10 月 21 日 22:52 UTC**，一次**例行维护**——更换出故障的 100G 光设备——导致 GitHub **美东网络枢纽**与**美东主数据中心**之间失去连通性 | "At 22:52 UTC on October 21, routine maintenance work to replace failing 100G optical equipment resulted in the loss of connectivity between our US East Coast network hub and our primary US East Coast data center." |
| A2 | 连通性在 **43 秒**后恢复 | "Connectivity between these locations was restored in 43 seconds" |
| A3 | 但这 43 秒触发了一连串事件，最终造成 **24 小时 11 分钟**的服务降级 | "but this brief outage triggered a chain of events that led to 24 hours and 11 minutes of service degradation." |
| A4 | 背景：GitHub 用 **MySQL** 存非 Git 的元数据（PR、issue、认证、后台任务等），集群规模从数百 GB 到近 **5 TB**，每个集群带最多数十个只读副本 | "GitHub operates multiple MySQL clusters varying in size from hundreds of gigabytes to nearly five terabytes, each with up to dozens of read replicas per cluster" |
| A5 | 用 **Orchestrator** 管理 MySQL 拓扑与自动 failover，它**基于 Raft 做共识** | "We use Orchestrator to manage our MySQL cluster topologies and handle automated failover. Orchestrator considers a number of variables during this process and is built on top of Raft for consensus." |
| A6 | S1 自己已经点出隐患：**Orchestrator 可能实现出应用层根本支撑不了的拓扑**，所以必须让它的配置与应用层预期对齐 | "It's possible for Orchestrator to implement topologies that applications are unable to support, therefore care must be taken to align Orchestrator's configuration with application-level expectations." |

## B. 跨区域 failover 后的数据分叉如何形成

| # | 陈述 | S1 原文依据 |
|---|---|---|
| B1 | 网络分区期间，原本在主数据中心活跃的 Orchestrator **按 Raft 共识开始"卸任"流程** | "During the network partition described above, Orchestrator, which had been active in our primary data center, began a process of leadership deselection, according to Raft consensus." |
| B2 | **美西数据中心**与**美东公有云**的 Orchestrator 节点**凑齐了法定人数（quorum）**，开始把集群 failover 过去，让写入指向**美西** | "The US West Coast data center and US East Coast public cloud Orchestrator nodes were able to establish a quorum and start failing over clusters to direct writes to the US West Coast data center." |
| B3 | 连通性恢复后，应用层**立刻**开始把写流量打向美西的新主库 | "When connectivity was restored, our application tier immediately began directing write traffic to the new primaries in the West Coast site." |
| B4 | **两边都有对方没有的写入**：美东数据库上有一小段还没复制到美西的写；美西又在持续接收新写入。因此**无法安全地把主库切回美东** | "The database servers in the US East Coast data center contained a brief period of writes that had not been replicated to the US West Coast facility. Because the database clusters in both data centers now contained writes that were not present in the other data center, we were unable to fail the primary back over to the US East Coast data center safely." |
| B5 | 未复制到美西的写入**总量很小**，例：**最繁忙的一个集群在受影响窗口里有 954 次写入** | "The total number of writes that were not replicated to the West Coast was relatively small. For example, one of our busiest clusters had 954 writes in the affected window." |

> **⚠️ 定性边界（终审加注）**：S1 **没有**证据表明美东旧主在美西提主后仍继续接受新写入，
> 也没有证据表明两个 MySQL 主库同时持有写入资格。S1 支持的是：
> failover 前美东有未复制出去的写 + failover 后美西有新写 = **两段无法直接拼接的历史**。
> 因此页面**不得**把它称为「同时双主」或「教科书式脑裂」，
> 准确表述是**「跨区域自动 failover 之后的数据分叉」**；
> 与病历卡 No.14 的关联只能写成「恢复阶段面对同一道难题」，不能写成同一种成因。
>
> 同理，**不得**写「没有任何组件出故障」——S1 明确写的是
> "routine maintenance work to replace **failing** 100G optical equipment"，
> 出故障的光设备是事故起点。可以写的是：官方未归因于个人操作失误或 Orchestrator 代码缺陷。

## C. 响应时间线（UTC）

| # | 时刻 | 陈述 | S1 原文依据 |
|---|---|---|---|
| C1 | 10-21 22:54 | 内部监控开始告警；多名工程师响应 | "Our internal monitoring systems began generating alerts indicating that our systems were experiencing numerous faults." |
| C2 | 23:02 | 一线响应团队判定多个数据库集群拓扑处于**非预期状态**；查 Orchestrator API 显示复制拓扑里**只剩美西的服务器** | "engineers in our first responder team had determined that topologies for numerous database clusters were in an unexpected state. Querying the Orchestrator API displayed a database replication topology that only included servers from our US West Coast data center." |
| C3 | 23:07 | 团队**手动锁死内部部署工具**，防止再引入任何变更 | "the responding team decided to manually lock our internal deployment tooling to prevent any additional changes from being introduced." |
| C4 | 23:09 / 23:13 | 站点状态置为 **yellow**，自动升级为正式事件；23:11 事件协调人加入，两分钟后（23:13）改为 **status red** | "At 23:09 UTC, the responding team placed the site into yellow status... At 23:11 UTC the incident coordinator joined and two minutes later made the decision change to status red." |
| C5 | 23:13 | 已明确问题波及多个集群；数据库工程团队被呼叫。此时**美西集群已经吃进了将近 40 分钟的应用写入**，同时美东还存在那几秒未复制的写，**双向阻断了复制** | "by this point the West Coast database cluster had ingested writes from our application tier for nearly 40 minutes. Additionally, there were the several seconds of writes that existed in the East Coast cluster that had not been replicated to the West Coast and prevented replication of new writes back to the East Coast." |
| C6 | 23:19 | 明确选择**暂停 webhook 投递与 GitHub Pages 构建**，宁可部分降级也不拿已收到的用户数据冒险 | "We made an explicit choice to partially degrade site usability by pausing webhook delivery and GitHub Pages builds instead of jeopardizing data we had already received from users." |
| C7 | 10-22 00:05 | 制定方案：**从备份恢复 → 两地副本同步 → 回到稳定拓扑 → 再处理积压任务** | "Our plan was to restore from backups, synchronize the replicas in both sites, fall back to a stable serving topology, and then resume processing queued jobs." |
| C8 | 00:41 | 所有受影响 MySQL 集群的备份恢复流程已启动 | "A backup process for all affected MySQL clusters had been initiated by this time" |
| C9 | 06:51 | 部分集群在美东完成备份恢复并开始从美西复制新数据；跨洋写入让页面变慢，但读到新恢复副本的请求能拿到最新结果 | "Several clusters had completed restoration from backups in our US East Coast data center and begun replicating new data from the West Coast. This resulted in slow site load times for pages that had to execute a write operation over a cross-country link" |
| C10 | 11:12 | **所有数据库主库重新回到美东**，站点响应显著改善；但仍有数十个只读副本落后主库数小时，用户会读到不一致的数据 | "All database primaries established in US East Coast again... there were still dozens of database read replicas that were multiple hours delayed behind the primary. These delayed replicas resulted in users seeing inconsistent data" |
| C11 | 13:15 | 接近流量高峰；复制延迟**不降反升**。团队在美东公有云增开只读副本，摊薄读负载后复制才追上来 | "It was clear that replication delays were increasing instead of decreasing towards a consistent state... Once these became available it became easier to spread read request volume across more servers. Reducing the utilization in aggregate across the read replicas allowed replication to catch up." |
| C12 | 16:24 | 副本同步后切回原拓扑，解决延迟与可用性问题；但**仍然保持 status red**，开始处理积压 | "Once the replicas were in sync, we conducted a failover to the original topology... As part of a conscious decision to prioritize data integrity over a shorter incident window, we kept the service status red while we began processing the backlog" |
| C13 | 16:45 | 积压规模：**超过 500 万个 hook 事件**、**8 万次 Pages 构建** | "There were over five million hook events and 80 thousand Pages builds queued." |
| C14 | 16:45 后 | 重新处理时，**约 20 万个 webhook 载荷**因超过内部 TTL 被丢弃；发现后暂停处理并上调 TTL | "we processed ~200,000 webhook payloads that had outlived an internal TTL and were dropped. Upon discovering this, we paused that processing and pushed a change to increase that TTL" |
| C15 | 23:03 | 全部积压处理完毕，系统完整性确认，状态转 **green** | "All pending webhooks and Pages builds had been processed and the integrity and proper operation of all systems had been confirmed. The site status was updated to green." |

## D. 那个决定（本关卡决策点的核心）

| # | 陈述 | S1 原文依据 |
|---|---|---|
| D1 | 团队判断：美西已写入 **30 多分钟**的数据，使他们**没有别的选择**，只能"向前修复"（fail forward）以保住用户数据 | "we decided that the 30+ minutes of data written to the US West Coast data center prevented us from considering options other than failing-forward in order to keep user data safe." |
| D2 | **代价很明确**：跑在美东、却要写美西 MySQL 的应用，**扛不住跨洲往返延迟**，这个决定会让服务对很多用户不可用 | "applications running in the East Coast that depend on writing information to a West Coast MySQL cluster are currently unable to cope with the additional latency introduced by a cross-country round trip for the majority of their database calls. This decision would result in our service being unusable for many users." |
| D3 | **明确表态**：「我们认为，为了确保用户数据的一致性，长时间的服务降级是值得的。」 | "We believe that the extended degradation of service was worth ensuring the consistency of our users' data." |
| D4 | 战略一句话：**优先保数据完整性，牺牲站点可用性与恢复速度** | "our strategy was to prioritize data integrity over site usability and time to recovery." |
| D5 | 结果：**没有用户数据丢失**；但仍有"几秒钟的数据库写入"需要人工对账，复盘发布时仍在进行 | "Ultimately, no user data was lost; however manual reconciliation for a few seconds of database writes is still in progress." |

## E. 为什么恢复这么久

| # | 陈述 | S1 原文依据 |
|---|---|---|
| E1 | MySQL 备份**每 4 小时**做一次、保留多年，但**存在异地公有云对象存储**上 | "While MySQL data backups occur every four hours and are retained for many years, the backups are stored remotely in a public cloud blob storage service." |
| E2 | 恢复数 TB 备份**要花数小时**，其中相当一部分时间耗在**从异地备份服务传输数据**；解压、校验、准备、加载到新机器占了大头 | "The time required to restore multiple terabytes of backup data caused the process to take hours. A significant portion of the time was consumed transferring the data from the remote backup service. The process to decompress, checksum, prepare, and load large backup files onto newly provisioned MySQL servers took the majority of time." |
| E3 | **关键细节**：这套恢复流程**至少每天演练一次**，恢复时长是清楚的；但**在这次事故之前，他们从来没有真的需要从备份完整重建整个集群**——以往都能靠延迟副本等手段解决 | "This procedure is tested daily at minimum, so the recovery time frame was well understood, however until this incident we have never needed to fully rebuild an entire cluster from backup and had instead been able to rely on other strategies such as delayed replicas." |
| E4 | 复制追赶的实际曲线**不是线性而是幂衰减**；加上欧美用户陆续上班带来写负载上升，恢复比原估计更久——他们据线性外推给出的"两小时"预期因此落空 | "In reality, the time required for replication to catch up had adhered to a power decay function instead of a linear trajectory. Due to increased write load on our database clusters as users woke up and began their workday in Europe and the US, the recovery process took longer than originally estimated." |
| E5 | 沟通反思：他们基于积压处理速率做过几次公开的修复时间估计，**事后承认估计没有考虑到全部变量**并致歉 | "we made several public estimates on time to repair based on the rate of processing of the backlog of data. In retrospect, our estimates did not factor in all variables. We are sorry for the confusion this caused" |
| E6 | 另一个沟通困境：**GitHub 内部就用 GitHub Pages**，构建已暂停数小时，所以 07:46 UTC 那篇说明**发出来本身就费了额外功夫** | "We use GitHub Pages internally and all builds had been paused several hours earlier, so publishing this took additional effort. We apologize for the delay." |

## F. 事后改进（复盘与"带回秒抢"用）

| # | 陈述 | S1 原文依据 |
|---|---|---|
| F1 | 调整 Orchestrator 配置，**禁止跨区域提升主库**。S1 强调：**Orchestrator 的行为完全符合它的配置**，问题在应用层撑不住这个拓扑变更；区域内选主一般是安全的，**突然引入的跨洲延迟才是主要成因** | "Adjust the configuration of Orchestrator to prevent the promotion of database primaries across regional boundaries. Orchestrator's actions behaved as configured, despite our application tier being unable to support this topology change. Leader-election within a region is generally safe, but the sudden introduction of cross-country latency was a major contributing factor" |
| F2 | 这是**系统的涌现行为**——因为他们此前从未见过这种量级的内部网络分区 | "This was emergent behavior of the system given that we hadn't previously seen an internal network partition of this magnitude." |
| F3 | 加快状态播报机制改造：当时只有 green / yellow / red 三档，无法反映"哪些部分还好用" | "we were only able to set our status to green, yellow, and red. We recognize that this doesn't give you an accurate picture of what is working and what is not" |
| F4 | 事故前几周已启动全公司工程计划，目标是 **active/active/active** 多数据中心、设施级 **N+1** 冗余，容忍单数据中心完全失效；本次事故**让这件事更紧迫** | "we had started a company-wide engineering initiative to support serving GitHub traffic from multiple data centers in an active/active/active design. This project has the goal of supporting N+1 redundancy at the facility level... This incident has added urgency to the initiative." |
| F5 | **组织层面的结论**：更严的运维管控或更快的响应，**不足以**保障这种复杂系统的可靠性；他们将系统性地**在故障影响用户之前主动验证失效场景**，并投入**故障注入与混沌工程**工具 | "We have learned that tighter operational controls or improved response times are insufficient safeguards for site reliability within a system of services as complicated as ours... we will also begin a systemic practice of validating failure scenarios before they have a chance to affect you. This work will involve future investment in fault injection and chaos engineering tooling at GitHub." |

> **F5 是全书结构上的关键一句**：它把关卡四直接接到**第 16 章混沌工程**。
> 页面的「带回秒抢」段必须写明这条引线。

## G. 页面红线复核

- [ ] 数字带「约」：约 40 分钟、约 20 万个 webhook、超过 500 万 hook 事件、8 万次 Pages 构建。
      S1 精确给出的 43 秒、24 小时 11 分、954 次写入、每 4 小时备份、各 UTC 时刻可直书
- [ ] **不虚构任何人物台词**（S1 署名 Jason Warner，页面可引用其**已发表**文字，但不得编造对白）
- [ ] 不指名批评任何个人；F1 明确 Orchestrator "behaved as configured"，不得写成工具有 bug
- [ ] 必须写出 D3/D4 的取舍表态原意：**长时间降级是主动选择，不是能力不足**
- [ ] 页头 `.disclaimer`、页末 `.sources` 就位，事实句挂 `[S1]`
