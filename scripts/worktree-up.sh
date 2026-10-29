#!/usr/bin/env bash
# ==============================================================================
# herdr-teamwork: Universal Git Worktree Bootstrap Script (worktree-up.sh)
# Usage: worktree-up.sh <change-id> [branch-name] [base-ref]
# Example: worktree-up.sh 001-user-auth feat/001-user-auth main
# ==============================================================================
set -euo pipefail

if [ "${#}" -lt 1 ]; then
  echo "Usage: $0 <change-id> [branch-name] [base-ref]" >&2
  exit 1
fi

CHANGE_ID="$1"
BRANCH_NAME="${2:-feat/${CHANGE_ID}}"
BASE_REF="${3:-HEAD}"
WORKTREE_DIR=".worktrees/${CHANGE_ID}"

# Ensure we are at the repository root (not already inside a worktree)
if [ -L "changes" ] || [ -L ".agents" ]; then
  echo "Error: Must be executed from the main workspace root, not inside a worktree." >&2
  exit 1
fi

mkdir -p .worktrees changes .agents

# 1. Create or attach Git Worktree
if [ -d "${WORKTREE_DIR}" ]; then
  echo "[worktree-up] Worktree directory ${WORKTREE_DIR} already exists."
else
  if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
    git worktree add "${WORKTREE_DIR}" "${BRANCH_NAME}"
  else
    git worktree add -b "${BRANCH_NAME}" "${WORKTREE_DIR}" "${BASE_REF}"
  fi
fi

# 2. Mount core herdr-teamwork shared asset & infrastructure symlinks
ln -sfn "../../changes" "${WORKTREE_DIR}/changes"
ln -sfn "../../.agents" "${WORKTREE_DIR}/.agents"

# 3. Polyglot dependency & environment zero-copy sharing (Copy-on-Write ready)
# - Node / TypeScript: symlink node_modules if present in main root
if [ -d "node_modules" ] && [ ! -e "${WORKTREE_DIR}/node_modules" ]; then
  ln -sfn "../../node_modules" "${WORKTREE_DIR}/node_modules"
  echo "[worktree-up] Linked shared node_modules (remember: 'rm node_modules' symlink before mutating deps)."
fi

# - Python: symlink .venv if present in main root
if [ -d ".venv" ] && [ ! -e "${WORKTREE_DIR}/.venv" ]; then
  ln -sfn "../../.venv" "${WORKTREE_DIR}/.venv"
  echo "[worktree-up] Linked shared .venv (remember: 'rm .venv' symlink before mutating deps)."
fi

# - Environment configs: copy local untracked .env* files if present
for env_file in .env .env.local .env.development; do
  if [ -f "${env_file}" ] && [ ! -e "${WORKTREE_DIR}/${env_file}" ]; then
    cp "${env_file}" "${WORKTREE_DIR}/${env_file}"
    echo "[worktree-up] Copied ${env_file} into ${WORKTREE_DIR}/"
  fi
done

# Note:
# - Go projects automatically share global $GOCACHE and $GOMODCACHE.
# - Rust projects keep isolated target/ per worktree to prevent concurrent .cargo-lock contention (or use sccache if configured).

echo "[worktree-up] Ready: ${WORKTREE_DIR} (branch: ${BRANCH_NAME})"
