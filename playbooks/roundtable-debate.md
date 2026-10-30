# Playbook: 重大架构变更圆桌辩论 (`roundtable-debate`)

> **定位**：Stage 1 宏观预审的「重型升级版」。由原 `planner` 临时 Fork 出一个一次性**圆桌主席分身**，组织多位专家「背靠背亮牌 ➔ 定向交锋 ➔ 主席裁决」，裁决落盘后分身销毁，原 `planner` 只消费结论。

---

## 1. 适用场景与触发条件 (When to Use)

仅当议题**同时满足**以下 3 条时才开圆桌（否则走常规 Stage 1 单点专家咨询）：
1. **难以逆转（单向门）**：核心数据模型、公共接口协议、模块边界或技术选型一旦落地回滚代价极高；
2. **跨维度显著权衡**：至少牵涉 2 个专业维度的正交张力（如 `arch` 求抽象解耦 vs `perf` 求扁平低延迟、`security` 求最小攻击面 vs `ux` 求低摩擦）；
3. **存在 2~3 套互斥候选方案**，且 `planner` 无法仅凭单一专家意见定夺。

---

## 2. 角色分工链路 (Role Handoff Chain)

| 角色 | 职责 |
| :--- | :--- |
| **原 `planner`（Window 1）** | 立题、点名参会专家、Fork 圆桌主席分身；收到结论后向人类呈报并请其点头；点头后固化进 `spec.md` 与 `docs/adr/<id>.md`。**辩论过程中不读专家原始发言，上下文保持纯净。** |
| **圆桌主席分身 (`planner-roundtable`，临时 Fork)** | 以本文件为唯一行动指南；组织两轮发言、提炼冲突、裁决并落盘 `roundtable.md`；完成后通知原 `planner` 并退出。**不是第 17 个常驻角色。** |
| **参会专家（2~4 人）** | 从 `reviewer-arch` / `reviewer-perf` / `reviewer-security` / `reviewer-ux` / `explorer` 中按议题点名，**不限篇幅**，须以代码事实与 5 级证据阶梯立论。 |
| **人类** | 对主席裁决「点头 / 否决 / 要求补议」。 |

```
[planner] 立题落盘 roundtable.md ➔ Fork 主席分身
      │
      ▼
[主席] 第 1 轮：背靠背独立亮牌 (并发，专家互不可见)
      │ ── 观点一致 ──────────────┐
      ▼ 存在冲突                    │
[主席] 第 2 轮：冲突双方定向交锋 (1 轮)  │
      │                              │
      ▼◄────────────────────────────┘
[主席] 裁决 ➔ 写入 roundtable.md ➔ 通知 planner ➔ 分身退出
      │
      ▼
[planner] 向人类呈报 ➔ 人类点头 ➔ 写入 spec.md + docs/adr/<id>.md
```

---

## 3. 分步执行规程 (Step-by-Step)

### 步骤 0：`planner` 立题与 Fork 主席分身
1. 创建 `changes/<id>/roundtable.md`，写入 **议题陈述**（一句话唯一争议问题）、**候选方案 A/B(/C)**、**参会专家名单与各自代表的维度**、**必须回答的约束**（如目标 QPS、兼容性要求）。
2. 临时 Fork 主席窗格并启动（复用 `.agents/environment.json` 中 `planner` 的 harness / model / thinking 配置）：
   ```bash
   RT_PANE=$(herdr pane split --target "${HERDR_PANE_ID}" --direction down -q)
   herdr agent start planner-roundtable --kind "$(jq -r '.roles.planner.harness' .agents/environment.json)" --pane "$RT_PANE" -- --model "$(jq -r '.roles.planner.model' .agents/environment.json)"
   herdr agent prompt planner-roundtable "你是圆桌主席分身。仅按 .agents/skills/herdr-teamwork/playbooks/roundtable-debate.md 第 4 节执行，议题见 changes/<id>/roundtable.md；完成后输出 ROUNDTABLE_DONE 并结束。"
   ```
3. 异步等待（或继续与人类讨论其他规划），收到 `ROUNDTABLE_DONE` 后读取 `roundtable.md` 的【裁决摘要】节。

### 步骤 1：主席分身执行规程（第 4 节）见下。

---

## 4. 圆桌主席分身行动指南 (Chair Protocol)

> 你是临时分身，只负责本次议题。**严禁修改 `prd.md` / `spec.md` / `tasks.md` / `KANBAN.md` / `pipeline.jsonl`，严禁读写业务源码**；你的唯一写入对象是 `changes/<id>/roundtable.md`。

