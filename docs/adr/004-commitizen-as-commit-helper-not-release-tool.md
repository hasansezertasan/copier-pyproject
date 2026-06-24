# ADR-004: Commitizen as a commit helper, not a release tool

## Status

Accepted

## Context

[ADR-002](002-release-please-for-release-automation.md) standardized release
automation on **release-please**, comparing it against release-it and
release-drafter. It did *not* compare release-please against a **Commitizen-based**
release pipeline; instead it treated `include_commitizen` as merely complementary
("Conventional Commits ... aligns with the existing `include_commitizen` and
commit-lint tooling").

That framing missed an overlap. Commitizen is not only a tool for *writing*
Conventional Commits — via `cz bump` it is itself a complete
Conventional-Commit-driven **release** pipeline. As shipped, the template's
`[tool.commitizen]` was configured for exactly that second role:

```toml
[tool.commitizen]
major_version_zero = true
name = "cz_conventional_commits"
tag_format = "v$version"
update_changelog_on_bump = true   # when include_changelog
version_provider = "scm"
version_scheme = "pep404"
```

`tag_format` + `version_provider` mean `cz bump` creates `vX.Y.Z` git tags;
`update_changelog_on_bump` means it writes `CHANGELOG.md`. release-please does the
*same three things* from the *same source* (Conventional Commits on `main`):

| Responsibility | release-please | Commitizen (`cz bump`) |
|----------------|----------------|------------------------|
| Derive version bump from commits | yes (`release-please-config.json` bump rules) | yes |
| Create the `vX.Y.Z` git tag | yes, on release-PR merge | yes (`tag_format = "v$version"`) |
| Write `CHANGELOG.md` | yes (`changelog-path: CHANGELOG.md`) | yes (`update_changelog_on_bump`) |

Two tools tagging the same releases and editing the same `CHANGELOG.md` is a
direct conflict: whichever runs creates a tag and a changelog entry the other does
not expect, and the file is rewritten by two generators with different formats.

The two pipelines also differ fundamentally in *model*, which is the comparison
ADR-002 should have made:

| Dimension | release-please pipeline | Commitizen (`cz bump`) pipeline |
|-----------|-------------------------|----------------------------------|
| Trigger | Push to `main` opens/maintains a Release PR; merge cuts the release | A `cz bump` invocation (local, or a CI action on push) |
| Review artifact | The Release PR — version + changelog reviewable *before* any tag | None by default; the bump commit + tag are produced directly |
| Version source | Git tags via hatch-vcs (`dynamic = ["version"]`); no literal is edited | Commitizen owns the bump and writes the tag/version |
| Changelog | Managed in `CHANGELOG.md` by release-please | Written inline by Commitizen on bump |
| Runtime footprint | GitHub Actions only | A `cz` invocation in the release path |
| `uv.lock` drift risk | None — version is never a static literal | Possible if a literal version source is used |

For this template — which already sources versions from git tags via hatch-vcs and
already adopted release-please's reviewable-Release-PR model in ADR-002 — the
release-please pipeline is the chosen one, and a parallel `cz bump` pipeline is
redundant at best and actively conflicting at worst.

## Decision

release-please is the sole owner of version bumping, git tagging, and
`CHANGELOG.md`. Commitizen is retained **only** as a commit-authoring and
commit-message-linting helper. Its configuration is reduced to the rule set both
`cz commit` and the commit-message hook need:

```toml
[tool.commitizen]
name = "cz_conventional_commits"
```

The release-coupled keys — `tag_format`, `version_provider`, `version_scheme`,
`major_version_zero`, and `update_changelog_on_bump` — are removed so `cz bump`
has no configured tagging/changelog behavior to compete with release-please. The
`commitizen` / `commitizen-branch` pre-commit hooks remain (message linting), and
`include_commitizen` stays an opt-in.

This refines ADR-002: the relationship between Commitizen and release-please is not
"aligned, both on" but "layered, non-overlapping" — Commitizen helps *produce*
well-formed Conventional Commits, release-please *consumes* them.

## Rationale

- **One owner per responsibility.** Versioning, tagging, and changelog have exactly
  one owner (release-please), eliminating competing tags and duplicate changelog
  writers on the same file.
- **Keeps the genuinely useful half.** Commitizen's value here is help in *writing*
  conforming commits and linting messages — orthogonal to release-please and worth
  keeping. Only its release role was redundant.
- **Consistent with ADR-002's model.** ADR-002 chose release-please specifically
  for its reviewable Release PR and git-tag-sourced versioning. A `cz bump`
  pipeline has neither by default; running it alongside would undercut both.
- **No `uv.lock` desync.** Because versions come from git tags via hatch-vcs and no
  tool edits a literal, the lockfile cannot drift on release — a property a
  Commitizen-writes-the-version pipeline does not guarantee.

## Consequences

- A generated project with `include_commitizen=true` gets a `[tool.commitizen]`
  block containing only `name`; `cz bump` is not configured to tag or write a
  changelog.
- `include_commitizen`'s help text, and the `CLAUDE.md` / `AGENTS.md` descriptions,
  are updated to describe it as commit authoring/linting, not "version bumping and
  changelog generation."
- The commit-message linting role overlaps with `check-pr-title.yml` given the
  required squash-by-PR-title merge strategy (the squashed commit is the validated
  PR title, so per-commit messages are discarded on merge). This redundancy is
  accepted: the hook gives fast local feedback while authoring, before the PR
  exists. Projects that find it noisy can disable `include_commitizen`.
- The commented-out `bump-my-version` entry in the `tool` dependency group — a
  vestige of the same pre-release-please bumping approach — is removed.
