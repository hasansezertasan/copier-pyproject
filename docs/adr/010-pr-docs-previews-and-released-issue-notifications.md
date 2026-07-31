# ADR-010: PR documentation previews and released-issue notifications

## Status

Proposed (2026-07). Inspired by a survey of established open-source Python
project repositories.

## Context

Beyond the external-SaaS integrations of
[ADR-009](009-optional-external-quality-community-integrations.md), some mature
project repos ship two purely **self-contained** CI/release ergonomics that need
no third-party account:

1. **PR documentation previews** (a `docs-preview.yml` workflow): on a successful
   PR CI run, the built Sphinx HTML is deployed and a preview URL is commented on
   the PR, so reviewers see rendered docs without checking out the branch.
2. **Released-issue notifications** (a `notify-released-issues.yml` workflow):
   when a release ships, the issues that release closed get an automated comment
   pointing at the release, closing the loop for reporters.

The template already builds Sphinx docs on every push/release
([ADR-006](006-sphinx-shibuya-for-documentation.md)) and already owns the release
lifecycle via `release.yml`
([ADR-002](002-release-please-for-release-automation.md)), so both features slot
onto existing machinery rather than introducing new infrastructure.

The upstream implementations these were drawn from, however, carry
organization-specific weight this template must shed:

- Their docs preview **deploys to a *separate* repository** authenticated with a
  **GitHub App token** (`CLIENT_ID`/`CLIENT_PRIVATE_KEY`). That is a second repo +
  App to provision — incompatible with the self-contained default.
- Their released-issue notifier shells out to a **committed Python script +
  `notify.js`** invoked from a `workflow_call`, which is more moving parts than a
  generated single-maintainer project needs.

## Decision

Adopt both, **always included** (no new toggle), but re-implemented to be fully
self-contained and to fit the template's existing conventions.

### 1. PR docs preview — same-repo `gh-pages` subfolder, no second repo, no App

A new single-job `docs-preview.yml` workflow, triggered by `pull_request`
(`types: [opened, synchronize, reopened, closed]`), builds the Sphinx HTML and
hands the whole preview lifecycle to a purpose-built action
(`rossjrw/pr-preview-action`) run with `action: auto`: it **deploys** the built
HTML to a `pr-preview/pr-<N>/` subfolder of the project's **own** `gh-pages`
branch on open/synchronize/reopen and **removes** that subfolder on close, and
maintains a single sticky preview-URL comment throughout. It authenticates from
`GITHUB_TOKEN` — no App, no `SONAR_TOKEN`-style secret, no second repo, and no
hand-rolled `gh-pages` git surgery (which is exactly what the released-docs
deploy already delegates to `JamesIves/github-pages-deploy-action`).

**Same-repo only, by design.** The workflow is guarded by
`if: github.event.pull_request.head.repo.full_name == github.repository`, so it
runs only for branches pushed to the repo itself, where the `pull_request`
`GITHUB_TOKEN` carries write access. Fork PRs receive a read-only token and are
**skipped cleanly** (no red ✗, no attempt to deploy) rather than failing. This
is a deliberate, safe simplification over the more elaborate
`workflow_run`/`pull_request_target` split: because untrusted fork code is never
run with a write token, plain `pull_request` needs no `dangerous-triggers`
ignore. Fork-PR previews are a known gap — the action gains fork support in its
upcoming v2, at which point this workflow can adopt the `workflow_run` recipe
without changing the template's contract. For a solo-maintainer template whose
day-to-day PRs come from same-repo branches, same-repo coverage is the 95% case.

**Why the purpose-built action over hand-rolling with `JamesIves`.** Deploying
docs to a subfolder is one `JamesIves` call, but *removing* a subfolder on PR
close and maintaining a sticky comment are not — they would mean hand-rolled git
on `gh-pages`, precisely the surface the repo deliberately moved *away* from when
it replaced `git remote set-url` + `ghp-import` with `JamesIves`. A single
SHA-pinned, Renovate-tracked action that owns deploy + remove + comment is less
bespoke logic, not more.

