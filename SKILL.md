---
name: herdr-teamwork
description: Multi-agent spec implementation orchestrated via Herdr terminal panes and tabs (Main, Coding, Test, optional Reviewer agents). Use when initiating multi-agent spec implementation, complex code changes, or when the user requests multi-agent teamwork.
---

# Herdr Multi-Agent Teamwork (多 Agent 协同体系)

本技能通过 Herdr 终端工作区管理工具构建多 Agent 物理隔离与协作体系。
支持根据任务复杂度灵活选择 **高效模式 (Main 兼任)**、**严格双盲模式 (冷启动独立 Reviewer)** 或 **分叉上下文模式 (Fork-Session 独立审查)**，并具备**角色契约内聚**与**跨引擎兼容（agy / claude / codex / pi 等）**能力。

---

## 1. 三种审查与协作模式对比

在需求对齐阶段，Main Agent 与用户确认采用何种模式（未特殊指明时默认采用高效模式）：

| 模式 | 拓扑结构 | Review 担当 | 适用场景 | 核心优势 |
| :--- | :--- | :--- | :--- | :--- |
| **模式 A：高效模式 (默认)** | 单 Tab 3-Pane | **Main Agent 兼任** | 中小型需求、日常迭代、常规 Bug 修复、交互细节较多的任务 | **零隐性意图丢失**，深度结合对话共识；拓扑轻捷，通信链路短，时延低。 |
| **模式 B：严格双盲模式** | 单 Tab 3-Pane + 独立 `review` Tab | **独立 Review Agent (冷启动)** | 规范明确的重大底层重构、安全漏洞修复、契约级严格交付 | **局外人客观视角**，无思维惯性，严格以 `spec.md` 契约为唯一标准进行双盲审查。 |
| **模式 C：分叉上下文模式 (Fork-Session)** | 单 Tab 3-Pane + 独立 `review` Tab | **独立 Review Agent (分叉会话)** | 具有大量前期讨论、隐性共识，但又需要高阶模型深度审查的高风险复杂需求 | **兼具 A 的意图理解与 B 的物理隔离**：100% 继承前序讨论记忆；Main 上下文不被审查细节污染；切换红方审计视角严厉挑刺。 |

---

## 2. 角色契约与职责隔离 (Role Contracts)

为了防止多 Agent 协作中的“角色越权”与“职责模糊”，本技能在 `roles/` 目录下内聚定义了各子 Agent 的专属系统契约与绝对红线：

| 角色 | 契约文件 | 核心职责 | 绝对红线 (Hard Boundaries) |
| :--- | :--- | :--- | :--- |
| **Coding Agent** | [`roles/coding.md`](roles/coding.md) | 业务代码实施与局部逻辑实现 | **严禁修改任何测试文件 (`*.test.*`)**；严禁私自扩展未经 `spec.md` 约定的需求。 |
| **Test Agent** | [`roles/test.md`](roles/test.md) | 编写并运行自动化测试 (Vitest) | **严禁修改任何非测试业务代码**；测试失败时如实报告，绝不为了测试变绿而篡改业务实现。 |
| **Ops Agent** (独立 Tab) | [`roles/ops.md`](roles/ops.md) | 环境准备、依赖安装、项目编译构建（npm run build）、常驻后台服务守护、数据库快照灾备与受控 Git 发布流水线执行 | **严禁修改任何业务代码与测试用例**；严禁越权审计（安全/体积审计归 Reviewer）；严禁擅自提前 commit；严禁向 Main 倒灌原始终端日志。 |
| **Debug Agent** (按需唤起) | [`roles/debugger.md`](roles/debugger.md) | 深度逆向推导、根因定位与修复方案规格 (Fix Spec) 设计 | **只读权限，严禁直接修改业务代码与测试用例**；严禁进行表象打补丁 (Symptom Patching)；严禁倒灌海量原始调试 dump。 |
| **Review Agent** | [`roles/reviewer.md`](roles/reviewer.md) | 契约审计与质量把关（含代码审查、CVE 依赖安全与包体积准入审计） | **只读权限，严禁修改任何文件**；直接向责任 Agent 直连反馈具体问题，不经 Main 中转。 |

