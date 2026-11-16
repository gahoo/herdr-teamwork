---
name: herdr-teamwork
description: Multi-agent spec implementation orchestrated via Herdr terminal panes, workspaces, and optional Git Worktrees (Planner, Explorer, Dispatcher, TDD, Coding, Reviewer Ensemble, Ops, Debugger, RedTeam, E2E, Reflector). Use when initiating multi-agent spec implementation, parallel feature development, or complex engineering workflows.
---

# Herdr Multi-Agent Teamwork (多 Agent 协同工程规范 v2.11.0)

本技能通过 Herdr 终端工作区管理工具构建**“双控台分治（窗口 1 规划 / 窗口 2 交付）、内外双驱（内部 `--wait` 同步 + 跨任务 `tail -f` 监听）、事件溯源（`pipeline.jsonl`）”**的多 Agent 物理隔离与协作体系。
遵循 **OpenSpec 活文档标准**，实现规划与交付彻底物理绝缘、宏微观契约正交、职责绝对边界化与证伪式分形审查。

---

## 1. 核心目录组织哲学与双模式架构 (Asset vs Infrastructure & Dual-Mode)

系统支持 **常规单线模式 (`standard`)** 与 **Worktree 并行模式 (`worktree`)**，由用户在节点 1 按需自由设定并发度（无硬性上限）。主工作区常驻两大交互控制台：**左窗格 `Planner`（总规划台）**与**右窗格 `Dispatcher`（交付总控台）**：

```text
project-root/                        # 【主工作区 (Workspace: main)】：窗口1 Planner + 窗口2 Dispatcher
├── GLOSSARY.md                      # 项目级统一领域语言词典 (Planner 维护，全角色共享词汇表，零实现细节)
├── E2E_PLAYBOOK.md                  # 端到端验证路由与交互剧本 (启用 e2e 角色时按需创建，由 E2E 增量维护)
├── docs/adr/                        # 架构决策记录 (仅当满足 3 条件门禁时由 Planner 创建)
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
│       ├── explore.md               # 复杂历史代码可行性预研简报 (按需产出)
│       └── roundtable.md            # 重大架构圆桌辩论纪要与主席裁决书 (圆桌主席分身按需产出)
├── reflections/                     # 项目级经验教训与待探索课题库 (Reflector 独占维护，纳入 Git 管理)
│   └── <domain>.md                  # 按领域沉淀确定性避坑守则与 🔬 [SPIKE_CANDIDATE] 探索课题
├── .agents/                         # Agent 运行时支撑基建 (Infrastructure Surface)
│   ├── environment.json             # 宿主机器 Harness 画像、并发模式与 16 角色动态配置
│   ├── session.json                 # Herdr 会话状态快照与跨天秒级复活配置
│   └── skills/herdr-teamwork/       # 本技能规范库
│       ├── roles/                   # 【Who】16 个正交角色的常驻本职契约库
│       ├── protocols/               # 【Rules】4 大跨角色核心协同协议库 (流水线与事件流 / 两阶段审查与专家分诊 / 上下文与水位预算 / 模型算力与环境配置)
│       ├── playbooks/               # 【How】11 个按需触发的专项战术剧本 (含 bootstrap-teamwork 初始化自举，跨角色共享)
│       ├── templates/               # 【What】10 个标准 JSON 配置与活文档填空骨架模板
│       ├── tools/                   # 【CLI】Herdr 编排与窗格控制唯一权威指令配方卡 (tools/herdr.md §[H-1]~§[H-6])
│       ├── scripts/                 # 【Tools】跨项目通用 Worktree 建场/销毁、水位探针与会话快照脚本 (worktree-up.sh / worktree-down.sh / agent-context.py / session-snapshot.py)
│       └── .reflections/            # Skill 级流程与契约改进反馈 (<id>.md，供 herdr-teamwork 消化吸收)
└── .worktrees/                      # 【并行执行隔离区】(worktree 模式下由 Ops 建场管理，纳入 .gitignore)
    └── <id>/                        # 绑定独立 Herdr Workspace (ws-<id>) + 独立分支 + 按需端口
        ├── changes -> ../../changes             # 🔗 软链接共享主工作区 changes/，契约与事件流 0 延迟互通
        ├── .agents -> ../../.agents             # 🔗 软链接共享主工作区 .agents/，复用全局环境配置
        ├── node_modules / .venv -> ../../...    # 🔗 按技术栈自动软链共享依赖；装新包时由 Ops 执行“写时解链”
        ├── src/                                 # 当前特性独立修改的业务源码
        └── tests/                               # 当前特性独立修改的测试代码
```

