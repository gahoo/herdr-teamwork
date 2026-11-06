# Herdr 编排与窗格控制标准指令集 (`tools/herdr.md`)

> **定位**：本文件为 `dispatcher`、`ops`、`planner`、`reflector` 及 `bootstrap-teamwork`、`roundtable-debate` 剧本的必读配套指令卡；各角色按职责遵照对应段落（`§[H-1]` ~ `§[H-6]`）执行。

---

## §[H-1] 切分窗格与创建标签页 (Pane Split & Tab Create)

所有创建类命令均返回 JSON，必须通过 `jq -r` 提取真实的稳定句柄（`pane_id` / `tab_id` / `workspace_id`）保存至变量中供后续步骤使用，并统一加上 `--no-focus` 保持人类当前焦点不被抢占：

```bash
# 1. 基于当前调用方窗格向右切分新窗格，并提取新窗格 ID：
NEW_PANE=$(herdr pane split --current --direction right --cwd "$PWD" --no-focus | jq -r '.result.pane.pane_id')

# 2. 基于指定窗格 ID 向下（或向右）切分新窗格，并提取新窗格 ID：
SUB_PANE=$(herdr pane split --pane "$TARGET_PANE" --direction down --cwd "$PWD" --no-focus | jq -r '.result.pane.pane_id')

# 3. 在当前工作区新建独立 Tab（如 ops 或 review 专属标签页），并提取其根窗格 ID：
TAB_ROOT_PANE=$(herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$PWD" --no-focus | jq -r '.result.root_pane.pane_id')

# 4. 查看当前工作区的全部窗格与活跃 Agent 分布：
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
herdr agent list
```

---

## §[H-2] 启动角色、导出快照与跨天会话恢复 (Agent Start, Session Snapshot & Resume)

`herdr agent start` 要求目标窗格处于空闲 Shell 状态；角色专属的模型与思考强度参数数组统一从 `.agents/environment.json` 的 `.roles["<role>"].cli_args` 展开并放在 `--` 之后透传：

```bash
# 1. 按 .agents/environment.json 启动单个角色实例（若尚未运行）：
ROLE="reviewer-quality"
if ! herdr agent get "$ROLE" >/dev/null 2>&1; then
  TARGET_PANE=$(herdr pane split --current --direction right --cwd "$PWD" --no-focus | jq -r '.result.pane.pane_id')
  HARNESS=$(jq -r --arg r "$ROLE" '.roles[$r].harness' .agents/environment.json)
  CLI_ARGS=($(jq -r --arg r "$ROLE" '.roles[$r].cli_args[]' .agents/environment.json))
  herdr agent start "$ROLE" --kind "$HARNESS" --pane "$TARGET_PANE" -- "${CLI_ARGS[@]}"
fi

# 2. 导出当前活跃 Agent 会话快照至 .agents/session.json（自动关联 model / thinking 并过滤未命名窗格与临时 bootstrap）：
herdr agent list | jq --slurpfile env .agents/environment.json \
  --arg ws "${HERDR_WORKSPACE_ID:-main}" --arg proj "$(basename "$PWD")" \
  '{
    updated_at: (now | todate),
    workspace_id: $ws,
    project: $proj,
    agents: [
      .result.agents[]
      | select(.name != null and .name != "bootstrap")
      | . as $a
      | ($env[0].roles[$a.name] // {}) as $r
      | {
          key: $a.name,
          value: {
            name: $a.name,
            pane_id: $a.pane_id,
            tab_id: $a.tab_id,
            harness: ($r.harness // $a.kind),
            model: ($r.model // "default"),
            thinking: ($r.thinking // "default"),
            conversation_id: $a.agent_session.value
          }
        }
    ] | from_entries
  }' > .agents/session.json

# 3. 跨天复工原地恢复某常驻角色的历史会话记忆：
ROLE="planner"
HARNESS=$(jq -r --arg r "$ROLE" '.agents[$r].harness' .agents/session.json)
CONV_ID=$(jq -r --arg r "$ROLE" '.agents[$r].conversation_id' .agents/session.json)
RESUME_FLAG=$(jq -r --arg h "$HARNESS" '.harness_profiles[$h].resume_flag' .agents/environment.json)
CLI_ARGS=($(jq -r --arg r "$ROLE" '.roles[$r].cli_args[]' .agents/environment.json))
herdr agent start "$ROLE" --kind "$HARNESS" --pane "$TARGET_PANE" -- "${CLI_ARGS[@]}" "$RESUME_FLAG" "$CONV_ID"
```

