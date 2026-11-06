---
name: herdr-teamwork
description: Multi-agent spec implementation orchestrated via Herdr terminal panes, workspaces, and optional Git Worktrees (Planner, Explorer, Dispatcher, TDD, Coding, Reviewer Ensemble, Ops, Debugger, RedTeam, E2E, Reflector). Use when initiating multi-agent spec implementation, parallel feature development, or complex engineering workflows.
---

# Herdr Multi-Agent Teamwork (多 Agent 协同工程规范 v2.9.0)

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
│       ├── playbooks/               # 【How】11 个按需触发的专项战术剧本 (含 bootstrap-teamwork 初始化自举，跨角色共享)
│       ├── tools/                   # 【CLI】Herdr 编排与窗格控制唯一权威指令配方卡 (tools/herdr.md §[H-1]~§[H-6])
│       ├── scripts/                 # 【Tools】跨项目通用 Worktree 建场/销毁与上下文水位探针脚本 (worktree-up.sh / worktree-down.sh / agent-context.sh)
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

| 文档路径 | 唯一写入人 (Writer) | 定位与维护机制 | 格式范式与流转准则 |
| :--- | :--- | :--- | :--- |
| **`GLOSSARY.md`** | **`Planner`** | **项目级统一领域语言 (Ubiquitous Language)**：<br>全项目常驻标准工件，消除 16 个 Agent 间的概念命名漂移。 | 只定义核心业务概念边界与禁用同义词表；**严禁混入类名、文件路径或数据库表名等实现细节**。 |
| **`E2E_PLAYBOOK.md`** | **`E2E Agent`**<br>(`Planner` 初始化) | **端到端验证路由与源码映射剧本 (按需工件)**：<br>仅在项目启用 `e2e` 角色时创建，免去每次测试或排障重新摸索 DOM 与源码路径。 | 按 **6 要素结构化记录**（`feature_id`、`entry_point` 源码路径、`user_route`、`dom_selectors`、`keyboard_shortcuts`、`gotchas`），每次验收通过后增量更新。 |
| **`docs/adr/<id>.md`** | **`Planner`** | **架构决策记录 (Selective ADRs)**：<br>记录深远架构取舍，防止后续 Agent 因不解背景而回退设计。 | **严格 3 条件门禁**（同时满足才写）：① 难以逆转；② 缺乏背景看代码会感到惊讶；③ 存在真实的方案权衡（Trade-off）。 |
| **`changes/KANBAN.md`** | **`Planner` 独占** | **全局大盘单文件内聚（含规划台交接备忘）**：<br>严禁私建碎片化 `Inbox.md`；未开展需求第一时间入池占位；结项与 `CONSTRUCTIVE` 建议仅在人类确认后由 `Planner` 录入；底部常设 `📌 规划台交接备忘 (Planner Handoff)` 供高水位传位「Planner 二世」。 | **需求未启，看板先行**：<br>- 状态流转：`📥 占位池 (Inbox/Backlog)` ➔ `🚀 进行中 (In Progress)` ➔ `✅ 已完成 (Done)`；<br>- 依赖与并发前沿：多任务间显式标注 `[Blocked by: <id>]`，无未决阻塞项的即构成可并发启动 Worktree 的 **Ready Frontier**。 |
| **`changes/<id>/prd.md`** | **`Planner`** | **产品诉求 (Why & What)**：需求调整直接在原文就地演进。 | 文末附 2~3 行简明 `## 变更备忘录 (Changelog)` 记录妥协或调整原因。 |
| **`changes/<id>/spec.md`** | **`Planner`**<br>(可咨询 `Arch`/`Sec`) | **活契约原则 (Living Truth)**：反映当前生效的最新接口与数据结构。 | 原地更新，不留弃用字段，历史交由 Git 追溯；含明确的验收条件编号 (`AC-1, AC-2...`)。 |
| **`changes/<id>/tasks.md`** | **`Planner`** (建档)<br>**`TDD` / `Coding`** (勾选) | **微观代码任务清单 (How & Checklist)**：<br>细化到源码模块、函数与测试文件的改造点清单（不含任何运行时状态头，`Dispatcher` 不触碰此文件）。 | 按纵向切片排列 `- [ ]` 勾选框；`tdd` 与 `coding` 每完成一项代码实施即勾选 `- [x]`。 |
| **`changes/<id>/pipeline.jsonl`** | **`Planner`** (首行 `PLAN`)<br>**`Dispatcher`** (独占续写) | **宏观编排配方 + 运行状态事件流 (Event Sourcing)**：<br>合一承载动态定制的 Agent 工序序列与实时执行轨迹；下游工人严禁写此文件。 | **Append-Only 单行自包含 JSON**：<br>- 首行 `event:"PLAN"` 记模式、Workspace、端口与定制 `pipeline` 数组；<br>- 推进追加 `event:"STEP"`；中途变阵追加 `event:"REPLAN"`；<br>- 随特性结项一并归档为“黑匣子飞行记录仪”。 |
| **`changes/<id>/review.md`** | **`Lead Reviewer`** | **单文件权威收敛**：严禁各审查专家私建碎片文件。 | **报纸头条原则 + 四大法定专区**：<br>1. 裁决看板与红黄分级 (`APPROVED` / `CHANGES_REQUESTED`)；<br>2. 审查团队与路由依据；<br>3. 工具执行取证清单；<br>4. 契约对账单与防线行号举证 (`Proof of Defense`)。历史轮次用 `<details>` 折叠。 |
| **`changes/<id>/debug.md`** | **`Debug Agent`** | **法医溯源与修复契约**：窗口 2 验收报障、`e2e` 崩溃或终审回归失败时产出。 | 最新一轮置顶：含异常现象、根因定位 (`file:line`)、供 `coding` 执行的《Fix Spec》与供 `tdd` 执行的必补断言。 |
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
| **后厂<br>执行层** | **`dispatcher`** | [`roles/dispatcher.md`](roles/dispatcher.md) | **交付总控、状态机调度与上下文统筹官（窗口 2 总控 / `ws-<id>` 执行机）**：后台 `tail -f` 监听多任务、内部 `--wait` 阻塞调度、独占续写 `pipeline.jsonl`、替主审拉起/复用专家、通过 `agent-context.sh` 在派活前与结项采蜜后统筹全队上下文。 | **严格工具白名单（仅限 `herdr *`、`agent-context.sh`、只读契约文件、追加 `pipeline.jsonl`、`git status/diff`）**；**物理蒙眼禁读源码**；一切建场/构建/装包/Git 写操作全归 `ops`。 |
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