### 2.1 职责正交与上下文保护原则 (Context Hygiene)
- **调度核心，极简视界**：Main Agent 负责用户沟通、需求对齐、架构决策与最终质量把控，其上下文是整个团队认知对齐的枢纽，必须竭力避免被琐碎的代码细节、环境构建日志或安装包进度污染。
- **环境、运维与发布独占独立 Tab**：依赖包安装、环境探针、编译打包构建（`npm run build`）、常驻后台服务（`dev/start`）、数据库快照与受控 Git 提交由专属 **Ops Agent** 在独立的 `ops` Tab 中常驻承接，彻底物理隔离海量终端噪音与后台守护进程，解放 Coding Agent 和 Main Agent。
- **关于 `/rewind` 的精准定位**：
  - 由于环境与构建杂事已由独立 `ops` Tab 物理吸收，Coding Agent 不再需要兼任环境杂事；
  - **`/rewind` 回归其核心本质用途**：专用于 Coding Agent 进行**探索性代码重构、临时辅助脚本编写、或单点方案验证**时。在尝试完毕或取得局部成果后，通过 `/rewind` 安全回滚思考过程，丢弃分叉过程的认知负担，同时保留磁盘文件改动，实现代码探索的“轻装再出发”。

---

## 3. 终端与 Pane 拓扑布局

该拓扑**长期复用**。新任务开始时通过清空或重置 Agent 会话复用环境，无需反复创建销毁 Pane。

### 模式 A：高效模式拓扑 (单 Tab 3-Pane)
```
+-------------------------------------------------------------+
|                         主工作 Tab                           |
+------------------------------+------------------------------+
|                              | Coding Agent (右上)          |
| Main Agent (左侧，全高)      | 角色: roles/coding.md        |
| 模型: 深度思考高阶模型        +------------------------------+
| 职责: 讨论规划 + 协调调度    | Test Agent (右下)            |
|       + 意图对齐审查(Review) | 角色: roles/test.md          |
+------------------------------+------------------------------+
```

### 模式 B & 模式 C：独立 Reviewer 拓扑 (单 Tab 3-Pane + 独立 `review` Tab)
```
+-------------------------------------------------------------+
|                         主工作 Tab                           |
+------------------------------+------------------------------+
|                              | Coding Agent (右上)          |
| Main Agent (左侧，全高)      | 角色: roles/coding.md        |
| 模型: 深度思考高阶模型        +------------------------------+
| 职责: 讨论规划 + 总体调度    | Test Agent (右下)            |
|                              | 角色: roles/test.md          |
+------------------------------+------------------------------+

+-------------------------------------------------------------+
|                     独立 Tab: "review"                      |
+-------------------------------------------------------------+
| Review Agent (全屏)                                         |
| 角色: roles/reviewer.md                                     |
| 模型: gemini-3.8-flash-high                                  |
| 模式 B: 冷启动双盲审查 / 模式 C: Fork Session 上下文继承审查   |
+-------------------------------------------------------------+
```

### 按需常驻：独立 `ops` Tab (运维与环境守护)
当项目涉及依赖安装、项目完整编译打包（`npm run build`）或常驻后台服务（`npm run dev` / `next start`）时，按需开启独立的 `ops` Tab：
```
+-------------------------------------------------------------+
|                     独立 Tab: "ops"                         |
+-------------------------------------------------------------+
| Ops Agent (全屏独占，推荐模型: gemini-3.8-flash-low)        |
| 角色: roles/ops.md                                          |
| 职责: 后台开发服务常驻守护 (dev / start / db / docker)        |
|       + 全量编译打包 (npm run build / tsc)                  |
|       + 依赖包安装更新 (npm install) + 端口/网络探针检测      |
+-------------------------------------------------------------+
```

---

## 4. 拓扑初始化与跨引擎启动机制 (Engine-Agnostic)

Herdr 原生支持多种 Agent 客户端（`--kind` 支持 `agy`, `claude`, `codex`, `pi` 等）。无论使用哪种客户端，通过统一的**角色握手指令 (Role Handshake)** 完成专属人设与行为边界注入。

在派发任务前，Main Agent 检查所需 Agent 是否已经就绪：
```bash
herdr agent list
```

