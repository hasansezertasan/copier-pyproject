# Agent instructions in generated projects

## ai-rulez is the opt-in single source for agent instructions, with the prose in shared macros

**Id:** e1545d12-ac20-426b-9cd5-519e80a56b5f
**Type:** decision
**Status:** superseded
**Superseded by:** 249600a2-79c3-49b9-b4b5-277ccc245d1b
**Evidence:** confirmed
**Source:** ADR-035 ([`docs/adr/035-ai-rulez-as-the-agent-instruction-source.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/035-ai-rulez-as-the-agent-instruction-source.md)), §1 and §5; issue #309
**Revisit when:** a host stops reading its generated file, ai-rulez leaves PyPI, or a sixth host is expected to open PRs
**See:** repo-setup.md#a-resume-driven-repo-setup-skill-reads-check-blocks-from-the-setup-doc-no-separate-manifest — 68ac4665-dcde-456b-aef7-2faaf6fe51f4 — as of 2026-10-11
**See:** template-testing.md#collection-literals-are-rendered-through-one-shared-macro — 47b21a49-5fc4-46b8-b450-7d9f3225706c — as of 2026-10-11

`include_ai_rulez` (default off, `full` preset) with an `ai_rulez_presets`
multiselect renders `.ai-rulez/` sources from which ai-rulez generates each
host's native instruction files and skill copies. With the toggle off, the
hand-written `AGENTS.md` and the Claude-only skills render. The section prose
lives once in `_macros.jinja`; both the hand-written file and the rule sources
call the same macros. The pin lives in its own `agents` dependency group,
exact, Renovate-tracked through the native uv manager.

**Reason:** the generated project's branch-name check already whitelists five
agent prefixes, but only Claude received the repo-setup skill and only two
hosts received instructions; hand-writing five formats is the duplication the
template exists to remove; four of the five agents got nothing, not even
`.github/copilot-instructions.md`, which GitHub's Copilot coding agent and PR
review read server-side. [ai-rulez](https://github.com/Goldziher/ai-rulez)
(MIT, Go) authors rules, context, skills, agents and commands once and
generates tool-native output for 20 hosts. It ships on PyPI (no Node) and has
the cobo shape — sources in, committed output out, a check that proves they
agree. A
second hand-maintained copy of the paragraphs would recreate inside the
template the drift it removes downstream. Its own group because `dev` includes
`style` wholesale and only two callers invoke the tool; upstream's pre-commit
hooks would add a second `rev` pin. The exact pin matters because the PyPI
launcher downloads a Go binary and proceeds with a warning if the checksum file
cannot be fetched.

**Rejected alternative:** hand-written per-host files — five dialects drifting.

## Generated host files are build output; the template renders none of them

**Id:** e827d3fc-e3f6-4852-b2e3-d56180eac949
**Type:** decision
**Status:** superseded
**Superseded by:** 249600a2-79c3-49b9-b4b5-277ccc245d1b
**Evidence:** confirmed
**Source:** ADR-035 §2 and §8 ([`docs/adr/035-ai-rulez-as-the-agent-instruction-source.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/035-ai-rulez-as-the-agent-instruction-source.md))
**Revisit when:** ai-rulez and copier produce identical bytes for the same content, or the template gains a post-render step
**See:** agent-instructions.md#ai-rulez-is-the-opt-in-single-source-for-agent-instructions-with-the-prose-in-shared-macros — e1545d12-ac20-426b-9cd5-519e80a56b5f — as of 2026-10-11
**See:** template-updates.md#copieryml-defines-no-_tasks — 86130379-1660-4992-8aba-8b6cd7b4a9f7 — as of 2026-10-11

The template renders `.ai-rulez/` and stops. `AGENTS.md`, the Copilot
instructions and the per-host skill copies are written by the adopter's first
`ai-rulez generate` and committed from then on. Turning the toggle on via
update leaves a project with no instruction files until the generator runs
(the after-update message names the two commands, `uv lock` then the
generator; CI is red until the output is committed). On a fresh copy the
generator is an explicit numbered step of the after-copy message, beside
`git init` and `uv sync`. Turning it off requires running ai-rulez's clean
command before the update, while the sources it reads still exist, because the
host files are not copier-managed and would otherwise stay committed and stale.
Clean reads `.ai-rulez/.generated-manifest.json`, which the generator writes
into the source tree; it is committed, and the prek `^\.ai-rulez/` gate and the
`documentation` labeler glob cover it. Clean is run with ai-rulez's
keep-gitignore flag as belt-and-braces: `gitignore = false` leaves no ai-rulez
block to remove and the `.gitignore` is cobo-sealed.

