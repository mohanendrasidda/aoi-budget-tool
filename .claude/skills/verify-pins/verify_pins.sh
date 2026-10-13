#!/usr/bin/env bash
# verify_pins.sh: read-only supply-chain check.
# Every GitHub Action (`uses:`) and pre-commit hook (`rev:`) must be pinned to a full
# 40-char commit SHA, carry a "# vX.Y.Z" (or "# frozen: vX.Y.Z") comment, and that tag
# must resolve (git ls-remote, peeled ^{} for annotated tags) to the same SHA.
# Usage: verify_pins.sh [git-ref]   (default: working tree; e.g. FETCH_HEAD for a PR head)
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
REF="${1:-}"
show() { if [ -n "$REF" ]; then git show "$REF:$1" 2>/dev/null; else cat "$1" 2>/dev/null; fi; }
list_workflows() {
  if [ -n "$REF" ]; then git ls-tree --name-only "$REF" .github/workflows/ 2>/dev/null
  else ls .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null; fi | grep -E '\.ya?ml$'
}
fail=0; n=0
check() { # url sha tag where
  local url=$1 sha=$2 tag=$3 where=$4 got
  n=$((n+1))
  if ! [[ $sha =~ ^[0-9a-f]{40}$ ]]; then echo "FAIL  $where: '$sha' is not a full commit SHA"; fail=1; return; fi
  if [ -z "$tag" ]; then echo "FAIL  $where: no '# vX.Y.Z' comment naming the tag"; fail=1; return; fi
  got=$(git ls-remote "$url" "refs/tags/$tag" "refs/tags/$tag^{}" 2>/dev/null | awk '{print $1}' | tail -1)
  if [ -z "$got" ]; then echo "FAIL  $where: tag $tag not found at $url"; fail=1
  elif [ "$got" = "$sha" ]; then echo "PASS  $where: $tag = ${sha:0:7}"
  else echo "FAIL  $where: $tag resolves to ${got:0:7}, file pins ${sha:0:7}"; fail=1; fi
}
# GitHub Actions
for wf in $(list_workflows); do
  while IFS= read -r line; do
    lineno=${line%%:*}; text=${line#*:}
    ref=$(printf '%s\n' "$text" | sed -E 's/.*uses:[[:space:]]*["'\'']?([^[:space:]"'\''#]+).*/\1/')
    case $ref in ./*|docker://*) continue ;; esac
    spec=${ref%@*}; sha=${ref##*@}
    repo=$(printf '%s\n' "$spec" | cut -d/ -f1-2)
    tag=$(printf '%s\n' "$text" | sed -nE 's/.*#[[:space:]]*(v[0-9][^[:space:]]*).*/\1/p')
    check "https://github.com/$repo" "$sha" "$tag" "$wf:$lineno $spec"
  done < <(show "$wf" | grep -nE '^[[:space:]]*(-[[:space:]]*)?uses:')
done
# pre-commit hooks
while IFS='|' read -r lineno repo text; do
  case $repo in local|meta|"") continue ;; esac
  sha=$(printf '%s\n' "$text" | sed -E 's/.*rev:[[:space:]]*["'\'']?([^[:space:]"'\''#]+).*/\1/')
  tag=$(printf '%s\n' "$text" | sed -nE 's/.*#[[:space:]]*(frozen:[[:space:]]*)?(v[0-9][^[:space:]]*).*/\2/p')
  check "$repo" "$sha" "$tag" ".pre-commit-config.yaml:$lineno $(basename "$repo")"
done < <(show .pre-commit-config.yaml | awk '/^[[:space:]]*-[[:space:]]*repo:/{r=$3} /^[[:space:]]*rev:/{print NR"|"r"|"$0}')
echo "---"
if [ $fail -eq 0 ]; then echo "verify-pins: $n checked, all PASS"; else echo "verify-pins: $n checked, FAILURES above"; fi
exit $fail