---

## 2. 变更集核心文档维护准则 (Living Specs & Single Owner Rules)

为彻底杜绝多 Agent 并发写冲突、消除孤儿文件并保护 `Planner` 上下文，严格执行**宏微观正交**与**单文件唯一写者**规范：

| 文档路径 | 唯一写入人 (Writer) | 定位与维护机制 | 格式范式与流转准则（附标准骨架模板） |
| :--- | :--- | :--- | :--- |
| **`GLOSSARY.md`** | **`Planner`** | **项目级统一领域语言 (Ubiquitous Language)**：<br>全项目常驻标准工件，消除 16 个 Agent 间的概念命名漂移。 | 只定义核心业务概念边界与禁用同义词表；**严禁混入类名、文件路径或数据库表名等实现细节**（模板见 [`templates/GLOSSARY.template.md`](templates/GLOSSARY.template.md)）。 |
| **`E2E_PLAYBOOK.md`** | **`E2E Agent`**<br>(`Planner` 初始化) | **端到端验证路由与源码映射剧本 (按需工件)**：<br>仅在项目启用 `e2e` 角色时创建，免去每次测试或排障重新摸索 DOM 与源码路径。 | 按 **6 要素结构化记录**（`feature_id`、`entry_point`、`user_route`、`dom_selectors`、`keyboard_shortcuts`、`gotchas`），每次验收通过后增量更新（模板见 [`templates/E2E_PLAYBOOK.template.md`](templates/E2E_PLAYBOOK.template.md)）。 |
| **`docs/adr/<id>.md`** | **`Planner`** | **架构决策记录 (Selective ADRs)**：<br>记录深远架构取舍，防止后续 Agent 因不解背景而回退设计。 | **严格 3 条件门禁**（同时满足才写）：① 难以逆转；② 缺乏背景看代码会感到惊讶；③ 存在真实的方案权衡（Trade-off）。 |
| **`changes/KANBAN.md`** | **`Planner` 独占** | **全局大盘单文件内聚（含规划台交接备忘）**：<br>严禁私建碎片化 `Inbox.md`；未开展需求第一时间入池占位；结项与 `CONSTRUCTIVE` 建议仅在人类确认后由 `Planner` 录入；底部常设 `📌 规划台交接备忘 (Planner Handoff)` 供高水位传位「Planner 二世」。 | **需求未启，看板先行**（模板见 [`templates/KANBAN.template.md`](templates/KANBAN.template.md)）：<br>- 状态流转：`📥 占位池 (Inbox/Backlog)` ➔ `🚀 进行中 (In Progress)` ➔ `✅ 已完成 (Done)`；<br>- 仅对**硬逻辑前置依赖**标注 `[Blocked by: <id>]`（涉及相同文件的任务允许并发开启 Worktree，由合入期预同步消解冲突），无未决阻塞项的构成 **Ready Frontier**。 |
| **`changes/<id>/prd.md`** | **`Planner`** | **产品诉求 (Why & What)**：需求调整直接在原文就地演进。 | 文末附 2~3 行简明 `## 变更备忘录 (Changelog)` 记录妥协或调整原因（模板见 [`templates/prd.template.md`](templates/prd.template.md)）。 |
| **`changes/<id>/spec.md`** | **`Planner`**<br>(可咨询 `Arch`/`Sec`) | **活契约原则 (Living Truth)**：反映当前生效的最新接口与数据结构。 | 原地更新，不留弃用字段，历史交由 Git 追溯；含明确的验收条件编号 (`AC-1, AC-2...`)（模板见 [`templates/spec.template.md`](templates/spec.template.md)）。 |
| **`changes/<id>/tasks.md`** | **`Planner`** (建档)<br>**`TDD` / `Coding`** (勾选) | **微观代码任务清单 (How & Checklist)**：<br>细化到源码模块、函数与测试文件的改造点清单（不含任何运行时状态头，`Dispatcher` 不触碰此文件）。 | 按纵向切片排列 `- [ ]` 勾选框；`tdd` 与 `coding` 每完成一项代码实施即勾选 `- [x]`（模板见 [`templates/tasks.template.md`](templates/tasks.template.md)）。 |
| **`changes/<id>/pipeline.jsonl`** | **`Planner`** (首行 `PLAN`)<br>**`Dispatcher`** (独占续写) | **宏观编排配方 + 运行状态事件流 (Event Sourcing)**：<br>合一承载动态定制的 Agent 工序序列与实时执行轨迹；下游工人严禁写此文件。 | **Append-Only 单行自包含 JSON**：首行 `event:"PLAN"` 记模式、Workspace、端口与定制 `pipeline` 数组；推进追加 `event:"STEP"`；中途变阵追加 `event:"REPLAN"`；随特性结项一并归档为“黑匣子飞行记录仪”（完整规范见 [`protocols/pipeline-and-events.md`](protocols/pipeline-and-events.md)）。 |
| **`changes/<id>/review.md`** | **`Lead Reviewer`** | **单文件权威收敛**：严禁各审查专家私建碎片文件。 | **报纸头条原则 + 四大法定专区**：裁决看板与红黄分级、审查团队与路由依据、工具执行取证清单、契约对账单与防线行号举证 (`Proof of Defense`)，历史轮次用 `<details>` 折叠（模板见 [`templates/review.template.md`](templates/review.template.md)）。 |
| **`changes/<id>/debug.md`** | **`Debug Agent`** | **法医溯源与修复契约**：窗口 2 验收报障、`e2e` 崩溃或终审回归失败时产出。 | 最新一轮置顶：含异常现象、根因定位 (`file:line`)、供 `coding` 执行的《Fix Spec》与供 `tdd` 执行的必补断言（模板见 [`templates/debug.template.md`](templates/debug.template.md)）。 |
| **`changes/<id>/security-poc.md`** | **`Red Team Lead`** | **攻防演练产物**：高危特性触发，隔离沙箱动态渗透。 | 含 STRIDE 威胁类型、CVSS 定级、复现步骤、可直接转化的最小化 PoC 脚本与加固建议。 |
| **`changes/<id>/explore.md`** | **`Explorer`** | **深度代码考古简报**：复杂历史代码摸底时按需产出。 | 浓缩现有模块拓扑、技术债约束与演进可行性评估，保护 `Planner` 上下文不被海量源码污染。 |
| **`reflections/<domain>.md`** | **`Reflector`** | **项目级经验与探索课题库**：结项时由 `pipeline.jsonl` 异常信号触发。 | 按领域归并去重：区分 🎯 `DETERMINISTIC_LESSON`（确定性避坑指南）与 🔬 `SPIKE_CANDIDATE`（交 `Planner` 立项专项 `changes` 实验验证）。 |
| **`.agents/skills/herdr-teamwork/.reflections/<id>.md`** | **`Reflector`** | **Skill 级演进反馈**：记录角色边界模糊、调度卡点或契约缺陷。 | 按 `<id>.md` 独立成文，定位 `SKILL.md` / `roles/*.md` 具体章节并给出修改建议，供本技能库消化吸收。 |