---

## §[H-3] 事件驱动派发、等待与输出读取 (Event-Driven Prompt, Wait & Read —— 零轮询)

- **纯事件驱动准则**：`herdr agent prompt <target> "<text>" --wait` 与 `herdr agent wait <target>` 底层自带 **5 秒启动活性门禁（5000ms Liveness Gate）**，并在任务进行期间监听底层状态机事件，默认自动匹配 **`idle`、`done`、`blocked` 三种终态**后毫秒级唤醒返回。
- **直接使用默认终态与持续事件监听**：`herdr agent prompt <target> "<text>" --wait` 与 `herdr agent wait <target>` 只需传入目标角色名（及 `--wait`），自动覆盖全部三种终态并持续等待直至事件触发。若宿主 CLI 的 Bash 工具自身支持设置工具调用超时上限，将其设为允许的最大值；万一超长任务触发宿主 Shell 工具层中断，先执行 `herdr agent get <target>` 检查状态，只要 `.result.agent.status == "working"`，直接执行 `herdr agent wait <target>` 继续挂回事件流等待即可。

```bash
# 1. 【单角色串联阻塞调度】（提交 Prompt 并原地等待目标进入 idle / done / blocked 任一终态）：
herdr agent prompt tdd "请阅读 changes/001-auth/spec.md 与 changes/001-auth/tasks.md，编写失败测试 (Red Test) 并勾选对应任务项" --wait

# 2. 【多专家并发派发与统一回收】（先并发提交不带 --wait 的 Prompt，再逐一执行无参数 agent wait 回收事件）：
herdr agent prompt reviewer-quality "请执行静态健康度扫描与类型检查，输出 <=15 行简报"
herdr agent prompt reviewer-arch "请结合 changes/001-auth/spec.md 审查架构边界与爆炸半径，焦点：$FOCUS"
herdr agent wait reviewer-quality
herdr agent wait reviewer-arch

# 3. 【读取角色终端输出】（统一使用 --source recent-unwrapped 消除终端软换行导致的路径截断）：
herdr agent read reviewer-lead --source recent-unwrapped --lines 40
```

---

## §[H-4] Worktree 平行工作区建场与回收 (Worktree Workspace Lifecycle)

在 `worktree` 并行模式下，每个并发变更集 `<id>` 绑定独立的物理目录 `.worktrees/<id>` 与独立的 Herdr 工作区 `ws-<id>`。跨工作区的 Agent 依靠**全局唯一角色名**（如 `dispatcher-001`、`coding-001`）直接寻址：

```bash
# 1. 主工作区 Ops 调用内置脚本完成 .worktrees/<id> 物理建场与 changes/.agents/依赖 软链挂载：
.agents/skills/herdr-teamwork/scripts/worktree-up.sh "001-auth" "feat/001-auth"

# 2. 创建绑定该 Worktree 目录的独立 Herdr Workspace，并提取其根窗格 ID：
WS_JSON=$(herdr workspace create --label "ws-001" --cwd "$PWD/.worktrees/001-auth" --no-focus)
WS_ID=$(echo "$WS_JSON" | jq -r '.result.workspace.workspace_id')
WS_ROOT_PANE=$(echo "$WS_JSON" | jq -r '.result.root_pane.pane_id')

# 3. 在新工作区根窗格启动带变更集后缀的全局唯一 Worker Dispatcher 并异步点火（不加 --wait）：
DISP_HARNESS=$(jq -r '.roles.dispatcher.harness' .agents/environment.json)
DISP_ARGS=($(jq -r '.roles.dispatcher.cli_args[]' .agents/environment.json))
herdr agent start "dispatcher-001" --kind "$DISP_HARNESS" --pane "$WS_ROOT_PANE" -- "${DISP_ARGS[@]}"
herdr agent prompt "dispatcher-001" "请接管 changes/001-auth，按 pipeline.jsonl 在当前工作区启动流水线"

# 4. 特性结项合入后，安全销毁 Worktree 目录并关闭对应 Herdr Workspace：
.agents/skills/herdr-teamwork/scripts/worktree-down.sh "001-auth" --delete-branch
herdr workspace close "$WS_ID"
```

---

## §[H-5] 后台服务守护子窗格 (`.ops-pane` Daemon Pane)

`Ops` 运行常驻开发服务器（`npm run dev` / `cargo run` / `uvicorn` 等）时，在 `ops` Tab 内切分专属守护子窗格并将窗格 ID 持久化至 `.ops-pane`，通过 `herdr pane` 表面直接投递命令并监听端口就绪：

