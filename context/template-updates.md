# Template versioning and downstream updates

## Renovate's copier manager delivers downstream updates; the template keeps release-please as its tag source

**Id:** f26da4b3-8b97-4cfc-9aba-64eba4acf04f
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-015 ([`docs/adr/015-template-self-versioning-and-copier-update-automation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/015-template-self-versioning-and-copier-update-automation.md)); prompted by [hwid#113](https://github.com/hasansezertasan/hwid/pull/113)
**Revisit when:** Renovate fails its artifacts check on conflict markers ([renovate#31600](https://github.com/renovatebot/renovate/issues/31600)), or the copier manager accepts Copier's `gh:` shorthand
**See:** release-automation.md#release-please-is-the-sole-release-orchestrator — 7ec8a937-fd4d-41f2-96b7-824fe3be913b — as of 2026-10-11
**See:** template-updates.md#copieryml-defines-no-_tasks — 86130379-1660-4992-8aba-8b6cd7b4a9f7 — as of 2026-10-11

Generated projects receive template updates through Renovate's first-party
[`copier` manager](https://docs.renovatebot.com/modules/manager/copier/), which
watches the template's git tags, runs the real
`copier update` and opens a PR. No bespoke workflow ships. This repository's
own release-please therefore must keep cutting tags — they are the datasource.
Scaffolding uses the `.git` HTTPS URL because the `gh:` shorthand is not a git
URL and the `git-tags` datasource rejects it silently.

**Reason:** nothing in a generated project watched for template changes and the
template published no tags, so a default `copier update` found nothing. The
template already ships Renovate as the canonical updater; its App token can
push workflow files (the repo `GITHUB_TOKEN` cannot), and its PRs flow through
the existing dashboard and review. Tags are cheap since release-please already
runs and give adopters a changelog besides.

**Rejected alternative:** a bespoke `copier-update.yml` workflow — ~50 lines of
security-sensitive YAML per project, and its default token cannot push
`.github/workflows/*`, forcing every consumer to provision a PAT.

**Rejected alternative:** `fohte/copier-update-action` — the bespoke workflow as
a third-party action, same token and conflict characteristics, plus an external
action to trust with `--trust`.

**Rejected alternative:** drop the template's own versioning and track HEAD —
the copier manager is tag-based, so release-please is the price of Renovate.

**Consequence:** a copier-update PR can look mergeable while carrying conflict
markers; maintainers review for them. A repo pinned to a raw SHA needs one
manual update to re-anchor onto a tag. Existing repos start receiving copier PRs
once the Renovate App is installed and the template has a tag newer than their
recorded `_commit`.

**`_src_path` must be a real git URL.** Copier records `_src_path` verbatim
from the `copier copy` argument, and the `gh:` shorthand is Copier-only, so
Renovate's `git-tags` datasource rejects it ("non-git url", then `no-result`)
and never opens an update PR even though the template has tags. Renovate accepts
`_src_path` only when it starts with `git+https://`, `git+ssh://`, `git@` or
`git://`, or ends with `.git`, which is why the README scaffold step and the
setup guide's adoption section use the `.git` HTTPS URL. A project scaffolded with
`gh:` can be fixed by rewriting the `_src_path` line; `copier update` preserves
it. The manager is enabled by default (the shared preset sets no
`enabledManagers`), so the template's own `renovate.json` needs no addition.

## `copier.yml` defines no `_tasks`

**Id:** 86130379-1660-4992-8aba-8b6cd7b4a9f7
**Type:** decision
**Type:** constraint
**Status:** active
**Evidence:** confirmed
**Source:** ADR-015 ([`docs/adr/015-template-self-versioning-and-copier-update-automation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/015-template-self-versioning-and-copier-update-automation.md)); the constraint is re-affirmed in ADR-018, ADR-023, ADR-024 and ADR-035
**Revisit when:** the hosted Renovate App allows `--trust`, or Copier marks tasks safe
**See:** template-updates.md#renovates-copier-manager-delivers-downstream-updates-the-template-keeps-release-please-as-its-tag-source — f26da4b3-8b97-4cfc-9aba-64eba4acf04f — as of 2026-10-11

The template has no post-copy tasks; the former `git init` task is gone and
the scaffold instructions tell the adopter to run it. Every later feature that
needs a post-render step (the render harness; formerly the repo-setup skill and the
ai-rulez generator) is a rendered file or a documented command, never a task.

**Reason:** any task marks a template unsafe and forces `--trust`, which
Renovate gates behind a self-hosted-only setting the hosted App disables — a
task-bearing template makes the hosted App's `copier update` fail.

**Rejected alternative:** keep the `git init` task — breaks the update path for
every hosted-Renovate adopter.

## Shipped `template/**` pins are frozen from this repository's Renovate

**Id:** 86e0af71-9614-42c1-9363-d16170d942a8
**Type:** decision
**Type:** constraint
**Status:** active
**Evidence:** confirmed
**Source:** ADR-020 ([`docs/adr/020-freeze-shipped-template-pins-from-renovate.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/020-freeze-shipped-template-pins-from-renovate.md)); the confirmed conflict source was [PR #196](https://github.com/hasansezertasan/copier-pyproject/pull/196)
**Revisit when:** seed staleness becomes a security concern faster than downstream Renovate catches up, or Renovate learns to skip lines the downstream already moved
**See:** template-updates.md#renovates-copier-manager-delivers-downstream-updates-the-template-keeps-release-please-as-its-tag-source — f26da4b3-8b97-4cfc-9aba-64eba4acf04f — as of 2026-10-11

A `packageRules` entry in `.github/renovate.json` matches `template/**` and
disables updates there. Shipped version literals (action SHAs, prek `rev` pins,
mise tool versions, dependency pins) are seed values only; each generated
project's own Renovate owns them afterwards. This repository's root workflows,
`prek.toml` and `mise.toml` stay Renovate-managed.

**Reason:** `copier update` is a 3-way merge per file, and a pinned line
conflicts when both sides moved it to different values. Both repositories'
bots advanced the same literals on independent schedules, so copier-update PRs
conflicted on nearly every release — and Renovate does not fail on those
conflicts, so a PR looked mergeable with markers inside. With the template
frozen, "theirs" equals "base" on every pin line and the downstream's value
wins cleanly: the conflict class is eliminated structurally. `matchFileNames`
plus `enabled: false` rather than `ignorePaths` preserves the shared preset's
own ignore list and composes with its digest-pinning policy. The confirmed conflict source was the
plain `template/*.yml` workflow files; the `.jinja`-suffixed files are not
matched by Renovate's stock managers, so freezing them is a safe no-op unless
the shared preset's custom managers are extended to reach them.

**Rejected alternative:** auto-resolve in the downstream's favour via a
`merge=ours` driver or copier `_exclude` — `_exclude` is whole-file and would
block genuine template changes; a per-downstream merge driver is fragile.

**Rejected alternative:** converge by cadence (group bumps, release
immediately) — only shrinks the race window.

**Consequence:** new projects start with slightly stale but valid seeds and
their own Renovate opens catch-up PRs; refreshing seeds before a release is a
deliberate act that reintroduces conflicts for projects not yet caught up.
Re-enabling Renovate for `template/**` reads as fixing staleness but rebuilds
the conflict engine.

## Retired template modules become adopter-owned

**Id:** 4dd6729a-697e-4588-a7a7-d37152018b6b
**Type:** decision
**Type:** constraint
**Status:** active
**Evidence:** confirmed
**Source:** [PR #333](https://github.com/hasansezertasan/copier-pyproject/pull/333), [version-sweep results](https://github.com/hasansezertasan/copier-pyproject/pull/333#issuecomment-5932489770); commits [c150ec3](https://github.com/hasansezertasan/copier-pyproject/commit/c150ec30519c1e1ddcc3fb05ffc7ea3ba4e85709) and [0f7a406](https://github.com/hasansezertasan/copier-pyproject/commit/0f7a4062c251828f00fb27f91d8648d13d4e339d)
**Verification:** corroborated — `copier.yml` excludes the retired paths and requires Copier 9.10.3; the update skill records the same compatibility floor
**Revisit when:** Copier changes update-deletion semantics or a retired module is rendered again
**See:** components.md#one-application-payload-in-coreapppy-components-are-adapters-over-it — 8bb1e55e-f468-44fc-80a5-d3b3719e5ddc — as of 2026-10-11

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

The architectural reason for retiring the placeholders is the shared
application payload entry in `components.md`; this entry records the distinct
ownership and update-safety constraint.

## Adoption audits preserve behavior before consolidating workflows

**Id:** dfd6cd98-9d07-4dc4-b58f-d1343d636ea4
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** [issue #348](https://github.com/hasansezertasan/copier-pyproject/issues/348), [PR #349](https://github.com/hasansezertasan/copier-pyproject/pull/349); commit [0abcffc](https://github.com/hasansezertasan/copier-pyproject/commit/0abcffc525ed4a558ecb80649a1b6e9a231c5ff5); `docs/template-adoption.md`
**Verification:** corroborated — the adoption and update sections of the generated `REPOSITORY_SETUP.rst` (formerly a shipped skill) compare behavior and preserve customizations; the older update skill now shares that contract
**Revisit when:** the adoption and update skills change their reconciliation contract
**See:** repo-setup.md#a-resume-driven-repo-setup-skill-reads-check-blocks-from-the-setup-doc-no-separate-manifest — 68ac4665-dcde-456b-aef7-2faaf6fe51f4 — as of 2026-10-11

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

The execution procedure is the "Adopting into an existing project" section of the generated `REPOSITORY_SETUP.rst`.

## Which reconciliation policy governs machine-config and CI conflicts?

**Id:** 3f155d92-8518-4294-bfcd-26251c36e2e1
**Type:** constraint
**Status:** superseded
**Evidence:** unknown
**Source:** `skills/update/SKILL.md`, Shared reconciliation; the formerly shipped `template-adoption` skill (now `REPOSITORY_SETUP.rst`); [PR #349](https://github.com/hasansezertasan/copier-pyproject/pull/349)
**Verification:** uncorroborated — the original justification for category-based precedence could not be established; the conflicting wording found during recovery has since been replaced
**See:** template-updates.md#adoption-audits-preserve-behavior-before-consolidating-workflows — dfd6cd98-9d07-4dc4-b58f-d1343d636ea4 — as of 2026-10-08
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
**Status:** superseded
**Evidence:** confirmed
**Source:** maintainer-approved reconciliation-policy review, 2026-10-08; the former `docs/template-adoption.md` (now `REPOSITORY_SETUP.rst`); `skills/update/SKILL.md`
**Verification:** corroborated — the older update skill now preserves custom behavior, requires evidence for equivalence, and delegates repository-settings transitions to `repo-setup`
**Revisit when:** either skill changes its scope or introduces a conflicting reconciliation policy
**Superseded by:** e4cd1c46-28c3-4241-82c8-d5aac41c293f
**See:** template-updates.md#adoption-audits-preserve-behavior-before-consolidating-workflows — dfd6cd98-9d07-4dc4-b58f-d1343d636ea4 — as of 2026-10-08

Superseded on 2026-10-12 by [the companion-skill retirement decision](companion-skills.md#every-lifecycle-skill-ships-through-the-template).
The preservation-first contract now lives in the generated `REPOSITORY_SETUP.rst`;
the separate root `skills/update` delivery surface is retired.

At the time of this decision, both skills used the same preservation-first contract.
The older update skill ran or reconciled updates; the generated adoption skill additionally handled
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

## The LICENSE start year is a visible `copyright_year` question

**Id:** 4ecf9da8-3879-40c8-9a46-85f5cfc3bfc5
**Type:** decision
**Type:** constraint
**Status:** active
**Evidence:** confirmed
**Source:** empirical runs against Copier 9.18.2 (copy, update and recopy with a faked clock)
**Verification:** corroborated — `tests/test_license.py` pins the recorded answer, the stability across `copier update` and the existing-project path
**Revisit when:** Copier exposes the copy-versus-update operation to question defaults, or removes the `strftime` filter

`LICENSE` renders `Copyright (c) <copyright_year>-present`. `copyright_year` is
an asked `int` question defaulting to the current year (`'%Y' | strftime`), so
Copier records it in `.copier-answers.yml` and every later `copier update` keeps
the creation year.

**Reason:** Copier writes only asked questions to the answers file; a
`when: false` default is not recorded and is re-evaluated on each run. A hidden
or inline current-year expression only looks stable on update, because the
three-way merge re-renders the old side with the same clock: it conflicts when a
neighbouring line changes, and `copier recopy` or any re-render at the recorded
commit rewrites the year.

**Rejected alternative:** hard-coding `2025`. It is the bug: every later project
claims a year it did not start in.

**Rejected alternative:** a `when: false` default, or `{{ now().year }}` inline.
Not recorded, so not stable (above). `now` is also a deprecated Copier builtin
that warns it will be removed; the `strftime` filter is the supported spelling.

**Consequence:** a project scaffolded before this question has no answer and an
existing `2025-present`. Copier's question defaults cannot see whether the run is
a copy or an update (`_copier_operation` exists only for tasks and exclusions),
so a non-interactive update (Renovate) adopts the current year and rewrites that
line. An interactive update prompts, and `-d copyright_year=<year>` keeps the
original; `_message_after_update` says so. No default avoids this without
leaving the bug in new projects.
