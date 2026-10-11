# Repository setup

## This repository's own one-time setup is two documented commands, not a repo-local skill

**Id:** c85feefa-0063-4a34-8030-8c348190b96b
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Revisit when:** this repository's own setup grows beyond a couple of settings, or has to be re-applied repeatedly (forks, re-created repo, recurring drift)

The template repository's own setup — squash-only merging with the PR title as
the commit message, plus `can_approve_pull_request_reviews=true` so
release-please can open its release PR, with `default_workflow_permissions`
left at least-privilege `read` — is recorded as two `gh` commands under
"One-time repo setup" in `docs/template-architecture.md`. The repo-local
`.claude/skills/repo-setup/` that drove them (ADR-023 §3) is removed. The
shipped `repo-setup` skill and the plugin `setup` skill keep their roles.

**Reason:** the setup runs once per repository and has already run —
release-please has been cutting releases. Afterwards the skill sat in every
session's skill list next to two similarly named setup skills for generated
projects, and it duplicated the two commands the architecture doc already
carries.

**Rejected alternative:** keep it as an idempotent verifier for when the
release PR stops opening, or for a fork — re-running the two documented
commands covers that by hand.
