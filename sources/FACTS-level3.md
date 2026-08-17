# FACTS-level3.md · Knight Capital 2012-08-01 四十五分钟 · 逐句核对清单

> QUALITY.md 第二节协议。level3.html 的每个事实性陈述都必须能在本表找到行号。

## 来源

| 代号 | 文档 | URL | 本地留档 |
|---|---|---|---|
| S1 | 美国证券交易委员会（SEC）行政令 *In the Matter of Knight Capital Americas LLC*，Securities Exchange Act Release No. **70694**，2013-10-16，File No. 3-15570 | https://www.sec.gov/litigation/admin/2013/34-70694.pdf | `sources/raw/sec-34-70694-knight-capital.txt` |

**只有 S1。** 坊间关于本事故的技术细节（如"部署脚本"、"运维手滑"等具体说法）多为二手推测，
S1 未支持的一律不写。

> **法律语境须写明**：Knight 提交了和解要约，**在不承认也不否认**这些认定的前提下同意该行政令
> （S1 §II："without admitting or denying the findings herein"）。页面在来源清单里注明这一点。

---

## A. 事故规模（引子用）

| # | 陈述 | S1 原文依据 |
|---|---|---|
| A1 | 时间：**2012 年 8 月 1 日** | "On August 1, 2012, Knight Capital Americas LLC ('Knight') experienced a significant error..." (§1) |
| A2 | 出问题的是 Knight 的自动化股票订单路由系统，代号 **SMARS** | "its automated routing system for equity orders, known as SMARS" (§1) |
| A3 | 在处理**212 笔**来自客户的小额零售订单时，SMARS 在**约 45 分钟内**向市场发出了**数百万笔**订单 | "While processing 212 small retail orders that Knight had received from its customers, SMARS routed millions of orders into the market over a 45-minute period" (§1) |
| A4 | 成交结果：**超过 400 万笔成交**，涉及 **154 只股票**、**超过 3.97 亿股** | "obtained over 4 million executions in 154 stocks for more than 397 million shares" (§1) |
| A5 | 停手时，Knight 在 **80 只**股票上净多头约 **35 亿美元**，在 **74 只**股票上净空头约 **31.5 亿美元** | "a net long position in 80 stocks of approximately $3.5 billion and a net short position in 74 stocks of approximately $3.15 billion" (§1) |
| A6 | 最终损失**超过 4.6 亿美元** | "Knight lost over $460 million from these unwanted positions." (§1) / "Knight realized a $460 million loss on these positions." (§17) |
| A7 | 参照系：2011–2012 年间 Knight 的总交易量约占全美上市股票交易的 **10%**，SMARS 一家约占 **1% 以上** | "Knight's aggregate trading... generally represented approximately ten percent of all trading in listed U.S. equity securities. SMARS generally represented approximately one percent or more" (§11) |

## B. 僵尸代码：Power Peg

| # | 陈述 | S1 原文依据 |
|---|---|---|
| B1 | 起因是为配合 NYSE 的 **Retail Liquidity Program (RLP)** 上线（原定 2012-08-01 启动），Knight 改了订单处理相关代码，包括在 SMARS 里部署新代码 | "To enable its customers' participation in the Retail Liquidity Program ('RLP') at the New York Stock Exchange, which was scheduled to commence on August 1, 2012, Knight made a number of changes... These changes included developing and deploying new software code in SMARS." (§12) |
| B2 | 新 RLP 代码本意是**替换**订单路由器里一段**没在用的旧代码**，那段旧代码属于一个叫 **Power Peg** 的功能 | "the new RLP code in SMARS was intended to replace unused code in the relevant portion of the order router. This unused code previously had been used for functionality called 'Power Peg'" (§13) |
| B3 | Power Peg **多年前就停用了**，但代码**仍然留在服务器上且可被调用** | "Knight had discontinued using [Power Peg] many years earlier. Despite the lack of use, the Power Peg functionality remained present and callable at the time of the RLP deployment." (§13) |
| B4 | **新代码复用了那个原本用来激活 Power Peg 的开关（flag）**。Knight 本打算删掉 Power Peg 代码，这样开关置 "yes" 时激活的就是新 RLP 功能 | "The new RLP code also repurposed a flag that was formerly used to activate the Power Peg code. Knight intended to delete the Power Peg code so that when this flag was set to 'yes,' the new RLP functionality—rather than Power Peg—would be engaged." (§13) |
| B5 | Power Peg 当年正常工作时，有一个**累计数量函数**统计母单已成交股数，据此在母单成交完毕后**停止**继续拆发子单 | "as child orders were executed, a cumulative quantity function counted the number of shares of the parent order that had been executed. This feature instructed the code to stop routing child orders after the parent order had been filled completely." (§14) |
| B6 | 时间线：**2003 年** Knight 停用 Power Peg；**2005 年** 把这个累计数量函数**挪到了 SMARS 代码序列中更靠前的位置** | "In 2003, Knight ceased using the Power Peg functionality. In 2005, Knight moved the tracking of cumulative shares function in the Power Peg code to an earlier point in the SMARS code sequence." (§14) |
| B7 | **搬完之后，Knight 没有再测试过 Power Peg 代码**，因而不知道它若被调用还能否正确工作 | "Knight did not retest the Power Peg code after moving the cumulative quantity function to determine whether Power Peg would still function correctly if called." (§14) |

