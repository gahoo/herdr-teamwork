# Implementation Tasks: <特性名称> (`changes/<id>/tasks.md`)

> **维护铁律**：
> 1. **纯微观编码任务清单**：由 `Planner` 建档拆解，专供 **`TDD Agent` (`tdd`)** 与 **`Coding Agent` (`coding`)** 执行并勾选 `- [x]`（`Dispatcher` 不触碰此文件，运行时状态流转全归 `pipeline.jsonl`）。
> 2. **纵向高内聚切片**：每个 Step 聚焦最相关的少量文件，完成一项即勾选一项；若实现途中存在关键方案取舍，由 `coding` 在对应条目下内联追加一行 `> [Decision]: <取舍原因与实证依据>`。

---

## Step 1: <切片 1 标题 — 对应 `AC-1`>
- **目标测试文件**：`tests/<domain>/<file>.test.ts`
- **目标业务文件**：`src/<domain>/<file>.ts`
- [ ] **`[TDD]`**：编写覆盖 `AC-1` 正常路径与空值/异常边界的失败测试（Red Test），验证测试因预期特性未实现而见红。
- [ ] **`[Coding]`**：在 `src/<domain>/<file>.ts` 中实现核心逻辑，运行测试迭代至全绿（Green），并完成类型检查与 `gitnexus detect-changes` 自检。

---

## Step 2: <切片 2 标题 — 对应 `AC-2`>
- **目标测试文件**：`tests/<domain>/<file2>.test.ts`
- **目标业务文件**：`src/<domain>/<file2>.ts`
- [ ] **`[TDD]`**：编写覆盖 `AC-2` 场景及上游调用链回归守护的失败测试（Red Test）。
- [ ] **`[Coding]`**：完成业务代码实现与门面导出，确保局部与存量回归测试全绿（Green）。
