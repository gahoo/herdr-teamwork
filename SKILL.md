---
name: herdr-teamwork
description: Multi-agent spec implementation orchestrated via Herdr terminal panes, tabs, and optional Git Worktrees (Planner, Explorer, Dispatcher, Coding, Test, Reviewer Ensemble, Ops, Debugger, RedTeam, E2E). Use when initiating multi-agent spec implementation, parallel feature development, or complex engineering workflows.
---

# Herdr Multi-Agent Teamwork (多 Agent 协同工程规范 v2.0)

本技能通过 Herdr 终端工作区管理工具构建**“前店后厂、控制流两级星型、数据流文件直连”**的多 Agent 物理隔离与协作体系。
遵循 **OpenSpec 活文档标准**、**事件驱动免轮询机制 (`herdr agent prompt --wait`)** 与 **单向异步信箱机制**，实现规划与调度彻底解耦、职责绝对正交与证伪式分形审查。

---

## 1. 核心目录组织哲学与双模式架构 (Asset vs Infrastructure & Dual-Mode)

系统支持 **常规单线模式 (`standard`)** 与 **Worktree 并行模式 (`worktree`)**，由用户在初始化时自由决定并发度（无硬性上限）。严格遵循“业务数据资产”与“运行工具基建”物理隔离：

```text
project-root/                        # 【主工作区 (Main Workspace)】：Planner 与 Explorer 驻留基准目录
├── changes/                         # 第一类业务数据资产 (First-Class Artifacts，纳入版本管理)
│   ├── KANBAN.md                    # 全局大盘总看板 (Planner 独占维护，含占位池 Inbox 与认知队列)
│   └── <id>/                        # 具体特性变更集目录 (如 001-user-auth/)
│       ├── prd.md                   # 业务诉求、痛点与验收标准 (Definition of Done)
│       ├── spec.md                  # 技术契约、架构边界与接口定义 (Living Truth)
│       ├── tasks.md                 # 状态信箱头 + 依赖拓扑与执行阶段卡片 (吸收原 plan.md)
│       ├── review.md                # 审查裁决归档 (含对账单、防御行号举证、双清单与红黄分级)
│       ├── debug.md                 # 法医排错根因诊断与 Fix Spec 报告 (按需产出)
│       ├── security-poc.md          # 红队渗透测试与 PoC 验证报告 (按需产出)
│       └── explore.md               # 复杂历史代码可行性预研简报 (按需产出)
├── .agents/                         # Agent 运行时支撑基建 (Infrastructure Surface)
│   ├── environment.json             # 宿主机器 Harness 画像、并发模式与 15 角色动态配置
│   ├── session.json                 # Herdr 会话状态快照与跨天秒级复活配置
│   └── skills/herdr-teamwork/roles/ # 15 个正交角色的专属契约库
└── .worktrees/                      # 【并行执行隔离区】(仅在 worktree 模式启用，纳入 .gitignore)
    └── <id>/                        # 对应特性的独立 Git Worktree 检出目录 (独立分支 + 独立端口)
        ├── changes -> ../../changes # 🔗 软链接指向主工作区 changes/，实现契约 0 延迟双向共享
        ├── .agents -> ../../.agents # 🔗 软链接指向主工作区 .agents/，共享环境与会话配置
        ├── src/                     # 当前特性隔离修改的业务源码
        └── tests/                   # 当前特性隔离修改的测试代码
```

---

## 2. 变更集核心文档维护准则 (Living Specs & Single Owner Rules)

为防止多 Agent 并发写冲突与“文档债务”，严格执行**单文件唯一维护人（Single Owner）**与**状态拉取信箱（Pull-based Mailbox）**规范：

