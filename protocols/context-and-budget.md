# 多 Agent 上下文主动统筹管理与预算协议 (`protocols/context-and-budget.md`)

> **适用角色**：`dispatcher`（全局水位巡检与主动压缩统筹）、`planner`（规划台高水位二世交接与上下文策略设定）、`bootstrap`（初始化 `context_monitor` 阈值）。
> **关联总纲**：[`SKILL.md §5`](../SKILL.md) | **关联脚本**：[`scripts/agent-context.py`](../scripts/agent-context.py) | **关联工具配方**：[`tools/herdr.md §[H-6]`](../tools/herdr.md)

---

## 1. 核心目标与总体机制

为彻底根治「不知当前水位」、「刚发命令或任务做到一半撞上 ~90% 被动自动压缩导致失忆」、「提前清空误伤 `Reflector` 采蜜」以及「压缩后遗忘角色契约与命令规范」四大痛点，建立 **「双通道水位探针 + 动态智力阈值 + Arm/Fire 稳态边界点火 + 三域统筹矩阵 + 压缩后强制重载锁」** 完整体系。

---

## 2. 双通道水位探针 (`scripts/agent-context.py`) 与「70% / 60% / 50% 黄金比例法则」

通过 [`scripts/agent-context.py`](../scripts/agent-context.py) 跨 Harness 实时获取各窗格的精确上下文消耗、当前模型、**实际自动压缩窗口 (`WIN`)** 与**思考等级 (`THINK`: `off/low/medium/high/xhigh`)**：
- **通道 1（插件高速通道）**：优先读取 `herdr-agent-usage` 插件的 StatusLine 缓存/Metadata；
- **通道 2（原生 `.jsonl` 兜底通道）**：通过 `herdr agent list` 的 `agent_session.value` 绑定本地 `.jsonl` 会话文件执行 **256KB 有界尾部倒扫**，结合窗格底部状态栏与配置文件自动识别实时模型与思考深度，并**每次巡检时自动将实时状态增量同步至 `.agents/session.json`**。

### 2.1 水位状态定义
- **`WIN`（自动压缩死线）**：Harness 触发强制自动压缩的实际会话上限（注意：部分 Harness 如 `agy` 虽底层模型支持 1M，但客户端固定在 **`262k` (`262,144`)** 触发自动压缩，故 `WIN` 必须以实际自动压缩死线为准）；
- **`🟡 ARMED`（趁空闲压缩线）**：**不打断当前在途任务**；提醒 `Dispatcher` 趁任务刚结束处于 `idle` 空闲边界时顺手发起主动压缩；
- **`🔴 DANGER`（派活前必压红线）**：距离自动压缩死线过近，**派发下一条指令前必须先完成压缩**，否则任务做一半必撞上自动压缩。

### 2.2 三维智力抗衰分档规则
以 `medium` 思考为基准：`70% / 60% / 50%`；`high` 思考 `+5%`，`low` 思考 `-8%`：

| 模型智力与抗衰档位 | 宏观模型特征画像（不绑定易过时的具体模型名） | `medium` 思考压缩水位 (`🟡 ARMED` / `🔴 DANGER`) | 思考等级微调规律 (`low` / `high`) | 典型窗口换算示例 |
| :--- | :--- | :---: | :---: | :--- |
| **Tier S：高智商旗舰档** | 大规模前沿深度推理旗舰模型，逻辑链深、最抗长文噪音干扰 | • **`70%`** 趁空闲压 (`ARMED`)<br>• **`80%`** 派活前必压 (`DANGER`) | • `low`：`62%` / `73%`<br>• `high`：`75%` / `85%` | 以 **`262k` 窗口** 为例：<br>• `low`：`162k` / `191k`<br>• **`medium`：`183k` / `209k`**<br>• `high`：`196k` / `222k` |
| **Tier A：主力全能编码档** | 大规模通用或主力编码模型（含大型 MoE 及高速长窗主力模型），太长时易遗忘边缘细节 | • **`60%`** 趁空闲压 (`ARMED`)<br>• **`72%`** 派活前必压 (`DANGER`) | • `low`：`52%` / `65%`<br>• `high`：`65%` / `77%` | 以 **`262k` 窗口** 为例：<br>• `low`：`136k` / `170k`<br>• **`medium`：`157k` / `188k`**<br>• `high`：`170k` / `201k` |
| **Tier B：中等参数开源 / 轻量档** | 十余 B 至数十 B 参数级开源模型或轻量高速模型（**铁律：物理大窗口 ≠ 高有效智力上限**，长文易降智，需勤压快跑） | • **`50%`** 趁空闲压 (`ARMED`)<br>• **`62%`** 派活前必压 (`DANGER`)<br>*(超大窗下 `ARMED` 最高封顶 `90k~100k`)* | • `low`：`42%` / `55%`<br>• `high`：`55%` / `67%` | 以 **`163k` 窗口** 为例：<br>• `low`：`68k` / `89k`<br>• **`medium`：`81k` / `101k`**<br>• `high`：`90k` / `109k` |

---

## 3. 侦测武装与稳态点火分离 (`Arm / Fire Separation` —— 两大最佳点火窗口)

严禁在任务执行中途打断压缩，也严禁在 `Reflector` 复盘前盲目清理。实行 **「双通道侦测武装 (Arm) + 仅在 `idle`/`done` 稳态边界点火 (Fire)」**：

- **双通道武装 (Arm)**：
  1. **数值通道**：`agent-context.py` 报 `🟡 ARMED` 或 `🔴 DANGER`；
  2. **语义通道**：`pipeline.jsonl` 的 `PLAN` 事件标注了 `"ctx": "compact"` 或 `"ctx": "clear"`。
