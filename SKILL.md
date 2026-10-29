---
name: herdr-teamwork
description: Multi-agent spec implementation orchestrated via Herdr terminal panes, workspaces, and optional Git Worktrees (Planner, Explorer, Dispatcher, TDD, Coding, Reviewer Ensemble, Ops, Debugger, RedTeam, E2E). Use when initiating multi-agent spec implementation, parallel feature development, or complex engineering workflows.
---

# Herdr Multi-Agent Teamwork (多 Agent 协同工程规范 v2.1)

本技能通过 Herdr 终端工作区管理工具构建**“双控台分治（窗口 1 规划 / 窗口 2 交付）、内外双驱（内部 `--wait` 同步 + 跨任务 `tail -f` 监听）、事件溯源（`pipeline.jsonl`）”**的多 Agent 物理隔离与协作体系。
遵循 **OpenSpec 活文档标准**，实现规划与交付彻底物理绝缘、宏微观契约正交、职责绝对边界化与证伪式分形审查。

---

## 1. 核心目录组织哲学与双模式架构 (Asset vs Infrastructure & Dual-Mode)

系统支持 **常规单线模式 (`standard`)** 与 **Worktree 并行模式 (`worktree`)**，由用户在节点 1 按需自由设定并发度（无硬性上限）。主工作区常驻两大交互控制台：**左窗格 `Planner`（总规划台）**与**右窗格 `Dispatcher`（交付总控台）**：

```text
project-root/                        # 【主工作区 (Workspace: main)】：窗口1 Planner + 窗口2 Dispatcher
├── changes/                         # 第一类业务数据资产 (First-Class Artifacts，纳入 Git 版本管理)
│   ├── KANBAN.md                    # 全局大盘总看板 (Planner 100% 独占维护，含 Inbox 占位池)
│   └── <id>/                        # 具体特性变更集目录 (如 001-user-auth/)
│       ├── prd.md                   # 业务诉求、痛点与产品级验收标准 (Why & What)
│       ├── spec.md                  # 技术契约、架构边界与编号化验收条件 AC-* (Architecture & API)
│       ├── tasks.md                 # 纯微观代码改造勾选清单 (How & Checklist，专供 tdd / coding 使用)
│       ├── pipeline.jsonl           # 流水线编排与状态事件流 (Planner 创世 PLAN，Dispatcher 独占续写)
│       ├── review.md                # 审查裁决归档 (含对账单、防御行号举证、双清单与红黄分级)
│       ├── debug.md                 # 法医排错根因诊断与 Fix Spec 报告 (按需产出)
│       ├── security-poc.md          # 红队渗透测试与 PoC 验证报告 (按需产出)
│       └── explore.md               # 复杂历史代码可行性预研简报 (按需产出)
├── .agents/                         # Agent 运行时支撑基建 (Infrastructure Surface)
│   ├── environment.json             # 宿主机器 Harness 画像、并发模式与 15 角色动态配置
│   ├── session.json                 # Herdr 会话状态快照与跨天秒级复活配置
│   └── skills/herdr-teamwork/roles/ # 15 个正交角色的专属契约库
└── .worktrees/                      # 【并行执行隔离区】(worktree 模式下由 Ops 建场管理，纳入 .gitignore)
    └── <id>/                        # 绑定独立 Herdr Workspace (ws-<id>) + 独立分支 + 独立端口
        ├── changes -> ../../changes             # 🔗 软链接共享主工作区 changes/，契约与事件流 0 延迟互通
        ├── .agents -> ../../.agents             # 🔗 软链接共享主工作区 .agents/，复用全局环境配置
        ├── node_modules -> ../../node_modules   # 🔗 默认软链接秒级复用依赖；装新包时由 Ops 执行“写时解链”
        ├── src/                                 # 当前特性独立修改的业务源码
        └── tests/                               # 当前特性独立修改的测试代码
```

---

## 2. 变更集核心文档维护准则 (Living Specs & Single Owner Rules)

为彻底杜绝多 Agent 并发写冲突、消除孤儿文件并保护 `Planner` 上下文，严格执行**宏微观正交**与**单文件唯一写者**规范：