### 基础 3-Pane（模式 A / B / C 公用）初始化步骤
```bash
# 1. 在主 Tab 中右侧分屏建立 Coding Pane
CODING_PANE=$(herdr pane split --current --direction right --cwd "$PWD" --no-focus | jq -r '.result.pane.pane_id')

# 2. 在 Coding Pane 下方分屏建立 Test Pane
TEST_PANE=$(herdr pane split --pane "$CODING_PANE" --direction down --cwd "$PWD" --no-focus | jq -r '.result.pane.pane_id')

# 3. 启动 Coding 与 Test Agent（此处以 agy 为例，亦可换用 --kind claude / codex / pi）
herdr agent start coding --kind agy --pane "$CODING_PANE" -- --model gemini-3.8-flash-medium
herdr agent start test --kind agy --pane "$TEST_PANE" -- --model gemini-3.8-flash-medium

# 4. 角色握手 (Role Handshake)：注入专属行为契约与红线
SKILL_DIR="$(pwd)/.agents/skills/herdr-teamwork"
herdr agent prompt coding "请阅读并严格遵照执行位于 $SKILL_DIR/roles/coding.md 的角色契约与红线准则。"
herdr agent prompt test "请阅读并严格遵照执行位于 $SKILL_DIR/roles/test.md 的角色契约与红线准则。"
```

### 模式 B（严格双盲模式）独立 Tab 初始化
```bash
REVIEW_TAB=$(herdr tab create --name review --cwd "$PWD" | jq -r '.result.tab.tab_id')
REVIEW_PANE=$(herdr pane list | jq -r ".result.panes[] | select(.tab_id == \"$REVIEW_TAB\") | .pane_id")

# 冷启动独立 Reviewer（零先入为主）
herdr agent start reviewer --kind agy --pane "$REVIEW_PANE" -- --model gemini-3.8-flash-high
herdr agent prompt reviewer "请阅读并严格遵照执行位于 $SKILL_DIR/roles/reviewer.md 的角色契约与红线准则。"
```

### 模式 C（分叉上下文模式 Fork-Session）独立 Tab 初始化
```bash
REVIEW_TAB=$(herdr tab create --name review --cwd "$PWD" | jq -r '.result.tab.tab_id')
REVIEW_PANE=$(herdr pane list | jq -r ".result.panes[] | select(.tab_id == \"$REVIEW_TAB\") | .pane_id")

# 1. 以分叉/恢复当前会话方式启动（若底层 CLI 支持 --conversation 或 session fork）
herdr agent start reviewer --kind agy --pane "$REVIEW_PANE" -- --conversation "$HERDR_CURRENT_CONV_ID" --model gemini-3.8-flash-high

# 2. 注入红方审计握手指令（切换视角，克服证实偏见）
herdr agent prompt reviewer "【视角切换】你当前作为独立 Reviewer。你已完整继承前序讨论的全部隐性意图与背景，请阅读并严格执行 $SKILL_DIR/roles/reviewer.md。请切换为红方挑刺（Red Teaming）视角，审视 Coding 和 Test 的产出是否真正达成了我们此前达成共识的业务目标与边界要求。"
```

### 按需常驻：独立 `ops` Tab 初始化步骤
```bash
# 1. 创建独立 ops Tab（物理隔离守护进程与构建日志）
OPS_TAB=$(herdr tab create --name ops --cwd "$PWD" | jq -r '.result.tab.tab_id')
OPS_PANE=$(herdr pane list | jq -r ".result.panes[] | select(.tab_id == \"$OPS_TAB\") | .pane_id")

# 2. 启动轻量 Ops Agent（选用 flash-low，兼顾极速与极低消耗）
herdr agent start ops --kind agy --pane "$OPS_PANE" -- --model gemini-3.8-flash-low

# 3. 角色握手指令
SKILL_DIR="$(pwd)/.agents/skills/herdr-teamwork"
herdr agent prompt ops "请阅读并严格遵照执行位于 $SKILL_DIR/roles/ops.md 的角色契约与红线准则。"
```

---

## 5. 协作流转机制

### 模式 A：Main 兼任审查流程
1. **双轨推进**：Coding Agent 实施代码，Test Agent 编写并执行测试；
2. **Main Agent 意图审查**：测试与代码完成后，Main Agent 基于对话共识与 `spec.md` 契约直接审阅 diff，调度 `gitnexus_detect_changes()` 与 Vitest 进行客观验证，指导修正。

### 模式 B：冷启动独立审查流程
1. **双轨推进**：同模式 A；
2. **双盲审查与直连反馈**：测试与代码完成后，分别唤起 Review Agent，Reviewer 基于 `spec.md` 契约通过 `herdr agent prompt coding/test` 发送具象直连修改意见；
3. **终审门禁**：通过后由 Main Agent 运行 `gitnexus_detect_changes()` 归档。

