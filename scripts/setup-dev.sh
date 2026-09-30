#!/usr/bin/env bash
# Every teammate runs this once after cloning.
set -euo pipefail
command -v pre-commit >/dev/null || { echo "Installing pre-commit..."; pipx install pre-commit 2>/dev/null || pip install --user pre-commit; }
pre-commit install
pre-commit run --all-files || true
git config pull.rebase true
git config fetch.prune true
echo
echo "Done. Also do these by hand if you haven't:"
echo "  1. GitHub > Settings > Password and authentication: turn on 2FA"
echo "  2. Use an SSH key (or gh auth login) instead of saving a password"
echo "  3. cp .env.example .env   and fill it in locally"
