# Security

## Reporting

Found a vulnerability, a committed secret, or AOI data somewhere it shouldn't be? Post in the Teams **#security** channel *and* DM the repo admin. Don't open a public issue with the details.

## Leaked secret runbook

A secret that reached GitHub counts as compromised, **even if you delete the commit a minute later**. Bots scrape new commits within seconds, and history rewriting does not un-leak it.

1. **Revoke/rotate first.** Kill the key at the provider (OpenAI/Anthropic/Azure console, etc.) and issue a new one. Do this before touching git.
2. Tell the team in #security: what leaked, when, and that it's rotated.
3. Remove it from the code, put the new key in `.env` / Actions secrets.
4. Only if needed, scrub history (`git filter-repo`) with the admin. That's cleanup, not the fix. Step 1 is the fix.
5. Add a short dated note in `docs/decisions/` so we learn from it.

## AOI data exposure runbook

1. Remove access or delete the copy (message, file, commit) immediately.
2. Tell the repo admin and team in #security.
3. Team lead tells Chad/Mark the same day; they decide how AOI is informed. Don't sit on it.

## Baseline controls in this repo

- `gitleaks` pre-commit hook (local) + GitHub Action (every push and PR)
- `.gitignore` blocks `.env`, keys, `data/raw/`, exports
- Dependabot alerts and weekly updates
- Branch rules on `main`: PR required, 1 approval, status checks pass, no force-push, no deletion
- CODEOWNERS: security-sensitive files need the admin's review
- Every member has 2FA on GitHub (required, not optional)
- Least privilege: collaborators get write access; only the admin changes settings
- AI agents are denied read access to `.env` and `data/raw/` (see `.claude/settings.json`)

## App-level checklist (once we have an app)

- [ ] Validate every input (sq ft is a positive number within a sane range, scope is from a fixed list)
- [ ] Treat LLM output as untrusted: never execute it, never render it as raw HTML
- [ ] Prompt injection: user text never gets to change system instructions or pricing rules
- [ ] No pricing logic or secrets in client-side code
- [ ] Rate-limit any endpoint that calls a paid API
- [ ] Log requests without logging confidential inputs
- [ ] If there's login: authorization checks on the server for every request, not just hidden buttons