### 模式 C：分叉上下文继承审查流程
1. **双轨推进**：同模式 A；
2. **带记忆的红方审查**：
   - Reviewer 既知晓讨论中的历史妥协（不发生教条式误报），又深知隐性架构意图（不放过神似形不似的缺陷）；
   - Reviewer 通过直连命令指导 Coding/Test 进行精细修正；
3. **主会话免受污染**：审查细节与拉锯讨论留在 `review` 分叉 Tab，Main Agent 保持极简上下文与全局视野。

### 5.4 法医式排错协同流转规范 (Forensic Debugging Protocol)

当系统遭遇非浅层的复杂 Bug、逻辑暗坑、偶发竞态或测试用例挂掉时，**严禁 Coding Agent 带着证实偏差盲目试错或打表面补丁**，严格启动法医式五步闭环：

```
       Bug 现象 / 异常堆栈 / 测试红灯
                      │
                      ▼
  【第 1 步：立案】  Test Agent 编写最小可复现失败用例 (Red Test)
                      │
                      ▼
  【第 2 步：剖析】  按需唤起 Debug Agent (逆向推导，隔离根因)
                └── 产出：《根因诊断与修复规格 (Fix Spec)》 (严格只读，不改代码)
                      │
                      ▼
  【第 3 步：把关】  Main Agent 架构审定 (评估影响面，批准方案)
                      │
                      ▼
  【第 4 步：修复】  Coding Agent 外科手术式精准实施 (最小化行级改动)
                      │
                      ▼
  【第 5 步：验收】  Test Agent 运行测试变绿 (Green Test) ➔ Ops 验证打包
```

1. **第 1 步（立案）**：Test Agent 编写一个且仅一个最小化的失败测试，将 Bug 现象客观固定下来；
2. **第 2 步（剖析）**：Main Agent 按需唤起 Debug Agent（或 Fork 派生），Debugger 沿调用栈逆向推导状态扭曲起点，产出《根因诊断与修复建议报告》（严禁直接修改业务代码）；
3. **第 3 步（把关）**：Main Agent 审阅方案，确认修改方案影响面最小且不破坏现有架构风格；
4. **第 4 步（修复）**：Main Agent 将 Fix Spec 明确指派给 Coding Agent，Coding Agent 严格按照规格进行最小行级修复；
5. **第 5 步（验收）**：Test Agent 重新执行测试验证红灯变绿（Green Test），确认修复成功后销毁临时 Debugger。

---

## 6. 常用 Herdr 调度命令速查

- **派发任务并等待**：
  ```bash
  herdr agent prompt coding "请按照 changes/xxx/tasks.md 执行任务 1" --wait --timeout 120000
  ```
- **读取输出**：
  ```bash
  herdr agent read coding --source recent-unwrapped --lines 80
  ```
- **重置会话上下文 (新任务开始前)**：
  ```bash
  herdr agent prompt coding "/clear"
  herdr agent prompt test "/clear"
  # 若处于模式 B / C
  herdr agent prompt reviewer "/clear"
  ```
- **动态无损切换 Agent 模型（热切换保留上下文）**：
  ```bash
  # 避免退出重启 Agent 导致丢失上下文！直接发送 /model 命令无损热切换：
  herdr agent prompt coding "/model gemini-3.8-flash-medium"
  herdr agent prompt coding "/model gemini-3.8-flash-high"
  ```
  > **重要准则**：严禁为了更换模型而重启或销毁 Agent 会话。直接发送 `/model <model-name>` 可以原地即时切换思考模型，既不中断会话，又能 100% 完整保留历史对话与上下文记忆。
- **调度 Ops Agent 执行构建或环境运维**：
  ```bash
  # 调度 Ops 执行打包编译并等待高阶结果：
  herdr agent prompt ops "npm run build 并报告是否有构建或类型报错" --wait --timeout 60000
  # 调度 Ops 安装新依赖：
  herdr agent prompt ops "npm install xxx --save 并验证依赖状态" --wait
  # 查看后台常驻服务最新输出：
  herdr agent read ops --lines 50
  ```
- **使用 `/rewind` 进行探索性代码剪枝（保留磁盘成果，回退思考记忆）**：
  ```bash
  # 当 Coding Agent 完成了探索性实现尝试、编写了独立验证脚本，需要剪掉冗长排查记录时：
  herdr agent prompt coding "/rewind"
  ```
  > **定位更新**：由于依赖安装、项目编译与常驻服务已全权由独立 `ops` Tab 物理吸收，Coding Agent 不再需要兼任环境杂事；`/rewind` 回归其纯粹的核心用途——专用于业务代码探索时的**“对话记忆修剪与上下文保鲜”**。
