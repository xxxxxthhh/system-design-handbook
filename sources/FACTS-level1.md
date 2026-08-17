# FACTS-level1.md · GitLab 2017-01-31 数据库误删事故 · 逐句核对清单

> QUALITY.md 第二节协议。**level1.html 里的每一个事实性陈述都必须能在本表找到行号。**
> 表外的任何"事实"一律不许写进页面。氛围与心理描写属于改编，须在页头声明覆盖范围内。

## 来源

| 代号 | 文档 | URL | 本地留档 |
|---|---|---|---|
| S1 | GitLab 官方复盘 *Postmortem of database outage of January 31* | https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/ | `sources/raw/gitlab-2017-postmortem.txt` |
| S2 | GitLab 事发当日说明 *GitLab.com Database Incident*（2017-02-01） | https://about.gitlab.com/blog/gitlab-dot-com-database-incident | 引用其存在，事实一律以 S1 为准 |

**二手文章一律不作为事实依据。**

---

## ⚠️ 骨架修正（必须执行）

SKELETON.md 写「五层备份逐层揭牌**全部失效**」。**这与 S1 不符，页面不得这样写。**

S1 的事实是：**四层失效，第五层活了**——救回 GitLab 的是一位工程师在事发前约 6 小时
为了做负载测试**临时手动**打的一个 LVM 快照，它根本不属于灾备体系。
正确的教学结论比原来的更锋利：**「救命的不是备份制度，是一次为了别的目的的临时起意。」**
页面按此改写。

---

## A. 时间线（UTC，2017-01-31）

| # | 陈述（页面可用） | S1 原文依据 |
|---|---|---|
| A1 | 一名工程师当天在预发环境搭多台 PostgreSQL，想试 pgpool-II 做读负载均衡 | "an engineer started setting up multiple PostgreSQL servers in our staging environment. The plan was to try out pgpool-II" |
| A2 | 约 17:20，他为此**手动**打了一个生产库 LVM 快照灌进预发；这个动作平时每 24 小时（01:00 UTC）自动做一次，他只是想要更新的副本 | "± 17:20 UTC: prior to starting this work, our engineer took an LVM snapshot of the production database... This procedure normally happens automatically once every 24 hours (at 01:00 UTC), but they wanted a more up to date copy" |
| A3 | 约 19:00，数据库负载升高，**疑似垃圾内容（spam）**所致；压住负载花了几个小时 | "± 19:00 UTC: GitLab.com starts experiencing an increase in database load due to what we suspect was spam... Getting the load under control took several hours." |
| A4 | 后来查明，部分负载来自一个后台任务在删除**一名 GitLab 员工及其关联数据**——该账号被人恶意举报为滥用，被误安排删除 | "part of the load was caused by a background job trying to remove a GitLab employee and their associated data. This was the result of their account being flagged for abuse and accidentally scheduled for removal." / "The employee was reported for abuse by a troll." |
| A5 | 约 23:00，负载导致从库复制开始落后；因主库已删除从库还需要的 WAL 段、且**未开启 WAL 归档**，复制失败，只能手工重建从库 | "± 23:00 UTC: ...replication process started to lag behind. The replication failed as WAL segments needed by the secondary were already removed from the primary. As GitLab.com was not using WAL archiving, the secondary had to be re-synchronised manually" |
| A6 | 重建从库的步骤是：清空从库数据目录，再跑 `pg_basebackup` | "This involves removing the existing data directory on the secondary, and running pg_basebackup" |
| A7 | `pg_basebackup` 挂住不动，即使加了 `--verbose` 也没有任何有意义输出 | "pg_basebackup would hang, producing no meaningful output, despite the --verbose option being set" |
| A8 | 报错显示主库可用复制连接不够；工程师把 `max_wal_senders` 从默认 **3** 临时改到 **32** | "the master not having enough available replication connections (as controlled by the max_wal_senders option)... decided to temporarily increase max_wal_senders from the default value of 3 to 32" |
| A9 | 改完 PostgreSQL 拒绝启动，报信号量过多；原因是 `max_connections` 被设成 **8000**（一年前设的，此前一直正常）；调到 **2000** 后正常启动 | "PostgreSQL refused to restart, claiming too many semaphores were being created... In our case this was set to 8000... it had been applied almost a year ago and was working fine until that point. To resolve this the setting's value was reduced to 2000" |
| A10 | 问题仍未解决；用 `strace` 看到卡在 `poll` 调用，但看不出原因 | "strace showed that pg_basebackup was hanging in a poll call, but that did not provide any other meaningful information" |
| A11 | **后来才知道，这个"卡住"是正常行为**：`pg_basebackup` 会静静等待主库开始发送复制数据。当时的内部 runbook 和官方文档都没写清楚 | "this is normal behaviour: pg_basebackup will wait for the primary to start sending over replication data and it will sit and wait silently until that time. Unfortunately this was not clearly documented in our engineering runbooks nor in the official pg_basebackup document." |
| A12 | 约 23:30，工程师为恢复复制去清空 PostgreSQL 数据目录，**误以为自己在从库上操作，实际执行在主库上** | "an engineer proceeds to wipe the PostgreSQL database directory, errantly thinking they were doing so on the secondary. Unfortunately this process was executed on the primary instead." |
| A13 | 他在发现后一两秒就终止了进程，但此时**约 300 GB** 数据已被删除 | "The engineer terminated the process a second or two after noticing their mistake, but at this point around 300 GB of data had already been removed." |