### 2.1 全局文档与汇报「反 AI 腔」准则 (`unslop` 中文版 5 条铁律)
全体角色在撰写任何面向人类或跨角色阅读的文档（`prd.md`、`spec.md`、`review.md`、`debug.md`、`explore.md`、`roundtable.md` 及回场简报）时，严格执行以下去水分铁律：
1. **异项可迁移裁剪测试（Cross-Project Cut Test）**：审视你写的每一句话——**如果这句话原封不动复制到另一个毫不相干的项目文档里依然成立**（如“旨在提供极致的扩展性，确保系统高可用”），说明它对本项目是零信息量废话，**直接删掉**！
2. **写具体机制与数字，不写主观感受（Mechanism & Numbers over Feelings）**：严禁写“大幅提升了性能、让数据触手可及”等空洞形容词；必须写明具体运作机制或实测数字（如“`.toSQL()` 返回发往数据库的精确字符串”、“耗时从 1,240ms 降至 780ms”）。
3. **禁用中文 AI 八股黑话**：严禁堆砌**“赋能、抓手、闭环（泛化滥用时）、底座、护城河、生态、全方位、多维度、至关重要、不言而喻、不仅……更……”**等假大空词汇，一律替换为直白的具体动作（调哪个函数、读写哪个文件、改哪个字段）。
4. **严禁同义词轮换与强行凑三排比（No Synonym Cycling or Forced Triads）**：同一领域概念全篇严格锁定 `GLOSSARY.md` 中的唯一标准名称重复使用（绝不在同一段话里变换两三个近义词）；有 2 个原因就写 2 条，严禁为了排比工整硬凑第 3 条。
5. **主动语态指明责任模块 + 零讨好寒暄**：用主动语态写明行为主体（写“`AuthGuard` 拦截了非法 Token”，而非“Token 被校验并拦截了”）；彻底剔除“这是一个非常好的问题！”、“你完全正确！”等客套寒暄与“**性能优化**：我们对性能进行了优化……”式的粗体复读机列表。

