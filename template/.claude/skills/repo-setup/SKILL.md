---
name: repo-setup
description: Use to perform (or resume, or verify) the one-time repository & release-automation setup this copier-pyproject-generated project needs before its automation works — squash-merge policy, workflow permissions, branch protection / ruleset, PyPI trusted publishing, GitHub Pages, Discussions, and the optional secrets/App installs. Reach for it on "set up this repo", "finish setup", "wire up releases", "why hasn't the release PR opened", or when a fresh clone needs its GitHub settings applied. The setup is invisible to CI (a green build proves nothing), so re-run this anytime to see what is still missing.
---

# Set up this repository's release & maintenance automation

## What this does

This project passes CI green with none of the repository setup done — every
piece lives outside the code (branch settings, secrets, App installs, a PyPI
publisher registration), so no test or linter catches a missing step. The
failures surface later and off to the side: the release PR never opens, the
first publish fails, docs 404. This skill drives that setup to completion and is
safe to re-run: it reports what is already done and resumes at the first gap.

## The single source of truth

`docs/maintaining/setup.rst` is the manifest. Every step there carries three
tags:

- **`[AGENT]`** — a shell command you can run unattended.
- **`[HUMAN]`** — browser-only work (sign up, mint a credential, install a
  GitHub App, flip a UI-only toggle). You cannot do these; you hand them off.
- **`[CHECK]`** — a shell snippet where **exit code 0 means the step is already
  done**. Some `[HUMAN]` steps have no scriptable check and say so.

The commands there are already interpolated with this project's owner and repo
and gated to this project's Copier answers, so read and run exactly what ships —
never reconstruct commands from memory.

## Resume protocol

Read `docs/maintaining/setup.rst` top to bottom (its order is the dependency
order). For each step:

1. Run its `[CHECK]` (the shell block under `**[CHECK]**`).
2. **Exit 0** → the step is done. Say so briefly and move on.
3. **Nonzero, and the step is `[AGENT]`** → run the step's `[AGENT]` command,
   then re-run the `[CHECK]`. Green → continue. Still red → stop and report the
   command's output.
4. **Nonzero, and the step is `[HUMAN]`** (or the `[CHECK]` says "no scriptable
   check") → **stop**. Emit a handoff block: the exact browser instruction from
   the doc, verbatim, in a copy-pasteable form. Wait for the user to confirm
   they have done it, then re-run the `[CHECK]` (or, if there is none, take their
   confirmation).

Prerequisites: an authenticated `gh` CLI (`gh auth status`). If `gh` is missing
or unauthenticated, stop and ask the user to run `gh auth login` first.

## Rules

- **Two steps are deferred until after the first release** — GitHub Pages and
  the PR doc previews depend on the `gh-pages` branch, which the first release's
  `deploy-docs` job creates. Their `[CHECK]` stays red until then; note this and
  move on rather than treating it as a failure.
- **Steps under "Optional integrations" are opt-in.** A red `[CHECK]` there
  means "not configured", which is a fine state to leave. Present each as a
  choice ("configure Docker Hub publishing? it needs a token you mint") rather
  than driving it unprompted — every one needs a human-minted credential anyway.
- **Register the PyPI publisher before the first release**, and do the
  merge-policy step first — several later steps depend on it.
- **Do not transcribe commands from memory.** Run what `setup.rst` ships on the
  template version this project is on.
- Cross-check `.copier-answers.yml` to confirm which optional integrations are
  even relevant — the doc already renders only the applicable ones.

## When everything is green

Report "repository setup complete — every step's check passes" and list any
deferred (post-first-release) or intentionally-skipped optional steps so the
user knows what remains by choice.
