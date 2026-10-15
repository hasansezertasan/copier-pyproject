# Context index

Why copier-pyproject is built the way it is. The numbered architecture decision records that used to live in `docs/adr/` were deleted; each entry here names the record it was carried from and links it by permalink.

## 0

## 1

## 2

## 3

## 4

## 5

## 6

## 7

## 8

## 9

## A

- [agent-instructions.md](agent-instructions.md) — ai-rulez as the opt-in agent-instruction source: shared prose macros, generated output as build output, no builtins, convergence gates, the default host set.
- [architecture-contracts.md](architecture-contracts.md) — The exhaustive import-linter layers contract and how whole-program analyzers run on the prek gate.

## B

## C

- [ci-topology.md](ci-topology.md) — Generated-project CI: weekly crons for network-dependent checks, per-component jobs and coverage gates, the asymmetric matrix, draft skipping, smokeshow.
- [companion-skills.md](companion-skills.md) — Lifecycle skills ship through the template; prompts bridge the pre-scaffold step.
- [components.md](components.md) — Runnable components: subcommands over one console root, the CLI framework choice, the dependency guard, no extras, run/dev verbs, the shared application payload.

## D

- [docs-stack.md](docs-stack.md) — Sphinx + Shibuya, PR previews, docs linting, the warning allowlist, the docs toggle, executed examples, API-reference rendering.
- [docs-versioning.md](docs-versioning.md) — Build-current-preserve-rest versioned docs, granularity, the manual redeploy, loud gh-pages fetch failures, last-updated stamps, the warning gate's job.

## E

- [external-integrations.md](external-integrations.md) — The self-contained default and the opt-in external services (Sourcery, SonarCloud, all-contributors, benchmarking).

## F

## G

- [gitignore-generation.md](gitignore-generation.md) — cobo-sealed gitignore, its lockfiles, the always-on fragment set, and the seal-keeps/render-strips macOS CR split.

## H

## I

## J

## K

## L

- [lint-orchestration.md](lint-orchestration.md) — tox `style` as the sole lint suite, prek stages, Taplo schema fetching, the five type checkers, MegaLinter, semgrep, deptry + creosote.

## M

## N

## O

## P

- [package-distribution.md](package-distribution.md) — Homebrew/Scoop dispatch, the executable payload precedence, optional PyPI publishing.
- [presets.md](presets.md) — Archetype presets and what the example input file holds.

## Q

## R

- [rationale-records.md](rationale-records.md) — `context/` as the source of the why, and the ADR archive's freeze and deletion.
- [release-automation.md](release-automation.md) — release-please, the draft-release flow, the dispatch trigger and publish environment, token workarounds, Commitizen's role, the open re-evaluation, Docker Hub gating, issue notifications.
- [repo-setup.md](repo-setup.md) — Settings App metadata, rulesets as code, the single maintainer setup doc, the resume-driven repo-setup skill, this repository's own two-command setup.
- [runtime-logging.md](runtime-logging.md) — Console-only degradation, home-directory resolution, and logging ownership boundaries.

## S

- [standalone-executables.md](standalone-executables.md) — Launcher/compiler/freezer toggles, binary naming and the single entrypoint, PR-time build checks.
- [supply-chain-security.md](supply-chain-security.md) — Protected build and publication attestations, visibility fallback policies, and layered secret scanning.

## T

- [template-testing.md](template-testing.md) — Testing the template itself: render-and-inspect, formatter-canonical output, the shared collection macro, the single render entrypoint, derived artifacts, the watch loop.
- [template-updates.md](template-updates.md) — Renovate's copier manager, no `_tasks`, frozen template pins, adopter-owned retired modules, preservation-first reconciliation.
- [templating-engine.md](templating-engine.md) — Why Copier.
- [testing-strategy.md](testing-strategy.md) — Generated-project testing: the broker factory, real-broker integration tests, coverage exclusions, headless driver seams, the async axis.

## U

## V

## W

## X

## Y

## Z
