---
name: setup
description: Use for the one-time repository + external-service setup a project scaffolded from the hasansezertasan/copier-pyproject Copier template needs before its automation works — trusted publishing, branch protection / required checks, squash-merge policy, "Actions can open PRs", release immutability, GitHub Pages, Renovate, and the optional secrets/App installs (CODECOV_TOKEN, DOCKERHUB, HOMEBREW_TAP_TOKEN, SCOOP_BUCKET_TOKEN, SONAR_TOKEN, Settings/Sourcery/all-contributors). Reach for it whenever a generated project's release-please PR never opens, PyPI publish fails, docs 404 on Pages, Renovate/copier-update PRs never appear, or someone asks to "wire up releases", "configure the repo", or "finish setup" — this config is invisible to CI (a green sweep proves nothing), so it is never caught automatically.
---

# Set up a copier-pyproject project's repository & release automation

## Overview

A freshly generated `copier-pyproject` project **passes CI green with none of this
done.** Every piece here lives *outside* the code — branch settings, secrets, App
installs, a PyPI publisher registration — so no linter, type check, or test suite
can catch a missing step. The failures surface later and off to the side: the
release PR silently never opens, the first `git tag` fails to publish to PyPI, the
docs URL 404s, Renovate stays quiet. **A green sweep is not evidence setup is done.**

This is distinct from adopting the template into an existing package (that is the
`adopt` skill, which reconciles source/config collisions). This skill assumes the
project files are already correct and only wires up the repo + external services.

**Design: the shipped `docs/maintaining/setup.rst` is the source of truth for the
exact commands.** The generated project's `docs/maintaining/setup.rst`
("Repository setup", published under **Maintainer guide** on the docs site)
carries every `gh` command already interpolated with the real owner/repo, plus
the optional steps gated on this project's Copier answers. Each step is tagged
**`[AGENT]`** (a shell command you can run unattended) or **`[HUMAN]`**
(browser-only — sign up, mint a credential, install an App, or a UI-only toggle),
so the tags tell you directly which steps you execute and which you must hand to
a human. Do **not** hand-transcribe commands from memory — read that doc and run
what it ships, so you never drift from the template version the project is
actually on. (The contributor-facing `.github/CONTRIBUTING.md` only *points* to
this doc; it no longer carries the commands.) This skill owns what prose can't:
the **order**, the **dependencies between steps**, the **timing traps**, and the
**failure symptom** each step prevents.

## First: read what this project actually needs

Two files tell you the exact scope before you touch anything:

1. **`docs/maintaining/setup.rst` → "Repository setup"** — the ready-to-run
   `gh` commands (already interpolated), each tagged `[AGENT]`/`[HUMAN]`. Optional
   steps (Docker Hub, Homebrew, Scoop, SonarCloud, Sourcery, all-contributors,
   Settings App) are rendered in only when the matching Copier answer is enabled —
   so the doc already lists *exactly* the steps that apply.
2. **`.copier-answers.yml`** — confirms which optional components/integrations are
   on (`include_web`, `include_homebrew`, `include_scoop`, `include_sonarcloud`,
   `include_sourcery`, `include_all_contributors`, `include_repo_settings`), so you
   can cross-check the setup-doc steps and know which secrets/Apps are needed.

Then work the dependency order below.

## Dependency order (why the sequence matters)

Do it in this order — several steps unblock others, and two cannot be done until
a later event has happened:

1. **Merge policy** (squash-only, commit message = PR title, delete head branches)
   — load-bearing for release-please: only a squash whose message is the validated
   PR title puts a Conventional Commit on `main` for release-please to read. Do
   this first; everything release-related depends on it.
2. **"Allow Actions to create and approve PRs"** — unblocks **both** release-please
   (opening the release PR) **and** the all-contributors workflow. Note the
   generated project uses **least-privilege `default_workflow_permissions=read`**
   with `can_approve_pull_request_reviews=true` (per-job workflows grant their own
   `write` scopes) — *not* `write`. Don't copy the template-repo's own `=write`.
