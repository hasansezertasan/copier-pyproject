# Template adoption and update audits

Generated projects include `template-adoption` beside `repo-setup`, without a
new toggle. The skill reconciles initial adoption, updates to a newer template
version, and audits after an update has already happened. It treats template
defaults as evidence to compare with project behavior, rather than instructions
to discard customizations. Repository settings remain the job of `repo-setup`.

## Invocation and delivery

Open an agent session in the adopting project and ask:

> Audit this template adoption against our existing behavior. Compare overlapping
> workflows and preserve our custom tooling; ask before consequential changes.

For an update, specify the previous and target versions if known; for a
post-update audit, point to the update commit or PR. The agent inspects history
and records unavailable evidence rather than guessing the baseline.

Use the request above to select the skill. With `include_ai_rulez=true`, run
`ai-rulez generate` to deliver it to selected hosts. Otherwise it ships at
`.claude/skills/template-adoption/SKILL.md`. The ai-rulez source is
`.ai-rulez/skills/template-adoption/SKILL.md`. An agent without automatic skill
discovery can read the file directly. Both paths contain the same procedure and
a self-contained walkthrough, even with `include_docs=false`.

## Example adoption walkthrough

This illustrative case follows the overlapping prek workflows raised during
openapipages' adoption; the event and check names below are examples, not a
claim about that repository's current settings.

1. **Baseline:** record the pre-adoption project commit, target template version,
   Copier answers, release notes, and the adoption diff. Inventory local work
   before editing. For a merged update, use the actual pre-update commit and
   committed diff; do not run Copier again just to recreate the comparison.
2. **Evidence:** the existing `check-prek.yml` runs `prek run --all-files` on PRs
   and manual dispatch; the generated CI hooks job runs it on PRs and pushes.
   Compare their filters, permissions, runners, secrets, job conditions,
   dependencies, and failure propagation too. The old check name is required
   by live branch protection, so deleting the file would block merges. A local
   ruleset alone is insufficient evidence of the live requirements.
3. **Decision:** recommend retaining the old workflow until manual dispatch and
   the required-check transition are accounted for. Show two options: keep both
   (duplicate PR execution, existing manual path and protection preserved), or
   consolidate (retain manual dispatch, verify the replacement gate, and hand
   the settings transition to `repo-setup`). Obtain the adopter's explicit
   choice before changing triggers or removing a workflow. If settings cannot
   be read, defer deletion and list the evidence needed to resume.
4. **Reconciliation:** after approval and verification of the required-check
   transition, consolidate only the agreed behavior. Preserve custom prek hooks,
   project source/tests, dependencies, release state, and any starting user edits.
   Update references to the retired workflow. A stale docs command can be
   mechanically corrected when the replacement is already established and
   equivalence is proven.
5. **Validation:** use the project's workflow validators and relevant lint/test
   commands, inspect trigger paths and aggregate gates, and review the final
   diff. YAML parsing alone does not prove event coverage or mergeability.
6. **Report:** list the baseline/version range, the decision and changes,
   customizations retained, checks passed/failed/skipped, and remaining tasks.
   No issue filing, commit, push, or PR is needed to complete this audit.

The same procedure checks conflicts and reject files, stale configs and docs,
dependency groups/extras, test coverage, supported platforms, packaging, and
release behavior. Unavailable evidence is an explicit unresolved item, not a
reason to assume the template's behavior is correct for the project.

## Lost-check coverage audit

Before retiring a hook configuration, inventory each old hook and quality/security
job. The generated skill reports retained, replaced, missing, intentionally
omitted, or optional checks, with evidence and user decisions. Compare rule sets,
Python targets, stages, file/type filters, exclusions, execution environments,
dependencies, suppressions, and feedback timing—not just tool names.
Verify pinned hook IDs and positive/negative file matches. Ask before accepting
reduced coverage or later feedback, and preserve project-specific checks unless
the adopter chooses otherwise.

The [generated-project check audit](hook-coverage.md) records the default
decisions and known non-equivalences for this template. A passing CI run does not
prove an old check was replaced, or that an independent security job is required
by branch protection.
