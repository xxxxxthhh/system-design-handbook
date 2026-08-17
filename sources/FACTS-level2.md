# FACTS-level2.md · AWS S3 US-EAST-1 2017-02-28 · 逐句核对清单

> QUALITY.md 第二节协议。level2.html 的每个事实性陈述都必须能在本表找到行号。

## 来源

| 代号 | 文档 | URL | 本地留档 |
|---|---|---|---|
| S1 | AWS 官方 *Summary of the Amazon S3 Service Disruption in the Northern Virginia (US-EAST-1) Region* | https://aws.amazon.com/message/41926/ | `sources/raw/aws-s3-2017-summary.txt` |

**只有 S1。** 关于"半个互联网瘫痪"的坊间说法，S1 未作此表述——页面只能写 S1 列举的受影响服务，
不得引用未核实的第三方影响面统计。

---

## ⚠️ 骨架措辞修正

SKELETON.md 写「连 AWS 状态页自己的图标都加载不出」。S1 的原文说的是
**SHD 管理控制台依赖 S3，导致无法更新各服务状态**，并未提到"图标加载不出"。
页面按 S1 写：**「状态页更新不了，因为它自己也建在 S3 上」**（依赖自举问题），
不写图标细节。

---

## A. 起因

| # | 陈述 | S1 原文依据 |
|---|---|---|
| A1 | 时间：**2017 年 2 月 28 日上午**，北弗吉尼亚（US-EAST-1）区域 | "the service disruption that occurred in the Northern Virginia (US-EAST-1) Region on the morning of February 28th, 2017" |
| A2 | 背景：S3 团队正在排查一个**计费系统变慢**的问题 | "The Amazon Simple Storage Service (S3) team was debugging an issue causing the S3 billing system to progress more slowly than expected." |
| A3 | **9:37AM PST**，一位**获授权的** S3 团队成员**按既有操作手册**执行了一条命令，目的是下线计费流程所用的某个 S3 子系统的**少量**服务器 | "At 9:37AM PST, an authorized S3 team member using an established playbook executed a command which was intended to remove a small number of servers for one of the S3 subsystems that is used by the S3 billing process." |
| A4 | 命令的**一个输入参数填错了**，结果移除的服务器**比预期多得多** | "one of the inputs to the command was entered incorrectly and a larger set of servers was removed than intended" |

> **教学要点（S1 支持）**：这不是越权、不是没走流程、不是没有手册——
> A3 三个限定词（authorized / established playbook / intended small number）全部成立，事故照样发生。

## B. 连锁反应

| # | 陈述 | S1 原文依据 |
|---|---|---|
| B1 | 被误删的服务器**同时**支撑着另外两个 S3 子系统 | "The servers that were inadvertently removed supported two other S3 subsystems." |
| B2 | **index 子系统**：管理该区域内**所有 S3 对象**的元数据与位置信息；GET / LIST / PUT / DELETE **全部**依赖它 | "the index subsystem, manages the metadata and location information of all S3 objects in the region. This subsystem is necessary to serve all GET, LIST, PUT, and DELETE requests." |
| B3 | **placement 子系统**：管理新存储的分配，**依赖 index 子系统正常工作**；PUT 请求要用它给新对象分配存储 | "the placement subsystem, manages allocation of new storage and requires the index subsystem to be functioning properly to correctly operate. The placement subsystem is used during PUT requests to allocate storage for new objects." |
| B4 | 移除了相当大比例的容量，导致这两个子系统**都必须完整重启**；重启期间 S3 无法服务请求 | "Removing a significant portion of the capacity caused each of these systems to require a full restart. While these subsystems were being restarted, S3 was unable to service requests." |
| B5 | 同区域内依赖 S3 存储的其它 AWS 服务同样受影响，S1 点名：**S3 console、EC2 新实例启动、EBS 卷（当需要从 S3 快照取数据时）、AWS Lambda** | "Other AWS services in the US-EAST-1 Region that rely on S3 for storage, including the S3 console, Amazon Elastic Compute Cloud (EC2) new instance launches, Amazon Elastic Block Store (EBS) volumes (when data was needed from a S3 snapshot), and AWS Lambda were also impacted" |

## C. 为什么重启这么久（本关卡最重要的教学点）