### 4.1 第 1 轮：背靠背独立亮牌与类型草图征集 (Blind Opening & Type Sketch)
对每位参会专家（复用常驻窗格，不存在则按 `SKILL.md` 7.3 节方式拉起）**并发**派发，且**不得透露其他专家的存在、立场或发言**（若议题仅有痛点尚无成型候选方案，要求各专家先按各自维度独立草拟一套**仅含类型签名与调用方示例、函数体填 `not implemented` 的接口草图 Type Sketch**）：
```bash
herdr agent prompt <expert> "圆桌议题见 changes/<id>/roundtable.md。请仅从你的专业维度独立立论，不限篇幅，必须包含：① 推荐方案及排序（若尚无现成方案，请直接给出你设计的类型签名与调用方代码示例草图 Type Sketch）；② 支撑证据（file:line / gitnexus 取证 / 量级推算，禁止教科书套话）；③ 若忽视你所代表维度，最先在哪里出事；④ 你能接受的最小让步条件。输出完毕后结束回合。" 
herdr agent wait <expert> --timeout 300000
herdr agent read <expert> --source recent-unwrapped --lines 200
```
将各专家原话**按原文**写入 `roundtable.md` 的【第 1 轮立论】节（保留证据，不转述润色）。

### 4.2 冲突提炼
- 所有专家推荐一致且无「最小让步条件」冲突 ➔ 跳过第 2 轮；
- 否则提炼 **唯一最关键的冲突焦点**（如「`arch` 的抽象层是否会让热点路径多一次间接调用」），明确**冲突双方**（可多于两方，每个焦点一组）。

### 4.3 第 2 轮：定向交锋 (Targeted Clash，仅 1 轮)
只对冲突方，把**对方的原始立论**喂给他，要求正面回应：
```bash
herdr agent prompt <expert> "对方立论见 changes/<id>/roundtable.md【第 1 轮立论】中 <对方> 一节。针对冲突焦点「<焦点>」：① 指出对方立论依赖的前提是否成立（给出证据）；② 若成立，你愿意接受的折中修正是什么；③ 给出你的最终推荐。仅此一轮。"
```
将回应原文写入【第 2 轮交锋】节。**严禁发起第 3 轮**；仍无法调和的分歧由主席在裁决中显式取舍。

### 4.4 裁决：单一主干底座 + 局部优势嫁接 (Verdict: Base + Graft)
主席必须给出**唯一裁决方案**（**禁止和稀泥、禁止把问题抛回人类、禁止把两个互斥方案硬拼成四不像的委员会缝合怪**）：必须**选定某一套结构自洽的方案作为唯一主干底座（Base），仅将其他专家合理的核心防线或局部优秀接口设计嫁接（Graft）到该主干上**，写入 `roundtable.md` 顶部【裁决摘要】：
```markdown
## ⚖️ 裁决摘要
- **议题**：...
- **裁决方案（主干底座 + 嫁接项）**：以方案 X 为唯一主干底座，嫁接融入 <专家> 提出的 <具体局部设计/防线>
- **采纳依据**：采纳了 <专家> 的 <论据>（证据等级 Level N）
- **牺牲项**：为此放弃/弱化了 <维度/指标>，原因 ...
- **败方风险的缓解措施**：针对 <专家> 指出的 <风险>，通过 ... 规避
- **各方分歧与交锋摘要**（3~5 行）
- **建议 ADR**：是否满足 3 条件 ➔ 是 / 否
```
证据不足以裁决时（关键前提无 Level 3 以上证据），在摘要中标注 `NEEDS_SPIKE` 并建议 `playbooks/prototype-spike.md`，而非强行拍板。

### 4.5 收尾
输出单行 `ROUNDTABLE_DONE: changes/<id>/roundtable.md`，原 `planner` 读取后由其 `herdr pane close` 销毁本窗格（主席不得自行销毁以免丢失回执）。

---

## 5. 人类点头与固化 (Close the Loop)

1. 原 `planner` 向人类呈报【裁决摘要】（不转述全文，提示 `roundtable.md` 路径供深读），请人类选择：**点头 / 否决并指明理由 / 要求补议某焦点**；
2. **点头后**：将裁决写入 `spec.md`；若 ADR 三条件满足，创建 `docs/adr/<id>.md`（引用 `roundtable.md`）；
3. 否决或补议：由 `planner` 更新议题后重新 Fork 主席（新分身，不继承旧上下文）。