---

## 3. 角色矩阵与职责正交契约 (16 Orthogonal Role Contracts)

全系统划分为**“前店规划层（窗口 1）”**、**“后厂交付与执行层（窗口 2 及各 Workspace）”**与**“分形审查层”**三大正交集群：

| 集群 | 角色 ID (全局统一) | 契约文件 | 核心职责 | 绝对红线 (Hard Boundaries) |
| :--- | :--- | :--- | :--- | :--- |
| **前店<br>规划层** | **`planner`** | [`roles/planner.md`](roles/planner.md) | **产品与架构规划师（窗口 1）**：直面人类聊需求、独占维护 `KANBAN.md`、撰写 `prd/spec/tasks`、动态定制工序并创建 `pipeline.jsonl` 首行 `PLAN`（含上下文策略 `ctx`）。 | **严格工具白名单（仅限 `gitnexus query/context/impact`、读写 `changes/**`、`herdr *`）**；严禁介入后厂排障；严禁未经人类确认擅自压缩或清空上下文。 |
| **前店<br>规划层** | **`explorer`**<br>(项目记忆沉淀) | [`roles/explorer.md`](roles/explorer.md) | **代码探路与可行性预研员**：深入复杂历史源码验证用户想法的现实可行性，输出 `explore.md` 简报并沉淀项目演进心智模型。 | **严格只读权限**；严禁倒灌大段原始源码；`standard` 模式常驻复用（Feature 结项后 `/compact`），`worktree` 模式随工作区销毁。 |
| **后厂<br>执行层** | **`dispatcher`** | [`roles/dispatcher.md`](roles/dispatcher.md) | **交付总控、状态机调度与上下文统筹官（窗口 2 总控 / `ws-<id>` 执行机）**：后台 `tail -f` 监听多任务、内部 `--wait` 阻塞调度、独占续写 `pipeline.jsonl`、替主审拉起/复用专家、通过 `agent-context.py` 在派活前与结项采蜜后统筹全队上下文并同步 `.agents/session.json`。 | **严格工具白名单（仅限 `herdr *`、`agent-context.py`、`session-snapshot.py`、只读契约文件、追加 `pipeline.jsonl`、`git status/diff`）**；**物理蒙眼禁读源码**；一切建场/构建/装包/Git 写操作全归 `ops`。 |
| **后厂<br>执行层** | **`tdd`** | [`roles/tdd.md`](roles/tdd.md) | **测试驱动开发工程师**：在业务编码前依据 `spec.md`、`tasks.md`、`debug.md` 或 `security-poc.md` 编写高严谨度失败用例 (Red Test) 并勾选 `tasks.md`。 | **严禁修改业务代码 (`src/`) 或 `pipeline.jsonl`**；严禁为迎合变绿而弱化断言或编写同语反复假阳性测试。 |
| **后厂<br>执行层** | **`coding`** | [`roles/coding.md`](roles/coding.md) | **业务代码实现者**：依据 `spec.md` / `tasks.md` / `debug.md` 编写业务代码并勾选 `tasks.md`，**主动运行单元与回归测试迭代至全绿 (Green)**，执行编译/类型检查与 `gitnexus detect-changes`。 | **严禁修改任何测试文件 (`tests/`) 或 `pipeline.jsonl`**；严禁私自装包或启停服务（缺包输出 `NEED_OPS`）。 |
| **后厂<br>执行层** | **`ops`**<br>(项目记忆沉淀) | [`roles/ops.md`](roles/ops.md) | **跨语言环境、Worktree 与发布守护者**：遵循“原生命令优先 + 通用调 Skill 脚本 + 仅高频复合痛点按生态沉淀脚本”；负责 Worktree 生命周期、多语言依赖隔离、**切分专属子窗格透明运行守护服务**、环境快照与受控 Git 发布。 | **严禁在自身主窗格前台阻塞运行服务（必须切分子窗格运行）**；**严禁在软链上直接装包污染主目录**；严禁代跑代码审查或单元测试；严禁未授权提前 commit；常驻沉淀环境与构建经验（高水位时 `/compact`）。 |
| **后厂<br>执行层** | **`debugger`**<br>(项目记忆沉淀) | [`roles/debugger.md`](roles/debugger.md) | **法医式排错侦探**：窗口 2 验收报障、`e2e` 崩溃或终审回归失败时出马，利用 `gitnexus` 逆向溯源并输出 `changes/<id>/debug.md`。 | **严格只读权限，绝不亲自动手改代码**；严禁倒灌原始调试日志；`standard` 模式常驻并在高水位或结项后 `/compact` 沉淀项目记忆。 |
| **后厂<br>执行层** | **`security-redteam`**<br>(项目记忆沉淀) | [`roles/security-redteam.md`](roles/security-redteam.md) | **红队渗透测试领队**：STRIDE 威胁建模、白盒污点追踪、隔离沙箱动态渗透，产出 `security-poc.md`。 | **严禁攻击非授权或生产环境**；严禁修改业务代码与标准测试；`standard` 模式常驻并在高水位或结项后 `/compact` 沉淀攻击面记忆。 |
| **后厂<br>执行层** | **`e2e`**<br>(项目记忆沉淀) | [`roles/e2e.md`](roles/e2e.md) | **端到端与冒烟测试专家**：双轨制走查（90% 结合 `E2E_PLAYBOOK.md` 现场冒烟查白屏/Console红字/500错误；10% 黄金链路原子 JS 脚本化）。 | **严禁为日常易变切片制造脆弱脚本债务**；单动作自愈 ≤3 次、总步数 ≤15 步刚性熔断；常驻沉淀页面路由与交互心智，高水位或结项后执行 `/compact`。 |
| **分形<br>审查层** | **`reviewer-lead`** | [`roles/reviewer-lead.md`](roles/reviewer-lead.md) | **主审统筹与裁决官**：独立执行 **Stage 2A 测试快检**；在 **Stage 2B 终审**分诊输出 `SPAWN_EXPERTS` 点将令，回收简报后做 ROI 仲裁并独占签署 `review.md`。 | **严禁亲自运行静态分析/类型编译/测试/`impact`/安全审计**；严禁亲自敲 `herdr pane` 切屏命令；严禁无行号举证的无脑 `APPROVED`。 |
| **分形<br>审查层** | **`reviewer-quality`** | [`roles/reviewer-quality.md`](roles/reviewer-quality.md) | **静态代码质量与健康度过滤官**：独占运行并消化跨语言静态健康度与类型分析工具（TS `fallow+tsc` / Rust `clippy` / Go `golangci-lint` / Python `ruff+mypy`）原始日志，输出 ≤15 行健康简报。 | **严禁向主审倒灌原始终端日志**；**不越界重跑单元测试**；严禁伪造指标；只读权限；由 `Dispatcher` 按水位与 `ctx` 策略统筹 `/compact` 或 `/clear`。 |
| **分形<br>审查层** | **`reviewer-arch`**<br>(项目记忆沉淀) | [`roles/reviewer-arch.md`](roles/reviewer-arch.md) | **系统架构专家**：承接前店 **Stage 1 宏观预审** 与后厂 **Stage 2B 架构终审**；审查深模块设计、单向数据流与 `gitnexus impact` 爆炸半径。 | 必须附带工具取证清单与防线行号举证；只读权限；`standard` 模式常驻并在 Feature 结项后 `/compact` 沉淀架构演进记忆。 |
| **分形<br>审查层** | **`reviewer-perf`**<br>(项目记忆沉淀) | [`roles/reviewer-perf.md`](roles/reviewer-perf.md) | **性能与并发专家**：审查无效重渲染、闭包内存泄漏、N+1 查询、全表扫描与缓存并发安全。 | 必须给出具体瓶颈行号与复杂度推导；只读权限；`standard` 模式常驻并在 Feature 结项后 `/compact` 沉淀性能基线记忆。 |
| **分形<br>审查层** | **`reviewer-security`**<br>(项目记忆沉淀) | [`roles/reviewer-security.md`](roles/reviewer-security.md) | **蓝队安全合规专家**：承接前店安全预审与后厂安全终审；审查注入防御、RBAC/ABAC 越权、供应链 CVE，复核红队 PoC 闭环。 | 对高危漏洞拥有一票否决权；必须附带防御行号举证；只读权限；`standard` 模式常驻并在 Feature 结项后 `/compact` 沉淀安全防线记忆。 |
| **分形<br>审查层** | **`reviewer-ux`**<br>(项目记忆沉淀) | [`roles/reviewer-ux.md`](roles/reviewer-ux.md) | **交互与无障碍专家**：审查快捷键冲突、输入法容错、焦点闭环 (Focus Trap)、ARIA 无障碍属性与界面文案。 | 只读权限；`standard` 模式常驻并在 Feature 结项后 `/compact` 沉淀交互规范记忆。 |
| **反思<br>演进层** | **`reflector`**<br>(全局唯一常驻) | [`roles/reflector.md`](roles/reflector.md) | **流程反思与持续演进官（主区全局单实例）**：当 `pipeline.jsonl` 含波折信号时，在销毁 Worktree/清理上下文前介入，按需跨窗格问询当事 Agent，落盘项目级 `reflections/<domain>.md` 与 Skill 级 `.reflections/<id>.md`。 | **无异常信号不空转**；严禁改源码或在途契约；完成复盘后执行 `/compact` 沉淀跨特性系统性认知。 |

