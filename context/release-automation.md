# Release automation

## release-please is the sole release orchestrator

**Id:** 7ec8a937-fd4d-41f2-96b7-824fe3be913b
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-002 ([`docs/adr/002-release-please-for-release-automation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/002-release-please-for-release-automation.md)); validated against the keycast release pipeline ([keycast#11](https://github.com/hasansezertasan/keycast/pull/11))
**Revisit when:** the open re-evaluation below is decided, or the generated project's version stops being sourced from git tags
**See:** release-automation.md#the-release-automation-choice-is-under-re-evaluation — d9131d49-3c27-48f8-a903-e97caf4acff6 — as of 2026-10-11
**See:** package-distribution.md#optional-pypi-publishing — 20be7463-ca95-4d01-82c9-71f632d1b4be — as of 2026-10-12

Every generated project ships an unconditional release-please pipeline in one
unified `release.yml`: Conventional Commits on `main` open a release PR, its
merge cuts the tag and release, and every downstream job (build, PyPI — optional
since ADR-039 —, executables, Docker, docs, SBOM, notifications) gates on its
outputs. The
former `release_automation` choice (`none`, release-please, release-it,
release-drafter) and the separate `cd.yml` are gone. Versioning is sourced from
git tags through hatch-vcs, so release-please never edits a version literal and
`uv.lock` cannot desync; `bump-minor-pre-major` keeps pre-1.0 projects pre-1.0.

**Reason:** offering three tools multiplied the integration surface for a
feature each project configures once. release-please is Python-native, derives
the version from commits the template already enforces, and produces a
reviewable release PR before any tag exists. Two of the three hard-won keycast
fixes were already in the template, so it was the option with the most
evidence.

**Rejected alternative:** release-it — JS-oriented, needs a Node runtime, and a
human picks the bump every time.

**Rejected alternative:** release-drafter — label-driven, writes release notes
but no `CHANGELOG.md`.

**Rejected alternative:** keeping a `none` escape hatch — projects that want no
automation delete the files after generation; accepted for a template whose
audience publishes releases.

**Consequence:** the PyPI trusted publisher must register `release.yml` as the
workflow. Rendering plus actionlint validate the workflow across option
combinations, but draft-tag timing, OIDC publishing and reconciliation can only
be exercised by a live release. The template has no `CHANGELOG.md` seed file:
release-please owns the changelog, and a scaffold-time seed would wipe an
adopting project's release history on update.

## The release is created as a draft, finalized after artifacts attach

**Id:** 398b3cd9-e57b-4856-b2c7-76752c0ec37f
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-002 ([`docs/adr/002-release-please-for-release-automation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/002-release-please-for-release-automation.md)); the wrong-version bug caught in [cobo#49](https://github.com/hasansezertasan/cobo/pull/49)
**Revisit when:** release-please creates releases after artifact upload natively, or computes its commit range from drafts
**See:** release-automation.md#release-please-is-the-sole-release-orchestrator — 7ec8a937-fd4d-41f2-96b7-824fe3be913b — as of 2026-10-11

release-please creates the GitHub release with `draft: true` and
`force-tag-creation: true`. Build jobs attach wheels, executables and the SBOM
to the draft; `finalize-release` un-drafts it and then closes the phantom
next-release PR and re-dispatches the workflow, bounded.

**Reason:** a public release must never exist without its artifacts, so the
release stays a draft until they are attached. GitHub withholds a draft's git
tag until publication, so without forced tag creation the build job would run
before the tag exists and hatch-vcs would stamp the previous version. The
phantom PR exists because release-please computes its commit range from the
latest *published* release and ignores drafts.

**Rejected alternative:** `draft: false` — a window with a public release and no
artifacts.

**Consequence:** docs deployment lives in the same workflow (`deploy-docs`,
after finalization) because an event fired by `finalize-release`'s token cannot
trigger a separate workflow.

## The `workflow_dispatch` trigger on `release.yml` stays; the `publish` environment is the containment

**Id:** 0d93a35d-46a3-4ac6-b072-fc07da789842
**Type:** decision
**Type:** constraint
**Status:** active
**Evidence:** confirmed
**Source:** ADR-002 ([`docs/adr/002-release-please-for-release-automation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/002-release-please-for-release-automation.md))
**Revisit when:** the GitHub API for re-running a workflow stops requiring the dispatch trigger, or environment deployment-branch policies change
**See:** release-automation.md#the-release-is-created-as-a-draft-finalized-after-artifacts-attach — 398b3cd9-e57b-4856-b2c7-76752c0ec37f — as of 2026-10-11
**See:** supply-chain-security.md#provenance-minting-shares-the-protected-publication-boundary — a0396603-cb34-4151-9d5b-1fc77eb31f6e — as of 2026-10-11

`release.yml` keeps `workflow_dispatch`. The publish jobs run in a `publish`
environment whose deployment-branch policy is limited to `main`; the generated
setup guide ships that policy as a scriptable step with a check, because GitHub
auto-creates the environment unprotected on first use.

**Reason:** the trigger looks like a publish-escalation surface — a manual run
executes the workflow file from the selected branch, so the `release_created`
guard cannot stop someone with write access from dispatching a guard-free copy
and minting a trusted-publishing token. But `finalize-release`'s reconciliation
re-dispatches the workflow through the API, which requires the trigger.
GitHub evaluates an environment's branch policy outside the workflow file, so
the environment contains what the trigger exposes.

**Rejected alternative:** remove the trigger — breaks release-PR reconciliation.

## Release workflows use `GITHUB_TOKEN`, with two documented manual workarounds

**Id:** bc96b93e-9b9e-4496-8fbb-b215f1d9a04c
**Type:** decision
**Type:** workaround
**Status:** active
**Evidence:** confirmed
**Source:** ADR-002 ([`docs/adr/002-release-please-for-release-automation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/002-release-please-for-release-automation.md)); [issue #332](https://github.com/hasansezertasan/copier-pyproject/issues/332)
**Revisit when:** GitHub lets the workflow token start workflow runs or grants it workflow write access
**See:** release-automation.md#release-please-is-the-sole-release-orchestrator — 7ec8a937-fd4d-41f2-96b7-824fe3be913b — as of 2026-10-11

Release-please runs with the implicit `GITHUB_TOKEN`. Two consequences are
handled procedurally in the generated setup guide rather than with a stronger
credential: the release PR reports no required status contexts until a human
closes and reopens it, and a merge that changes workflow files between the
release PR merging and the release run finishing must wait, because the
release API then refuses tag creation with a 403.

**Reason:** events created with the workflow token do not start workflow runs,
and the token cannot be granted workflow write access. A PAT or App token would
fix both but is a standing credential with write access to `main`; closing and
reopening the PR (every required context listens for `reopened`) and pausing
workflow merges are the cheaper side of that trade. Editing the PR body is not
equivalent — two of the checks do not listen for `edited`.

**Rejected alternative:** a PAT or GitHub App token for release-please.

## The stale draft-release comment link is an accepted cosmetic defect

**Id:** 2c6a6034-1936-4026-b10a-93445ace87b1
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-002 ([`docs/adr/002-release-please-for-release-automation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/002-release-please-for-release-automation.md)); [issue #143](https://github.com/hasansezertasan/copier-pyproject/issues/143), [PR #152](https://github.com/hasansezertasan/copier-pyproject/pull/152)
**Revisit when:** release-please rewrites its release comment after un-drafting, or the draft flow is replaced
**See:** release-automation.md#the-release-is-created-as-a-draft-finalized-after-artifacts-attach — 398b3cd9-e57b-4856-b2c7-76752c0ec37f — as of 2026-10-11

release-please posts its "created releases" comment once, at draft-creation
time, with the transient `untagged-<hash>` slug; after finalization that link
404s. It is left as is.

**Reason:** the release, tag, artifacts and SBOM are all correct; only a link on
an already-merged PR is dead. `draft: false` would repair the link but
reintroduce the no-artifacts window, and having `finalize-release` patch the
comment adds API surface for no functional gain.

**Rejected alternative:** patch the comment in `finalize-release` — still
available without switching tools, listed as an option in the re-evaluation.

## Commitizen is a commit helper, never a release tool

**Id:** ee1d2fad-67ab-4f4a-a531-73458da14eb1
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-004 ([`docs/adr/004-commitizen-as-commit-helper-not-release-tool.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/004-commitizen-as-commit-helper-not-release-tool.md))
**Revisit when:** the re-evaluation below selects a Commitizen-based orchestrator
**See:** release-automation.md#release-please-is-the-sole-release-orchestrator — 7ec8a937-fd4d-41f2-96b7-824fe3be913b — as of 2026-10-11

The generated `[tool.commitizen]` block contains only the convention name. The
release-coupled keys (tag format, version provider and scheme,
`major_version_zero`, changelog-on-bump) were removed, so `cz bump` has no
configured tagging or changelog behaviour. The commit-message hooks stay;
Commitizen is always included (the `include_commitizen` toggle was dropped
because its hooks were unconditional anyway).

**Reason:** as shipped, Commitizen was configured as a second complete release
pipeline that tags the same releases and rewrites the same `CHANGELOG.md` as
release-please — a direct conflict the first release decision never compared.
Versioning, tagging and changelog get exactly one owner; Commitizen keeps the
orthogonal half, helping to write and lint conforming commits.

**Rejected alternative:** keep both configured as "aligned" — competing tags
and two changelog writers on one file.

**Consequence:** message linting overlaps the PR-title check under the required
squash-by-title merge strategy; accepted because the hook gives feedback while
authoring, before a PR exists.

## The release-automation choice is under re-evaluation

**Id:** d9131d49-3c27-48f8-a903-e97caf4acff6
**Type:** decision
**Status:** open
**Evidence:** confirmed
**Source:** ADR-037 ([`docs/adr/037-release-automation-reevaluation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/037-release-automation-reevaluation.md)), a research record last refreshed 2026-10-05; upstream release-please issues [#2515](https://github.com/googleapis/release-please/issues/2515) and [#2605](https://github.com/googleapis/release-please/issues/2605)
**Revisit when:** git-cliff ships prerelease version calculation ([#1380](https://github.com/orhun/git-cliff/issues/1380)), RC series become frequent, or a maintainer picks one of the four options
**See:** release-automation.md#release-please-is-the-sole-release-orchestrator — 7ec8a937-fd4d-41f2-96b7-824fe3be913b — as of 2026-10-11
**See:** release-automation.md#commitizen-is-a-commit-helper-never-a-release-tool — ee1d2fad-67ab-4f4a-a531-73458da14eb1 — as of 2026-10-11

Two friction points reopened the tool choice: a stable release cut after
release candidates lists only changes since the last RC (release-please has no
prerelease/stable distinction and no config remedy; the npm CLI team works
around the same behaviour by hand), and the draft-then-finalize dance plus
phantom-PR reconciliation are workarounds layered on release-please's model.
The research frames tools as commit helpers, changelog engines and release
orchestrators, and compares Commitizen (`cz bump`, fixes the RC range with one
setting, medium effort, reverses the commit-helper decision, loses the
reviewable release PR) against git-cliff (a changelog engine only; high effort,
RC math stays hand-written). Four options stand: stay and document, migrate to
Commitizen, git-cliff inside a bespoke orchestrator, or defer. Until decided,
nothing changes.

**Why this needs an answer:** both replacements need a standing privileged
credential or a maintainer-local bump under the `full` preset's ruleset, and
`release.yml` fans out to every generated project while being validated only
by rendering until a live release runs. Whether the RC gap bites often enough
to justify that blast radius is a maintainer judgement, not a research result.

## Optional Docker Hub configuration gates the publish fan-out

**Id:** f6f9eea4-dd38-4a74-98ed-f67e436c393d
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** [PR #51](https://github.com/hasansezertasan/copier-pyproject/pull/51), [shared-gate review discussion](https://github.com/hasansezertasan/copier-pyproject/pull/51#discussion_r3524165040); commit [f48250e](https://github.com/hasansezertasan/copier-pyproject/commit/f48250ebe8b92c880964e892f7c2fb37471a12c4)
**Verification:** corroborated — the web release workflow makes both PyPI and Docker publication depend on `docker-publish-preflight`
**Revisit when:** a new irreversible publication channel is added or Docker Hub opt-in semantics change

Docker Hub publication is optional and its credential pair is all-or-nothing:
neither credential means GHCR-only publication, both enable Docker Hub, and a
partial pair fails a shared preflight before either PyPI or Docker publication.

**Reason:** PyPI uploads are irreversible. A credential check inside only the
Docker job would allow PyPI publication to finish concurrently before Docker
failed, stranding a partially published release. The shared prerequisite rejects
that known configuration error before the publish jobs fan out; it does not make
all later external uploads transactional.

**Rejected alternative:** validate the credentials only inside Docker
publication. Review moved the check into a shared prerequisite specifically to
prevent the PyPI race. Requiring Docker Hub for every web release is not the
selected contract; GHCR-only publication remains supported.

The narrowly scoped ghalint exceptions exist because conditional steps need
job-scoped credential-presence information and GitHub does not expose the
secrets context directly in conditions. The token itself is reduced to a
presence flag, not exposed job-wide. The exceptions are recorded in the
generated `.github/ghalint.yaml` rather than disabling that policy globally.

## Released-issue notifications are one inline job in `release.yml`

**Id:** c8cd015d-12ff-47a7-9447-40b69a2b1a82
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-010 §2 ([`docs/adr/010-pr-docs-previews-and-released-issue-notifications.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/010-pr-docs-previews-and-released-issue-notifications.md))
**Revisit when:** the release lifecycle is split across workflows
**See:** release-automation.md#the-release-is-created-as-a-draft-finalized-after-artifacts-attach — 398b3cd9-e57b-4856-b2c7-76752c0ec37f — as of 2026-10-11

A `notify-released-issues` job, gated on a created release and running after
finalization, uses a single inline `github-script` step to comment the release
tag and URL on every issue the release closed. It is always on, with no toggle.

**Reason:** the upstream implementation shipped a committed Python script and a
JS helper behind a reusable workflow — more moving parts than a single-maintainer
project needs. Inline in `release.yml` matches keeping the whole release
lifecycle in one workflow, and it is zero-config: no closed issues means no
notification, so it cannot fail an unused feature.

**Rejected alternative:** a separate `workflow_call` file with committed scripts.
