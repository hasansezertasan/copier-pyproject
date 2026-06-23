# ADR-002: Standardize on release-please for Release Automation

## Status

Accepted

## Context

The template originally exposed a `release_automation` choice variable with four
values — `none`, `release-please`, `release-it`, `release-drafter`. Each non-`none`
value generated its own workflow and config files and carried its own versioning,
changelog, and triggering model. Offering all three multiplied the integration
surface: release-drafter's config branched on `dependency_management`,
release-please paired with `include_changelog`/`include_commitizen`, and each tool
needed a distinct version-bump story while all three ultimately had to converge on
the single `cd.yml` PyPI publish step. Maintaining and testing that matrix for a
feature that every generated project configures exactly once was disproportionate.

The three candidates differ fundamentally in *how a version and a GitHub Release
get created* (PyPI publishing via `cd.yml` is identical for all):

| Dimension | **release-please** | release-it | release-drafter |
|---|---|---|---|
| Trigger model | Push → release PR → merge | Manual `workflow_dispatch` + explicit bump | Push/PR → draft → manual publish |
| Versioning | Automatic from Conventional Commits | Human picks the bump each time | Label-driven semver from PR labels |
| Changelog | Generates & commits `CHANGELOG.md` | None (manual) | Release notes only, no file |
| Runtime | Pure GitHub Action | Requires Node.js (`npx release-it`) | Pure GitHub Action |
| Discipline required | Conventional Commits | Maintainer judgement per release | PR-labelling hygiene |
| Python-native fit | First-class (`release-type: python`) | Generic, JS-oriented | Generic |
| Audit trail | Reviewable PR before tag | Commit after the fact | Draft before tag |

This decision was validated against a real adopter project, **keycast PR #11**
(<https://github.com/hasansezertasan/keycast/pull/11>), which hardens a
release-please pipeline against its real-world edge cases:

- **Lockfile desync** — moving to a `hatch-vcs` *dynamic* version so `uv.lock`
  carries no `version =` field for the editable project, making
  `release-please`-bumps-`pyproject.toml`-but-not-`uv.lock` desync structurally
  impossible and `uv run --locked` reliable. **This template already ships
  `dynamic = ["version"]` + hatch-vcs**, so this fix is pre-satisfied here.
- **Pre-1.0 promotion** — `bump-minor-pre-major: true` so a `feat!:` /
  `BREAKING CHANGE` bumps `0.x → 0.x+1` instead of jumping to `1.0.0`. **Already
  set in this template's `release-please-config.json`.**
- **Draft-release ergonomics** — `draft: true` plus an inline publish job that
  attaches build artifacts *before* un-drafting, plus a phantom-release-PR
  reconciliation step (close the orphan PR and re-dispatch) to work around
  release-please computing its commit range from the latest *published* release.

## Decision

Standardize on **release-please** as the sole release-automation system. Remove
the `release_automation` choice variable entirely and make the release-please
workflow, config, and manifest unconditional in every generated project.

The **keycast PR #11 pipeline is the canonical reference design** for how
release-please should be wired:

1. Conventional-Commit-driven release PRs open automatically on push to `main`.
2. Versioning is sourced exclusively from git tags via hatch-vcs
   (`dynamic = ["version"]`); release-please never edits a static version literal.
3. `bump-minor-pre-major: true` keeps pre-1.0 projects pre-1.0.
4. On release, PyPI publishing uses Trusted Publishing (`id-token: write`) and the
   publish checkout uses `fetch-depth: 0` so hatch-vcs can see the release tag.

## Rationale

- **Python-native.** release-please's `release-type: python` and changelog
  generation fit a Python package directly; release-it is JS-oriented and pulls in
  a Node.js runtime, and release-drafter produces no `CHANGELOG.md` file.
- **Automation over discipline.** release-please derives the version from
  Conventional Commits, which this template already encourages via
  `include_commitizen` and commit linting. release-it requires a human to choose
  the bump on every release; release-drafter requires per-PR label hygiene.
- **Reviewable audit trail.** The release PR is a reviewable artifact before any
  tag is cut — stronger than release-it's after-the-fact commit.
- **Validated, not theoretical.** keycast PR #11 proves the release-please path end
  to end against its sharp edges, and two of its three hard-won fixes (dynamic
  version, pre-1.0 bump cap) are *already* baked into this template — so adopting
  it standardizes on the option we have the most evidence for.
- **Single integration surface.** One tool means one workflow to maintain, one
  changelog story, and the removal of the release-drafter ↔ `dependency_management`
  coupling — directly addressing the complexity that motivated this ADR.

## Consequences

- The `release_automation` variable is removed from `copier.yml`; the release-it
  and release-drafter config + workflow files are deleted; the three release-please
  files (`release-please-config.json`, `.release-please-manifest.json`,
  `.github/workflows/release-please.yml`) become unconditional.
- Generated projects now always include a release-please pipeline. The previous
  `none` escape hatch is gone — projects that want no automation must delete the
  files post-generation. This is an accepted trade-off for a template whose target
  audience publishes to PyPI.
- `.example-input.yml` no longer sets `release_automation`, so `example/` is
  regenerated with release-please present.
- **The keycast pipeline is implemented, not deferred.** `cd.yml` is deleted and
  its jobs are folded into a single unified `release-please.yml`: `release-please`
  → `build` (matrix when `include_c_extensions`) → `pypi-publish` → conditional
  `build-executables` (PyCrucible) / `docker-publish` (web) → `attach-github-release`
  → `finalize-release`. All post-`release-please` jobs gate on
  `release_created == 'true'`. The release is created `draft: true`, artifacts are
  attached to the draft, and `finalize-release` un-drafts it (firing
  `release: published`, which `gh-pages.yml` still consumes) and reconciles the
  phantom next-release PR (close + bounded re-dispatch).
- **Trusted publishing entry workflow changed.** Because the PyPI publish step is
  inline in `release-please.yml` (not a reusable `cd.yml`), the PyPI Trusted
  Publisher must register `release-please.yml` as the workflow filename. README and
  CLAUDE.md are updated accordingly.
- **`draft: true` requires `force-tag-creation: true`** (and
  `release-please-action` v5.0.0). GitHub withholds a draft release's git tag until
  it is published, so without this the `build` job would run before the tag exists
  and hatch-vcs would stamp the *previous* version (or `fallback-version`). This
  latent wrong-version bug was caught in
  [cobo#49](https://github.com/hasansezertasan/cobo/pull/49) and is fixed here.
- **Validation limit:** rendering and `actionlint` confirm the workflow is correct
  across option combinations (default, c-extensions, PyCrucible, web, all-on), but
  the end-to-end release behavior (draft tag timing, OIDC publish, reconciliation)
  can only be fully exercised by a live release — as cobo#49 demonstrates, that is
  where the subtle bugs surface.
- Conventional Commits become a soft requirement for the version bump to work;
  this aligns with the existing `include_commitizen` and commit-lint tooling.
