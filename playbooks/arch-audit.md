# Playbook: 全库架构深度巡检与模块深化 (`arch-audit`)

> **设计溯源**：融合自 Matt Pocock 的 `improve-codebase-architecture` 与 John Ousterhout《软件设计哲学》的深模块（Deep Modules）理论，专为多 Agent 协同场景定制。

---

## 1. 适用场景与触发条件 (When to Use)

当代码库经过多轮快速特性迭代后，AI Agent 的局部最优修改往往会加速软件熵增（浅模块泛滥、跨模块耦合加深、职责边界模糊）。在以下任一条件满足时触发本剧本：
1. **里程碑定期触发**：`KANBAN.md` 每累计完成 **3~5 个 Feature**（或完成一个大版本里程碑）时，由 `planner` 主动向人类提议执行。
2. **摩擦信号触发**：`reviewer-arch` 在日常审查中连续发现浅模块（Shallow Modules）/透传层，或 `reflector` 在复盘 `pipeline.jsonl` 时发现多起由于架构耦合导致的反复打回，抛出 `ARCH_AUDIT_NEEDED` 建议。

---

## 2. 角色分工链路 (Role Handoff Chain)

> ⚠️ **严禁由 `planner` 亲自扫描全库源码！** `planner` 受工具白名单约束且需保护主控台（Window 1）上下文不被海量源码污染。

```
[planner / reviewer-arch / reflector] 侦测信号并向人类提议
        │ (人类确认开启)
        ▼
    [planner] 在 KANBAN.md 创建巡检项 (如 arch-audit-01)，写入 SPEC_READY
        │
        ▼
  [dispatcher] 唤醒常驻架构专家 [reviewer-arch] (必要时协同 [explorer])
        │
        ▼
[reviewer-arch] 执行全库扫描，产出可视化 HTML 报告与 Markdown 重构清单
        │ (写入 ARCH_AUDIT_DONE)
        ▼
    [planner] 与人类一起审阅报告，挑选高价值深化项拆解为正式重构任务
```

---

## 3. 分角色执行规程 (Step-by-Step by Role)

### 阶段一：`planner` 立项与范围界定
1. 向人类确认本次巡检的范围（全库扫描，或聚焦特定核心子系统/目录）。
2. 创建 `changes/arch-audit-<id>/spec.md`，声明巡检范围及近期痛点模块。
3. 向 `changes/pipeline.jsonl` 追加立项事件：
   ```json
   {"ts":"...","feat":"arch-audit-01","node":1,"role":"planner","status":"SPEC_READY","summary":"立项全库架构深度巡检，交由 reviewer-arch 扫描浅模块与耦合摩擦点"}
   ```

### 阶段二：`reviewer-arch` 全库扫描与报告生成（核心执行者）
`reviewer-arch` 被唤醒后，按以下维度对目标代码库进行系统性深潜（可调用 GitNexus 依赖图分析或配合 `explorer`）：

1. **寻找「浅模块（Shallow Modules）」与深化机会（Deepening Candidates）**：
   * 识别接口复杂（参数繁多、导出函数零碎、透传调用多）但内部实际承担逻辑很薄的模块。
   * 识别完成同一个业务动作需要调用方按特定顺序串联调用 3 个以上模块的**时序分解（Temporal Decomposition）**坏味道。
   * 识别跨模块共享可变状态、内部私有实现被外部直接 `import`、或“一件事在代码库里有新旧两种写法”的 **AI 劣化重灾区**。
2. **设计「加深模块（Module Deepening）」的候选方案**：
   * 对每个发现的痛点，构思如何通过**收敛窄接口（Narrow Interface）**将内部复杂度、状态流转与边缘情况隐藏在单一深模块背后，并提供干净的测试接缝（Test Seam）。
3. **双格式产物落盘**：
   * **产物 A（人类决策友好）：`changes/arch-audit-<id>/arch-report.html`**
     生成一份单文件自包含的可视化 HTML 架构体检报告（内嵌简洁 CSS 与 Mermaid 依赖对比图），按**改造收益/紧迫度**从高到低展示 Top 3~5 个架构深化候选点（每个候选点包含：现状耦合图、具体痛点文件行号、深化后的目标接口签名、改造风险定级）。
   * **产物 B（Agent 消费友好）：`changes/arch-audit-<id>/result.md`**
     结构化列出每个候选重构项的边界、涉及文件与验收标准。
4. 向 `changes/pipeline.jsonl` 追加完成事件：
   ```json
   {"ts":"...","feat":"arch-audit-01","node":5,"role":"reviewer-arch","status":"DONE","summary":"架构深度巡检完成，已生成可视化报告 arch-report.html 共包含 N 个模块深化建议"}
   ```

### 阶段三：`planner` 引导人类决策与任务转化
1. `planner` 提示人类在浏览器中打开 `changes/arch-audit-<id>/arch-report.html` 直观浏览。
2. 对人类挑中的候选改造项，`planner` 通过简短的问答（Grilling）敲定接口细节，将其转化为 `KANBAN.md` 中独立的重构 Feature，进入标准 `TDD -> Coding -> Review` 流水线执行。
