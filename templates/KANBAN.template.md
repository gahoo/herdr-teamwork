# 全局变更集看板 (`changes/KANBAN.md`)

> **维护铁律**：本文件由窗口 1 **`Planner` 100% 独占维护**，严禁私建碎片化 `Inbox.md`。
> - **需求未启，看板先行**：任何新需求意向、远期拆解切片、人类确认采纳的 `🟡 [CONSTRUCTIVE]` 建议、以及 `Reflector` 产出的 `🔬 [SPIKE_CANDIDATE]` 或 `🛡️ [GUARDRAIL]` 任务，必须第一时间登记入池。
> - **依赖与并发前沿 (`Ready Frontier`)**：仅对存在**硬逻辑前置依赖**（如特性 B 强依赖特性 A 尚未建立的数据结构或接口）的条目显式标注 `[Blocked by: <id>]`；单纯涉及相同源码文件修改的任务无需硬性串行化，可直接并发启动多个 Worktree，由合入期预同步消解冲突。凡无未决阻塞项的待开展条目均构成 **可执行前沿 (`Ready Frontier`)**。

---

## 📥 需求收件与待开展占位池 (Inbox / Backlog)

### 🟢 可执行前沿 (Ready Frontier —— 无前置阻塞，可随时立项或并发启动)
- [ ] **`002-<feature-slug>`**：<一句话业务目标与价值概述>
- [ ] **`003-<spike-slug>`** `[SPIKE]`：<待探索验证的技术/交互假设>

### ⏳ 存在硬逻辑前置依赖 (Blocked)
- [ ] **`004-<dependent-slug>`** `[Blocked by: 001, 002]`：<依赖前置契约落盘后方可开展的特性描述>

---

## 🚀 进行中 (In Progress)

| 变更集 ID (`<id>`) | 特性简述 | 运行模式 / Workspace | 绑定端口 | 当前状态 | 备注与契约路径 |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **`001-<feature-slug>`** | <核心目标简述> | `standard` / `ws-001` | `3001` | `RUNNING` | [`changes/001-<feature-slug>/`](./001-<feature-slug>/) |

---

## ✅ 已完成 (Done)

| 变更集 ID (`<id>`) | 特性简述 | 结项日期 | 归档摘要与关键产物 |
| :--- | :--- | :---: | :--- |
| **`000-init`** | 项目协同基建初始化 | `YYYY-MM-DD` | 建立 `GLOSSARY.md`、`KANBAN.md` 与双控台拓扑 |

---

## 📌 规划台交接备忘 (Planner Handoff —— 供高水位传位「Planner 二世」)

> **使用规程**：当窗口 1 `Planner` 在契约落盘后的里程碑边界达到 `🟡 ARMED` 高水位时，先在此处更新 **EESV 四要素交接单（≤15 行）**，经人类确认后执行 `/clear`（或 `/new`）唤醒「Planner 二世」零噪音接管。

1. **`[Ground Truth / 确定性事实锚点]`**：
   - 当前活跃变更集：`changes/001-<feature-slug>/`（已落盘 `prd.md`, `spec.md`, `tasks.md`, `pipeline.jsonl`）
   - 领域词典与 ADR：[`GLOSSARY.md`](../GLOSSARY.md)、`docs/adr/`
2. **`[Continuity Ledger / 延续性决策台账]`**：
   - 架构红线与人类偏好：<记录已确立的全局技术偏好与约束>
   - 已否决废案（严禁二世重提）：<记录已被人类明确否决的设计方案及原因>
3. **`[Open Loops / 未闭环悬念]`**：
   - <记录下一特性待深入探讨的设计分支或遗留问题>
4. **`[Delta / 本轮增量]`**：
   - <记录本代 Planner 刚完成的规划里程碑摘要>