- **稳态点火窗口 A：派活前水位闸门 (`Pre-Dispatch Gate` —— 支持 `strict` / `relaxed` 双档松紧度)**：
  `Dispatcher` 按 `.agents/environment.json` 中 `context_monitor.probe_policy` 设定的策略执行派活前检查：
  - **`"strict"`（严格逐步必检，适合 Tier B 开源/短窗模型、挂载了外部自动压缩插件或大颗粒度特性）**：每次唤醒下游角色前均执行 `python3 scripts/agent-context.py <role>`；
  - **`"relaxed"`（宽松按需抽检，适合大窗口 Tier S/A 模型与常规小切片）**：利用结项全检建立底数，常规 `round == 1` 顺畅推进中途免检；仅当进入多轮返工（`round >= 2` / `REPLAN`）或某角色开局距 `ARMED` 不足 `35k` 且被二次唤醒前才执行单点抽检。
  一旦检出目标角色处于 `🔴 DANGER`（或处于 `🟡 ARMED` 且即将派发重度任务），**必须先下发 `compact_cmd` 并 `--wait` 完成后，再下发业务任务指令**，从根源消灭「刚发命令就自动压缩」与「任务做一半自动压缩」。
- **稳态点火窗口 B：特性结项且 `Reflector` 采蜜完成后的空闲窗口 (`Post-Reflector Idle Window`)**：
  1. **🔒 `Reflector` 采蜜保护锁**：当特性包含波折信号需触发 `Reflector` 时，在 `Reflector` 跨窗格访谈并落盘经验之前，**严禁对任何参与角色执行压缩或清空**，保留 100% 原始排障现场；
  2. **⏱️ 等待挪位 (`Shift the Wait`)**：待 `Reflector` 采蜜完成（或无波折直接结项）进入 `DONE` 后，由 `Dispatcher` 对所有已达 `🟡 ARMED`（或命中 `PLAN.ctx == "compact"`）的常驻角色发起主动压缩，将 20~60 秒的压缩耗时隐藏在特性切换的空闲间隙中。

---

## 4. 三域统筹权责矩阵与防失忆重载锁 (`3-Domain Matrix & Post-Compaction Reload Lock`)

| 治理域与覆盖角色 | 统筹发起人 | 何时 `/compact`（EESV 结构化提纯） vs 何时 `/clear`（清空并重塑） | 压缩后防失忆闭环 (`Reload Lock`) |
| :--- | :--- | :--- | :--- |
| **域 1：后厂与审查全员 (14 个)**<br>`tdd`, `coding`, `ops`, `e2e`, `debugger`, `explorer`, `security-redteam`, `reviewer-*`, `reflector` | **`Dispatcher`<br>集中统筹** | • **全员默认优先 `/compact`（含 `ops`、`e2e`）**：各角色在运行中均会积累宝贵的环境、路由与代码拓扑经验，绝不每完结一个特性就无脑清空；在「派活前闸门」或「采蜜后空闲期」发送带 **EESV 四要素锚点**（Ground Truth / Continuity Ledger / Open Loops / Delta）的 `compact_cmd`；<br>• **仅在 2 种场景下执行 `Clear & Re-Prime`（`/clear` + 立即重读角色书）**：① 跨完全无关业务大域（`PLAN.ctx == "clear"` 且 `Reflector` 已完成）；② 角色陷入死循环或上下文被错误尝试严重污染（`STALLED`）。 | 若 `Dispatcher` 刚刚对其执行了主动压缩，或 `agent-context.py` 检测到 `+JUST_COMPACTED`（上一轮刚经历了自动压缩断崖：`curr < prev * 0.6`），`Dispatcher` 在下发下一条指令时**必须在开头强制附带「请先调用读取工具重读 `roles/<role>.md`」**！ |
| **域 2：中枢调度官 (1 个)**<br>`dispatcher` 自身 | **`Dispatcher` 自检<br>+ 顶层 `AGENTS.md`** | `Dispatcher` 在特性结项或派活间隙运行 `agent-context.py` 时同步检查自身水位；若达 `🟡 ARMED`，在特性间空闲期主动触发自压缩（或向人类汇报后压缩）。 | **顶层 `AGENTS.md` 布尔判据强制重载锁**：任何角色一旦发现上下文顶部存在自动压缩摘要（如 `<CONTEXT_SUMMARY>`），且**在该摘要之后的未压缩记录中未曾调用读取工具读过自身 `roles/<role>.md` 原文**，第 1 个动作必须无条件重读 `roles/<role>.md` 与 `tools/herdr.md`！ |
| **域 3：前店规划官 (1 个)**<br>`planner` (窗口 1) | **人类主导<br>+ `Planner` 提议** | **`Dispatcher` 严禁从后台触碰窗口 1 上下文**！实行阶段分治：<br>• **讨论未落盘中途高水位** ➔ 提议人类执行原地 `/compact`；<br>• **契约落盘后里程碑高水位** ➔ 向 `changes/KANBAN.md` 的 `📌 规划台交接备忘` 区写入 **EESV 四要素交接单**（① 已落盘契约路径 Ground Truth；② 人类偏好与否决废案 Continuity Ledger；③ 未决悬念 Open Loops；④ 本轮增量 Delta），经人类确认后执行 `/clear` + 重读 `roles/planner.md` 满血唤醒 **「Planner 二世」**。 | 「Planner 二世」启动首回合直接读取 `roles/planner.md`、`tools/herdr.md`、`GLOSSARY.md` 与 `KANBAN.md` 交接备忘，实现 100% 零噪音无缝继任。 |
