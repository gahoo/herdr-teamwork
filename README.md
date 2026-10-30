# Herdr Teamwork v2.3 ⚡

> **Multi-Agent Spec Implementation Framework Orchestrated via Herdr & Git Worktrees**
>
> 基于 **Herdr** 终端工作区管理工具构建的**“双控台分治、内外双驱、事件溯源、双层自演进”**多 Agent 协同工程规范。遵循 **OpenSpec 活文档标准**、**单流水线内同步等待 (`--wait`) + 跨流水线文件流监听 (`tail -f pipeline.jsonl`)**，通过 **`roles/`（常驻职责）+ `playbooks/`（按需战术剧本）+ `scripts/`（自动化基建）** 三元架构，无缝支持跨语言单线开发与多 Worktree / Workspace 高并发并行交付。

[![Skill](https://img.shields.io/badge/Agent_Skill-herdr--teamwork-blue?style=flat-square)](https://skills.sh)
[![Version](https://img.shields.io/badge/Version-v2.3-orange?style=flat-square)](SKILL.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

---

## 🚀 快速安装 (Installation)

无需复杂配置，直接通过 `npx skills` 将本技能一键安装至你的工程或全局环境中：

```bash
# 1. 安装至当前项目
npx skills add gahoo/herdr-teamwork

# 2. 或者全局安装 (User Scope)
npx skills add gahoo/herdr-teamwork -g
```

---

## 🏛️ 核心架构亮点 (v2.3 Architecture Highlights)

1. **双主控台分治 + 严格工具白名单（规划与交付物理绝缘，90% 问题就地闭环）**：
   - **窗口 1：`Planner`（总规划台）**：常驻主工作区左窗格，受严格只读图谱与契约工具白名单约束。负责与人类探讨需求、维护统一领域语言 `GLOSSARY.md` 与 `changes/KANBAN.md`、唤起 `Explorer` 深潜摸底、按需直询 `Arch / Security` 专家进行 Stage 1 预审，落盘 `prd.md`、`spec.md`、`tasks.md` 并写入 `pipeline.jsonl` 首行 `PLAN` 事件，上下文 100% 纯净。
   - **窗口 2：`Dispatcher`（交付总控台）**：常驻主工作区右窗格，物理剥夺源码读取权（禁读 `src/` 与 `tests/`），独占续写 `pipeline.jsonl`。负责维护人类 FIFO 认知队列，**将 90% 的验收报障（追加 `REPLAN` 调 `debugger`）与发布授权（调 `ops`）在窗口 2 就地闭环**，仅 10% 契约缺陷（`SPEC_DEFECT`）切回窗口 1。
2. **内外双驱、跨语言 Worktree 隔离与子窗格透明守护（零冲撞、零黑盒）**：
   - **微观单流水线内（模式乙）**：`Dispatcher` 使用 `herdr agent prompt <role> "..." --wait --timeout <ms>` 同步阻塞调度下游角色，仅由 `Dispatcher` 追加写入 `changes/<id>/pipeline.jsonl`，彻底杜绝下游忘写收据引发的永久死锁。
   - **宏观跨流水线层（`worktree` 并行模式）**：由 `Ops` 调用内置 [`scripts/worktree-up.sh`](scripts/worktree-up.sh) 与 [`scripts/worktree-down.sh`](scripts/worktree-down.sh) 管理 `.worktrees/<id>/` 生命周期与跨语言依赖软链（支持 Node `node_modules` / Python `.venv` 写时解链、Rust/Go 缓存加速）；`Ops` 在专属子窗格（`.ops-pane`）前台透明运行守护服务，人类与 Agent 均可直读原生实时日志。
3. **三拍点将、5 级证据阶梯与跨语言静态健康门禁（杜绝橡皮图章与脑补挑刺）**：
   - **三拍点将**：`Lead Reviewer` 分诊输出 `SPAWN_EXPERTS` 点将令 ➔ `Dispatcher` 代为切屏并发拉起专家并回收简报 ➔ `Lead Reviewer` 基于 **5 级证据阶梯**（剔除无确定性触发路径的理论担忧）执行 ROI 仲裁。
   - **行号级证伪举证 (`Proof of Defense`) + 跨语言静态扫描**：`Quality Reviewer` 独占吞吐 TS (`fallow`+`tsc`) / Rust (`clippy`) / Go (`golangci-lint`) / Python (`ruff`+`mypy`) 原始日志；全体审查员强制贴出源码/测试防御行号 (`file:line`) 方可放行。
4. **渐进式战术剧本（`playbooks/`）与领域知识物化（`GLOSSARY.md` + `E2E_PLAYBOOK.md`）**：
   - **渐进式加载（Progressive Disclosure）**：16 个角色的常驻契约（`roles/`）保持极简底线，仅通过尾部路由表按需挂载 9 大专项战术剧本（`playbooks/`），平时零 Token 负担，命中条件时跨角色协同执行 **`[SPIKE]` 快速原型刺探**、**`[HILLCLIMB]` 科学爬山**、**全库架构深度巡检**、**重大架构圆桌辩论**、**形式化状态机验证**、**像素级视觉比对**与**交互式配置向导生成**。
   - **物化导航与领域词典**：通过 `GLOSSARY.md` 消除多 Agent 命名漂移；通过 `E2E_PLAYBOOK.md` 物化页面路由与交互记忆，让 `e2e` 告别每次从零盲目摸索 DOM。
5. **全局 `Reflector` 双层反思闭环与「四级防错强化阶梯」**：
   - 当 `pipeline.jsonl` 出现返工、重排或受阻信号时，在销毁工作区前唤醒全局 `Reflector`，按需跨窗格问询当事 Agent，并严格遵循 **「Level 1 架构消除 > Level 2 类型/Lint 机械拦截 > Level 3 行为测试锁死 > Level 4 文档规则兜底」** 阶梯，同步沉淀项目级 `reflections/<domain>.md`（含 `🔬 SPIKE_CANDIDATE` 立项闭环）与 Skill 级 `.reflections/<id>.md`。
6. **非 Worktree (`standard`) 模式 4 级上下文生命周期管理**：
   - 特性进行中全员保留现场；特性结项（`DONE`）后，8 个项目记忆型专家（`reflector` / `explorer` / `debugger` / `security-redteam` / `reviewer-arch/security/perf/ux`）统一执行 `/compact` 沉淀长期架构心智，4 个高噪工具人（`dispatcher` / `ops` / `reviewer-quality` / `e2e`）直接 `/clear` 瞬时归零。

---

## 📂 目录结构规范

```text
project-root/
├── GLOSSARY.md                      # 项目级统一领域语言词典（Planner 维护，全角色共享，零实现细节）
├── E2E_PLAYBOOK.md                  # 端到端验证路由与交互剧本（启用 e2e 时按需创建，由 E2E 增量维护）
├── docs/adr/                        # 架构决策记录（仅当满足 3 条件门禁时由 Planner 创建）
├── changes/                         # 第一类业务数据资产（纳入 Git 版本管理）
│   ├── KANBAN.md                    # 全局大盘总看板（Planner 独占，含 Inbox 占位池）
│   └── <id>/                        # 特性变更集目录 (如 001-user-auth/)
│       ├── prd.md                   # 业务诉求与验收标准 (Why & What)
│       ├── spec.md                  # 技术契约与接口定义 (Architecture & API)
│       ├── tasks.md                 # 微观代码改造勾选清单 (供 tdd / coding 使用)
│       ├── pipeline.jsonl           # 流水线编排与状态事件流 (Planner 创世 PLAN，Dispatcher 独占续写)
│       ├── review.md                # 审查裁决归档 (含对账单、防御行号举证与双清单)
│       ├── debug.md                 # 法医排错根因诊断与 Fix Spec (按需产出)
│       ├── security-poc.md          # 红队渗透测试与 PoC 报告 (按需产出)
│       └── explore.md               # 复杂源码可行性预研简报 (按需产出)
├── reflections/                     # 项目级经验教训与待探索课题库（Reflector 独占维护）
├── .agents/                         # Agent 运行时支撑基建
│   ├── environment.json             # 宿主机器 Harness 画像与 16 角色配置
│   ├── session.json                 # Herdr 会话状态快照
│   └── skills/herdr-teamwork/       # 本技能规范库 (roles/ + playbooks/ + scripts/ + .reflections/)
└── .worktrees/                      # Worktree 并行执行隔离区 (Ops 建场管理，软链共享 changes / .agents / 依赖)
```

---

## 📖 规范全览：16 正交角色 × 8 战术剧本 × 2 基建脚本

### 1. 总纲与自动化脚本
- **核心总纲**：[`SKILL.md`](SKILL.md) —— 完整工程规范、双控台交互协议、`pipeline.jsonl` 事件流标准、两阶段审查、上下文生命周期与 CLI 命令矩阵。
- **内置脚本 (`scripts/`)**：[`scripts/worktree-up.sh`](scripts/worktree-up.sh)（跨语言 Worktree 物理建场与依赖软链挂载）、[`scripts/worktree-down.sh`](scripts/worktree-down.sh)（守护进程清理、安全解链与工作区销毁）。

### 2. 16 个正交角色契约 (`roles/` —— Who)

| 所属集群 | 角色契约文件 | 核心定位与一句话职责 |
| :--- | :--- | :--- |
| **前店规划层** | [`roles/planner.md`](roles/planner.md) | **总规划师（窗口 1）**：需求复述对齐、维护 `KANBAN.md` 与 `GLOSSARY.md`、撰写契约四件套、工具白名单绝缘施工噪音。 |
| **前店规划层** | [`roles/explorer.md`](roles/explorer.md) | **代码考古与可行性预研员**：执行 `/how` 调用链追踪与 `/why` (`git log -S`) 历史意图溯源，输出 `explore.md` 保护主控台。 |
| **后厂执行层** | [`roles/dispatcher.md`](roles/dispatcher.md) | **交付总控与状态机调度员（窗口 2 / `ws-<id>`）**：物理蒙眼禁读源码，独占续写 `pipeline.jsonl`，驱动流水线与结项上下文打理。 |
| **后厂执行层** | [`roles/tdd.md`](roles/tdd.md) | **测试驱动开发工程师**：在业务编码前编写强断言 Red Test（只测公开行为契约，不绑内部实现细节）。 |
| **后厂执行层** | [`roles/coding.md`](roles/coding.md) | **业务代码实现者**：实施业务代码并自跑单测至 Green，遵循边界解析、类型防呆与“用结构代替脆弱注释”纪律。 |
| **后厂执行层** | [`roles/ops.md`](roles/ops.md) | **跨语言环境、Worktree 与发布守护者**：管理 Worktree 软链写时解链、切分子窗格透明运行守护服务、生成配置向导与受控发布。 |
| **后厂执行层** | [`roles/debugger.md`](roles/debugger.md) | **法医式排错侦探**：5 阶段硬门禁排障（先建秒级见红回路并极小化复现 ➔ 提可证伪假说 ➔ 攻击前提 `attack-the-premise`），独占输出 `debug.md`。 |
| **后厂执行层** | [`roles/security-redteam.md`](roles/security-redteam.md) | **红队渗透测试领队**：STRIDE 威胁建模、白盒污点追踪与隔离沙箱动态渗透，产出可武器化的 `security-poc.md`。 |
| **后厂执行层** | [`roles/e2e.md`](roles/e2e.md) | **端到端与冒烟测试专家**：结合 `E2E_PLAYBOOK.md` 导航记忆执行双轨浏览器走查，增量回写路由与避坑指南。 |
| **分形审查层** | [`roles/reviewer-lead.md`](roles/reviewer-lead.md) | **主审统筹与裁决官**：独立执行 Stage 2A 测试快检；在 Stage 2B 开方点将并按 5 级证据阶梯过滤理论噪音，独占签署 `review.md`。 |
| **分形审查层** | [`roles/reviewer-quality.md`](roles/reviewer-quality.md) | **静态代码质量过滤官**：独占吞吐跨语言静态分析器（`fallow` / `clippy` / `golangci-lint` / `ruff`）并拦截脆弱注释，输出 ≤15 行简报。 |
| **分形审查层** | [`roles/reviewer-arch.md`](roles/reviewer-arch.md) | **系统架构专家**：审查深模块设计、`gitnexus impact` 爆炸半径及专为 AI Agent 设定的 4 大架构红旗。 |
| **分形审查层** | [`roles/reviewer-perf.md`](roles/reviewer-perf.md) | **性能与并发专家**：审查渲染/内存泄漏、N+1 查询、并发竞争，并依据 `Explain the Number` 核验性能跑分真实性。 |
| **分形审查层** | [`roles/reviewer-security.md`](roles/reviewer-security.md) | **蓝队安全合规专家**：审查注入防御、RBAC/ABAC 越权、供应链 CVE 与红队 PoC 闭环，握有一票否决权。 |
| **分形审查层** | [`roles/reviewer-ux.md`](roles/reviewer-ux.md) | **交互与无障碍专家**：审查热键冲突、输入法容错、Focus Trap 焦点闭环、ARIA 无障碍与视觉一致性。 |
| **反思演进层** | [`roles/reflector.md`](roles/reflector.md) | **全局流程反思官**：由异常信号触发，按四级防错强化阶梯沉淀项目级 `reflections/<domain>.md` 与 Skill 级 `.reflections/<id>.md`。 |

### 3. 9 个按需触发战术剧本 (`playbooks/` —— How)

| 战术剧本文件 | 触发场景 (When) | 发起者 ➔ 核心执行者 |
| :--- | :--- | :--- |
| [`playbooks/arch-audit.md`](playbooks/arch-audit.md) | 每累计完成 3~5 个特性，或连续出现浅模块耦合预警时 | `planner` 提议立项 ➔ **`reviewer-arch`** 全库扫描产出 `arch-report.html` |
| [`playbooks/roundtable-debate.md`](playbooks/roundtable-debate.md) | 重大架构议题：单向门 + 跨 ≥2 维度显著权衡 + 2~3 套互斥方案时 | `planner` 立题并 Fork **临时主席分身** ➔ 专家背靠背亮牌 + 冲突方交锋 1 轮 ➔ 主席裁决 ➔ **人类点头** |
| [`playbooks/prototype-spike.md`](playbooks/prototype-spike.md) | UI/技术方案吃不准，或验证 `reflector` 的 `🔬 SPIKE_CANDIDATE` 时 | `planner` 立项 `[SPIKE]` ➔ **`coding` + `ops`** 快速构建原型（拍板后用完即焚） |
| [`playbooks/hillclimb.md`](playbooks/hillclimb.md) | 针对耗时、内存、吞吐量或准确率等单一量化指标持续逼近优化时 | `planner` 定基线 `[HILLCLIMB]` ➔ **`coding`** 实测爬山回滚循环 ➔ **`reviewer-perf`** 核验 |
| [`playbooks/formal-statechart.md`](playbooks/formal-statechart.md) | 触及复杂状态机、并发竞态、分布式重试、解析器或 `unsafe` 代码时 | **`planner`** 画含禁止状态的 Statechart ➔ **`tdd` / `coding`** 写属性/模型测试 ➔ **`reviewer-arch`** 对账 |
| [`playbooks/visual-parity.md`](playbooks/visual-parity.md) | 附带参考设计图/旧版截图，或要求 UI 迁移前后像素级视觉一致时 | `planner` 标注 `[VISUAL_PARITY]` ➔ **`reviewer-ux` + `e2e`** 实机截图与计算样式六维比对 |
| [`playbooks/setup-wizard.md`](playbooks/setup-wizard.md) | 环境启动发现缺失必须由人类提供的外部 API 密钥、OAuth 或证书时 | **`ops`** 全自动编写幂等、带即时连通性自检的 `scripts/setup-wizard.sh` 引导人类一键运行 |
| [`playbooks/ketchup-briefing.md`](playbooks/ketchup-briefing.md) | 后台连续流转后人类回到窗口询问进展，或特性结项呈报合入验收时 | **`planner`** 在 Window 1 输出可视化进度图、单/双向门风险定级与自包含选择题 |
| [`playbooks/teach-explain.md`](playbooks/teach-explain.md) | 人类表示“没看懂/说人话”，或要求深入剖析存量复杂子系统原理时 | 当前方案由 **`planner`** 降维解释；存量代码由 **`explorer`** 执行 `/how`+`/why` 产出递进图解 |

---

## 🙏 致谢与设计溯源 (Credits & Acknowledgements)

`herdr-teamwork` 的多角色纪律、渐进式战术剧本与反脆弱工程机制，深度借鉴并融合了以下开源项目与工程思想的精华，特此致谢：

- **[Matt Pocock (`@mattpocock`) — `mattpocock/skills`](https://github.com/mattpocock/skills)**：
  启发了本项目中面向多 Agent 共享的统一领域语言词典（`GLOSSARY.md`）与 3 条件 ADR 门禁（源自 `domain-modeling` & `grill-with-docs`）、五阶段硬门禁排障循环与临时探针标记（源自 `diagnosing-bugs`）、用完即焚的快速原型刺探（源自 `prototype`）、周期性深模块架构体检报告（源自 `improve-codebase-architecture`）、人类专属配置交互式向导脚本（源自 `wizard`）、单/双向门合入风险评估（源自 `pr`）以及渐进式披露与正向引导的 Agent 契约写作准则（源自 `writing-for-agents` & `retro`）。
- **[Lauren Tan (`@poteto`) — `pstack`](https://github.com/cursor/plugins/tree/main/pstack)**：
  启发了本项目 `Reflector` 的「四级防错强化阶梯：架构消除 > 类型/Lint > 测试 > 文档兜底」（源自 `/correct`）、面向 AI Agent 协作的 4 大架构红旗与推倒重来信号（源自 `/architect` & `design-red-flags`）、5 级证据阶梯与实证过滤铁律（源自 `/blast-radius` & `/interrogate`）、单一量化指标科学爬山循环與数字真实性核查（源自 `hillclimb`、`benchmark-checklist` & `explain-the-number`）、高危状态机图解与形式化验证（源自 `/statechart` & `/create-formal-verification-skill`）、像素级视觉等价同屏比对（源自 `visual-parity`）、物化 E2E 路由与交互记忆的 `E2E_PLAYBOOK.md`（源自 `/create-verification-skill` 的 Feature Map 与 `build-the-lever`）、用结构代替脆弱注释（源自 `/no-comments`）以及人类回场全局简报与 `/how`+`/why` 递进图解教学（源自 `/ketchup` & `/teach`）。
- **核心生态与基建工具**：
  感谢 **Herdr**（多窗格终端工作区与 Agent 编排底座）、**[GitNexus](https://github.com/abhigyanpatwari/GitNexus)**（AST 级代码知识图谱与爆炸半径分析）、**[Fallow](https://github.com/fallow-rs/fallow)**（极速静态死代码与架构健康度分析）以及 **OpenSpec** 活文档规范。

---

## 📄 License

[MIT](LICENSE)