| 文档路径 | 唯一维护人 (Owner) | 维护策略与核心机制 | 格式范式与历史处理 |
| :--- | :--- | :--- | :--- |
| **`changes/KANBAN.md`** | **`Planner`** | **全局大盘单文件内聚**：<br>严禁私建碎片化 `Inbox.md`，所有新需求与 [🟡 CONSTRUCTIVE] 演进建议第一时间入池占位。 | **需求未启，看板先行**：<br>- 状态流转：`📥 占位池 (Inbox/Backlog)` ➔ `🚀 进行中 (In Progress)` ➔ `🔔 待人类处理 (Pending Human)` ➔ `✅ 已完成 (Done)`。 |
| **`changes/<id>/tasks.md`** | **`Planner`** (建档)<br>**`Dispatcher`** (更新状态) | **异步状态信箱 + 任务切片拓扑**：<br>- `Dispatcher` 严禁主动向 `Planner` 发终端消息打断对话，仅通过更新本文件顶部状态头投递信号。 | **顶部法定状态信箱头**：<br>`> 🔔 **STATUS**: RUNNING \| WAITING_HUMAN_DECISION \| WAITING_HUMAN_ACCEPTANCE`<br>`> 🌐 **PORT**: 3001 \| **BRANCH**: feat/001`<br>- 下方为按依赖排序的 Phase 任务勾选卡 (`[ ]` / `[-]` / `[x]`)。 |
| **`changes/<id>/prd.md`** | **`Planner`** | **就地演进 (In-place)**：需求调整直接在原文修改。 | 文末附 2~3 行简明 `## 变更备忘录 (Changelog)` 记录妥协或调整原因。 |
| **`changes/<id>/spec.md`** | **`Planner`**<br>(可咨询 `Arch`/`Sec`) | **活契约原则 (Living Truth)**：反映当前生效的最新接口与数据结构。 | 原地更新，不留弃用字段，历史交由 Git 追溯；含明确的验收条件编号 (`AC-1`, `AC-2`)。 |
| **`changes/<id>/review.md`** | **`Lead Reviewer`**<br>(Phase 1 可由 `Arch`/`Sec` 写入预审意见) | **单文件权威收敛**：严禁各审查专家私建碎片文件。 | **报纸头条原则 + 四大法定专区**：<br>1. 裁决看板与红黄分级摘要 (`APPROVED` / `CHANGES_REQUESTED`)；<br>2. 【👥 审查团队构成与路由依据】；<br>3. 【🛠️ 工具执行与取证清单】；<br>4. 【🛡️ 契约对账单与核心防线行号举证 (Proof of Defense)】。历史轮次使用 `<details>` 折叠。 |
| **`changes/<id>/debug.md`** | **`Debug Agent`** | **法医溯源与修复契约**：人类验收报障、E2E 崩溃或终审回归失败时产出。 | 最新一轮排障置顶，包含：问题现象、调用链根因定位 (`file:line`)、最小化《Fix Spec》与建议补充的断言。 |
| **`changes/<id>/security-poc.md`** | **`Red Team Lead`** | **攻防演练产物**：高危特性触发，任务结束即销毁窗格。 | 含 STRIDE 威胁类型、CVSS 定级、复现步骤、最小化可运行 PoC 脚本与加固建议。 |
| **`changes/<id>/explore.md`** | **`Explorer`** | **深度代码考古简报**：复杂历史代码摸底时按需产出。 | 浓缩现有相关模块拓扑、技术债约束与演进可行性评估，保护 `Planner` 上下文不被海量源码污染。 |

---

## 3. 角色矩阵与职责正交契约 (15 Orthogonal Role Contracts)

全系统划分为**“前店规划层”**、**“后厂调度与执行层”**与**“分形审查层”**三大正交集群：

