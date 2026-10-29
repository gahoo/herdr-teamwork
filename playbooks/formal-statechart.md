# Playbook: 高危状态机图解与形式化验证 (`formal-statechart`)

> **设计溯源**：融合自 Lauren Tan (`pstack`) 的 `statechart`、`create-formal-verification-skill` 与 `type-system-discipline`（让非法状态不可表示）。

---

## 1. 适用场景与触发条件 (When to Use)

普通示例级单元测试（Example-based Unit Tests）只能覆盖开发者想得到的正向/常规异常路径。当新增或修改的代码触及以下 **5 类高危逻辑** 之一时，必须触发本剧本：
1. **复杂生命周期与状态机**：具有 3 个以上状态及多重外部事件触发转换的模块（如订单流转、调度流水线、连接池会话）。
2. **并发与多执行体协调**：涉及多线程/协程锁、无锁通道、共享状态读写或跨进程通信总线。
3. **分布式重试、崩溃恢复与幂等性**：中途断电/网络超时后重放是否会导致双花、死锁或状态卡死（Stuck State）。
4. **协议 / 语法解析器（Parser / Serializer）**：面对任意畸形、截断或恶意构造字节流时的安全性。
5. **底层内存与 `unsafe` 代码**：如 Rust 中的 `unsafe` 块、指针操作或自定义内存分配。

---

## 2. 角色分工链路 (Role Handoff Chain)

```
[planner / reviewer-arch] 识别到上述 5 类高危特征
        │
        ▼
    [planner] 在 spec.md 中绘制含「禁止状态」的 Mermaid Statechart + 定义系统不变量 (Invariants)
        │ (同时向人类提议是否在本次任务中引入属性测试 / 模型检查工具)
        ▼
[tdd / coding] 1. 在类型层面消灭非法状态；2. 编写属性测试 (Proptest/Fast-Check) 或并发模型验证
        │
        ▼
[reviewer-arch] 对照 spec.md 中的 Statechart 逐条核验状态转换边与不变量测试覆盖
```

---

## 3. 分角色执行规程 (Step-by-Step by Role)

### 阶段一：`planner` 状态图建模与不变量声明
在编写任何实现代码前，`planner` 必须在 `changes/<feat>/spec.md` 中交付两样东西：

1. **可视化状态机图（`stateDiagram-v2`）**：
   * 不仅要画出合法的状态转换边（标注触发事件与守卫条件 Guard），还必须**显式列出绝对不允许进入的「非法/死胡同状态（Violated / Stuck States）」**。
   * 示例结构：
     ```mermaid
     stateDiagram-v2
         [*] --> Idle
         Idle --> Running : DISPATCH
         Running --> Done : PASS
         Running --> Blocked : FAIL (retry < 3)
         Blocked --> Running : RETRY
         Blocked --> Escalated : FAIL (retry >= 3)
     ```
2. **核心安全不变量清单（Safety & Liveness Invariants）**：
   * **安全性（Safety — 坏事绝不发生）**：例如 *“同一时刻最多只有一个 Worker 持有同一任务的写锁”*。
   * **活性（Liveness — 好事终将发生）**：例如 *“任何进入 `Running` 的任务，在有限步内必然到达 `Done` 或 `Escalated`，绝不无限卡死”*。

### 阶段二：`tdd` 与 `coding` 编码锁死与属性验证
1. **类型防呆（Make Illegal States Unrepresentable）**：
   * `coding` 严禁用多个松散的布尔值（如 `isLoading: bool, isError: bool, data: Option<T>`，这会产生 $2 \times 2 \times 2 = 8$ 种组合，其中一半是非法状态）表示状态机！必须使用**代数数据类型 / 可辨识联合（Rust `enum` / TypeScript Discriminated Union / Go 状态结构体）**，从编译器层面直接封死非法状态组合。
2. **引入匹配栈的验证工具（Property-Based Testing / Model Checking）**：
   * 根据语言栈，在 `tdd` / `coding` 阶段针对核心不变量编写自动生成海量随机输入/交错时序的验证测试：
     * **Rust**：使用 `proptest`（随机状态转换序列/解析器输入）、`loom`（确定性穷举并发线程交错时序）或 `kani`（模型检查 `unsafe` 块）。
     * **TypeScript / JavaScript**：使用 `fast-check`（特别是 `fc.commands` 状态机模型测试，自动寻找能破坏不变量的最短操作序列 Shrinking）。
     * **Go**：使用原生 `testing.F`（Fuzzing 模糊测试）与 `-race` 竞态检测器。
     * **Python**：使用 `hypothesis`（含 `RuleBasedStateMachine` 状态机属性测试）。

### 阶段三：`reviewer-arch` 状态图对齐核查
`reviewer-arch` 在审查时：
1. 检查代码中的状态转换枚举与分支是否与 `spec.md` 中的 Mermaid `stateDiagram-v2` 完全一一对应，是否存在未受保护的隐式状态跳转。
2. 若属性测试或并发检查发现了反例（Counterexample），要求在修复后将触发该反例的**最短路径序列**固化为永久回归单测。
