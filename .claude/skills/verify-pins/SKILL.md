---
name: verify-pins
description: Verify that every GitHub Action and pre-commit hook is pinned to a full commit SHA that matches the tag named in its "# vX.Y.Z" comment. Use after any change to .github/workflows/ or .pre-commit-config.yaml, and when reviewing Dependabot PRs.
argument-hint: "[git-ref] (default: working tree; e.g. FETCH_HEAD after fetching a PR head)"
allowed-tools: Bash(bash .claude/skills/verify-pins/verify_pins.sh:*), Bash(git fetch:*)
---

# verify-pins

Read-only supply-chain check. A tag can be moved to point at different code; a commit SHA cannot. This confirms each pin is a SHA **and** that the SHA is what the tag in its comment really points to.

1. Run `bash .claude/skills/verify-pins/verify_pins.sh $ARGUMENTS`.
   - To check a PR without checking it out: `git fetch origin pull/<n>/head` then pass `FETCH_HEAD`.
2. Report the PASS/FAIL lines as a short table: file:line, action or hook, tag, result.
3. For any FAIL, explain which kind it is and the fix:
   - **Not a SHA** (a tag or branch): pin it. Resolve with `git ls-remote https://github.com/<org>/<repo> 'refs/tags/<tag>' 'refs/tags/<tag>^{}'` (use the `^{}` line if present: it's the commit an annotated tag points to).
   - **No tag comment**: add `# vX.Y.Z` (Actions) or `# frozen: vX.Y.Z` (pre-commit) so humans and Dependabot can read it.
   - **Mismatch**: treat as suspicious. Do not "fix" it by changing the comment; stop and tell the human.
4. Never edit files in this skill. It only reports.
