#!/usr/bin/env bash
# scripts/agent-context.sh
# 跨 Harness 多 Agent 上下文水位探针 (Dual-Channel Context Watermark Probe)
#
# 设计准则：
# 1. 双通道感知：优先读取 herdr-agent-usage 状态行缓存/Metadata；兜底采用 256KB 有界尾部倒扫 (tail -c 262144) + 终端状态栏嗅探。
# 2. 严格会话归属 (Strict Attribution) + 失败闭合 (Fail-Closed)：仅按 herdr agent list 的 agent_session.value 精确匹配会话文件；未落盘时输出 UNATTRIBUTED，绝不伪造 0%。
# 3. 三维动态阈值 (Tier S/A/B × Window Size × Thinking Level)：自动探测模型、物理窗口与思考等级 (off/low/medium/high/xhigh)，动态计算 ARMED 与 DANGER 阈值并检测 JUST_COMPACTED 压缩断崖。
#
# 用法：
#   bash .agents/skills/herdr-teamwork/scripts/agent-context.sh [role_name_or_pane_id] [--all] [--json]

set -euo pipefail

TARGET_FILTER=""
OUTPUT_JSON=0
ALL_WORKSPACES=0

for arg in "$@"; do
  case "$arg" in
    --json) OUTPUT_JSON=1 ;;
    --all|-a) ALL_WORKSPACES=1 ;;
    -h|--help)
      echo "Usage: bash scripts/agent-context.sh [role_name_or_pane_id] [--all] [--json]"
      exit 0
      ;;
    *) TARGET_FILTER="$arg" ;;
  esac
done

ENV_FILE=".agents/environment.json"
PI_MODELS_FILE="${HOME}/.pi/agent/models.json"
AGY_SETTINGS_FILE="${HOME}/.gemini/antigravity-cli/settings.json"
TAIL_BYTES=262144
MIN_FLOOR_TOKENS=16000

# 提取最近 8 次 LLM 调用中的峰值 (作为 prev_peak) 与最后一次值 (作为 curr)，确保同一回合内压缩后连续调多次工具也能稳定捕获 +JUST_COMPACTED 断崖
extract_last_two_numbers() {
  local file="$1"
  local jq_expr="$2"
  tail -c "$TAIL_BYTES" "$file" 2>/dev/null \
    | grep -E '^\{.*\}$' \
    | jq -r "$jq_expr" 2>/dev/null \
    | awk 'NF && $1 ~ /^[0-9]+$/ && $1 > 0' \
    | tail -n 8 \
    | awk '
        { vals[NR] = $1 }
        END {
          if (NR == 1) {
            print vals[1]
          } else if (NR >= 2) {
            max_prev = 0
            for (i = 1; i < NR; i++) {
              if (vals[i] > max_prev) max_prev = vals[i]
            }
            print max_prev
            print vals[NR]
          }
        }
      ' || true
}

# 根据 Tier (S / A / B) × 有效窗口 (window) × 思考等级 (thinking) 计算 ARMED 与 DANGER 阈值
# 核心「70% / 60% / 50% 黄金比例法则」（以 medium 思考为基准）：
# - Tier S (高智商旗舰)：70% ARMED (趁空闲压) / 80% DANGER (派活前必压)
# - Tier A (主力编码模型)：60% ARMED (趁空闲压) / 72% DANGER (派活前必压)
# - Tier B (中等参数开源/轻量)：50% ARMED (趁空闲压) / 62% DANGER (派活前必压)，且为防超大物理窗口下注意力稀释，设置 85k~100k 智力上限封顶
# - 思考等级微调：high/xhigh 思考 +5% 空间；low/off 思考 -8% 空间
calc_thresholds() {
  local tier="$1"
  local window="$2"
  local thinking="$3"
  local armed_pct=60
  local danger_pct=72
  local cap=200000

  case "$tier" in
    S|s)
      armed_pct=70
      danger_pct=80
      cap=280000
      ;;
    A|a)
      armed_pct=60
      danger_pct=72
      cap=190000
      ;;
    B|b)
      armed_pct=50
      danger_pct=62
      cap=90000
      ;;
    *)
      armed_pct=60
      danger_pct=72
      cap=190000
      ;;
  esac

  local think_lower
  think_lower=$(printf '%s' "$thinking" | tr '[:upper:]' '[:lower:]')
  case "$think_lower" in
    high|xhigh|max)
      armed_pct=$(( armed_pct + 5 ))
      danger_pct=$(( danger_pct + 5 ))
      cap=$(( cap * 110 / 100 ))
      ;;
    low|off|none|minimal)
      armed_pct=$(( armed_pct - 8 ))
      danger_pct=$(( danger_pct - 7 ))
      cap=$(( cap * 82 / 100 ))
      ;;
    *)
      # medium: keep baseline
      ;;
  esac

  local armed=$(( window * armed_pct / 100 ))
  if [ "$cap" -lt "$armed" ]; then
    armed="$cap"
  fi
  if [ "$armed" -lt "$MIN_FLOOR_TOKENS" ]; then
    armed="$MIN_FLOOR_TOKENS"
  fi

  local danger=$(( window * danger_pct / 100 ))
  local danger_cap=$(( cap + 25000 ))
  local danger_hard=$(( window * 88 / 100 ))
  [ "$danger_cap" -lt "$danger" ] && danger="$danger_cap"
  [ "$danger_hard" -lt "$danger" ] && danger="$danger_hard"
  [ "$danger" -le "$armed" ] && danger=$(( armed + 15000 ))

  echo "${armed} ${danger}"
}

