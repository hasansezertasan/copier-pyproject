# CI topology of generated projects

## Network-dependent checks run on a weekly cron, never in the merge gate

**Id:** 3e5b9525-9087-4125-b19f-80f6c226c01f
**Type:** decision
**Type:** constraint
**Status:** active
**Evidence:** confirmed
**Source:** ADR-011 (`docs/adr/011-docs-linting-and-cross-platform-filename-safety.md`), ADR-012 §4 (`docs/adr/012-cobo-for-gitignore-generation.md`), ADR-031 §3 (`docs/adr/031-single-render-entrypoint.md`); the same posture is cited for `check-security.yml`'s periodic scans
**Revisit when:** a network-dependent check becomes reliable enough to block, or the merge gate gains a retry mechanism

Checks whose outcome depends on the network or on an upstream that can change
without a commit here — docs link checking, the cobo gitignore drift check, the
template's generated-artifact drift check — run on a weekly `schedule` plus
`workflow_dispatch`, never on `pull_request`, and never join the `check`
aggregation. They surface rot as a visible, non-blocking workflow result; a tox
env or mise task lets a maintainer run each on demand.

**Reason:** a transient 5xx, a rate limit, a site blocking CI, or an upstream
boilerplate update must never block an unrelated merge. A weekly signal is the
right cadence for drift that accumulates slowly, and a PR-time check cannot see
drift caused by something that changed underneath the repository.

**Rejected alternative:** run them on pull requests — flaky red checks on
unrelated changes.

## A single union coverage gate across the whole matrix

**Id:** ca90a48d-f648-40b3-ae1a-05f9f21cf411
**Type:** decision
**Status:** superseded
**Evidence:** confirmed
**Source:** ADR-026 §1 (`docs/adr/026-combined-cross-matrix-coverage-and-tokenless-html-host.md`)
**Superseded by:** 467b6cc3-775b-4e4c-9a8e-b0d1c3d733ac
**See:** testing-strategy.md#coverage-exclusions-are-per-site-pragmas-and-the-globs-must-match-the-installed-layout — 68366ce3-cc8e-4720-aa91-5eb83aaf2e2d — as of 2026-10-11

Each matrix cell combined its per-interpreter data, kept a non-gating report,
and uploaded a per-OS artifact; one `coverage-combine` job (today's
`coverage-report`) merged every cell
and was the only place `fail_under = 99` was enforced, measuring the union of
all OS and interpreter cells. `relative_files = true` made data from different
runners mergeable, complementing the `src`/`site-packages` path remap. The
combined XML became the one Codecov upload.

**Reason:** per-cell gating measured each OS alone, so a line covered on Linux
but gated off on Windows was reported inconsistently, and there was no
authoritative cross-fan-out number. The union is the correct scope. This held
while the matrix was symmetric — every cell measured the same code.

**Consequence:** once the CI job split into path-filtered per-component jobs, a
skipped component dropped its subtree from the union and the single gate failed
on every partial PR; the principle survives per component in the successor.

## A tokenless public HTML coverage mirror via smokeshow

**Id:** 21119a10-df03-494b-ac84-a57b9b1832c2
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-026 §2 (`docs/adr/026-combined-cross-matrix-coverage-and-tokenless-html-host.md`)
**Revisit when:** Codecov becomes tokenless for private repositories, or smokeshow changes its rate-limit model
**See:** external-integrations.md#a-freshly-generated-project-is-green-on-first-push-with-zero-external-accounts — 392b6dcf-6e9d-441d-bf7b-64ba362578d7 — as of 2026-10-11

`include_smokeshow` (default off, `full` preset) adds a step that uploads the
HTML report to an ephemeral public URL with no secret. It runs only on public
repositories, last in the coverage job, and is best-effort
(`continue-on-error`).

**Reason:** Codecov is opt-in and non-blocking, so a self-contained project had
no hosted, browsable coverage report; smokeshow gives a public project one
without an account. Its tokenless endpoint has low rate limits, so a transient
failure must neither fail the job that feeds the required `check` gate nor
abort the authoritative Codecov upload; a private report must never be
published.

## Per-component markers, path-filtered jobs, and one coverage gate per component

**Id:** 467b6cc3-775b-4e4c-9a8e-b0d1c3d733ac
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-028 (`docs/adr/028-per-component-markers-and-path-filtered-ci.md`)
**Revisit when:** a component gains a dependency on another component's tree, or the aggregation action changes how it treats skipped jobs
**See:** ci-topology.md#a-single-union-coverage-gate-across-the-whole-matrix — ca90a48d-f648-40b3-ae1a-05f9f21cf411 — as of 2026-10-11
**See:** architecture-contracts.md#one-exhaustive-import-linter-layers-contract-cli-above-independent-components-above-core-above-utils — 3b7cdbee-7c66-4e52-9d7e-8ab0ffe32e56 — as of 2026-10-11