3. **PyPI trusted publishing** — register the **pending** publisher *before* the
   first release, or the first `pypi-publish` job fails. Owner + repo + workflow
   `release.yml` + environment `publish` must match exactly.
4. **Branch protection / required status checks** — set the four contexts by name
   (`Validate PR title`, `Validate branch name`, `Verify linked issue`,
   `Task Completed Checker`). The `gh api .../branches/main/protection` call accepts
   contexts by name even before they have run; the **UI picker only lists a context
   after that check has run at least once** (open one throwaway PR first if using
   the UI). Requires a public repo or GitHub Pro for private.
5. **Release immutability** — UI-only toggle (Settings → General). Protects
   published tags/assets.
6. **Renovate App install** — inert config until installed; unblocks both routine
   dependency PRs **and** the copier-update manager (next).
7. **Optional secrets / Apps** — only those the setup doc lists for this
   project (see the conditional table below).

Two steps are **deferred until after the first release**, because they depend on an
event that has not happened yet on a brand-new repo:

- **GitHub Pages** — the `gh-pages` branch does **not exist** until the first
  release's `deploy-docs` job runs. Enable Pages (`source[branch]=gh-pages`,
  `path=/`) *after* that first release, or the API call fails / has nothing to
  serve. PR doc previews (`docs-preview.yml`) then work with no extra setup.
- **Enable Discussions** (`has_discussions=true`) can be done anytime, but do it
  before advertising the repo — `SUPPORT.md`, the issue-template chooser, and
  CONTRIBUTING all link the Discussions tab, which 404s until enabled.

## Conditional steps — apply only what this project enabled

Check `.copier-answers.yml`; run the step only when its answer is true. The
setup doc already renders exactly these, but this is the trigger→need map:

| Copier answer | One-time setup | Secret / App | Failure if skipped |
|---|---|---|---|
| `include_web` | Docker Hub publish (optional; GHCR always works token-free) | `DOCKERHUB_USERNAME` **+** `DOCKERHUB_TOKEN` (all-or-nothing) | Only one set → preflight **fails the whole release** (PyPI too); neither → GHCR-only, fine |
| `include_homebrew` | Create tap repo + listener (`docs/packaging/homebrew-tap/`) | `HOMEBREW_TAP_TOKEN` — fine-grained PAT, **Contents: write** on `<user>/homebrew-tap` only | Unset → `bump-homebrew` skips with a notice (release still passes) |
| `include_scoop` | Create bucket repo + listener (`docs/packaging/scoop-bucket/`) | `SCOOP_BUCKET_TOKEN` — same **Contents: write**-only PAT on `<user>/scoop-bucket` | Unset → `bump-scoop` skips with a notice |
| `include_sonarcloud` | Create SonarCloud org + project (key `<user>_<repo>`) | `SONAR_TOKEN` | Unset → `sonar` job records a `::notice::` and skips (non-blocking) |
| `include_sourcery` | Install Sourcery GitHub App | (App, no secret) | Config inert; no PR reviews |
| `include_all_contributors` | Nothing extra — reuses step 2's "Actions can open PRs" | (none) | Regenerate PR can't open if step 2 skipped |
| `include_repo_settings` | Install **Settings** GitHub App | (App, no secret) | `settings.yml` never syncs. **Escalates push→admin — pair with CODEOWNERS + "Require review from Code Owners"** (see gotcha) |

`CODECOV_TOKEN` is **not** in this table because it is unconditional-but-usually-
unneeded: on a **public** repo coverage uploads tokenless (no setup); a token is
only needed for a **private** repo or to dodge rate limits. Skipping it on a
private repo is non-fatal — CI records a `::notice::` and the build still passes.

## Verify (externally — CI won't)

None of this can be proven from a branch or a green CI run. Confirm each out of band:

- **Merge policy:** `gh repo view <owner>/<repo> --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed,deleteBranchOnMerge` → squash true, others false.
- **Workflow PR permission:** `gh api repos/<owner>/<repo>/actions/permissions/workflow` → `can_approve_pull_request_reviews: true`.
- **Branch protection:** `gh api repos/<owner>/<repo>/branches/main/protection --jq '.required_status_checks.contexts'` → the four contexts.
- **PyPI:** the pending publisher appears at <https://pypi.org/manage/account/publishing/>.
- **Renovate:** an onboarding PR appears after install; merge it.
- **Secrets:** `gh secret list --repo <owner>/<repo>`.
- **Pages (post-first-release):** `gh api repos/<owner>/<repo>/pages --jq '.html_url'` resolves.

## Gotchas (each is a silent, off-to-the-side failure)

| # | Gotcha | Fix |
|---|--------|-----|
| 1 | `default_workflow_permissions` — copying the **template repo's** `=write` into a **generated** project | Generated projects use least-privilege **`read`** + `can_approve_pull_request_reviews=true`; per-job workflows grant their own write scopes |
| 2 | Status-check contexts don't appear in the branch-protection **UI picker** until each check has run once | Use the `gh api .../protection` call (sets by name up-front), or open one throwaway PR first |
| 3 | Enabling **Pages** on a new repo fails — `gh-pages` branch doesn't exist yet | Defer Pages until *after* the first release runs `deploy-docs`; it creates the branch |
| 4 | **PyPI publisher registered late** — after the first tag → first release's publish job fails | Register the *pending* publisher before the first release |
| 5 | Merge policy left as merge-commit/rebase → release-please misses or mis-bumps releases | Squash-only, squash message = **PR title**; this is the only config release-please reads correctly |
| 6 | **Docker Hub** with only one of the two secrets set → preflight **fails the entire release** (PyPI included), by design | Set both `DOCKERHUB_USERNAME` + `DOCKERHUB_TOKEN`, or neither |
| 7 | **Settings App** silently escalates anyone with push access to **admin** on merge to default branch | Keep CODEOWNERS (`* @<user>` ships) + enable branch protection **"Require review from Code Owners"**; narrow CODEOWNERS to `/.github/settings.yml` to scope it |
| 8 | **GITLEAKS** in `check-security.yml` — free for personal accounts / public repos, but an **org** needs a `GITLEAKS_LICENSE` secret | Add `GITLEAKS_LICENSE` only when the repo lives under an org (noted inline in the workflow) |
| 9 | Renovate **copier manager** relies on the template publishing **tags**; a copier-update PR can carry unresolved conflict markers Renovate won't flag ([renovate#31600](https://github.com/renovatebot/renovate/issues/31600)) | Nothing to configure — but review copier PRs for `<<<<<<<` / `.rej` before merging |
| 10 | Branch protection needs a **public repo or GitHub Pro** for private repos | On free-plan private repos, skip protection (or upgrade); the other steps still apply |

## Common mistakes

- **Assuming a green CI means setup is done.** All of this is invisible to CI — it
  only fails at merge/release time, off to the side. Verify externally.
- **Transcribing commands from memory instead of the shipped
  `docs/maintaining/setup.rst`.** The exact `gh` commands (with owner/repo already
  interpolated) and the precise set of optional steps ship in the project on the
  template version it's actually on — read them rather than reconstructing, or
  you'll drift.
- **Running optional steps the project didn't enable.** Gate every optional secret/
  App on `.copier-answers.yml`; the setup doc already omits the ones that
  don't apply.
- **Enabling Pages (or expecting doc previews) before the first release.** The
  `gh-pages` branch doesn't exist yet.
- **Registering the PyPI publisher after the first tag.** The first release's
  publish job needs the *pending* publisher already there.
- **Copying the template repo's `default_workflow_permissions=write`.** Generated
  projects are least-privilege `read` + approve-PRs.
