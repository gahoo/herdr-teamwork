# Playbook: Teamwork 协同环境自举与建场 (`bootstrap-teamwork` — Project Onboarding & Bootstrap)

> **定位**：本剧本专供新项目或存量项目首次启用 `herdr-teamwork`（或重新调整团队模型与工具链配置）时执行。
> 由人类在初始 Herdr 终端窗格中唤醒一个**一次性临时引导实例（`Bootstrap Agent`）**读取本剧本：负责探测宿主机器可用 Harness/模型与工具集、与人类一轮对齐项目配置、生成 `.agents/environment.json` 与活文档骨架、拉起真正的 `Planner`（窗口 1）+ `Dispatcher`（窗口 2）+ `Ops` 常驻窗格并保存 `.agents/session.json`，最后**关闭自身临时窗格功成身退**，确保 `Planner` 从第 0 回合起即保持 100% 纯净上下文与严格沙箱。

---

## 1. 触发时机与执行主体

- **触发时机 (When)**：
  1. 项目尚未创建 `.agents/environment.json` 或 `changes/KANBAN.md`；
  2. 人类主动下达“初始化 teamwork 环境 / 重新配置角色模型或工具链”指令。
- **执行主体 (Who)**：当前窗格中的**临时 `Bootstrap Agent`**（不占用 16 个常驻角色编制，建场完成后自动退出关闭）。

---

## 2. 五步自举建场规程 (5-Step Bootstrap Loop)

### Step 1：宿主机能力与项目形态全自动探针 (`Zero-Guess Probing`)
在向人类提问前，先一次性运行非侵入式探测命令摸清家底（严禁盲目猜测或还没探查就向人类抛出一堆空泛问题）：

```bash
# 1. 验证处于 Herdr 托管窗格内，并查看支持的 Agent Kind 列表：
test "${HERDR_ENV:-}" = 1 && herdr agent

# 2. 探测宿主机已安装的 Agent CLI 与核心基建工具：
for cmd in claude codex agy pi hermes jq rg gitnexus fallow tsc cargo golangci-lint ruff mypy pytest; do
  command -v "$cmd" >/dev/null 2>&1 && echo "[INSTALLED] $cmd" || echo "[MISSING] $cmd"
done

# 3. 对本机已安装的 Agent CLI 执行一次 --help 探测，核实其传模型、思考强度与会话恢复的真实参数语法：
for h in claude codex agy pi hermes; do
  command -v "$h" >/dev/null 2>&1 && "$h" --help | head -n 40 || true
done

# 4. 扫描项目根目录技术栈特征、既有规范与版本锚点：
ls -la Cargo.toml go.mod pyproject.toml package.json manifest.json tsconfig.json AGENTS.md CLAUDE.md .fallow-baseline.json 2>/dev/null || true
```

#### 主流 Harness 参数与控制命令速查基线（以本机 `--help` 实测输出为准固化至 `environment.json`）

| Harness (`kind`) | 模型与思考强度 CLI 参数参考 (`cli_args`) | 会话恢复参数 (`resume_flag`) | 压缩上下文指令 (`compact_cmd`) | 清空与停止/退出准则 |
| :--- | :--- | :--- | :--- | :--- |
| **`claude`** | `["--model", "<m>", "--effort", "<high\|medium\|low>"]` | `"--resume"` | `"/compact 保留项目架构拓扑与核心演进决策"` | 清空：`/clear`<br>**停止/退出：统一调 `herdr agent stop` 或 `herdr pane close`，严禁盲猜 `/exit` 或 `/quit`** |
| **`codex`** | `["--model", "<m>", "-c", "model_reasoning_effort=\"<high\|medium\|low>\""]` | `"resume"` | `"/compact"` | 清空：`/new`（或 `stop && start`） |
| **`pi`** | `["--model", "<m>", "--thinking", "<high\|medium\|low\|off>"]` | `"--resume"` | `"/compact 保留项目架构拓扑与核心演进决策"` | 清空：`/new` |
| **`agy`** / **`hermes`** | 按 `<cmd> --help` 实测填入 `cli_args` | 按 `--help` 实测填入 | `"/compact"` | 清空：`/clear`（或 `herdr agent stop && start` 进程级归零） |

### Step 2：四档算力选型建议与人类一轮式拍板 (`1-Round Human Alignment`)
根据 Step 1 的探测结果，按以下原则草拟一份《项目协同配置方案表》，向人类发起**单轮确认**：

