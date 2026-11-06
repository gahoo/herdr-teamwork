# Playbook: Teamwork 协同环境自举与建场 (`bootstrap-teamwork` — Project Onboarding & Bootstrap)

> **定位**：本剧本专供新项目或存量项目首次启用 `herdr-teamwork`（或重新调整团队模型与工具链配置）时执行。
> 由人类在初始 Herdr 终端窗格中唤醒一个**一次性临时引导实例（`Bootstrap Agent`）**读取本剧本：负责探测宿主机器可用 Harness/模型与工具集、与人类一轮对齐项目配置、生成 `.agents/environment.json` 与活文档骨架、拉起真正的 `Planner`（窗口 1）+ `Dispatcher`（窗口 2）+ `Ops` 常驻窗格并保存 `.agents/session.json`，最后**关闭自身临时窗格功成身退**，确保 `Planner` 从第 0 回合起即保持 100% 纯净上下文与严格沙箱。
> **配套必读文档**：**[`tools/herdr.md`](../tools/herdr.md)** —— 窗格切分、角色启动、`session.json` 快照导出与自身窗格关闭统一遵照其中 `§[H-1]`、`§[H-2]`、`§[H-3]` 与 `§[H-6]` 段落执行。

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

# 2. 探测宿主机已安装的 Agent CLI、上下文水位监控插件 (herdr-agent-usage) 与核心基建工具：
for cmd in claude codex agy pi hermes herdr-agent-usage jq rg gitnexus fallow tsc cargo golangci-lint ruff mypy pytest; do
  command -v "$cmd" >/dev/null 2>&1 && echo "[INSTALLED] $cmd" || echo "[MISSING] $cmd"