| # | 陈述 | S1 原文依据 |
|---|---|---|
| C1 | S3 子系统本来就是**按"容量会失效"设计**的，移除并替换容量是核心运维流程之一 | "S3 subsystems are designed to support the removal or failure of significant capacity with little or no customer impact. We build our systems with the assumption that things will occasionally fail, and we rely on the ability to remove and replace capacity as one of our core operational processes." |
| C2 | **但是**：在较大的区域里，index 子系统与 placement 子系统**已经很多年没有被完整重启过** | "we have not completely restarted the index subsystem or the placement subsystem in our larger regions for many years" |
| C3 | S3 这些年增长巨大，重启这些服务、并跑完校验元数据完整性的安全检查，**比预期花的时间长** | "S3 has experienced massive growth over the last several years and the process of restarting these services and running the necessary safety checks to validate the integrity of the metadata took longer than expected." |

## D. 恢复时间线（PST）

| # | 时刻 | 陈述 | S1 原文依据 |
|---|---|---|---|
| D1 | 12:26PM | index 子系统恢复了足够容量，开始服务 **GET / LIST / DELETE** | "By 12:26PM PST, the index subsystem had activated enough capacity to begin servicing S3 GET, LIST, and DELETE requests." |
| D2 | 1:18PM | index 子系统**完全恢复**，GET / LIST / DELETE API 正常 | "By 1:18PM PST, the index subsystem was fully recovered and GET, LIST, and DELETE APIs were functioning normally." |
| D3 | 1:54PM | placement 子系统恢复完成（它要等 index 可用才能开始恢复）；此时 S3 恢复正常 | "The placement subsystem began recovery when the index subsystem was functional and finished recovery at 1:54PM PST. At this point, S3 was operating normally." |
| D4 | — | 部分受影响的其它服务在 S3 中断期间**积压了工作**，需要额外时间才完全恢复 | "Some of these services had accumulated a backlog of work during the S3 disruption and required additional time to fully recover." |

> 从 9:37AM 到 1:54PM 约 **4 小时 17 分**。页面写「约四个多小时」。

## E. 状态页的依赖自举问题

| # | 陈述 | S1 原文依据 |
|---|---|---|
| E1 | 从事件开始直到 **11:37AM PST**，AWS **无法在 Service Health Dashboard (SHD) 上更新各服务状态**，因为 **SHD 管理控制台依赖 S3** | "From the beginning of this event until 11:37AM PST, we were unable to update the individual services' status on the AWS Service Health Dashboard (SHD) because of a dependency the SHD administration console has on Amazon S3." |
| E2 | 期间改用 **@AWSCloud 推特**和 SHD 顶部横幅文字通报 | "Instead, we used the AWS Twitter feed (@AWSCloud) and SHD banner text to communicate status" |
| E3 | 事后把 SHD 管理控制台改成**跨多个 AWS 区域**运行 | "we have changed the SHD administration console to run across multiple AWS regions." |

## F. 护栏改进（决策点素材）

| # | 陈述 | S1 原文依据 |
|---|---|---|
| F1 | AWS 的判断：移除容量是关键运维实践，但这次**工具允许移除的容量太多、太快** | "While removal of capacity is a key operational practice, in this instance, the tool used allowed too much capacity to be removed too quickly." |
| F2 | 改进一：**降低移除速率** | "We have modified this tool to remove capacity more slowly" |
| F3 | 改进二：**最小容量护栏**——当移除会让任一子系统低于其最小所需容量时，禁止移除 | "added safeguards to prevent capacity from being removed when it will take any subsystem below its minimum required capacity level. This will prevent an incorrect input from triggering a similar event in the future." |
| F4 | 改进三：**审计其它运维工具**是否有同类安全检查 | "We are also auditing our other operational tools to ensure we have similar safety checks." |
| F5 | 改进四：继续把服务拆成更小的 **cell**（分区）以**缩小爆炸半径**、改善恢复时间；index 子系统本已计划年内进一步分区，事后**提前立即启动** | "breaking services into small partitions which we call cells. By factoring services into cells... to reduce blast radius and improve recovery... The S3 team had planned further partitioning of the index subsystem later this year. We are reprioritizing that work to begin immediately." |

> **注意 F2/F3 的教学价值**：AWS 的修复**不是**"让人别输错"，而是**让工具在输错时也不至于致命**。
> 这正是决策点要逼读者体会的取舍：护栏会让日常运维变慢，代价该不该付。

## G. 页面红线复核

- [ ] 数字带「约」，除 S1 给出的精确时刻（9:37AM / 11:37AM / 12:26PM / 1:18PM / 1:54PM PST）
- [ ] **不写**"半个互联网瘫痪"这类 S1 未支持的影响面表述；只写 B5 点名的服务
- [ ] **不写**"状态页图标加载不出"，按 E1 写依赖自举
- [ ] 不指名批评那位操作人员——S1 本身强调其 authorized、按 playbook 操作
- [ ] 页头 `.disclaimer`、页末 `.sources` 就位，事实句挂 `[S1]`
