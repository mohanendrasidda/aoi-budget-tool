# 2026-09-30: Repository guardrail verification

- Repo: `mohanendrasidda/aoi-budget-tool`
- Performed by: Sidd (repo admin), with Claude Code
- Scope: initial setup from the starter kit (`scripts/admin-setup.sh`, `scripts/setup-dev.sh`), no collaborators invited yet

## Results

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Repo is private | PASS | `gh repo view --json visibility` → `{"visibility":"PRIVATE"}` |
| 2 | `protect-main` ruleset active and correct | PASS | Ruleset id `24274837`, `enforcement: active`, target `~DEFAULT_BRANCH`. Rules: `deletion`, `non_fast_forward`, `pull_request` (`required_approving_review_count: 1`, `require_code_owner_review: true`, `dismiss_stale_reviews_on_push: true`, `require_last_push_approval: true`, `required_review_thread_resolution: true`), `required_status_checks` (`gitleaks`, strict). `bypass_actors`: `actor_id 5` (RepositoryRole = admin), `bypass_mode: pull_request` |
| 3 | Direct push to `main` rejected | PASS | Throwaway commit pushed with `git push origin HEAD:main` → `GH013: Repository rule violations` ("Changes must be made through a pull request", "Required status check gitleaks is expected"), `! [remote rejected]`. Commit made on a side branch, so no hook bypass was used. Local reset to `origin/main` afterwards |
| 4 | Local secret block (pre-commit gitleaks) | PASS | Fake `ghp_` + 36 random alphanumerics staged on local branch `test/secret-scan`. Commit blocked: `Detect hardcoded secrets...Failed`, `RuleID: github-pat`, `leaks found: 1`. No commit created; file and branch deleted; never pushed |
| 5 | CI secret scan runs on a PR | PASS (after fix) | PR #3. First `pull_request` run failed with HTTP 403 "Resource not accessible by integration" on `GET /pulls/3/commits` (workflow lacked `pull-requests: read`). Fixed in commit `daad5a6`. Re-run: push run `36816021080` success, pull_request run `36816023959` success. PR state `BLOCKED` / `REVIEW_REQUIRED`, left open for admin bypass merge |
| 6 | Dependabot alerts on | PASS | `gh api -i repos/{owner}/aoi-budget-tool/vulnerability-alerts` → `HTTP/2.0 204 No Content`; `automated-security-fixes` → `{"enabled":true,"paused":false}`. Dependabot opened its first update PRs within minutes |
| 7 | Merge settings | PASS | `{"squashMergeAllowed":true,"mergeCommitAllowed":false,"rebaseMergeAllowed":false,"deleteBranchOnMerge":true,"hasWikiEnabled":false}` |
| 8 | `.gitignore` covers secrets and local files | PASS | `git check-ignore -v` → `.gitignore:2:.env`, `.gitignore:16:data/raw/`, `.gitignore:53:CLAUDE.local.md` |
| 9 | Admin account has 2FA | PASS | `gh api user -q .two_factor_authentication` → `true` |

## Findings fixed or noted during setup

| Severity | Finding | Status |
|---|---|---|
| High | `secret-scan.yml` granted only `contents: read`; on private repos the PR run 403s, so the required `gitleaks` check fails on every PR | Fixed on PR #3 (`pull-requests: read`) |
| Medium | `scripts/setup-dev.sh` ends `pre-commit run --all-files \|\| true`, so a broken hook install still exits 0 | Open: make the script fail loudly, or print a clear warning |
| Low | Homebrew `python@3.14` 3.14.7 on macOS 26.2 cannot import `pyexpat`, which breaks the Homebrew `pre-commit` install. Workaround: `uv tool install pre-commit` | Noted for teammates on macOS |
| Low | `scripts/ruleset-main.json` has no trailing newline; `end-of-file-fixer` rewrites it on every `--all-files` run | Open |