---

## 4. 两阶段审查与证伪式分形审查纲要 (Two-Stage Review & Falsification Summary)

详细分诊路由特征、三拍点将规程与 5 级证据阶梯详见 **[`protocols/review-and-quality.md`](protocols/review-and-quality.md)**（归档模板见 [`templates/review.template.md`](templates/review.template.md)）：
1. **🏛️ Stage 1 计划期宏观预审（窗口 1 按需触发）**：`Planner` 起草完 `spec.md` 后，对照 [`protocols/review-and-quality.md §2`](protocols/review-and-quality.md) 触发特征直接唤醒或复用 `reviewer-arch`/`security`/`perf`/`ux` 预审（重大单向门多方案分歧升级为 [`playbooks/roundtable-debate.md`](playbooks/roundtable-debate.md) 圆桌辩论）。
2. **🔬 Stage 2 实施期双门禁（后厂强制触发）**：
   - **Stage 2A（测试前置快检）**：`tdd` 写完 Red Test 后由 `reviewer-lead` 独立执行硬编码证伪快检；
   - **Stage 2B（实现终审三拍闭环）**：`reviewer-lead` 按 [`protocols/review-and-quality.md §2`](protocols/review-and-quality.md) 特征矩阵输出 `SPAWN_EXPERTS` 点将令 ➔ `dispatcher` 并发调度专家回收简报 ➔ `reviewer-lead` 按 **5 级证据阶梯** 仲裁并落盘 `review.md`。
