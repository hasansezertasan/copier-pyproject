# Lint and type-check orchestration

## The tox `style` env is the sole authoritative lint suite; prek is a fast gate, not a second suite

**Id:** 9b74fc8b-a808-4f2b-bdbd-9e4253c1b35a
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-003 (`docs/adr/003-tox-as-canonical-lint-runner.md`), including its 2026-06 update
**Revisit when:** a second orchestrator is proposed, or tool versions gain a second pinning location

Tool versions live in the uv-managed `style` dependency group and the tox
`style` env runs the full lint/type-check suite from it. Git hooks are always
included (the `include_precommit` toggle was removed) and run via prek as a
fast local and CI gate; Renovate keeps both the prek `rev` pins and the `style`
group current. Pants and Trunk, once default-on orchestrators of the same
linters, were first demoted to opt-ins and later removed entirely.

**Reason:** a default project shipped three orchestrators (tox, Pants, Trunk)
pinning `ruff`, `mypy`, `actionlint` and others in three places with three
update mechanisms, and the pins had already drifted — a contributor could pass
the local suite and fail CI on a rule that changed between two pinned versions.
One source of truth makes drift impossible, keeps linting on the uv/tox spine
the generated project already uses, and leaves one updater. The prek overlap is
deliberate: fast feedback while editing, authoritative coverage in tox; the
cost is duplicate execution and at most a brief window between two Renovate
PRs, not sustained drift.

**Rejected alternative:** keep Pants and Trunk as opt-ins — the intermediate
state this ADR first established; its 2026-06 update dropped them outright so
that the tox `style` env is the sole orchestrator and nothing can drift against
it.

**Consequence:** MegaLinter, when enabled, is scoped so it cannot drift against
the Python toolchain (see its own entry below).

## Taplo checks do not fetch schemas from generated TOML directives

