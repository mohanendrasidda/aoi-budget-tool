#!/usr/bin/env bash
# Every teammate runs this once after cloning. Safe to re-run.
# Exits non-zero if hooks can't be installed or don't pass, so a broken setup
# never prints "Done". Works in macOS/Linux shells and Git Bash on Windows.
set -euo pipefail

pyexpat_hint() {
  echo "Your Python can't load pyexpat (a known Homebrew Python issue on macOS)." >&2
  echo "Fix: install uv (https://astral.sh/uv), run 'uv tool install pre-commit', then re-run this script." >&2
  exit 1
}

# 1. pre-commit itself
if ! command -v pre-commit >/dev/null 2>&1; then
  python3 -c "import pyexpat" 2>/dev/null || pyexpat_hint
  echo "Installing pre-commit..."
  if command -v uv >/dev/null 2>&1; then uv tool install pre-commit
  elif command -v pipx >/dev/null 2>&1; then pipx install pre-commit
  else python3 -m pip install --user pre-commit
  fi
  command -v pre-commit >/dev/null 2>&1 || { echo "pre-commit installed but not on PATH. Add ~/.local/bin to PATH and re-run." >&2; exit 1; }
fi

# 2. pre-commit builds hook environments with its OWN Python, so check that one
#    (read from its #! line), not whatever python3 happens to be first on PATH.
pc_python=""
shebang=$(head -n1 "$(command -v pre-commit)" 2>/dev/null | tr -d '\r' || true)
case $shebang in
  '#!'*) set -- ${shebang#'#!'}; pc_python=${1:-}; [ "${1##*/}" = env ] && pc_python=${2:-} ;;
esac
command -v "${pc_python:-python3}" >/dev/null 2>&1 && pc_python=${pc_python:-python3} || pc_python=""
[ -z "$pc_python" ] || "$pc_python" -c "import pyexpat" 2>/dev/null || pyexpat_hint

# 3. repo git settings (before the hook run, so they apply even if a hook fails)
git config pull.rebase true
git config fetch.prune true

# 4. install the hooks and prove they pass on the current tree.
#    no-commit-to-branch is skipped for this check only: a fresh clone is on main,
#    where that hook always fails. Real commits on main are still blocked.
pre-commit install
if ! SKIP=no-commit-to-branch pre-commit run --all-files; then
  echo >&2
  echo "Setup NOT complete: a hook failed or changed files (see above). Review with: git status && git diff" >&2
  exit 1
fi

echo
echo "Done. Hooks installed and passing. Also do these by hand if you haven't:"
echo "  1. GitHub > Settings > Password and authentication: turn on 2FA"
echo "  2. Use an SSH key (or gh auth login) instead of saving a password"
echo "  3. cp .env.example .env   and fill it in locally"