| 文档路径 | 唯一写入人 (Writer) | 定位与维护机制 | 格式范式与流转准则 |
| :--- | :--- | :--- | :--- |
| **`changes/KANBAN.md`** | **`Planner` 独占** | **全局大盘单文件内聚**：<br>严禁私建碎片化 `Inbox.md`；未开展需求第一时间入池占位；结项与 `CONSTRUCTIVE` 建议仅在人类确认后由 `Planner` 录入。 | **需求未启，看板先行**：<br>- 状态流转：`📥 占位池 (Inbox/Backlog)` ➔ `🚀 进行中 (In Progress)` ➔ `✅ 已完成 (Done)`。 |
| **`changes/<id>/prd.md`** | **`Planner`** | **产品诉求 (Why & What)**：需求调整直接在原文就地演进。 | 文末附 2~3 行简明 `## 变更备忘录 (Changelog)` 记录妥协或调整原因。 |
| **`changes/<id>/spec.md`** | **`Planner`**<br>(可咨询 `Arch`/`Sec`) | **活契约原则 (Living Truth)**：反映当前生效的最新接口与数据结构。 | 原地更新，不留弃用字段，历史交由 Git 追溯；含明确的验收条件编号 (`AC-1, AC-2...`)。 |
| **`changes/<id>/tasks.md`** | **`Planner`** (建档)<br>**`TDD` / `Coding`** (勾选) | **微观代码任务清单 (How & Checklist)**：<br>细化到源码模块、函数与测试文件的改造点清单（不含任何运行时状态头，`Dispatcher` 不触碰此文件）。 | 按纵向切片排列 `- [ ]` 勾选框；`tdd` 与 `coding` 每完成一项代码实施即勾选 `- [x]`。 |
| **`changes/<id>/pipeline.jsonl`** | **`Planner`** (首行 `PLAN`)<br>**`Dispatcher`** (独占续写) | **宏观编排配方 + 运行状态事件流 (Event Sourcing)**：<br>合一承载动态定制的 Agent 工序序列与实时执行轨迹；下游工人严禁写此文件。 | **Append-Only 单行自包含 JSON**：<br>- 首行 `event:"PLAN"` 记模式、Workspace、端口与定制 `pipeline` 数组；<br>- 推进追加 `event:"STEP"`；中途变阵追加 `event:"REPLAN"`；<br>- 随特性结项一并归档为“黑匣子飞行记录仪”。 |
| **`changes/<id>/review.md`** | **`Lead Reviewer`** | **单文件权威收敛**：严禁各审查专家私建碎片文件。 | **报纸头条原则 + 四大法定专区**：<br>1. 裁决看板与红黄分级 (`APPROVED` / `CHANGES_REQUESTED`)；<br>2. 审查团队与路由依据；<br>3. 工具执行取证清单；<br>4. 契约对账单与防线行号举证 (`Proof of Defense`)。历史轮次用 `<details>` 折叠。 |
| **`changes/<id>/debug.md`** | **`Debug Agent`** | **法医溯源与修复契约**：窗口 2 验收报障、`e2e` 崩溃或终审回归失败时产出。 | 最新一轮置顶：含异常现象、根因定位 (`file:line`)、供 `coding` 执行的《Fix Spec》与供 `tdd` 执行的必补断言。 |
| **`changes/<id>/security-poc.md`** | **`Red Team Lead`** | **攻防演练产物**：高危特性触发，隔离沙箱动态渗透。 | 含 STRIDE 威胁类型、CVSS 定级、复现步骤、可直接转化的最小化 PoC 脚本与加固建议。 |
| **`changes/<id>/explore.md`** | **`Explorer`** | **深度代码考古简报**：复杂历史代码摸底时按需产出。 | 浓缩现有模块拓扑、技术债约束与演进可行性评估，保护 `Planner` 上下文不被海量源码污染。 |

---

## 3. 角色矩阵与职责正交契约 (15 Orthogonal Role Contracts)

全系统划分为**“前店规划层（窗口 1）”**、**“后厂交付与执行层（窗口 2 及各 Workspace）”**与**“分形审查层”**三大正交集群：

