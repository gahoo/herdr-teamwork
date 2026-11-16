# 角色算力画像、环境配置与会话快照规范 (`protocols/model-tiers-and-env.md`)

> **适用角色**：`bootstrap`（探测并生成 `.agents/environment.json`）、`planner`（参考角色模型能力拆分任务）、`dispatcher` & `ops`（读取配置与恢复会话快照 `.agents/session.json`）。
> **关联总纲**：[`SKILL.md §6`](../SKILL.md) | **标准配置模板**：[`templates/environment.example.json`](../templates/environment.example.json)、[`templates/session.example.json`](../templates/session.example.json) | **管理脚本**：[`scripts/session-snapshot.py`](../scripts/session-snapshot.py)

---

## 1. 四档角色算力画像与 Harness 选配参考

首次在项目中启用本技能（或重配团队模型与工具链）时，由一次性临时引导实例（`Bootstrap Agent`）读取并执行 **[`playbooks/bootstrap-teamwork.md`](../playbooks/bootstrap-teamwork.md)**：自动探测宿主机已安装的 CLI (`claude`, `codex`, `agy`, `pi`, `hermes`) 与静态工具链，按以下**四档算力画像**与人类灵活敲定模型分配（不死板绑定易过时的固定模型名）：

| 角色集群与 ID | 核心算力诉求 | 优选 Harness 倾向参考 | 理想思考深度 (Thinking) |
| :--- | :--- | :--- | :--- |
| **`planner` / `reflector` / `explorer` / `debugger` / `security-redteam` / `reviewer-lead` / `reviewer-arch` / `reviewer-perf` / `reviewer-security`** | 高维架构抽象、元认知复盘、法医式逆向溯源、攻防博弈与证伪裁决 | 当前可用池中逻辑推理最强的 Harness 与模型 (`claude-code` / `codex` / `agy`) | **High** (深度推理) |
| **`coding` / `tdd` / `reviewer-ux`** | 严格契约遵从、边界用例推演、精准行级实现与交互审计 | 代码生成精准且速度均衡的主力模型 (`codex` / `claude-code` / `agy`) | **Medium** (适度推断) |
| **`e2e`** | 极速 DOM/A11y 树理解、页面语义自愈与冒烟走查 | 挂载了 `chrome-devtools-mcp` 且响应迅速的模型 (`agy` / `claude-code` / `pi`) | **Low ~ Medium** (极速自愈) |
| **`dispatcher` / `ops` / `reviewer-quality`** | 毫秒级状态机流转、确定性建场发布、海量原始日志吞吐过滤 | 延迟最低、Token 最经济的轻量 Harness 与模型 (`pi` / `hermes` / `agy`) | **None / Low** (零延迟确定性) |

---

## 2. `.agents/environment.json` 字段字典说明

完整 JSON 模板见 **[`templates/environment.example.json`](../templates/environment.example.json)**。各字段含义与运行机制如下：

