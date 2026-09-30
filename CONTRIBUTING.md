# Contributing

## The flow

```
main (protected, always works)
 └── feat/12-sqft-input      ← your branch, one issue, short-lived
       └── PR → 1 review → checks green → squash merge → delete branch
```

1. Pick or create an issue. Assign yourself.
2. `git switch main && git pull`
3. `git switch -c feat/<issue#>-<short-name>` (prefixes: `feat/`, `fix/`, `docs/`, `chore/`, `spike/`)
4. Commit small and often. Push your branch daily so work isn't only on your laptop.
5. Open a PR early (draft is fine). Fill in the template.
6. One teammate reviews. Author merges after approval. **Squash merge.**
7. Delete the branch.

Never commit straight to `main`. Branch rules will block it anyway.

## Commits

Conventional-ish, present tense, says *why* when it isn't obvious:

```
feat: add price-per-sqft calculation for open office scope
fix: reject negative square footage (#14)
docs: record decision to use synthetic data until AOI agreement
```

- One logical change per commit.
- Review what you're committing: `git diff --staged` every time. This is the habit that catches secrets and junk files.
- Never `git add .` blindly on a dirty tree. Use `git add -p` or name the files.

## Pull requests

- Under ~400 changed lines. Big PRs get skimmed, not reviewed.
- Describe what changed, why, how you tested it, and what the AI wrote.
- Reviewer checks: does it do what the issue says, are there tests, any secret or AOI data, any input that isn't validated, would I be able to maintain this.
- Reviewer approval means "I read it and I'd defend it." Not "looks fine."

## AI-generated code

AI agents (Claude Code, Copilot, etc.) are welcome. Rules:

- **You own what you merge.** "Claude wrote it" is not a defense in review or in a demo.
- Mark it in the PR template (none / some / most).
- Read every line before you commit it. If you can't explain a line, don't ship it.
- Tests for AI-written logic are mandatory, not optional.
- Agents follow [CLAUDE.md](CLAUDE.md). Agents never push to `main`, never touch `.env`, never see `data/raw/`.

## Things that will bite you

| Situation | Do | Don't |
|---|---|---|
| Your branch is behind main | `git pull --rebase origin main` on *your* branch | Rebase or force-push a branch someone else is using |
| Merge conflict | Read both sides, talk to the other author if unsure | Pick "accept mine" for the whole file |
| Committed something wrong, not pushed | `git reset --soft HEAD~1` and fix | Panic |
| Committed a secret, pushed | Follow [SECURITY.md](SECURITY.md): rotate first | Just delete the file and hope |
| Need to undo a merged PR | `git revert <sha>` via new PR | `git push --force` on main |
| Big binary / dataset | Ask first; probably doesn't belong in git | Commit a 200 MB CSV |