**Reason:** copier's renderer and ai-rulez's renderer produce different bytes
for the same content (ai-rulez composes its own headings and stamps a
provenance header with a content hash), so rendering both would diff on first
generate and every `copier update` would re-render on top of generated files —
churn on files the adopter never touched. As build output they sit outside the
3-way merge, which then covers only the small per-rule sources. Neither
direction is automatic because the template has no tasks. Dropping the toggle
from `full` was rejected: `full` means every toggle, and a preset that quietly
omits one is a worse surprise than a loud one.

**Rejected alternative:** render the generated files as well — the churn above.

**Rejected alternative:** mark the generated host files `linguist-generated` in
`.gitattributes` — the path set differs per host and is ai-rulez's contract, so
re-encoding it would be a second copy that rots. The files carry their own
DO-NOT-EDIT banner instead.

## No builtin ai-rulez domains, and ai-rulez never touches `.gitignore`

**Id:** e9823c4a-891f-4344-8d64-029dd8d31138
**Type:** decision
**Type:** constraint
**Status:** superseded
**Superseded by:** 249600a2-79c3-49b9-b4b5-277ccc245d1b
**Evidence:** confirmed
**Source:** ADR-035 §3–4 ([`docs/adr/035-ai-rulez-as-the-agent-instruction-source.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/035-ai-rulez-as-the-agent-instruction-source.md))
**Revisit when:** a builtin domain stops contradicting a gate the project enforces, or the gitignore stops being cobo-sealed
**See:** gitignore-generation.md#cobo-generates-the-gitignore-with-a-hash-sealed-fence-and-lockfiles — 3e3bc38e-bc1e-4e65-b74d-e91848262157 — as of 2026-10-11

`builtins = false`: the shipped rules are only the project's own.
`gitignore = false`: the generated output is committed and ai-rulez does not
rewrite the ignore file.

**Reason:** every one of the seven auto-included builtin domains (of 33
shipped) either restates a gate or contradicts it — complexity 20 versus ruff's
5, 120 columns versus 88, Google-style docstrings and 80% coverage versus
ruff's pep257 and 99%, "use conventional commits" versus the blocking title
check, "descriptive branch names" versus Conventional Branch and the blocking
`check-branch-name.yml`. A rule an agent obeys and a gate that fails it must never
be two separately maintained sentences, and per-domain exclusions would leave
the next release free to add a contradiction to a domain opted into. Off
entirely also keeps the generated file ~60 lines instead of ~270. ai-rulez's
default gitignore rewrite would break the cobo-sealed fence and hide the very
files GitHub must find in the repository.

**Rejected alternative:** per-domain `!` exclusions — the next-release risk.

## Two gates plus a convergence scenario over every host

**Id:** b23fd420-5b88-4075-93ad-5122b4f7622e
**Type:** decision
**Type:** incident
**Status:** superseded
**Superseded by:** 249600a2-79c3-49b9-b4b5-277ccc245d1b
**Evidence:** confirmed
**Source:** ADR-035 §6–7 ([`docs/adr/035-ai-rulez-as-the-agent-instruction-source.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/035-ai-rulez-as-the-agent-instruction-source.md))
**Revisit when:** ai-rulez gains a check mode for preset output, or a host's generated output changes format
**See:** template-testing.md#generated-files-must-be-formatter-canonical-not-merely-valid — 9b931598-7e52-4ff1-bb07-ef65c01d5369 — as of 2026-10-11
**See:** lint-orchestration.md#the-tox-style-env-is-the-sole-authoritative-lint-suite-prek-is-a-fast-gate-not-a-second-suite — 9b74fc8b-a808-4f2b-bdbd-9e4253c1b35a — as of 2026-10-11

prek runs the generator as a fixing hook; tox `style` runs `ai-rulez validate`;
and `ci.yml`'s hooks job additionally fails on any working-tree change
including untracked files. A template-ci scenario renders the toggle on with
*every* offered host, runs the generator, then the generated project's own
fixing hooks, and gates on `git diff`; it also runs the checking hooks and
gates on their exit codes. Checking hooks skip the paths a generator owns
(`.continue/prompts/` for trailing-whitespace, yamllint and the editorconfig
checker; `.mdc` for the editorconfig checker), rendered only under the toggle.

**Reason:** there is no check mode for preset output, and a fixing hook only
fails on a modified *tracked* file — a project that never committed its output
would have it regenerated untracked and stay green, shipping instructions that
exist on no branch. Two generators writing one tree that disagree on a byte
leave a repository that never converges. The defaults emit markdown alone and
converge; two hosts found only once the scenario covered every host do not —
continue-dev's YAML header carries trailing-space comment lines the whitespace
hook strips and the next generate restores, and cursor's `.mdc` rules fail the
editorconfig checker because the `\.md$` exclude does not reach the extra
character. A checking hook rejecting generated output cannot be satisfied at
all, so it gets the `.copier-answers.yml` answer: skip the generator-owned
path.

**Consequence:** the width of the gate is the width of the output it sees;
every offered host widens the scenario that must keep passing.

