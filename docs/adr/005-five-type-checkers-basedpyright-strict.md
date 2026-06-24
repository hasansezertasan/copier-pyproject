# ADR-005: Five type checkers; basedpyright (strict) replaces pyright

## Status

Accepted

## Context

[ADR-003](003-tox-as-canonical-lint-runner.md) made the tox `style` env the
canonical lint/type-check runner but explicitly deferred *how many* type checkers
it should invoke. At that point the `style` dependency group installed **six**
type checkers while the env invoked only **four**:

| Tool | Installed | Invoked | Notes |
|------|-----------|---------|-------|
| mypy | yes | yes (×2: `--python-version` 3.10 and 3.14) | reference checker |
| pyright | yes | yes | Microsoft |
| basedpyright | yes | **no** | strict superset/fork of pyright |
| ty | yes | yes | Astral, `0.0.2` (pre-alpha) |
| pyrefly | yes | yes | Meta, `0.46.0` (preview) |
| zuban | yes | **no** | Rust, mypy-compatible, `0.3.0` (new) |

`basedpyright` and `zuban` were dead weight: installed (and paid for on every
`uv sync --group style`) but never run. Wiring them in to find out what they
caught surfaced **two genuine latent bugs** that the four invoked checkers all
missed:

1. **`[tool.pyright]` venv misconfiguration.** It set `venvPath = ".venv"` *and*
   `venv = ".venv"`, so tools looked for `.venv/.venv`. pyright tolerated it
   silently; basedpyright treated the missing venv as a fatal config error
   (exit 3). The correct value is `venvPath = "."`.
2. **A real type error in the TUI.** `tui/app.py` assigned a bare
   `list[tuple[str, str, str]]` to Textual's `BINDINGS`, whose declared type is
   `list[BindingType]`. Because `list` is invariant, this is an incompatible
   assignment — flagged by zuban's mypy-compatible engine, missed by mypy-strict,
   pyright, ty, and pyrefly.

A redundancy also became clear: **basedpyright is a strict superset of pyright**
(same engine, extra rules). Running both is the most redundant pairing in the
set — basedpyright catches everything pyright does. The two only earn separate
invocations if basedpyright runs at its stricter bar.

## Decision

Invoke five type checkers in the `style` env: **mypy (×2 versions), basedpyright
(strict), ty, pyrefly, zuban.** Drop `pyright` from the group and the env;
basedpyright supersedes it. Both bugs above are fixed (`venvPath = "."`; a
correctly typed `BINDINGS: ClassVar[list[BindingType]]`).

basedpyright runs at its **full strict ruleset** (`[tool.basedpyright]` disables
no rules). Generated code is fixed to satisfy it rather than relaxing the
checker:

- `@override` on overriding methods (adds a `typing_extensions` dependency to the
  `tui` extra, since `typing.override` is 3.12+ and the floor is 3.10);
- `ClassVar` annotations on class attributes (`CSS`, `BINDINGS`, `model_config`)
  and `@final` on the local TUI app class;
- `_ = ...` on intentionally-discarded call results;
- single-string literals (not implicit concatenation) for multi-line messages.

The two `Any`-boundary rules (`reportExplicitAny`, `reportAny`) flag *unavoidable*
`Any` at library seams — chiefly MCP's `dict[str, Any]` tool arguments. These
stay enabled; the genuine boundary site carries an explicit `# pyright: ignore[...]`
comment rather than a global carve-out. (The worker's event-loop setup, which
previously needed a `reportAny` suppression for uvloop, was modernized to
`uvloop.run()` — see below — which removed both the `Any` and a deprecation
finding.)

All tool versions are pinned to their latest releases in the `style` group. An
earlier zuban (`0.3.0`) was mypy-compatible but miscategorized the MCP
untyped-decorator finding under code `misc` (mypy reports it under
`untyped-decorator`), which forced broadening that file's `# mypy:
disable-error-code` list and weakened mypy there. zuban `0.9.0` fixed this, so the
`misc` entry was removed and mypy's full strictness in `mcp/app.py` is restored —
no concession remains.

## Rationale

- **Coverage with evidence.** Each checker has caught something the others miss
  (zuban found the `BINDINGS` invariance bug; basedpyright found the venv
  misconfig). Five independent engines is defensible *because* invoking the
  former dead-weight tools paid for itself immediately.
- **No pyright/basedpyright redundancy.** Replacing pyright with strict
  basedpyright keeps the pyright engine's coverage while adding its stricter
  rules — one tool, not two doing the same work.
- **Fix code, not the checker.** Strict rules drive real annotations and explicit
  intent in the generated code; relaxing them would forfeit the hardening. The
  only suppressions are localized, documented `# pyright: ignore` at true library
  boundaries — not blanket rule disables.
- **Verified against the real gate.** `tox -e style` passes end to end on both a
  default render and a litestar + MCP + worker render, so the five-checker bar is
  green out of the box for generated projects.

## Consequences

- A default generated project type-checks with mypy (two Python versions),
  basedpyright (strict), ty, pyrefly, and zuban; `pyright` is no longer installed
  or invoked. The prek `pyright` hook is replaced by a local `basedpyright`
  hook run through uv.
- Projects that include the TUI gain a `typing_extensions` dependency (via the
  `tui` extra) for `@override` on Python 3.10/3.11.
- MCP code carries one explicit `# pyright: ignore[reportExplicitAny]` at the
  tool-argument boundary — an intentional library-boundary suppression, not
  technical debt. The worker no longer needs any suppression after modernizing to
  `uvloop.run()`.
- ty (`0.0.x`) remains pre-release; its diagnostics and exit behavior may shift
  between versions. It is kept because it currently passes and adds coverage, but
  a future ADR may revisit it if churn becomes a burden. (pyrefly reached `1.x`.)
- `package` keywords and the `style` toolchain references in `README.md`,
  `CLAUDE.md`, and `AGENTS.md` are updated from `pyright` to
  `basedpyright`/`zuban`.