| 集群 | 角色 ID (全局统一) | 契约文件 | 核心职责 | 绝对红线 (Hard Boundaries) |
| :--- | :--- | :--- | :--- | :--- |
| **前店<br>规划层** | **`planner`** | [`roles/planner.md`](roles/planner.md) | **产品与架构规划师**：直面人类沟通、维护 `KANBAN.md`、撰写 `prd/spec/tasks`、管理人类认知单工队列、异步点火 `dispatcher`。 | **严禁阻塞等待流水线**；严禁通读海量业务源码（交由 `explorer`）；**严禁越权执行构建、测试、改代码或直接调度后厂工人**。 |
| **前店<br>规划层** | **`explorer`**<br>(按需/即用即销) | [`roles/explorer.md`](roles/explorer.md) | **代码探路与可行性预研员**：深入复杂历史源码库验证用户想法的现实可行性，输出 `explore.md` 简报。 | **严格只读权限**；严禁修改任何代码或契约；完成预研汇报后立即销毁窗格。 |
| **后厂<br>执行层** | **`dispatcher`** | [`roles/dispatcher.md`](roles/dispatcher.md) | **无头流水线状态机调度员**：接管单个 Change，阻塞式依次调度后厂角色、替 `reviewer-lead` 物理切屏拉起专家、执行三步自愈 SOP、更新 `tasks.md` 状态信箱。 | **物理蒙眼：严禁读取 `src/` 与 `tests/` 源码**；**全系统仅允许写 `changes/<id>/tasks.md`**；严禁运行 `npm/tsc/vitest/fallow/gitnexus/kill`；严禁反向唤醒 `planner`。 |
| **后厂<br>执行层** | **`test`** | [`roles/test.md`](roles/test.md) | **测试工程师**：依据 `spec.md`、`debug.md` 或 `security-poc.md` 编写高严谨度失败用例 (Red Test)。 | **严禁修改业务代码 (`src/`)**；严禁为迎合通过而弱化断言或编写同语反复假阳性测试。 |
| **后厂<br>执行层** | **`coding`** | [`roles/coding.md`](roles/coding.md) | **业务代码实现者**：依据 `spec.md` / `debug.md` 编写业务代码，**运行当前关联单测迭代至 Green**，执行 `tsc --noEmit` 与 `gitnexus detect-changes` 自检。 | **严禁修改任何测试文件 (`tests/`)**；严禁私自安装依赖或启停服务（缺依赖输出 `NEED_OPS` 交由 `dispatcher` 调 `ops`）。 |
| **后厂<br>执行层** | **`ops`** | [`roles/ops.md`](roles/ops.md) | **环境与发布守护者**：随叫随到安装依赖、**非阻塞**后台守护服务（支持动态端口绑定）、数据库快照、构建打包、受控 Git 提交/Worktree 合入与刷新图谱/基线。 | **严禁在前台阻塞自身交互主线程**（常驻服务必须后台化或分屏）；严禁修改源码与测试；严禁未经授权提前 commit。 |
| **后厂<br>执行层** | **`debugger`**<br>(按需/即用即销) | [`roles/debugger.md`](roles/debugger.md) | **法医式排错侦探**：在人类验收报障、E2E 崩溃或终审意外回归失败时出马，利用 `gitnexus` 逆向溯源并输出 `changes/<id>/debug.md`。 | **严格只读权限，绝不亲自动手改代码**；严禁倒灌原始调试日志；输出 `debug.md` 后即刻销毁。 |
| **后厂<br>执行层** | **`security-redteam`**<br>(按需/即用即销) | [`roles/security-redteam.md`](roles/security-redteam.md) | **红队渗透测试领队**：STRIDE 威胁建模、白盒污点追踪、隔离沙箱动态渗透，产出 `security-poc.md`。 | **严禁攻击非授权或生产环境**；严禁修改业务代码与标准测试；交付后立即销毁。 |
| **后厂<br>执行层** | **`test-e2e`**<br>(按需/即用即销) | [`roles/test-e2e.md`](roles/test-e2e.md) | **端到端与冒烟测试专家**：双轨制走查（90% 小模型现场冒烟查白屏/Console红字/500错误用完即焚；10% 黄金链路原子 JS 脚本化）。 | **严禁为日常易变切片制造脆弱脚本债务**；单动作自愈 ≤3 次、总步数 ≤15 步刚性熔断；用后即销。 |
| **分形<br>审查层** | **`reviewer-lead`** | [`roles/reviewer-lead.md`](roles/reviewer-lead.md) | **主审统筹与裁决官**：常驻 `review` 左屏；独立执行 **Stage 2A 测试代码快检**；在 **Stage 2B 代码终审**中分诊输出 `SPAWN_EXPERTS` 点将令，回收简报后做 ROI 仲裁并独占签署 `review.md`。 | **严禁亲自运行 `fallow/tsc/vitest/impact/audit`**；严禁亲自敲 `herdr pane` 切屏命令（交由 `dispatcher` 代跑）；严禁无行号举证的无脑 `APPROVED`。 |
| **分形<br>审查层** | **`reviewer-quality`**<br>(按需/即用即销) | [`roles/reviewer-quality.md`](roles/reviewer-quality.md) | **代码健康与回归过滤官**：独占运行并消化 `fallow`、`tsc --noEmit` 与 **全量测试套件回归 (`vitest run`)** 原始日志，输出 ≤15 行健康简报。 | **严禁向主审倒灌原始终端日志**；严禁伪造 `delta: +0` 或回归通过率；只读权限。 |
| **分形<br>审查层** | **`reviewer-arch`**<br>(按需/即用即销) | [`roles/reviewer-arch.md`](roles/reviewer-arch.md) | **系统架构专家**：承接前店 **Stage 1 宏观架构会诊** 与后厂 **Stage 2B 架构终审**；审查深模块设计、单向数据流与 `gitnexus impact` 爆炸半径。 | 必须附带【🛠️ 工具执行与取证清单】及防线行号举证；只读权限。 |
| **分形<br>审查层** | **`reviewer-perf`**<br>(按需/即用即销) | [`roles/reviewer-perf.md`](roles/reviewer-perf.md) | **性能与并发专家**：审查无效重渲染、闭包内存泄漏、N+1 查询、全表扫描与缓存并发安全。 | 必须给出具体瓶颈行号与复杂度推导；只读权限。 |
| **分形<br>审查层** | **`reviewer-security`**<br>(按需/即用即销) | [`roles/reviewer-security.md`](roles/reviewer-security.md) | **蓝队安全合规专家**：承接前店安全预审与后厂安全终审；审查注入防御、RBAC/ABAC 越权、供应链 CVE (`npm audit`)，复核红队 PoC 闭环。 | 对高危漏洞拥有一票否决权；必须附带防御行号举证；只读权限。 |
| **分形<br>审查层** | **`reviewer-ux`**<br>(按需/即用即销) | [`roles/reviewer-ux.md`](roles/reviewer-ux.md) | **交互与无障碍专家**：审查快捷键冲突、输入法容错、焦点陷阱 (Focus Trap)、ARIA 无障碍属性与界面文案。 | 只读权限；完成专项汇报后由 `dispatcher` 销毁分屏。 |