| 集群 | 角色 ID (全局统一) | 契约文件 | 核心职责 | 绝对红线 (Hard Boundaries) |
| :--- | :--- | :--- | :--- | :--- |
| **前店<br>规划层** | **`planner`** | [`roles/planner.md`](roles/planner.md) | **产品与架构规划师（窗口 1）**：直面人类聊需求、独占维护 `KANBAN.md`、撰写 `prd/spec/tasks`、动态定制工序并创建 `pipeline.jsonl` 首行 `PLAN`（含上下文策略 `ctx`）。 | **严禁介入后厂日常验收排障**；严禁未经人类确认擅自压缩或清空上下文；严禁通读海量源码；严禁改代码或直接调后厂工人。 |
| **前店<br>规划层** | **`explorer`**<br>(项目记忆沉淀) | [`roles/explorer.md`](roles/explorer.md) | **代码探路与可行性预研员**：深入复杂历史源码验证用户想法的现实可行性，输出 `explore.md` 简报并沉淀项目演进心智模型。 | **严格只读权限**；严禁倒灌大段原始源码；`standard` 模式常驻复用（Feature 结项后 `/compact`），`worktree` 模式随工作区销毁。 |
| **后厂<br>执行层** | **`dispatcher`** | [`roles/dispatcher.md`](roles/dispatcher.md) | **交付总控与状态机调度员（窗口 2 总控 / `ws-<id>` 执行机）**：后台 `tail -f` 监听多任务、内部 `--wait` 阻塞调度、独占续写 `pipeline.jsonl`、替主审拉起/复用专家、在 Feature 结项后统一打理各角色上下文。 | **物理蒙眼：禁读 `src/` 与 `tests/`**；**仅允许追加写入 `pipeline.jsonl`**（对所有 `.md` 只读）；严禁执行建场/构建/装包/Git 写命令（全归 `ops`）。 |
| **后厂<br>执行层** | **`tdd`** | [`roles/tdd.md`](roles/tdd.md) | **测试驱动开发工程师**：在业务编码前依据 `spec.md`、`tasks.md`、`debug.md` 或 `security-poc.md` 编写高严谨度失败用例 (Red Test) 并勾选 `tasks.md`。 | **严禁修改业务代码 (`src/`) 或 `pipeline.jsonl`**；严禁为迎合变绿而弱化断言或编写同语反复假阳性测试。 |
| **后厂<br>执行层** | **`coding`** | [`roles/coding.md`](roles/coding.md) | **业务代码实现者**：依据 `spec.md` / `tasks.md` / `debug.md` 编写业务代码并勾选 `tasks.md`，**运行关联单测迭代至 Green**，执行 `tsc --noEmit` 与 `gitnexus detect-changes`。 | **严禁修改任何测试文件 (`tests/`) 或 `pipeline.jsonl`**；严禁私自装包或启停服务（缺包输出 `NEED_OPS`）。 |
| **后厂<br>执行层** | **`ops`** | [`roles/ops.md`](roles/ops.md) | **环境、Worktree 与发布守护者**：全权负责 Worktree 物理建场与销毁、`node_modules` 写时解链装包、**非阻塞**后台守护服务、数据库快照、构建与受控 Git 发布。 | **严禁前台阻塞自身终端主线程**；**严禁在软链上直接装包污染主目录**；严禁改源码/测试/看板；严禁未授权提前 commit。 |
| **后厂<br>执行层** | **`debugger`**<br>(项目记忆沉淀) | [`roles/debugger.md`](roles/debugger.md) | **法医式排错侦探**：窗口 2 验收报障、`e2e` 崩溃或终审回归失败时出马，利用 `gitnexus` 逆向溯源并输出 `changes/<id>/debug.md`。 | **严格只读权限，绝不亲自动手改代码**；严禁倒灌原始调试日志；`standard` 模式常驻并在 Feature 结项后 `/compact` 沉淀项目记忆。 |
| **后厂<br>执行层** | **`security-redteam`**<br>(项目记忆沉淀) | [`roles/security-redteam.md`](roles/security-redteam.md) | **红队渗透测试领队**：STRIDE 威胁建模、白盒污点追踪、隔离沙箱动态渗透，产出 `security-poc.md`。 | **严禁攻击非授权或生产环境**；严禁修改业务代码与标准测试；`standard` 模式常驻并在 Feature 结项后 `/compact` 沉淀攻击面记忆。 |
| **后厂<br>执行层** | **`e2e`**<br>(用完清空) | [`roles/e2e.md`](roles/e2e.md) | **端到端与冒烟测试专家**：双轨制走查（90% 小模型现场冒烟查白屏/Console红字/500错误；10% 黄金链路原子 JS 脚本化）。 | **严禁为日常易变切片制造脆弱脚本债务**；单动作自愈 ≤3 次、总步数 ≤15 步刚性熔断；Feature 结项后直接 `/clear` 清空过期 DOM 快照。 |
| **分形<br>审查层** | **`reviewer-lead`** | [`roles/reviewer-lead.md`](roles/reviewer-lead.md) | **主审统筹与裁决官**：独立执行 **Stage 2A 测试快检**；在 **Stage 2B 终审**分诊输出 `SPAWN_EXPERTS` 点将令，回收简报后做 ROI 仲裁并独占签署 `review.md`。 | **严禁亲自运行 `fallow/tsc/vitest/impact/audit`**；严禁亲自敲 `herdr pane` 切屏命令；严禁无行号举证的无脑 `APPROVED`。 |
| **分形<br>审查层** | **`reviewer-quality`**<br>(用完清空) | [`roles/reviewer-quality.md`](roles/reviewer-quality.md) | **代码健康与回归过滤官**：独占运行并消化 `fallow`、`tsc --noEmit` 与 **全量测试套件回归 (`vitest run`)** 原始日志，输出 ≤15 行健康简报。 | **严禁向主审倒灌原始终端日志**；严禁伪造 `delta: +0` 或回归通过率；只读权限；Feature 结项后直接 `/clear` 清空。 |
| **分形<br>审查层** | **`reviewer-arch`**<br>(项目记忆沉淀) | [`roles/reviewer-arch.md`](roles/reviewer-arch.md) | **系统架构专家**：承接前店 **Stage 1 宏观预审** 与后厂 **Stage 2B 架构终审**；审查深模块设计、单向数据流与 `gitnexus impact` 爆炸半径。 | 必须附带工具取证清单与防线行号举证；只读权限；`standard` 模式常驻并在 Feature 结项后 `/compact` 沉淀架构演进记忆。 |
| **分形<br>审查层** | **`reviewer-perf`**<br>(项目记忆沉淀) | [`roles/reviewer-perf.md`](roles/reviewer-perf.md) | **性能与并发专家**：审查无效重渲染、闭包内存泄漏、N+1 查询、全表扫描与缓存并发安全。 | 必须给出具体瓶颈行号与复杂度推导；只读权限；`standard` 模式常驻并在 Feature 结项后 `/compact` 沉淀性能基线记忆。 |
| **分形<br>审查层** | **`reviewer-security`**<br>(项目记忆沉淀) | [`roles/reviewer-security.md`](roles/reviewer-security.md) | **蓝队安全合规专家**：承接前店安全预审与后厂安全终审；审查注入防御、RBAC/ABAC 越权、供应链 CVE，复核红队 PoC 闭环。 | 对高危漏洞拥有一票否决权；必须附带防御行号举证；只读权限；`standard` 模式常驻并在 Feature 结项后 `/compact` 沉淀安全防线记忆。 |
| **分形<br>审查层** | **`reviewer-ux`**<br>(项目记忆沉淀) | [`roles/reviewer-ux.md`](roles/reviewer-ux.md) | **交互与无障碍专家**：审查快捷键冲突、输入法容错、焦点闭环 (Focus Trap)、ARIA 无障碍属性与界面文案。 | 只读权限；`standard` 模式常驻并在 Feature 结项后 `/compact` 沉淀交互规范记忆。 |