3. **🛡️ 防线行号举证 (`Proof of Defense`) + 🚦 红黄三级定性**：批准前必须贴出防御最脆弱边界的确切 `file:line`；审查意见严格分为 🔴 `BLOCKER`（打回返工，≤2 轮熔断）、🟡 `CONSTRUCTIVE`（不阻断放行，记入 `pipeline.jsonl` 经人类确认后转入 `KANBAN.md` Inbox）与 ⚪ `NITPICK`（严禁输出）。

---

## 5. 双控台分治、事件流与上下文统筹总览 (Dual-Console, Event Stream & Context Orchestration)

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
        Worker[Dispatcher 执行机<br/>同步 --wait 驱动 + 独占续写 pipeline.jsonl]
        Worker -->|prompt --wait| TDD[1. TDD: 写 Red Test 勾选 tasks.md]
        TDD --> Rev2A[2. Lead Reviewer: Stage 2A 测试快检]
        Rev2A --> Coding[3. Coding: 实现至局部 Green 勾选 tasks.md]
        Coding --> Rev2B[4. Stage 2B 终审: 三拍点将 + 全量回归]
        Rev2B -.->|按需走查| E2E[5. E2E: 双轨冒烟走查]
        Rev2B & E2E -->|追加 WAITING_ACCEPTANCE| EventLog
    end

    Master ==>|验收报障: 追加 REPLAN 事件| BugLoop[debugger 产出 debug.md ➔ tdd ➔ coding ➔ review]
    Master ==>|验收通过: 授权发布| Release[ops 构建/Commit/合入 ➔ 异常信号按需调 reflector 复盘 ➔ 销毁/清理收尾并追加 DONE]
