# ADR-009: Optional external quality/community integrations (Sourcery, SonarCloud, all-contributors)

## Status

Proposed (2026-07). Inspired by a survey of established open-source Python
project repositories.

Amended (2026-07): `include_all_contributors` additionally renders an opt-in
`all-contributors.yml` workflow that runs the all-contributors **CLI** to
regenerate the README table and opens a PR with the result — so the toggle no
longer depends solely on the external bot/App. See the all-contributors rows in
the Decision and Consequences below.

## Context

A number of mature Python project repositories layer a few third-party SaaS
integrations on top of their in-repo tooling:

| Integration | Typical artifacts | What it is |
| ------------- | ------------------- | ------------ |
| **Sourcery** | `.sourcery.yaml` | AI refactoring / clone-detection bot; runs as a GitHub App, config-file only — no workflow |
| **SonarCloud** | `sonar-project.properties` + a `sonar` CI job | Hosted static-analysis + coverage dashboard; consumes `coverage.xml`, needs `SONAR_TOKEN` |
| **all-contributors** | `.all-contributorsrc` + a README grid | Renders a contributor-recognition table into the README, driven by a bot/App |

All three share the same shape from the template's point of view:

- They depend on an **external service** the project owner must set up out-of-band
  (install a GitHub App, create a SonarCloud org, add a repo secret).
- They **overlap** with tooling the template already ships. SonarCloud's Python
  analysis and coverage view overlap heavily with the template's existing stack:
  Codecov upload, CodeQL, ruff, vulture, and five type checkers
  ([ADR-005](005-five-type-checkers-basedpyright-strict.md)). Sourcery's
  refactoring suggestions overlap with ruff's lint/refactor rules.
- With no setup they are **inert or noisy**: a Sonar job with no `SONAR_TOKEN`
  fails; an all-contributors grid nobody maintains goes stale.

The amendment above revises the first point for **all-contributors**: its bundled
CLI workflow gives it a first-party provisioning path, so of the three only
Sourcery and SonarCloud strictly depend on an external service. The
toggle-not-always-on rationale below still holds for all three.

This tension is exactly why they do **not** belong in the always-on base like the
community-health files (`SUPPORT.md`, `CITATION.cff`, Renovate, Codecov). The
template's default posture is *self-contained* — a freshly generated project is
green on push with zero external accounts. These integrations would violate that
default if forced on.

## Decision

Ship all three as **independent, opt-in boolean toggles, defaulting to `false`**,
so the self-contained default is preserved and a project owner turns on only the
services they have actually provisioned.

| Toggle | Artifact(s) rendered | Requires |
| -------- | ---------------------- | ---------- |
| `include_sourcery` | `.sourcery.yaml` | Sourcery GitHub App installed on the repo |
| `include_sonarcloud` | `sonar-project.properties` + a `sonar` job in `ci.yml` | SonarCloud org + `SONAR_TOKEN` secret |
| `include_all_contributors` | `.all-contributorsrc` + a README section + `all-contributors.yml` | all-contributors bot/App **or** the bundled CLI workflow |

### Config-file-first, minimal-workflow

`include_sourcery` adds **no workflow at all** — it renders only a config file;
the work is done by an installed GitHub App reacting to PRs, so CI minutes and
the zizmor-audited workflow surface are unchanged when it is enabled.

`include_sonarcloud` adds a workflow job that follows the same
gated-on-secret, non-blocking pattern the template already uses for the Codecov
upload (see [the CI Codecov note in CLAUDE.md]): the `sonar` job runs only on
same-repo, non-fork events and records a visible skip rather than failing when
`SONAR_TOKEN` is unset, so it never blocks a green build for a contributor who
has not wired up SonarCloud.

