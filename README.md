# Herdr Teamwork v2.0 ⚡

> **Multi-Agent Spec Implementation Framework Orchestrated via Herdr & Git Worktrees**
>
> 基于 **Herdr** 终端工作区管理工具构建的**“前店后厂、控制流两级星型、数据流文件直连”**多 Agent 协同工程规范。遵循 **OpenSpec 活文档标准**、**事件驱动免轮询 (`herdr agent prompt --wait`)** 与 **单向异步信箱 (`tasks.md`)**，支持常规单线开发与多 Worktree 高并发并行交付。

[![Skill](https://img.shields.io/badge/Agent_Skill-herdr--teamwork-blue?style=flat-square)](https://skills.sh)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

---

## 🚀 快速安装 (Installation)

无需复杂配置，直接通过 `npx skills` 将本技能一键安装至你的工程或全局环境中：

```bash
# 1. 安装至当前项目
npx skills add <owner>/herdr-teamwork

# 2. 或者全局安装 (User Scope)
npx skills add <owner>/herdr-teamwork -g
```

---

## 🏛️ 核心架构亮点 (v2.0 Architecture Highlights)

1. **前店后厂彻底解耦（永不阻塞人类主窗口）**：
   - **前店（规划与探索）**：`Planner` 常驻主窗口与人类高频对话、维护 `changes/KANBAN.md` 与 `prd/spec/tasks.md`；遇到复杂历史代码按需唤起 `Explorer` 深潜摸底；遇到重大架构变更直接按需咨询 `Arch / Security` 专家（Stage 1 预审）。
   - **后厂（无头流水线）**：方案经人类拍板后，`Planner` 单向异步点火 `Dispatcher`（零阻塞释放主窗口）。`Dispatcher` 被物理剥夺源码读取权（禁读 `src/` 与 `tests/`），专注驱动 `Test ➔ Reviewer ➔ Coding ➔ Ops` 闭环，彻底根治管理型 Agent“越俎代庖抢活干”的顽疾。
2. **双模式自适应（`standard` 单线 vs `worktree` 并发）**：
   - 支持单目录极简推进，也支持基于 `.worktrees/<id>/` + 软链接共享 `changes/` 的多特性并行开发。
   - **单向信箱与认知排队（Cognitive Funnel）**：后台 `Dispatcher` 遇到卡点或完工待验收时，仅更新各自 `changes/<id>/tasks.md` 的状态头并静默挂起，绝不反向打断正在对话的 `Planner`；`Planner` 在空闲时按 FIFO 单工队列逐个向人类呈报，保护人类心流。
3. **三拍点将与证伪式审查（杜绝橡皮图章与过度挑刺）**：
   - **三拍点将**：`Lead Reviewer` 分诊输出一行 `SPAWN_EXPERTS` 点将令 ➔ `Dispatcher` 代为物理切屏并发拉起专家并回收简报 ➔ `Lead Reviewer` 进行 ROI 仲裁。
   - **行号级证伪举证 (Proof of Defense)**：要求所有 Reviewer 必须贴出源码/测试中防御脆弱边界的确切行号 (`file:line`) 方可放行。
   - **红黄分级分流**：严格区分 🔴 `BLOCKER`（打回返工，限 2 轮）与 🟡 `CONSTRUCTIVE`（当前直接放行，由 `Planner` 提取沉淀至 `KANBAN.md` Inbox 占位池），禁绝 ⚪ `NITPICK`。

---

## 📂 目录结构规范

```text
project-root/
├── changes/                         # 第一类业务数据资产（纳入 Git 版本管理）
│   ├── KANBAN.md                    # 全局大盘总看板（含 Inbox 占位池与待人类处理队列）
│   └── <id>/                        # 特性变更集目录
│       ├── prd.md                   # 业务诉求与验收标准
│       ├── spec.md                  # 技术契约与接口定义 (Living Truth)
│       ├── tasks.md                 # 状态信箱头 + 阶段任务卡片 (含通道类型与端口分配)
│       ├── review.md                # 审查裁决归档 (含对账单、防御行号举证与双清单)
│       ├── debug.md                 # 法医排错根因诊断与 Fix Spec (按需产出)
│       ├── security-poc.md          # 红队渗透测试与 PoC 报告 (按需产出)
│       └── explore.md               # 复杂源码可行性预研简报 (按需产出)
├── .agents/                         # Agent 运行时支撑基建
│   ├── environment.json             # 宿主机器 Harness 画像与 15 角色配置
│   ├── session.json                 # Herdr 会话状态快照
│   └── skills/herdr-teamwork/       # 本技能与 15 角色契约库
└── .worktrees/                      # Worktree 并行执行隔离区 (按需启用，软链接共享 changes/ 与 .agents/)
```

---

## 📖 规范全览

- [SKILL.md](SKILL.md)：完整工程规范、两阶段审查协议、命令矩阵与图谱导航指南。
- [roles/](roles/)：15 个正交角色的专属契约库（`planner`, `explorer`, `dispatcher`, `coding`, `test`, `ops`, `debugger`, `security-redteam`, `test-e2e`, `reviewer-lead`, `reviewer-quality`, `reviewer-arch`, `reviewer-perf`, `reviewer-security`, `reviewer-ux`）。

---

## 📄 License

[MIT](LICENSE)