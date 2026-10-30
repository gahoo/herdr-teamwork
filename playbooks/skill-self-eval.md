# Playbook: 技能自省与盲测重评 (`skill-self-eval` — Skill Self-Evaluation & Blind Re-evaluation)

> **定位**：本剧本专用于检验**「指挥 Agent 的契约本身（`SKILL.md` / `roles/*.md` / `playbooks/*.md` / `AGENTS.md`）」**在重大改版后的真实有效性。
> 当 `reflector`（节点 6 双层自演进）或人类重写、精简或新增了关键角色契约条款时，通过**防迎合隐蔽沙盒 + A/B 盲评打分**，实证检验新版契约是否真正改善了 Agent 行为（日常 1~2 行微调无需触发本剧本）。

---

## 1. 触发条件与协作链路 (`Initiator ➔ Executor`)

- **触发条件 (When)**：
  1. 对 `SKILL.md`、`roles/<role>.md` 或项目级 Skill 执行了结构性重写、大幅裁剪或新增高危红线，需验证未发生遵从度退化（Regression）；
  2. 某条写入契约的防错规则反复被 Agent 无视，需通过对照实验定位如何改写提示词才能让 Agent 真正执行。
- **角色分工**：
  - **发起与统筹 (`reflector`)**：定义评测任务与评分标尺（Rubric），汇总盲评得分并裁决契约去留；
  - **被测执行者 (`Target Role Agent`)**：在完全不知情的隐蔽沙盒中按常规角色身份执行任务；
  - **盲评裁判 (`Blind Judge`)**：优先选用与被测 Agent **不同模型家族**的独立实例，对匿名隐去版本身份的产物对照 Rubric 逐项打分。

---

## 2. 四步盲测重评规程 (4-Step Blind Self-Evaluation Loop)

### Step 1：制定可观测行为标尺 (`Rubric Definition` —— 0~3 分制)
将待验证的契约修改目标拆解为 **3~5 个可凭物证判定的具体行为维度**，严禁使用“代码更优雅”、“思考更全面”等主观词：

| 评估维度示例 | `0 分 (违背)` | `1 分 (走过场)` | `2 分 (达标)` | `3 分 (卓越且有物证)` |
| :--- | :--- | :--- | :--- | :--- |
| **修改前图谱爆炸半径核查** | 未调用 `gitnexus impact` 直接改代码 | 改完代码后才补跑 `impact` 凑数 | 改前运行了 `impact` 但未在汇报中引用结果 | 改前运行 `impact` 并准确列出受波及的直接调用方与应对措施 |
| **领域垂直内聚与反 `utils` 倾倒** | 直接在全局 `utils/` 新建业务辅助函数 | 放在业务目录但跨模块直接 import 内部私有文件 | 函数内聚于所属领域目录并通过 `index` 门面导出 | 内聚于领域目录、单门面导出且关联单测就地共存 |

### Step 2：构建防迎合隐蔽沙盒 (`Anti-Gaming Camouflaged Sandbox`)
> ⚠️ **反霍桑效应铁律**：AI Agent 一旦从工作目录路径、Git 分支名或 Prompt 中嗅出自己正在接受“考试/评测（Eval / Benchmark / Test）”，就会激活迎合模式（刻意把每一步规程做满），导致评测结果严重失真。

1. **真实感伪装命名**：在 `/tmp/` 下使用逼真的业务项目名创建隔离目录（如 `/tmp/ invoice-sync-service` 或 `/tmp/meridian-core`）；
2. **敏感词清零**：沙盒路径、分支名、初始 Commit 消息与下发给被测 Agent 的 Prompt 中，**严禁出现 `eval`、`benchmark`、`rubric`、`self-eval`、`experiment`、`candidate` 等任何暗示评测的字眼**；
3. **埋设真实诱惑陷阱**：在沙盒代码中预置一处诱发旧习的现场（例如：故意留一个现成的 `src/utils/helpers.ts` 垃圾桶，或留一个有 8 个上游调用方的浅模块函数），观察被测 Agent 是否会踩坑。

### Step 3：A/B 双盲对照执行 (`Baseline vs Candidate Run`)
1. 在两个完全一致的隐蔽沙盒副本中，分别挂载 **改版前契约（`Baseline`）** 与 **改版后契约（`Candidate`）**；
2. 向两个沙盒中的被测角色发送**一字不差的真实业务指令**（如：`“请按 changes/002-tax-calc/spec.md 完成代码实施并自检”`）；
3. 完整采集两边的两类客观物证：
   - **工具调用序列 (`Tool Call Trace`)**：调用了哪些命令、先后顺序如何；
   - **最终产物 (`Git Diff & Terminal Output`)**：代码修改 Diff 与角色终端汇报文本。

### Step 4：跨模型匿名盲评与去留裁决 (`Blind Judge & Hillclimb Verdict`)
1. **匿名打乱**：将 `Baseline` 与 `Candidate` 的物证随机标记为 `Sample Alpha` 与 `Sample Beta`（隐去哪份是新版）；
2. **独立裁判打分**：将两份匿名样本与 Step 1 的 Rubric 发给独立裁判实例（Judge），要求其对每个维度给出 `0~3` 分，并**必须贴出对应的工具调用记录或代码行号作为给分证据**；
3. **契约去留铁律**：
   - **✅ 正式合入**：`Candidate` 在目标改进维度得分提升 $\ge 1$ 分，且其余维度无退步；
   - **🔄 识别无效空话并回滚 (`No-Op Rollback`)**：若 `Candidate` 新增了一段规程条文，但盲测得分与 `Baseline` 完全持平（说明模型根本没听进去），**严禁保留这段无效文字污染上下文**！必须立即 `git checkout` 回滚该条文，转而改写为更直白的正向触发句式（`当遇到 X 时，执行 Y`），或直接下沉为 Level 2 自定义 Lint/脚本机械阻断。