# 获取 Herdr 活跃 Agent 列表（支持通过 HERDR_AGENT_LIST_JSON 注入测试数据）
if [ -n "${HERDR_AGENT_LIST_JSON:-}" ]; then
  AGENTS_RAW="$HERDR_AGENT_LIST_JSON"
elif command -v herdr >/dev/null 2>&1 && [ "${HERDR_ENV:-0}" = "1" ]; then
  AGENTS_RAW=$(herdr agent list 2>/dev/null || echo '{"result":{"agents":[]}}')
else
  AGENTS_RAW='{"result":{"agents":[]}}'
fi

CURRENT_WS="${HERDR_WORKSPACE_ID:-}"
CURRENT_CWD="$PWD"

# 提取目标角色列表（默认过滤当前工作区；支持已命名角色及未命名的活跃 Agent 窗格）
AGENT_ROWS=$(echo "$AGENTS_RAW" | jq -c \
  --arg filter "$TARGET_FILTER" \
  --arg ws "$CURRENT_WS" \
  --arg cwd "$CURRENT_CWD" \
  --argjson all "$ALL_WORKSPACES" '
  (.result.agents // [])[]
  | select(.name != "bootstrap")
  | select(
      $all == 1
      or $filter != ""
      or ($ws != "" and .workspace_id == $ws)
      or ($ws == "" and (.cwd == $cwd or .foreground_cwd == $cwd))
    )
  | (.name // "\(.agent // .kind // "agent")@\(.pane_id)") as $display_name
  | select($filter == "" or .name == $filter or .pane_id == $filter or $display_name == $filter)
  | {
      name: $display_name,
      raw_name: (.name // ""),
      pane_id: (.pane_id // "-"),
      workspace_id: (.workspace_id // "-"),
      kind: (.kind // .agent // "unknown"),
      status: (
        if (.status | type) == "string" then .status
        elif (.agent_status | type) == "string" then .agent_status
        elif (.agent_status | type) == "object" then (.agent_status.value // "unknown")
        else "unknown"
        end
      ),
      session_kind: (.agent_session.kind // "id"),
      session_val: (.agent_session.value // ""),
      raw_json: (. | tostring)
    }
')

RESULTS_JSON="[]"

if [ -z "$AGENT_ROWS" ]; then
  if [ "$OUTPUT_JSON" -eq 1 ]; then
    echo "[]"
  else
    echo "No matching active Herdr agents found in workspace."
  fi
  exit 0
fi

while IFS= read -r row; do
  [ -z "$row" ] && continue
  ROLE_NAME=$(echo "$row" | jq -r '.name')
  RAW_ROLE_NAME=$(echo "$row" | jq -r '.raw_name')
  PANE_ID=$(echo "$row" | jq -r '.pane_id')
  KIND=$(echo "$row" | jq -r '.kind')
  AGENT_STATUS=$(echo "$row" | jq -r '.status')
  SESSION_KIND=$(echo "$row" | jq -r '.session_kind')
  SESSION_VAL=$(echo "$row" | jq -r '.session_val')

  # 1. 从 .agents/environment.json 读取预设档位、模型、思考等级、窗口与显式阈值
  CONF_TIER=""
  CONF_MODEL=""
  CONF_THINK=""
  CONF_WIN=200000
  CONF_ARMED=0
  CONF_DANGER=0
  LOOKUP_ROLE="${RAW_ROLE_NAME:-$ROLE_NAME}"
  if [ -f "$ENV_FILE" ]; then
    CONF_MODEL=$(jq -r --arg r "$LOOKUP_ROLE" '.roles[$r].model // ""' "$ENV_FILE" 2>/dev/null || echo "")
    CONF_THINK=$(jq -r --arg r "$LOOKUP_ROLE" '.roles[$r].thinking // ""' "$ENV_FILE" 2>/dev/null || echo "")
    CONF_TIER=$(jq -r --arg r "$LOOKUP_ROLE" '
      .context_monitor.role_overrides[$r].tier
      // .roles[$r].context_tier
      // .context_monitor.default_profile.tier
      // ""
    ' "$ENV_FILE" 2>/dev/null || echo "")
    CONF_WIN=$(jq -r --arg r "$LOOKUP_ROLE" '
      .context_monitor.role_overrides[$r].window_tokens
      // .roles[$r].window_tokens
      // .context_monitor.default_profile.window_tokens
      // 200000
    ' "$ENV_FILE" 2>/dev/null || echo "200000")
    CONF_ARMED=$(jq -r --arg r "$LOOKUP_ROLE" '
      .context_monitor.role_overrides[$r].armed_tokens
      // .context_monitor.default_profile.armed_tokens
      // 0
    ' "$ENV_FILE" 2>/dev/null || echo "0")
    CONF_DANGER=$(jq -r --arg r "$LOOKUP_ROLE" '
      .context_monitor.role_overrides[$r].danger_tokens
      // .context_monitor.default_profile.danger_tokens
      // 0
    ' "$ENV_FILE" 2>/dev/null || echo "0")
  fi

  CURR_TOKENS=0
  PREV_TOKENS=0
  DETECTED_WIN=0
  DETECTED_MODEL=""
  DETECTED_THINK=""
  DETECTED_PROVIDER=""
  SOURCE_CHANNEL="unattributed"

  # 提取纯会话 ID（若 session_val 是路径则取文件名）用于查 statusline 缓存
  SESSION_BASENAME=$(basename "${SESSION_VAL:-}" .jsonl 2>/dev/null || true)

  # 2. 通道一：优先检查 herdr-agent-usage 的 statusline 实时缓存
  STATUSLINE_CACHE="${HOME}/.cache/herdr-agent-usage/statusline/${SESSION_BASENAME}.json"
  if [ -n "$SESSION_BASENAME" ] && [ -f "$STATUSLINE_CACHE" ]; then
    CURR_TOKENS=$(jq -r '
      (.context_window.current_usage.input_tokens // 0) +
      (.context_window.current_usage.cache_creation_input_tokens // 0) +
      (.context_window.current_usage.cache_read_input_tokens // 0)
    ' "$STATUSLINE_CACHE" 2>/dev/null || echo 0)
    DETECTED_WIN=$(jq -r '.context_window.context_window_size // 0' "$STATUSLINE_CACHE" 2>/dev/null || echo 0)
    DETECTED_MODEL=$(jq -r '.model.id // .model.display_name // ""' "$STATUSLINE_CACHE" 2>/dev/null || echo "")
    if [ "${CURR_TOKENS:-0}" -gt 0 ]; then
      SOURCE_CHANNEL="plugin_statusline"
    fi
  fi

  # 3. 通道二：严格按 SESSION_VAL 定位本地 .jsonl 会话文件（支持 kind=="path" 直读与 kind=="id" 查找）
  TRANSCRIPT_FILE=""
  if [ -n "$SESSION_VAL" ]; then
    if [ "$SESSION_KIND" = "path" ] || [ -f "$SESSION_VAL" ]; then
      [ -f "$SESSION_VAL" ] && TRANSCRIPT_FILE="$SESSION_VAL"
    else
      case "$KIND" in
        agy|antigravity)
          CANDIDATE="${HOME}/.gemini/antigravity-cli/brain/${SESSION_VAL}/.system_generated/logs/transcript.jsonl"
          [ -f "$CANDIDATE" ] && TRANSCRIPT_FILE="$CANDIDATE"
          ;;
        claude|claude-code)
          TRANSCRIPT_FILE=$(find "${HOME}/.claude/projects" -maxdepth 3 -name "${SESSION_VAL}.jsonl" -print -quit 2>/dev/null || true)
          ;;
        codex)
          TRANSCRIPT_FILE=$(find "${HOME}/.codex/sessions" -maxdepth 4 -name "*${SESSION_VAL}*.jsonl" -print -quit 2>/dev/null || true)
          ;;
        pi|omp)
          TRANSCRIPT_FILE=$(find "${HOME}/.pi/agent/sessions" "${HOME}/.omp/agent/sessions" -maxdepth 3 -name "*${SESSION_VAL}*.jsonl" -print -quit 2>/dev/null || true)
          ;;
      esac
    fi
  fi

  if [ -n "$TRANSCRIPT_FILE" ] && [ -f "$TRANSCRIPT_FILE" ]; then
    NUMS=""
    case "$KIND" in
      agy|antigravity)
        NUMS=$(extract_last_two_numbers "$TRANSCRIPT_FILE" '((.input_tokens // 0) + (.cache_read_tokens // 0))')
        # 1) 优先从 Herdr 窗格底部状态栏实时读取 Agy 当前模型与思考等级（如 "Gemini 4 Argon · medium"）
        if [ -n "$PANE_ID" ] && [ "$PANE_ID" != "-" ] && command -v herdr >/dev/null 2>&1 && [ "${HERDR_ENV:-0}" = "1" ]; then
          AGY_BAR=$(herdr pane read "$PANE_ID" --lines 6 2>/dev/null | grep -oE '[A-Za-z0-9._ -]+ · (off|none|low|medium|high|xhigh)' | tail -n 1 || true)
          if [ -n "$AGY_BAR" ]; then
            DETECTED_MODEL=$(echo "$AGY_BAR" | awk -F' · ' '{print $1}' | sed -E 's/^.*  +//;s/^[[:space:]]*//;s/[[:space:]]*$//')
            DETECTED_THINK=$(echo "$AGY_BAR" | awk -F' · ' '{print $2}' | tr -d '[:space:]')
          fi
        fi
        # 2) 兜底：从 transcript.jsonl 的 <USER_SETTINGS_CHANGE> 或 ~/.gemini/antigravity-cli/settings.json 提取
        if [ -z "$DETECTED_MODEL" ]; then
          AGY_CHANGE=$(tail -c "$TAIL_BYTES" "$TRANSCRIPT_FILE" 2>/dev/null | grep -oE 'Model Selection` from [^)]+\) to [A-Za-z0-9._ -]+ \([A-Za-z]+\)' | tail -n 1 || true)
          if [ -n "$AGY_CHANGE" ]; then
            DETECTED_MODEL=$(echo "$AGY_CHANGE" | sed -E 's/.* to (.*) \([^)]+\)/\1/')
            DETECTED_THINK=$(echo "$AGY_CHANGE" | sed -E 's/.*\(([^)]+)\)/\1/' | tr '[:upper:]' '[:lower:]')
          elif [ -f "$AGY_SETTINGS_FILE" ]; then
            RAW_AGY_SETTING=$(jq -r '.model // ""' "$AGY_SETTINGS_FILE" 2>/dev/null || echo "")
            if [ -n "$RAW_AGY_SETTING" ]; then
              DETECTED_MODEL=$(echo "$RAW_AGY_SETTING" | sed -E 's/ *\([^)]+\)$//')
              DETECTED_THINK=$(echo "$RAW_AGY_SETTING" | grep -oE '\([^)]+\)$' | tr -d '()' | tr '[:upper:]' '[:lower:]' || true)
            fi
          fi
        fi
        # Agy 客户端的会话管理器在 ~256k (262,144 Tokens) 处触发强制自动压缩
        if [ "${DETECTED_WIN:-0}" -le 0 ]; then
          DETECTED_WIN=262144
        fi
        ;;
      claude|claude-code)
        NUMS=$(extract_last_two_numbers "$TRANSCRIPT_FILE" 'select(.message.usage != null) | ((.message.usage.input_tokens // 0) + (.message.usage.cache_creation_input_tokens // 0) + (.message.usage.cache_read_input_tokens // 0))')
        CLAUDE_MODEL=$(tail -c "$TAIL_BYTES" "$TRANSCRIPT_FILE" 2>/dev/null | grep -E '^\{.*\}$' | jq -r 'select(.message.model != null) | .message.model' 2>/dev/null | tail -n 1 || true)
        [ -n "$CLAUDE_MODEL" ] && DETECTED_MODEL="$CLAUDE_MODEL"
        if [ -z "$DETECTED_THINK" ] && [ -f "${HOME}/.claude/settings.json" ]; then
          DETECTED_THINK=$(jq -r '.effortLevel // ""' "${HOME}/.claude/settings.json" 2>/dev/null || echo "")
        fi
        ;;
      codex)
        NUMS=$(extract_last_two_numbers "$TRANSCRIPT_FILE" 'select(.type == "event_msg" and .payload.type == "token_count") | (.payload.info.last_token_usage.total_tokens // 0)')
        CODEX_WIN=$(tail -c "$TAIL_BYTES" "$TRANSCRIPT_FILE" 2>/dev/null | grep -E '^\{.*\}$' | jq -r 'select(.type == "event_msg" and .payload.type == "token_count") | (.payload.info.model_context_window // 0)' 2>/dev/null | awk '$1 > 0' | tail -n 1 || true)
        CODEX_META=$(tail -c "$TAIL_BYTES" "$TRANSCRIPT_FILE" 2>/dev/null | grep -E '^\{.*\}$' | jq -r 'select(.type == "turn_context") | "\(.payload.model // "")\t\(.payload.effort // .payload.collaboration_mode.settings.reasoning_effort // "")"' 2>/dev/null | awk 'NF' | tail -n 1 || true)
        [ -n "${CODEX_WIN:-}" ] && [ "${CODEX_WIN:-0}" -gt 0 ] && DETECTED_WIN="$CODEX_WIN"
        if [ -n "$CODEX_META" ]; then
          DETECTED_MODEL=$(echo "$CODEX_META" | cut -f1)
          DETECTED_THINK=$(echo "$CODEX_META" | cut -f2)
        fi
        ;;
      pi|omp)
        NUMS=$(extract_last_two_numbers "$TRANSCRIPT_FILE" 'select(.type == "message" and .message.role == "assistant") | (.message.usage.totalTokens // ((.message.usage.input // 0) + (.message.usage.output // 0) + (.message.usage.cacheRead // 0) + (.message.usage.cacheWrite // 0)))')
        PI_META=$(tail -c "$TAIL_BYTES" "$TRANSCRIPT_FILE" 2>/dev/null | grep -E '^\{.*\}$' | jq -r 'select(.type == "model_change" or (.type == "message" and .message.role == "assistant" and .message.model != null)) | "\(.provider // .message.provider // "")\t\(.modelId // .message.model // "")"' 2>/dev/null | tail -n 1 || true)
        PI_THINK=$(tail -c "$TAIL_BYTES" "$TRANSCRIPT_FILE" 2>/dev/null | grep -E '^\{.*\}$' | jq -r 'select(.type == "thinking_level_change") | (.thinkingLevel // "")' 2>/dev/null | awk 'NF' | tail -n 1 || true)
        if [ -n "$PI_META" ]; then
          DETECTED_PROVIDER=$(echo "$PI_META" | cut -f1)
          DETECTED_MODEL=$(echo "$PI_META" | cut -f2)
        fi
        [ -n "$PI_THINK" ] && DETECTED_THINK="$PI_THINK"
        # 若存在 ~/.pi/agent/models.json，自动查询该模型的真实 contextWindow
        if [ -n "$DETECTED_MODEL" ] && [ -f "$PI_MODELS_FILE" ]; then
          PI_WIN=$(jq -r --arg p "$DETECTED_PROVIDER" --arg m "$DETECTED_MODEL" '
            [
              (if $p != "" then (.providers[$p].models // [])[] else (.providers // {} | .[].models // [])[] end)
              | select(.id == $m or .name == $m)
              | .contextWindow
            ] | first // 0
          ' "$PI_MODELS_FILE" 2>/dev/null || echo 0)
          [ -n "${PI_WIN:-}" ] && [ "${PI_WIN:-0}" -gt 0 ] && DETECTED_WIN="$PI_WIN"
        fi
        ;;
    esac

    if [ -n "$NUMS" ]; then
      LINE_COUNT=$(echo "$NUMS" | wc -l | tr -d ' ')
      if [ "$LINE_COUNT" -ge 2 ]; then
        PREV_TOKENS=$(echo "$NUMS" | head -n 1)
        LAST_JSONL_TOKENS=$(echo "$NUMS" | tail -n 1)
      else
        PREV_TOKENS=0
        LAST_JSONL_TOKENS=$(echo "$NUMS" | tail -n 1)
      fi
      if [ "${CURR_TOKENS:-0}" -le 0 ]; then
        CURR_TOKENS="$LAST_JSONL_TOKENS"
        SOURCE_CHANNEL="jsonl_tail_256k"
      fi
    fi
  fi

  # 3.5 通道一补充：若上述未命中但 herdr agent list 中包含 herdr-agent-usage 注入的 "Context: [...] XX%" 元数据，则按百分比换算
  if [ "${CURR_TOKENS:-0}" -le 0 ]; then
    META_PCT=$(echo "$row" | jq -r '.raw_json' | grep -oE 'Context: \[[█░]+\] [0-9]{1,3}%' | grep -oE '[0-9]{1,3}%' | tr -d '%' | head -n 1 || true)
    if [ -n "${META_PCT:-}" ] && [ "${META_PCT:-0}" -gt 0 ]; then
      CURR_TOKENS=$(( CONF_WIN * META_PCT / 100 ))
      SOURCE_CHANNEL="plugin_metadata"
    fi
  fi

  [ -z "$DETECTED_MODEL" ] && [ -n "$CONF_MODEL" ] && DETECTED_MODEL="$CONF_MODEL"
  [ -z "$DETECTED_THINK" ] && [ -n "$CONF_THINK" ] && DETECTED_THINK="$CONF_THINK"
  [ -z "$DETECTED_THINK" ] && DETECTED_THINK="medium"

  # 4. 若未在 .agents/environment.json 显式配置 Tier，则按宏观原则自动推断默认档位
  if [ -z "$CONF_TIER" ]; then
    PROV_LOWER=$(printf '%s' "$DETECTED_PROVIDER" | tr '[:upper:]' '[:lower:]')
    MODEL_LOWER=$(printf '%s' "$DETECTED_MODEL" | tr '[:upper:]' '[:lower:]')
    case "$PROV_LOWER" in
      xinference|ollama|vllm|lmstudio|llamacpp|local*)
        CONF_TIER="B"
        ;;
      *)
        case "$MODEL_LOWER" in
          *argon*|*opus*|*pro*|*ultra*)
            CONF_TIER="S"
            ;;
          *-mini*|*" mini"*|*haiku*|*lite*|*nano*)
            CONF_TIER="B"
            ;;
          *)
            CONF_TIER="A"
            ;;
        esac
        ;;
    esac
  fi

  # 5. 确定最终生效的物理窗口与 ARMED / DANGER 阈值（融合 Tier × Window × Thinking Level）
  EFFECTIVE_WIN="$CONF_WIN"
  if [ "${DETECTED_WIN:-0}" -gt 0 ]; then
    EFFECTIVE_WIN="$DETECTED_WIN"
  fi

  read -r CALC_ARMED CALC_DANGER <<< "$(calc_thresholds "$CONF_TIER" "$EFFECTIVE_WIN" "$DETECTED_THINK")"
  ARMED_TOKENS="$CALC_ARMED"
  DANGER_TOKENS="$CALC_DANGER"
  [ "${CONF_ARMED:-0}" -gt 0 ] && ARMED_TOKENS="$CONF_ARMED"
  [ "${CONF_DANGER:-0}" -gt 0 ] && DANGER_TOKENS="$CONF_DANGER"

  # 6. 判定状态与压缩断崖 (curr_tokens < prev_tokens * 0.6)
  JUST_COMPACTED="false"
  if [ "${PREV_TOKENS:-0}" -ge 30000 ] && [ "${CURR_TOKENS:-0}" -gt 0 ]; then
    DROP_LIMIT=$(( PREV_TOKENS * 60 / 100 ))
    if [ "$CURR_TOKENS" -lt "$DROP_LIMIT" ]; then
      JUST_COMPACTED="true"
    fi
  fi

  if [ "$SOURCE_CHANNEL" = "unattributed" ] || [ "${CURR_TOKENS:-0}" -le 0 ]; then
    WATERMARK_STATE="UNATTRIBUTED"
    ACTION_HINT="Wait for first turn or verify session attribution"
  elif [ "$CURR_TOKENS" -ge "$DANGER_TOKENS" ]; then
    WATERMARK_STATE="DANGER"
    ACTION_HINT="MUST compact BEFORE next prompt"
  elif [ "$CURR_TOKENS" -ge "$ARMED_TOKENS" ]; then
    WATERMARK_STATE="ARMED"
    ACTION_HINT="Compact at current/next idle boundary"
  else
    WATERMARK_STATE="OK"
    ACTION_HINT="Safe to dispatch"
  fi

  if [ "$JUST_COMPACTED" = "true" ]; then
    WATERMARK_STATE="${WATERMARK_STATE}+JUST_COMPACTED"
    ACTION_HINT="Prepend role reload (read roles/${LOOKUP_ROLE}.md) on next prompt!"
  fi

  PCT=0
  if [ "$EFFECTIVE_WIN" -gt 0 ] && [ "$CURR_TOKENS" -gt 0 ]; then
    PCT=$(( CURR_TOKENS * 100 / EFFECTIVE_WIN ))
  fi

  RESULTS_JSON=$(echo "$RESULTS_JSON" | jq -c \
    --arg role "$ROLE_NAME" \
    --arg pane "$PANE_ID" \
    --arg kind "$KIND" \
    --arg model "${DETECTED_MODEL:--}" \
    --arg think "${DETECTED_THINK:--}" \
    --arg status "$AGENT_STATUS" \
    --arg channel "$SOURCE_CHANNEL" \
    --arg tier "$CONF_TIER" \
    --argjson curr "${CURR_TOKENS:-0}" \
    --argjson prev "${PREV_TOKENS:-0}" \
    --argjson win "$EFFECTIVE_WIN" \
    --argjson pct "$PCT" \
    --argjson armed "$ARMED_TOKENS" \
    --argjson danger "$DANGER_TOKENS" \
    --arg wm_state "$WATERMARK_STATE" \
    --arg hint "$ACTION_HINT" \
    '. + [{
      role: $role,
      pane_id: $pane,
      harness: $kind,
      model: $model,
      thinking: $think,
      agent_status: $status,
      channel: $channel,
      tier: $tier,
      curr_tokens: $curr,
      prev_tokens: $prev,
      window_tokens: $win,
      usage_pct: $pct,
      armed_tokens: $armed,
      danger_tokens: $danger,
      watermark_state: $wm_state,
      action_hint: $hint
    }]')
done <<< "$AGENT_ROWS"

if [ "$OUTPUT_JSON" -eq 1 ]; then
  echo "$RESULTS_JSON" | jq .
else
  printf "%-18s %-7s %-7s %-18s %-7s %-7s %-4s %-23s %-16s %s\n" \
    "ROLE" "PANE" "HARNESS" "MODEL" "THINK" "STATUS" "TIER" "TOKENS(CURR/ARM/WIN)" "WATERMARK_STATE" "ACTION_HINT"
  printf "%-18s %-7s %-7s %-18s %-7s %-7s %-4s %-23s %-16s %s\n" \
    "------------------" "-------" "-------" "------------------" "-------" "-------" "----" "-----------------------" "----------------" "------------------------------"
  echo "$RESULTS_JSON" | jq -r '.[] | [
    .role,
    .pane_id,
    .harness,
    .model,
    .thinking,
    .agent_status,
    .tier,
    "\(.curr_tokens / 1000 | floor)k/\(.armed_tokens / 1000 | floor)k/\(if .window_tokens >= 1000000 then "\(.window_tokens / 1000000 | floor)M" else "\(.window_tokens / 1000 | floor)k" end)(\(.usage_pct)%)",
    .watermark_state,
    .action_hint
  ] | @tsv' | while IFS=$'\t' read -r r p h m th s t tok wm hint; do
    printf "%-18s %-7s %-7s %-18s %-7s %-7s %-4s %-23s %-16s %s\n" "$r" "$p" "$h" "$m" "$th" "$s" "$t" "$tok" "$wm" "$hint"
  done
fi
