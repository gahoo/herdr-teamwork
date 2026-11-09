#!/usr/bin/env python3
"""
scripts/agent-context.py
跨 Harness 多 Agent 上下文水位探针 (Dual-Channel Context Watermark Probe)

设计准则：
1. 双通道感知：优先读取 herdr-agent-usage 状态行缓存/Metadata；兜底采用 256KB 有界尾部倒扫 (tail -c 262144) + 终端状态栏嗅探。
2. 严格会话归属 (Strict Attribution) + 失败闭合 (Fail-Closed)：仅按 herdr agent list 的 agent_session.value 精确匹配会话文件；未落盘时输出 UNATTRIBUTED，绝不伪造 0%。
3. 三维动态阈值 (Tier S/A/B × Window Size × Thinking Level)：自动探测模型、物理窗口与思考等级 (off/low/medium/high/xhigh)，动态计算 ARMED 与 DANGER 阈值并检测 JUST_COMPACTED 压缩断崖。
4. 安全角色映射：base_role 安全映射（优先最长前缀匹配，兜底剥离 -[0-9].* 后缀）。
5. 自动快照同步：每次运行探测后，增量同步（Upsert）至 .agents/session.json。
"""

import argparse
import glob
import importlib.util
import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple


ENV_FILE = ".agents/environment.json"
PI_MODELS_FILE = os.path.expanduser("~/.pi/agent/models.json")
AGY_SETTINGS_FILE = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
CLAUDE_SETTINGS_FILE = os.path.expanduser("~/.claude/settings.json")
TAIL_BYTES = 262144
MIN_FLOOR_TOKENS = 16000


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def get_project_root(cwd: Optional[str] = None) -> str:
    """获取项目主工作区根目录（即使在 .worktrees/<id> 子工作区内执行也能还原主根目录）。"""
    cur = os.path.abspath(cwd or os.getcwd())
    m = re.match(r"^(.*?)/\.worktrees/[^/]+", cur)
    if m:
        return m.group(1)
    if os.path.islink(os.path.join(cur, ".agents")):
        return os.path.dirname(os.path.realpath(os.path.join(cur, ".agents")))
    return cur