---

## 4. 两阶段审查体系与证伪式分形审查矩阵 (Two-Stage Review & Falsification Protocol)

为彻底根治“带着宏观架构硬伤进入编码”、“Lead Reviewer 偷懒不派活”以及“Reviewer 走过场无脑 Approve（Rubber Stamping）”，建立**两阶段、三拍点将、证伪举证与红黄分级**体系：

### 4.1 两阶段审查全链路划分
1. **🏛️ 第一阶段：计划期宏观与架构预审 (Stage 1: Macro & Arch Consultation —— 窗口 1 按需触发)**
   - **触发时机**：`Planner` 起草完 `changes/<id>/spec.md` 后，若涉及跨模块架构重构、核心数据模型演进或高危安全机制，在呈交人类最终拍板前触发（常规轻量需求可跳过）。
   - **执行方式**：**略过 `reviewer-lead`**，由 `Planner` 直接按需唤醒或复用 **`reviewer-arch`** 或 **`reviewer-security`**，评估深模块合理性与 `gitnexus impact` 爆炸半径，将宏观修正直接融入 `spec.md` 并记录于 `review.md` Stage 1 章节（`standard` 模式下窗格常驻保留上下文至 Feature 结项）。
2. **🔬 第二阶段：实施期测试与代码细节/防偏离终审 (Stage 2: Implementation & Drift Gate —— 后厂强制门禁)**
   - **子阶段 2A：测试代码前置快检 (Red Test Gate)**：在 `tdd` 写完 Red Test 后、`coding` 动手前，由 **`reviewer-lead` 独立执行**（仅在涉及红队 PoC 转化时点名 `reviewer-security` 协审）。严格按《4 维测试审查清单》与“硬编码证伪法”拦截弱断言与契约偏差。
   - **子阶段 2B：业务实现与防偏离终审 (Code & Drift Gate)**：在 `coding` 跑通局部单测变绿后触发，实行**“主审开方点将 ➔ Dispatcher 抓药调度 ➔ 主审合议裁决”**三拍闭环：
     - **第 1 拍（主审分诊点将）**：`reviewer-lead` 仅运行 `git diff --stat` 与 `gitnexus detect-changes`（**严禁自己跑 `fallow`/`tsc`/`vitest`/`impact`**）。若属 Tier 1（<20 行纯文档/文案/样式微调），直接签字放行；若属 Tier 2/3，立即向终端输出一行点将令并结束回合：
       `TRIAGE_RESULT: Tier 2 | SPAWN_EXPERTS: [reviewer-quality, reviewer-perf] | FOCUS: "核查 xxx 模块"`
     - **第 2 拍（Dispatcher 并发代跑）**：`dispatcher` 解析点将令，复用已常驻的专家窗格（若首次调用则切出对应专家 Pane）、传入 `FOCUS` 指令并 `wait` 等待，收集 ≤25 行专家简报（`standard` 模式下保留专家窗格至当前 Feature 结项后统一打理上下文；`worktree` 模式下可即用即关或随工作区销毁）。
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
   - 任何 Reviewer 在给予通过前，必须在报告中明确指出本次改动**最脆弱的边界/异常点**，并**贴出源码或测试中实施防御的确切文件名与行号 (`file:line`)**。拿不出确切防御行号，严禁给予 `APPROVED`。
