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

## Retired template modules become adopter-owned

**Id:** 4dd6729a-697e-4588-a7a7-d37152018b6b
**Type:** decision
**Type:** constraint
**Status:** active
**Evidence:** confirmed
**Source:** [PR #333](https://github.com/hasansezertasan/copier-pyproject/pull/333), [version-sweep results](https://github.com/hasansezertasan/copier-pyproject/pull/333#issuecomment-5932489770); commits [c150ec3](https://github.com/hasansezertasan/copier-pyproject/commit/c150ec30519c1e1ddcc3fb05ffc7ea3ba4e85709) and [0f7a406](https://github.com/hasansezertasan/copier-pyproject/commit/0f7a4062c251828f00fb27f91d8648d13d4e339d)
**Verification:** corroborated — `copier.yml` excludes the retired paths and requires Copier 9.10.3; the update skill records the same compatibility floor
**Revisit when:** Copier changes update-deletion semantics or a retired module is rendered again

The dropped `utils/app.py` and library-only `core/app.py` placeholders are
excluded from updates, leaving existing copies under the adopter's ownership.
The custom exclusion list explicitly retains Copier's default exclusions because
`_exclude` replaces that list rather than extending it.

**Reason:** an adopter can have replaced a placeholder with real application
code. Removing the template file can delete that edited copy without conflict
markers or reject files, so ordinary conflict review cannot catch the loss.
The recorded version sweep found that Copier 9.6.0–9.10.2 still deleted the
excluded files; 9.10.3 and later preserved them. The version floor makes an older
Copier refuse the update instead of silently deleting adopter code.

**Rejected alternative:** let normal template deletion remove the old modules.
Rejected because the files may no longer be empty placeholders in the adopter.

**Rejected alternative:** use exclusions without raising the Copier minimum.
Rejected because the version sweep showed the protection was ineffective on
older supported versions.

The architectural reason for retiring the placeholders remains in
[ADR-033](033-shared-app-service-components-as-adapters.md); this entry records
the distinct ownership and update-safety constraint.

## Adoption audits preserve behavior before consolidating workflows

**Id:** dfd6cd98-9d07-4dc4-b58f-d1343d636ea4
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** [issue #348](https://github.com/hasansezertasan/copier-pyproject/issues/348), [PR #349](https://github.com/hasansezertasan/copier-pyproject/pull/349); commit [0abcffc](https://github.com/hasansezertasan/copier-pyproject/commit/0abcffc525ed4a558ecb80649a1b6e9a231c5ff5); `docs/template-adoption.md`
**Verification:** corroborated — the shipped `template-adoption` skill and its walkthrough compare behavior and preserve customizations; the older update skill now shares that contract
**Revisit when:** the adoption and update skills change their reconciliation contract

The shipped adoption skill treats template defaults as evidence to compare with
existing project behavior, rather than automatic authority to replace it.
It handles initial adoption, updates, and audits of already-committed updates;
repository-settings changes remain the responsibility of `repo-setup`.

**Reason:** two workflows that both run prek can differ in event coverage and
required-check identity. Consolidating them can discard manual dispatch or leave
live branch protection waiting for a check that no longer exists. A local
ruleset file alone cannot establish the live requirements. A post-update audit
can compare the actual committed baseline and diff without rerunning Copier and
disturbing the state being inspected.

**Alternatives considered:** retain both workflows, accepting duplicate PR
execution, or consolidate after preserving event coverage and transitioning the
required check. The documented walkthrough deliberately makes that choice
conditional on the adopter's decision and evidence; neither option is rejected
universally. Deletion without establishing equivalence is excluded because it
can silently remove functionality or block merges.

The execution procedure is in [the adoption guide](../template-adoption.md),
and the repository-settings boundary is in
[ADR-023](023-repo-setup-skill.md).

## Which reconciliation policy governs machine-config and CI conflicts?

**Id:** 3f155d92-8518-4294-bfcd-26251c36e2e1
**Type:** constraint
**Status:** superseded
**Evidence:** unknown
**Source:** `skills/update/SKILL.md`, Shared reconciliation; the shipped `template-adoption` skill; [PR #349](https://github.com/hasansezertasan/copier-pyproject/pull/349)
**Verification:** uncorroborated — the original justification for category-based precedence could not be established; the conflicting wording found during recovery has since been replaced
**See:** 015-template-self-versioning-and-copier-update-automation.md#adoption-audits-preserve-behavior-before-consolidating-workflows — dfd6cd98-9d07-4dc4-b58f-d1343d636ea4 — as of 2026-10-08
**Superseded by:** 9a6bf00c-33c1-4f0c-962e-7e960f9d2d58

At recovery, the two skills coexisted with conflicting guidance: the older
update skill selected template-side CI/config hunks by category, while the newer
adoption skill required behavioral preservation and decisions before
consequential cleanup. The reviewed historical sources did not establish which
policy governed their overlap or justify the older precedence rule.

The question has been resolved by the current decision below, rather than by
claiming to have recovered the original justification.

## Update and adoption skills share preservation-first reconciliation

**Id:** 9a6bf00c-33c1-4f0c-962e-7e960f9d2d58
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** maintainer-approved reconciliation-policy review, 2026-10-08; `docs/template-adoption.md`; `skills/update/SKILL.md`
**Verification:** corroborated — the older update skill now preserves custom behavior, requires evidence for equivalence, and delegates repository-settings transitions to `repo-setup`
**Revisit when:** either skill changes its scope or introduces a conflicting reconciliation policy
**See:** 015-template-self-versioning-and-copier-update-automation.md#adoption-audits-preserve-behavior-before-consolidating-workflows — dfd6cd98-9d07-4dc4-b58f-d1343d636ea4 — as of 2026-10-08

Both skills use the same preservation-first contract. The older update skill
runs or reconciles updates; the generated adoption skill additionally handles
initial adoption and audits of completed updates. Those workflow differences do
not justify opposite advice about the same project customization.

**Reason:** file category does not establish behavioral equivalence. CI and
machine configuration can encode adopter-specific event coverage, permissions,
required-check identity, hooks, and dependencies. Replacing a hunk on the basis
of its category can discard functioning customizations despite a green lint run.
Routine maintenance can proceed directly when equivalence is established within
the requested update; consequential behavior changes need an explicit decision.

The contract applies to clean merges as well as conflicts. Recovery uses the
actual pre-update snapshot and preserves later edits: a current base branch can
lack branch-owned release history, while the index may already hold the reset.

**Rejected alternative:** retain automatic template precedence for CI/config
hunks. It gives template origin more authority than evidence of the adopter's
existing behavior. Even action digest updates require checking release effects
and preserving configured inputs rather than assuming equivalence from the SHA.

Repository-settings transitions remain with `repo-setup`; the reconciliation
procedure is in the skills, not duplicated here. The former policy's historical
justification remains unknown in the superseded record above.