1. **按「四档算力画像」灵活选配 Harness 与模型（拒绝死板写死模型名）**：
   询问人类当前各 CLI 可用的主力模型与额度偏好，按角色能力诉求给出推荐搭配供人类微调：
   - **档位 A（高维推理与逆向溯源）** ➔ `planner`, `reflector`, `explorer`, `debugger`, `security-redteam`, `reviewer-lead/arch/perf/security`：**选配当前逻辑推理与架构抽象最强的模型 + `high` 思考深度**；
   - **档位 B（严谨契约遵从与代码生成）** ➔ `coding`, `tdd`, `reviewer-ux`：**选配代码生成精准、速度均衡的主力编码模型 + `medium` 思考深度**；
   - **档位 C（浏览器多模态与 DOM 交互）** ➔ `e2e`：**选配已挂载 `chrome-devtools-mcp` 且响应迅速的模型 + `low~medium` 思考深度**；
   - **档位 D（低延迟状态机与海量日志吞吐）** ➔ `dispatcher`, `ops`, `reviewer-quality`：**选配响应最快、Token 成本最低的轻量模型 + `none/low` 思考深度**。
2. **裁剪项目专属「活跃角色编制 (`active_roles`)」**：
   - 根据项目类型建议启用的角色子集（例如：纯 CLI / SDK 库 / 后端无界面项目默认剔除 `e2e` 与 `reviewer-ux`；个人轻量工具可按需剔除 `security-redteam`）。
3. **锁定「三类交付运行态 (`runtime_type`)」与版本锚点 (`version_anchors`)**：
   - **`daemon_port`（常驻服务/Web 类）**：确认 `base_port`（默认 `3000`）与启动命令（如 `npm run dev`）；
   - **`push_to_host`（寄生态插件类：浏览器扩展、油猴脚本、Obsidian/IDE 插件）**：`base_port: null`，确认构建命令、热推送命令（`push_cmd`）及验收目标站点 `target_url`；
   - **`artifact_only`（CLI 工具 / SDK 库 / 编译器）**：`base_port: null`，确认构建与测试命令；
   - 确认发版时需同步递增版本号的文件清单（`version_anchors`，如 `["package.json", "manifest.json", "src/config.ts"]`）。
4. **确认并发模式与跨特性上下文策略**：
   - 默认模式：`standard`（单工作区原地串行） vs `worktree`（多分支独立工作区高并发）；
   - 默认上下文打理策略（`default_ctx`，针对 `standard` 模式结项后）：`"compact"`（默认推荐：压缩保留项目架构记忆）、`"clear"`（跨无关域清空归零）或 `"keep"`（连续微切片保留）。
5. **推荐安装缺失的高价值工具（按需）**：
   - 若探测发现缺失 `gitnexus`、`jq`、`rg` 或当前语言核心静态分析器（如 TS/JS 缺 `fallow`、Rust 缺 `clippy`、Go 缺 `golangci-lint`、Python 缺 `ruff`），列出 1 行安装命令询问人类是否现在安装；将最终确认可用的验证命令固化进 `toolchain`，**后续日常运行直接读取配置执行，不再每次重复探测浪费 Token**。

### Step 3：配置落盘、图谱建库与活文档骨架初始化 (`Scaffolding`)
人类确认后，依次执行以下幂等建场动作：

1. **写入 `.agents/environment.json`**：
   严格按照 [`SKILL.md` §6](../SKILL.md) 的标准结构，将对齐后的完整配置（含 `mode`、`default_ctx`、`runtime_type`、`base_port`/`target_url`、`active_roles`、`toolchain`、`version_anchors`、`harness_profiles` 以及包含 `thinking` 与实测 `cli_args` 数组的 `roles` 映射）写入 `.agents/environment.json`。
2. **加固 `.gitignore`**：
   检查项目 `.gitignore`，确保包含 `.worktrees/`、`.ops-pane`、`.ops.pid`（防止 Worktree 目录与后台守护子窗格句柄污染版本库）。
3. **初始化代码图谱与存量静态基线**：
   - 执行 `npx gitnexus analyze` 建立 AST 代码知识图谱；
   - 若为存量项目且启用了支持基线豁免的静态分析器（如 `fallow`），运行 `fallow --save-regression-baseline .fallow-baseline.json` 建立存量基线（确保后续审查“存量不误伤，增量零退化”）。
