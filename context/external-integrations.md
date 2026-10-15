# External integrations and the self-contained default

## A freshly generated project is green on first push with zero external accounts

**Id:** 392b6dcf-6e9d-441d-bf7b-64ba362578d7
**Type:** constraint
**Status:** active
**Evidence:** confirmed
**Source:** ADR-009, ADR-010, ADR-011, ADR-013, ADR-017, ADR-018, ADR-021, ADR-026, ADR-034 ([`docs/adr/`](https://github.com/hasansezertasan/copier-pyproject/tree/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr)); the preset exceptions from ADR-016 and ADR-039 and `preset_map` in `copier.yml`
**Revisit when:** the template's target audience shifts to teams that provision external services as a matter of course
**See:** package-distribution.md#optional-pypi-publishing — 20be7463-ca95-4d01-82c9-71f632d1b4be — as of 2026-10-13

The template's default posture: anything that needs an external service, a
secret, a personal access token or a per-owner repository is an opt-in toggle,
off in the `library`, `tool` and `web` presets; anything self-contained and
zero-config may be always-on. Two exceptions: the `full` preset deliberately
turns most of these toggles on, and PyPI publishing is on in every preset so
existing projects and `copier update` keep publishing (its entry in
`package-distribution.md`).
Secret-gated jobs skip with a visible notice or warning instead of failing, and
such jobs never join the `check` merge gate unless the project owner requires
them through branch protection.

**Reason:** an integration forced on without its setup is inert or noisy — a
SonarCloud job with no token fails, an unmaintained contributors grid rots, a
multi-gigabyte linter image slows every push — and most of them duplicate gates
the template already ships. Keeping the default fast and account-free is what
lets a scaffold be green on its first push. This is the shared rationale the
per-integration entries cite rather than restate.

**Rejected alternative:** ship the integrations always-on because mature
projects use them. Rejected for the failure modes above.

## Sourcery, SonarCloud and all-contributors are independent opt-in toggles

**Id:** e926a0ce-c030-4a76-8b11-41c450bb43f4
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-009 ([`docs/adr/009-optional-external-quality-community-integrations.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/009-optional-external-quality-community-integrations.md)), including its 2026-07 amendment
**Revisit when:** one of the three services gains a provisioning-free mode, or a fourth integration of the same shape is proposed
**See:** external-integrations.md#a-freshly-generated-project-is-green-on-first-push-with-zero-external-accounts — 392b6dcf-6e9d-441d-bf7b-64ba362578d7 — as of 2026-10-11
**See:** standalone-executables.md#three-architecture-named-executable-toggles-instead-of-one-brand-toggle — d5aed1a0-0b7c-4ac3-9d75-fb9568d9e34d — as of 2026-10-11

`include_sourcery` renders only a config file (the GitHub App does the work; no
workflow surface). `include_sonarcloud` adds a `sonar` CI job that runs only on
same-repo events and records a visible skip when `SONAR_TOKEN` is unset.
`include_all_contributors` renders the config, a README section and a small
workflow that runs the all-contributors CLI (delivered through mise's npm
backend, Renovate-tracked) and opens a pull request with the regenerated table —
it never pushes to the default branch, so the toggle is useful without the bot.

**Reason:** all three depend on out-of-band provisioning and overlap with
tooling already shipped (SonarCloud with Codecov, CodeQL, ruff and the type
checkers; Sourcery with ruff's refactor rules). Teams that already run them get
a correctly wired start instead of hand-rolling config. The amendment gave
all-contributors a first-party path so the toggle no longer depends solely on
an external bot.

**Rejected alternative:** always-on — breaks the self-contained default.

**Rejected alternative:** omit them entirely — loses the first-class starting
point and the discoverability of the option.

**Rejected alternative:** one shared enum or parent toggle — they solve
different problems and compose freely, mirroring the independent-boolean
precedent of the executable toggles.

**Consequence:** the all-contributors workflow needs the repository setting that
lets Actions create pull requests, which release-please already requires.

**Consequence:** the CLI is a mise `npm:` tool, not a `bunx`-arg invocation, so
Renovate's mise manager (npm datasource) bumps the pin with no manual upkeep;
the entry is conditional on the toggle. The workflow runs on `workflow_dispatch`
and on pushes that change `.all-contributorsrc`, opens the PR on a `chore/`
branch via `peter-evans/create-pull-request`, and the bot stays an alternative
for `@all-contributors please add` comment-driven edits.

## Opt-in benchmarking with pytest-codspeed

**Id:** 841ba12d-3ad2-402e-9c7e-6791b8221952
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-034 ([`docs/adr/034-opt-in-performance-benchmarking.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/034-opt-in-performance-benchmarking.md))
**Revisit when:** a benchmarking service becomes usable without an account, or the default CI budget changes
**See:** external-integrations.md#a-freshly-generated-project-is-green-on-first-push-with-zero-external-accounts — 392b6dcf-6e9d-441d-bf7b-64ba362578d7 — as of 2026-10-11

`include_benchmarks` (default off, on in the `full` preset) renders a
`benchmarks/` starter suite, a `benchmark` pytest marker excluded from the
ordinary run, `benchmark` tox/mise entry points and a separate `benchmarks.yml`
workflow. The workflow is gated on `CODSPEED_TOKEN`, emits a notice when it is
not configured, and stays out of the `check` gate.

**Reason:** correctness and coverage gates do not catch a valid change that
makes a hot path materially slower, but timings must not slow every project's
default CI or require an account. Service setup is an explicit, reversible
owner choice.

**Alternatives:** unknown — ADR-034 records the decision and its constraints,
no alternative that was in contention.
