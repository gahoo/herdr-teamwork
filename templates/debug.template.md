# 🕵️ 法医排错与修复规格报告 (`changes/<id>/debug.md` — Forensic Debug & Fix Spec)

> **维护铁律**：由 **`Debug Agent` (`debugger`)** 独占执笔（严格只读 `src/` 与 `tests/`，绝不亲自动手改代码）。采用结论置顶原则（最新一轮排障置顶，历史轮次用文末 `<details>` 折叠）。若根因属于 `spec.md` 原接口契约设计缺陷，必须在顶部醒目标注 `SPEC_DEFECT`。

- **排障轮次**: Round 1 | **触发来源**: 人类验收报障 / E2E 冒烟崩溃 / 终审回归测试失败
- **契约影响**: `IMPLEMENTATION_BUG` (仅实现层修复) / `SPEC_DEFECT` (涉及接口契约调整，需切回窗口 1 `Planner`)

---

## 1. 异常现象与最小复现回路 (Symptom & Minimal Reproducer)
- **复现命令 / 触发路径**：<给出可在数秒内确定性见红的命令或最小复现步骤>
- **观测到的错误表现**：<关键错误码、异常输出或状态偏离现象（严禁倒灌冗长原始堆栈）>

---

## 2. 假说求证与根本原因溯源 (Hypothesis Verification & Root Cause)
- **可证伪假说排查记录**：
  1. 假说 A：<如果根因是 X，观测 Y 将看到 Z> ➔ ❌ 已证伪 / ✅ 已证实（依据：<实测结果>）
- **罪魁祸首定位 (`file:line`)**: `src/path/to/file.ts:Lines`
- **机制推导**: <说明数据流在此处为何发生扭曲/竞态/空指针，以及调用链上下游关系>
- **🛠️ 取证工具记录**: <列出本次调用的 `E2E_PLAYBOOK.md` 路由映射、`gitnexus context/query/impact` 入参与返回发现>

---

## 3. 最小化修复规格 (Fix Specification —— 供 `Coding Agent` 执行)
- **目标文件与符号**: `src/path/to/file.ts` -> `functionName`
- **行级修改指导**: <给出明确、无副作用的修复逻辑说明或最小伪代码，确保最小爆炸半径；若建议临时探针须带 `[DEBUG-xxxx]` 标记>

---

## 4. 防线加固要求 (TDD Lock Specification —— 供 `TDD Agent` 执行)
- **目标测试文件**: `tests/path/to/file.test.ts`
- **必补失败断言**: <明确要求 `tdd` 补充哪几个边界输入与断言以复现并锁死该 Bug>

---

<details>
<summary>📂 历史排障轮次归档 (Historical Debug Rounds)</summary>

<!-- 多轮排障时将旧轮次折叠移入此处 -->

</details>
