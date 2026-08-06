# ADR-018: Repository metadata as code via the "Settings" GitHub App

## Status

Proposed (2026-08).

## Context

Projects want to manage repository metadata — description, website URL, and
topics — from within the repository instead of the GitHub web UI
(repository-configuration-as-code). The "Include in the home page" activity
toggles (Releases / Packages / Deployments in the About sidebar) were also
requested.

Two facts constrain the design:

1. **The activity toggles are not exposed by any GitHub REST API.** No tool —
   the Settings App, a `gh` CLI workflow, or anything else — can set them; they
   are web-UI-only.
2. **Labels are already managed as code, App-free.** `.github/labels.yml` +
   `label-sync.yml` (`crazy-max/ghaction-github-labeler`, always-on, repo
   `GITHUB_TOKEN`, `skip-delete: true`) provision labels on first push —
   including `no-issue`, which `check-linked-issues.yml` needs as its bypass.

## Decision

Add an **opt-in** `include_repo_settings` toggle (`default: false`, in the
`full` preset only) that renders `.github/settings.yml` for the
[Settings GitHub App](https://github.com/apps/settings). It manages
`description`, `homepage` (the docs site), `topics` (from a free-form
`repository_topics` answer — lower-cased with spaces/underscores hyphenated, and
omitted entirely when empty so the App leaves existing topics untouched; the
author is responsible for keeping the answer within GitHub's topic rules, which
the template does not enforce), and the squash-merge policy flags release-please
requires. It is a plain config file, not a workflow, so it carries
no zizmor/ghalint/actionlint obligations.

It is **opt-in** because the App is an external install — the same posture as
`include_sourcery` / `include_sonarcloud` (ADR-009), preserving the
"green on first push, zero external accounts" default.

**Labels are intentionally excluded** from `settings.yml`. Consolidating them
under the App was considered and rejected: the App is opt-in and externally
installed, so moving labels there would drop the always-on provisioning of
`no-issue` and break the `check-linked-issues` escape hatch for any project that
does not install the App. Labels stay with the existing App-free actions.

**Branch protection and collaborators are excluded**: branch protection would
duplicate/conflict with the required-status-checks setup CONTRIBUTING already
documents, and collaborators are per-project.

## Consequences

- Enabling the toggle requires installing the Settings App; until then
  `settings.yml` is inert (CI stays green).
- The App escalates push access to admin. Mitigated by documenting the
  CODEOWNERS + "Require review from Code Owners" pattern in CONTRIBUTING (the
  template already ships `* @<user>` CODEOWNERS).
- The activity-sidebar toggles remain a manual web-UI task, documented as a
  known limitation.
- No `_tasks` are added, so Renovate's copier manager (ADR-015) is unaffected.
