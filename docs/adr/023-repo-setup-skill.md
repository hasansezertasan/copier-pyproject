# ADR-023: Ship a resume-driven repo-setup skill, single-sourced from the setup doc

## Status

Proposed (2026-08).

## Context

A generated project's one-time repository setup — squash-merge policy, workflow
permissions, branch protection / ruleset sync, PyPI trusted publishing, GitHub
Pages, Discussions, and the optional secrets/App installs — is documented as
one actor-tagged home in `docs/maintaining/setup.rst` (ADR-022). Every step is
already tagged `[AGENT]` (a scriptable `gh`/CLI command) or `[HUMAN]`
(browser-only), precisely so a skill can drive it.

Today that prose is executed two ways, both lossy:

- A human reads the doc and hand-runs the commands.
- The companion **plugin** `setup` skill (`skills/setup/`, installed via the
  copier-pyproject plugin) reads the doc and walks a maintainer through it. It
  is external — it only helps someone who has installed the plugin, and it
  carries a hand-maintained "Verify (externally — CI won't)" list of checks that
  duplicates knowledge the doc should own.

Neither is available to an arbitrary agent that simply opens a freshly generated
repository, and neither knows, per step, whether that step is *already done* — so
re-running setup means re-reading prose and re-deciding each item by hand. The
setup is invisible to CI (a green sweep proves nothing), so "am I done?" is a
real, repeated question with no scriptable answer today.

The `infra-setup` skill in `infra-copilot` is the reference implementation of the
pattern that fits: a thin router over actor-tagged steps, each carrying an
idempotent check, that resumes at the first not-yet-done step and pauses only for
the human-only ones.

The template repository has the **same** shape of one-time setup for *itself*
(the squash-merge policy and `default_workflow_permissions=write` release-please
needs — see CLAUDE.md "Template self-versioning (this repo, ADR-015)"), executed
today only as CLAUDE.md prose.

## Decision

Ship a **resume-driven repo-setup skill**, single-sourced from the setup doc, in
two symmetric places, and give each setup step an idempotent check that lives in
**one** place.

### 1. The check is a third tag in the setup doc — no separate manifest

Extend `docs/maintaining/setup.rst` so every actionable step carries a `[CHECK]`
block alongside its `[AGENT]`/`[HUMAN]` block: a shell command where **exit 0
means the step is already done**. The doc stays the single source of truth
(ADR-022); the skill is a consumer, not a second copy.

We deliberately reject a standalone `steps.yaml` manifest (as the issue floated).
A separate machine file would re-encode the commands, actor tags, and the Jinja
copier-gating the doc already carries, and would have to be kept in lockstep with
it — reintroducing exactly the drift ADR-022 collapsed. RST is not the tidiest
machine format, but the skill's consumer is an LLM-driven router reading prose,
not a parser, so the doc's readability is sufficient and the single-source
guarantee is worth more than a tidier schema.

Three flavors of `[CHECK]`:

- **`[AGENT]` steps** get a real idempotent check that verifies the *end state*
  the step establishes, not a weaker proxy (e.g. merge policy via `gh repo view
  … --json squashMergeAllowed,… --jq`; workflow permissions asserting **both**
  `can_approve_pull_request_reviews` and the least-privilege
  `default_workflow_permissions == "read"`; the classic branch protection
  asserting `strict` plus its contexts; the ruleset variant querying the applied
  `Protect main` ruleset is `enforcement: active`, not merely that its admin
  token exists; Pages asserting `source.branch`/`source.path`, not merely that a
  site exists).
- **`[HUMAN]` steps that store a secret** (any of `REPO_ADMIN_TOKEN`,
  `DOCKERHUB_USERNAME`/`DOCKERHUB_TOKEN`, `HOMEBREW_TAP_TOKEN`,
  `SCOOP_BUCKET_TOKEN`, `SONAR_TOKEN`, `CODECOV_TOKEN` — i.e. every setup secret)
  check the *artifact* by exact name — `gh secret list … --json name --jq` for a
  precise match. Minting the credential is human; its presence is scriptable.
- **`[HUMAN]` steps with no API-visible artifact** (PyPI publisher registration,
  the release-immutability toggle, the Settings/Sourcery/Renovate App installs)
  carry an explicit `# no scriptable check — confirm in browser`, so the skill
  treats them as a manual confirm gate rather than silently passing them.

The checks the plugin `setup` skill kept in its "Verify (externally)" section
move **into** the doc as these `[CHECK]` blocks, so both skills consume one
source.

### 2. A skill shipped *into* generated projects