`include_all_contributors` renders the config + README section and a small
`all-contributors.yml` workflow (`workflow_dispatch` + `push` to the default
branch on `.all-contributorsrc` changes). The workflow runs the all-contributors
**CLI** — delivered via mise's npm backend (`mise exec -- all-contributors
generate`), mirroring how ghalint is delivered/invoked — to regenerate the README
table, and opens a **PR** with any change via `peter-evans/create-pull-request`.
It never pushes to the default branch, so it respects the squash-merge policy and
the `persist-credentials: false` hardening rule (the action authenticates its
own push from its `token` input, like `JamesIves` does for docs). This means the
toggle is useful **without** installing the bot; the bot remains an alternative
for `@all-contributors please add …` comment-driven edits. Like release-please,
the workflow needs the repo's *Allow GitHub Actions to create and approve pull
requests* setting — already required and documented for release-please, so no new
provisioning.

### Why toggles rather than "always on" or "never"

- **Not always-on:** they need external provisioning and would fail/rot without
  it, breaking the self-contained default. They also duplicate existing gates
  (Sonar vs. Codecov+CodeQL+ruff+type-checkers), so forcing them adds cost, not
  coverage.
- **Not omitted entirely:** teams that already run these services get a
  first-class, correctly-wired starting point instead of hand-rolling the config,
  and the toggle names document that the option exists.

### Why each toggle is independent

They solve different problems (refactoring suggestions vs. quality dashboard vs.
community recognition) and compose freely, mirroring the independent-boolean
decision in [ADR-007](007-standalone-executable-toggles.md). No `when:` gating
and no mutually-exclusive enum.

### `.editorconfig` / lint alignment

`.sourcery.yaml` and `sonar-project.properties` are new config formats. The
2-space `.editorconfig` glob and the `validate-pyproject`/`taplo`/`yamllint`
suite must be checked against them when implementing so the generated project
stays lint-clean (the same correctness fix `.jsonc`/`.cff` needed — see
CLAUDE.md). `sonar-project.properties` is a Java-`.properties` file (not TOML);
confirm no style hook wrongly claims it.

## Consequences

- Three new `copier.yml` booleans (`include_sourcery`, `include_sonarcloud`,
  `include_all_contributors`), all `default: false`, each with `help` text noting
  the **external setup** it requires.
- `.example-input.yml` sets all three to `false` (consistent with it disabling
  every optional component), so their rendered form is only validated when
  generated explicitly — the same "generate it to test it" caveat as every other
  component (CLAUDE.md, [ADR-008](008-worker-broker-testing-strategy.md)).
- New conditional template files:
  `template/{% if include_sourcery %}.sourcery.yaml{% endif %}.jinja`,
  `template/{% if include_sonarcloud %}sonar-project.properties{% endif %}.jinja`,
  `template/{% if include_all_contributors %}.all-contributorsrc{% endif %}.jinja`,
  and `template/.github/workflows/{% if include_all_contributors %}all-contributors.yml{% endif %}.jinja`.
- The `all-contributors.yml` workflow installs the CLI via `jdx/mise-action`
  (`npm:all-contributors-cli` pinned in `mise.toml`), runs
  `mise exec -- all-contributors generate`, and opens a PR via
  `peter-evans/create-pull-request` on a `chore/`-prefixed branch (never pushes to
  the default branch). It must stay zizmor/ghalint-green like every workflow:
  `permissions: {}` top-level with `contents: write` + `pull-requests: write` on
  the one job, `persist-credentials: false`, per-job `timeout-minutes`, SHA-pinned
  actions (Renovate-tracked). The CLI version is pinned in `mise.toml`'s `[tools]`
  and bumped by Renovate's mise manager (npm datasource) — no manual pin, unlike a
  `bunx`-arg approach. The `npm:` tool entry is conditional on the toggle so
  projects without it carry no extra mise tool.
- `ci.yml.jinja` gains a `sonar` job guarded by
  `{% if include_sonarcloud %}` and by the `SONAR_TOKEN`-presence flag; it must
  keep the workflow zizmor-green (least-privilege `permissions`,
  `persist-credentials: false`, `timeout-minutes`, SHA-pinned action — pinned/kept
  current by Renovate like every other `uses:`).
- `README.md.jinja` conditionally renders the SonarCloud quality-gate badge and
  the all-contributors grid section (behind their toggles), next to the existing
  Codecov/Scorecard badges.
- `CONTRIBUTING.md.jinja`'s repository-setup section documents the one-time
  provisioning for each enabled integration (install App, create Sonar org + add
  `SONAR_TOKEN`), alongside the existing PyPI/Codecov setup steps.
- The CLAUDE.md "Optional components" and README feature tables gain the three
  toggles.
- More template surface to test: each toggle exercised independently and in
  combination, per the CLAUDE.md testing convention.