- **按需唤起 Debug Agent 进行法医式排查 (On-Demand Debugger)**：
  ```bash
  # 1. 在主 Tab 中临时切分一个 debug pane
  DEBUG_PANE=$(herdr pane split --pane "w7:p2" --direction down --cwd "$PWD" --no-focus | jq -r '.result.pane.pane_id')
  # 2. 启动高推理模型 Debugger
  herdr agent start debug --kind agy --pane "$DEBUG_PANE" -- --model gemini-3.8-flash-high
  # 3. 注入角色契约与排错任务（只出方案，不直接改代码）
  herdr agent prompt debug "请阅读 roles/debugger.md 契约。请分析相关测试失败原因，深入排查根本原因并向 Main Agent 输出《根因诊断与修复建议报告》。" --wait
  # 4. 方案验收完成后，销毁临时 pane 保持屏幕整洁
  herdr pane close --pane "$DEBUG_PANE"
  ```

---

## 7. 会话状态持久化与零冷启动续接 (Session Persistence & Resume)

为了避免终端重启、系统关机或断电后 Agent 上下文丢失导致的“冷启动阵痛”，本技能支持将会话状态归档至 `.agents/session.json`（已加入 `.gitignore`）。

### 7.1 会话归档文件格式 (`.agents/session.json`)
```json
{
  "updated_at": "2026-10-09T17:23:00+08:00",
  "workspace_id": "w7",
  "project": "examBuilder",
  "agents": {
    "main": {
      "name": "main",
      "role": "需求对齐与调度",
      "tab_id": "w7:t1",
      "pane_id": "w7:p1",
      "model": "gemini-3.8-flash-high",
      "conversation_id": "c683900f-ced0-4186-952d-cbc930f255d4"
    },
    "coding": {
      "name": "coding",
      "role": "业务代码实施",
      "tab_id": "w7:t1",
      "pane_id": "w7:p2",
      "model": "gemini-3.8-flash-medium",
      "conversation_id": "caa7fca3-b51a-4ef7-a59c-69b5fde72c18"
    },
    "test": {
      "name": "test",
      "role": "自动化测试",
      "tab_id": "w7:t1",
      "pane_id": "w7:p3",
      "model": "gemini-3.8-flash-high",
      "conversation_id": "83852d7c-e35a-4658-aa56-80c8aa5095af"
    },
    "ops": {
      "name": "ops",
      "role": "环境与运维发布",
      "tab_id": "w7:t2",
      "pane_id": "w7:p4",
      "model": "gemini-3.8-flash-low",
      "conversation_id": "14004428-c9ed-4384-aec4-934544d0e946"
    }
  }
}
```

### 7.2 一键快照保存命令
在日常开发结束或阶段性里程碑时，执行以下命令从 Herdr 动态抓取当前各 Agent 的 Conversation ID 并持久化：
```bash
herdr agent list | jq '{updated_at: (now | todate), workspace_id: "w7", project: "examBuilder", agents: [.result.agents[] | {key: (.name // "main"), value: {name: (.name // "main"), pane_id, tab_id, conversation_id: .agent_session.value, model: (.terminal_title | capture("--model (?<m>[^ ]+)") | .m // "gemini-3.8-flash-high")}}] | from_entries}' > .agents/session.json
```

### 7.3 跨天/重启后零冷启动一键续接 (Resume)
当重新打开终端或开机后，在对应 Pane 重新启动 Agent 时传入 `--conversation` 参数，即可**100% 完整继承前序记忆与推理脉络原地复活**：
```bash
# 1. 恢复 Coding Agent（带着全部代码记忆苏醒）
CODING_ID=$(jq -r '.agents.coding.conversation_id' .agents/session.json)
herdr agent start coding --kind agy --pane "w7:p2" -- --conversation "$CODING_ID" --model gemini-3.8-flash-medium

# 2. 恢复 Test Agent
TEST_ID=$(jq -r '.agents.test.conversation_id' .agents/session.json)
herdr agent start test --kind agy --pane "w7:p3" -- --conversation "$TEST_ID" --model gemini-3.8-flash-high

# 3. 恢复 Ops Agent
OPS_ID=$(jq -r '.agents.ops.conversation_id' .agents/session.json)
herdr agent start ops --kind agy --pane "w7:p4" -- --conversation "$OPS_ID" --model gemini-3.8-flash-low
```



