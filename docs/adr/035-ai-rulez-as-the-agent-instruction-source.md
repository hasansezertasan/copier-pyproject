# ADR-035: ai-rulez as the opt-in single source for agent instructions

## Status

Accepted (2026-09). Opt-in via `include_ai_rulez`. Extends
[ADR-023](023-repo-setup-skill.md) (the repo-setup skill) beyond Claude, obeys
[ADR-012](012-cobo-for-gitignore-generation.md)'s sealed `.gitignore`,
[ADR-003](003-tox-as-canonical-lint-runner.md)'s single lint orchestrator and
[ADR-030](030-generated-files-must-be-formatter-canonical.md)'s
formatter-canonical rule, and is verified by
[ADR-024](024-render-and-inspect-template-test-suite.md)'s harness. Resolves
issue #309.

## Context

A generated project ships agent instructions for **two** hosts: `AGENTS.md`
carries the content (commands, the import-linter package-structure table, the
conventions, the PR/branch rules) and a five-line `CLAUDE.md` `@AGENTS.md`-imports
it. The `repo-setup` skill (ADR-023) — the most valuable agent-facing artifact
the template renders — is authored directly in `.claude/skills/`, so it is
**Claude-only**.

The same project's `check-branch-name.yml` whitelists the branch prefixes `ai`,
`copilot`, `cursor`, `claude` and `codex`. We already expect five agents to open
PRs in these repos and hand four of them nothing: no
`.github/copilot-instructions.md` (which GitHub's Copilot coding agent and PR
review read server-side), no `.cursor/rules/`, no `.codex/`, no skills anywhere
but Claude.

Writing those by hand is the duplication this template exists to remove: five
formats, five frontmatter dialects, five directory conventions, one body of
prose that then drifts per host.

