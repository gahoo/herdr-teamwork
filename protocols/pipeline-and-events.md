# 流水线编排、事件溯源与故障自愈协议 (`protocols/pipeline-and-events.md`)

> **适用角色**：`planner`（立项定制 `PLAN` 事件）、`dispatcher`（驱动流水线、续写 `STEP`/`REPLAN`、跨流水线监听与故障自愈）、`reflector`（审计异常事件流）。
> **关联总纲**：[`SKILL.md §5`](../SKILL.md) | **关联工具配方**：[`tools/herdr.md §[H-3] & §[H-6]`](../tools/herdr.md)

---

## 1. 动态可调流水线预设模板与专项战术剧本 (Customizable Pipeline Presets & Tactical Playbooks)

以下通道仅作为**基础预设起点**，`Planner` 在【法定节点 1】必须向人类展示拟启用的具体角色数组 `pipeline`，支持按需动态增删、插件化调节：

- **微型轻量预设 (`Quick-Fix`)**（<20 行 / 纯文案 / 纯样式 / 简单配置）：
  `["coding", "reviewer-lead:2B", "ops"]`
- **标准功能预设 (`Standard`)**（20~150 行 / 局部新特性 / 常规组件）：
  `["tdd", "reviewer-lead:2A", "coding", "reviewer-lead:2B", "ops"]`（可按需插拔 `"e2e"`）
- **全量高危预设 (`Full-Rigor`)**（核心架构 / 鉴权计费 / 数据库迁移）：
  `Stage 1 预审` + `["tdd", "reviewer-lead:2A", "coding", "security-redteam", "tdd", "coding", "reviewer-lead:2B", "e2e", "ops"]`
- **探索性原型刺探预设 (`[SPIKE]`)**（UI/交互方案对比或技术可行性刺探，用完即焚）：
  `["coding", "ops"]`（跳过 `tdd` 与代码规范审查，详见 [`playbooks/prototype-spike.md`](../playbooks/prototype-spike.md)，拍板后销毁临时分支）
- **单一指标科学爬山预设 (`[HILLCLIMB]`)**（针对耗时/内存/吞吐量等单一量化指标执行“测基线-改代码-退步即回滚”循环）：
  `["coding", "reviewer-perf", "ops"]`（详见 [`playbooks/hillclimb.md`](../playbooks/hillclimb.md)）
- **阶段性全库架构深度巡检 (`Arch-Audit`)**（每完成 3~5 个特性扫描浅模块并产出 HTML 体检报告）：
  `["reviewer-arch"]`（必要时协同 `"explorer"`，详见 [`playbooks/arch-audit.md`](../playbooks/arch-audit.md)）
- **排障重排序列 (`REPLAN: Bugfix`)**（窗口 2 验收报障 / `e2e` 崩溃 / 终审回归失败时由 `Dispatcher` 追加）：
  `["debugger", "tdd", "coding", "reviewer-lead:2B", "ops"]`

---

## 2. `changes/<id>/pipeline.jsonl` 事件流规范 (8+ 字段扁平自包含快照)

`changes/<id>/pipeline.jsonl` 合一承载动态定制的 Agent 工序序列与实时执行轨迹（Event Sourcing），随特性结项一并归档为“黑匣子飞行记录仪”。**仅允许 `Planner` 写入首行 `PLAN`，`Dispatcher` 独占追加后续事件；下游执行角色严禁触碰此文件。**

每一行均为合法的单行 JSON（**严禁美化折行**），确保 `tail -n 1` 即可获取完整上下文：

