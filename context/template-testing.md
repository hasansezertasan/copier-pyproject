# Testing the template itself

## Render-and-inspect is the fast matrixed layer; generate-and-run stays separate

**Id:** c9bcdf52-af5d-4438-9c9f-d55e8226812c
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-024 ([`docs/adr/024-render-and-inspect-template-test-suite.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/024-render-and-inspect-template-test-suite.md)); issue #365 for the parallel run
**Revisit when:** the golden set grows past a couple of stable artifacts, or a root Python project appears
**See:** template-testing.md#toolsrenderpy-is-the-only-place-the-template-is-rendered — f41fa3a2-20e2-4ba5-a3d0-c53a0074a9d0 — as of 2026-10-11

`tests/` renders the template through Copier's Python API into temp
directories and asserts on the output tree: every preset renders, plus one
render per broker and per web framework; every generated YAML parses; the
rendered `pyproject.toml` is valid TOML; and pytest-regressions golden files
snapshot `pyproject.toml` for the `library` and `full` presets only. It runs in
`template-ci.yml`'s `render-tests` job from an ephemeral uv env, in parallel.

**Reason:** the template's correctness across presets and toggle combinations
had no automated guard — `example/` covered one option set when a human
remembered. A Jinja mistake emitting malformed YAML in a conditional file, or a
whitespace regression in a guarded block, merged green. Rendering without
installing is fast enough to fan out; `pyproject.toml` carries pins that move
on every update, so a broad golden set would be churn without coverage.

**Rejected alternative:** `pytest-copie` — a terser fixture that does not earn a
second dependency beyond copier.

**Rejected alternative:** only generate-and-run — proves the project works but
is slow and heavy; "renders and is structurally valid" is a strictly weaker,
far cheaper property, so the two layers stay separate.

**Consequence:** an intentional change to the two golden artifacts needs a
regeneration and a reviewed diff.

## Generated files must be formatter-canonical, not merely valid

**Id:** 9b931598-7e52-4ff1-bb07-ef65c01d5369
**Type:** decision
**Type:** constraint
**Type:** incident
**Status:** active
**Evidence:** confirmed
**Source:** ADR-030 ([`docs/adr/030-generated-files-must-be-formatter-canonical.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/030-generated-files-must-be-formatter-canonical.md)); [issue #213](https://github.com/hasansezertasan/copier-pyproject/issues/213)
**Revisit when:** yamlfmt or taplo change the semantics of the pinned non-default knobs, or the generated project's formatter set changes
**See:** template-testing.md#render-and-inspect-is-the-fast-matrixed-layer-generate-and-run-stays-separate — c9bcdf52-af5d-4438-9c9f-d55e8226812c — as of 2026-10-11

A generated file must already be in the exact byte form the generated project's
own formatters produce — yamlfmt, ruff-format, the prek builtins and taplo.
Three things follow: formatter config is chosen so the hand-written layout is
canonical (`retain_line_breaks_single` for yamlfmt; no array auto-expand,
auto-collapse or comment alignment for taplo; no yamlfmt `max_line_length`);
template sources are written in that form (one-line folded scalars, no comment
trailing a sequence, TOML arrays one-per-line with trailing comma, Jinja
whitespace control so no conditional leaves more than two blank lines or one at
EOF, literal UTF-8 author tokens instead of `tojson`); and taplo runs in strict
check mode. `template-ci.yml`'s render job runs the rendered project's own
fixing hooks per scenario and gates on `git diff`, with an `integrations`
scenario and a non-ASCII author name covering toggles nothing else rendered.

**Reason:** on a pristine scaffold the first hook run rewrote two workflow files
and taplo rewrote two TOML files while exiting 0, so the adopter's `hooks` CI
failed and every later `copier update` showed drift they never caused. Nothing
caught it because this repo ran only checking tools over a render and the
harness asserts YAML parses, not that it is canonical; taplo's fix mode made the
defect invisible. Width-driven reflow would make a file's canonical form depend
on which components are enabled, and comment alignment would let a Renovate
bump break a line nothing touched. The diff, not hook exit codes, is the gate
because a fixing hook that rewrites and exits 0 sails through an exit-code
check.

**Rejected alternative:** chase the formatters' output in the templates — the
config is pinned to make the written layout canonical instead.

**Consequence:** hand-aligned trailing comments and hand-wrapped folded scalars
are unavailable; a conditional block in rendered YAML/TOML requires thinking
about whitespace control; the pinned knobs fail loudly if a release changes
them.

## Collection literals are rendered through one shared macro

**Id:** 47b21a49-5fc4-46b8-b450-7d9f3225706c
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-030, 2026-09 amendment ([`docs/adr/030-generated-files-must-be-formatter-canonical.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/030-generated-files-must-be-formatter-canonical.md)); the agent-prose macros in the same file are recorded in ADR-035
**Revisit when:** ruff-format changes its magic-trailing-comma or width behaviour, or Copier gains a way to share helpers inside `_subdirectory`
**See:** template-testing.md#generated-files-must-be-formatter-canonical-not-merely-valid — 9b931598-7e52-4ff1-bb07-ef65c01d5369 — as of 2026-10-11

`py_collection(name, items, kind)` in `_macros.jinja` emits a tuple or list
literal in the form ruff-format produces: one line when the statement fits in
88 columns, one element per line otherwise. The file sits at the repository
root, outside `_subdirectory`, and templates import it on their first line. It
is used for `__all__`, the dependency allowlists and the guard tuples.

**Reason:** a literal rendered from a Jinja loop has no single correct spelling
— the width depends on values known only at render time (package name, broker
module, component count) — so a template that always emits one form ships a
file the adopter's first hook run rewrites. Outside `_subdirectory` the file is
an input Copier can never render into a project and needs no `_exclude`
override, which would replace Copier's default exclude list wholesale.

**Rejected alternative:** a second hand-written copy of the width branch — the
drift this replaced.

## `tools/render.py` is the only place the template is rendered

**Id:** f41fa3a2-20e2-4ba5-a3d0-c53a0074a9d0
**Type:** decision
**Type:** constraint
**Status:** active
**Evidence:** confirmed
**Source:** ADR-031 §1 ([`docs/adr/031-single-render-entrypoint.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/031-single-render-entrypoint.md)); issues #181, #183, #164, #184
**Revisit when:** Copier's API changes, or a root `pyproject.toml` appears (it must keep the repo root importable under pytest)
**See:** template-testing.md#render-and-inspect-is-the-fast-matrixed-layer-generate-and-run-stays-separate — c9bcdf52-af5d-4438-9c9f-d55e8226812c — as of 2026-10-11

A plain Python module with PEP 723 metadata wraps `copier.run_copy`. The render
harness fixture, the generate-and-run CI matrix, the committed docs artifacts,
the watch loop and the mise tasks all call it. Answers layer as a neutral
identity, then `--data-file`, then explicit answers; programmatic renders use
only the neutral identity so golden files stay stable regardless of a
maintainer's own example input. The CI matrix's kitchen-sink scenario is
spelled as the `full` preset rather than a hand-listed toggle set.

**Reason:** "render this template with these answers" had forked into the
harness, an inline CI invocation, the example task and three proposals each
adding a script — six spellings where the answers baseline, the `vcs_ref` or
the defaults handling can quietly disagree, and a CI matrix rendering a shape
no other consumer can reproduce. A Python module, not a shell script, because
the pytest harness must import the same code path. The preset spelling means a
component added to `full` is exercised end-to-end without editing the matrix.

**Rejected alternative:** per-purpose shell scripts — two renderers again.

**Consequence:** adding another `copier copy` invocation is a review defect; a
new consumer imports `render()` or calls the CLI.

**Consequence:** `tools/render.py` is import-reachable from the tests only
because the repo root is on `sys.path` under pytest (`tests/__init__.py` plus
prepend import mode). A future root `pyproject.toml` must keep that true.

## The generated-project tree page is a committed derived artifact with two drift guards

**Id:** 54918c4d-49dd-4ce8-94a6-3d472010173f
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-031 §2–3 ([`docs/adr/031-single-render-entrypoint.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/031-single-render-entrypoint.md)); generalizes the cobo drift-guard posture of ADR-012
**Revisit when:** copier is pinned in the render path, or another derived artifact joins `regenerate`
**See:** template-testing.md#toolsrenderpy-is-the-only-place-the-template-is-rendered — f41fa3a2-20e2-4ba5-a3d0-c53a0074a9d0 — as of 2026-10-11
**See:** ci-topology.md#network-dependent-checks-run-on-a-weekly-cron-never-in-the-merge-gate — 3e5b9525-9087-4125-b19f-80f6c226c01f — as of 2026-10-11
**See:** gitignore-generation.md#cobo-generates-the-gitignore-with-a-hash-sealed-fence-and-lockfiles — 3e3bc38e-bc1e-4e65-b74d-e91848262157 — as of 2026-10-11

`regenerate` renders the four presets and writes the exact file set each
produces into `docs/generated-project-trees.md`, committed, plain fenced blocks.
Two guards, one per direction of drift: a blocking test in `render-tests`
asserts the committed page equals a fresh render (this repo changed), and a
weekly non-blocking `artifact-drift.yml` regenerates and diffs (the toolchain
changed underneath, since copier is installed unpinned). Golden files are not
folded into `regenerate`.

**Reason:** the documented structure of a generated project is the first thing
a scaffolding template's docs get wrong, and a hand-maintained page cannot
show "this toggle adds these five files" as review signal. Committed rather
than built into a gitignored directory precisely for that diff; `example/`
stays gitignored because a diff-based guard cannot apply to an untracked tree.
A PR-time check cannot see a new copier release changing the output with no
commit here. Golden files already have the same job and their own regeneration
path.

**Consequence:** a PR changing what a preset renders must regenerate the page
or fail `render-tests`; `regenerate` is the extension point for future derived
artifacts.

## The watch loop is an authoring aid whose target is validated before every rebake

**Id:** 36ddff82-32d4-4234-a9cf-ea40d694df58
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-031 §5 ([`docs/adr/031-single-render-entrypoint.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/031-single-render-entrypoint.md))
**Revisit when:** the rebake stops removing its target tree
**See:** template-testing.md#toolsrenderpy-is-the-only-place-the-template-is-rendered — f41fa3a2-20e2-4ba5-a3d0-c53a0074a9d0 — as of 2026-10-11

`watch` re-renders into a gitignored directory on every save under the template
sources and survives a failed render. Its output path is rejected when it
touches a watched source in either direction, or when it is a non-empty
directory without a `.copier-answers.yml`. `watchfiles` is supplied by the mise
task, not declared by the script.

**Reason:** each rebake removes its target tree. "Do not delete what this tool
did not render" is checkable; enumerating which directories are precious is
not. No other consumer should pay for a dependency only the loop needs.