> **教学核心（B4 + B6 + B7）**：复用一个旧 feature flag，等于把一段**七年没人测过**的代码
> 重新接上电源。「唤醒亡灵」这个比喻由 S1 事实完全支持。

## C. 部署不一致

| # | 陈述 | S1 原文依据 |
|---|---|---|
| C1 | 从 **2012 年 7 月 27 日**起，新 RLP 代码**分批**部署，连续几天陆续放到 SMARS 的部分服务器上 | "Beginning on July 27, 2012, Knight deployed the new RLP code in SMARS in stages by placing it on a limited number of servers in SMARS on successive days." (§15) |
| C2 | 部署过程中，一名技术人员**漏了 8 台 SMARS 服务器中的 1 台**，没把新代码拷过去 | "one of Knight's technicians did not copy the new code to one of the eight SMARS computer servers." (§15) |
| C3 | Knight **没有安排第二名技术人员复核**这次部署，**也没有任何人**发现第八台服务器上 Power Peg 代码没被删、新 RLP 代码没被加 | "Knight did not have a second technician review this deployment and no one at Knight realized that the Power Peg code had not been removed from the eighth server, nor the new RLP code added." (§15) |
| C4 | Knight **没有书面规程**要求做这种复核 | "Knight had no written procedures that required such a review." (§15) |
| C5 | 8 月 1 日，**七台**装了新代码的服务器处理正确；带着那个被复用开关的订单一到**第八台**，就触发了残留的 Power Peg 代码 | "The seven servers that received the new code processed these orders correctly. However, orders sent with the repurposed flag to the eighth server triggered the defective Power Peg code still present on that server." (§16) |
| C6 | 因为累计数量函数已被搬走，这台服务器对每一笔进来的母单，**不管已经成交了多少**，都持续快速地发出子单 | "Because the cumulative quantity function had been moved, this server continuously sent child orders, in rapid sequence, for each incoming parent order without regard to the number of share executions Knight had already received" (§16) |
| C7 | Knight 系统里**另有一部分**已经知道母单成交完毕了，但**这个信息没有传给 SMARS** | "Although one part of Knight's order handling system recognized that the parent orders had been filled, this information was not communicated to SMARS." (§16) |

## D. 开市前的 97 封警报（最刺痛的一段）

| # | 陈述 | S1 原文依据 |
|---|---|---|
| D1 | 8 月 1 日约 **8:01 a.m. ET** 起，Knight 内部系统开始自动生成邮件（称 **"BNET rejects"**），内容引用 SMARS 并标明错误 **"Power Peg disabled"** | "beginning at approximately 8:01 a.m. ET, an internal system at Knight generated automated e-mail messages (called 'BNET rejects') that referenced SMARS and identified an error described as 'Power Peg disabled.'" (§19) |
| D2 | 在 **9:30 a.m. 开市前**，系统向一组 Knight 人员发出了 **97 封**这样的邮件 | "Knight's system sent 97 of these e-mail messages to a group of Knight personnel before the 9:30 a.m. market open." (§19) |
| D3 | 但 Knight **并未把这类邮件设计成系统告警**，相关人员**一般也不看** | "Knight did not design these types of messages to be system alerts, and Knight personnel generally did not review them when they were received." (§19) |
| D5（推导） | 页面写「97 封邮件，**89 分钟**」——89 分钟由 D1 与 D2 两个已核实时刻相减得到，不是原文给出的数字 | 8:01 a.m. ET（D1）→ 9:30 a.m. 开市（D2），相隔 89 分钟 |
| D4 | SEC 明确指出：这些消息是**实时发出**的、**正是由部署失误引起**的，本可提供在开市前发现并修复问题的机会——但**开市前无人处理，开市后也没被用于诊断** | "these messages were sent in real time, were caused by the code deployment failure, and provided Knight with a potential opportunity to identify and fix the coding issue prior to the market open. These notifications were not acted upon before the market opened and were not used to diagnose the problem after the open." (§19) |

