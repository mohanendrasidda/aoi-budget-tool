---
name: pr-shepherd
description: Shepherd open pull requests toward merge. Brings branches up to date, waits for checks, summarizes each diff, flags security-relevant files, verifies SHA pins, and recommends a next step. Never approves, merges, or closes.
argument-hint: "[PR number ...] (default: all open PRs)"
disable-model-invocation: true
allowed-tools: Bash(gh pr list:*), Bash(gh pr view:*), Bash(gh pr checks:*), Bash(gh pr diff:*), Bash(git fetch:*), Bash(git ls-remote:*), Bash(bash .claude/skills/verify-pins/verify_pins.sh:*)
---

# pr-shepherd

Target PRs: `$ARGUMENTS`, or every open PR if empty (`gh pr list --state open`).

For each PR, in number order:

1. **State:** `gh pr view <n> --json number,title,author,headRefName,mergeStateStatus,reviewDecision,isDraft,files`.
2. **Bring up to date:** if `mergeStateStatus` is `BEHIND` (or checks are stale from before a fix landed on main) and there are no conflicts, run `gh pr update-branch <n>`. This asks the human first (it is not pre-approved). If there are conflicts, report them and skip to step 7.
3. **Checks:** `gh pr checks <n> --watch --interval 15`. On failure, read the failing log (`gh run view <id> --log-failed`) and give the one-line cause.
4. **Diff summary:** `gh pr diff <n> --name-only`, then 2-4 bullets on what actually changes and why it matters.
5. **Security-relevant files:** flag any change to `.github/**`, `.claude/**`, `.pre-commit-config.yaml`, `.gitignore`, `.gitattributes`, `CODEOWNERS`, `SECURITY.md`, `DATA_HANDLING.md`, `CLAUDE.md`, `scripts/**`, dependency manifests or lockfiles, or anything under `data/`. Say what could go wrong (e.g. a widened permission, a removed ignore rule, a new dependency).
6. **Pins:** if the PR touches `.github/workflows/` or `.pre-commit-config.yaml`, run `git fetch origin pull/<n>/head` and `bash .claude/skills/verify-pins/verify_pins.sh FETCH_HEAD`. A Dependabot PR that replaces a SHA pin with a moving tag is a FAIL.
7. **Recommend** one of: `ready for human review`, `needs changes`, `blocked (reason)`, `close (reason)`.

Finish with one table: PR, title, checks, pins, security flags, recommendation.

**Never:** approve (`gh pr review --approve`), merge (`gh pr merge`), close, push commits, or use `--admin`. Those are human decisions.