2. **🚦 审查意见三级定性 (Severity Triage —— 杜绝过度挑刺与看板污染)**：
   - 🔴 **`[BLOCKER / 致命阻断]`**：违背 `spec.md` 契约、存在安全/崩溃/泄漏漏洞、测试假阳性、缺少核心边界防御或 `fallow` 退化 (`delta > 0`)。➔ **触发 `CHANGES_REQUESTED` 打回返工（最多允许 2 轮返工，超限挂起为 `WAITING_DECISION` 交人类裁决）**。
   - 🟡 **`[CONSTRUCTIVE / 建设性演进建议]`**：当前功能正确且安全，但存在中远期可优化的演进点。➔ **不阻断当前流水线（状态仍为 `APPROVED` 直接放行），由 `Dispatcher` 记录条数至 `pipeline.jsonl` 并在窗口 2 验收时提醒人类；人类确认采纳后再主动交窗口 1 `Planner` 记入 `KANBAN.md` Inbox**！
   - ⚪ **`[NITPICK / 主观风格吹毛求疵]`**：已被 Linter 覆盖的格式问题或个人命名偏好。➔ **绝对禁止输出**。

---

## 5. 双控台分治、内外双驱与 `pipeline.jsonl` 协议 (Dual-Console & Event Stream Protocol)

```mermaid
flowchart TD
    subgraph 主工作区左窗格 [窗口 1: Planner 总规划台 (上下文 100% 纯净)]
        H1([👤 人类开发者]) <-->|探讨需求 / 动态定制工序| Planner[Planner 规划师<br/>独占维护 KANBAN.md]
        Planner -.->|复杂源码考古| Explorer[Explorer 探路员<br/>输出 explore.md 沉淀项目记忆]
        Planner -.->|Stage 1 预审| PreRev[Arch / Security 专家]
        Planner ==>|节点 1 拍板落盘:<br/>prd + spec + tasks + pipeline.jsonl 首行 PLAN| EventLog[(changes/id/pipeline.jsonl)]
    end

    subgraph 主工作区右窗格 [窗口 2: Dispatcher 交付总控台 (90% 交付排障就地闭环)]
        Master[Dispatcher 总控台<br/>FIFO 认知队列 + 验收/排障/发布交互]
        EventLog -.->|跨流水线监听:<br/>tail -n 0 -f changes/*/pipeline.jsonl| Master
        Master <-->|播报待验收 (附 CONSTRUCTIVE 提醒)<br/>接收报障 / 接收 Commit 授权| H2([👤 人类开发者])
    end

    Master ==>|worktree 模式前置:<br/>调主区 Ops 建场 .worktrees/id 与软链| OpsInit[Ops 物理建场 + 创建 ws-id]
    OpsInit --> Worker

    subgraph 执行工作区 [Standard 原地 或 独立 Workspace ws-id (.worktrees/id/)]
        Worker[Dispatcher 执行机<br/>模式乙: 同步 --wait 驱动 + 独占续写 pipeline.jsonl]
        Worker -->|prompt --wait| TDD[1. TDD: 写 Red Test 勾选 tasks.md]
        TDD --> Rev2A[2. Lead Reviewer: Stage 2A 测试快检]
        Rev2A --> Coding[3. Coding: 实现至局部 Green 勾选 tasks.md]
        Coding --> Rev2B[4. Stage 2B 终审: 三拍点将 + 全量回归]
        Rev2B -.->|按需走查| E2E[5. E2E: 双轨冒烟走查]
        Rev2B & E2E -->|追加 WAITING_ACCEPTANCE| EventLog
    end

    Master ==>|验收报障: 追加 REPLAN 事件| BugLoop[debugger 产出 debug.md ➔ tdd ➔ coding ➔ review]
    Master ==>|验收通过: 授权发布| Release[ops 构建 / Commit / 合入并销毁 Worktree ➔ 追加 DONE]
```