One pytest marker per enabled component plus `core`, applied automatically by a
root `conftest.py` hook from each test's top-level `tests/<dir>/`. A
`changes` path-filter job emits one boolean per component plus `core`; the
monolithic CI job splits into `test-core` (always) and `test-<component>` jobs
gated on their own filter or `core`. Each `coverage-<component>` job merges
that component's OS cells and enforces `fail_under = 99` scoped to its subtree
via `--include`; `coverage-core` uses `--omit` of every component and re-adds
`*/_version.py` because a CLI `--omit` overrides the pyproject one. A
non-gating `coverage-report` job merges what ran, omitting skipped components so
their unexecuted files are not reported at zero, and publishes to Codecov,
smokeshow and SonarCloud. The `check` gate lists every path-gated job as an
allowed skip. The default `tox run` is unchanged.

**Reason:** every component's suite ran on every OS for a one-line change in
another component, and a contributor had no knob to run only one component.
`core` is the escape hatch — it watches dependencies, the shared `core/` tree,
root modules and root tests, so a change underpinning every component forces
the full fan-out, mirroring the import layering. Per-component skipping is
incompatible with a single union gate, so the gate is decomposed; skipping is
sound because an unchanged subtree has nothing to regress. The cross-OS union
is kept *within* a component, where a per-cell gate would wrongly fail on a
platform-gated branch. The aggregation action counts a skipped job as a
failure unless named, hence the allowed-skips list rendered from the same
component list as `needs`.

**Consequence:** a full run fans out to more jobs than before; the win is on
component-scoped PRs. `--include`/`--omit` patterns must match both the
editable and installed layouts (`*/`-anchored) and are verifiable only through a
real `tox run`. Adding a component touches the marker list, the conftest
directory set, the filters, two jobs and the omit list in lockstep.

## Asymmetric matrix: every interpreter on Linux, one representative elsewhere; style and installed-CLI are separate jobs

**Id:** 4457f652-2a84-4d70-ab7a-e9d1ebd9c670
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-029 (`docs/adr/029-asymmetric-ci-matrix-and-draft-pr-skip.md`); [issue #159](https://github.com/hasansezertasan/copier-pyproject/issues/159)
**Revisit when:** a platform-specific interpreter defect slips through often enough to matter, or a C-extension build no longer differs per OS/interpreter pair
**See:** ci-topology.md#per-component-markers-path-filtered-jobs-and-one-coverage-gate-per-component — 467b6cc3-775b-4e4c-9a8e-b0d1c3d733ac — as of 2026-10-11

Each `test-*` job runs Python 3.10 through 3.14 on Ubuntu and the invoking
interpreter on macOS and Windows; with `include_c_extensions` every OS runs all
five. `style` runs once on Ubuntu, with mypy additionally run for the win32
and darwin platforms. With `include_cli`, a `cli-installed` job runs the
installed console-script check on all three OSes. Explicit tox env lists keep
style and CLI execution out of the component jobs.

**Reason:** cross-platform behaviour needs every OS at one interpreter and
interpreter compatibility needs every interpreter on one OS; the full
cross-product repeats two mostly independent dimensions. Type checkers prune
`sys.platform` branches against their host, so the platform flags keep static
coverage of platform-gated code. Marker arguments forwarded to pytest must not
reach the `cli` tox env, which would call the installed command with pytest's
`-m` option instead of its default argument.

**Consequence:** a defect needing one particular non-Linux OS and a
non-representative interpreter may pass CI — the accepted cost.

## Every generated CI job skips draft pull requests

**Id:** 43288d9b-11b3-4d92-8a84-6efe1aa43001
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-029 (`docs/adr/029-asymmetric-ci-matrix-and-draft-pr-skip.md`)
**Revisit when:** GitHub adds `ready_for_review` to the default trigger set, or drafts need a cheap smoke run

Every job in `ci.yml` carries the falsy-safe condition that the pull request is
not a draft, composed with existing conditions rather than replacing them
(`check` keeps `always()`, SonarCloud its fork guard, component jobs their
change filters). The `pull_request` trigger explicitly includes
`ready_for_review`. Security and docs-preview workflows still run on drafts.

**Reason:** drafts paid for the whole fan-out before review. `!= true` keeps
running on push and manual events where the pull-request object is absent,
unlike `== false`. Without `ready_for_review`, a PR opened as a draft could
stay permanently skipped after becoming reviewable. Draft PRs skip `check`
itself, so they need no allowed-skip entry.
