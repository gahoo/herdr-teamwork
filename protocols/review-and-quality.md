# 两阶段审查、专家分诊路由与证伪裁决协议 (`protocols/review-and-quality.md`)

> **适用角色**：`planner`、`dispatcher`、`reviewer-lead` 及全体垂直审查专家（`reviewer-quality` / `reviewer-arch` / `reviewer-perf` / `reviewer-security` / `reviewer-ux`）
> **配套模板**：[`templates/review.template.md`](../templates/review.template.md)

为彻底根治“带着宏观架构硬伤进入编码”、“Lead Reviewer 偷懒不派活”以及“Reviewer 走过场无脑 Approve（Rubber Stamping）”，全系统实行**两阶段拦截、三拍点将、具象特征路由、证伪行号举证与红黄分级**协议。

---

## 1. 两阶段审查全链路划分 (Two-Stage Review Pipeline)

1. **🏛️ 第一阶段：计划期宏观与架构预审 (Stage 1: Macro & Arch Consultation —— 窗口 1 按需触发)**
   - **触发时机**：`Planner` 起草完 `changes/<id>/spec.md` 后，若命中下方 `§2《垂直专家具象触发特征矩阵》` 中的高风险特征（如跨模块架构重构、核心数据模型演进、高危鉴权机制、复杂并发/缓存策略或复杂交互状态），在呈交人类最终拍板前触发（常规轻量需求可跳过）。
   - **执行方式**：**略过 `reviewer-lead`**，由 `Planner` 直接按需唤醒或复用对应的垂直专家（如 **`reviewer-arch`**、**`reviewer-security`**、**`reviewer-perf`** 或 **`reviewer-ux`**），评估深模块合理性与 `gitnexus impact` 爆炸半径，将宏观修正直接融入 `spec.md` 并记录于 `review.md` Stage 1 章节（`standard` 模式下窗格常驻保留上下文至 Feature 结项）。
   - **升级形态：圆桌辩论 (Roundtable Debate)**：当议题同时满足「单向门 + 跨 ≥2 个专业维度显著权衡 + 2~3 套互斥候选方案」时，`Planner` 立题并 Fork 一个**一次性圆桌主席分身**（加载 [`playbooks/roundtable-debate.md`](../playbooks/roundtable-debate.md)），从 `§2` 矩阵中挑选 2~4 位正交专家组织「背靠背亮牌 ➔ 冲突方定向交锋(1 轮) ➔ 主席裁决」，落盘 `changes/<id>/roundtable.md` 后分身退出；`Planner` 向人类呈报裁决摘要，**人类点头后**方固化进 `spec.md` 与 `docs/adr/`。

2. **🔬 第二阶段：实施期测试与代码细节/防偏离终审 (Stage 2: Implementation & Drift Gate —— 后厂强制门禁)**
   - **子阶段 2A：测试代码前置快检 (Red Test Gate)**：在 `tdd` 写完 Red Test 后、`coding` 动手前，由 **`reviewer-lead` 独立执行**（仅在涉及红队 PoC 转化时点名 `reviewer-security` 协审）。严格按《4 维测试审查清单》（契约忠实度、防假阳性与硬编码证伪、边界与异常覆盖、角色红线核查）拦截弱断言与契约偏差。
   - **子阶段 2B：业务实现与防偏离终审 (Code & Drift Gate)**：在 `coding` 自证测试全绿后触发，实行**“主审开方点将 ➔ Dispatcher 抓药调度 ➔ 主审合议裁决”**三拍闭环：
     - **第 1 拍（主审分诊点将）**：`reviewer-lead` 仅运行 `git diff --stat` 与 `gitnexus detect-changes`（**严禁自己跑静态质量分析、编译检查、测试或 `impact`**）。若属 Tier 1（<20 行纯文档/文案/样式微调），直接签字放行；若属 Tier 2/3，严格依据下方 `§2《垂直专家具象触发特征矩阵》` 输出一行点将令并结束回合：
       ```text
       TRIAGE_RESULT: Tier 2 | SPAWN_EXPERTS: [reviewer-quality, reviewer-perf] | FOCUS: "核查 xxx 模块"
       ```
     - **第 2 拍（Dispatcher 并发代跑）**：`dispatcher` 解析点将令，复用已常驻的专家窗格（若首次调用则切出对应专家 Pane）、传入 `FOCUS` 指令并 `--wait` 等待，收集 ≤25 行专家简报（`standard` 模式下保留专家窗格至当前 Feature 结项后统一打理上下文；`worktree` 模式下可即用即关或随工作区销毁）。
     - **第 3 拍（主审 ROI 仲裁与落盘）**：`dispatcher` 将全部专家简报喂回 `reviewer-lead`，由主审权衡冲突、按 **5 级证据阶梯** 剔除无确定性触发路径的纯理论担忧，统一按 [`templates/review.template.md`](../templates/review.template.md) 写入 `changes/<id>/review.md`。

