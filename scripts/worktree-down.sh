#!/usr/bin/env bash
# ==============================================================================
# herdr-teamwork: Universal Git Worktree Teardown Script (worktree-down.sh)
# Usage: worktree-down.sh <change-id> [--delete-branch]
# Example: worktree-down.sh 001-user-auth --delete-branch
# ==============================================================================
set -euo pipefail

if [ "${#}" -lt 1 ]; then
  echo "Usage: $0 <change-id> [--delete-branch]" >&2
  exit 1
fi

CHANGE_ID="$1"
DELETE_BRANCH="${2:-}"
WORKTREE_DIR=".worktrees/${CHANGE_ID}"

if [ ! -d "${WORKTREE_DIR}" ]; then
  echo "[worktree-down] Worktree ${WORKTREE_DIR} does not exist. Nothing to clean."
  exit 0
fi

# 1. Close any dedicated Herdr daemon pane recorded via .ops-pane inside the worktree
if [ -f "${WORKTREE_DIR}/.ops-pane" ]; then
  DAEMON_PANE=$(cat "${WORKTREE_DIR}/.ops-pane" 2>/dev/null || true)
  if [ -n "${DAEMON_PANE}" ] && command -v herdr >/dev/null 2>&1; then
    echo "[worktree-down] Closing daemon pane ${DAEMON_PANE}..."
    herdr pane close "${DAEMON_PANE}" 2>/dev/null || true
  fi
  rm -f "${WORKTREE_DIR}/.ops-pane"
fi

# Fallback: Stop any background process recorded via .ops.pid inside the worktree
if [ -f "${WORKTREE_DIR}/.ops.pid" ]; then
  PID=$(cat "${WORKTREE_DIR}/.ops.pid" 2>/dev/null || true)
  if [ -n "${PID}" ] && kill -0 "${PID}" 2>/dev/null; then
    echo "[worktree-down] Stopping background process PID ${PID}..."
    kill "${PID}" 2>/dev/null || true
  fi
  rm -f "${WORKTREE_DIR}/.ops.pid"
fi

# 2. Detect branch name before removing worktree
BRANCH_NAME=$(git -C "${WORKTREE_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || true)

# 3. Safely unlink symlinks FIRST (never recursively delete through symlinks!)
for link_name in changes .agents node_modules .venv; do
  if [ -L "${WORKTREE_DIR}/${link_name}" ]; then
    rm "${WORKTREE_DIR}/${link_name}"
  fi
done

# 4. Remove the Git Worktree cleanly
git worktree remove --force "${WORKTREE_DIR}"
git worktree prune

# 5. Optionally delete the merged feature branch
if [ "${DELETE_BRANCH}" = "--delete-branch" ] && [ -n "${BRANCH_NAME}" ] && [ "${BRANCH_NAME}" != "main" ] && [ "${BRANCH_NAME}" != "master" ]; then
  git branch -d "${BRANCH_NAME}" 2>/dev/null || true
fi

echo "[worktree-down] Cleaned up ${WORKTREE_DIR}"