```

### 5.1 四大核心协同协议路由 (`protocols/`)
为保证全局宪章精炼并支持跨角色按需查阅，流水线编排、两阶段审查、上下文水位治理与环境算力规范沉淀于 [`protocols/`](protocols/) 四大核心协议中：

| 协议文件 | 适用角色 | 核心涵盖机制 |
| :--- | :--- | :--- |
| **[`protocols/pipeline-and-events.md`](protocols/pipeline-and-events.md)** | `planner`, `dispatcher`, `ops` | **流水线预设、事件流与故障自愈协议**：7 大动态可调流水线预设模板、`changes/<id>/pipeline.jsonl` 8+ 字段单行 JSON 规范与 6 态状态机枚举、下游故障自愈三步法及 `Master Dispatcher` 跨流水线 `tail -f` 监听配方。 |
| **[`protocols/review-and-quality.md`](protocols/review-and-quality.md)** | `planner`, `dispatcher`, `reviewer-lead`, `reviewer-*` | **两阶段审查、专家分诊路由与证伪裁决协议**：Stage 1 预审与圆桌辩论、Stage 2A/2B 三拍点将闭环、**《垂直专家具象触发特征矩阵》**、5 级证据阶梯过滤、`Proof of Defense` 防线行号举证与 `BLOCKER / CONSTRUCTIVE / NITPICK` 红黄三级定性。 |
| **[`protocols/context-and-budget.md`](protocols/context-and-budget.md)** | `dispatcher`, `planner`, `bootstrap` | **多 Agent 上下文主动统筹与水位预算协议**：[`scripts/agent-context.py`](scripts/agent-context.py) 双通道水位探针、`Tier S/A/B` 70%/60%/50% 黄金比例法则与思考等级微调表、`Arm/Fire` 稳态点火双窗口、三域统筹权责矩阵及压缩后强制重读 `roles/<role>.md` 重载锁。 |
| **[`protocols/model-tiers-and-env.md`](protocols/model-tiers-and-env.md)** | `bootstrap`, `planner`, `dispatcher`, `ops` | **四档算力画像与运行时配置字典协议**：16 角色的四档算力诉求与思考深度画像表、`.agents/environment.json` 字段字典（配合 [`templates/environment.example.json`](templates/environment.example.json)）以及 `.agents/session.json` 会话快照字段字典（配合 [`templates/session.example.json`](templates/session.example.json)）。 |

---

## 6. Herdr 编排指令配方与智能代码导航 (`tools/herdr.md` & Code Intelligence)

### 6.1 Herdr 终端与 Agent 编排指令速查 (`tools/herdr.md`)
`dispatcher`、`ops`、`planner`、`reflector` 角色及 `bootstrap-teamwork`、`roundtable-debate` 剧本必读 **[`tools/herdr.md`](tools/herdr.md)**，严格遵照 `§[H-1]` ~ `§[H-6]` 执行：

| 编排场景 | 唯一权威指令配方章节 | 核心机制要点 |
| :--- | :--- | :--- |
| **切分窗格与创建标签页** | **[`tools/herdr.md §[H-1]`](tools/herdr.md)** | 统一携带 `--no-focus`，并通过 `jq -r` 提取 `.result.pane.pane_id` 或 `.result.root_pane.pane_id`。 |
| **角色启动、快照导出与跨天复活** | **[`tools/herdr.md §[H-2]`](tools/herdr.md)** | 从 `.agents/environment.json` 展开 `cli_args` 透传；通过 [`scripts/session-snapshot.py`](scripts/session-snapshot.py) `save / restore / prune` 增量保存与一键恢复实时模型/思考深度/会话上下文。 |
| **事件驱动派发、等待与读取** | **[`tools/herdr.md §[H-3]`](tools/herdr.md)** | **纯事件驱动等待**，默认自动匹配 `idle \| done \| blocked` 三种终态唤醒；使用 `--source recent-unwrapped` 读取输出。 |
| **Worktree 平行工作区建场与回收** | **[`tools/herdr.md §[H-4]`](tools/herdr.md)** | 调 [`scripts/worktree-up.sh`](scripts/worktree-up.sh) ➔ `herdr workspace create --label "ws-<id>"` ➔ 启动全局唯一带后缀角色名（如 `dispatcher-001`、`coding-001`）；销毁时调 [`scripts/worktree-down.sh`](scripts/worktree-down.sh) 自动从 `session.json` 清理已下线角色。 |
| **后台服务守护子窗格 (`.ops-pane`)** | **[`tools/herdr.md §[H-5]`](tools/herdr.md)** | 在 `ops` Tab 内切分子窗格并存入 `.ops-pane`，用 `pane run` 与 `pane wait-output` 驱动常驻开发服务。 |
| **上下文探针、主动压缩与窗格回收** | **[`tools/herdr.md §[H-6]`](tools/herdr.md)** | 调 [`scripts/agent-context.py`](scripts/agent-context.py) 巡检水位（并自动保鲜 `session.json`）、发送 EESV `compact_cmd`/`clear_cmd`、`send-keys ctrl+c` 中断重试，或通过 `herdr pane close` 关闭窗格。 |

### 6.2 智能代码定位与图谱导航规范 (Code Intelligence & Navigation)
遵循**“图谱定位先行、精准切片读取”**原则，严禁盲目全量通读大文件：

| 场景与意图 | 首选工具 | 说明与使用范式 | 典型调用者 |
| :--- | :--- | :--- | :--- |
| **已知符号查行号与上下游** | **`gitnexus context`** | 秒级锁定定义文件、起止行号与 360 度调用拓扑。 | `planner`, `explorer`, `coding`, `debugger` |
| **探索未知业务执行流** | **`gitnexus query`** | 输入简短英文概念词（如 `"user auth"`），获取跨层执行拓扑。 | `planner`, `explorer`, `debugger` |
| **评估改动爆炸半径** | **`gitnexus impact`** | `gitnexus impact -d upstream <symbol>` 追溯上游调用方与受波及流程。 | `reviewer-arch`, `coding`, `explorer` |
| **验证改动范围与越界门禁** | **`gitnexus detect-changes`** | 将 Git Diff 映射到符号与业务流，形成**三重防线**（Coding 自检 ➔ Lead Reviewer 终审分诊 ➔ Ops 提交前 staged 拦截）。 | `coding`, `reviewer-lead`, `ops` |
| **查文案或精准报错字面量** | **`rg -n` (ripgrep)** | 毫秒级锁定 UI 文案、错误码或环境变量所在行号。 | 除 `dispatcher` 外的全体探查/实现角色 |
