#!/usr/bin/env bash
# Run ONCE by the repo admin, from inside the repo folder, after `gh auth login`.
# Usage: ./scripts/admin-setup.sh <teammate1> <teammate2> ...   (GitHub usernames)
set -euo pipefail
REPO_NAME="aoi-budget-tool"
OWNER="$(gh api user -q .login)"

if ! gh repo view "$OWNER/$REPO_NAME" >/dev/null 2>&1; then
  git init -b main 2>/dev/null || true
  git add -A && git commit -m "chore: initial repo guardrails" || true
  gh repo create "$REPO_NAME" --private --source=. --remote=origin --push \
     --description "ENGR 491 AOI pre-design budget tool (private)"
fi

# Repo settings: squash-only, delete branches after merge, no wiki (docs live in the repo)
gh repo edit "$OWNER/$REPO_NAME" --enable-squash-merge --enable-merge-commit=false \
  --enable-rebase-merge=false --delete-branch-on-merge --enable-wiki=false

# Dependabot alerts + automated security fixes
gh api -X PUT "repos/$OWNER/$REPO_NAME/vulnerability-alerts" || echo "WARN: could not enable Dependabot alerts"
gh api -X PUT "repos/$OWNER/$REPO_NAME/automated-security-fixes" || echo "WARN: could not enable security fixes"

# Branch ruleset on main (needs GitHub Pro for a PRIVATE personal repo; free via GitHub Student Pack)
if gh api "repos/$OWNER/$REPO_NAME/rulesets" -q '.[].name' 2>/dev/null | grep -qx protect-main; then
  echo "Ruleset 'protect-main' already exists; skipping."
elif gh api -X POST "repos/$OWNER/$REPO_NAME/rulesets" --input scripts/ruleset-main.json >/dev/null; then
  echo "Ruleset 'protect-main' applied."
else
  echo "WARN: ruleset failed. Private repos on GitHub Free can't enforce branch rules."
  echo "      Get GitHub Pro free via education.github.com/pack, then re-run this script."
fi

# Invite collaborators with write (push) access, not admin
for u in "$@"; do
  gh api -X PUT "repos/$OWNER/$REPO_NAME/collaborators/$u" -f permission=push >/dev/null \
    && echo "Invited $u (write)"
done

echo "Now: replace @TODO names in README.md and .github/CODEOWNERS with real usernames, via a PR."
