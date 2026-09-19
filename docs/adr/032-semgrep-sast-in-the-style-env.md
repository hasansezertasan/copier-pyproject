# ADR-032: semgrep as a style-env SAST layer, not a vendored ruleset

## Status

Accepted (2026-09). Extends
[ADR-003](003-tox-as-canonical-lint-runner.md) (tox `style` is the canonical
lint orchestrator). Resolves issue #174.

## Context

The template's security posture was strong on supply-chain and posture axes
(CodeQL, Scorecard, dependency-review, gitleaks, pip-audit, zizmor/ghalint,
Trivy for the web image) and on lint-level checks via ruff, but carried no
general-purpose **rules-database SAST engine** over the generated project's own
source — the class of tool that matches insecure patterns and cross-statement
taint flows from a curated rules database rather than per-node AST heuristics.

Issue #174 proposed `semgrep`, delivered as a `local` prek hook shelling through
the `style` dependency group, with a committed ruleset "so runs are
deterministic and network-independent".

Three facts, established while scoping it, decided the shape:

1. **The registry rules cannot be redistributed.** Every rule in `p/python`
   carries `metadata.license: Semgrep Rules License v1.0`, and
   `semgrep/semgrep-rules` reports SPDX `NOASSERTION` with that same license as
   its repository `LICENSE`. Its terms: *"You may not distribute the rules, or
   make them available to others as a service"*, granted solely for "your own
   internal business purposes", with no sublicensing. A Copier template exists
   to distribute files to adopters, so vendoring those rules into `template/`
   is precisely the prohibited act — and would place non-OSI-licensed content
   into every generated project.
2. **semgrep keeps no on-disk rule cache.** `~/.semgrep/` holds only
   `settings.yml` and a log; a warm second run is fast HTTP, not offline
   operation. A prek hook would therefore make a registry request on *every*
   `git commit`, and fail for an offline contributor or during a registry
   outage.
3. **The overlap with ruff is larger than #174 assumed.** Generated projects set
   `select = ["ALL"]`, so all of flake8-bandit (`S`) is already on; an md5 call
   trips both `S324` and `insecure-hash-algorithm-md5`. Of `p/python`'s 151
   rules, 55 are taint-mode and only 21 are relevant to what this template
   generates (`python.lang.security.*` plus `fastapi.wildcard-cors`).

## Decision

### 1. semgrep is pinned in the `style` dependency group

`semgrep==1.177.0` sits alongside the other linters, so the version has a single
source that Renovate tracks through the native `pep621` manager — no
`customManager`, per the repo's Renovate convention.

### 2. It runs in the tox `style` env only — not as a prek hook

```toml
["semgrep", "scan", "--config", "p/python", "--error", "--metrics=off", "src"]
```

This follows the precedent already set by `ty`/`pyrefly`/`zuban`, which are
deliberately style-env-only rather than prek hooks. Fact (2) above is the
reason: the fast pre-commit gate must not depend on a network round-trip.
`--error` makes findings blocking; `--metrics=off` keeps scan telemetry off the
wire; scoping to `src` audits the shipped package, not tests or docs.

### 3. The ruleset is named, not vendored, and not `auto`

`--config p/python` rather than `--config auto` so rule *selection* is
reproducible and independent of semgrep's language auto-detection. It is **not**
vendored into `template/`, because fact (1) forbids it. `p/security-audit` is
not stacked on top: it is the auditor-oriented low-confidence pack, and
`p/python` already carries the `python.lang.security.*` rules.

### 4. No `check-security.yml` job

An earlier revision of this change ran semgrep as a `uvx semgrep` job in
`check-security.yml`, beside gitleaks/pip-audit/trivy. Once semgrep lives in the
`style` env that job is pure duplication, and `uvx` left the version unpinned
and untracked by Renovate. The `style` env placement supersedes it.

## Consequences

**Accepted costs.**

- **Not hermetic.** The ruleset is fetched from the registry at scan time, so a
  semgrep release or a new community rule can turn a previously-green `main`
  red on an unrelated PR, and a registry outage fails `tox -e style`. This is
  the accepted trade for zero ruleset maintenance; fact (1) removes the only
  alternative that would have fixed it.
- **A ~70 MB wheel in the `style` group**, so every contributor's `uv sync` and
  every `tox -e style` run carries it — including all ten render scenarios in
  this repo's own `template-ci.yml`.
- **Findings overlap ruff.** A flagged line may need both `# noqa: S…` and
  `# nosemgrep: <rule-id>`. The genuine marginal value is the cross-statement
  taint rules ruff's per-node checks cannot express, on a faster cadence than
  CodeQL's scheduled deep analysis.

**Rejected alternative: hand-authored rules.** Original rules would be legal to
ship and fully offline, but would mean maintaining a taint-rule database by hand
that catches materially less than the 21 relevant community rules. Revisit only
if offline determinism ever outranks rule quality.
