# ADR-009: Optional external quality/community integrations (Sourcery, SonarCloud, all-contributors)

## Status

Proposed (2026-07). Inspired by a survey of established open-source Python
project repositories.

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
| `include_all_contributors` | `.all-contributorsrc` + a README section | all-contributors App/bot (or the CLI) |

### Config-file-first, minimal-workflow

Two of the three add **no workflow at all** — `include_sourcery` and
`include_all_contributors` render only a config file (and, for the latter, a
README anchor); the actual work is done by an installed GitHub App reacting to
PRs. This keeps CI minutes and the zizmor-audited workflow surface unchanged when
they are enabled.

Only `include_sonarcloud` adds a workflow job, and it follows the same
gated-on-secret, non-blocking pattern the template already uses for the Codecov
upload (see [the CI Codecov note in CLAUDE.md]): the `sonar` job runs only on
same-repo, non-fork events and records a visible skip rather than failing when
`SONAR_TOKEN` is unset, so it never blocks a green build for a contributor who
has not wired up SonarCloud.

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
  `template/{% if include_all_contributors %}.all-contributorsrc{% endif %}.jinja`.
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