---

## 4. 两阶段审查体系与证伪式分形审查矩阵 (Two-Stage Review & Falsification Protocol)

为彻底根治“带着宏观架构硬伤进入编码”、“Lead Reviewer 偷懒不派活”以及“Reviewer 走过场无脑 Approve（Rubber Stamping）”，建立**两阶段、三拍点将、证伪举证与红黄分级**体系：

### 4.1 两阶段审查全链路划分
1. **🏛️ 第一阶段：计划期宏观与架构预审 (Stage 1: Macro & Arch Consultation —— 前店按需触发)**
   - **触发时机**：`Planner` 起草完 `changes/<id>/spec.md` 后，若涉及跨模块架构重构、核心数据模型演进或高危安全机制，在呈交人类最终拍板前触发（常规轻量需求可跳过）。
   - **执行方式**：**略过 `reviewer-lead`**，由 `Planner` 直接按需切屏咨询 **`reviewer-arch`** 或 **`reviewer-security`**，评估深模块合理性与 `gitnexus impact` 爆炸半径，将宏观修正直接融入 `spec.md` 并记录于 `review.md` 的 Stage 1 章节，完事即销。
2. **🔬 第二阶段：实施期测试与代码细节/防偏离终审 (Stage 2: Implementation & Drift Gate —— 后厂强制门禁)**
   - **子阶段 2A：测试代码前置快检 (Red Test Gate)**：在 `Test Agent` 写完 Red Test 后、`Coding Agent` 动手前，由 **`reviewer-lead` 独立执行**（仅在涉及红队 PoC 转化时点名 `reviewer-security` 协审）。严格按《4 维测试审查清单》与“硬编码证伪法”拦截弱断言与契约偏差。
   - **子阶段 2B：业务实现与防偏离终审 (Code & Drift Gate)**：在 `Coding Agent` 跑通局部单测变绿后触发，实行**“主审开方点将 ➔ Dispatcher 抓药切屏 ➔ 主审合议裁决”**三拍闭环：
     - **第 1 拍（主审分诊点将）**：`reviewer-lead` 仅运行 `git diff --stat` 与 `gitnexus detect-changes`（**严禁自己跑 `fallow`/`tsc`/`vitest`/`impact`**）。若属 Tier 1（<20 行纯文档/文案/样式微调），直接签字放行；若属 Tier 2/3，立即向终端输出一行点将令并结束回合：
       `TRIAGE_RESULT: Tier 2 | SPAWN_EXPERTS: [reviewer-quality, reviewer-perf] | FOCUS: "核查 xxx 模块"`
     - **第 2 拍（Dispatcher 并发代跑）**：`dispatcher` 解析点将令，在 `review` Tab 右侧并发切出对应专家 Pane、传入 `FOCUS` 指令并 `--wait` 等待，收集 ≤15 行专家简报后执行 `herdr pane close` 销毁专家窗格。
     - **第 3 拍（主审 ROI 仲裁与落盘）**：`dispatcher` 将全部专家简报喂回 `reviewer-lead`，由主审权衡冲突、剔除吹毛求疵，统一写入 `changes/<id>/review.md`。

### 4.2 垂直专家具象触发特征矩阵 (Concrete Routing Heuristics)
`reviewer-lead` 在第 1 拍分诊时，严格依据以下客观特征组合点名专家：

