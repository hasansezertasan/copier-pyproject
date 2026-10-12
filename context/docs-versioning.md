# Versioned documentation

## Docs publish only the current version and carry older built versions forward from `gh-pages`

**Id:** 858025c1-19a6-46f6-a237-01ba6477262a
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-027 §1–2 (`docs/adr/027-versioned-documentation-and-last-updated-stamps.md`); issue #165; the Litestar docs build is the model
**Revisit when:** a Sphinx multiversion tool stops rebuilding old tags, or `conf.py` stops running build-time generators against the live app
**See:** docs-stack.md#sphinx-with-the-bare-shibuya-theme-replaces-mkdocs — 5133caa8-3231-4d4d-877b-041b315cb87a — as of 2026-10-11
**See:** docs-stack.md#pr-docs-previews-deploy-to-a-subfolder-of-the-projects-own-gh-pages-same-repo-only — 55a74975-a6e0-4f18-8254-fa27f047e829 — as of 2026-10-11

A generated `tools/build_docs.py` computes the version slug, enumerates the
version directories already on `gh-pages`, writes a generated (gitignored)
`versions.json` for Shibuya's native switcher, builds only the current ref,
copies every other version directory across from `gh-pages`, writes a root
redirect to `latest` (the highest non-prerelease by PEP 440 ordering), and
deploys with previews excluded from cleaning. Versioned publishing is how a
docs-enabled project always publishes; it is not a toggle. The version list is
stateless: `gh-pages` is the source of truth, and local builds hide the
switcher because no `versions.json` exists.

**Reason:** `sphinx-multiversion` (effectively unmaintained) and
`sphinx-polyversion` both rebuild every selected tag on every deploy. This
template's `conf.py` runs subprocess generators against the live app, so
rebuilding a historical tag re-runs that tag's generators against whatever the
build resolves — fragile, slow, and it forces every past `conf.py` to keep
building forever. Litestar's build-current-preserve-rest model avoids that.
Litestar commits and hand-edits its version list, which is untenable with
per-minor granularity and automated releases, and having CI commit back to a
protected `main` adds real machinery.

**Rejected alternative:** `sphinx-multiversion` or `sphinx-polyversion` — the
rebuild model above.

**Rejected alternative:** a committed `versions.json` — the hand-edit or
CI-commit cost above.

**Consequence:** `gh-pages` becomes load-bearing state; both deploy paths must
preserve the numeric version-slug directories. An older version's switcher is
frozen at its build time, so the switcher appears only from the first versioned
release onward.

## Version granularity is a scaffold-time question

**Id:** 5d18c9af-73e9-476b-9ba9-544c776812e6
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-027 §3 (`docs/adr/027-versioned-documentation-and-last-updated-stamps.md`)
**Revisit when:** the pre-1.0 minor-is-breaking bump policy changes
**See:** docs-versioning.md#docs-publish-only-the-current-version-and-carry-older-built-versions-forward-from-gh-pages — 858025c1-19a6-46f6-a237-01ba6477262a — as of 2026-10-11
**See:** release-automation.md#release-please-is-the-sole-release-orchestrator — 7ec8a937-fd4d-41f2-96b7-824fe3be913b — as of 2026-10-11

`docs_version_granularity` (asked with `include_docs`) offers `minor` (`X.Y`,
default), `major` (`X`) and `full` (`X.Y.Z`). The choice bakes a slicing
constant into the generated build script, overridable at build time only by the
manual redeploy.

**Reason:** granularity is the one knob adopters reasonably differ on. `minor`
matches the pre-1.0 posture where minors are the breaking bump; a large project
picks `major`, an archival one `full`. Prerelease slugs survive only under
`full` and are excluded from `latest`.

## The manual redeploy rebuilds the latest published release, never HEAD

**Id:** f0ad70ba-c790-42d2-94f0-152e9527be4f
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-027 §4 (`docs/adr/027-versioned-documentation-and-last-updated-stamps.md`)
**Revisit when:** release-please stops creating the tag before the release is published, or the build script's granularity stops being baked in
**See:** docs-versioning.md#docs-publish-only-the-current-version-and-carry-older-built-versions-forward-from-gh-pages — 858025c1-19a6-46f6-a237-01ba6477262a — as of 2026-10-11
**See:** release-automation.md#the-release-is-created-as-a-draft-finalized-after-artifacts-attach — 398b3cd9-e57b-4856-b2c7-76752c0ec37f — as of 2026-10-11