[ai-rulez](https://github.com/Goldziher/ai-rulez) (MIT, Go, v4.11.5) solves
exactly this: author rules / context / skills / agents / commands once under
`.ai-rulez/`, run `ai-rulez generate`, get tool-native output for 20 hosts. Two
properties make it fit *this* repo rather than merely being a nice tool:

- **It ships on PyPI**, so it needs no Node in a generated project and its
  version can live in a `uv` dependency group that Renovate's native manager
  already covers.
- **The cobo precedent already exists.** cobo (ADR-012) is a generator whose
  output is committed and drift-checked. ai-rulez has the same shape — sources
  in, committed output out, a check that proves they agree — so it slots into a
  posture this repo has already argued through.

## Decision

Ship it as an **opt-in toggle**, `include_ai_rulez` (`default: false`, seeded on
in the `full` preset), with an `ai_rulez_presets` multiselect naming the hosts
(default `claude`, `codex`, `copilot` — the three that reproduce today's surface
plus the one GitHub reads itself). With the toggle off, nothing changes: the
hand-written `AGENTS.md`/`CLAUDE.md` pair and the Claude-only skill render
exactly as before, byte for byte.

### 1. The prose has one source, whichever way it renders

The section bodies of `AGENTS.md` moved into `_macros.jinja` (`agent_commands`,
`agent_package_structure`, `agent_conventions`, `agent_pull_requests`, …). The
hand-written `AGENTS.md` calls them; so do the `.ai-rulez/` rule and context
sources. A toggle that produced a second hand-maintained copy of the same
paragraphs would have re-created, inside the template, the drift it exists to
remove downstream. The `repo-setup` skill needs no macro — it is one file whose
*path* is conditional (`.ai-rulez/skills/…` or `.claude/skills/…`), so there is
one copy of it either way.

`interface_components` (`copier.yml`) was extracted for the same reason: the
package-structure table's component list is now computed once instead of rebuilt
in each rendering's Jinja header.

### 2. Generated output is build output — the template renders none of it

The template renders `.ai-rulez/` and stops. `AGENTS.md`, `CLAUDE.md`,
`.github/copilot-instructions.md` and the per-host copies of the skill are
written by the adopter's first `ai-rulez generate` and committed from there on.

Rendering them *as well* was rejected: copier's renderer and ai-rulez's renderer
produce different bytes for the same content (ai-rulez composes its own heading
structure and stamps a provenance header with a content hash), so the first
`generate` would diff against the render, and every `copier update` would
re-render the copier version on top of the generated one — churn and conflicts
on a file the adopter never touched. As build output it is simply outside the
3-way merge: the merge surface becomes the small per-rule sources, which merge
far better than one monolithic `AGENTS.md`.

The cost is real and accepted: **a freshly rendered project has no agent
instruction files until `generate` runs once**. `_message_after_copy` carries the
command as an explicit numbered step, next to `git init` and `uv sync`.

### 3. `builtins = false` — no builtin domains

ai-rulez ships 33 opinionated domains, seven auto-included. They were audited
against what a generated project's CI already enforces, and every one either
restates a gate or contradicts it:

| Builtin rule | Says | The project enforces |
| --- | --- | --- |
| `code-quality/complexity-limits` | max cyclomatic complexity 20 | ruff mccabe **5** |
| `code-quality/readability-first` | max 120 columns | ruff **88** |
| `python/python-conventions` | Google-style docstrings, 80%+ coverage | ruff pydocstyle **pep257**, `fail_under = **99**` |
| `git-workflow/commit-messages` | use conventional commits | `check-pr-title.yml` (blocking) |
| `git-workflow/branch-hygiene` | "descriptive branch names" | Conventional Branch, `check-branch-name.yml` (blocking) |

A rule an agent obeys and a gate that fails it must never be two
separately-maintained sentences. Per-domain `!` exclusions would leave the next
`ai-rulez` release free to add a contradicting rule to a domain we opted into, so
the whole set is off and the shipped rules are only ours. The effect is also the
one this repo wants on size: the generated `CLAUDE.md` is ~60 lines, in keeping
with the lean-router posture (#214), instead of ~270 lines of generic advice.

### 4. `gitignore = false` — ai-rulez must not touch `.gitignore`

ai-rulez defaults to rewriting `.gitignore` so its output is ignored. Here that
would (a) break the cobo-sealed, sha256-verified fence (ADR-012) and fail
`gitignore-drift.yml`, and (b) hide the very files that have to be *in* the
repository for GitHub to read them. The output is committed.

### 5. One version pin, in a group nothing else drags in

`ai-rulez==4.11.5` lives in a new `agents` dependency group — its own group for
the reason `sast` has one: `dev` includes `style` wholesale, so folding it in
would install it everywhere for a tool only two callers invoke. Upstream ships
pre-commit hooks, but adopting them would add a second `rev` pin beside this
one, the same drift editorconfig-checker and detect-secrets are local hooks to
avoid. Renovate's native uv manager covers the pin; ADR-020 freezes it in
`template/**`.

The PyPI package is a launcher that downloads the matching Go binary on first
run and verifies it against the published checksums. When the checksum file
itself cannot be fetched it warns and proceeds — worth knowing for a repo that
SHA-pins its actions, and the reason the pin is exact rather than a range.

### 6. Two gates, because a fixing hook alone is not one

- **prek** runs `ai-rulez generate` as a *fixing* hook (there is no `--check`
  for preset output; `ai-rulez verify` covers plugin bundles only). Like the
  formatters, it rewrites what drifted and fails the run when it had to.
- **tox `style`** runs `ai-rulez validate`, so a malformed source fails the
  canonical lint runner (ADR-003) even on a clone whose hooks were never
  installed.
- **`ci.yml`'s `hooks` job** additionally fails on *any* working-tree change
  with untracked files included. A fixing hook only fails on a modified
  **tracked** file, so a project that never committed its generated output would
  have it regenerated as untracked files and stay green — shipping a repository
  whose agent instructions exist on no branch. That gate is what makes step 2's
  "generate once, then commit" safe to rely on.

### 7. The two generators are proven to converge

A `.ai-rulez` scenario in `template-ci.yml` renders the toggle on, runs
`ai-rulez generate`, then runs the generated project's own fixing hooks
(`yamlfmt`, `end-of-file-fixer`, `trailing-whitespace`, `markdownlint-cli2` —
which ships `fix: true` — and `typos`) over the result and gates on `git diff`.
Two generators writing the same tree that disagree on one byte would leave a
repository that never converges: every `prek run` rewriting what the last
`generate` wrote, and back. ADR-030 demands the proof.

The scenario selects **every** offered host, not the three defaults. The width of
the gate is the width of the output it sees, and the defaults
(`claude`/`codex`/`copilot`) emit markdown alone — which converges. Two hosts do
not, and both were found only once the scenario covered them:

- `continue-dev` writes the one YAML file ai-rulez emits, and its generated
  header carries two trailing-space comment lines. `trailing-whitespace` strips
  them, the next `generate` puts them back — the loop above, exactly.
- `cursor` writes `.cursor/rules/*.mdc`: markdown with frontmatter, whose
  2-space list continuations fail `editorconfig-checker` because the anchored
  `\.md$` exclude does not reach the extra `c`.

A *checking* hook rejecting generated output is the worse of the two failures: it
cannot be satisfied at all, because the edit that would satisfy it is erased by
the next `generate`. That is the `.copier-answers.yml` shape, and it gets the
`.copier-answers.yml` answer — the hook skips the path a generator owns
(`.continue/prompts/` for `trailing-whitespace`/`yamllint`/`ec`, `.mdc` for
`ec`). Those excludes render only under the toggle and are inert unless the host
that produces the path is selected. So the scenario now also runs the checking
hooks (`check-json`, `yamllint`, and `editorconfig-checker` via `tox -e style`)
and gates on their exit codes, which `git diff` cannot speak for.

### 8. Migrating an existing project, in both directions

Neither direction is automatic — the template has no `_tasks` (ADR-015) — so both
are documented and both fail loudly rather than silently:

**Turning it on.** `include_ai_rulez` is seeded by the `full` preset, so the
first `copier update` of a `full`-preset project answers the new question `yes`
by default. That update deletes the copier-managed `AGENTS.md`/`CLAUDE.md`, adds
the `.ai-rulez/` sources and the `agents` dependency group, and runs no
generator — leaving the project with no agent instruction files. Dropping the
toggle from `full` was rejected: `full` means every toggle, and a preset that
quietly omits one is a worse surprise than a loud one. Instead
`_message_after_update` prints the two commands (`uv lock`, then
`ai-rulez generate`) and CI is red until their output is committed.

**Turning it off.** The host files are *not* copier-managed, so an update that
answers `no` re-renders `AGENTS.md`/`CLAUDE.md` but leaves every other generated
file (`.github/copilot-instructions.md`, `.codex/skills/…`, `.cursor/rules/…`)
committed and stale, still feeding instructions to the hosts that read them.
ai-rulez records exactly what it wrote in `.ai-rulez/.generated-manifest.json`
and `ai-rulez clean` is the inverse of `generate`, so the retirement is
mechanical — but it must run **before** the update, while the sources it reads
still exist:

```bash
uv run --group agents ai-rulez clean --force --keep-gitignore  # first
copier update                                                  # then answer no
```

`--keep-gitignore` is belt-and-braces: `gitignore = false` means there is no
ai-rulez block to remove, and `.gitignore` is cobo-sealed (ADR-012).

## Consequences

- Four more hosts get first-class instructions, and the `repo-setup` skill stops
  being Claude-only, for one answer instead of N hand-written files.
- Adding a host later is a `copier update` with one changed answer.
- A generated project gains a build step it did not have. The failure mode is
  loud (CI red, with the command in the error message), not silent.
- `.gitattributes` deliberately does **not** mark the output `linguist-generated`:
  the path set differs per host and is ai-rulez's contract, so re-encoding it
  here would be a second copy that rots. The files carry their own DO-NOT-EDIT
  banner instead.
- MegaLinter's cspell dictionary gains `rulez`/`blake` under the toggle; cspell
  is report-only (ADR-013), so this is noise reduction, not a gate.
- MegaLinter's `COPYPASTE_JSCPD` will report the generated host files as clones
  of each other, which they are — three renderings of one source is the whole
  point. It is left unexcluded on purpose: the exclusion would have to spell out
  ai-rulez's per-host output paths, the same second copy the `.gitattributes`
  decision below refuses, and MegaLinter runs with `DISABLE_ERRORS: true`
  (ADR-013), so the cost is a Security-tab finding rather than a red job.
- `ai-rulez generate` writes `.ai-rulez/.generated-manifest.json` — a generated
  file inside the source tree. It is committed (it is what `ai-rulez clean`
  reads), it is covered by the prek hook's `^\.ai-rulez/` gate and the
  `documentation` labeler glob, and its content is stable for a fixed host set.
- `ai_rulez_presets` is the template's first **list-valued** answer, which
  surfaced a latent defect: copier writes block sequences unindented, so
  `.copier-answers.yml` fails the generated project's own yamllint
  `indentation` rule — an unfixable failure, since the file must not be
  hand-edited. The yamllint hook now skips it, as the yamlfmt hook already did
  for the same reason. Any future list answer would have hit this.
- The template now has two agent-instruction shapes to keep working. The macro
  split (step 1) is what keeps that from meaning two copies of the prose, and the
  harness asserts both shapes render.