### 5.1 动态可调流水线预设模板 (Customizable Pipeline Presets)
4 个通道仅作为**基础预设起点**，`Planner` 在【法定节点 1】必须展示拟启用的具体角色数组 `pipeline`，支持人类按需动态增删插件化调节：
- **微型轻量预设 (`Quick-Fix`)**（<20 行 / 纯文案 / 纯样式 / 简单配置）：`["coding", "reviewer-lead:2B", "ops"]`
- **标准功能预设 (`Standard`)**（20~150 行 / 局部新特性 / 常规组件）：`["tdd", "reviewer-lead:2A", "coding", "reviewer-lead:2B", "ops"]`（可按需插拔 `"e2e"`）
- **全量高危预设 (`Full-Rigor`)**（核心架构 / 鉴权计费 / 数据库迁移）：`Stage 1 预审` + `["tdd", "reviewer-lead:2A", "coding", "security-redteam", "tdd", "coding", "reviewer-lead:2B", "e2e", "ops"]`
- **排障重排序列 (`REPLAN: Bugfix`)**（窗口 2 验收报障 / `e2e` 崩溃 / 终审回归失败时由 `Dispatcher` 追加）：`["debugger", "tdd", "coding", "reviewer-lead:2B", "ops"]`

### 5.2 `changes/<id>/pipeline.jsonl` 事件流规范 (8+ 字段扁平自包含快照)
每一行均为合法的单行 JSON（严禁美化折行），确保 `tail -n 1` 即可获取完整上下文：
```jsonl
{"ts":"2026-10-27T08:00:00Z","id":"001-auth","event":"PLAN","mode":"worktree","ws":"ws-001","port":3001,"branch":"feat/001-auth","ctx":"compact","pipeline":["tdd","reviewer-lead:2A","coding","reviewer-lead:2B","ops"],"round":1,"state":"QUEUED","msg":"节点1对齐完成"}
{"ts":"2026-10-27T08:02:10Z","id":"001-auth","event":"STEP","ws":"ws-001","port":3001,"step":"tdd","round":1,"state":"RUNNING","msg":"Red Test 编写完成"}
{"ts":"2026-10-27T08:15:30Z","id":"001-auth","event":"STEP","ws":"ws-001","port":3001,"step":"reviewer-lead:2B","round":1,"state":"WAITING_ACCEPTANCE","constructive":1,"msg":"Stage 2B 终审 APPROVED [含1条CONSTRUCTIVE建议]，服务已在 http://localhost:3001 就绪待验收"}
```
- **`state` 核心状态机枚举（6 种）**：`QUEUED`（已立项待启动）| `RUNNING`（自动流转中）| `WAITING_ACCEPTANCE`（待人类浏览器验收）| `WAITING_DECISION`（审查阻断/返工满2轮/契约缺陷待人类拍板）| `STALLED`（自愈失败环境挂起）| `DONE`（已合并发布）。
- **`ctx` 跨特性上下文策略枚举（专供 `standard` 常驻模式）**：`"keep"`（强关联连续小切片，直接保留）| `"compact"`（默认推荐，结项后主动压缩沉淀项目演进记忆）| `"clear"`（跨完全无关业务域，清空重置）。

### 5.3 下游 Agent 故障自愈三步法 (Self-Healing SOP)
当 `Dispatcher` 执行 `--wait` 发生超时或下游异常时，**严禁越权代庖**，必须按序执行：
1. **观察与中断重试**：先执行 `herdr agent read <TARGET> --lines 20` 检查是否仍在正常输出；若确系卡死，执行 `herdr agent send-keys <TARGET> ctrl+c`，确认 `herdr agent get <TARGET>` 恢复就绪后重试。
2. **重启进程**：若重试无效，执行 `herdr agent stop <TARGET>` 后重新 `herdr agent start <TARGET>` 恢复会话。
3. **挂起上报**：若自愈仍失败，`Dispatcher` 向 `changes/<id>/pipeline.jsonl` 追加 `"state": "STALLED"` 事件并上报窗口 2。

### 5.4 非 Worktree (`standard`) 模式上下文生命周期管理 (Context Lifecycle Management)
在 `worktree` 模式下，每个特性拥有全新 Workspace 与独立 Agent 实例，天然无历史污染；而在 **`standard` 单线常驻模式**下，严格遵循**“特性内全员保真、特性结项 (`DONE`) 后按 4 类角色分级打理”**准则：