`gh-pages.yml` (manual dispatch only) routes through the build script, checks
out the tag of the latest *published* release via the releases API, sets up the
interpreter after that checkout, restores the build script itself from the
dispatch ref, and passes the tag's baked granularity back through the
environment.

**Reason:** a naive root publish would wipe every version directory. The tag
comes from the API rather than `git describe` because release-please creates
the tag the moment the release PR merges and leaves the release a draft until
publishing succeeds — so `git describe` would pick an unreleased version in
exactly the window a redeploy is most likely (right after a failed release).
The interpreter setup follows the checkout so the tagged docs build on the
Python the release shipped on. The script is orchestration, same layer as the
workflow, and an older tagged copy could carry the version-dropping bug the
loud-fetch rule prevents; its granularity is not orchestration — which slug a
release occupies is fixed at publish time — so an adopter who changed the
answer later must not republish a tag under a second slug and repoint `latest`.

**Rejected alternative:** `git describe --tags` — selects draft tags.

**Rejected alternative:** use the dispatch revision's granularity — duplicates a
released version under a new slug.

## A failed `gh-pages` fetch must abort, never fall through as "branch absent"

**Id:** 135cfbb5-6c5c-45d8-9239-cf225a819818
**Type:** decision
**Type:** incident
**Status:** active
**Evidence:** confirmed
**Source:** ADR-027 §4a (`docs/adr/027-versioned-documentation-and-last-updated-stamps.md`)
**Revisit when:** the deploy stops cleaning the target, or `git fetch` learns to distinguish a missing ref from a transport error
**See:** docs-versioning.md#docs-publish-only-the-current-version-and-carry-older-built-versions-forward-from-gh-pages — 858025c1-19a6-46f6-a237-01ba6477262a — as of 2026-10-11

Both deploy paths probe the branch with `git ls-remote --exit-code` and branch
on its exit code: 2 means no such ref, anything else aborts. One layer up, the
build script's preserve step raises when a version subtree it was handed cannot
be read; only the `latest` alias is optional.

**Reason:** the previous `fetch || echo` swallowed every failure, not only a
missing ref. The build script then assembled a site with no prior versions and
the clean deploy deleted every published version directory — one transient
transport error destroys the documentation archive for every prior release.
Every slug the preserve step receives came from a listing of that very ref, so
it provably exists and silently omitting it is the same deletion by another
route.

## Per-page "last updated" comes from git history

**Id:** 7e34868f-a26a-4c89-8189-f5778ad9a04b
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-027 §5 (`docs/adr/027-versioned-documentation-and-last-updated-stamps.md`)
**Revisit when:** a docs job checks out with shallow history
**See:** docs-stack.md#sphinx-warnings-use-an-exact-reviewable-allowlist — 2a555902-38e7-47d4-a231-445a8e6caa0f — as of 2026-10-11

`sphinx-last-updated-by-git` is in the `docs` group; every page footer shows the
commit date of its source. Any untracked-source warning from the generated
fragments goes through the warning allowlist, not blanket suppression.

**Reason:** readers could not tell how fresh a page was; git history is a cheap
offline freshness signal.

**Consequence:** every docs build needs full history (`fetch-depth: 0`),
including the CI job that runs the warning gate.

## The Sphinx warning gate runs in a job the required `check` context aggregates

**Id:** bc382803-5aa9-4582-9bad-1c9efef8fc49
**Type:** decision
**Type:** incident
**Status:** active
**Evidence:** confirmed
**Source:** ADR-027, Consequences (`docs/adr/027-versioned-documentation-and-last-updated-stamps.md`)
**Revisit when:** `docs-doctest` is renamed or leaves the `check` aggregation
**See:** docs-stack.md#sphinx-warnings-use-an-exact-reviewable-allowlist — 2a555902-38e7-47d4-a231-445a8e6caa0f — as of 2026-10-11
**See:** ci-topology.md#per-component-markers-path-filtered-jobs-and-one-coverage-gate-per-component — 467b6cc3-775b-4e4c-9a8e-b0d1c3d733ac — as of 2026-10-11

`tox -e docs-build` (Sphinx with warnings captured plus the allowlist checker)
runs in `ci.yml`'s `docs-doctest` job, which `check` aggregates.

**Reason:** it previously ran only in the docs-preview workflow, which forks
skip and no protected branch requires, so a PR introducing broken references
kept every required context green. The doctest job on its own runs the doctest
builder with no warnings-as-errors and no allowlist, so it never covered this.
A gate must be checked by which context a protected branch sees, not by whether
the job runs.