```jsonl
{"ts":"2026-10-27T08:00:00Z","id":"001-auth","event":"PLAN","mode":"worktree","ws":"ws-001","port":3001,"branch":"feat/001-auth","ctx":"compact","pipeline":["tdd","reviewer-lead:2A","coding","reviewer-lead:2B","ops"],"round":1,"state":"QUEUED","msg":"节点1对齐完成"}
{"ts":"2026-10-27T08:02:10Z","id":"001-auth","event":"STEP","ws":"ws-001","port":3001,"step":"tdd","round":1,"state":"RUNNING","msg":"Red Test 编写完成"}
{"ts":"2026-10-27T08:15:30Z","id":"001-auth","event":"STEP","ws":"ws-001","port":3001,"step":"reviewer-lead:2B","round":1,"state":"WAITING_ACCEPTANCE","constructive":1,"msg":"Stage 2B 终审 APPROVED [含1条CONSTRUCTIVE建议]，服务已在 http://localhost:3001 就绪待验收"}
```

### 2.1 核心字段与枚举定义
- **`event` 事件类型（3 种）**：
  - `"PLAN"`：`Planner` 在节点 1 拍板落盘时写入的首行创世事件，定义 `mode`、`ws`、`port`、`branch`、`ctx` 及 `pipeline` 数组；
  - `"STEP"`：`Dispatcher` 驱动每一步下游角色推进或完成时追加的常规状态事件；
  - `"REPLAN"`：验收报障、终审打回或中途变阵时，由 `Dispatcher` 追加的流水线重排事件。
- **`state` 核心状态机枚举（6 种）**：
  - `QUEUED`：已立项待启动；
  - `RUNNING`：自动流转推进中；
  - `WAITING_ACCEPTANCE`：代码与审查通过，服务/产物就绪，待人类实机验收；
  - `WAITING_DECISION`：审查阻断、返工满 2 轮、合并冲突或发现契约缺陷（`SPEC_DEFECT`），挂起待人类拍板；
  - `STALLED`：下游角色故障自愈失败，环境挂起；
  - `DONE`：已通过验收并由 `ops` 完成合并发布与收尾。
- **`ctx` 跨特性上下文策略枚举（专供 `standard` 常驻模式）**：
  - `"keep"`：强关联连续小切片，直接保留上下文继续下一特性；
  - `"compact"`：默认推荐，结项后主动执行结构化压缩，沉淀项目演进记忆；
  - `"clear"`：跨完全无关业务域，结项后清空重置并重读角色卡。

---

## 3. `Master Dispatcher` 跨流水线事件监听与 FIFO 认知队列提取

在主工作区右窗格（窗口 2），`Master Dispatcher` 通过以下命令实现零轮询跨任务监听与待处理队列提取：

```bash
# 1. 挂起后台单次触发监听命令（任一任务进入待处理状态即退出并自动唤醒窗口 2 总控台）：
tail -n 0 -f changes/*/pipeline.jsonl | grep --line-buffered -m 1 -E '"state":"(WAITING_|STALLED|DONE)"'

# 2. 提取全部待人类处理的 FIFO 认知队列（按时间戳升序）：
tail -q -n 1 changes/*/pipeline.jsonl | jq -s 'map(select(.state == "WAITING_ACCEPTANCE" or .state == "WAITING_DECISION" or .state == "STALLED")) | sort_by(.ts)'
```

---

## 4. 下游 Agent 故障自愈三步法 (Self-Healing SOP)

当 `Dispatcher` 执行同步等待（`--wait`）发生超时或异常时，**严禁越权代庖修改业务或测试代码**，必须严格按 [`tools/herdr.md §[H-6]`](../tools/herdr.md) 依次执行：

1. **观察与中断重试**：先读取目标窗格状态与最近输出，检查是否仍在正常 `working`；若确系卡死，发送 `ctrl+c` 中断当前回合并确认恢复 `idle` 就绪后重发指令重试。
2. **重建窗格重启进程**：若中断重试无效，切分新窗格并关闭旧异常窗格，通过 `scripts/session-snapshot.py restore --agent <role>`（或按 `environment.json` 的 `cli_args` + `resume_flag`）重新启动该角色实例并恢复会话。
3. **挂起上报**：若重建后仍失败，`Dispatcher` 向 `changes/<id>/pipeline.jsonl` 追加 `"state": "STALLED"` 事件并上报窗口 2 交人类介入。