| 专家角色 ID | 具象触发条件（命中任一特征即必须点名唤起） |
| :--- | :--- |
| **`reviewer-quality`** | **凡改动包含任何业务源码 (`src/`) 或测试代码 (`tests/`)**（非纯文档/注释微调），100% 必调！负责跑 `fallow` 增量健康度、`tsc` 与 **全量测试套件回归**。 |
| **`reviewer-arch`** | 1. `gitnexus detect-changes` 显示风险 `>= MEDIUM` 或波及业务流 `>= 2` 个；<br>2. 触及公共核心层、全局状态管理或数据库 Schema；<br>3. 跨 `>= 3` 个模块目录修改，或怀疑实现偏离了 `spec.md` 既定架构边界。 |
| **`reviewer-security`** | 1. 触及认证鉴权、权限守卫、加密脱敏、资金/计费/敏感状态流转；<br>2. 含数据库查询、文件 I/O、系统命令执行、富文本渲染或新增外部 API；<br>3. 修改了 `package.json` 依赖，或当前变更集存在 `security-poc.md`。 |
| **`reviewer-perf`** | 1. 数据层涉及循环内查询、大表查询、索引/缓存策略或并发锁；<br>2. 视图层涉及高频事件监听、定时器、海量节点渲染或复杂闭包。 |
| **`reviewer-ux`** | 1. 涉及前端交互组件、弹窗模态框、表单校验或布局样式；<br>2. 涉及键盘快捷键流、焦点捕获管理 (Focus Trap)、无障碍属性或用户提示文案。 |

### 4.3 防橡皮图章与防过度挑刺双保险：证伪举证 + 红黄分级
1. **🛡️ 核心防线证伪核查 (Proof of Defense —— 杜绝无脑 Approve)**：
   - 任何 Reviewer（含主审与专家）在给予通过前，必须在报告中明确指出本次改动**最脆弱的边界/异常点**，并**贴出源码或测试中实施防御的确切文件名与行号 (`file:line`)**。拿不出确切防御行号，严禁给予 `APPROVED`。
2. **🚦 审查意见三级定性 (Severity Triage —— 杜绝过度挑刺浪费 Token)**：
   - 🔴 **`[BLOCKER / 致命阻断]`**：违背 `spec.md` 契约、存在安全/崩溃/泄漏漏洞、测试假阳性、缺少核心边界防御或 `fallow` 退化 (`delta > 0`)。➔ **触发 `CHANGES_REQUESTED` 打回返工（最多允许 2 轮返工，超限挂起交人类裁决）**。
   - 🟡 **`[CONSTRUCTIVE / 建设性演进建议]`**：当前功能正确且安全，但存在中远期可优化的架构演进或扩展点。➔ **不阻断当前流水线（状态仍为 `APPROVED` 直接放行发布），由 `Planner` 在结项时提取并登记至 `KANBAN.md` 的 Inbox 占位池**！
   - ⚪ **`[NITPICK / 主观风格吹毛求疵]`**：已被 Linter 覆盖的格式问题或个人命名偏好。➔ **绝对禁止输出**。

---

## 5. 标准协同流水线与前店后厂交互机制 (Pipeline & Mailbox Protocol)

```mermaid
flowchart TD
    subgraph 前店规划层 [前店: 主工作区 (永不阻塞)]
        User([👤 人类开发者]) <-->|讨论需求 / 认知单工队列| Planner[Planner 规划师<br/>维护 KANBAN / prd / spec / tasks]
        Planner -.->|复杂历史代码摸底| Explorer[Explorer 探路员<br/>输出 explore.md 即用即销]
        Planner -.->|Stage 1: 宏观架构按需会诊| ArchPre[Arch / Security 专家<br/>把关宏观方向]
    end

    Planner ==>|1. 人类拍板后异步点火<br/>herdr agent prompt dispatcher (无 --wait)| Dispatcher

    subgraph 后厂执行层 [后厂: Standard 原地 或 .worktrees/id/ 隔离并发]
        Dispatcher[Dispatcher 状态机调度员<br/>仅读写 tasks.md 状态头] --> OpsDep[按需前置: Ops 安装新增依赖]
        OpsDep --> TestRed[2. 锁定测试: Test 编写失败用例 Red Test]
        TestRed --> Rev2A[3. 测试快检 Stage 2A: Lead Reviewer 审测试 4 维清单]
        Rev2A --> CodeGreen[4. 业务实施: Coding 编码 + 跑局部单测至 Green + detect-changes]
        CodeGreen --> Rev2B[5. 代码终审 Stage 2B:<br/>Lead 点将 ➔ Dispatcher 并发切专家 ➔ Lead 合议写 review.md]
        Rev2B -.->|按需冒烟| E2E[E2E Specialist 现场走查]
        Rev2B & E2E -->|更新 tasks.md 为 WAITING_HUMAN_ACCEPTANCE| Mailbox[(tasks.md 状态信箱)]
    end

    Mailbox -.->|Planner 空闲时拉取并按 FIFO 呈报人类| User
    User ==>|人类验收报障| DebugFlow[Planner 异步唤醒 Dispatcher ➔ 调 Debug Agent 产出 debug.md ➔ Test/Coding 修复]
    User ==>|人类验收通过授权| OpsRelease[Planner 异步唤醒 Dispatcher ➔ 调 Ops 构建/Commit/合并 Worktree/刷新图谱]
```

