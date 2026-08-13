# ADR-021: Repository branch protection as code via a Rulesets sync workflow

## Status

Proposed (2026-08). Supersedes in part
[ADR-018](018-repository-settings-as-code.md): branch protection, excluded
there, is now available opt-in.

## Context

[ADR-018](018-repository-settings-as-code.md) added `include_repo_settings` (the
"Settings" GitHub App syncing `.github/settings.yml`) for repository *metadata*
but deliberately excluded branch protection, on the grounds it "would
duplicate/conflict with the required-status-checks setup CONTRIBUTING already
documents".

That leaves a real gap: a generated repository ships the exact CI checks you
would gate merges on (`check`, `Validate branch name`, `Validate PR title`,
`Verify linked issue`, `Task Completed Checker`, the security scans) but none is
enforced until an admin hand-wires protection in the web UI — the per-project
drift the template otherwise designs away.

Two facts shape the decision:

1. **The "Settings" App cannot manage rulesets.** It handles *classic* branch
   protection at best and has no Rulesets API support, so this cannot ride on
   the existing `settings.yml`.
2. **The Actions `GITHUB_TOKEN` cannot manage rulesets.** Creating/updating a
   ruleset requires `Administration: read & write`, and `administration` is not a
   grantable scope for the workflow token. A fine-grained PAT (or a GitHub App
   token) is required.

## Decision

Add an opt-in `include_repo_ruleset` toggle (`default: false`, `full` preset
only — the ADR-009 posture), scaffolding two artifacts:

- `.github/rulesets/main.json` — the canonical repository ruleset: `enforcement:
  active`, targeting `~DEFAULT_BRANCH`; rules `deletion`, `non_fast_forward`,
  `required_linear_history`, a `pull_request` rule (squash-only merges, thread
  resolution required, **`required_approving_review_count: 0`**), and
  `required_status_checks` (strict) listing the template's actual CI job names
  (the Trivy context only when `include_web`). `bypass_actors: []`.
- `.github/workflows/ruleset-sync.yml` — an App-free, idempotent sync workflow
  (list → find by name → PUT/POST) mirroring `label-sync.yml`. It authenticates
  with a `REPO_ADMIN_TOKEN` fine-grained PAT (`Administration: read & write`) and
  **warn-and-skips when the secret is absent** (the ADR-017 PAT posture), so a
  fresh repo stays green.

Design choices:

- **`required_approving_review_count: 0`, no bypass** — status checks are strictly
  enforced, but no human approval is required. This avoids deadlocking solo
  maintainers on their own PRs and unblocks release-please/Renovate, while
  ensuring nobody bypasses the checks.
- **Independent of `include_repo_settings`** — the two are complementary
  (`settings.yml` controls which merge buttons exist; the ruleset enforces
  policy) and both encode squash-only so they agree.
- **Rulesets, not classic protection** — a ruleset is one declarative,
  export/import-friendly file, which weakens ADR-018's "would duplicate/conflict"
  concern.

## Consequences

- Branch protection is now available as code (opt-in), closing the gap ADR-018
  deferred. Managing collaborators/teams as code remains out of scope.
- `strict_required_status_checks_policy: true` means concurrent bot PRs must be
  rebased on the latest default branch before merging (some extra churn) — the
  intended "always current before merge" posture.
- Manual ruleset edits in the web UI are reverted on the next default-branch push
  (the intended config-as-code behavior).
- The `REPO_ADMIN_TOKEN` PAT is a one-time setup, documented in the generated
  `CONTRIBUTING.md` alongside the other repository-setup steps.