## E. 那 45 分钟里发生了什么（决策点素材）

| # | 陈述 | S1 原文依据 |
|---|---|---|
| E1 | Knight **没有任何关于事件响应的监督规程**，在重大问题发生时没有东西指导相关人员该怎么做 | "On August 1, Knight did not have supervisory procedures concerning incident response. More specifically, Knight did not have supervisory procedures to guide its relevant personnel when significant issues developed." (§27) |
| E2 | Knight 主要靠技术团队**在实盘交易环境里**边跑边查 SMARS 的问题；**期间系统持续发出数百万笔子单** | "Knight relied primarily on its technology team to attempt to identify and address the SMARS problem in a live trading environment. Knight's system continued to send millions of child orders while its personnel attempted to identify the source of the problem." (§27) |
| E3 | **关键的一步**：为了解决问题，Knight **把已正确部署的那七台服务器上的新 RLP 代码卸载了**。**这让情况更糟**——更多进来的母单开始在那七台上也激活 Power Peg 代码，重演第八台已经发生的事 | "In one of its attempts to address the problem, Knight uninstalled the new RLP code from the seven servers where it had been deployed correctly. This action worsened the problem, causing additional incoming parent orders to activate the Power Peg code that was present on those servers, similar to what had already occurred on the eighth server." (§27) |
| E4 | 技术人员排障期间，Knight **一直连着市场并继续在部分证券上发单** | "While Knight's technology staff worked to identify and resolve the issue, Knight remained connected to the markets and continued to send orders in certain listed securities." (§10) |

> **决策点设计（SKELETON：先停系统还是先查原因）**：E2 + E4 表明真实团队**没有先停**；
> E3 表明"回滚"这个直觉动作在部署不一致的前提下**放大了**故障。
> 页面的决策点必须建立在这两条事实上。

## F. 缺失的护栏（教学与决策点素材）

| # | 陈述 | S1 原文依据 |
|---|---|---|
| F1 | Knight 在订单到达 SMARS **之前**有若干控制（客户接口、内部订单管理系统、内部撮合系统都有防错单控制）——**但 SMARS 内部没有** | "Knight had a number of controls in place prior to the point that orders reached SMARS... However, Knight did not have adequate controls in SMARS to prevent the entry of erroneous orders." (§20–21) |
| F2 | 具体缺什么：**没有把 SMARS 的输出与输入做比对**的控制；**没有在系统自身行为异常时叫停 SMARS 的规程** | "Knight did not have sufficient controls to monitor the output from SMARS, such as a control to compare orders leaving SMARS with those that entered it. Knight also did not have procedures in place to halt SMARS's operations in response to its own aberrant activity." (§21) |
| F3 | 有一个价格上限控制（相对全国最优买/卖价 9.5%），但**在最优价变动不足 9.5% 时不起作用**，且**不适用于**开市前收到、准备参与开盘集合竞价的订单——**正是那 212 笔** | "Knight had a control that capped the limit price... at 9.5 percent below the National Best Bid... However, this control would not prevent the entry of erroneous orders in circumstances in which the National Best Bid or Offer moved by less than 9.5 percent. Further, it did not apply to orders—such as the 212 orders described above—that Knight received before the market open" (§21) |
| F4 | **33 号账户**：一个临时持仓账户，被分配了 **200 万美元**的总头寸限额，但**这个限额没有连到任何自动控制** | "Knight assigned a $2 million gross position limit to the 33 Account, but it did not link this account to any automated controls concerning Knight's overall financial exposure." (§23) |
| F5 | 8 月 1 日早晨 33 号账户开始堆积异常巨大的头寸；由于没有连到全公司的资本阈值自动控制，**SMARS 继续发单**，尽管母单其实早已成交完毕 | "the 33 Account began accumulating an unusually large position... Because Knight did not link the 33 Account to pre-set, firm-wide capital thresholds that would prevent the entry of orders, on an automated basis... SMARS continued to send millions of child orders to the market despite the fact that the parent orders already had been completely filled." (§24) |
| F6 | 由于 33 号账户混装多种来源的头寸，Knight 人员**无法快速判断**当天早上堆积的头寸是什么、从哪来 | "because the 33 Account held positions from multiple sources, Knight personnel could not quickly determine the nature or source of the positions" (§24) |
| F7 | 主要风控工具 **PMON** 是**事后（post-execution）**持仓监控系统。开市时高级人员**确实看到**了 33 号账户头寸激增，但 PMON **没有连到下单环节**、**不产生自动告警**、**不显示限额**（看的人得自己知道限额是多少），且在高成交量时**会延迟、报表不准** | "Knight's primary risk monitoring tool, known as 'PMON,' is a post-execution position monitoring system. At the opening of the market, senior Knight personnel observed a large volume of positions accruing in the 33 Account. However, Knight did not link this tool to its entry of orders... PMON relied entirely on human monitoring and did not generate automated alerts... PMON also did not display the limits... PMON experienced delays during high volume events... resulting in reports that were inaccurate." (§25) |
| F8 | 代码开发与部署：Knight **对 SMARS 没有书面的开发与部署规程**（公司其它组有），**不要求第二人复核**部署，也**没有书面规定**在生产服务器上动到未使用代码后必须测试它是否仍能正常工作 | "Knight did not have written code development and deployment procedures for SMARS (although other groups at Knight had written procedures), and Knight did not require a second technician to review code deployment in SMARS. Knight also did not have a written protocol concerning the accessing of unused code on its production servers, such as a protocol requiring the testing of any such code after it had been accessed" (§26) |

