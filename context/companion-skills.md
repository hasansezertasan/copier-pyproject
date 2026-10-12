# Companion skills

## Every lifecycle skill ships through the template

**Id:** e4cd1c46-28c3-4241-82c8-d5aac41c293f
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** maintainer decision, 2026-10-12
**Revisit when:** adoption requires executable guidance before a recoverable scaffold can be applied
**See:** companion-skills.md — d3127820-eee0-4618-bb95-4acf09cb4d68 — as of 2026-10-12

First-adoption hazards now live in the shipped `template-adoption` skill,
alongside the update audit. Repository setup stays in `repo-setup` and its
single-source guide. The root `skills/` and `.claude-plugin/` delivery surfaces
are removed. The README supplies the pre-scaffold prompt; Copier's completion
message points at the rendered skill before tools or commits run.

**Reason:** first adoption has two parts: creating a recoverable scaffold and
reconciling it. A prompt can establish a clean branch, committed baseline,
explicit answers and a target version before copying. The rendered skill is
then present for reconciliation, matched to the chosen template version and
parameterized with the adopter's package name and enabled components. This
removes the external installation prerequisite and duplicate prose.

**Rejected alternative:** retain `adopt` outside the template because adoption
starts before the skill exists — the pre-scaffold prompt covers that boundary,
while the hazards matter after files have been copied and before tools run.

**Rejected alternative:** move lifecycle skills into a separate repository —
template changes and skill updates would need separate releases and reviews.

**Consequence:** existing plugin installations must be removed in favor of the
project's shipped skills. Projects predating `template-adoption` receive it on
their next update; until then, the README and adoption walkthrough provide the
entry point. No Copier task or `--trust` requirement is introduced.

## Superseded proposal: keep adoption outside the template

**Id:** d3127820-eee0-4618-bb95-4acf09cb4d68
**Type:** decision
**Status:** superseded
**Evidence:** inferred
**Source:** maintainer decision, 2026-10-12; the stub rejection is inferred, not yet confirmed
**Revisit when:** a skill is needed before or outside an adopted project for something other than first adoption, or projects older than v1.6.0 (no `template-adoption`) still need help with their first update
**Superseded by:** e4cd1c46-28c3-4241-82c8-d5aac41c293f
**See:** repo-setup.md — c85feefa-0063-4a34-8030-8c348190b96b — as of 2026-10-12

This proposal was replaced before the changes were committed. It would have
kept only `adopt` in the repository-root `skills/` folder for installation via
the `copier-pyproject` plugin or the `skills` CLI, removing `update` and `setup`. Their unique content moved into the template: the
copier-update hazards into the shipped `template-adoption` skill, and the
private-repository branch-protection plan limit into the generated
`docs/maintaining/setup.rst`, which the shipped `repo-setup` skill walks.
Under this proposal, `adopt` would have stayed outside `template/` in this
repository. Removing `setup` would supersede ADR-023 §4.

**Reason:** a skill describes the template's internals, so where it lives
decides whether it stays matched to them. A skill shipped through `template/`
arrives with `copier update` and always matches the template version the
project is on, for every agent host. The plugin installs from `main`
regardless of that version, and only Claude Code had an install path until
the `skills` CLI was found to read the same folder. The proposal assumed `adopt` had to run before the template was present and
therefore required external delivery. The successor decision separates the
pre-scaffold prompt from the reconciliation skill, removing that assumption.
The plugin `update` and `setup` skills were near-copies of the shipped ones,
and the two sets were already drifting.

**Rejected alternative:** a separate repository for the skills — a template
change that makes a skill wrong could no longer be fixed in the same PR or
caught by this repository's review and render harness, and it would add a
second release line, for a gain of only a tidier repository root.

**Rejected alternative:** ship every skill through the template, including
`adopt` — `adopt` is needed before the template has been applied, so it would
never be present when it is needed.

**Rejected alternative:** keep the plugin `update` and `setup` skills as stubs
pointing at the shipped ones, for projects generated before those existed —
`repo-setup` shipped in v1.2.0 and `template-adoption` in v1.6.0, and a
project that old receives both with its next update. This rejection is
inferred; the maintainer has not ruled on it.

**Consequence:** a project older than v1.6.0 has no update skill for the one
update that brings `template-adoption` in.