**Id:** 152edfc1-817e-4265-ac23-53d2a730cd5f
**Type:** workaround
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** [issue #337](https://github.com/hasansezertasan/copier-pyproject/issues/337), [PR #338](https://github.com/hasansezertasan/copier-pyproject/pull/338); commit [9e86cb8](https://github.com/hasansezertasan/copier-pyproject/commit/9e86cb8fcd8ccebc667d70391531c5a33ccc8de4)
**Verification:** corroborated — generated root TOML omits schema directives while the style environment retains Taplo syntax and formatting checks
**Revisit when:** Taplo provides a verified way to retain editor directives without fetching their schemas during checks
**See:** lint-orchestration.md#semgrep-runs-in-the-style-env-against-a-named-registry-ruleset-never-vendored — 5068081c-24ce-4c39-9cdf-13e0a7c229b4 — as of 2026-10-11

Generated root TOML no longer carries the remote schema directive. Editors can
use SchemaStore's filename mapping, while Taplo still checks syntax and canonical
formatting without that schema fetch.

**Reason:** a transient remote schema failure could fail the required style gate
on unchanged source. The investigation found that Taplo 0.9.3 still fetched an
explicit directive's URL with its no-schema flag, so the apparent offline switch
did not solve this failure mode.

**Rejected alternative:** retain the directive and rely on the no-schema flag.
It was tested and rejected because the fetch still occurred. Vendoring a schema
was discussed with a maintenance cost, but the reviewed sources do not establish
an explicit verdict on that alternative.

This constraint applies to the Taplo pass, not to every style tool: the semgrep
entry below separately accepts a registry dependency.

## The prek gate runs at commit; push-only hooks opt in per hook

**Id:** 8fd817b4-fab6-4ce1-b80d-59a2ea93016f
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** found while adopting the template in openapipages; reproduced with prek 0.5.5; recorded in ADR-003 (`docs/adr/003-tox-as-canonical-lint-runner.md`)
**Verification:** corroborated — a hook with no `stages` ran on `pre-commit`, `pre-push`, `commit-msg` and `manual` when `default_stages` was unset
**Revisit when:** a hook other than `commitizen-branch` needs to run on push

`default_stages` is `["pre-commit"]`. Hooks that belong on push, such as
`commitizen-branch`, declare `stages` themselves.

**Reason:** `["pre-commit", "pre-push"]` ran every hook without its own stages
twice per change, including the whole-project type checkers and pylint, and the
push run added no coverage the commit run lacked.

**Rejected alternative:** dropping `default_stages`. prek then treats every
stage as the default, so file hooks also run on `commit-msg`.

## Five type checkers; strict basedpyright replaces pyright

**Id:** 7e130850-494b-427c-a892-a6b3479dd047
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-005 (`docs/adr/005-five-type-checkers-basedpyright-strict.md`)
**Revisit when:** `ty` churn becomes a burden, or two checkers stop catching anything the others miss

The `style` env invokes mypy (two Python versions), basedpyright at its full
strict ruleset, ty, pyrefly and zuban. pyright is dropped from the group and the
env. Generated code is fixed to satisfy strict rules rather than relaxing the
checker; the only suppressions are localized `# pyright: ignore` comments at
genuine library boundaries (MCP's untyped tool arguments).

**Reason:** basedpyright and zuban were installed but never invoked. Wiring them
in surfaced two latent bugs the four invoked checkers all missed — a pyright
venv misconfiguration that pyright tolerated silently, and an invariant-list
assignment to Textual's `BINDINGS` that only zuban's mypy-compatible engine
flagged. basedpyright is a strict superset of pyright, so running both was the
most redundant pairing in the set.

**Rejected alternative:** relax the strict rules — forfeits the hardening the
strict bar drove into the generated code.

**Rejected alternative:** keep pyright beside basedpyright — pure redundancy.

**Consequence:** TUI projects gain `typing_extensions` for `@override` on
3.10/3.11; `ty` is pre-release and kept because it currently passes and adds
coverage. An earlier zuban miscategorized one finding and forced broadening a
mypy disable list; zuban 0.9.0 fixed it and the concession was removed.

## mypy's prek hook runs through uv, like basedpyright

**Id:** 71f826cd-950d-4112-9cfb-7dad6ee98264
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** found while adopting the template in openapipages; recorded in ADR-005 (`docs/adr/005-five-type-checkers-basedpyright-strict.md`)
**Verification:** corroborated — the mirrors-mypy `rev` (v2.3.0) had drifted from the `style` group's `mypy==2.4.0` pin, and the hook's `files = "^src/"` skipped the `docs/examples` path that `[tool.mypy] files` adds with `include_docs`
**Revisit when:** mypy needs to run without the project's environment, for example in a hook-only CI job without uv
**See:** architecture-contracts.md#whole-program-analyzers-are-local-system-hooks-backed-by-the-style-group — 41f3397d-1afb-4e57-a0bd-b5ef85089bfc — as of 2026-10-11

The mypy prek hook is a `local` `system` hook running mypy from the project's
locked `style` group, with `pass_filenames = false`.

**Reason:** the mirrors-mypy hook ran in an isolated venv. It needed a Jinja
list in `additional_dependencies` copying each component's runtime deps, and a
missed entry failed only on the adopter's first full hook run. It also carried
a second mypy version that Renovate bumped separately from the `style` pin, and
its own file filter. The local hook uses the project's environment, the `style`
pin, and `[tool.mypy] files`, the same as tox.

**Rejected alternative:** keep mirrors-mypy and add a test that its
`additional_dependencies` match the runtime deps. That guards one of the three
drifts and keeps the duplicate version pin.

## MegaLinter is an opt-in lean complement, non-blocking on three levels

**Id:** f3041701-610f-4418-b297-e9707da5de40
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-013 (`docs/adr/013-megalinter-opt-in-lean-complement.md`); prompted by a real run ([hwid#90](https://github.com/hasansezertasan/hwid/actions/runs/30634574244/job/91168813067))
**Revisit when:** prek gains one of the five enabled linters, the `cupcake` flavor drops one, or GitHub changes SARIF ingestion rules
**See:** external-integrations.md#a-freshly-generated-project-is-green-on-first-push-with-zero-external-accounts — 392b6dcf-6e9d-441d-bf7b-64ba362578d7 — as of 2026-10-11
**See:** lint-orchestration.md#the-tox-style-env-is-the-sole-authoritative-lint-suite-prek-is-a-fast-gate-not-a-second-suite — 9b74fc8b-a808-4f2b-bdbd-9e4253c1b35a — as of 2026-10-11

`include_megalinter` (default off) renders the workflow and config. Enabled
linters are only the gaps prek and tox leave: shellcheck for standalone
scripts, hadolint (gated on `include_web`, the only config that renders a
Dockerfile), jsonlint, copy-paste detection, and cspell scoped to Markdown as a
deeper dictionary pass beside prek's fast `typos`. It uses the smaller
`cupcake` flavor image, no paths filter, exits 0 (`DISABLE_ERRORS`), posts no
commit status, and is not in the `check` gate; findings reach the Security tab
through a best-effort SARIF upload of the single aggregate report.

**Reason:** the always-on predecessor was documented nowhere, pulled an ~8 GB
image on every push (165 s of a 3-minute run was the pull), and five of its six
linters re-ran checks prek already performed. Unlike the external-service
integrations it needs no account, so it earned its own decision. A paths filter
was tried and dropped: copy-paste detection scans source, so the filter fired on
nearly every PR anyway and only confused. Pointing the SARIF upload at the
reports directory was rejected because GitHub rejects a file whose runs share a
tool and category; the aggregate's per-linter runs carry distinct tool names.

**Rejected alternative:** always-on — the posture above.

**Rejected alternative:** drop cspell entirely — an earlier revision did; it was
reinstated, scoped, during review.

**Consequence:** the best-effort upload fails silently, so the SARIF path is
verified against a live public repository via the code-scanning API, not by
rendering, after any change to that step or a major bump. A project wanting
MegaLinter to gate requires its code-scanning results via branch protection.

## semgrep runs in the `style` env against a named registry ruleset, never vendored

**Id:** 5068081c-24ce-4c39-9cdf-13e0a7c229b4
**Type:** decision
**Type:** constraint
**Status:** active
**Evidence:** confirmed
**Source:** ADR-032 (`docs/adr/032-semgrep-sast-in-the-style-env.md`); [issue #174](https://github.com/hasansezertasan/copier-pyproject/issues/174)
**Revisit when:** offline determinism outranks rule quality, semgrep gains an on-disk rule cache, or the registry rules' license permits redistribution
**See:** lint-orchestration.md#the-tox-style-env-is-the-sole-authoritative-lint-suite-prek-is-a-fast-gate-not-a-second-suite — 9b74fc8b-a808-4f2b-bdbd-9e4253c1b35a — as of 2026-10-11

semgrep is pinned in its own `sast` dependency group, runs only in the tox
`style` env over `src` with the `p/python` registry pack, findings blocking and
telemetry off. It is not a prek hook, not in `check-security.yml`, and no
ruleset is committed.

**Reason:** the registry rules carry the Semgrep Rules License, which forbids
distribution — a Copier template exists to distribute files, so vendoring them
is exactly the prohibited act. semgrep keeps no on-disk rule cache, so a prek
hook would hit the registry on every commit and fail offline; the style-env-only
placement follows the `ty`/`pyrefly`/`zuban` precedent. The dedicated group
exists because `dev` includes `style` wholesale and the wheel is ~215 MB with a
native core; only the Linux style job should pay that. `--config auto` was
avoided so rule selection is reproducible.

**Rejected alternative:** hand-authored rules — legal and offline, but a
hand-maintained taint database catching less than the relevant community rules.

**Rejected alternative:** a `uvx semgrep` job in `check-security.yml` — pure
duplication once semgrep is in `style`, with an unpinned version Renovate did
not track.

**Consequence:** not hermetic — a new community rule or a registry outage can
redden an unrelated PR; findings overlap ruff's bandit rules, so a line may need
both suppressions. The marginal value is cross-statement taint rules ruff
cannot express.