## G. 早有预警（复盘用）

| # | 陈述 | S1 原文依据 |
|---|---|---|
| G1 | **2011 年 10 月**，Knight 用测试数据做了一次周末灾备演练；演练结束后，做市台**误把测试数据继续用于生成自动报价**，周一开盘造成**近 750 万美元**损失 | "in October 2011, Knight used test data to perform a weekend disaster recovery test. After the test concluded, Knight's LMM desk mistakenly continued to use the test data to generate automated quotes when trading began that Monday morning. Knight experienced a nearly $7.5 million loss as a result of this event." (§33) |
| G2 | Knight 对此的应对是**几项局部修补**（限制系统只在交易时段运行、收到成交后停止报价、灾备清单加一项检查测试数据）——**但没有广泛地反思自己是否有足够的防错单控制** | "Knight responded to the event by limiting the operation of the system to market hours, changing the control so that this system would stop providing quotes after receiving an execution, and adding an item to a disaster recovery checklist that required a check of the test data. Knight did not broadly consider whether it had sufficient controls to prevent the entry of erroneous orders, regardless of the specific system that sent the orders or the particular reason for that system's error." (§33) |

## H. SEC 的定性（页面结尾"这不是运气问题"用）

SEC 认定 Knight 违反 Exchange Act Rule 15c3-5，其中与本书主题直接相关的是 §9.D：

> "Knight did not have technology governance controls and supervisory procedures sufficient to
> ensure the orderly deployment of new code **or to prevent the activation of code no longer
> intended for use in Knight's current operations but left on its servers that were accessing the
> market**; and Knight did not have controls and supervisory procedures reasonably designed to
> guide employees' responses to significant technological and compliance incidents"

> 这句话本身就是本关卡的三条教训：**部署一致性 / 僵尸代码 / 事件响应规程**。

## I. 页面红线复核

- [ ] 数字带「约」：约 45 分钟、约 400 万笔、约 3.97 亿股、约 35 亿 / 31.5 亿美元、
      超过 4.6 亿美元、约 750 万美元。S1 精确给出的 212 笔、154 只、80 只、74 只、
      8 台 / 7 台 / 1 台、97 封、2003 / 2005 / 2011-10 / 2012-07-27 可直书
- [ ] **不虚构任何人物台词**，不写"某工程师说……"
- [ ] 不指名批评任何个人（S1 通篇也未点名个人）
- [ ] 必须写明 Knight 是在**不承认也不否认**认定的前提下和解的
- [ ] 页头 `.disclaimer`、页末 `.sources` 就位，事实句挂 `[S1]` 与条款号