```bash
# 1. 创建或复用 .ops-pane 守护子窗格：
if [ ! -f .ops-pane ] || ! herdr pane layout --pane "$(cat .ops-pane)" >/dev/null 2>&1; then
  DAEMON_PANE=$(herdr pane split --current --direction right --cwd "$PWD" --no-focus | jq -r '.result.pane.pane_id')
  echo "$DAEMON_PANE" > .ops-pane
fi
DAEMON_PANE=$(cat .ops-pane)

# 2. 若子窗格已有旧进程运行，先发送 ctrl+c 中断，随后投递新启动命令：
herdr pane send-keys "$DAEMON_PANE" ctrl+c
herdr pane run "$DAEMON_PANE" "PORT=${PORT} npm run dev"

# 3. 事件驱动等待服务输出就绪特征词，并读取最近日志确认无启动报错：
herdr pane wait-output "$DAEMON_PANE" --match "localhost:${PORT}"
herdr pane read "$DAEMON_PANE" --source recent-unwrapped --lines 30
```

---

## §[H-6] 上下文水位探针、主动压缩/重置、中断重试与窗格回收 (Context Watermark, Compaction, Interrupt & Release)

```bash
# 1. 【跨 Harness 实时上下文水位探针】（双通道读取 herdr-agent-usage 或 256KB 有界尾部扫描 .jsonl，输出 OK / ARMED / DANGER / +JUST_COMPACTED）：
bash .agents/skills/herdr-teamwork/scripts/agent-context.sh
# 也可指定单个角色巡检（在派活前闸门 Pre-Dispatch Gate 调用）：
bash .agents/skills/herdr-teamwork/scripts/agent-context.sh coding

# 2. 【主动上下文压缩 (Proactive Compaction —— EESV 四要素保真)】（当角色处于 ARMED/DANGER 且处于 idle/done 稳态边界时执行）：
HARNESS=$(jq -r --arg r "$TARGET_ROLE" '.roles[$r].harness' .agents/environment.json)
COMPACT_CMD=$(jq -r --arg h "$HARNESS" '.harness_profiles[$h].compact_cmd' .agents/environment.json)
herdr agent prompt "$TARGET_ROLE" "$COMPACT_CMD" --wait
# 压缩完成后，在下一条任务指令开头附带角色书重载提醒：
# "请先调用读取工具确认 .agents/skills/herdr-teamwork/roles/${TARGET_ROLE}.md 职责边界，随后执行：..."

# 3. 【跨无关业务大域清空并重塑角色记忆 (Clear & Re-Prime)】（仅在 PLAN.ctx == "clear" 且 Reflector 复盘完毕，或角色死循环污染时执行）：
HARNESS=$(jq -r --arg r "$TARGET_ROLE" '.roles[$r].harness' .agents/environment.json)
CLEAR_CMD=$(jq -r --arg h "$HARNESS" '.harness_profiles[$h].clear_cmd' .agents/environment.json)
herdr agent prompt "$TARGET_ROLE" "$CLEAR_CMD" --wait
herdr agent prompt "$TARGET_ROLE" "请读取 .agents/skills/herdr-teamwork/roles/${TARGET_ROLE}.md 与 tools/herdr.md（若适用）恢复角色契约待命" --wait

# 4. 【下游异常自愈 Step 1：观察并发送 ctrl+c 中断当前卡死回合】：
herdr agent get "$TARGET_ROLE"
herdr agent read "$TARGET_ROLE" --source recent-unwrapped --lines 20
herdr agent send-keys "$TARGET_ROLE" ctrl+c

# 5. 【下游异常自愈 Step 2：销毁异常窗格并在新窗格重启进程】：
OLD_PANE=$(herdr agent get "$TARGET_ROLE" | jq -r '.result.agent.pane_id')
NEW_PANE=$(herdr pane split --pane "$OLD_PANE" --direction right --cwd "$PWD" --no-focus | jq -r '.result.pane.pane_id')
herdr pane close "$OLD_PANE"
# 随后按 §[H-2] 在 $NEW_PANE 上重新执行 herdr agent start "$TARGET_ROLE" ...

# 6. 【关闭指定窗格或自关闭当前临时窗格（如 bootstrap / planner-roundtable 退出）】：
herdr pane close "$TARGET_PANE"
# 若在临时窗格内部自关闭当前窗格，直接传入环境变量 $HERDR_PANE_ID：
herdr pane close "$HERDR_PANE_ID"
```
