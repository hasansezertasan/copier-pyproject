---
name: repo-setup
description: Use to perform, resume, or verify the one-time GitHub setup THIS copier-pyproject template repository needs so its own release-please self-versioning works — squash-merge policy and the workflow permissions that let Actions open the release PR. Reach for it on "set up this repo", "why hasn't the template's release PR opened", or after cloning fresh. Distinct from the shipped repo-setup skill that generated projects carry.
---

# Set up this template repository's own release automation

## What this does

This repository versions **itself** with release-please (ADR-015): its
Conventional-Commit PRs produce the semver git tags that Renovate's copier
manager consumes in generated projects, so the setup below is load-bearing, not
cosmetic. See CLAUDE.md → "Template self-versioning (this repo, ADR-015)" and
"One-time repo setup" for the full rationale. It is safe to re-run; each step has
a check and is skipped when already done.

`gh` must be authenticated (`gh auth status`); if not, stop and ask the user to
run `gh auth login`.

## Steps (run in order; skip any whose `[CHECK]` already passes)

### 1. Squash-only merge policy `[AGENT]`

Squash-merge with the commit message set to the PR title is the only strategy
under which the `check-pr-title`-validated title becomes the commit on `main`
that release-please parses.

`[CHECK]`

```sh
gh api repos/hasansezertasan/copier-pyproject \
  --jq '.allow_squash_merge and (.allow_merge_commit | not) and (.allow_rebase_merge | not) and (.squash_merge_commit_title == "PR_TITLE")' | grep -qx true
```

`[AGENT]` (run if the check is red)

```sh
gh repo edit hasansezertasan/copier-pyproject \
  --enable-squash-merge \
  --enable-merge-commit=false \
  --enable-rebase-merge=false \
  --squash-merge-commit-message=pr-title
```

### 2. Let Actions create and approve PRs `[AGENT]`

release-please opens its release PR as a GitHub Action, so the repo must allow
Actions to create and approve pull requests. **Note the deliberate divergence
from generated projects:** this repo uses `default_workflow_permissions=write`
(generated projects use least-privilege `read` — do not copy `write` into a
generated project; that divergence is the `setup` skill's gotcha #1).

`[CHECK]`

```sh
[ "$(gh api repos/hasansezertasan/copier-pyproject/actions/permissions/workflow --jq '.default_workflow_permissions')" = "write" ] \
  && [ "$(gh api repos/hasansezertasan/copier-pyproject/actions/permissions/workflow --jq '.can_approve_pull_request_reviews')" = "true" ]
```

`[AGENT]` (run if the check is red)

```sh
gh api -X PUT repos/hasansezertasan/copier-pyproject/actions/permissions/workflow \
  -f default_workflow_permissions=write \
  -F can_approve_pull_request_reviews=true
```

## When both pass

Report "template repository setup complete" — release-please can open and
maintain its release PR, and its tags will drive downstream copier updates.