done
# 检查 herdr-agent-usage 缓存目录与 Pi 压缩扩展挂载情况（避免双插件冲突或采蜜抢跑）：
ls -d ~/.cache/herdr-agent-usage ~/.pi/agent/extensions/* 2>/dev/null || true
grep -E "proactive-compact|smart-compact" ~/.pi/agent/settings.json 2>/dev/null || true

# 3. 对本机已安装的 Agent CLI 执行一次 --help 探测，核实其传模型、思考强度与会话恢复的真实参数语法：
for h in claude codex agy pi hermes; do
  command -v "$h" >/dev/null 2>&1 && "$h" --help | head -n 40 || true
done

# 4. 扫描项目根目录技术栈特征、既有规范与版本锚点：
ls -la Cargo.toml go.mod pyproject.toml package.json manifest.json tsconfig.json AGENTS.md CLAUDE.md .fallow-baseline.json 2>/dev/null || true

# 5. 盘点本机已安装的项目级与全局垂类 Skills，并按项目技术栈检索外部生态最新匹配的 Skill：
ls -d .agents/skills/* ~/.agents/skills/* ~/.claude/skills/* ~/.gemini/skills/* 2>/dev/null || true
# (若识别出特定框架如 shadcn/nextjs/chrome-extension/rust/fastapi，执行 npx skills find <keyword> 或联网搜索 skills.sh / GitHub 高评价垂类 Skill)
```

#### 主流 Harness 参数与控制命令速查基线（以本机 `--help` 实测输出为准固化至 `environment.json`）

| Harness (`kind`) | 模型与思考强度 CLI 参数参考 (`cli_args`) | 会话恢复参数 (`resume_flag`) | 压缩上下文指令 (`compact_cmd`) | 清空与停止/退出准则 |
| :--- | :--- | :--- | :--- | :--- |
| **`claude`** | `["--model", "<m>", "--effort", "<high\|medium\|low>"]` | `"--resume"` | `"/compact 请保留：1.[Ground Truth]已验证的文件路径/命令与报错签名；2.[Continuity Ledger]当前生效的架构约束与职责边界；3.[Open Loops]未决待办项；4.[Delta]本轮改动。严禁伪造未读路径。"` | 清空：`/clear`<br>**停止/退出：统一按 [`tools/herdr.md §[H-6]`](../tools/herdr.md) 关闭或重建窗格，严禁盲猜 `/exit` 或 `/quit`** |
| **`codex`** | `["--model", "<m>", "-c", "model_reasoning_effort=\"<high\|medium\|low>\""]` | `"resume"` | `"/compact"` | 清空：`/new` |
| **`pi`** | `["--model", "<m>", "--thinking", "<high\|medium\|low\|off>"]` | `"--resume"` | `"/compact 请保留：1.[Ground Truth]已验证的文件路径/命令与报错签名；2.[Continuity Ledger]当前生效的架构约束与职责边界；3.[Open Loops]未决待办项；4.[Delta]本轮改动。严禁伪造未读路径。"` | 清空：`/new` |
| **`agy`** / **`hermes`** | 按 `<cmd> --help` 实测填入 `cli_args` | 按 `--help` 实测填入 | `"/compact"` | 清空：`/clear`（或按 [`tools/herdr.md §[H-6]`](../tools/herdr.md) 重建窗格归零） |

### Step 2：四档算力选型建议与人类一轮式拍板 (`1-Round Human Alignment`)
根据 Step 1 的探测结果，按以下原则草拟一份《项目协同配置方案表》，向人类发起**单轮确认**：

1. **按「四档算力画像」灵活选配 Harness 与模型，并标定「长文智力抗衰档位 (`tier: S/A/B`) × 物理窗口 (`window_tokens`)」**：
   询问人类当前各 CLI 可用的主力模型、物理上下文窗口大小及额度偏好，按角色能力诉求给出推荐搭配，并依据**宏观分档指导原则（不绑定易过时的具体模型名）**计算上下文压缩阈值（写入 `context_monitor`）：
   - **档位 A（高维推理与逆向溯源）** ➔ `planner`, `reflector`, `explorer`, `debugger`, `security-redteam`, `reviewer-lead/arch/perf/security`：**选配当前逻辑推理与架构抽象最强的模型 + `high` 思考深度**；
   - **档位 B（严谨契约遵从与代码生成）** ➔ `coding`, `tdd`, `reviewer-ux`：**选配代码生成精准、速度均衡的主力编码模型 + `medium` 思考深度**；
   - **档位 C（浏览器多模态与 DOM 交互）** ➔ `e2e`：**选配已挂载 `chrome-devtools-mcp` 且响应迅速的模型 + `low~medium` 思考深度**；
   - **档位 D（低延迟状态机与海量日志吞吐）** ➔ `dispatcher`, `ops`, `reviewer-quality`：**选配响应最快、Token 成本最低的轻量或开源模型 + `none/low` 思考深度**。
   - **📏 上下文水位阈值「70% / 60% / 50% 黄金比例法则」（模型档位 `Tier` × 实际自动压缩窗口 `Window` × 思考深度 `Thinking`）**：
     - **窗口口径（以实际自动压缩死线为准）**：部分 Harness（如 `agy`）虽底层模型支持 1M，但客户端固定在 `262k` (`262,144`) 触发自动压缩，因此 `window_tokens` 以触发自动压缩的实际窗口为准；
     - **思考深度微调（以 `medium` 为基准）**：`high/xhigh` 深度思考抗干扰更强，阈值放宽 **`+5%`**；`low/off` 浅层思考易受历史噪音干扰，阈值收紧 **`-8%`**；
     - **Tier S（高智商旗舰级）**：`medium` 思考下 **`70%` 趁空闲压 (`ARMED`) / `80%` 派活前必压 (`DANGER`)**（例如 `262k` 窗口下：`low` `162k`、`medium` `183k`、`high` `196k` 趁空闲压）；
     - **Tier A（主力全能编码级）**：`medium` 思考下 **`60%` 趁空闲压 (`ARMED`) / `72%` 派活前必压 (`DANGER`)**（例如 `262k` 窗口下：`low` `136k`、`medium` `157k`、`high` `170k` 趁空闲压）；
     - **Tier B（中等参数开源 / 轻量级）**：`medium` 思考下 **`50%` 趁空闲压 (`ARMED`) / `62%` 派活前必压 (`DANGER`)**（**严格执行「物理大窗口 ≠ 高有效智力上限」原则**：十余 B 至数十 B 参数级开源模型受限于注意力容量，即便配置了超大窗口，`ARMED` 最高也封顶在 `90k~100k`；例如 `163k` 窗口下：`low` `68k`、`medium` `81k`、`high` `90k` 趁空闲压）。
2. **裁剪项目专属「活跃角色编制 (`active_roles`)」**：
   - 根据项目类型建议启用的角色子集（例如：纯 CLI / SDK 库 / 后端无界面项目默认剔除 `e2e` 与 `reviewer-ux`；个人轻量工具可按需剔除 `security-redteam`）。
3. **锁定「三类交付运行态 (`runtime_type`)」与版本锚点 (`version_anchors`)**：
   - **`daemon_port`（常驻服务/Web 类）**：确认 `base_port`（默认 `3000`）与启动命令（如 `npm run dev`）；
   - **`push_to_host`（寄生态插件类：浏览器扩展、油猴脚本、Obsidian/IDE 插件）**：`base_port: null`，确认构建命令、热推送命令（`push_cmd`）及验收目标站点 `target_url`；
   - **`artifact_only`（CLI 工具 / SDK 库 / 编译器）**：`base_port: null`，确认构建与测试命令；
   - 确认发版时需同步递增版本号的文件清单（`version_anchors`，如 `["package.json", "manifest.json", "src/config.ts"]`）。
4. **确认并发模式、跨特性上下文策略与水位巡检松紧度 (`probe_policy`)**：
   - **默认并发模式 (`mode`)**：`standard`（单工作区原地串行） vs `worktree`（多分支独立工作区高并发）；
   - **默认结项上下文打理策略 (`default_ctx`，针对 `standard` 模式)**：`"compact"`（默认推荐：压缩保留项目架构记忆）、`"clear"`（跨无关域清空归零）或 `"keep"`（连续微切片保留）；
   - **上下文水位巡检策略 (`context_monitor.probe_policy` —— 请人类二选一拍板)**：
     - **`"strict"`（严格逐步闸门模式）**：`Dispatcher` 在**每次唤醒任何下游角色前**均调用 `agent-context.sh <role>` 核验水位与 `+JUST_COMPACTED` 断崖 + 特性结项 `DONE` 全量盘点。**（当主力包含 Tier B 开源/本地模型、短窗口模型 `<=128k`、开启了 `pi-proactive-compact` 等外部自动压缩插件，或特性颗粒度较大时，优先推荐 `"strict"`）**；
     - **`"relaxed"`（宽松边界抽检模式）**：`Dispatcher` 仅在**特性结项 `DONE` 空闲期全量盘点 1 次**，常规一轮过（`round == 1`）中途免检；仅在发生多轮返工（`round >= 2` / `REPLAN`）或某角色开局距离 `ARMED` 不足 `35k` 且被二次唤醒前才执行单点抽检。**（当全队主力为 `200k~262k+` 大窗口 Tier S/A 旗舰模型且切片较小时，推荐 `"relaxed"` 以节省调度开销）**。
5. **推荐安装缺失的高价值基建工具与上下文监控设施（先给理由，由人类拍板决定装不装）**：
   - **代码图谱与静态健康工具**：若探测发现缺失 `gitnexus`、`jq`、`rg` 或当前语言核心静态分析器（如 TS/JS 缺 `fallow`、Rust 缺 `clippy`、Go 缺 `golangci-lint`、Python 缺 `ruff`），必须先说明**该工具在本项目中的具体作用与推荐理由**及 1 行安装命令，由人类拍板决定是否安装；将最终确认可用的验证命令固化进 `toolchain`，**后续日常运行直接读取配置执行，不再每次重复探测浪费 Token**；
   - **强烈推荐安装 `herdr-agent-usage`（跨 Harness 实时水位与额度插件）**：若 Step 1 探测未安装 `herdr-agent-usage`，主动向人类推荐安装（说明理由：① 在 Herdr 侧边栏直观展示各窗格实时上下文进度条与 5h/7d 配额；② 为 `Claude/Agy` 提供零扫描开销的 `statusline` 实时水位缓存供 `scripts/agent-context.sh` 直读），并将安装状态记录进 `.agents/environment.json` 的 `context_monitor.herdr_agent_usage_installed`；
   - **`pi` Agent 压缩插件策略说明（防抢跑误伤采蜜 & 防双插件冲突）**：若项目大量使用 `pi` Agent，向人类说明本套体系的配合准则：
     1. **严禁同时挂载 `pi-proactive-compact` 与 `pi-smart-compact`**（会引发 `session_before_compact` 事件竞态与双重压缩污染）；
     2. **推荐由 `Dispatcher` 统一宏观统筹（无需依赖 `pi-proactive-compact` 自动抢跑）**：`scripts/agent-context.sh` 原生即可直接读取 `~/.pi/agent/sessions/` 下的精确 Token 水位；由 `Dispatcher` 在「派活前闸门」与「`Reflector` 采蜜完成后」统一发起压缩，可避免 `pi-proactive-compact` 在回合结束瞬间自动抢跑压缩而**误伤 `Reflector` 所需的原始报错现场**或造成尾步派活锁阻塞；
     3. **若宿主全局已安装 `pi-proactive-compact` 且希望保留**：将 `context_monitor.pi_proactive_compact_installed` 记为 `true`；`Dispatcher` 仍通过 `agent-context.sh` 宏观监控全局，一旦捕捉到插件自动压缩产生的 `+JUST_COMPACTED` 断崖信号，立即在下一条派活指令中强制注入「重读 `roles/<role>.md`」指令以防失忆。
6. **推荐 AI 友好型领域方案与专业垂类/工具 Skill 选装及按角色挂载 (`domain_skills` —— 必须附推荐理由并由人类拍板）**：
   - **从 0 到 1 新项目方案建议**：若项目尚在技术选型阶段，主动给出对 AI Agent 最透明友好的白盒方案建议与理由（例如：现代 Web 前端推荐 `TypeScript + Tailwind CSS + shadcn/ui`——理由是组件源码直接落盘在项目内而非黑盒 `node_modules`，便于 Agent 直读直改与类型校验），供人类拍板；
   - **垂类领域与工具 Skill 推荐清单（严禁未经授权私自安装）**：结合项目核心框架/库与已启用工具（如 TS/JS 项目启用了 `fallow` 时推荐官方 `fallow-rs/fallow-skills`，前端推荐 `shadcn/ui`、React/Next.js、Chrome Extension MV3、Obsidian、Rust Tokio、FastAPI 等），汇总 Step 1 扫描到的本机既有 Skill 以及通过 `npx skills find <keyword>` / 联网搜索发现的外部最新高评价 Skill，向人类逐项呈报 **4 要素供拍板决定装不装**：
     1. **Skill 名称与安装来源**（本机已有路径，或 `npx skills add <owner/skill>`，如 `npx skills add fallow-rs/fallow-skills`）；
     2. **针对本项目的具体推荐理由（Why）**（说明它能提供什么最新框架规范或工具标准用法、能帮 Agent 避开什么常见反模式或参数臆测）；
     3. **拟精准挂载的角色（Who）**（遵循“按职责挂载、拒绝全员无脑加载”原则：如将 `shadcn-ui` 仅挂载给 `["planner", "coding", "reviewer-ux"]`，将 `fallow-skills` 仅挂载给 `["reviewer-quality", "reviewer-arch", "explorer"]`，让 `dispatcher`、`ops` 等无关角色保持零上下文负担）；
     4. **是否启用/安装（请人类拍板 Yes/No）**。

### Step 3：配置落盘、图谱建库与活文档骨架初始化 (`Scaffolding`)
待人类对 Step 2 方案（含选装哪些工具与 Skill）明确拍板后，依次执行以下幂等建场动作：

1. **仅安装人类明确拍板同意的外部工具与领域 Skills，写入 `.agents/environment.json`**：
   - 仅对人类在 Step 2 明确同意安装的项执行安装命令（如 `npx skills add <owner/skill>`；人类未勾选或拒绝的项严禁安装）；
   - 严格按照 [`SKILL.md` §6](../SKILL.md) 的标准结构，将对齐后的完整配置（含 `mode`、`default_ctx`、`runtime_type`、`base_port`/`target_url`、`active_roles`、`toolchain`、`version_anchors`、`domain_skills`、`harness_profiles` 以及包含 `thinking` 与实测 `cli_args` 数组的 `roles` 映射）写入 `.agents/environment.json`。
2. **加固 `.gitignore`**：
   检查项目 `.gitignore`，确保包含 `.worktrees/`、`.ops-pane`、`.ops.pid`（防止 Worktree 目录与后台守护子窗格句柄污染版本库）。
3. **初始化代码图谱与存量静态基线**：
   - 执行 `npx gitnexus analyze` 建立 AST 代码知识图谱；
   - 若为存量项目且启用了支持基线豁免的静态分析器（如 `fallow`），运行 `fallow --save-regression-baseline .fallow-baseline.json` 建立存量基线（确保后续审查“存量不误伤，增量零退化”）。
4. **创建核心活文档标准工件与顶层 `AGENTS.md` 防失忆重载锁（若尚不存在）**：
   - **`changes/KANBAN.md`**：创建包含 `## 📥 需求收件与待开展占位池 (Inbox / Backlog)`、`## 🚀 进行中 (In Progress)`、`## ✅ 已完成 (Done)` 以及底部 **`## 📌 规划台交接备忘 (Planner Handoff)`**（供高水位时按 EESV 四要素传位「Planner 二世」）的全局看板；
   - **`GLOSSARY.md`**：创建项目级统一领域语言词典（若为存量项目，扫描核心模块提取初始的 5~10 个业务领域概念填入；严禁混入类名/表名等实现细节）；
   - **`E2E_PLAYBOOK.md`**：仅当 `active_roles` 包含 `e2e` 时创建 6 要素结构化导航记忆表头；
   - **`AGENTS.md`（及 `CLAUDE.md` 软链/同步）注入「上下文压缩自检与角色书强制重载铁律」**：在项目根目录的 `AGENTS.md` 中确保写入以下跨角色保底条款，使任何角色在经历被动自动压缩或主动压缩后 100% 自动恢复职责与命令规范记忆：
     > **【上下文压缩自检与强制重载协议 (Post-Compaction Mandatory Reload)】**：每当你收到新指令或恢复执行时，先检查自身上下文窗口顶部是否存在压缩摘要（如 `<CONTEXT_SUMMARY>` / `Summary of previous conversation`）。若存在压缩摘要，且**在该摘要之后的未压缩对话记录中尚未重新读取过你所属的角色契约 `.agents/skills/herdr-teamwork/roles/<your-role>.md`**，说明你刚经历了上下文压缩！你**必须将「调用文件读取工具完整重读 `roles/<your-role>.md` 与 `tools/herdr.md`（若职责涉及执行 herdr 命令）以及当前 `changes/<id>/pipeline.jsonl` 尾部」作为你的第 1 个动作**，严禁凭压缩摘要的模糊印象盲猜命令参数或越界操作！

### Step 4：拉起常驻控制台拓扑并保存 `session.json` (`Spawn Console Topology`)
严格读取 **[`tools/herdr.md`](../tools/herdr.md)** 中 `§[H-1]`、`§[H-2]` 与 `§[H-3]` 的标准指令配方，依次完成常驻控制台拉起与快照落盘：
1. **切分双主控窗格与独立 `ops` 标签页（按 [`tools/herdr.md §[H-1]`](../tools/herdr.md)）**：
   - 在当前 Tab 向右切分出窗口 1（`PLANNER_PANE`）与窗口 2（`DISP_PANE`），并在当前工作区新建独立 `ops` Tab 获取其根窗格（`OPS_PANE`）。
2. **按 `environment.json` 启动三大常驻角色（按 [`tools/herdr.md §[H-2]`](../tools/herdr.md)）**：
   - 分别读取 `.agents/environment.json` 中 `planner`、`dispatcher`、`ops` 的 `harness` 与 `cli_args` 数组，在对应窗格启动三个角色实例。
3. **发送就位提示（按 [`tools/herdr.md §[H-3]`](../tools/herdr.md) 异步发送，不带 `--wait`）**：
   - 向 `planner` 发送：「请阅读 `.agents/skills/herdr-teamwork/SKILL.md`、`roles/planner.md` 与 `tools/herdr.md`，作为窗口 1 总规划台就位，读取 `changes/KANBAN.md` 与 `GLOSSARY.md` 等候人类需求。」
   - 向 `dispatcher` 发送：「请阅读 `.agents/skills/herdr-teamwork/SKILL.md`、`roles/dispatcher.md` 与 `tools/herdr.md`，作为窗口 2 交付总控台就位。」
4. **导出 `.agents/session.json` 快照（按 [`tools/herdr.md §[H-2]`](../tools/herdr.md)）**：
   - 运行 `§[H-2]` 中的 `herdr agent list | jq ...` 配方，将当前活跃角色拓扑、模型与 `conversation_id` 落盘至 `.agents/session.json`（自动过滤临时 `bootstrap` 自身）。

### Step 5：功成身退 (`Self-Teardown`)
1. 向人类输出简短的《建场完成汇报》（说明 `planner`、`dispatcher`、`ops` 窗格已就绪，`.agents/environment.json` 与 `.agents/session.json` 已落盘）；
2. **按 [`tools/herdr.md §[H-6]`](../tools/herdr.md) 关闭自身临时引导窗格**（传入 `$HERDR_PANE_ID`），把终端屏幕彻底交还给纯净的左窗格 `Planner`（窗口 1）与右窗格 `Dispatcher`（窗口 2）！