### 5.1 动态流水线裁剪通道 (Dynamic Pipeline Tailoring)
`Planner` 在与人类进行【法定节点 1：需求与方案对齐】时，必须根据改动规模在 `tasks.md` 头部明确标定执行通道：
- **微型轻量通道 (`Quick-Fix`)**（<20 行 / 纯文案 / 纯样式 / 简单配置）：`Dispatcher ➔ Coding ➔ Lead Reviewer (Tier 1 秒审) ➔ Ops`。
- **标准功能通道 (`Standard`)**（20~150 行 / 局部新特性 / 常规组件）：`Dispatcher ➔ Test (Red) ➔ Lead Reviewer (Stage 2A 测试快检) ➔ Coding (局部 Green) ➔ Reviewer Ensemble (Stage 2B 终审 + 全量回归) ➔ Ops`。
- **全量高危通道 (`Full-Rigor`)**（核心架构 / 鉴权计费 / 数据库迁移）：`Stage 1 宏观预审 ➔ Standard 全流程 + Red Team 动态渗透 (security-poc.md) + E2E Specialist 冒烟走查`。
- **疑难排障通道 (`Bugfix`)**（人类验收报障 / E2E 崩溃 / 终审回归失败）：`Dispatcher ➔ Debug Agent (产出 debug.md) ➔ Test (补写复现 Red Test) ➔ Coding (按 Fix Spec 修复变绿) ➔ Reviewer 终审`。

### 5.2 三大法定人类交互节点与单工认知队列 (Human Touchpoints & Cognitive Queue)
1. **三大法定人类介入节点**：
   - **节点 1（立项与通道拍板）**：`Planner` 完成 `prd.md`、`spec.md` 与 `tasks.md`（含推荐通道与端口分配），经人类确认后异步点火 `Dispatcher`。
   - **节点 2（审查重大阻断或返工超限）**：当审查遭遇 `BLOCKED`、高危架构分歧或 `Coding` 连续 2 轮返工仍未通过时，`Dispatcher` 将 `tasks.md` 标为 `WAITING_HUMAN_DECISION` 并静默挂起。
   - **节点 3（浏览器真实体验验收与发布授权）**：代码终审通过且服务就绪后，`Dispatcher` 将 `tasks.md` 标为 `WAITING_HUMAN_ACCEPTANCE` 并静默挂起，等待人类体验验收与 Git 提交授权。
2. **人类认知单工队列 (FIFO Cognitive Funnel)**：
   - 当后台多个并行 Worktree 同时处于 `WAITING_HUMAN_*` 状态时，`Planner` **每次仅向人类呈报 1 个变更集**的决策或验收清单，末尾仅用 1 行提示队列余量（如 `⏳ 队列中另有 [002, 003] 已就绪静候处理`），杜绝多任务轰炸导致的认知过载。

### 5.3 下游 Agent 故障自愈三步法 (Self-Healing SOP)
当 `Dispatcher` 执行 `--wait` 发生超时或下游异常时，**严禁越权代庖**，必须按序执行：
1. **观察与中断重试 (Read, Abort & Retry)**：先执行 `herdr agent read <TARGET> --lines 20` 检查是否仍在正常输出；若确系卡死，执行 `herdr agent send-keys <TARGET> ctrl+c`，确认 `herdr agent get <TARGET>` 恢复就绪后重新派发。
2. **重启进程 (Reboot Agent)**：若重试无效，执行 `herdr agent stop <TARGET>` 后重新 `herdr agent start <TARGET>` 恢复会话。
3. **挂起上报 (Escalate via Mailbox)**：若自愈仍失败，`Dispatcher` 将报错现场记录至 `tasks.md` 并设为 `WAITING_HUMAN_DECISION` 挂起。

---

## 6. 异构 Agent 环境探针与全角色映射 (`.agents/environment.json`)

初始化时探测本地已安装的 CLI (`claude`, `codex`, `agy`, `pi`, `hermes`)，根据 15 个角色的算力诉求生成 `.agents/environment.json`（全局与各 `roles/*.md` 梯队严格对齐）：

