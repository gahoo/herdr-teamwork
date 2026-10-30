# Playbook: 探索性快速原型刺探 (`prototype-spike`)

> **设计溯源**：融合自敏捷开发 Spike（技术刺探）实践、Matt Pocock 的 `prototype` 技能以及 Lauren Tan (`pstack`) 的 `exhaust-the-design-space` 原则。

---

## 1. 适用场景与触发条件 (When to Use)

> **核心信条**：当面对未知的交互体验或未验证的技术假设时，写 1000 字的推测性文档不如花 15 分钟跑通一个可交互/可测量的粗糙原型。

在以下任一条件满足时触发本剧本：
1. **UI / 交互形态吃不准**：人类和 `planner` 对某个功能的布局、交互手感或视觉呈现存在多种设想（如方案 A 分栏 vs 方案 B 抽屉），仅靠文字描述无法拍板。
2. **技术可行性 / 性能边界吃不准**：不确定某个第三方库、算法或架构改动在真实场景下是否可行。
3. **反思闭环触发**：`reflector` 在 `reflections/<domain>.md` 中记录了 `🔬 SPIKE_CANDIDATE`（待验证探索项）。

---

## 2. 角色分工链路 (Role Handoff Chain)

```
[planner] 侦测不确定性或读取 SPIKE_CANDIDATE ➔ 向人类提议发起 [SPIKE]
        │ (人类确认开启)
        ▼
[planner] 创建极简 changes/spike-<id>/spec.md (标记 [SPIKE])
        │
        ▼
[dispatcher] 识别 [SPIKE] 标记 ➔ 跳过 TDD 与常规 Review，直接派发 [coding]
        │
        ▼
[coding] (配合 [ops]) 快速构建单文件 HTML 原型或 A/B 可切换原型 / 压测探针
        │ (写入 SPIKE_READY)
        ▼
[Human + planner] 亲自体验对比并拍板结论 ➔ 结论写入正式 spec.md / ADR
        │
        ▼
[dispatcher] 立即销毁/回滚 Spike 临时代码（用完即焚，严禁直接合入主干！）
```

---

## 3. 分角色执行规程 (Step-by-Step by Role)

### 阶段一：`planner` 立项（严格限定问题与边界）
1. 在 `KANBAN.md` 新增带有 `[SPIKE]` 前缀的任务（如 `spike-editor-layout`）。
2. 在 `changes/spike-<id>/spec.md` 中仅需写明三件事：
   * **待回答的核心问题（The Question）**：本次刺探唯一要验证的假设是什么？
   * **候选对比方案（2~3 Variants）**：例如要求在同一个预览路由下提供方案 A 与方案 B 的顶部切换按钮（Toggle），以便人类同屏直观对比。
   * **豁免声明**：明确标注 `[SPIKE]` 模式——**免写单元测试、免除静态代码规范审查、允许硬编码假数据（Mock Data）**。

### 阶段二：`dispatcher` 极简路由
* 识别到任务带有 `[SPIKE]` 标签时，**跳过 Node 2 (`tdd`) 及所有 `reviewer-*` 节点**，直接将任务由 Node 1 (`planner`) 路由至 Node 3 (`coding`)。

### 阶段三：`coding`（协同 `ops`）极速构建原型
`coding` 读取本剧本后，按问题类型选择以下两种形态之一快速实现：
1. **状态模型 / 逻辑验证型**：构建一个零外部依赖、单文件自包含的交互式 `changes/spike-<id>/prototype.html`（或独立探针脚本），把内部状态机直接渲染在界面上供人类拨弄验证。
2. **UI 布局 / 交互对比型**：在隔离分支或临时路由下，构建 **2~3 个风格/结构迥异的候选变体（Variants）**，并在页面角落提供一个浮动的 **Variant Switcher（方案切换器）**，让人类无需切分支即可秒级切换对比手感。
3. 如需启动本地服务预览，通知 `ops` 在子窗格拉起预览服务，随后写入 `SPIKE_READY` 并在 `changes/spike-<id>/result.md` 中写明预览地址或实测对比数据。

### 阶段四：拍板转化与「用完即焚」铁律
1. **人类拍板**：人类在浏览器中点击体验或审阅实测数据后，在 Window 1 向 `planner` 给出明确裁决（例如：“采用方案 B 的布局，加上方案 A 的快捷键”）。
2. **结论固化与知识提炼（Capture the Findings before Teardown）**：
   * 在销毁临时分支前，`coding` 或 `planner` 必须将本次原型刺探验证得出的**非平凡技术事实**（如：跑通的数据结构/状态机定义、关键 API 调用方式、实测性能数据或选定的布局参数）提炼归档至 `changes/spike-<id>/result.md`；
   * `planner` 将验证后的结论融入正式 Feature 的 `spec.md`（若满足 ADR 三条件，则写入 `docs/adr/` 并指向 `changes/spike-<id>/result.md`）；
   * 若源自 `reflections/<domain>.md` 的 `🔬 SPIKE_CANDIDATE`，将其状态更新为 `✅ DETERMINISTIC_LESSON`。
3. **🔥 用完即焚（Throwaway Discipline）**：
   * **严禁将 Spike 期间编写的粗糙代码直接 Merge 进主干分支！**
   * 结论落盘后，`dispatcher` 必须清理/销毁 Spike 分支（或执行 `git reset`/`checkout` 清空临时改动），随后为正式 Feature 启动干净的标准 `TDD -> Coding -> Review` 生产流水线。
