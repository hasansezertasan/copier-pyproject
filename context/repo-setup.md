# Repository configuration as code and maintainer setup

## Repository metadata via the Settings GitHub App, opt-in; labels and branch protection stay out of it

**Id:** dee6eadb-b617-4d64-bbec-7c688bad0604
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-018 (`docs/adr/018-repository-settings-as-code.md`)
**Revisit when:** GitHub exposes the About-sidebar activity toggles through an API, or the Settings App gains rulesets support
**See:** external-integrations.md#a-freshly-generated-project-is-green-on-first-push-with-zero-external-accounts — 392b6dcf-6e9d-441d-bf7b-64ba362578d7 — as of 2026-10-11
**See:** repo-setup.md#branch-protection-as-code-through-an-opt-in-rulesets-sync-workflow — 3f94789f-94e8-4758-a32d-1e0d72c0140b — as of 2026-10-11

`include_repo_settings` (default off, `full` preset only) renders
`.github/settings.yml` for the Settings App: description, homepage, topics
(normalized from a free-form answer and omitted when empty so existing topics
stay untouched) and the squash-merge flags release-please needs. Labels are
excluded; branch protection and collaborators are excluded. The activity
toggles cannot be set by anything.

**Reason:** the App is an external install, so opt-in. Labels are already
managed App-free by an always-on label-sync workflow, and moving them under an
opt-in App would drop the provisioning of the `no-issue` label that the
linked-issue check needs as its bypass. Branch protection was excluded as
duplicating the documented required-checks setup — a part later superseded by
the rulesets workflow below. The activity toggles are web-UI only.

**Rejected alternative:** consolidate labels under the App — breaks the
linked-issue escape hatch for any project without the App.

**Consequence:** the App escalates push access to admin, mitigated by the
documented CODEOWNERS plus required code-owner review pattern.

## Branch protection as code through an opt-in Rulesets sync workflow

**Id:** 3f94789f-94e8-4758-a32d-1e0d72c0140b
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-021 (`docs/adr/021-repository-ruleset-as-code.md`)
**Revisit when:** the workflow token can manage rulesets, the Settings App supports them, or a project needs required human approvals
**See:** repo-setup.md#repository-metadata-via-the-settings-github-app-opt-in-labels-and-branch-protection-stay-out-of-it — dee6eadb-b617-4d64-bbec-7c688bad0604 — as of 2026-10-11