| 分类与角色 | 特性进行中 (Intra-Feature) | 特性结项后 (Post-Feature `DONE` / 下一特性启动前) |
| :--- | :--- | :--- |
| **1. 人类确认型 (1 个)**<br>`planner` (窗口 1) | 保持完整规划上下文 | **严禁擅自压缩或清空**！立项落盘或长对话后向人类提议，**获人类明确确认后**再执行 `/compact`（同域演进）或 `/clear`（跨大域重置）。 |
| **2. 关联度动态型 (3 个)**<br>`tdd`, `coding`, `reviewer-lead` | 同一 `change-id` 内（含多轮返工）100% 保留完整记忆（仅当超长时 `/compact`） | 由 `Dispatcher` 按 `PLAN` 事件中的 `"ctx"` 策略执行：<br>- `compact`（默认）：压缩保留项目拓扑与公共模块约定；<br>- `keep`：强关联连续小切片直接沿用；<br>- `clear`：跨完全无关业务域时清空。 |
| **3. 方案甲：常驻沉淀型专家 (7 个)**<br>`explorer`, `debugger`, `security-redteam`, `reviewer-arch/security/perf/ux` | **窗格常驻不销毁**；同一 `change-id` 内（如 Stage 1 ➔ Stage 2B、多次排障）保持完整上下文，不中途压缩 | 若在该 Feature 中被调用过，在 **Feature 完成 (`DONE`) 后统一执行 `/compact`**，将模块演进、鉴权边界与历史架构决策沉淀为长期心智模型，避免下次重头通读源码。 |
| **4. 无脑清空型工具人 (4 个)**<br>`dispatcher`, `ops`, `reviewer-quality`, `e2e` | 单特性内保持运行 | **毫无跨特性记忆价值，从不使用 `/compact`**！在 Feature 结项（`DONE`）后直接执行 `/clear`（或 `/new`）瞬时归零，彻底清除过期 DOM 快照与海量命令日志。 |

---

## 6. 异构 Agent 环境探针与全角色映射 (`.agents/environment.json`)

初始化时探测本地已安装的 CLI (`claude`, `codex`, `agy`, `pi`, `hermes`)，根据 15 个角色的算力诉求生成 `.agents/environment.json`：

| 角色集群与 ID | 核心算力诉求 | 优选 Harness 梯队 (由高到低) | 理想思考深度 (Thinking) |
| :--- | :--- | :--- | :--- |
| **`planner` / `explorer` / `debugger` / `security-redteam` / `reviewer-lead` / `reviewer-arch` / `reviewer-perf` / `reviewer-security`** | 高维架构抽象、法医式逆向溯源、攻防博弈与证伪裁决 | `claude-code` ➔ `codex` ➔ `agy` | **High** (深度推理) |
| **`coding` / `tdd` / `reviewer-ux`** | 严格契约遵从、边界用例推演、精准行级实现与交互审计 | `codex` ➔ `claude-code` ➔ `agy` | **Medium** (适度推断) |
| **`e2e`** | 极速 DOM/A11y 树理解、页面语义自愈与冒烟走查 | `agy` ➔ `claude-code` ➔ `pi` | **Low ~ Medium** (极速自愈) |
| **`dispatcher` / `ops` / `reviewer-quality`** | 毫秒级状态机流转、确定性建场发布、海量原始日志吞吐过滤 | `pi` ➔ `hermes` ➔ `agy` ➔ `claude-code` | **None / Low** (零延迟确定性) |

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
    "tdd": { "harness": "codex", "model": "gpt-5-codex", "thinking": "medium" },
    "coding": { "harness": "codex", "model": "gpt-5-codex", "thinking": "medium" },
    "ops": { "harness": "pi", "model": "gemini-3.8-flash-low", "thinking": "none" },
    "debugger": { "harness": "claude", "model": "claude-3-7-sonnet", "thinking": "high" },
    "security-redteam": { "harness": "claude", "model": "claude-3-7-sonnet", "thinking": "high" },
    "e2e": { "harness": "agy", "model": "gemini-3.8-flash-medium", "thinking": "low" },
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

## 7. Herdr 内外双驱调度、Workspace 隔离与分屏范式 (CLI Patterns)