**Why not artifact-only:** uploading the HTML as a bare CI artifact (no deploy)
is simpler but forces every reviewer to download-and-unzip to view rendered
docs. A live URL is the whole value of the feature; the same-repo subfolder gets
it without the separate-repo/App provisioning cost.

**Degradation:** the preview publishes to `gh-pages`, which the template already
uses for released docs (`release.yml` `deploy-docs` publishes to the repo
*root*; previews live under `pr-preview/`, a disjoint path, so they never
collide). If GitHub Pages is not enabled on the repo the deploy step fails only
on that PR — the workflow is not wired into the `check` aggregation gate, so it
never blocks a merge.

### 2. Released-issue notifications — one job in `release.yml`

Add a `notify-released-issues` job to `release.yml`, gated on
`needs.release-please.outputs.release_created == 'true'` and running after
`finalize-release` (so it fires only on a real, un-drafted release). It uses a
single `actions/github-script` step (no committed Python/JS files) to find the
issues closed by the release and comment the release tag/URL on each, reading the
`tag_name`/`version` outputs already exposed by the `release-please` job.

Keeping it inline in `release.yml` (rather than a separate
`workflow_call` file) matches this template's decision to keep the whole release
lifecycle in one workflow ([ADR-002](002-release-please-for-release-automation.md),
which folded `cd.yml` into `release.yml`).

### Why always-on rather than a toggle

Both are zero-config for the project owner and cause no failure when the
surrounding feature is unused (no open PRs → no preview; no closed issues → no
notification). They mirror the always-on, no-toggle community-health items
(`issue-manager`, `stale`, Codecov). Neither depends on an external account, so
neither compromises the self-contained default that
[ADR-009](009-optional-external-quality-community-integrations.md) protects — the
reason those integrations are toggles and these two are not.

## Consequences

- A new `docs-preview.yml` workflow is added, triggered by `pull_request`
  (`opened`/`synchronize`/`reopened`/`closed`), single job, guarded to same-repo
  PRs. It builds the docs (skipping the build on `closed`, which only removes the
  preview) and runs `rossjrw/pr-preview-action` with `action: auto`. It is
  least-privilege (`permissions: {}` top-level; `contents: write` +
  `pull-requests: write` on the one job), `persist-credentials: false`,
  SHA-pinned actions, per-job `timeout-minutes` — i.e. it must pass the same
  zizmor/ghalint gate as every other workflow. Plain `pull_request` (not
  `pull_request_target`) means **no `dangerous-triggers` ignore is needed**. It
  is *not* wired into the `check` aggregation gate — a preview is best-effort,
  not merge-blocking. `ci.yml` is left unchanged.
- `release.yml.jinja` gains a `notify-released-issues` job gated on
  `release_created` and `needs: finalize-release`, using inline `github-script`
  (no new committed scripts).
- No new `copier.yml` variable — both features are always rendered.
- Docs previews and released docs share the `gh-pages` branch on **disjoint
  paths** (`pr-preview/**` vs. root). The released-docs deploys
  (`release.yml` `deploy-docs` and the manual `gh-pages.yml`) use
  `JamesIves/github-pages-deploy-action`, whose default `clean: true` would wipe
  the `pr-preview/` tree on every release; both therefore gain
  `clean-exclude: pr-preview/**` so live previews survive a release deploy. They
  also set `force: false` so the action merges rather than force-pushing
  `gh-pages` — otherwise a root-docs deploy racing a concurrent preview deploy
  could overwrite the preview's commit. The preview action deploys only into
  `pr-preview/pr-<N>/` and preserves siblings, so it never touches the root docs.
- `CONTRIBUTING.md.jinja` notes that PR docs previews require **GitHub Pages
  enabled** on the repo (already implied by the released-docs deploy), so no new
  provisioning beyond what released docs already need.
- CLAUDE.md's CI/CD Workflows section documents the new `docs-preview.yml` and
  the `notify-released-issues` job.
- Testing: generate a project and confirm both workflows render, pass
  `prek run zizmor --all-files` and ghalint, and that `pr-preview/` paths do not
  collide with the root docs deploy.