## 4. 两阶段审查体系与证伪式分形审查矩阵 (Two-Stage Review & Falsification Protocol)

为彻底根治“带着宏观架构硬伤进入编码”、“Lead Reviewer 偷懒不派活”以及“Reviewer 走过场无脑 Approve（Rubber Stamping）”，建立**两阶段、三拍点将、证伪举证与红黄分级**体系：

### 4.1 两阶段审查全链路划分
1. **🏛️ 第一阶段：计划期宏观与架构预审 (Stage 1: Macro & Arch Consultation —— 窗口 1 按需触发)**
   - **触发时机**：`Planner` 起草完 `changes/<id>/spec.md` 后，若涉及跨模块架构重构、核心数据模型演进或高危安全机制，在呈交人类最终拍板前触发（常规轻量需求可跳过）。
   - **执行方式**：**略过 `reviewer-lead`**，由 `Planner` 直接按需唤醒或复用 **`reviewer-arch`** 或 **`reviewer-security`**，评估深模块合理性与 `gitnexus impact` 爆炸半径，将宏观修正直接融入 `spec.md` 并记录于 `review.md` Stage 1 章节（`standard` 模式下窗格常驻保留上下文至 Feature 结项）。
    - **升级形态：圆桌辩论 (Roundtable Debate)**：当议题同时满足「单向门 + 跨 ≥2 个专业维度显著权衡 + 2~3 套互斥候选方案」时，`Planner` 立题并 Fork 一个**一次性圆桌主席分身**（非常驻角色，加载 [`playbooks/roundtable-debate.md`](playbooks/roundtable-debate.md)），由其组织 2~4 位专家「背靠背亮牌 ➔ 冲突方定向交锋(1 轮) ➔ 主席裁决」，落盘 `changes/<id>/roundtable.md` 后分身退出；`Planner` 向人类呈报裁决摘要，**人类点头后**方固化进 `spec.md` 与 `docs/adr/`。
2. **🔬 第二阶段：实施期测试与代码细节/防偏离终审 (Stage 2: Implementation & Drift Gate —— 后厂强制门禁)**
   - **子阶段 2A：测试代码前置快检 (Red Test Gate)**：在 `tdd` 写完 Red Test 后、`coding` 动手前，由 **`reviewer-lead` 独立执行**（仅在涉及红队 PoC 转化时点名 `reviewer-security` 协审）。严格按《4 维测试审查清单》与“硬编码证伪法”拦截弱断言与契约偏差。
   - **子阶段 2B：业务实现与防偏离终审 (Code & Drift Gate)**：在 `coding` 自证测试全绿后触发，实行**“主审开方点将 ➔ Dispatcher 抓药调度 ➔ 主审合议裁决”**三拍闭环：
     - **第 1 拍（主审分诊点将）**：`reviewer-lead` 仅运行 `git diff --stat` 与 `gitnexus detect-changes`（**严禁自己跑静态质量分析、编译检查、测试或 `impact`**）。若属 Tier 1（<20 行纯文档/文案/样式微调），直接签字放行；若属 Tier 2/3，立即向终端输出一行点将令并结束回合：
       `TRIAGE_RESULT: Tier 2 | SPAWN_EXPERTS: [reviewer-quality, reviewer-perf] | FOCUS: "核查 xxx 模块"`
     - **第 2 拍（Dispatcher 并发代跑）**：`dispatcher` 解析点将令，复用已常驻的专家窗格（若首次调用则切出对应专家 Pane）、传入 `FOCUS` 指令并 `wait` 等待，收集 ≤25 行专家简报（`standard` 模式下保留专家窗格至当前 Feature 结项后统一打理上下文；`worktree` 模式下可即用即关或随工作区销毁）。
     - **第 3 拍（主审 ROI 仲裁与落盘）**：`dispatcher` 将全部专家简报喂回 `reviewer-lead`，由主审权衡冲突、剔除吹毛求疵，统一写入 `changes/<id>/review.md`。

### 4.2 垂直专家具象触发特征矩阵 (Concrete Routing Heuristics)
`reviewer-lead` 在第 1 拍分诊时，严格依据以下客观特征组合点名专家：