### 7.1 Worktree 物理建场（`Ops` 执行）与多任务监听（`Master Dispatcher` 执行）
```bash
# 1. 【worktree 模式前置建场】Master Dispatcher 阻塞调度主工作区 Ops 初始化目录与三大软链：
herdr agent prompt ops "请为 changes/001-auth 执行 Worktree 建场：分支 feat/001-auth，目录 .worktrees/001-auth" --wait --timeout 30000

# Ops 内部执行的标准建场命令（含 node_modules 默认软链；后续若需装新包则先 rm .worktrees/001-auth/node_modules 解链）：
mkdir -p .worktrees
git worktree add -b "feat/001-auth" ".worktrees/001-auth"
ln -sfn "../../changes" ".worktrees/001-auth/changes"
ln -sfn "../../.agents" ".worktrees/001-auth/.agents"
ln -sfn "../../node_modules" ".worktrees/001-auth/node_modules"

# 2. 【Master Dispatcher】创建独立 Herdr Workspace (ws-001) 并异步点火该工作区的 Worker Dispatcher：
herdr workspace create ws-001 --cwd ".worktrees/001-auth"
# (在 ws-001 启动独立角色实例后异步点火，不带 --wait)
herdr agent prompt dispatcher --workspace ws-001 "请接管 changes/001-auth，按 pipeline.jsonl 启动流水线"

# 3. 【Master Dispatcher】挂起后台单次触发监听命令（任一任务进入待处理状态即退出并自动唤醒总控台）：
tail -n 0 -f changes/*/pipeline.jsonl | grep --line-buffered -m 1 -E '"state":"(WAITING_|STALLED|DONE)"'

# 4. 【Master Dispatcher】提取全部待人类处理的 FIFO 认知队列（按时间戳升序）：
tail -q -n 1 changes/*/pipeline.jsonl | jq -s 'map(select(.state == "WAITING_ACCEPTANCE" or .state == "WAITING_DECISION" or .state == "STALLED")) | sort_by(.ts)'
```

### 7.2 单流水线内部同步阻塞调度范式（模式乙）
```bash
# Dispatcher 在当前所属 Workspace 内依次阻塞式调度下游工人（必须显式传入契约路径）：
herdr agent prompt tdd "请阅读 changes/001-auth/spec.md 与 changes/001-auth/tasks.md，编写失败测试 (Red Test) 并勾选对应任务项" --wait --timeout 120000
herdr agent prompt reviewer-lead "请依据 changes/001-auth/spec.md 对新增测试执行 Stage 2A 测试代码快检，更新 changes/001-auth/review.md" --wait --timeout 90000
herdr agent prompt coding "请阅读 changes/001-auth/spec.md 与 changes/001-auth/tasks.md，实施业务代码、勾选任务项并运行关联单测迭代至 Green" --wait --timeout 180000

# 读取终端输出（使用 --source recent-unwrapped 防止终端软换行截断路径）：
herdr agent read reviewer-lead --source recent-unwrapped --lines 40
```

### 7.3 Dispatcher 替 Lead Reviewer 动态调度与常驻复用专家范式
```bash
# 1. 若目标专家尚未启动，则在当前 Workspace 的 review Tab 右侧切分新窗格并启动（若已常驻则直接复用）：
if ! herdr agent get reviewer-quality >/dev/null 2>&1; then
  QUAL_PANE=$(herdr pane split --target review:p1 --direction right -q)
  herdr agent start reviewer-quality --kind $(jq -r '.roles["reviewer-quality"].harness' .agents/environment.json) --pane "$QUAL_PANE" -- --model $(jq -r '.roles["reviewer-quality"].model' .agents/environment.json)
fi
if ! herdr agent get reviewer-arch >/dev/null 2>&1; then
  ARCH_PANE=$(herdr pane split --target review:p1 --direction down -q)
  herdr agent start reviewer-arch --kind $(jq -r '.roles["reviewer-arch"].harness' .agents/environment.json) --pane "$ARCH_PANE" -- --model $(jq -r '.roles["reviewer-arch"].model' .agents/environment.json)
fi

# 2. 并发派发任务并依次 wait 回收：
herdr agent prompt reviewer-quality "请执行静态健康度扫描与全量测试回归，输出 <=15 行简报"
herdr agent prompt reviewer-arch "请结合 changes/001-auth/spec.md 审查架构边界与爆炸半径，焦点：$FOCUS"
herdr agent wait reviewer-quality --timeout 120000
herdr agent wait reviewer-arch --timeout 120000

# 3. 提取专家简报（standard 模式下保持窗格常驻，待整个 Feature 结项 DONE 后再对 arch 执行 /compact、对 quality 执行 /clear）：
QUAL_REPORT=$(herdr agent read reviewer-quality --source recent-unwrapped --lines 30)
ARCH_REPORT=$(herdr agent read reviewer-arch --source recent-unwrapped --lines 45)
```

### 7.4 会话快照与跨天秒级复活 (`.agents/session.json`)
```bash
# 保存快照：
herdr agent list | jq --arg ws "${HERDR_WORKSPACE_ID:-main}" --arg proj "$(basename "$PWD")" \
  '{updated_at: (now | todate), workspace_id: $ws, project: $proj, agents: [.result.agents[] | {key: (.name // "planner"), value: {name: (.name // "planner"), pane_id, tab_id, conversation_id: .agent_session.value, model: (.terminal_title | capture("--model (?<m>[^ ]+)") | .m // "default")}}] | from_entries}' > .agents/session.json
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