def load_json(filepath: str) -> Optional[Any]:
    if not os.path.isfile(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_base_role(name: str, roles_dict: Optional[Dict[str, Any]] = None) -> str:
    """
    base_role 安全映射：
    1. 支持安全剥离测试/临时前缀 (dummy-, test-, tmp-, mock-)；
    2. 先精确匹配 .agents/environment.json 中 .roles 的 key；
    3. 若未命中则匹配 .roles 中以 "<role>-" 为前缀的标准角色名（最长前缀优先）；
    4. 兜底剥离 -[0-9].* 后缀（例如 reviewer-lead-001 -> reviewer-lead, coding-001 -> coding）。
    """
    if not name:
        return ""
    DEFAULT_ROLES = (
        "planner", "explorer", "dispatcher", "tdd", "coding", "ops",
        "debugger", "security-redteam", "e2e", "reviewer-lead",
        "reviewer-quality", "reviewer-arch", "reviewer-perf",
        "reviewer-security", "reviewer-ux", "reflector",
    )
    known_roles = list(roles_dict.keys()) if roles_dict else list(DEFAULT_ROLES)
    cleaned_name = re.sub(r"^(?:dummy|test|tmp|mock)-", "", name)
    if cleaned_name in known_roles:
        return cleaned_name
    matches = [r for r in known_roles if cleaned_name.startswith(f"{r}-")]
    if matches:
        matches.sort(key=len, reverse=True)
        return matches[0]

    return re.sub(r"-[0-9].*$", "", cleaned_name)


def calc_thresholds(tier: str, window: int, thinking: str) -> Tuple[int, int]:
    """
    根据 Tier (S / A / B) × 有效窗口 (window) × 思考等级 (thinking) 计算 ARMED 与 DANGER 阈值。
    """
    tier_upper = (tier or "A").upper()
    if tier_upper == "S":
        armed_pct = 70
        danger_pct = 80
        cap = 280000
    elif tier_upper == "B":
        armed_pct = 50
        danger_pct = 62
        cap = 90000
    else:  # Tier A or default
        armed_pct = 60
        danger_pct = 72
        cap = 190000

    think_lower = (thinking or "medium").strip().lower()
    if think_lower in ("high", "xhigh", "max"):
        armed_pct += 5
        danger_pct += 5
        cap = cap * 110 // 100
    elif think_lower in ("low", "off", "none", "minimal"):
        armed_pct -= 8
        danger_pct -= 7
        cap = cap * 82 // 100

    armed = window * armed_pct // 100
    if armed > cap:
        armed = cap
    if armed < MIN_FLOOR_TOKENS:
        armed = MIN_FLOOR_TOKENS

    danger = window * danger_pct // 100
    danger_cap = cap + 25000
    danger_hard = window * 88 // 100
    danger = min(danger, danger_cap, danger_hard)
    if danger <= armed:
        danger = armed + 15000

    return armed, danger


def extract_clean_session_id(session_val: str) -> str:
    """从 session_val 中提取纯净的会话 ID（如将 pi 的 .../2026-11-09T..._01a1bdcf-....jsonl 提取为 01a1bdcf-...）。"""
    if not session_val:
        return ""
    val = session_val.strip()
    if "/" in val or val.endswith(".jsonl"):
        stem = os.path.splitext(os.path.basename(val))[0]
        if "_" in stem:
            return stem.split("_", 1)[1]
        return stem
    return val


def read_tail_bytes(filepath: str, nbytes: int = TAIL_BYTES) -> bytes:
    try:
        with open(filepath, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            seek_pos = max(0, size - nbytes)
            f.seek(seek_pos, os.SEEK_SET)
            return f.read()
    except Exception:
        return b""


def find_transcript_file(kind: str, session_kind: str, session_val: str) -> Optional[str]:
    if not session_val:
        return None

    if session_kind == "path" or os.path.isfile(session_val):
        return session_val if os.path.isfile(session_val) else None

    kind_lower = (kind or "").lower()
    if kind_lower in ("agy", "antigravity"):
        candidate = os.path.expanduser(
            f"~/.gemini/antigravity-cli/brain/{session_val}/.system_generated/logs/transcript.jsonl"
        )
        if os.path.isfile(candidate):
            return candidate
    elif kind_lower in ("claude", "claude-code"):
        base_dir = os.path.expanduser("~/.claude/projects")
        matches = glob.glob(f"{base_dir}/**/{session_val}.jsonl", recursive=True)
        if matches:
            return matches[0]
    elif kind_lower == "codex":
        base_dir = os.path.expanduser("~/.codex/sessions")
        matches = glob.glob(f"{base_dir}/**/*{session_val}*.jsonl", recursive=True)
        if matches:
            return matches[0]
    elif kind_lower in ("pi", "omp"):
        for root in ("~/.pi/agent/sessions", "~/.omp/agent/sessions"):
            base_dir = os.path.expanduser(root)
            matches = glob.glob(f"{base_dir}/**/*{session_val}*.jsonl", recursive=True)
            if matches:
                return matches[0]

    return None


def probe_agy_pane_bar(pane_id: str) -> Tuple[str, str]:
    """通过 herdr pane read 读取 Agy 底部状态栏模型与思考等级。"""
    if not pane_id or pane_id == "-":
        return "", ""
    try:
        proc = run_cmd(["herdr", "pane", "read", pane_id, "--lines", "6"])
        if proc.returncode == 0 and proc.stdout:
            lines = proc.stdout.splitlines()
            for line in reversed(lines):
                m = re.search(r"([A-Za-z0-9._ -]+)\s*·\s*(off|none|low|medium|high|xhigh)", line)
                if m:
                    model = re.sub(r"^.*? {2,}", "", m.group(1)).strip()
                    think = m.group(2).strip()
                    return model, think
    except Exception:
        pass
    return "", ""


def probe_agent_context(
    target_filter: str = "",
    workspace: Optional[str] = None,
    all_workspaces: bool = False,
    env_file: str = ENV_FILE,
) -> List[Dict[str, Any]]:
    """
    执行跨 Harness 多 Agent 上下文水位与实时元数据探测。
    """
    env_data = load_json(env_file) or {}
    roles_cfg = env_data.get("roles", {})
    context_monitor = env_data.get("context_monitor", {})
    role_overrides = context_monitor.get("role_overrides", {})
    default_profile = context_monitor.get("default_profile", {})

    # 1. 获取 Herdr 活跃 Agent 列表
    env_json = os.environ.get("HERDR_AGENT_LIST_JSON")
    raw_agents: List[Dict[str, Any]] = []
    if env_json:
        try:
            raw_agents = json.loads(env_json).get("result", {}).get("agents", [])
        except Exception:
            raw_agents = []
    else:
        try:
            proc = run_cmd(["herdr", "agent", "list"])
            if proc.returncode == 0 and proc.stdout:
                raw_agents = json.loads(proc.stdout).get("result", {}).get("agents", [])
        except Exception:
            raw_agents = []

    current_ws = workspace or os.environ.get("HERDR_WORKSPACE_ID", "")
    current_cwd = os.getcwd()
    project_root = get_project_root(current_cwd)

    results: List[Dict[str, Any]] = []

    for agent in raw_agents:
        raw_name = agent.get("name") or ""
        if raw_name == "bootstrap":
            continue

        pane_id = agent.get("pane_id") or "-"
        ws_id = agent.get("workspace_id") or "-"
        tab_id = agent.get("tab_id") or "-"
        cwd = agent.get("cwd") or agent.get("foreground_cwd") or ""
        kind = agent.get("kind") or agent.get("agent") or "unknown"

        display_name = raw_name if raw_name else f"{kind}@{pane_id}"

        # 工作区过滤：
        # - 默认：仅当前 HERDR_WORKSPACE_ID（或当前 cwd）
        # - --all (-a)：当前项目主工作区及全部并发子 Worktree (.worktrees/*)，自动排除 Herdr 中其他无关项目的工作区
        if not target_filter:
            if all_workspaces:
                if cwd != project_root and not cwd.startswith(project_root + "/"):
                    continue
            elif current_ws:
                if ws_id != current_ws:
                    continue
            else:
                if cwd != current_cwd and agent.get("foreground_cwd") != current_cwd:
                    continue

        # 目标名称/窗格过滤
        if target_filter:
            if target_filter not in (raw_name, pane_id, display_name):
                continue

        # 状态
        raw_status = agent.get("status")
        if isinstance(raw_status, str):
            agent_status = raw_status
        else:
            raw_ag_status = agent.get("agent_status")
            if isinstance(raw_ag_status, str):
                agent_status = raw_ag_status
            elif isinstance(raw_ag_status, dict):
                agent_status = raw_ag_status.get("value", "unknown")
            else:
                agent_status = "unknown"

        session_obj = agent.get("agent_session", {})
        session_kind = session_obj.get("kind", "id")
        session_val = session_obj.get("value", "")

        # 角色与配置读取
        lookup_role = raw_name if raw_name else display_name
        base_role = get_base_role(lookup_role, roles_cfg)
        role_key = base_role if base_role in roles_cfg else lookup_role

        conf_role = roles_cfg.get(role_key, {})
        conf_model = conf_role.get("model", "")
        conf_think = conf_role.get("thinking", "")
        conf_override = role_overrides.get(role_key, {})

        conf_tier = (
            conf_override.get("tier")
            or conf_role.get("context_tier")
            or default_profile.get("tier")
            or ""
        )
        conf_win = (
            conf_override.get("window_tokens")
            or conf_role.get("window_tokens")
            or default_profile.get("window_tokens")
            or 200000
        )
        conf_armed = conf_override.get("armed_tokens") or default_profile.get("armed_tokens") or 0
        conf_danger = conf_override.get("danger_tokens") or default_profile.get("danger_tokens") or 0

        curr_tokens = 0
        prev_tokens = 0
        detected_win = 0
        detected_model = ""
        detected_think = ""
        detected_provider = ""
        source_channel = "unattributed"

        session_basename = extract_clean_session_id(session_val) if session_val else ""

        # 通道一：herdr-agent-usage 的 statusline 实时缓存
        statusline_cache = (
            os.path.expanduser(f"~/.cache/herdr-agent-usage/statusline/{session_basename}.json")
            if session_basename
            else ""
        )
        cache_data = load_json(statusline_cache)
        if cache_data:
            cw = cache_data.get("context_window", {})
            usage = cw.get("current_usage", {})
            c_inp = usage.get("input_tokens") or 0
            c_creat = usage.get("cache_creation_input_tokens") or 0
            c_read = usage.get("cache_read_input_tokens") or 0
            c_tokens = c_inp + c_creat + c_read

            c_win = cw.get("context_window_size") or 0
            c_model = cache_data.get("model", {}).get("id") or cache_data.get("model", {}).get("display_name") or ""

            if c_tokens > 0:
                curr_tokens = c_tokens
                source_channel = "plugin_statusline"
            if c_win > 0:
                detected_win = c_win
            if c_model:
                detected_model = c_model

        # 通道二：本地 256KB .jsonl 尾部扫描
        transcript_file = find_transcript_file(kind, session_kind, session_val)
        if transcript_file and os.path.isfile(transcript_file):
            tail_content = read_tail_bytes(transcript_file, TAIL_BYTES)
            text = tail_content.decode("utf-8", errors="replace")
            lines = text.splitlines()

            token_series: List[int] = []
            kind_lower = kind.lower()

            if kind_lower in ("agy", "antigravity"):
                for line in lines:
                    line_s = line.strip()
                    if line_s.startswith("{") and line_s.endswith("}"):
                        try:
                            obj = json.loads(line_s)
                            t = (obj.get("input_tokens") or 0) + (obj.get("cache_read_tokens") or 0)
                            if t > 0:
                                token_series.append(t)
                        except Exception:
                            pass

                # 1) 优先从窗格读取状态栏
                bar_model, bar_think = probe_agy_pane_bar(pane_id)
                if bar_model:
                    detected_model = bar_model
                if bar_think:
                    detected_think = bar_think

                # 2) 兜底：从 transcript.jsonl 中抓取 Model Selection
                if not detected_model:
                    matches = re.findall(
                        r"Model Selection` from [^)]+\) to ([A-Za-z0-9._ -]+) \(([A-Za-z]+)\)",
                        text,
                    )
                    if matches:
                        detected_model = matches[-1][0].strip()
                        detected_think = matches[-1][1].strip().lower()
                    elif os.path.isfile(AGY_SETTINGS_FILE):
                        agy_settings = load_json(AGY_SETTINGS_FILE) or {}
                        raw_setting = agy_settings.get("model", "")
                        if raw_setting:
                            detected_model = re.sub(r" *\([^)]+\)$", "", raw_setting)
                            m_think = re.search(r"\(([^)]+)\)$", raw_setting)
                            if m_think:
                                detected_think = m_think.group(1).lower()

                # Agy 客户端在 ~256k 处强制自动压缩
                if detected_win <= 0:
                    detected_win = 262144

            elif kind_lower in ("claude", "claude-code"):
                for line in lines:
                    line_s = line.strip()
                    if line_s.startswith("{") and line_s.endswith("}"):
                        try:
                            obj = json.loads(line_s)
                            msg = obj.get("message")
                            if msg and isinstance(msg, dict):
                                usage = msg.get("usage") or {}
                                t = (
                                    (usage.get("input_tokens") or 0)
                                    + (usage.get("cache_creation_input_tokens") or 0)
                                    + (usage.get("cache_read_input_tokens") or 0)
                                )
                                if t > 0:
                                    token_series.append(t)
                                if msg.get("model"):
                                    detected_model = msg.get("model")
                        except Exception:
                            pass

                if not detected_think and os.path.isfile(CLAUDE_SETTINGS_FILE):
                    c_settings = load_json(CLAUDE_SETTINGS_FILE) or {}
                    detected_think = c_settings.get("effortLevel", "")

            elif kind_lower == "codex":
                for line in lines:
                    line_s = line.strip()
                    if line_s.startswith("{") and line_s.endswith("}"):
                        try:
                            obj = json.loads(line_s)
                            if obj.get("type") == "event_msg":
                                payload = obj.get("payload") or {}
                                if payload.get("type") == "token_count":
                                    info = payload.get("info") or {}
                                    t = info.get("last_token_usage", {}).get("total_tokens") or 0
                                    if t > 0:
                                        token_series.append(t)
                                    w = info.get("model_context_window") or 0
                                    if w > 0:
                                        detected_win = w
                            elif obj.get("type") == "turn_context":
                                payload = obj.get("payload") or {}
                                if payload.get("model"):
                                    detected_model = payload.get("model")
                                eff = (
                                    payload.get("effort")
                                    or payload.get("collaboration_mode", {}).get("settings", {}).get("reasoning_effort")
                                )
                                if eff:
                                    detected_think = eff
                        except Exception:
                            pass

            elif kind_lower in ("pi", "omp"):
                for line in lines:
                    line_s = line.strip()
                    if line_s.startswith("{") and line_s.endswith("}"):
                        try:
                            obj = json.loads(line_s)
                            msg = obj.get("message")
                            if obj.get("type") == "message" and msg and msg.get("role") == "assistant":
                                usage = msg.get("usage") or {}
                                t = usage.get("totalTokens") or (
                                    (usage.get("input") or 0)
                                    + (usage.get("output") or 0)
                                    + (usage.get("cacheRead") or 0)
                                    + (usage.get("cacheWrite") or 0)
                                )
                                if t > 0:
                                    token_series.append(t)
                                if msg.get("model"):
                                    detected_model = msg.get("model")
                                if msg.get("provider"):
                                    detected_provider = msg.get("provider")
                            elif obj.get("type") == "model_change":
                                if obj.get("provider"):
                                    detected_provider = obj.get("provider")
                                if obj.get("modelId"):
                                    detected_model = obj.get("modelId")
                            elif obj.get("type") == "thinking_level_change":
                                if obj.get("thinkingLevel"):
                                    detected_think = obj.get("thinkingLevel")
                        except Exception:
                            pass

                # 查询 ~/.pi/agent/models.json
                if detected_model and os.path.isfile(PI_MODELS_FILE):
                    pi_models_data = load_json(PI_MODELS_FILE) or {}
                    providers = pi_models_data.get("providers", {})
                    found_win = 0
                    if detected_provider and detected_provider in providers:
                        models = providers[detected_provider].get("models", [])
                        for m_item in models:
                            if m_item.get("id") == detected_model or m_item.get("name") == detected_model:
                                found_win = m_item.get("contextWindow") or 0
                                break
                    if not found_win:
                        for p_val in providers.values():
                            for m_item in p_val.get("models", []):
                                if m_item.get("id") == detected_model or m_item.get("name") == detected_model:
                                    found_win = m_item.get("contextWindow") or 0
                                    break
                            if found_win:
                                break
                    if found_win > 0:
                        detected_win = found_win

            # 从最近 8 次中提取 peak (prev_tokens) 与 last (curr_tokens)
            if token_series:
                last_8 = token_series[-8:]
                if len(last_8) == 1:
                    prev_tokens = 0
                    last_jsonl_tokens = last_8[0]
                else:
                    prev_tokens = max(last_8[:-1])
                    last_jsonl_tokens = last_8[-1]

                if curr_tokens <= 0:
                    curr_tokens = last_jsonl_tokens
                    source_channel = "jsonl_tail_256k"

        # 通道一补充：从 herdr agent list 元数据中抓取 Context: [...] XX%
        if curr_tokens <= 0:
            raw_str = json.dumps(agent, ensure_ascii=False)
            m_pct = re.search(r"Context:\s*\[[█░]+\]\s*([0-9]{1,3})%", raw_str)
            if m_pct:
                pct_val = int(m_pct.group(1))
                if pct_val > 0:
                    curr_tokens = conf_win * pct_val // 100
                    source_channel = "plugin_metadata"

        # 若未从 transcript 读取到 model/think，尝试从窗格状态栏或 terminal_title 兜底
        if kind.lower() in ("agy", "antigravity"):
            if not detected_model or not detected_think:
                b_mod, b_thk = probe_agy_pane_bar(pane_id)
                if b_mod and not detected_model:
                    detected_model = b_mod
                if b_thk and not detected_think:
                    detected_think = b_thk

        term_title = agent.get("terminal_title_stripped") or agent.get("terminal_title") or ""
        if term_title:
            if not detected_model:
                m_mod = re.search(r"--model\s+([A-Za-z0-9._-]+)", term_title)
                if m_mod:
                    detected_model = m_mod.group(1)
            if not detected_think:
                m_thk = re.search(r"--(?:effort|thinking)\s+([A-Za-z0-9._-]+)", term_title)
                if m_thk:
                    detected_think = m_thk.group(1).lower()

        # 默认值回填
        if not detected_model and conf_model:
            detected_model = conf_model
        if not detected_think and conf_think:
            detected_think = conf_think
        if not detected_think:
            detected_think = "medium"

        # Tier 自动推断
        if not conf_tier:
            prov_l = (detected_provider or "").lower()
            model_l = (detected_model or "").lower()
            if prov_l in ("xinference", "ollama", "vllm", "lmstudio", "llamacpp") or prov_l.startswith("local"):
                conf_tier = "B"
            elif any(k in model_l for k in ("argon", "opus", "pro", "ultra")):
                conf_tier = "S"
            elif any(k in model_l for k in ("-mini", " mini", "haiku", "lite", "nano")):
                conf_tier = "B"
            else:
                conf_tier = "A"

        effective_win = detected_win if detected_win > 0 else conf_win
        calc_arm, calc_dang = calc_thresholds(conf_tier, effective_win, detected_think)
        armed_tokens = conf_armed if conf_armed > 0 else calc_arm
        danger_tokens = conf_danger if conf_danger > 0 else calc_dang

        # 压缩断崖判定 (curr < prev * 0.6)
        just_compacted = False
        if prev_tokens >= 30000 and curr_tokens > 0:
            if curr_tokens < (prev_tokens * 60 // 100):
                just_compacted = True

        if source_channel == "unattributed" or curr_tokens <= 0:
            watermark_state = "UNATTRIBUTED"
            action_hint = "Wait for first turn or verify session attribution"
        elif curr_tokens >= danger_tokens:
            watermark_state = "DANGER"
            action_hint = "MUST compact BEFORE next prompt"
        elif curr_tokens >= armed_tokens:
            watermark_state = "ARMED"
            action_hint = "Compact at current/next idle boundary"
        else:
            watermark_state = "OK"
            action_hint = "Safe to dispatch"

        if just_compacted:
            watermark_state += "+JUST_COMPACTED"
            action_hint = f"Prepend role reload (read roles/{base_role}.md) on next prompt!"

        pct = (curr_tokens * 100 // effective_win) if (effective_win > 0 and curr_tokens > 0) else 0

        results.append({
            "role": display_name,
            "raw_name": raw_name,
            "base_role": base_role,
            "pane_id": pane_id,
            "workspace_id": ws_id,
            "tab_id": tab_id,
            "cwd": cwd,
            "harness": kind,
            "model": detected_model if detected_model else "-",
            "thinking": detected_think if detected_think else "-",
            "agent_status": agent_status,
            "channel": source_channel,
            "tier": conf_tier,
            "curr_tokens": curr_tokens,
            "prev_tokens": prev_tokens,
            "window_tokens": effective_win,
            "usage_pct": pct,
            "armed_tokens": armed_tokens,
            "danger_tokens": danger_tokens,
            "watermark_state": watermark_state,
            "action_hint": action_hint,
            "conversation_id": extract_clean_session_id(session_val),
        })

    return results


def sync_to_session_snapshot(probed_agents: List[Dict[str, Any]], workspace: Optional[str] = None, all_workspaces: bool = False) -> None:
    """自动调用 session-snapshot.py 的保存逻辑，增量更新至 .agents/session.json（仅当项目已初始化 .agents 目录时执行）。"""
    if not os.path.isdir(".agents") and not os.path.islink(".agents"):
        return
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mod_path = os.path.join(script_dir, "session-snapshot.py")
    if os.path.isfile(mod_path):
        try:
            spec = importlib.util.spec_from_file_location("session_snapshot", mod_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                mod.save_snapshot(
                    workspace=workspace,
                    all_workspaces=all_workspaces,
                    probed_agents=probed_agents,
                )
        except Exception as e:
            # 失败闭合，非阻塞但打印错误
            print(f"[agent-context] Warning: failed to sync session snapshot: {e}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="跨 Harness 多 Agent 上下文水位探针 (Dual-Channel Context Watermark Probe)"
    )
    parser.add_argument("role_or_pane", nargs="?", default="", help="过滤指定角色名或窗格 ID")
    parser.add_argument("--workspace", "-w", type=str, help="指定工作区 ID")
    parser.add_argument("--all", "-a", action="store_true", help="跨全部工作区探测")
    parser.add_argument("--json", action="store_true", help="输出结构化 JSON 格式")

    args = parser.parse_args()

    results = probe_agent_context(
        target_filter=args.role_or_pane,
        workspace=args.workspace,
        all_workspaces=args.all,
    )

    # 自动保存/同步至 .agents/session.json
    sync_to_session_snapshot(results, workspace=args.workspace, all_workspaces=args.all)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    if not results:
        print("No matching active Herdr agents found in workspace.")
        return

    # 输出表格
    header_fmt = "%-18s %-7s %-7s %-18s %-7s %-7s %-4s %-23s %-16s %s"
    print(header_fmt % ("ROLE", "PANE", "HARNESS", "MODEL", "THINK", "STATUS", "TIER", "TOKENS(CURR/ARM/WIN)", "WATERMARK_STATE", "ACTION_HINT"))
    print(header_fmt % ("------------------", "-------", "-------", "------------------", "-------", "-------", "----", "-----------------------", "----------------", "------------------------------"))

    for item in results:
        curr_k = item["curr_tokens"] // 1000
        arm_k = item["armed_tokens"] // 1000
        win = item["window_tokens"]
        win_str = f"{win // 1000000}M" if win >= 1000000 else f"{win // 1000}k"
        tok_str = f"{curr_k}k/{arm_k}k/{win_str}({item['usage_pct']}%)"

        print(header_fmt % (
            item["role"],
            item["pane_id"],
            item["harness"],
            item["model"],
            item["thinking"],
            item["agent_status"],
            item["tier"],
            tok_str,
            item["watermark_state"],
            item["action_hint"],
        ))


if __name__ == "__main__":
    main()