---

## 2. 垂直专家具象触发特征矩阵 (Concrete Routing Heuristics)

供 **Stage 1 `Planner`（预审/圆桌选将）** 与 **Stage 2B `Reviewer-Lead`（第 1 拍分诊点将）** 共同遵循：

| 专家角色 ID | 具象触发条件（命中任一特征即点名唤起） |
| :--- | :--- |
| **`reviewer-quality`** | **【Stage 2B 专属必选】凡改动包含任何业务源码 (`src/`) 或测试代码 (`tests/`)**（非纯文档/注释微调），100% 必调！负责跑跨语言对等静态代码健康度与类型分析（TS `fallow+tsc` / Rust `clippy` / Go `golangci-lint` / Python `ruff+mypy`）。 |
| **`reviewer-arch`** | 1. `gitnexus detect-changes` / `impact` 显示风险 `>= MEDIUM` 或波及业务流 `>= 2` 个；<br>2. 触及公共核心层、全局状态管理或数据库 Schema；<br>3. 跨 `>= 3` 个模块目录修改，需评估深模块边界与单向数据流合理性，或怀疑实现偏离了 `spec.md` 既定架构边界。 |
| **`reviewer-security`** | 1. 触及认证鉴权、权限守卫、加密脱敏、资金/计费/敏感状态流转；<br>2. 含数据库查询、文件 I/O、系统命令执行、富文本渲染或新增外部 API；<br>3. 修改了项目依赖清单（`Cargo.toml` / `go.mod` / `pyproject.toml` / `package.json`），或当前变更集存在 `security-poc.md`。 |
| **`reviewer-perf`** | 1. 数据层涉及循环内查询、大表查询、索引/缓存策略或并发锁；<br>2. 视图层涉及高频事件监听、定时器、海量节点渲染或复杂闭包。 |
| **`reviewer-ux`** | 1. 涉及前端交互组件、弹窗模态框、表单校验或布局样式；<br>2. 涉及键盘快捷键流、焦点捕获管理 (Focus Trap)、无障碍属性或用户提示文案。 |

---

## 3. 防橡皮图章与防过度挑刺双保险：证伪举证 + 红黄分级

1. **🛡️ 核心防线证伪核查 (Proof of Defense —— 杜绝无脑 Approve)**：
   - 任何 Reviewer 在给予通过前，必须在报告中明确指出本次改动**最脆弱的边界/异常点**，并**贴出源码或测试中实施防御的确切文件名与行号 (`file:line`)**。拿不出确切防御行号，严禁给予 `APPROVED`。
2. **🔍 5 级证据阶梯过滤（剔除脑补的理论担忧）**：
   - Level 1 仅凭直觉猜测 ➔ Level 2 仅指出行号 ➔ Level 3 推演出确切的触发输入与失败路径 ➔ Level 4 单测/脚本实证复现 ➔ Level 5 实机复现。
   - **凡未达到 Level 3（确切失败路径）或 Level 4（实测复现）的纯理论假想担忧，一律剔除或降级，严禁列为 `🔴 BLOCKER` 阻塞流水线！**
3. **🚦 审查意见三级定性 (Severity Triage —— 杜绝过度挑刺与看板污染)**：
   - 🔴 **`[BLOCKER / 致命阻断]`**：违背 `spec.md` 契约、存在安全/崩溃/泄漏漏洞、测试假阳性、缺少核心边界防御或静态质量退化（如 `fallow delta > 0` / `clippy` 报错 / `golangci-lint` 报错）。➔ **触发 `CHANGES_REQUESTED` 由 `Dispatcher` 打回返工（最多允许 2 轮返工，超限挂起为 `WAITING_DECISION` 交人类裁决）**。
   - 🟡 **`[CONSTRUCTIVE / 建设性演进建议]`**：当前功能正确且安全，但存在中远期可优化的演进点。➔ **不阻断当前流水线（状态仍为 `APPROVED` 直接放行），由 `Dispatcher` 记录条数至 `pipeline.jsonl` 并在窗口 2 验收时提醒人类；人类确认采纳后再主动交窗口 1 `Planner` 记入 `KANBAN.md` Inbox**！
   - ⚪ **`[NITPICK / 主观风格吹毛求疵]`**：已被 Linter 覆盖的格式问题或个人命名偏好。➔ **绝对禁止输出**。
