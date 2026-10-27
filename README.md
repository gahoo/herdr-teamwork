# Herdr Teamwork v2.1 ⚡

> **Multi-Agent Spec Implementation Framework Orchestrated via Herdr & Git Worktrees**
>
> 基于 **Herdr** 终端工作区管理工具构建的**“双控台分治、内外双驱、事件溯源”**多 Agent 协同工程规范。遵循 **OpenSpec 活文档标准**、**单流水线内同步等待 (`--wait`) + 跨流水线文件流监听 (`tail -f pipeline.jsonl`)**，无缝支持常规单线开发与多 Worktree / Workspace 高并发并行交付。

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

## 🏛️ 核心架构亮点 (v2.1 Architecture Highlights)

1. **双主控台分治（规划与交付物理绝缘，90% 问题就地闭环）**：
   - **窗口 1：`Planner`（总规划台）**：常驻主工作区左窗格，专注探讨需求、唤起 `Explorer` 深潜摸底、按需直询 `Arch / Security` 专家进行 Stage 1 预审、独占维护 `changes/KANBAN.md`。与人类对齐后落盘 `prd.md`、`spec.md`、`tasks.md`，并创建 `pipeline.jsonl` 写入首行 `PLAN` 事件（支持动态增删调节工序序列），上下文 100% 纯净。
   - **窗口 2：`Dispatcher`（交付总控台）**：常驻主工作区右窗格，物理剥夺源码读取权（禁读 `src/` 与 `tests/`），独占续写 `pipeline.jsonl`。负责维护人类 FIFO 认知队列，**将 90% 的验收报障（追加 `REPLAN` 调 `debugger`）与发布授权（调 `ops`）在窗口 2 就地闭环**，仅 10% 契约缺陷（`SPEC_DEFECT`）切回窗口 1。
2. **内外双驱与 `pipeline.jsonl` 事件溯源（零冲撞、零死锁）**：
   - **微观单流水线内（模式乙）**：`Dispatcher` 使用 `herdr agent prompt <role> "..." --wait --timeout <ms>` 同步阻塞调度下游角色，仅由 `Dispatcher` 追加写入 `changes/<id>/pipeline.jsonl`，彻底杜绝下游忘写收据引发的永久死锁。
   - **宏观跨流水线层（`worktree` 并行模式）**：各变更集运行在独立的 Herdr Workspace（`ws-<id>`）与 `.worktrees/<id>/` 中；物理建场（含 `changes`、`.agents` 及 `node_modules` 写时解链软链）全权归属 `Ops`；`Worker Dispatcher` 只写各自 `pipeline.jsonl`，总控台通过后台 `tail -f` 自动感知唤醒，零终端输入冲撞。
3. **三拍点将与证伪式审查（杜绝橡皮图章与过度挑刺）**：
   - **三拍点将**：`Lead Reviewer` 分诊输出 `SPAWN_EXPERTS` 点将令 ➔ `Dispatcher` 代为切屏并发拉起专家并回收简报 ➔ `Lead Reviewer` 执行 ROI 仲裁。
   - **行号级证伪举证 (`Proof of Defense`)**：强制贴出源码/测试中防御脆弱边界的确切行号 (`file:line`) 方可放行。
   - **红黄分级与人类受控入池**：🔴 `BLOCKER` 打回返工（限 2 轮）；🟡 `CONSTRUCTIVE` 当场放行并在 `pipeline.jsonl` 中提醒人类，经人类确认后在窗口 1 交 `Planner` 记入 `KANBAN.md` Inbox。

---

## 📂 目录结构规范

```text
project-root/
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
├── .agents/                         # Agent 运行时支撑基建
│   ├── environment.json             # 宿主机器 Harness 画像与 15 角色配置
│   ├── session.json                 # Herdr 会话状态快照
│   └── skills/herdr-teamwork/       # 本技能与 15 角色契约库
└── .worktrees/                      # Worktree 并行执行隔离区 (Ops 建场管理，软链共享 changes / .agents / node_modules)
```

---

## 📖 规范全览

- [SKILL.md](SKILL.md)：完整工程规范、双控台交互协议、`pipeline.jsonl` 事件标准、两阶段审查与命令矩阵。
- [roles/](roles/)：15 个正交角色的专属契约库（`planner`, `explorer`, `dispatcher`, `tdd`, `coding`, `ops`, `debugger`, `security-redteam`, `e2e`, `reviewer-lead`, `reviewer-quality`, `reviewer-arch`, `reviewer-perf`, `reviewer-security`, `reviewer-ux`）。

---

## 📄 License

[MIT](LICENSE)