| 角色集群与 ID | 核心算力诉求 | 优选 Harness 梯队 (由高到低) | 理想思考深度 (Thinking) |
| :--- | :--- | :--- | :--- |
| **`planner` / `explorer` / `debugger` / `security-redteam` / `reviewer-lead` / `reviewer-arch` / `reviewer-perf` / `reviewer-security`** | 高维架构抽象、法医式逆向溯源、攻防博弈与证伪裁决 | `claude-code` ➔ `codex` ➔ `agy` | **High** (深度推理) |
| **`coding` / `test` / `reviewer-ux`** | 严格契约遵从、边界用例推演、精准行级实现与交互审计 | `codex` ➔ `claude-code` ➔ `agy` | **Medium** (适度推断) |
| **`test-e2e`** | 极速 DOM/A11y 树理解、页面语义自愈与冒烟走查 | `agy` ➔ `claude-code` ➔ `pi` | **Low ~ Medium** (极速自愈) |
| **`dispatcher` / `ops` / `reviewer-quality`** | 毫秒级状态机流转、确定性构建发布、海量原始日志吞吐过滤 | `pi` ➔ `hermes` ➔ `agy` ➔ `claude-code` | **None / Low** (零延迟确定性) |

### `.agents/environment.json` 标准完整结构
```json
{
  "updated_at": "2026-10-27T00:00:00Z",
  "mode": "standard",
  "base_port": 3000,
  "detected_harnesses": ["claude", "codex", "agy", "pi"],
  "roles": {
    "planner": { "harness": "claude", "model": "claude-3-7-sonnet", "thinking": "high" },
    "explorer": { "harness": "claude", "model": "claude-3-7-sonnet", "thinking": "high" },
    "dispatcher": { "harness": "pi", "model": "gemini-3.8-flash-low", "thinking": "none" },
    "coding": { "harness": "codex", "model": "gpt-5-codex", "thinking": "medium" },
    "test": { "harness": "codex", "model": "gpt-5-codex", "thinking": "medium" },
    "ops": { "harness": "pi", "model": "gemini-3.8-flash-low", "thinking": "none" },
    "debugger": { "harness": "claude", "model": "claude-3-7-sonnet", "thinking": "high" },
    "security-redteam": { "harness": "claude", "model": "claude-3-7-sonnet", "thinking": "high" },
    "test-e2e": { "harness": "agy", "model": "gemini-3.8-flash-medium", "thinking": "low" },
    "reviewer-lead": { "harness": "claude", "model": "claude-3-7-sonnet", "thinking": "high" },
    "reviewer-quality": { "harness": "pi", "model": "gemini-3.8-flash-low", "thinking": "none" },
    "reviewer-arch": { "harness": "claude", "model": "claude-3-7-sonnet", "thinking": "high" },
    "reviewer-perf": { "harness": "claude", "model": "claude-3-7-sonnet", "thinking": "high" },
    "reviewer-security": { "harness": "claude", "model": "claude-3-7-sonnet", "thinking": "high" },
    "reviewer-ux": { "harness": "codex", "model": "gpt-5-codex", "thinking": "medium" }
  }
}
```

---

## 7. Herdr 免轮询调度、分屏范式与会话持久化 (CLI Patterns & Session Persistence)

### 7.1 前店异步点火与后厂阻塞调度范式
```bash
# 1. 【前店 Planner】异步点火 Dispatcher（严禁加 --wait，0 秒释放主窗口）：
herdr agent prompt dispatcher-001 "请接管 changes/001，严格依据 changes/001/tasks.md 启动 Standard 通道流水线"

# 2. 【后厂 Dispatcher】阻塞式派发执行角色（必须显式指明契约文件路径，并带 --wait）：
herdr agent prompt test "请阅读 changes/001/spec.md 与 changes/001/tasks.md，编写 Phase 1 失败测试 (Red Test)" --wait --timeout 120000
herdr agent prompt reviewer-lead "请依据 changes/001/spec.md 对新增测试文件执行 Stage 2A 测试代码快检，并更新 changes/001/review.md" --wait --timeout 90000
herdr agent prompt coding "请阅读 changes/001/spec.md 与 changes/001/tasks.md，实施业务代码并运行关联单测迭代至 Green" --wait --timeout 180000

# 3. 读取输出（使用 --source recent-unwrapped 防止终端软换行截断表格/路径）：
herdr agent read reviewer-lead --source recent-unwrapped --lines 40
```

