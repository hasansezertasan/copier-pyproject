# ADR-022: Consolidate maintainer repository setup into one actor-tagged docs home

## Status

Proposed (2026-08).

## Context

The generated `CONTRIBUTING.md` had grown to ~590 lines, of which ~330 (a
`Repository setup (one-time)` section of ten-plus numbered steps plus an
`Optional third-party integrations` section) were **maintainer/author** work:
squash-merge policy, branch protection, `release.yml` Actions permissions,
release immutability, PyPI trusted publishing, Codecov/SonarCloud tokens, the
Settings/Renovate/Sourcery GitHub Apps, the Homebrew/Scoop dispatch PATs, and
GitHub Pages enablement.

That is a category error. `CONTRIBUTING.md` is **contributor-facing** — how to
ask a question, file a bug, open a PR, follow the styleguides. A contributor
submitting a PR never registers a PyPI publisher or mints a `REPO_ADMIN_TOKEN`.
Burying one-time owner setup there both misfiled it and pushed the genuinely
contributor-relevant material below hundreds of lines they must scroll past.

The same guidance was also **scattered**: `CONTRIBUTING.md` carried the bulk,
while `README.md`, `ci.yml` `::notice::` skip messages, `sonar-project.properties`,
`.sourcery.yaml`, and `.github/settings.yml` each pointed back at
"CONTRIBUTING.md (Repository setup)", and the Homebrew/Scoop packaging READMEs
under `docs/packaging/` held the deep per-target detail with no single home
linking them together.

A companion goal (a stacked issue) is a **setup skill** that can drive this
process. That is only tractable if the setup doc distinguishes, per step, work a
tool can script (`gh` commands) from work only a human in a browser can do
(sign up, mint a credential, install an App, flip a UI-only toggle).

The maintainer setup content itself was correct and load-bearing (ADR-002,
ADR-009, ADR-013, ADR-017, ADR-018, ADR-021 all reference "the repository-setup
section"). This ADR is about **where it lives and how it is structured**, not
its content.

## Decision

Give the maintainer setup **one structured home** and slim `CONTRIBUTING.md`
back to contributor concerns.

- **New `docs/maintaining/setup.rst`** (Sphinx RST, matching the docs stack;
  ADR-006), titled *Repository setup*, organized by concern rather than a flat
  numbered list: merge/PR policy, branch protection, letting Actions open the
  release PR, release immutability, PyPI trusted publishing, coverage, docs
  site, dependency updates, template updates, Discussions, and an
  `Optional integrations` section (Docker Hub, Homebrew, Scoop, SonarCloud,
  Sourcery, all-contributors, Settings App) under the same Jinja conditionals as
  before. Section headings replace the fragile `{% raw %}{% set ns.step %}{% endraw %}` dynamic
  numbering, which is removed.
- **Actor-tagged steps.** Every actionable step is tagged `[AGENT]` (a
  scriptable `gh`/CLI command) or `[HUMAN]` (browser-only). Steps that mint a
  credential and then store it (Codecov private, SonarCloud, Homebrew/Scoop
  PATs, `REPO_ADMIN_TOKEN`) are tagged at the sub-action, so the human step and
  the scriptable `gh secret set` are distinguished. This doubles as the manifest
  the setup skill consumes.
- **Published under a `Maintainer guide` toctree caption** in `index.rst`, so it
  gets a stable docs-site URL and is discoverable, kept visually distinct from
  the consumer-facing Installation/Usage nav.
- **`CONTRIBUTING.md` keeps the contributor-facing `Releasing` narrative** and
  replaces the setup section with a one-line pointer to
  `../docs/maintaining/setup.rst`.
- **Pointers retargeted.** `README.md` (Releasing section), the two `ci.yml`
  skip notices, `sonar-project.properties`, `.sourcery.yaml`, and
  `settings.yml` now reference `docs/maintaining/setup.rst`. The packaging
  READMEs are unchanged and are now linked from the setup doc's Homebrew/Scoop
  entries via `:doc:`.

### Why these choices

- **Repo-relative pointer, not the published URL.** `CONTRIBUTING.md` and the
  workflow notices point at the `.rst` **source path**, not
  `https://…github.io/…/maintaining/setup.html`. Enabling the docs site is
  itself one of the setup steps, so the published URL 404s until setup is done —
  a chicken-and-egg the source path avoids. RST renders on GitHub, so the link
  works immediately.
- **Concern sections over numbered steps.** The old flat numbering needed a
  hand-maintained `namespace(step=…)` seed that had to be bumped whenever a
  fixed step was added; RST sections carry no such coupling.
- **RST, not Markdown.** Matches the existing docs stack (ADR-006) and the
  `docs-build`/`sphinx-lint`/`docs-linkcheck` tooling that already gates the
  other docs pages, so the setup guide is linted and link-checked like the rest.

## Consequences

- `CONTRIBUTING.md` drops from ~590 to ~270 lines and is unambiguously
  contributor-facing.
- Maintainer setup has a single source of truth; the scattered copies become
  thin pointers to it.
- The `[AGENT]`/`[HUMAN]` tagging is a stable contract the stacked setup skill
  parses — future setup steps must carry a tag to stay machine-readable.
- The setup guide renders on the **public** docs site. It contains no secrets
  (only the shape of the setup), so public exposure is acceptable and, for an
  open-source template, useful.
- Prior ADRs that refer to "the CONTRIBUTING repository-setup section" describe
  the location as it was when written; this ADR records the relocation. New
  references should point to `docs/maintaining/setup.rst`.