| 专家角色 ID | 具象触发条件（命中任一特征即必须点名唤起） |
| :--- | :--- |
| **`reviewer-quality`** | **凡改动包含任何业务源码 (`src/`) 或测试代码 (`tests/`)**（非纯文档/注释微调），100% 必调！负责跑跨语言对等静态代码健康度与类型分析（TS `fallow+tsc` / Rust `clippy` / Go `golangci-lint` / Python `ruff+mypy`）。 |
| **`reviewer-arch`** | 1. `gitnexus detect-changes` 显示风险 `>= MEDIUM` 或波及业务流 `>= 2` 个；<br>2. 触及公共核心层、全局状态管理或数据库 Schema；<br>3. 跨 `>= 3` 个模块目录修改，或怀疑实现偏离了 `spec.md` 既定架构边界。 |
| **`reviewer-security`** | 1. 触及认证鉴权、权限守卫、加密脱敏、资金/计费/敏感状态流转；<br>2. 含数据库查询、文件 I/O、系统命令执行、富文本渲染或新增外部 API；<br>3. 修改了项目依赖清单（`Cargo.toml` / `go.mod` / `pyproject.toml` / `package.json`），或当前变更集存在 `security-poc.md`。 |
| **`reviewer-perf`** | 1. 数据层涉及循环内查询、大表查询、索引/缓存策略或并发锁；<br>2. 视图层涉及高频事件监听、定时器、海量节点渲染或复杂闭包。 |
| **`reviewer-ux`** | 1. 涉及前端交互组件、弹窗模态框、表单校验或布局样式；<br>2. 涉及键盘快捷键流、焦点捕获管理 (Focus Trap)、无障碍属性或用户提示文案。 |

### 4.3 防橡皮图章与防过度挑刺双保险：证伪举证 + 红黄分级
1. **🛡️ 核心防线证伪核查 (Proof of Defense —— 杜绝无脑 Approve)**：
   - 任何 Reviewer 在给予通过前，必须在报告中明确指出本次改动**最脆弱的边界/异常点**，并**贴出源码或测试中实施防御的确切文件名与行号 (`file:line`)**。拿不出确切防御行号，严禁给予 `APPROVED`。
2. **🚦 审查意见三级定性 (Severity Triage —— 杜绝过度挑刺与看板污染)**：
   - 🔴 **`[BLOCKER / 致命阻断]`**：违背 `spec.md` 契约、存在安全/崩溃/泄漏漏洞、测试假阳性、缺少核心边界防御或静态质量退化（如 `fallow delta > 0` / `clippy` 报错 / `golangci-lint` 报错）。➔ **触发 `CHANGES_REQUESTED` 打回返工（最多允许 2 轮返工，超限挂起为 `WAITING_DECISION` 交人类裁决）**。
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
    Master ==>|验收通过: 授权发布| Release[ops 构建/Commit/合入 ➔ 异常信号按需调 reflector 复盘 ➔ 销毁/清理收尾并追加 DONE]