### 7.2 Dispatcher 替 Lead Reviewer 动态切屏并发调度专家范式
当 `reviewer-lead` 输出 `SPAWN_EXPERTS: [reviewer-quality, reviewer-arch]` 时，由 `dispatcher` 执行以下标准生命周期：
```bash
# 1. 在 review Tab 右侧切分新窗格并启动垂直专家（自动读取 environment.json 配置）：
QUAL_PANE=$(herdr pane split --target review:p1 --direction right -q)
ARCH_PANE=$(herdr pane split --target "$QUAL_PANE" --direction down -q)

herdr agent start reviewer-quality --kind $(jq -r '.roles["reviewer-quality"].harness' .agents/environment.json) --pane "$QUAL_PANE" -- --model $(jq -r '.roles["reviewer-quality"].model' .agents/environment.json)
herdr agent start reviewer-arch --kind $(jq -r '.roles["reviewer-arch"].harness' .agents/environment.json) --pane "$ARCH_PANE" -- --model $(jq -r '.roles["reviewer-arch"].model' .agents/environment.json)

# 2. 并发派发任务（先连发不带 --wait 的指令实现并行，再依次 wait 回收）：
herdr agent prompt reviewer-quality "请执行静态健康度扫描与全量测试回归，输出 <=15 行简报"
herdr agent prompt reviewer-arch "请结合 changes/001/spec.md 审查架构边界与爆炸半径，焦点：$FOCUS"
herdr agent wait reviewer-quality --timeout 120000
herdr agent wait reviewer-arch --timeout 120000

# 3. 提取专家简报后立即关闭专家窗格释放资源：
QUAL_REPORT=$(herdr agent read reviewer-quality --source recent-unwrapped --lines 30)
ARCH_REPORT=$(herdr agent read reviewer-arch --source recent-unwrapped --lines 45)
herdr pane close "$QUAL_PANE"
herdr pane close "$ARCH_PANE"
```

### 7.3 Worktree 创建与软链接初始化范式
在 `worktree` 并行模式下，启动新特性 `<id>` 时的标准目录初始化命令：
```bash
mkdir -p .worktrees
git worktree add -b "feat/<id>" ".worktrees/<id>"
ln -sfn "../../changes" ".worktrees/<id>/changes"
ln -sfn "../../.agents" ".worktrees/<id>/.agents"
```

### 7.4 会话快照与跨天秒级复活 (`.agents/session.json`)
```bash
# 保存快照（统一使用环境变量回退机制，零外部子命令依赖）：
herdr agent list | jq --arg ws "${HERDR_WORKSPACE_ID:-w1}" --arg proj "$(basename "$PWD")" \
  '{updated_at: (now | todate), workspace_id: $ws, project: $proj, agents: [.result.agents[] | {key: (.name // "planner"), value: {name: (.name // "planner"), pane_id, tab_id, conversation_id: .agent_session.value, model: (.terminal_title | capture("--model (?<m>[^ ]+)") | .m // "default")}}] | from_entries}' > .agents/session.json

# 按角色复活 Agent（结合 environment.json 与 session.json）：
ROLE="coding"
HARNESS=$(jq -r --arg r "$ROLE" '.roles[$r].harness // "codex"' .agents/environment.json)
MODEL=$(jq -r --arg r "$ROLE" '.roles[$r].model // "default"' .agents/environment.json)
CONV_ID=$(jq -r --arg r "$ROLE" '.agents[$r].conversation_id' .agents/session.json)
PANE_ID=$(jq -r --arg r "$ROLE" '.agents[$r].pane_id' .agents/session.json)
herdr agent start "$ROLE" --kind "$HARNESS" --pane "$PANE_ID" -- --conversation "$CONV_ID" --model "$MODEL"
```

---

## 8. 智能代码定位与图谱导航规范 (Code Intelligence & Navigation)

遵循**“图谱定位先行、精准切片读取”**原则，严禁盲目全量通读大文件：

| 场景与意图 | 首选工具 | 说明与使用范式 | 典型调用者 |
| :--- | :--- | :--- | :--- |
| **已知符号查行号与上下游** | **`gitnexus context`** | 秒级锁定定义文件、起止行号与 360 度调用拓扑。 | `planner`, `explorer`, `coding`, `debugger` |
| **探索未知业务执行流** | **`gitnexus query`** | 输入简短英文概念词（如 `"user auth"`），获取跨层执行拓扑。 | `planner`, `explorer`, `debugger` |
| **评估改动爆炸半径** | **`gitnexus impact`** | `gitnexus impact -d upstream <symbol>` 追溯上游调用方与受波及流程。 | `reviewer-arch`, `coding`, `explorer` |
| **验证改动范围与越界门禁** | **`gitnexus detect-changes`** | 将 Git Diff 映射到符号与业务流，形成**三重防线**（Coding 自检 ➔ Lead Reviewer 终审分诊 ➔ Ops 提交前 staged 拦截）。 | `coding`, `reviewer-lead`, `ops` |
| **查文案或精准报错字面量** | **`rg -n` (ripgrep)** | 毫秒级锁定 UI 文案、错误码或环境变量所在行号。 | 除 `dispatcher` 外的全体探查/实现角色 |