**Consequence:** MegaLinter's `COPYPASTE_JSCPD` reports the generated host
files as clones of each other, which they are. It is left unexcluded on
purpose: an exclusion would spell out ai-rulez's per-host output paths, the
same second copy refused for `.gitattributes`, and MegaLinter runs with
`DISABLE_ERRORS: true`, so the cost is a Security-tab finding, not a red job.

**Consequence:** `ai_rulez_presets` is the template's first list-valued answer,
which surfaced a latent defect: copier writes block sequences unindented, so
`.copier-answers.yml` fails the generated project's own yamllint `indentation`
rule, and the file cannot be hand-edited. The yamllint hook now skips it, as the
yamlfmt hook already did; any later list answer would have hit the same thing.

## No `CLAUDE.md` by default; `claude` left the preset defaults; `gemini` is no longer offered

**Id:** 1a6849be-72d0-4990-abe2-7a0243cd5e67
**Type:** decision
**Status:** needs-review
**Evidence:** confirmed
**Source:** ADR-035, 2026-10 amendment ([`docs/adr/035-ai-rulez-as-the-agent-instruction-source.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/035-ai-rulez-as-the-agent-instruction-source.md))
**Revisit when:** Claude Code stops reading `AGENTS.md` natively, or the maintainers start using Gemini
**See:** agent-instructions.md#ai-rulez-is-the-opt-in-single-source-for-agent-instructions-with-the-prose-in-shared-macros — e1545d12-ac20-426b-9cd5-519e80a56b5f — as of 2026-10-11

The default shape uses `AGENTS.md` alone, including for Claude Code. The former
`@AGENTS.md` wrapper is neither rendered nor preserved on update any more, so
an update deletes leftover copies (customized ones too). `ai_rulez_presets`
defaults to `codex` and `copilot`; `claude` is still offered but not default;
`gemini` was removed from the choices.

**Reason:** Claude Code reads `AGENTS.md` natively, removing the only reason the
wrapper existed — and a leftover `CLAUDE.md` makes Claude Code's default mode
*skip* `AGENTS.md`, the opposite of what the default shape wants. The `codex`
host already writes `AGENTS.md`, so `claude` only added a duplicate wrapper and
a `.claude/` tree. The maintainers do not use Gemini and every offered host
widens the convergence scenario.

**Rejected alternative:** keep excluding `CLAUDE.md` from updates to protect
adopter guidance — kept a file that actively harmed the default; the README
tells adopters to move unique guidance first, and git history keeps the old
content.

**Consequence:** by default the per-host skills no longer reach Claude Code,
which looks under `.claude/skills/`; adopters who want them select `claude`.
Removing a choice has a sharp edge: a `--defaults` update (what Renovate runs)
silently replaces a recorded selection containing a removed choice with the new
defaults, so a project that selected `gemini` loses every other host too and
keeps a stale `GEMINI.md`; such a project cleans before updating and re-selects.

## ai-rulez is removed; the template ships one hand-written `AGENTS.md` and no per-host files

**Id:** 249600a2-79c3-49b9-b4b5-277ccc245d1b
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** issue #428 (maintainer decision), 2026-10-19
**Revisit when:** copier-skill-repo stops generating per-host agent and skill files, or an adopter needs per-host files this template must render itself
**See:** agent-instructions.md#ai-rulez-is-the-opt-in-single-source-for-agent-instructions-with-the-prose-in-shared-macros — e1545d12-ac20-426b-9cd5-519e80a56b5f — as of 2026-10-19
**See:** repo-setup.md#the-repo-setup-skill-is-no-longer-shipped-the-setup-doc-is-read-directly — 4ff05ee1-3b53-423d-96cf-acb7681b6a97 — as of 2026-10-19

`include_ai_rulez`, `ai_rulez_presets`, the `.ai-rulez/` sources, the `agents`
dependency group, the prek hook, the tox `ai-rulez validate` command and the CI
convergence scenario are gone. `AGENTS.md` is always rendered from the
`agent_*()` macros in `_macros.jinja`. The adjacent entries on ai-rulez (build
output, no builtins, the convergence gates) are superseded with the toggle;
the rule that the template renders no `CLAUDE.md` still stands, but its
mention of `ai_rulez_presets` is obsolete, so that entry is `needs-review`.

**Reason:** copier-skill-repo now generates agent and skill files per host, so
keeping a second generator in this template duplicated it and carried the
cost the earlier entries record (non-copier-managed output, two-way manual
update steps, extra lint exclusions).

**Rejected alternative:** keep the toggle beside copier-skill-repo — two
generators for the same files, and the update hazards stay.

**Consequence:** breaking change (`refactor!`). Adopters with
`include_ai_rulez=true` must migrate: run `ai-rulez clean --force
--keep-gitignore` before updating, then move any guidance from the `.ai-rulez/`
sources into `AGENTS.md`. Adopters with it off see only the removed question.
