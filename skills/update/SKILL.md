---
name: update
description: Use to pull newer hasansezertasan/copier-pyproject template changes into an already-adopted project via `copier update` — either reviewing/reconciling a Renovate-opened copier-update PR by number, or running the update from scratch. Covers surfacing and approving NEW template questions/features with the maintainer (so a new answer can't silently enable a dependency), preservation-first reconciliation, restoring project-owned files the update resets (CHANGELOG, release-please manifest), the conflict markers Renovate won't flag, and the update-anchor convergence gate. Reach for it on "review this copier update PR", "a Renovate template PR is open", "bump to the latest template", "run copier update", or when a copier-update branch has conflict markers — obtaining maintainer decisions for new features and consequential behavior changes.
---

# Update an already-adopted copier-pyproject project

## Overview

This is the **recurring** flow: a project already carries a `.copier-answers.yml`
with a `_commit:` anchor, and you want newer template changes. It is **not** first
adoption (that is the `adopt` skill — `copier copy --overwrite` then restore from
git). `copier update` does a **3-way git merge** against the recorded answers, so it
preserves reconciliations already committed and only conflicts where the template
and your edits touched the same lines.

> **Never `copier copy --overwrite` an already-adopted project** — it discards every
> prior reconciliation and forces the full manual restore again. Update only.

Two things stay true no matter the entry mode and are the reason a human stays in
the loop:

- **New template questions default silently.** A newer template version may add a
  question; under `--defaults` it takes the default with no prompt — which can
  **enable a dependency** and break invariants (e.g. the zero-dep guarantees
  `include_cli=false` / `include_pydantic_settings=false`). Every new answer is a
  maintainer decision, not an automatic one.
- **The update resets project-owned files.** `copier update` deletes `CHANGELOG.md`
  and resets `.github/release-please-manifest.json` to `0.0.0`. These must be
  restored to real values or the next release mis-computes.

## Entry mode A — review a Renovate copier-update PR (by number)

Renovate's **copier manager** opens these automatically when the template publishes
a new tag. The PR looks routine but has a specific hazard:

1. **Establish the baseline, then check out and scan for breakage.** Inventory
   local work before checkout and preserve unrelated edits. Identify and record
   the actual pre-update commit from the PR's commit history and base; current
   `origin/main` may have advanced and is not automatically that snapshot.
   Renovate runs `copier update --defaults` and
   **does not fail its check on merge conflicts**
   ([renovate#31600](https://github.com/renovatebot/renovate/issues/31600)) — so a
   PR can look green/mergeable while carrying `<<<<<<<` markers or `.rej` files.
   ```bash
   gh pr checkout <N>
   git grep -nE '^(<<<<<<<|>>>>>>>)' ; find . -name '*.rej' -not -path './.git/*'
   ```
   If either is non-empty, the PR is **not** mergeable as-is — reconcile below.
   Also list what the update **deleted**: when the template drops a file it
   has not protected with `_exclude`, copier removes your copy even if you put
   real code in it — no marker, no `.rej`:
   ```bash
   git diff --name-only --diff-filter=D <pre-update-commit>
   ```
   Restore deleted project code from the recorded pre-update snapshot, merging
   any later user edits, or obtain a decision to relocate it rather than lose it.

2. **Diff the answers for silently-added features.** Renovate answered any new
   question with its default:
   ```bash
   git show <pre-update-commit>:.copier-answers.yml > /tmp/before-answers.yml
   diff /tmp/before-answers.yml .copier-answers.yml
   ```
   Take every added/changed key to the maintainer (see *Approving new features*).
   Defend the zero-dep invariants explicitly.

3. **Reconcile**, **restore project-owned files**, **re-run gates** (shared steps
   below), then **push back to the Renovate branch** and let the maintainer approve
   and merge — do not merge on their behalf.

## Entry mode B — run the update from scratch (no PR yet)

Run it yourself when you want the update ahead of Renovate, or Renovate isn't
installed. The important choice here is **whether to surface new questions**:

1. **Record the baseline; prefer interactive over blind `--defaults`.** Record
   the current commit and inventory local work before running Copier. Preserve
   unrelated edits so a later restoration does not overwrite them.
   The whole point of a human in the loop is to *see* new questions.
   The `mise` shim is often unresolvable (`No version
   is set for shim: copier`); `uvx` is reliable:
   ```bash
   uvx copier@latest update           # interactive: prompts for genuinely-new questions
   ```
   Use `--defaults` only when you have already reviewed the answers diff and
   accept the defaults. No `--trust` is needed (the template defines no
   `_tasks`/migrations).

2. **Approve each new question with the maintainer** as it appears (or from the
   `--pretend` answers diff first), then reconcile / restore / gate / commit.

## Approving new features (human in the loop — the spine of this skill)

Mirror the disciplined, one-at-a-time pattern the `adopt` skill uses for planted
TODOs: **do not batch-accept.** For each new or changed answer:

1. **Show it in context** — the answer key, its old vs. new value, and *what it
   pulls in* (new dependency, new files/workflows, a new CI gate).
2. **Recommend based on the project's nature.** A zero-dep library should refuse a
   toggle that adds a runtime dependency; defend `include_cli=false` /
   `include_pydantic_settings=false` unless the maintainer explicitly wants them.
3. **Apply the decision, then move to the next** — one at a time, so the diff stays
   legible and no feature is silently enabled.

## Shared reconciliation (both modes)

1. **Audit the whole update, then resolve conflicts per hunk.** Compare the
   recorded pre-update snapshot with the updated tree, including deleted files
   and cleanly merged CI/config changes; absence of conflict markers does not
   prove preservation. Preserve adopter behavior. Markers read
   `<<<<<<< before updating` (your committed version) / `=======` / `>>>>>>> after
   updating` (template). Compare the pre-update behavior, project customizations,
   and template intent; file category alone does not decide which side wins.
   This is the same preservation-first contract as the generated
   `template-adoption` skill:
   - Keep project identity, authored prose, custom hooks, dependency choices, and
     release state; graft in relevant template capabilities without replacing
     existing functionality. Replace planted TODOs with the project's content.
   - Apply behavior-preserving maintenance directly only when equivalence is
     established and it is within the requested update. A SHA-pin change is not
     automatically equivalent: check the action release and preserve customized
     inputs, permissions, triggers, and conditions.
   - For behavior-changing replacements, deletions, or workflow consolidation,
     explain what is gained and lost and obtain the maintainer's decision.
     Security improvements also need their effects explained rather than being
     accepted solely because they came from the template.
   - Before retiring a workflow or check, compare event coverage and failure
     propagation and inspect live required-status references. Two jobs running
     the same command can differ in manual dispatch or merge-gate identity.
     If live settings cannot be inspected, preserve the existing path and report
     the missing evidence; delegate approved repository-settings transitions to
     `repo-setup`.
   Preserve unrelated user edits and stage only the intended reconciliation
   files. `git grep -nE '^(<<<<<<<|>>>>>>>)'` must be empty (the two 7-char
   markers are unambiguous; `=======` is omitted because it false-matches
   Markdown/RST heading underlines).

2. **Recover reset project-owned content from the recorded pre-update snapshot,
   not the index or an assumed current base.** In **Mode A** (Renovate PR) the
   checked-out branch already has the deletion/reset *committed*, so a plain
   `git checkout -- CHANGELOG.md` restores the **deleted** state from the index (or
   fails with a pathspec error) — it cannot bring the file back. The actual
   pre-update commit preserves branch-specific release state that current
   `origin/main` may lack. Compare it with later user work and recover only
   the content Copier reset. When the file has no other changes to preserve, a
   full-file restore is appropriate:
   ```bash
   git restore --source=<pre-update-commit> -- CHANGELOG.md
   git restore --source=<pre-update-commit> -- .github/release-please-manifest.json
   ```
   Otherwise merge the recovered release history/state with the subsequent
   changes rather than overwriting them. Confirm the manifest holds the
   **actual current released version**, not `0.0.0` or a stale snapshot value.

3. **Re-run the gates the update can trip:**
   - **ruff** — the template ships `fix=true`+`unsafe-fixes`+`select=ALL`; run
     `ruff check --diff` before letting any fix touch `src/**`.
   - **taplo** — `prek.toml`/`pyproject.toml` may arrive un-taplo-formatted, failing
     the `style` env (and cascading into every matrix job). `taplo format
     prek.toml pyproject.toml`, then `tox -e style`.
   - Confirm `docs/conf.py` kept your custom `exclude_patterns` (a dropped one can
     publish internal design specs to Pages).
   - Re-verify the zero-dep invariants: `dependencies=[]`, no new transitive deps.

## Anchor gate — the proof it converged

A plain `copier update --pretend` targets the template's **current HEAD**; if HEAD
advanced since your update (it can move mid-session) it reports wanting the *newer*
commit — which is **not** reconciliation divergence. Test convergence against the
commit you actually reconciled to (run after committing the baseline — `--pretend`
refuses on a dirty tree):

```bash
uvx copier@latest update --vcs-ref=<your _commit> --pretend --defaults
```

Must print **`Keeping template version …<your _commit>`** (nothing to re-apply). If
it wants to re-apply changes, your reconciliation diverged and future updates will
conflict-storm. If a newer commit exists and you want it, just run `update` again —
a fresh, usually-tiny merge, committed separately.

## Gotchas

| # | Gotcha | Fix |
|---|--------|-----|
| 1 | Renovate copier PR looks mergeable but carries `<<<<<<<` / `.rej` (renovate#31600) | Scan on checkout; reconcile before merging |
| 2 | New template question silently takes its default under `--defaults` → enables a dependency | Diff `.copier-answers.yml`; approve each new answer with the maintainer; defend zero-dep invariants |
| 3 | `copier update` deletes `CHANGELOG.md` and resets the release-please manifest to `0.0.0` | Recover from the recorded **pre-update commit**, preserving later edits — the index may already contain the reset and current `origin/main` may not contain branch-owned history; verify the real released version |
| 4 | ruff `fix=true`+`unsafe-fixes`+`select=ALL` rewrites `src/**` on first contact | `ruff check --diff` / `per-file-ignores` before any fix |
| 5 | `prek.toml`/`pyproject.toml` arrive un-taplo-formatted → `style` env fails, cascading into every matrix job | `taplo format prek.toml pyproject.toml`; re-run `tox -e style` |
| 6 | A dropped `exclude_patterns` in `docs/conf.py` publishes internal specs to Pages | Re-add custom `exclude_patterns`; diff `docs/conf.py` |
| 7 | Plain `--pretend` reports "diverged" only because template HEAD moved | Pin with `--vcs-ref=<your _commit>` |
| 8 | `Verify linked issue` CI check fails a chore/update PR with no issue | Apply the `no-issue` label |
| 9 | Template dropped a file you had edited → copier deletes it silently (no conflict) | Audit deletions against the recorded pre-update snapshot in both modes; recover custom code without overwriting later edits |
| 10 | `mise` shim can't resolve copier (`No version is set for shim: copier`) | Use `uvx copier@latest update` |

## Common mistakes

- **`copier copy --overwrite` on an already-adopted project.** Use `update` —
  overwrite throws away every committed reconciliation.
- **Merging a Renovate copier PR without scanning for conflict markers.** Renovate
  won't fail on them; a green check is not proof it merged cleanly.
- **Blindly accepting `--defaults` on a version that added questions.** A new answer
  can enable a dependency and break invariants — surface and approve each.
- **Leaving the manifest at `0.0.0` / letting `CHANGELOG.md` stay deleted.** The next
  release mis-computes the version or loses history.
- **Trusting a plain `--pretend` after template HEAD moved.** Pin the anchor with
  `--vcs-ref=<your _commit>`.
- **Taking template-side CI/config hunks by category.** Preserve custom behavior;
  prove equivalence or obtain a decision before replacing it. A successful lint
  run does not prove event coverage or required-check continuity.
- **Merging on the maintainer's behalf.** Push the reconciliation; let them approve.