```

### 5.1 动态可调流水线预设模板与专项战术剧本 (Customizable Pipeline Presets & Tactical Playbooks)
通道仅作为**基础预设起点**，`Planner` 在【法定节点 1】必须展示拟启用的具体角色数组 `pipeline`，支持人类按需动态增删插件化调节：
- **微型轻量预设 (`Quick-Fix`)**（<20 行 / 纯文案 / 纯样式 / 简单配置）：`["coding", "reviewer-lead:2B", "ops"]`
- **标准功能预设 (`Standard`)**（20~150 行 / 局部新特性 / 常规组件）：`["tdd", "reviewer-lead:2A", "coding", "reviewer-lead:2B", "ops"]`（可按需插拔 `"e2e"`）
- **全量高危预设 (`Full-Rigor`)**（核心架构 / 鉴权计费 / 数据库迁移）：`Stage 1 预审` + `["tdd", "reviewer-lead:2A", "coding", "security-redteam", "tdd", "coding", "reviewer-lead:2B", "e2e", "ops"]`
- **探索性原型刺探预设 (`[SPIKE]`)**（UI/交互方案对比或技术可行性刺探，用完即焚）：`["coding", "ops"]`（跳过 `tdd` 与代码规范审查，详见 [`playbooks/prototype-spike.md`](playbooks/prototype-spike.md)，拍板后销毁临时分支）
- **单一指标科学爬山预设 (`[HILLCLIMB]`)**（针对耗时/内存/吞吐量等单一量化指标执行“测基线-改代码-退步即回滚”循环）：`["coding", "reviewer-perf", "ops"]`（详见 [`playbooks/hillclimb.md`](playbooks/hillclimb.md)）
- **阶段性全库架构深度巡检 (`Arch-Audit`)**（每完成 3~5 个特性扫描浅模块并产出 HTML 体检报告）：`["reviewer-arch"]`（必要时协同 `"explorer"`，详见 [`playbooks/arch-audit.md`](playbooks/arch-audit.md)）
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
当 `Dispatcher` 执行等待发生异常时，**严禁越权代庖**，必须严格按 [`tools/herdr.md §[H-6]`](tools/herdr.md) 依次执行：
1. **观察与中断重试**：先读取目标状态与最近输出检查是否仍在正常 `working`；若确系卡死，发送 `ctrl+c` 中断当前回合并确认恢复就绪后重试。
2. **重建窗格重启进程**：若重试无效，切分新窗格并关闭旧异常窗格，重新启动该角色实例恢复会话。
3. **挂起上报**：若自愈仍失败，`Dispatcher` 向 `changes/<id>/pipeline.jsonl` 追加 `"state": "STALLED"` 事件并上报窗口 2。

### 5.4 多 Agent 上下文主动统筹管理架构 (Proactive Multi-Agent Context Orchestration)
为彻底根治「不知当前水位」、「刚发命令或任务做到一半撞上 ~90% 被动自动压缩导致失忆」、「提前清空误伤 `Reflector` 采蜜」以及「压缩后遗忘角色契约与命令规范」四大痛点，建立 **「双通道水位探针 + 动态智力阈值 + Arm/Fire 稳态边界点火 + 三域统筹矩阵 + 压缩后强制重载锁」** 完整体系：

#### 1. 双通道水位探针 (`scripts/agent-context.sh`) 与「70% / 60% / 50% 黄金比例法则」
通过 [`scripts/agent-context.sh`](scripts/agent-context.sh) 跨 Harness 实时获取各窗格的精确上下文消耗、当前模型、**实际自动压缩窗口 (`WIN`)** 与**思考等级 (`THINK`: `off/low/medium/high/xhigh`)**（优先读取 `herdr-agent-usage` 插件的 StatusLine 缓存/Metadata；兜底通过 `herdr agent list` 的 `agent_session.value` 绑定本地 `.jsonl` 会话文件执行 **256KB 有界尾部倒扫 `tail -c 262144`**，并结合窗格底部状态栏与配置文件自动识别模型与思考深度）。
- **两个水位的直白定义**：
  - **`WIN`（自动压缩死线）**：Harness 触发强制自动压缩的实际会话上限（注意：部分 Harness 如 `agy` 虽底层模型支持 1M，但客户端固定在 **`262k` (`262,144`)** 触发自动压缩，故 `WIN` 必须以实际自动压缩死线为准）；
  - **`🟡 ARMED`（趁空闲压缩线）**：**不打断当前在途任务**；提醒 `Dispatcher` 趁任务刚结束处于 `idle` 空闲边界时顺手发起主动压缩；
  - **`🔴 DANGER`（派活前必压红线）**：距离自动压缩死线过近，**派发下一条指令前必须先完成压缩**，否则任务做一半必撞上自动压缩。
- **极简三维分档规则（以 `medium` 思考为基准：`70% / 60% / 50%`；`high` 思考 `+5%`，`low` 思考 `-8%`）**：

| 模型智力与抗衰档位 | 宏观模型特征画像（不绑定易过时的具体模型名） | `medium` 思考压缩水位 (`🟡 ARMED` / `🔴 DANGER`) | 思考等级微调规律 (`low` / `high`) | 典型窗口换算示例 |
| :--- | :--- | :---: | :---: | :--- |
| **Tier S：高智商旗舰档** | 大规模前沿深度推理旗舰模型，逻辑链深、最抗长文噪音干扰 | • **`70%`** 趁空闲压 (`ARMED`)<br>• **`80%`** 派活前必压 (`DANGER`) | • `low`：`62%` / `73%`<br>• `high`：`75%` / `85%` | 以 **`262k` 窗口** 为例：<br>• `low`：`162k` / `191k`<br>• **`medium`：`183k` / `209k`**<br>• `high`：`196k` / `222k` |
| **Tier A：主力全能编码档** | 大规模通用或主力编码模型（含大型 MoE 及高速长窗主力模型），太长时易遗忘边缘细节 | • **`60%`** 趁空闲压 (`ARMED`)<br>• **`72%`** 派活前必压 (`DANGER`) | • `low`：`52%` / `65%`<br>• `high`：`65%` / `77%` | 以 **`262k` 窗口** 为例：<br>• `low`：`136k` / `170k`<br>• **`medium`：`157k` / `188k`**<br>• `high`：`170k` / `201k` |
| **Tier B：中等参数开源 / 轻量档** | 十余 B 至数十 B 参数级开源模型或轻量高速模型（**铁律：物理大窗口 ≠ 高有效智力上限**，长文易降智，需勤压快跑） | • **`50%`** 趁空闲压 (`ARMED`)<br>• **`62%`** 派活前必压 (`DANGER`)<br>*(超大窗下 `ARMED` 最高封顶 `90k~100k`)* | • `low`：`42%` / `55%`<br>• `high`：`55%` / `67%` | 以 **`163k` 窗口** 为例：<br>• `low`：`68k` / `89k`<br>• **`medium`：`81k` / `101k`**<br>• `high`：`90k` / `109k` |

#### 2. 侦测武装与稳态点火分离 (`Arm / Fire Separation` —— 两大最佳点火窗口)
严禁在任务执行中途打断压缩，也严禁在 `Reflector` 复盘前盲目清理。实行 **「双通道侦测武装 (Arm) + 仅在 `idle`/`done` 稳态边界点火 (Fire)」**：
- **双通道武装 (Arm)**：① **数值通道**：`agent-context.sh` 报 `🟡 ARMED` 或 `🔴 DANGER`；② **语义通道**：`pipeline.jsonl` 的 `PLAN` 事件标注了 `"ctx": "compact"` 或 `"ctx": "clear"`。
- **稳态点火窗口 A：派活前水位闸门 (`Pre-Dispatch Gate` —— 支持 `strict` / `relaxed` 双档松紧度)**：
  `Dispatcher` 按 `.agents/environment.json` 中 `context_monitor.probe_policy` 设定的策略执行派活前检查：
  - **`"strict"`（严格逐步必检，适合 Tier B 开源/短窗模型、挂载了外部自动压缩插件或大颗粒度特性）**：每次唤醒下游角色前均执行 `agent-context.sh <role>`；
  - **`"relaxed"`（宽松按需抽检，适合大窗口 Tier S/A 模型与常规小切片）**：利用结项全检建立底数，常规 `round == 1` 顺畅推进中途免检；仅当进入多轮返工（`round >= 2` / `REPLAN`）或某角色开局距 `ARMED` 不足 `35k` 且被二次唤醒前才执行单点抽检。
  一旦检出目标角色处于 `🔴 DANGER`（或处于 `🟡 ARMED` 且即将派发重度任务），**必须先下发 `compact_cmd` 并 `--wait` 完成后，再下发业务任务指令**，从根源消灭「刚发命令就自动压缩」与「任务做一半自动压缩」。
- **稳态点火窗口 B：特性结项且 `Reflector` 采蜜完成后的空闲窗口 (`Post-Reflector Idle Window`)**：
  1. **🔒 `Reflector` 采蜜保护锁**：当特性包含波折信号需触发 `Reflector` 时，在 `Reflector` 跨窗格访谈并落盘经验之前，**严禁对任何参与角色执行压缩或清空**，保留 100% 原始排障现场；
  2. **⏱️ 等待挪位 (`Shift the Wait`)**：待 `Reflector` 采蜜完成（或无波折直接结项）进入 `DONE` 后，由 `Dispatcher` 对所有已达 `🟡 ARMED`（或命中 `PLAN.ctx == "compact"`）的常驻角色发起主动压缩，将 20~60 秒的压缩耗时隐藏在特性切换的空闲间隙中。

#### 3. 三域统筹权责矩阵与防失忆重载锁 (`3-Domain Matrix & Post-Compaction Reload Lock`)

| 治理域与覆盖角色 | 统筹发起人 | 何时 `/compact`（EESV 结构化提纯） vs 何时 `/clear`（清空并重塑） | 压缩后防失忆闭环 (`Reload Lock`) |
| :--- | :--- | :--- | :--- |
| **域 1：后厂与审查全员 (14 个)**<br>`tdd`, `coding`, `ops`, `e2e`, `debugger`, `explorer`, `security-redteam`, `reviewer-*`, `reflector` | **`Dispatcher`<br>集中统筹** | • **全员默认优先 `/compact`（含 `ops`、`e2e`）**：各角色在运行中均会积累宝贵的环境、路由与代码拓扑经验，绝不每完结一个特性就无脑清空；在「派活前闸门」或「采蜜后空闲期」发送带 **EESV 四要素锚点**（Ground Truth / Continuity Ledger / Open Loops / Delta）的 `compact_cmd`；<br>• **仅在 2 种场景下执行 `Clear & Re-Prime`（`/clear` + 立即重读角色书）**：① 跨完全无关业务大域（`PLAN.ctx == "clear"` 且 `Reflector` 已完成）；② 角色陷入死循环或上下文被错误尝试严重污染（`STALLED`）。 | 若 `Dispatcher` 刚刚对其执行了主动压缩，或 `agent-context.sh` 检测到 `+JUST_COMPACTED`（上一轮刚经历了自动压缩断崖：`curr < prev * 0.6`），`Dispatcher` 在下发下一条指令时**必须在开头强制附带「请先调用读取工具重读 `roles/<role>.md`」**！ |
| **域 2：中枢调度官 (1 个)**<br>`dispatcher` 自身 | **`Dispatcher` 自检<br>+ 顶层 `AGENTS.md`** | `Dispatcher` 在特性结项或派活间隙运行 `agent-context.sh` 时同步检查自身水位；若达 `🟡 ARMED`，在特性间空闲期主动触发自压缩（或向人类汇报后压缩）。 | **顶层 `AGENTS.md` 布尔判据强制重载锁**：任何角色一旦发现上下文顶部存在自动压缩摘要（如 `<CONTEXT_SUMMARY>`），且**在该摘要之后的未压缩记录中未曾调用读取工具读过自身 `roles/<role>.md` 原文**，第 1 个动作必须无条件重读 `roles/<role>.md` 与 `tools/herdr.md`！ |
| **域 3：前店规划官 (1 个)**<br>`planner` (窗口 1) | **人类主导<br>+ `Planner` 提议** | **`Dispatcher` 严禁从后台触碰窗口 1 上下文**！实行阶段分治：<br>• **讨论未落盘中途高水位** ➔ 提议人类执行原地 `/compact`；<br>• **契约落盘后里程碑高水位** ➔ 向 `changes/KANBAN.md` 的 `📌 规划台交接备忘` 区写入 **EESV 四要素交接单**（① 已落盘契约路径 Ground Truth；② 人类偏好与否决废案 Continuity Ledger；③ 未决悬念 Open Loops；④ 本轮增量 Delta），经人类确认后执行 `/clear` + 重读 `roles/planner.md` 满血唤醒 **「Planner 二世」**。 | 「Planner 二世」启动首回合直接读取 `roles/planner.md`、`tools/herdr.md`、`GLOSSARY.md` 与 `KANBAN.md` 交接备忘，实现 100% 零噪音无缝继任。 |

---

## 6. 项目自举初始化与异构环境画像 (`.agents/environment.json`)

首次在项目中启用本技能（或重配团队模型与工具链）时，由当前终端中的**一次性临时引导实例（`Bootstrap Agent`）**读取并执行 **[`playbooks/bootstrap-teamwork.md`](playbooks/bootstrap-teamwork.md)**：自动探测宿主机已安装的 CLI (`claude`, `codex`, `agy`, `pi`, `hermes`) 与静态工具链，按以下**四档算力画像**与人类灵活敲定模型分配（而非死板绑定固定模型名），落盘 `.agents/environment.json` 与活文档骨架，拉起 `Planner` + `Dispatcher` + `Ops` 常驻窗格后关闭临时引导窗格功成身退：

| 角色集群与 ID | 核心算力诉求 | 优选 Harness 倾向参考 | 理想思考深度 (Thinking) |
| :--- | :--- | :--- | :--- |
| **`planner` / `reflector` / `explorer` / `debugger` / `security-redteam` / `reviewer-lead` / `reviewer-arch` / `reviewer-perf` / `reviewer-security`** | 高维架构抽象、元认知复盘、法医式逆向溯源、攻防博弈与证伪裁决 | 当前可用池中逻辑推理最强的 Harness 与模型 (`claude-code` / `codex` / `agy`) | **High** (深度推理) |
| **`coding` / `tdd` / `reviewer-ux`** | 严格契约遵从、边界用例推演、精准行级实现与交互审计 | 代码生成精准且速度均衡的主力模型 (`codex` / `claude-code` / `agy`) | **Medium** (适度推断) |
| **`e2e`** | 极速 DOM/A11y 树理解、页面语义自愈与冒烟走查 | 挂载了 `chrome-devtools-mcp` 且响应迅速的模型 (`agy` / `claude-code` / `pi`) | **Low ~ Medium** (极速自愈) |
| **`dispatcher` / `ops` / `reviewer-quality`** | 毫秒级状态机流转、确定性建场发布、海量原始日志吞吐过滤 | 延迟最低、Token 最经济的轻量 Harness 与模型 (`pi` / `hermes` / `agy`) | **None / Low** (零延迟确定性) |

### `.agents/environment.json` 标准完整结构与字段字典
```json
{
  "updated_at": "2026-11-05T00:00:00Z",
  "mode": "standard",
  "default_ctx": "compact",
  "runtime_type": "daemon_port",
  "base_port": 3000,
  "target_url": null,
  "detected_harnesses": ["claude", "codex", "agy", "pi"],
  "active_roles": [
    "planner", "explorer", "dispatcher", "tdd", "coding", "ops",
    "debugger", "e2e", "reviewer-lead", "reviewer-quality",
    "reviewer-arch", "reviewer-perf", "reviewer-security", "reviewer-ux", "reflector"
  ],
  "toolchain": {
    "build": "npm run build",
    "test": "npx vitest run",
    "typecheck": "npx tsc --noEmit",
    "static_health": "fallow --fail-on-regression --regression-baseline .fallow-baseline.json --summary",
    "push_cmd": null
  },
  "version_anchors": ["package.json"],
  "domain_skills": {
    "shadcn-ui": {
      "path": ".agents/skills/shadcn-ui/SKILL.md",
      "roles": ["planner", "coding", "reviewer-ux"]
    },
    "fallow-skills": {
      "path": ".agents/skills/fallow-skills/SKILL.md",
      "roles": ["reviewer-quality", "reviewer-arch", "explorer"]
    }
  },
  "context_monitor": {
    "probe_policy": "strict",
    "herdr_agent_usage_installed": true,
    "pi_proactive_compact_installed": false,
    "default_profile": {
      "tier": "A",
      "window_tokens": 262144,
      "armed_tokens": 157000,
      "danger_tokens": 188000
    },
    "role_overrides": {
      "planner": { "tier": "S", "window_tokens": 262144, "armed_tokens": 183000, "danger_tokens": 209000 },
      "dispatcher": { "tier": "B", "window_tokens": 163840, "armed_tokens": 81000, "danger_tokens": 101000 }
    }
  },
  "harness_profiles": {
    "claude": { "compact_cmd": "/compact 请保留：1.[Ground Truth]已验证的文件路径/命令与报错签名；2.[Continuity Ledger]当前生效的架构约束与职责边界；3.[Open Loops]未决待办项；4.[Delta]本轮改动。严禁伪造未读路径。", "clear_cmd": "/clear", "resume_flag": "--resume" },
    "codex": { "compact_cmd": "/compact", "clear_cmd": "/new", "resume_flag": "resume" },
    "pi": { "compact_cmd": "/compact 请保留：1.[Ground Truth]已验证的文件路径/命令与报错签名；2.[Continuity Ledger]当前生效的架构约束与职责边界；3.[Open Loops]未决待办项；4.[Delta]本轮改动。严禁伪造未读路径。", "clear_cmd": "/new", "resume_flag": "--resume" },
    "agy": { "compact_cmd": "/compact", "clear_cmd": "/clear", "resume_flag": "--resume" }
  },
  "roles": {
    "planner": { "harness": "claude", "model": "<high-reasoning-model>", "thinking": "high", "cli_args": ["--model", "<high-reasoning-model>", "--effort", "high"] },
    "reflector": { "harness": "claude", "model": "<high-reasoning-model>", "thinking": "high", "cli_args": ["--model", "<high-reasoning-model>", "--effort", "high"] },
    "explorer": { "harness": "claude", "model": "<high-reasoning-model>", "thinking": "high", "cli_args": ["--model", "<high-reasoning-model>", "--effort", "high"] },
    "dispatcher": { "harness": "pi", "model": "<fast-light-model>", "thinking": "none", "cli_args": ["--model", "<fast-light-model>", "--thinking", "off"] },
    "tdd": { "harness": "codex", "model": "<coding-model>", "thinking": "medium", "cli_args": ["--model", "<coding-model>", "-c", "model_reasoning_effort=\"medium\""] },
    "coding": { "harness": "codex", "model": "<coding-model>", "thinking": "medium", "cli_args": ["--model", "<coding-model>", "-c", "model_reasoning_effort=\"medium\""] },
    "ops": { "harness": "pi", "model": "<fast-light-model>", "thinking": "none", "cli_args": ["--model", "<fast-light-model>", "--thinking", "off"] },
    "debugger": { "harness": "claude", "model": "<high-reasoning-model>", "thinking": "high", "cli_args": ["--model", "<high-reasoning-model>", "--effort", "high"] },
    "security-redteam": { "harness": "claude", "model": "<high-reasoning-model>", "thinking": "high", "cli_args": ["--model", "<high-reasoning-model>", "--effort", "high"] },
    "e2e": { "harness": "agy", "model": "<browser-model>", "thinking": "low", "cli_args": ["--model", "<browser-model>"] },
    "reviewer-lead": { "harness": "claude", "model": "<high-reasoning-model>", "thinking": "high", "cli_args": ["--model", "<high-reasoning-model>", "--effort", "high"] },
    "reviewer-quality": { "harness": "pi", "model": "<fast-light-model>", "thinking": "none", "cli_args": ["--model", "<fast-light-model>", "--thinking", "off"] },
    "reviewer-arch": { "harness": "claude", "model": "<high-reasoning-model>", "thinking": "high", "cli_args": ["--model", "<high-reasoning-model>", "--effort", "high"] },
    "reviewer-perf": { "harness": "claude", "model": "<high-reasoning-model>", "thinking": "high", "cli_args": ["--model", "<high-reasoning-model>", "--effort", "high"] },
    "reviewer-security": { "harness": "claude", "model": "<high-reasoning-model>", "thinking": "high", "cli_args": ["--model", "<high-reasoning-model>", "--effort", "high"] },
    "reviewer-ux": { "harness": "codex", "model": "<coding-model>", "thinking": "medium", "cli_args": ["--model", "<coding-model>", "-c", "model_reasoning_effort=\"medium\""] }
  }
}
```

| 字段路径 | 类型 / 枚举值 | 含义与运行机制说明 |
| :--- | :--- | :--- |
| **`mode`** | `"standard"` \| `"worktree"` | 默认开发模式：`standard`（单工作区原地串行）或 `worktree`（`.worktrees/<id>` 独立工作区高并发）。 |
| **`default_ctx`** | `"compact"` \| `"clear"` \| `"keep"` | `standard` 模式下每完成一个 Feature 后，对 `tdd/coding/reviewer-lead` 的默认上下文打理策略。 |
| **`runtime_type`** | `"daemon_port"` \| `"push_to_host"` \| `"artifact_only"` | 验收运行态：常驻端口服务（配 `base_port`）、寄生态热推插件（配 `toolchain.push_cmd` + `target_url`）或纯编译产物。 |
| **`active_roles`** | `string[]` | 本项目实际启用的角色白名单（如纯 CLI 项目剔除 `e2e`/`reviewer-ux`，防误点名）。 |
| **`toolchain`** | `object` | 初始化阶段一次性验证固化的构建（`build`）、单测（`test`）、类型检查（`typecheck`）、静态健康（`static_health`）与热推（`push_cmd`）命令，日常运行零探测直接调用。 |
| **`version_anchors`** | `string[]` | 受控发版时 `ops` 需同步递增 SemVer 版本号的文件清单（如 `package.json`, `manifest.json`, 代码常量文件）。 |
| **`domain_skills`** | `object` | `Bootstrap` 扫描或联网检索推荐安装的垂类领域与工具 Skill（如 `shadcn-ui`、`fallow-skills`、`chrome-extensions`），通过 `roles` 数组按需精准挂载给相关角色，避免无关角色消耗上下文。 |
| **`context_monitor`** | `object` | 上下文水位监控配置：包含巡检松紧策略 **`probe_policy`**（`"strict"` 每次派活前必检 \| `"relaxed"` 结项全检+仅返工/临界时抽检）、是否安装了 `herdr-agent-usage` 与 `pi-proactive-compact` 插件，以及按「70%/60%/50% 黄金比例法则」（`tier: "S"\|"A"\|"B"` × `window_tokens`）计算的 `default_profile` 与 `role_overrides` 阈值，供 `scripts/agent-context.sh` 与 `Dispatcher` 直接读取。 |
| **`harness_profiles`** | `object` | `Bootstrap` 通过 `<harness> --help` 核实的各 CLI 压缩指令（`compact_cmd`，内置 EESV 四要素保真锚点）、清空指令（`clear_cmd`）与会话恢复参数（`resume_flag`）；中断与关闭窗格统一按 [`tools/herdr.md §[H-6]`](tools/herdr.md) 执行。 |
| **`roles.<id>`** | `object` | 各角色绑定的 `harness`、逻辑 `model`、逻辑思考强度 `thinking` (`"none"`\|`"low"`\|`"medium"`\|`"high"`)，以及供 `herdr agent start` 直接展开透传的原生启动参数数组 **`cli_args`**。 |

---

## 7. Herdr 编排指令规范、跨任务监听与会话快照 (`tools/herdr.md` & `session.json`)

> **配套必读规范**：`dispatcher`、`ops`、`planner`、`reflector` 角色及 `bootstrap-teamwork`、`roundtable-debate` 剧本必读 **[`tools/herdr.md`](tools/herdr.md)**，并遵照对应段落（`§[H-1]` ~ `§[H-6]`）执行：

| 编排场景 | 唯一权威指令配方章节 | 核心机制要点 |
| :--- | :--- | :--- |
| **切分窗格与创建标签页** | **[`tools/herdr.md §[H-1]`](tools/herdr.md)** | 统一携带 `--no-focus`，并通过 `jq -r` 提取 `.result.pane.pane_id` 或 `.result.root_pane.pane_id`。 |
| **角色启动、快照导出与跨天复活** | **[`tools/herdr.md §[H-2]`](tools/herdr.md)** | 从 `.agents/environment.json` 展开 `cli_args` 透传；用 `herdr agent list \| jq ...` 导出 `.agents/session.json`。 |
| **事件驱动派发、等待与读取** | **[`tools/herdr.md §[H-3]`](tools/herdr.md)** | **纯事件驱动等待**，默认自动匹配 `idle \| done \| blocked` 三种终态唤醒；使用 `--source recent-unwrapped` 读取输出。 |
| **Worktree 平行工作区建场与回收** | **[`tools/herdr.md §[H-4]`](tools/herdr.md)** | 调 `worktree-up.sh` ➔ `herdr workspace create --label "ws-<id>"` ➔ 启动全局唯一角色名（如 `dispatcher-001`）。 |
| **后台服务守护子窗格 (`.ops-pane`)** | **[`tools/herdr.md §[H-5]`](tools/herdr.md)** | 在 `ops` Tab 内切分子窗格并存入 `.ops-pane`，用 `pane run` 与 `pane wait-output` 驱动常驻开发服务。 |
| **上下文探针、主动压缩与窗格回收** | **[`tools/herdr.md §[H-6]`](tools/herdr.md)** | 调 `scripts/agent-context.sh` 巡检水位、发送 EESV `compact_cmd`/`clear_cmd`、`send-keys ctrl+c` 中断重试，或通过 `herdr pane close` 关闭窗格。 |

### 7.1 `Master Dispatcher` 跨流水线事件监听与 FIFO 认知队列提取
```bash
# 1. 挂起后台单次触发监听命令（任一任务进入待处理状态即退出并自动唤醒窗口 2 总控台）：
tail -n 0 -f changes/*/pipeline.jsonl | grep --line-buffered -m 1 -E '"state":"(WAITING_|STALLED|DONE)"'

# 2. 提取全部待人类处理的 FIFO 认知队列（按时间戳升序）：
tail -q -n 1 changes/*/pipeline.jsonl | jq -s 'map(select(.state == "WAITING_ACCEPTANCE" or .state == "WAITING_DECISION" or .state == "STALLED")) | sort_by(.ts)'
```

### 7.2 会话快照结构与字段字典 (`.agents/session.json`)
`.agents/session.json` 记录当前活跃窗格的运行时拓扑与会话 ID（导出与恢复命令见 **[`tools/herdr.md §[H-2]`](tools/herdr.md)**），专供终端重启或跨天复工时秒级恢复常驻角色记忆：

```json
{
  "updated_at": "2026-11-05T08:00:00Z",
  "workspace_id": "w1",
  "project": "my-project",
  "agents": {
    "planner": {
      "name": "planner",
      "pane_id": "w1:p2",
      "tab_id": "w1:t1",
      "harness": "claude",
      "model": "<high-reasoning-model>",
      "thinking": "high",
      "conversation_id": "conv_01hxyz..."
    },
    "dispatcher": {
      "name": "dispatcher",
      "pane_id": "w1:p3",
      "tab_id": "w1:t1",
      "harness": "pi",
      "model": "<fast-light-model>",
      "thinking": "none",
      "conversation_id": "session_98abc..."
    }
  }
}
```

| 字段路径 | 含义与运行机制说明 |
| :--- | :--- |
| **`workspace_id` / `project`** | 快照所属的 Herdr 工作区 ID（如 `w1`）与项目目录名。 |
| **`agents.<role>.pane_id` / `tab_id`** | 角色当前驻留的稳定窗格与标签页句柄（Herdr 关闭其他窗格不会导致已分配 ID 重排）。 |
| **`agents.<role>.harness` / `model` / `thinking`** | 从 `.agents/environment.json` 同步关联记录的实际运行底座、模型名与思考强度。 |
| **`agents.<role>.conversation_id`** | Herdr 捕获的底层 Agent 会话 ID（`.agent_session.value`），配合 `harness_profiles.<harness>.resume_flag` 实现跨天原地恢复上下文。 |

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