> 主库主机名 `db1.cluster.gitlab.com`，从库 `db2.cluster.gitlab.com`；当时是**单主 + 单热备**，
> 热备只用于 failover。（S1 "Database setup" 段）

## B. 五层揭牌（页面的核心桥段）

| # | 层 | 结果 | S1 原文依据 |
|---|---|---|---|
| B1 | **复制（从库）** | ❌ 失效。主从两侧数据都已被清空，无从恢复 | "At this point the replication process was broken and data had already been wiped from both the primary and secondary, meaning we could not restore from either host." 另注：S1 明确复制"primarily used for failover purposes and **not** for disaster recovery" |
| B2 | **`pg_dump` 每日备份 → S3** | ❌ 失效。**S3 桶是空的** | "When we went to look for the pg_dump backups we found out they were not there. The S3 bucket was empty" |
| B2a | 失效原因：备份用 `pg_dump` **9.2**，而数据库跑 PostgreSQL **9.6**，大版本不匹配导致 `pg_dump` 直接报错退出 | "the backup procedure was using pg_dump 9.2, while our database is running PostgreSQL 9.6... A difference in major versions results in pg_dump producing an error, terminating the backup procedure." |
| B2b | 根因：备份跑在**普通应用服务器**上，那里没有 PostgreSQL 数据目录，Omnibus 因此回退到 9.2 | "The pg_dump procedure was executed on a regular application server, not the database server. As a result there is no PostgreSQL data directory present on these servers, thus Omnibus defaults to PostgreSQL 9.2." |
| B2c | **失败通知也失效**：cron 报错走邮件，但 cron 邮件没配 DMARC，被收件方拒收——「我们从来不知道备份在失败，直到为时已晚」 | "these notifications are sent by email... DMARC was not enabled for the cronjob emails, resulting in them being rejected by the receiver. This means we were never aware of the backups failing, until it was too late." |
| B3 | **Azure 磁盘快照** | ❌ 失效。给 NFS 服务器开了，**没给数据库服务器开**——因为「我们假设其它备份手段已经够了」 | "While enabled for the NFS servers, these snapshots were not enabled for any of the database servers as we assumed that our other backup procedures were sufficient enough." |
| B3a | 且跨存储账户恢复极慢，曾有一次恢复花了**一周以上** | "when using a host in a different storage account the procedure can take hours if not days to complete. For example, in one such case it took over a week to restore a snapshot." |
| B4 | **每日自动 LVM 快照** | ⚠️ 存在，但是**事发前将近 24 小时**的——用它意味着丢近 24 小时数据 | "A snapshot created for our staging environment every 24 hours, almost 24 hours before the outage happened." |
| B5 | **A2 那个手动 LVM 快照** | ✅ **唯一活口**。事发前约 **6 小时**，为做负载测试临时打的 | "A snapshot created manually by one of the engineers roughly 6 hours before the outage." + "we decided to use the LVM snapshot created 6 hours before the outage, as it was our only option to reduce data loss as much as possible (the alternative was to lose almost 24 hours of data)" |

> **注意**：LVM 快照的用途是把生产数据拷到预发，S1 明说它们 "are not really meant to be used for disaster recovery"。

## C. 恢复过程

| # | 陈述 | S1 原文依据 |
|---|---|---|
| C1 | 从预发主机把数据拷回生产花了**约 18 小时**；磁盘是网络盘且被限速到**约 60Mbps**，瓶颈在磁盘不在网络或 CPU | "Copying the data from the staging to the production host took around 18 hours. These disks are network disks and are throttled to a really low number (around 60Mbps)... the bottleneck was in the drives." |
| C2 | 预发用的是 Azure classic、没上 Premium Storage，为省成本——这直接决定了恢复速度 | "For our staging environment we were using Azure classic, without Premium Storage. This is primarily done to save costs... As a result the disks are very slow, resulting in them being the main bottleneck in the restoration process." |
| C3 | 恢复到的状态是 1 月 31 日 **17:20 UTC** | "we were able to restore the database (including webhooks) to the state it was at January 31st, 17:20 UTC" |
| C4 | 2 月 1 日 **17:00 UTC** 恢复了不含 webhooks 的数据库；约 **18:00 UTC** 完成 webhooks 恢复等收尾 | "On February 1st at 17:00 UTC we managed to restore the GitLab.com database without webhooks... Around 18:00 UTC we finished the final restoration procedures" |
| C5 | 恢复流程中把所有数据库序列**加了 100,000**，防止复用事故前可能已用过的 ID | "Increment all database sequences by 100,000 so one can't re-use IDs that might have been used before the outage." |

