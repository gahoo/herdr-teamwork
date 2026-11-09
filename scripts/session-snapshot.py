#!/usr/bin/env python3
"""
scripts/session-snapshot.py
Herdr Agent 会话快照持久化、幂等复活与变更集生命周期清理工具

子命令：
  save    [--workspace <ws> | --all]
  restore [all | <role_name>] [--workspace <ws> | --all] [--force] [--dry-run]
  prune   [<change-id>]
"""

import argparse
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple


SESSION_FILE = ".agents/session.json"
ENV_FILE = ".agents/environment.json"


def get_project_root(cwd: Optional[str] = None) -> str:
    """获取项目主工作区根目录（即使在 .worktrees/<id> 子工作区内执行也能还原主根目录）。"""
    cur = os.path.abspath(cwd or os.getcwd())
    m = re.match(r"^(.*?)/\.worktrees/[^/]+", cur)
    if m:
        return m.group(1)
    if os.path.islink(os.path.join(cur, ".agents")):
        return os.path.dirname(os.path.realpath(os.path.join(cur, ".agents")))
    return cur


def load_json_file(filepath: str) -> Optional[Any]:
    """安全读取 JSON 文件，失败时返回 None。"""
    if not os.path.isfile(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_json_file(filepath: str, data: Any) -> None:
    """原子化保存 JSON 文件。"""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    temp_path = f"{filepath}.tmp.{os.getpid()}"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(temp_path, filepath)


def get_base_role(name: str, roles_dict: Optional[Dict[str, Any]] = None) -> str:
    """
    base_role 安全映射：
    1. 支持安全剥离测试/临时前缀 (dummy-, test-, tmp-, mock-)；
    2. 先精确匹配 .agents/environment.json 中 .roles 的 key；
    3. 若未命中则匹配 .roles 中以 "<role>-" 为前缀的标准角色名（最长前缀优先）；
    4. 兜底剥离 -[0-9].* 后缀（如 reviewer-lead-001 -> reviewer-lead, coding-001 -> coding）。
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


def assemble_resume_args(
    harness: str,
    model: str,
    thinking: str,
    conv_id: str,
    harness_profiles: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    拼装各 Harness 的 resume_args 数组：
    - claude:  ["--model", model, "--effort", thinking, "--resume", conv_id]
    - pi/omp:  ["--model", model, "--thinking", thinking, "--session", conv_id]
    - codex:   ["--model", model, "-c", f'model_reasoning_effort="{thinking}"', "resume", conv_id]
    - agy:     ["--model", model, "--effort", thinking, "--conversation", conv_id]
    （若某字段为 "-" 或空则省略对应 flag）。
    """
    args: List[str] = []
    h = (harness or "").lower()

    def is_val(v: Optional[str]) -> bool:
        return bool(v and v.strip() and v.strip() != "-")

    clean_conv_id = extract_clean_session_id(conv_id) if is_val(conv_id) else ""

    custom_resume_flag = None
    if harness_profiles and h in harness_profiles:
        custom_resume_flag = harness_profiles[h].get("resume_flag")

    if h in ("claude", "claude-code"):
        if is_val(model):
            args.extend(["--model", model.strip()])
        if is_val(thinking):
            args.extend(["--effort", thinking.strip()])
        if is_val(clean_conv_id):
            flag = custom_resume_flag or "--resume"
            args.extend([flag, clean_conv_id])
    elif h in ("pi", "omp"):
        if is_val(model):
            args.extend(["--model", model.strip()])
        if is_val(thinking):
            args.extend(["--thinking", thinking.strip()])
        if is_val(clean_conv_id):
            flag = custom_resume_flag or "--session"
            if flag == "--resume":
                flag = "--session"
            args.extend([flag, clean_conv_id])
    elif h == "codex":
        if is_val(model):
            args.extend(["--model", model.strip()])
        if is_val(thinking):
            args.extend(["-c", f'model_reasoning_effort="{thinking.strip()}"'])
        if is_val(clean_conv_id):
            flag = custom_resume_flag or "resume"
            args.extend([flag, clean_conv_id])
    elif h in ("agy", "antigravity"):
        if is_val(model):
            m_clean = model.strip()
            # 将状态栏展示名（如 "Gemini 3.8 Flash" + thinking "medium"）规范化为 agy CLI 接受的 model ID（如 "gemini-3.8-flash-medium"）
            if " " in m_clean:
                m_slug = re.sub(r"\s+", "-", m_clean.lower())
                if is_val(thinking) and not m_slug.endswith(f"-{thinking.strip().lower()}"):
                    m_slug = f"{m_slug}-{thinking.strip().lower()}"
                args.extend(["--model", m_slug])
            else:
                args.extend(["--model", m_clean])
        if is_val(thinking):
            args.extend(["--effort", thinking.strip().lower()])
        if is_val(clean_conv_id):
            flag = custom_resume_flag or "--conversation"
            args.extend([flag, clean_conv_id])
    else:
        if is_val(model):
            args.extend(["--model", model.strip()])
        if is_val(clean_conv_id):
            flag = custom_resume_flag or "--resume"
            args.extend([flag, clean_conv_id])

    return args


def run_command(cmd: List[str], check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def get_active_agents_raw() -> List[Dict[str, Any]]:
    """读取 Herdr 活跃 Agent 列表。"""
    env_json = os.environ.get("HERDR_AGENT_LIST_JSON")
    if env_json:
        try:
            data = json.loads(env_json)
            return data.get("result", {}).get("agents", [])
        except Exception:
            return []

    try:
        proc = run_command(["herdr", "agent", "list"])
        if proc.returncode == 0 and proc.stdout:
            data = json.loads(proc.stdout)
            return data.get("result", {}).get("agents", [])
    except Exception:
        pass
    return []


def is_idle_shell(pane_id: str, active_agents: Optional[List[Dict[str, Any]]] = None) -> bool:
    """检查原 pane_id 是否存在且为空闲 shell。"""
    if not pane_id or pane_id == "-":
        return False

    if active_agents is None:
        active_agents = get_active_agents_raw()

    # 1. 检查是否有活跃 Agent 占用该 pane
    for a in active_agents:
        if a.get("pane_id") == pane_id:
            return False

    # 2. 检查 pane 是否存在且未挂载 Agent
    try:
        proc_pane = run_command(["herdr", "pane", "get", pane_id])
        if proc_pane.returncode != 0:
            return False
        pane_data = json.loads(proc_pane.stdout).get("result", {}).get("pane", {})
        if pane_data.get("agent"):
            return False
    except Exception:
        return False

    # 3. 检查 pane 进程树是否仅为主 Shell
    try:
        proc_info = run_command(["herdr", "pane", "process-info", "--pane", pane_id])
        if proc_info.returncode != 0:
            return False
        info = json.loads(proc_info.stdout).get("result", {}).get("process_info", {})
        shell_pid = info.get("shell_pid")
        fg_procs = info.get("foreground_processes", [])
        fg_grp = info.get("foreground_process_group_id")

        if not fg_procs:
            return True

        # 若前台进程均属于当前 shell
        non_shell = [
            p
            for p in fg_procs
            if p.get("pid") != shell_pid
            and p.get("name") not in ("zsh", "bash", "sh", "fish", "dash", "-zsh", "-bash")
        ]
        if not non_shell and (fg_grp is None or fg_grp == shell_pid):
            return True
    except Exception:
        return False

    return False


def normalize_model(m: str) -> str:
    """规范化模型名称以便比较（转小写、连字符、剥离思考深度后缀）。"""
    if not m or m == "-":
        return ""
    s = re.sub(r"\s+", "-", m.strip().lower())
    s = re.sub(r"-(?:off|none|low|medium|high|xhigh|max)$", "", s)
    return s


def normalize_thinking(t: str) -> str:
    """规范化思考深度。"""
    if not t or t == "-":
        return ""
    return t.strip().lower()


def get_agy_model_slug(model: str, thinking: str, resume_args: List[str]) -> str:
    """生成适用于 Agy /model 原地切换命令的 slug。"""
    if "--model" in resume_args:
        try:
            idx = resume_args.index("--model")
            if idx + 1 < len(resume_args):
                return resume_args[idx + 1]
        except Exception:
            pass
    m_clean = model.strip()
    th_clean = thinking.strip().lower() if thinking and thinking != "-" else ""
    if " " in m_clean:
        m_slug = re.sub(r"\s+", "-", m_clean.lower())
        if th_clean and not m_slug.endswith(f"-{th_clean}"):
            m_slug = f"{m_slug}-{th_clean}"
        return m_slug
    return m_clean


def probe_agy_pane_bar(pane_id: str) -> Tuple[str, str]:
    """读取 Agy 底部状态栏模型与思考等级。"""
    if not pane_id or pane_id == "-":
        return "", ""
    try:
        proc = run_command(["herdr", "pane", "read", pane_id, "--lines", "6"])
        if proc.returncode == 0 and proc.stdout:
            for line in reversed(proc.stdout.splitlines()):
                m = re.search(r"([A-Za-z0-9._ -]+)\s*·\s*(off|none|low|medium|high|xhigh)", line)
                if m:
                    model = re.sub(r"^.*? {2,}", "", m.group(1)).strip()
                    think = m.group(2).strip()
                    return model, think
    except Exception:
        pass
    return "", ""


def get_panes_in_workspace(ws_id: Optional[str]) -> List[Dict[str, Any]]:
    """获取指定工作区的窗格列表。"""
    if not ws_id or ws_id == "-":
        return []
    try:
        proc = run_command(["herdr", "pane", "list", "--workspace", ws_id])
        if proc.returncode == 0:
            return json.loads(proc.stdout).get("result", {}).get("panes", [])
    except Exception:
        pass
    return []


def create_new_pane(target_ws: Optional[str], target_cwd: str) -> Optional[str]:
    """在目标工作区/cwd 下使用 herdr pane split --no-focus 创建新窗格。"""
    split_cmd = ["herdr", "pane", "split", "--direction", "right", "--cwd", target_cwd, "--no-focus"]
    panes = get_panes_in_workspace(target_ws)
    if panes:
        split_cmd.extend(["--pane", panes[0]["pane_id"]])
    else:
        split_cmd.append("--current")

    try:
        proc = run_command(split_cmd)
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            return data.get("result", {}).get("pane", {}).get("pane_id")
    except Exception as e:
        print(f"[session-snapshot] Error splitting pane: {e}", file=sys.stderr)
    return None


def load_agent_context_module():
    """动态加载 agent-context.py 模块。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mod_path = os.path.join(script_dir, "agent-context.py")
    spec = importlib.util.spec_from_file_location("agent_context", mod_path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    return None


def save_snapshot(
    workspace: Optional[str] = None,
    all_workspaces: bool = False,
    probed_agents: Optional[List[Dict[str, Any]]] = None,
    env_file: str = ENV_FILE,
    session_file: str = SESSION_FILE,
) -> int:
    """
    保存活跃 Agent 状态快照至 .agents/session.json（增量 Upsert，严禁冲掉其他活跃工作区记录）。
    """
    env_data = load_json_file(env_file) or {}
    roles_cfg = env_data.get("roles", {})
    profiles_cfg = env_data.get("harness_profiles", {})

    if probed_agents is None:
        agent_context_mod = load_agent_context_module()
        if agent_context_mod:
            probed_agents = agent_context_mod.probe_agent_context(
                workspace=workspace,
                all_workspaces=all_workspaces,
            )
        else:
            probed_agents = []

    # 读取已有 session.json
    existing_session = load_json_file(session_file) or {}
    existing_agents = existing_session.get("agents", {})

    current_ws = workspace or os.environ.get("HERDR_WORKSPACE_ID") or existing_session.get("workspace_id") or "main"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    upsert_count = 0
    skipped_unnamed: List[str] = []
    for agent in probed_agents:
        raw_name = (agent.get("raw_name") or "").strip()
        display_role = agent.get("role") or agent.get("name") or agent.get("pane_id") or "unknown"
        # 仅保存通过 herdr agent start / herdr agent rename 正式命名的合法角色
        if not raw_name:
            skipped_unnamed.append(display_role)
            continue
        if raw_name in ("bootstrap", "py-coder", "script-tester") or not re.match(r"^[a-z][a-z0-9_-]{0,31}$", raw_name):
            continue
        name = raw_name

        base_role = agent.get("base_role") or get_base_role(raw_name, roles_cfg)
        harness = agent.get("harness") or agent.get("kind") or "unknown"
        model = agent.get("model", "")
        if model == "-":
            model = ""
        thinking = agent.get("thinking", "")
        if thinking == "-":
            thinking = ""
        raw_conv_id = agent.get("conversation_id") or agent.get("session_val") or ""
        conv_id = extract_clean_session_id(raw_conv_id)

        resume_args = assemble_resume_args(
            harness=harness,
            model=model,
            thinking=thinking,
            conv_id=conv_id,
            harness_profiles=profiles_cfg,
        )

        agent_record = {
            "name": name,
            "base_role": base_role,
            "workspace_id": agent.get("workspace_id", current_ws),
            "pane_id": agent.get("pane_id", "-"),
            "tab_id": agent.get("tab_id", "-"),
            "cwd": agent.get("cwd") or os.getcwd(),
            "harness": harness,
            "model": model,
            "thinking": thinking,
            "conversation_id": conv_id,
            "resume_args": resume_args,
        }

        existing_agents[name] = agent_record
        upsert_count += 1

    updated_session = {
        "updated_at": now_iso,
        "project": os.path.basename(get_project_root()),
        "agents": existing_agents,
    }

    save_json_file(session_file, updated_session)
    if skipped_unnamed and os.path.basename(sys.argv[0]) == "session-snapshot.py":
        print(
            f"[session-snapshot] Note: skipped {len(skipped_unnamed)} unnamed pane(s) ({', '.join(skipped_unnamed)}); "
            f"use 'herdr agent rename <pane_id> <role_name>' if you want them tracked in {session_file}."
        )
    return upsert_count


def restore_agents(
    target: str = "all",
    workspace: Optional[str] = None,
    all_workspaces: bool = False,
    force: bool = False,
    dry_run: bool = False,
    session_file: str = SESSION_FILE,
) -> int:
    """
    幂等恢复角色。
    """
    session_data = load_json_file(session_file)
    if not session_data or "agents" not in session_data:
        print(f"[restore] No valid agents found in {session_file}.", file=sys.stderr)
        return 0

    agents_dict = session_data.get("agents", {})
    current_ws = workspace or os.environ.get("HERDR_WORKSPACE_ID")
    current_cwd = os.getcwd()

    # 1. 筛选目标恢复记录
    targets_to_restore: List[Dict[str, Any]] = []
    if target != "all":
        # 单点恢复
        found = agents_dict.get(target)
        if not found:
            for k, v in agents_dict.items():
                if v.get("name") == target or v.get("base_role") == target:
                    found = v
                    break
        if not found:
            print(f"[restore] Target agent '{target}' not found in {session_file}.", file=sys.stderr)
            return 0
        targets_to_restore.append(found)
    else:
        for name, record in agents_dict.items():
            if all_workspaces:
                targets_to_restore.append(record)
            elif workspace:
                if record.get("workspace_id") == workspace:
                    targets_to_restore.append(record)
            elif current_ws:
                if record.get("workspace_id") == current_ws:
                    targets_to_restore.append(record)
            else:
                if record.get("cwd") == current_cwd:
                    targets_to_restore.append(record)

    if not targets_to_restore:
        print("[restore] No matching agent records to restore.")
        return 0

    active_agents = get_active_agents_raw()
    active_names = {a.get("name"): a for a in active_agents if a.get("name")}
    active_panes = {a.get("pane_id"): a for a in active_agents if a.get("pane_id")}

    restored_count = 0
    for agent_rec in targets_to_restore:
        name = agent_rec.get("name")
        harness = agent_rec.get("harness") or "agy"
        orig_pane = agent_rec.get("pane_id")
        target_cwd = agent_rec.get("cwd") or current_cwd
        target_ws = agent_rec.get("workspace_id")
        resume_args = agent_rec.get("resume_args") or []

        # 检查是否已存活
        old_running_pane = None
        if name in active_names:
            cur_pane = active_names[name].get("pane_id")
            live_model = ""
            live_thinking = ""
            live_conv_id = ""

            # 实时探测当前运行中的 Agent 状态
            agent_context_mod = load_agent_context_module()
            if agent_context_mod:
                try:
                    probed_list = agent_context_mod.probe_agent_context(target_filter=name)
                    if probed_list:
                        live_info = probed_list[0]
                        live_model = (live_info.get("model") or "").strip()
                        live_thinking = (live_info.get("thinking") or "").strip().lower()
                        live_conv_id = (live_info.get("conversation_id") or "").strip()
                except Exception:
                    pass

            if not live_model or live_model == "-":
                b_mod, b_thk = probe_agy_pane_bar(cur_pane)
                if b_mod:
                    live_model = b_mod
                if b_thk:
                    live_thinking = b_thk

            target_model = (agent_rec.get("model") or "").strip()
            target_thinking = (agent_rec.get("thinking") or "").strip().lower()
            target_conv_id = extract_clean_session_id((agent_rec.get("conversation_id") or "").strip())
            live_conv_id = extract_clean_session_id(live_conv_id)

            conv_mismatch = bool(target_conv_id and live_conv_id and target_conv_id != live_conv_id)
            norm_target_m = normalize_model(target_model)
            norm_live_m = normalize_model(live_model)
            model_mismatch = bool(norm_target_m and norm_live_m and norm_target_m != norm_live_m)
            norm_target_t = normalize_thinking(target_thinking)
            norm_live_t = normalize_thinking(live_thinking)
            think_mismatch = bool(norm_target_t and norm_live_t and norm_target_t != norm_live_t)

            if not force and not conv_mismatch and not model_mismatch and not think_mismatch:
                print(f"[restore] Agent '{name}' is already running on pane {cur_pane} with matching configuration ({live_model} · {live_thinking}). Skipping (use --force to restart).")
                continue

            if not force and (conv_mismatch or model_mismatch or think_mismatch):
                diff_items = []
                if conv_mismatch:
                    diff_items.append(f"conversation_id (live='{live_conv_id}' != session='{target_conv_id}')")
                if model_mismatch:
                    diff_items.append(f"model (live='{live_model}' != session='{target_model}')")
                if think_mismatch:
                    diff_items.append(f"thinking (live='{live_thinking}' != session='{target_thinking}')")
                print(f"[restore] Detected drift for active agent '{name}' on pane {cur_pane}: {', '.join(diff_items)}")

                # 尝试非交互式原地切换模型/思考深度（仅当 conversation_id 一致且 Harness 支持时）
                if not conv_mismatch and (model_mismatch or think_mismatch):
                    h_lower = (harness or "").lower()
                    if h_lower in ("agy", "antigravity"):
                        slug = get_agy_model_slug(target_model, target_thinking, resume_args)
                        if dry_run:
                            print(f"[dry-run] Would in-place switch '{name}' on pane {cur_pane} via: /model {slug}")
                            restored_count += 1
                            continue
                        else:
                            print(f"[restore] Harness '{harness}' supports non-interactive in-place switch. Sending: /model {slug} ...")
                            run_command(["herdr", "agent", "prompt", name, f"/model {slug}"])
                            time.sleep(0.6)
                            b_mod, b_thk = probe_agy_pane_bar(cur_pane)
                            if (not norm_target_m or normalize_model(b_mod) == norm_target_m) and (
                                not norm_target_t or normalize_thinking(b_thk) == norm_target_t
                            ):
                                print(f"[restore] Successfully switched '{name}' in-place to {b_mod} · {b_thk} on pane {cur_pane}.")
                                restored_count += 1
                                continue
                            else:
                                print(f"[restore] In-place switch verification got '{b_mod} · {b_thk}'. Falling back to restart...")
                    elif h_lower in ("pi", "omp"):
                        if dry_run:
                            print(f"[dry-run] Would in-place switch pi model/thinking for '{name}' on pane {cur_pane}")
                            restored_count += 1
                            continue
                        else:
                            print(f"[restore] Harness '{harness}' supports in-place switch. Updating...")
                            if model_mismatch:
                                run_command(["herdr", "agent", "prompt", name, f"/model {target_model}"])
                            if think_mismatch:
                                run_command(["herdr", "agent", "prompt", name, f"/thinking {target_thinking}"])
                            time.sleep(0.5)
                            print(f"[restore] Successfully switched '{name}' in-place on pane {cur_pane}.")
                            restored_count += 1
                            continue
                    else:
                        print(f"[restore] Harness '{harness}' does not support non-interactive in-place model switch. Automatically restarting '{name}'...")
                else:
                    print(f"[restore] Conversation ID mismatch or restart required. Automatically restarting '{name}'...")

            old_running_pane = cur_pane

        # 检查原 pane 是否为空闲 shell
        target_pane = None
        if not old_running_pane and orig_pane and is_idle_shell(orig_pane, active_agents):
            target_pane = orig_pane
            print(f"[restore] Reusing existing idle pane {orig_pane} for '{name}'.")
        else:
            if dry_run:
                target_pane = f"{target_ws or 'ws'}:p_new"
                print(f"[dry-run] Would split new pane in workspace={target_ws}, cwd={target_cwd} for '{name}'.")
                if old_running_pane:
                    print(f"[dry-run] Would close old running pane {old_running_pane} before starting '{name}'.")
            else:
                target_pane = create_new_pane(target_ws, target_cwd)
                if not target_pane:
                    print(f"[restore] Failed to create new pane for '{name}'.", file=sys.stderr)
                    continue
                print(f"[restore] Created new pane {target_pane} for '{name}'.")
                if old_running_pane and old_running_pane != target_pane:
                    run_command(["herdr", "pane", "close", old_running_pane])
                    time.sleep(0.5)

        start_cmd = ["herdr", "agent", "start", name, "--kind", harness, "--pane", target_pane, "--"] + resume_args

        if dry_run:
            print(f"[dry-run] Would execute: {' '.join(start_cmd)}")
            restored_count += 1
        else:
            print(f"[restore] Starting agent '{name}' on pane {target_pane}...")
            proc = run_command(start_cmd)
            if proc.returncode != 0:
                print(f"[restore] Failed to start agent '{name}': {proc.stderr or proc.stdout}", file=sys.stderr)
            else:
                print(f"[restore] Successfully started agent '{name}'.")
                agent_rec["pane_id"] = target_pane
                restored_count += 1

    if not dry_run and restored_count > 0:
        save_snapshot(workspace=workspace, all_workspaces=all_workspaces)

    return restored_count


def prune_records(change_id: Optional[str] = None, session_file: str = SESSION_FILE) -> int:
    """
    清理 .agents/session.json：
    - 若传 <change-id>：清理属于 .worktrees/<change-id> 目录或带 -<change-id> / 对应短编号后缀的角色记录；
    - 若未传 <change-id>：清理当前已不在 herdr agent list 中的失效记录。
    """
    session_data = load_json_file(session_file)
    if not session_data or "agents" not in session_data:
        return 0

    agents_dict: Dict[str, Any] = session_data.get("agents", {})
    to_remove: List[str] = []

    if change_id:
        change_id_clean = change_id.strip()
        short_num = ""
        m = re.match(r"^([0-9]+)", change_id_clean)
        if m:
            short_num = m.group(1)

        wt_pattern = f".worktrees/{change_id_clean}"
        suffix_full = f"-{change_id_clean}"
        suffix_short = f"-{short_num}" if short_num else ""

        for name, record in agents_dict.items():
            cwd = record.get("cwd", "")
            match_wt = wt_pattern in cwd or (short_num and f".worktrees/{short_num}" in cwd)
            match_suffix = (
                name == change_id_clean
                or name.endswith(suffix_full)
                or (suffix_short and name.endswith(suffix_short))
            )
            if match_wt or match_suffix:
                to_remove.append(name)
    else:
        active_agents = get_active_agents_raw()
        active_names = {a.get("name") for a in active_agents if a.get("name")}
        active_panes = {a.get("pane_id") for a in active_agents if a.get("pane_id")}

        for name, record in agents_dict.items():
            if name not in active_names and record.get("pane_id") not in active_panes:
                to_remove.append(name)

    for name in to_remove:
        del agents_dict[name]

    if to_remove:
        session_data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save_json_file(session_file, session_data)
        for name in to_remove:
            print(f"[prune] Removed '{name}' from {session_file}")

    return len(to_remove)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Herdr Agent 会话快照持久化、幂等复活与变更集生命周期清理工具",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # 1. save
    save_parser = subparsers.add_parser("save", help="扫描活跃 Agent 并增量合并写入 .agents/session.json")
    save_group = save_parser.add_mutually_exclusive_group()
    save_group.add_argument("--workspace", "-w", type=str, help="指定工作区 ID")
    save_group.add_argument("--all", "-a", action="store_true", help="跨全部工作区扫描保存")

    # 2. restore
    restore_parser = subparsers.add_parser("restore", help="从 .agents/session.json 幂等恢复角色")
    restore_parser.add_argument("target", nargs="?", default="all", help="角色名或 'all' (默认 'all')")
    restore_group = restore_parser.add_mutually_exclusive_group()
    restore_group.add_argument("--workspace", "-w", type=str, help="指定工作区 ID")
    restore_group.add_argument("--all", "-a", action="store_true", help="跨全部工作区恢复")
    restore_parser.add_argument("--force", "-f", action="store_true", help="强制重新启动即使 Agent 已在运行")
    restore_parser.add_argument("--dry-run", "-n", action="store_true", help="预演恢复动作，不实际执行命令")

    # 3. prune
    prune_parser = subparsers.add_parser("prune", help="从 .agents/session.json 清理失效或属于变更集的工作区记录")
    prune_parser.add_argument("change_id", nargs="?", help="变更集编号（如 001 或 001-user-auth）")

    args = parser.parse_args()

    if args.subcommand == "save":
        count = save_snapshot(workspace=args.workspace, all_workspaces=args.all)
        print(f"[session-snapshot] Saved/updated {count} agent(s) into {SESSION_FILE}")
    elif args.subcommand == "restore":
        count = restore_agents(
            target=args.target,
            workspace=args.workspace,
            all_workspaces=args.all,
            force=args.force,
            dry_run=args.dry_run,
        )
        print(f"[session-snapshot] Restored {count} agent(s).")
    elif args.subcommand == "prune":
        count = prune_records(change_id=args.change_id)
        print(f"[session-snapshot] Pruned {count} agent record(s).")


if __name__ == "__main__":
    main()
