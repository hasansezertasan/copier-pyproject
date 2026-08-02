# ADR-014: Template self-versioning + downstream `copier update` automation

## Status

Proposed (2026-08). Prompted by
[hwid#113](https://github.com/hasansezertasan/hwid/pull/113) — a fully
hand-driven `copier update` that pinned raw commit SHAs (`00ce24c` → `082f641`)
because the template exposed no versions and downstream repos had no signal that
an update even existed.

## Context

Copier already ships the propagation mechanism: every generated project carries a
`.copier-answers.yml` recording the template ref it was built from, and
`copier update` re-renders the newer template over the project with a git 3-way
merge. hwid#113 is exactly that mechanism, run by hand.

Two gaps kept it manual, and will keep it manual for every future adopter:

1. **The template repo published no versions.** It had *zero git tags*; the repo
   root has no `pyproject.toml`/`package.json` and no release automation of its
   own (all of the template's release-please machinery targets *generated*
   projects, not itself). `copier update` compares `.copier-answers.yml._commit`
   against the latest template **tag** by default — with no tags, "is there an
   update?" is unanswerable, so hwid#113 had to pin SHAs and drive the update by
   hand.
2. **Nothing in a generated project watched for or pulled updates.** The only
   path was a human remembering to run `copier update` (or the
   `adopt-copier-pyproject` skill). This does not scale past a couple of repos.

## Decision

Close both gaps, in two layers.

### Layer 1 — the template versions itself (release-please, `simple`)

Add release-please to the **template repository itself** so template changes
produce semver git tags (`v0.1.0`, …). New files at the **repo root** (distinct
from the `template/`-shipped release-please that versions generated projects):

- `.github/release-please-config.json` — `release-type: "simple"` (the repo has
  no source version file to bump; `simple` maintains the manifest + `CHANGELOG.md`
  + tag only), `bump-minor-pre-major: true`, `include-v-in-tag: true`,
  `draft: false` (no release artifacts to attach, unlike a package release).
- `.github/release-please-manifest.json` — seeded `{ ".": "0.0.0" }`, mirroring
  the generated-project convention. The **first** release PR therefore lands as
  **v0.1.0** (bump-minor-pre-major over the accumulated `feat:` history), which is
  the intended starting version.
- `.github/workflows/release.yml` — a single `release-please` job on push to
  `main`, hardened to the repo's zizmor/ghalint posture (SHA-pinned,
  `permissions: {}` top-level with per-job least privilege,
  `persist-credentials: false`). No build/publish jobs — the template is not a
  distributable package.

The template's commits are already Conventional Commits (enforced by
`check-pr-title` + squash-to-title), so bumps derive automatically with no manual
tagging — the same contract ADR-002 relies on for generated projects.

### Layer 2 — generated projects pull updates automatically

Ship a new **always-on** static workflow
`template/.github/workflows/copier-update.yml` into every generated project
(no toggle — same posture as `gitignore-drift.yml`). It:

- runs on a **weekly `schedule`** + `workflow_dispatch`;
- runs `uvx copier update --trust --skip-tasks --defaults --skip-answered`
  (`--defaults`/`--skip-answered` keep it non-interactive and preserve recorded
  answers; the token/task rationale is below);
- opens a PR via `peter-evans/create-pull-request` onto a `chore/copier-update`
  branch labelled `no-issue` — **never pushes to the default branch**, so it
  respects the squash-merge policy and needs no persisted git credentials,
  exactly like `all-contributors.yml`.

Because `copier update` walks to the latest template **tag**, Layer 2 only
produces a PR when Layer 1 has cut a new release — no tag, no noise.

It is a plain `.yml` (not `.jinja`): Copier's default `_templates_suffix: .jinja`
copies it verbatim, so its `${{ … }}` GitHub Actions expressions survive
rendering without `{% raw %}` wrapping, matching every other static shipped
workflow (`codeql.yml`, `zizmor.yml`, …).

### The bot drafts; the human reconciles

The auto-PR is a **starting point, not a merge-ready change**. It is opened as a
**GitHub draft** (`draft: true`) so it cannot be merged before review. A 3-way
merge can leave conflict markers or `.rej` files where a project's local edits
diverge from the template (README identity, `.cspell.yml` word lists — precisely
hwid#113's "Reconciliation" section). The PR body says so and points at the
`adopt-copier-pyproject` workflow. This is deliberately non-blocking and
best-effort — the same posture as `gitignore-drift.yml` and the
`check-security.yml` cron: automation delivers the **signal + the draft**, never
the judgment.

**Token caveat (why the signal is the *diff*, not a red check, by default).** A
PR opened with the workflow's default `GITHUB_TOKEN` does **not** trigger the
project's own `push`/`pull_request` checks — GitHub suppresses events caused by
that token to prevent workflow-recursion loops. So out of the box the "human
needed here" signal is the **visible conflict markers in the draft's diff**, not
a red CI check. Projects that want the update PR to run checks like any other set
a `COPIER_UPDATE_TOKEN` secret (a PAT or GitHub App token), which the workflow
prefers over `GITHUB_TOKEN`. Keeping the fallback preserves the zero-external-setup
default; the secret is a pure opt-in, mirroring how release-please's own docs
treat cross-workflow triggering.

**No unattended template-code execution (`--skip-tasks`).** The draft-PR review
gate protects against malicious *file content* a compromised template might
render — a human sees it before merge. It does **not** protect against `_tasks`
*execution*: `--trust` would run template task code during the workflow,
unattended, in a job holding `contents: write`/`pull-requests: write` and the
token, before any PR exists. So the update command passes **`--skip-tasks`**:
Copier still requires `--trust` to proceed when the template *defines* tasks
(the flag does not imply trust), but no task code runs. The template's only task
(`git init`) is additionally gated `when: "{{ _copier_operation == 'copy' }}"`,
so it is a no-op on update regardless. Since this template defines no
`_migrations` or `_jinja_extensions`, `--skip-tasks` neutralizes *all* template
code execution on the scheduled path — keeping the workflow single-job (no
read-only/write-only split) while removing the one execution vector the review
gate can't cover. If the template ever grows a migration (which `--skip-tasks`
does not cover), isolating the write token into a separate PR-creation job would
be the next step.

## Consequences

- **Positive.** Downstream repos learn about template changes without anyone
  watching the template. Every current and future generated project inherits the
  behavior. Template releases gain a real changelog and semver history.
- **Bootstrapping (one-time chicken-and-egg).** Existing generated repos do not
  have `copier-update.yml` until they pull one more template update that adds it —
  seed it via a single manual `copier update` (or cherry-pick the file), after
  which the repo self-sustains.
- **First template changelog is large.** Seeding the manifest at `0.0.0` means the
  first release PR aggregates the accumulated commit history into the v0.1.0
  changelog. This is a one-time cosmetic artifact and is acceptable.
- **Setup already satisfied.** The auto-PR needs "Allow GitHub Actions to create
  and approve pull requests" — already required and documented for release-please,
  so no new repository setting.