`include_repo_ruleset` (default off, `full` preset) scaffolds a canonical
ruleset JSON for the default branch — no deletion or force push, linear
history, pull requests with squash-only merges and thread resolution, zero
required approvals, no bypass actors, strict required status checks naming the
template's real contexts (the task-list gate as its check run `Task Completed
Checker`, not its job name) — and an idempotent sync workflow authenticated by a
`REPO_ADMIN_TOKEN` fine-grained PAT that warns and skips when the secret is
absent.

**Reason:** a generated repository ships exactly the checks to gate merges on
but none is enforced until an admin hand-wires protection — the per-project
drift the template designs away. The Settings App cannot manage rulesets and
the workflow token cannot be granted administration, so a PAT is required.
Zero required approvals avoids deadlocking solo maintainers on their own PRs
and unblocks release-please and Renovate while still enforcing every check.
Requiring the task-list job name would gate nothing: the job is green with
boxes unticked, so the check run it publishes is what must be required.

**Rejected alternative:** classic branch protection — a ruleset is one
declarative, export-friendly file, which weakens the earlier duplication
concern.

**Consequence:** strict status checks mean concurrent bot PRs rebase before
merging; manual web-UI ruleset edits are reverted on the next push.

## Maintainer repository setup has one actor-tagged home in the docs tree

**Id:** 4e0fcdab-d3b9-4f96-b61d-8e34927af98d
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-022 (`docs/adr/022-maintainer-setup-as-single-doc-home.md`)
**Revisit when:** the docs site is published before setup starts (making a published URL viable), or the setup guide moves
**See:** docs-stack.md#the-sphinx-subsystem-is-toggleable-include_docs-default-on-the-maintainer-guide-is-not — e983d1e7-421f-4926-9415-a3da4626f220 — as of 2026-10-11

`docs/maintaining/setup.rst` is the single home for one-time owner setup,
organized by concern with every step tagged `[AGENT]` (scriptable) or `[HUMAN]`
(browser-only), published under a maintainer-guide toctree caption.
`CONTRIBUTING.md` keeps the contributor-facing release narrative and a
one-line pointer; README, the CI skip notices and the integration config files
point at the `.rst` source path.

**Reason:** `CONTRIBUTING.md` had grown to ~590 lines, ~330 of them owner work
a contributor never performs — a category error that also buried the
contributor material. The guidance was scattered across six files pointing
back at it. Actor tags are what make a setup skill tractable. The pointer is
the repo-relative source path, not the published URL, because enabling the
docs site is itself a setup step, so the URL 404s until setup is done. RST
sections replaced a hand-maintained step counter that had to be bumped whenever
a step was added, and RST keeps the guide under the existing docs lint and
link-check gates.

**Rejected alternative:** a flat numbered list — the counter coupling above.

**Rejected alternative:** Markdown — outside the docs tooling that gates the
other pages.

**Consequence:** the setup guide renders on the public docs site; it contains
only the shape of the setup, no secrets.

## A resume-driven repo-setup skill reads `[CHECK]` blocks from the setup doc; no separate manifest

**Id:** 68ac4665-dcde-456b-aef7-2faaf6fe51f4
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-023 (`docs/adr/023-repo-setup-skill.md`); the pattern follows the `infra-setup` skill in infra-copilot
**Revisit when:** a setup step cannot carry a `[CHECK]` block, or the skill grows a parser instead of an LLM reader
**See:** repo-setup.md#maintainer-repository-setup-has-one-actor-tagged-home-in-the-docs-tree — 4e0fcdab-d3b9-4f96-b61d-8e34927af98d — as of 2026-10-11
**See:** agent-instructions.md#ai-rulez-is-the-opt-in-single-source-for-agent-instructions-with-the-prose-in-shared-macros — e1545d12-ac20-426b-9cd5-519e80a56b5f — as of 2026-10-11
**See:** template-updates.md#copieryml-defines-no-_tasks — 86130379-1660-4992-8aba-8b6cd7b4a9f7 — as of 2026-10-11
**See:** repo-setup.md — c85feefa-0063-4a34-8030-8c348190b96b — as of 2026-10-12

Every actionable step in the setup doc carries a `[CHECK]` block: a command
where exit 0 means the step is done. End-state checks assert the state a step
establishes (not a weaker proxy); secret-presence checks assert the stored
artifact by name, with conditional variants gated on repository attributes;
steps with no API-visible artifact carry an explicit no-scriptable-check
marker; steps covered by another step point at it. A skill shipped verbatim
into every generated project walks the doc top to bottom without aborting,
classifies steps as required, deferred (GitHub Pages and previews, expected red
until the first release) or optional (asks configure-or-skip), and reports
everything together.

**Reason:** the prose was executed two lossy ways — a human hand-running
commands, or an external plugin skill with its own hand-maintained verify list
duplicating the doc. Neither knew per step whether it was already done, and
setup is invisible to CI. A standalone `steps.yaml` manifest would re-encode the
commands, actor tags and Jinja gating the doc already carries and drift against
it — exactly what the single-home decision collapsed. The consumer is an LLM
reader, not a parser, so RST readability suffices. Deferred classification is
the fix for a naive walk deadlocking at Pages before reaching the rest. The
skill is a rendered file, so it never needs a post-copy task.

**Rejected alternative:** a `steps.yaml` manifest — the drift above.

**Consequence:** every future setup step must carry a `[CHECK]` block to stay
machine-drivable, as every step already had to carry an actor tag.

This repository's own setup has no repo-local skill since 2026-10-12; the
entry below records why.

## This repository's own one-time setup is two documented commands, not a repo-local skill

**Id:** c85feefa-0063-4a34-8030-8c348190b96b
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Revisit when:** this repository's own setup grows beyond a couple of settings, or has to be re-applied repeatedly (forks, re-created repo, recurring drift)

The template repository's own setup — squash-only merging with the PR title as
the commit message, plus `can_approve_pull_request_reviews=true` so
release-please can open its release PR, with `default_workflow_permissions`
left at least-privilege `read` — is recorded as two `gh` commands under
"One-time repo setup" in `docs/template-architecture.md`. The repo-local
`.claude/skills/repo-setup/` that drove them (ADR-023 §3) is removed. The
shipped `repo-setup` skill keeps its role; the plugin `setup` skill was
later removed (companion-skills.md).

**Reason:** the setup runs once per repository and has already run —
release-please has been cutting releases. Afterwards the skill sat in every
session's skill list next to two similarly named setup skills for generated
projects, and it duplicated the two commands the architecture doc already
carries.

**Rejected alternative:** keep it as an idempotent verifier for when the
release PR stops opening, or for a fork — re-running the two documented
commands (with the fork's `OWNER/REPO` substituted) covers that by hand.