`template/.claude/skills/repo-setup/SKILL.md` becomes
`.claude/skills/repo-setup/SKILL.md` in every generated project. It carries no
`{{ }}` substitutions (it reads the already-interpolated setup doc), so it ships
as plain Markdown with no `.jinja` suffix — copier copies everything under
`template/` and renders only `.jinja`-suffixed files, so this file is copied
verbatim. `.claude/skills/` is a Claude Code auto-discovery path, so any agent
opening the repo finds it without the plugin. It is a lean **resume-driver**, not
a prose duplicate of the doc:

- Walk `docs/maintaining/setup.rst` top-to-bottom (its order already *is* the
  dependency order — ADR-022 sections are sequenced deliberately) and **never
  abort the walk before the end** — collect outcomes and report them together.
- Classify each step by where it sits in the doc, because the class decides what
  a red `[CHECK]` means:
  - **Required** (above `Optional integrations`, minus the deferred two): red
    `[AGENT]` → run the command and re-check; red `[HUMAN]` → emit a handoff
    (batched across the walk, not a hard stop); a still-red required step is
    recorded as a blocker and the walk continues.
  - **Deferred** (GitHub Pages and the PR doc previews): their `[CHECK]` is
    expected red on a fresh repo because the `gh-pages` branch does not exist
    until the first release's `deploy-docs` runs. The skill records them as
    "deferred" and continues — it never runs their `[AGENT]` command or stops on
    them pre-release. This is the fix for a naïve walk deadlocking at Pages before
    reaching Renovate/Discussions/optional.
  - **Optional** (under `Optional integrations`): a red check means "not
    configured", a fine end state; the skill **asks** configure-or-skip and
    records the choice rather than driving it unprompted. These are not uniformly
    credential-minting — some are just a GitHub App install (Sourcery, Settings).
- A copier-gated section that did not render is absent from the doc, so its steps
  are simply not walked — the gating is inherited from the doc for free.
- Re-running is safe and idempotent; an all-green walk reports "nothing to do".

### 3. A symmetric skill for the template repo's own setup

`.claude/skills/repo-setup/` at this repository's root (repo-local, **not**
shipped under `template/` and **not** part of the plugin's `./skills/`) drives
*this* repo's one-time setup with the same resume shape. Its steps are few
(squash-merge policy; `default_workflow_permissions=write` +
`can_approve_pull_request_reviews=true`), so the step + `[CHECK]` pairs live
**inline** in its `SKILL.md` rather than in a doc — there is no doc home to
justify, and inlining a two-step manifest is not the drift surface a fifteen-step
one would be. It loudly flags the deliberate **`write`-not-`read`** divergence
from generated projects (CLAUDE.md gotcha #1) and points at CLAUDE.md's "Template
self-versioning (this repo, ADR-015)" for the rationale rather than restating it.

### 4. The plugin `setup` skill stays, with one cross-reference

`skills/setup/` keeps its richer cross-project value (dependency-order rationale,
timing traps, the gotchas table) — it serves someone working across *many*
generated projects, including ones generated before this skill shipped. Its
duplicated verify commands are removed in favor of the doc's `[CHECK]` blocks,
and it gains one line noting that newly generated projects now carry an in-repo
`repo-setup` skill. It is not otherwise rewritten.

## Consequences

- Any agent opening a generated repo can run setup to completion with no plugin
  install, and re-run it safely — one walk reports what is already done, what is
  deferred, what still blocks, and which optional steps are left unconfigured.
- The setup doc gains a `[CHECK]` contract: **every future setup step must carry
  a `[CHECK]` block** (real, secret-presence, or the explicit no-scriptable-check
  marker) to stay machine-drivable, just as ADR-022 made `[AGENT]`/`[HUMAN]`
  mandatory. This is the maintenance cost, and it is one file.
- No `steps.yaml`: no second copy of the commands/gating to drift, consistent
  with ADR-022's single-source consolidation.
- The template repo's own bootstrap is now scriptable-and-resumable too, and the
  `write`-vs-`read` workflow-permission gotcha is encoded where an agent will act
  on it, not only in prose.
- The shipped `SKILL.md` is a generated project's own Markdown and is subject to
  its markdownlint gate; being plain Markdown (no Jinja) it sidesteps the
  whitespace rules that guarded-section conditionals would otherwise have to
  respect.
- This does not touch `copier.yml` `_tasks` (there are none — ADR-015): the skill
  is a rendered file, not a post-copy task, so it does not jeopardize Renovate's
  hosted copier manager (which disallows `--trust`).
