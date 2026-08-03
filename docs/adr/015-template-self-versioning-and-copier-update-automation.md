# ADR-015: Template self-versioning + downstream `copier update` automation

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
  no source version file to bump; `simple` maintains only the manifest,
  `CHANGELOG.md`, and tag), `bump-minor-pre-major: true`, `include-v-in-tag: true`,
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

**Token caveat (the default `GITHUB_TOKEN` has two limits).** The workflow falls
back to the built-in `GITHUB_TOKEN`, but that token:

1. **cannot push changes to `.github/workflows/*`** — a hard GitHub security rule
   (the token lacks the `workflow` scope, and it is not grantable via
   `permissions:`). Because template updates frequently touch workflow files, an
   update that does so **fails to open the PR at all** on the default token; and
2. **does not trigger the project's own `push`/`pull_request` checks** on the PR
   it opens — GitHub suppresses token-created events to prevent recursion loops,
   so the runs are **absent entirely, not queued in a pending-approval state**
   (that approval gate is a separate mechanism, for fork PRs from first-time
   contributors, and does not apply to this same-repo token-created PR). A bad
   3-way merge therefore surfaces only as **visible conflict markers in the
   draft's diff**, not a red CI check.

Both limits are lifted by setting a `COPIER_UPDATE_TOKEN` — a **persistent**
credential (a fine-grained PAT, or a classic PAT with `repo` + `workflow` scope)
carrying contents + pull-requests + **workflows** write. A GitHub App
*installation* token is deliberately not recommended as the stored secret because
it expires hourly; an App-based setup must mint one at runtime instead. The
workflow prefers it over `GITHUB_TOKEN`
(`${{ secrets.COPIER_UPDATE_TOKEN || secrets.GITHUB_TOKEN }}`) and reads it
**only** in the scheduled/dispatch run — never a `pull_request` job — so the
write credential is never exposed to code from the update PR. Keeping the
fallback preserves the zero-external-setup default (updates that do not touch
workflows still work with no secret); the token is a documented opt-in (generated
`CONTRIBUTING.md`, "Template updates"), mirroring how release-please's own docs
treat cross-workflow triggering. Because the token limitation means many updates
need the secret to open a PR, the `CONTRIBUTING` entry states this plainly rather
than presenting the secret as purely cosmetic.

`draft: true` is a **merge-convenience** (it blocks accidental merge before
reconciliation), **not** a security boundary: it forces no approval, and the
generated branch protection does not require PR reviews by default. The actual
safety boundaries are the two above — no template code executes during the update
(`--skip-tasks`), and the write credential is confined to the scheduled job
(never a PR-triggered one). A project that wants a human to approve every template
update should additionally require pull-request reviews in branch protection.

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