| 字段路径 | 类型 / 枚举值 | 含义与运行机制说明 |
| :--- | :--- | :--- |
| **`mode`** | `"standard"` \| `"worktree"` | 默认开发模式：`standard`（单工作区原地串行）或 `worktree`（`.worktrees/<id>` 独立工作区高并发）。 |
| **`default_ctx`** | `"compact"` \| `"clear"` \| `"keep"` | `standard` 模式下每完成一个 Feature 后，对 `tdd/coding/reviewer-lead` 的默认上下文打理策略。 |
| **`runtime_type`** | `"daemon_port"` \| `"push_to_host"` \| `"artifact_only"` | 验收运行态：常驻端口服务（配 `base_port`）、寄生态热推插件（配 `toolchain.push_cmd` + `target_url`）或纯编译产物。 |
| **`active_roles`** | `string[]` | 本项目实际启用的角色白名单（如纯 CLI 项目剔除 `e2e`/`reviewer-ux`，防误点名）。 |
| **`toolchain`** | `object` | 初始化阶段一次性验证固化的构建（`build`）、单测（`test`）、类型检查（`typecheck`）、静态健康（`static_health`）与热推（`push_cmd`）命令，日常运行零探测直接调用。 |
| **`version_anchors`** | `string[]` | 受控发版时 `ops` 需同步递增 SemVer 版本号的文件清单（如 `package.json`, `manifest.json`, 代码常量文件）。 |
| **`domain_skills`** | `object` | `Bootstrap` 扫描或联网检索推荐安装的垂类领域与工具 Skill（如 `shadcn-ui`、`fallow-skills`、`chrome-extensions`），通过 `roles` 数组按需精准挂载给相关角色，避免无关角色消耗上下文。 |
| **`context_monitor`** | `object` | 上下文水位监控配置：包含巡检松紧策略 **`probe_policy`**（`"strict"` 每次派活前必检 \| `"relaxed"` 结项全检+仅返工/临界时抽检）、是否安装了 `herdr-agent-usage` 与 `pi-proactive-compact` 插件，以及按「70%/60%/50% 黄金比例法则」（`tier: "S"\|"A"\|"B"` × `window_tokens`）计算的 `default_profile` 与 `role_overrides` 阈值，供 `scripts/agent-context.py` 与 `Dispatcher` 直接读取（详见 [`protocols/context-and-budget.md`](./context-and-budget.md)）。 |
| **`harness_profiles`** | `object` | `Bootstrap` 通过 `<harness> --help` 核实的各 CLI 压缩指令（`compact_cmd`，内置 EESV 四要素保真锚点）、清空指令（`clear_cmd`）与会话恢复参数（`resume_flag`）；中断与关闭窗格统一按 [`tools/herdr.md §[H-6]`](../tools/herdr.md) 执行。 |
| **`roles.<id>`** | `object` | 各角色绑定的 `harness`、逻辑 `model`、逻辑思考强度 `thinking` (`"none"`\|`"low"`\|`"medium"`\|`"high"`)，以及供 `herdr agent start` 直接展开透传的原生启动参数数组 **`cli_args`**。 |

---

## 3. `.agents/session.json` 会话快照字段字典说明

完整 JSON 模板见 **[`templates/session.example.json`](../templates/session.example.json)**。
`.agents/session.json` 记录主工作区及所有并发子 Worktree 中活跃已命名窗格的运行时拓扑、**从 `.jsonl` 实时提取的当前生效模型与思考深度**及会话恢复参数（由 [`scripts/agent-context.py`](../scripts/agent-context.py) 日常巡检时自动同步，也可通过 [`scripts/session-snapshot.py`](../scripts/session-snapshot.py) 的 `save / restore / prune` 显式管理，操作命令详见 **[`tools/herdr.md §[H-2]`](../tools/herdr.md)**）：

| 字段路径 | 含义与运行机制说明 |
| :--- | :--- |
| **`agents.<name>.base_role`** | 将多 Worktree 下带后缀的实例名（如 `coding-001`、`reviewer-lead-001`）通过前缀匹配还原出的标准角色 ID（`coding`、`reviewer-lead`），用于关联 `.agents/environment.json` 配置与 `roles/<base_role>.md` 角色书。 |
| **`agents.<name>.workspace_id` / `cwd`** | 该角色所属的 Herdr 工作区 ID（如 `w1` 主工作区、`w2` 子工作区）与工作目录绝对路径，支持多 Worktree 并发快照共存。 |
| **`agents.<name>.pane_id` / `tab_id`** | 角色当前驻留的稳定窗格与标签页句柄。 |
| **`agents.<name>.model` / `thinking`** | 从本地 `.jsonl` 会话尾部及状态栏**实时提取**的最后一次真实生效模型与思考深度（若运行途中通过 `/model` 等切换过模型或思考层级，自动捕获最新值）。 |
| **`agents.<name>.conversation_id` / `resume_args`** | 底层纯净会话 ID 及预拼装好的完整恢复参数数组（如 `pi` 使用 `--session <id>`，`agy` 使用 `--conversation <id>`，`claude` 使用 `--resume <id>`）；执行 `scripts/session-snapshot.py restore` 时直接透传给 `herdr agent start`（若角色已存活但模型/思考深度漂移，优先执行非交互式原地 `/model` 切换，不支持时自动重启对齐），解决 Herdr 原生恢复丢失模型与思考深度的问题。 |
