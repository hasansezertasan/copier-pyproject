# ADR-015: Automated downstream `copier update` via Renovate's copier manager

## Status

Accepted (2026-08). Prompted by
[hwid#113](https://github.com/hasansezertasan/hwid/pull/113) — a fully
hand-driven `copier update` that pinned raw commit SHAs because downstream repos
had no signal that a template update existed.

## Context

Copier ships the propagation mechanism: every generated project carries a
`.copier-answers.yml` recording the template revision it was built from
(`_commit`), and `copier update` re-renders the newer template over the project
with a git 3-way merge. hwid#113 is exactly that, run by hand. Two gaps kept it
manual:

1. Nothing in a generated project **watched for or pulled** template changes.
2. `copier update` defaults to the template's latest **git tag**, and the
   template published none — so a default run found nothing.

The template **already ships and documents [Renovate](https://docs.renovatebot.com/)**
as the canonical updater for everything else (deps, GitHub Action digests, prek
hook `rev`s). Renovate has a first-party
[`copier` manager](https://docs.renovatebot.com/modules/manager/copier/): it
detects `.copier-answers.yml`, and when the template has a newer version it runs
the real `copier update` (an `updateArtifacts` step) and opens a PR with the
re-rendered diff.

## Decision

**Use Renovate's copier manager for downstream template updates.** No bespoke
workflow ships to generated projects. Two supporting changes make the manager
work with this template:

1. **Keep the template's own release-please** (the root-level
   `.github/release-please-config.json`, its manifest, and `release.yml`) as the
   **tag source**. Renovate's
   copier manager uses the `git-tags` datasource with `pep440` versioning — it
   detects updates from **version tags**, not the default-branch HEAD — so the
   template must publish tags. release-please already produces them from the
   Conventional Commits landing on `main` (see the *self-versioning* note in
   `CLAUDE.md`). A generated project's Renovate reads `_src_path` from
   `.copier-answers.yml`, watches that repo's tags, and bumps `_commit`.

   This only works when `_src_path` is a **real git URL**. Copier records
   `_src_path` verbatim from the `copier copy` argument, and the
   `gh:hasansezertasan/copier-pyproject` shorthand is Copier-only — it is not a
   valid git URL, so Renovate's `git-tags` datasource rejects it (`Attempting to
   use non-git url for git operations` → `no-result`) and never opens an update
   PR, even though the template has tags. Renovate accepts `_src_path` only when
   it starts with `git+https://`, `git+ssh://`, `git@`, or `git://`, or ends with
   `.git`. Scaffold with the `.git` HTTPS URL
   (`https://github.com/hasansezertasan/copier-pyproject.git`); the README
   scaffold step and the `copier-pyproject:adopt` skill both use it for this
   reason. Existing projects that were scaffolded with the `gh:` shorthand can be
   fixed by rewriting the `_src_path` line — `copier update` re-reads and
   preserves it.
2. **Define no `_tasks` in `copier.yml`.** Any task marks a template "unsafe",
   forcing `copier ... --trust`; `--trust` is gated behind Renovate's
   `allowScripts`, a **self-hosted-only** setting that the **hosted Mend Renovate
   App disables**. A task-bearing template would therefore make the hosted App's
   `copier update` fail with `UnsafeTemplateError`. Dropping the former
   `_tasks: git init` keeps the template updatable by the hosted App; the cost is
   that the initial `copier copy` no longer auto-inits git, so the scaffold
   instructions (README, generated `CONTRIBUTING.md`) tell the user to run
   `git init`.

The copier manager is enabled by default (Renovate sets no `enabledManagers`
restriction in the shared preset chain), so generated projects get it for free
via the `.copier-answers.yml` they already ship — no addition to the template's
`renovate.json`. Renovate authenticates as its **GitHub App**, whose token *can*
push changes to `.github/workflows/*` (unlike the repo `GITHUB_TOKEN`), and its
PRs flow through the same dashboard, labels, and review as every other update.

### Known limitation: conflict PRs can land "green"

When a consumer has diverged from the template, `copier update`'s 3-way merge
emits conflict markers (or `.rej` files). Renovate currently does **not** fail its
artifacts check on such conflicts
([renovate#31600](https://github.com/renovatebot/renovate/issues/31600)), so a
copier-update PR can appear mergeable while carrying `<<<<<<<` markers. This is
inherent to `copier update` (any runner surfaces the same conflicts), not unique
to Renovate. The generated `CONTRIBUTING.md` "Template updates" note tells
maintainers to review these PRs for conflict markers before merging, and to lean
on the `copier-pyproject:update` reconciliation workflow.

## Considered and rejected

- **A bespoke `copier-update.yml` workflow** (weekly `copier update
  --vcs-ref=HEAD` + `create-pull-request`). It works and can track HEAD tag-free,
  but it is ~50 lines of security-sensitive YAML in every generated project
  (`--trust`/`--skip-tasks`, a write token, draft PRs), and its default
  `GITHUB_TOKEN` **cannot push `.github/workflows/*`** (a hard GitHub rule),
  forcing every consumer to provision a `COPIER_UPDATE_TOKEN` PAT for the common
  case. Renovate's App token has no such limitation and adds no per-repo YAML or
  secret. Reinventing Renovate's job — when the template already depends on
  Renovate — was not worth it.
- **[`fohte/copier-update-action`](https://github.com/fohte/copier-update-action)**
  — essentially the bespoke workflow packaged as a third-party action. Same
  token/conflict characteristics, plus an external action to trust with `--trust`
  and a token and to SHA-pin. No advantage over Renovate here.
- **Dropping the template's own versioning entirely** (HEAD-tracking). Attractive
  for simplicity, but the copier manager is tag-based, so keeping release-please
  is the price of using Renovate. The tags are cheap (release-please already runs)
  and give external adopters a changelog besides.

## Consequences

- **Positive.** One update mechanism for the whole generated project; no bespoke
  workflow, no per-repo update token, no `--trust` execution surface. Every
  generated project inherits it via its existing `.copier-answers.yml` +
  Renovate config.
- **Requires the Renovate App** (already a documented one-time setup, and the
  canonical updater here) and **the template to publish tags** (release-please,
  already present).
- **Initial scaffold is not auto-git-init'd** — documented as a one-line manual
  step.
- **Conflict PRs need human review** (renovate#31600) — documented.
- **Bootstrapping (one-time).** Existing generated repos start receiving
  Renovate copier PRs once (a) the Renovate App is installed and (b) the template
  has at least one tag newer than their recorded `_commit`. A repo pinned to a raw
  SHA (pre-tag, like hwid) needs one manual `copier update` to re-anchor onto a
  tagged revision first.