4. **创建核心活文档标准工件（若尚不存在）**：
   - **`changes/KANBAN.md`**：创建包含 `## 📥 需求收件与待开展占位池 (Inbox / Backlog)`、`## 🚀 进行中 (In Progress)`、`## ✅ 已完成 (Done)` 的全局看板；
   - **`GLOSSARY.md`**：创建项目级统一领域语言词典（若为存量项目，扫描核心模块提取初始的 5~10 个业务领域概念填入；严禁混入类名/表名等实现细节）；
   - **`E2E_PLAYBOOK.md`**：仅当 `active_roles` 包含 `e2e` 时创建 6 要素结构化导航记忆表头。

### Step 4：拉起常驻控制台拓扑并保存 `session.json` (`Spawn Console Topology`)
严格读取 `.agents/environment.json` 中为各角色敲定的 `harness` 与 `cli_args`（同时携带模型与思考强度参数），使用 `herdr` 拉起常驻控制台窗格：

```bash
# 1. 在当前 Tab 切分出窗口 1 (Planner) 与窗口 2 (Dispatcher)：
PLANNER_PANE=$(herdr pane split --current --direction right --cwd "$PWD" --no-focus | jq -r '.result.pane.pane_id')
DISP_PANE=$(herdr pane split --pane "$PLANNER_PANE" --direction right --cwd "$PWD" --no-focus | jq -r '.result.pane.pane_id')

# 2. 创建独立 ops Tab 并获取其根窗格：
OPS_PANE=$(herdr tab create --workspace "${HERDR_WORKSPACE_ID}" --cwd "$PWD" | jq -r '.result.root_pane.pane_id')

# 3. 按 environment.json 配置的 Harness 与 cli_args（含模型与思考强度）分别启动三大核心常驻角色：
PLANNER_ARGS=($(jq -r '.roles.planner.cli_args[]' .agents/environment.json))
DISP_ARGS=($(jq -r '.roles.dispatcher.cli_args[]' .agents/environment.json))
OPS_ARGS=($(jq -r '.roles.ops.cli_args[]' .agents/environment.json))

herdr agent start planner --kind "$(jq -r '.roles.planner.harness' .agents/environment.json)" --pane "$PLANNER_PANE" -- "${PLANNER_ARGS[@]}"
herdr agent start dispatcher --kind "$(jq -r '.roles.dispatcher.harness' .agents/environment.json)" --pane "$DISP_PANE" -- "${DISP_ARGS[@]}"
herdr agent start ops --kind "$(jq -r '.roles.ops.harness' .agents/environment.json)" --pane "$OPS_PANE" -- "${OPS_ARGS[@]}"

# 4. 向 Planner 与 Dispatcher 发送各自身份就位提示（加载各自角色契约）：
herdr agent prompt planner "请阅读 .agents/skills/herdr-teamwork/SKILL.md 与 roles/planner.md，作为窗口 1 总规划台就位，读取 changes/KANBAN.md 与 GLOSSARY.md 等候人类需求。"
herdr agent prompt dispatcher "请阅读 .agents/skills/herdr-teamwork/SKILL.md 与 roles/dispatcher.md，作为窗口 2 交付总控台就位。"

# 5. 保存会话快照 .agents/session.json（关联读取 environment.json 中的 model 与 thinking，显式过滤临时 bootstrap 自身）：
herdr agent list | jq --slurpfile env .agents/environment.json \
  --arg ws "${HERDR_WORKSPACE_ID:-main}" --arg proj "$(basename "$PWD")" \
  '{updated_at: (now | todate), workspace_id: $ws, project: $proj, agents: [.result.agents[] | select(.name != null and .name != "bootstrap") | . as $a | ($env[0].roles[$a.name] // {}) as $r | {key: $a.name, value: {name: $a.name, pane_id: $a.pane_id, tab_id: $a.tab_id, harness: ($r.harness // $a.kind), model: ($r.model // "default"), thinking: ($r.thinking // "default"), conversation_id: $a.agent_session.value}}] | from_entries}' > .agents/session.json
```

### Step 5：功成身退 (`Self-Teardown`)
1. 向人类输出简短的《建场完成汇报》（说明 `planner` 与 `dispatcher` 窗格已就绪、`.agents/environment.json` 与 `.agents/session.json` 已落盘）；
2. **使用 Herdr 原语销毁临时引导窗格（严禁盲猜 `/exit` 或 `/quit`）**：直接执行 `herdr pane close --current`，把终端屏幕彻底交还给纯净的左窗格 `Planner`（窗口 1）与右窗格 `Dispatcher`（窗口 2）！