## D. 损失

| # | 陈述 | S1 原文依据 |
|---|---|---|
| D1 | GitLab.com **宕机约 18 小时** | "Problem 1: GitLab.com was down for about 18 hours." |
| D2 | 丢失的是 1 月 31 日 **17:20 到 00:00 UTC** 之间对数据库数据的修改（项目、评论、用户账号、issue、代码片段等） | "we lost modifications to database data such as projects, comments, user accounts, issues and snippets, that took place between 17:20 and 00:00 UTC on January 31" |
| D3 | 估计影响**约 5,000 个项目、约 5,000 条评论、约 700 个新用户账号**（页面必须带"约"） | "Our best estimate is that it affected roughly 5,000 projects, 5,000 comments and 700 new user accounts." |
| D4 | **Git 仓库与 wiki 没有丢**（它们单独存储），但在宕机期间不可用 | "Code repositories or wikis hosted on GitLab.com were unavailable during the outage, but were not affected by the data loss." / "Git repositories and Wikis were not removed as they are stored separately." |
| D5 | 自建（self-managed）实例与 GitHost 客户不受影响 | "GitLab Enterprise customers, GitHost customers, and self-managed GitLab CE users were not affected" |

## E. 对外沟通（教学重点之一）

| # | 陈述 | S1 原文依据 |
|---|---|---|
| E1 | 进度记录在一份**公开可见的 Google 文档**里 | "we kept track of progress and notes in a publicly visible Google document" |
| E2 | 恢复过程在 **YouTube 直播**，峰值约 **5000** 人观看，一度是 YouTube 全站第 2 的直播 | "We also streamed the recovery procedure on YouTube, with a peak viewer count of around 5000 (resulting in the stream being the #2 live stream on YouTube for several hours)" |
| E3 | 同时用 Twitter 账号 @gitlabstatus 通报 | "Finally we used Twitter (https://twitter.com/gitlabstatus) to inform those that might not be watching the stream." |
| E4 | 那份文档最初含误删工程师的名字（**是他本人加的，他本人不介意公开**）；GitLab 表示今后会打码，因为别的工程师未必愿意 | "The document in question was initially private to GitLab employees and contained name of the engineer who accidentally removed the data. While the name was added by the engineer themselves (and they had no problem with this being public), we will redact names in future cases" |
| E5 | CEO 在复盘中公开道歉：「丢失生产数据是不可接受的。」 | "Losing production data is unacceptable." / "I apologize personally, as GitLab's CEO, and on behalf of everyone at GitLab." |

> **E4 的处理**：页面**不写**任何工程师姓名（QUALITY.md 二.6 不指名批评）。
> E4 只作为「对外透明的边界在哪里」的教学素材，用第三人称概括。

## F. 决策点素材（三处"本可以刹车"）

页面的三个决策点必须建立在上表事实上，**选项本身是教学设计，不是事实断言**：

1. **约 19:00** —— 负载异常，且部分负载来自一个删除员工数据的后台任务（A3/A4）。
   刹车点：危险的批量删除任务该不该有速率限制与二次确认。
2. **约 23:00–23:30** —— 已连续处理故障数小时，`pg_basebackup` 反复失败且无输出（A5–A11）。
   刹车点：深夜疲劳 + 工具静默 = 该换人还是该继续。
3. **约 23:30 执行删除的那一刻**（A12）。刹车点：终端里有没有东西告诉你"你在主库上"。
4. （复盘用，不做决策点）备份从未演练——刹车点在事故前几个月（B2/B2c/B3）。

## G. 页面红线复核

- [ ] 所有数字带「约」，除 A8/A9 的配置值（3 / 32 / 8000 / 2000）与 D3 的官方估计值
      （D3 官方原文即用 roughly，页面照写「约」）
- [ ] 不出现任何真实人物姓名，不给真实人物编造台词
- [ ] 不写「五层备份全部失效」，按上文 ⚠️ 改写
- [ ] 页头 `.disclaimer` 声明就位
- [ ] 页末 `.sources` 列出 S1（与 S2），正文事实句挂 `[S1]` 角标
