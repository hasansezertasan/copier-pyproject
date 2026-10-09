# ADR-037: Re-evaluating Release Automation — Changelog Engines vs Release Orchestrators

## Status

**Proposed — under discussion. No decision has been made.**

Last refreshed 2026-10-05 against template 1.5.3 (`release.yml`,
`release-please-action` v5.0.0) and the upstream issue states cited below.

This ADR is a *research record*. It captures a deliberate re-evaluation of the
release-automation tooling chosen in
[ADR-002](002-release-please-for-release-automation.md) and refined in
[ADR-004](004-commitizen-as-commit-helper-not-release-tool.md), the two-pass
web research behind it, a conceptual framing of the tool landscape, and a
head-to-head comparison of the two most credible replacements (Commitizen and
git-cliff). It intentionally stops short of a decision so the options can be
discussed on the record. If a direction is chosen later, this ADR is updated to
**Accepted** with the selected option, and it then refines or supersedes ADR-002
and ADR-004 as noted under "Consequences".

## Context

### What we run today

The template standardized on **release-please** (ADR-002) and reduced
**Commitizen** to a commit-authoring/linting helper only (ADR-004). In the
generated `template/.github/workflows/release.yml.jinja`, release-please is not
merely "the release tool" — it performs **five distinct responsibilities**, and
up to fourteen downstream jobs (some render only with their toggle) are bolted
directly to its outputs:

1. Parses Conventional Commits and **computes the next version**.
2. Opens and maintains the **reviewable Release PR** (accumulate-then-merge).
3. On merge, **creates the git tag** (`force-tag-creation: true`) and a **draft
   GitHub Release** with generated notes.
4. **Writes `CHANGELOG.md`** using the project's `changelog-sections` emoji
   taxonomy.
5. Emits `release_created` / `tag_name` / `version` **outputs** that gate
   `build`, `pypi-publish`, `sbom`, `docker-publish(-preflight)`,
   `build-launcher`/`build-freezer`/`build-compiler`, `attach-github-release`,
   `finalize-release`, `bump-homebrew`/`bump-scoop`, `deploy-docs`, and
   `notify-released-issues`.

Two consequences of release-please's model are load-bearing complexity in the
workflow today: the **draft → attach SBOM/artifacts/Sigstore provenance
([#318](https://github.com/hasansezertasan/copier-pyproject/pull/318)) →
un-draft** sequence (because release-please creates the GitHub Release
atomically at PR-merge time, before the build artifacts exist), and the **phantom-PR reconciliation** in
`finalize-release` (because release-please derives its commit range from the
latest *published* release and ignores drafts). Versioning is git-tag-sourced
via hatch-vcs (`dynamic = ["version"]`), so release-please never edits a static
version literal and `uv.lock` cannot desync.

A third constraint landed after this research began and is **not specific to
release-please**: a merge that changes `.github/workflows/` after the release PR
merges but before the Release run finishes can make GitHub's release API refuse
tag/release creation with a 403, because `GITHUB_TOKEN` cannot be granted
workflow write access
([#332](https://github.com/hasansezertasan/copier-pyproject/issues/332)). ADR-002
now documents the merge pause and recovery
([#339](https://github.com/hasansezertasan/copier-pyproject/pull/339)). Any
candidate that creates the tag or release from a workflow with `GITHUB_TOKEN`
inherits this; only a model where a maintainer pushes the tag from their own
clone would plausibly sidestep it (not verified).

### Why we are re-opening the decision

Three friction points motivated this review:

1. **Release-candidate to stable changelog range.** After cutting several
   prereleases (`v1.2.0-rc.1`, `v1.2.0-rc.2`) and then a final stable `v1.2.0`,
   the stable release's notes contain only the changes **since the last RC**,
   not all changes **since the last stable** (`v1.1.0`). The observed cause is
   that release-please computes the commit range from the last release marker
   with no prerelease/stable distinction.
2. **Stale draft-release comment link.** release-please posts its
   `🤖 Created releases:` comment on the merged Release PR once, at
   draft-creation time, capturing the transient `/releases/tag/untagged-<hash>`
   slug. When `finalize-release` un-drafts the release, GitHub moves it to
   `/releases/tag/vX.Y.Z` and the `untagged-…` link 404s. This is tracked and
   **accepted** as a cosmetic limitation in
   [#143](https://github.com/hasansezertasan/copier-pyproject/issues/143)
   (closed) and documented by
   [#152](https://github.com/hasansezertasan/copier-pyproject/pull/152)
   (merged), which added the inline comment at the `finalize-release` "Publish
   the draft release" step and the corresponding ADR-002 Consequences bullet.
3. **General "unconventional usage" friction** of the release-PR model — the
   draft dance and phantom-PR reconciliation are workarounds layered on top of
   release-please's opinions rather than features of it.

The prior art in ADR-002 compared release-please against release-it and
release-drafter; ADR-004 compared it against a Commitizen `cz bump` pipeline.
This ADR widens the field to the current (2025–2026) landscape and re-frames the
question around a distinction ADR-002/004 never drew explicitly: the difference
between a **changelog engine**, a **release orchestrator**, and a **commit
helper**.

## A conceptual frame: three roles in release automation

The candidate tools are frequently compared as if interchangeable, but they
occupy three different layers. Naming the layers is the point of this section —
it is the frame for the discussion this ADR is meant to open.

| Role | Responsibility | Examples |
| --- | --- | --- |
| Commit helper | Author and lint Conventional Commit messages | Commitizen `cz commit`, commit hooks |
| Changelog engine | Turn a commit range into release notes / `CHANGELOG.md` | git-cliff, the changelog half of any tool |
| Release orchestrator | Decide *when* to release, compute the version, tag, create the GitHub Release, gate downstream jobs | release-please, semantic-release, `cz bump`, cocogitto, knope |

The critical insight for this decision: **release-please is a release
orchestrator, git-cliff is a changelog engine, and Commitizen can act as
either a commit helper (its role today, per ADR-004) or a release
orchestrator (`cz bump`).** A changelog engine cannot replace an orchestrator
on its own — it fills exactly one of the five responsibilities above. That
single fact dominates the effort comparison later.

A second, non-obvious insight: **both named pain points are artifacts of
release-please's specific orchestration model** ("maintain a Release PR; create
the GitHub Release atomically at merge; range from the last *published*
release"). A tool that instead lets *the pipeline* sequence
tag → build → release can create a non-draft release with artifacts already
attached (eliminating pain point 2's draft dance) and can be pointed at the last
*stable* tag for changelog range (addressing pain point 1) — provided the tool
supports it. Whether each candidate actually supports it is the empirical
question the research answered.

## Research method

Two background "deep-research" passes were run (fan-out web search →
source fetch → per-claim adversarial verification with a 3-vote majority →
synthesis). Both preferred **primary sources**: tool source code, config
schemas, official docs, and specific GitHub issues/PRs.

- **Pass 1 (landscape).** 6 angles, 23 sources fetched, 96 claims extracted, 25
  verified → 23 confirmed, 2 refuted. Established the candidate set and each
  tool's fit against the hatch-vcs / uv / GitHub Actions / Trusted-Publishing /
  no-Node constraints.
- **Pass 2 (decisive questions).** 6 angles, 21 sources fetched, 75 claims
  extracted, 25 verified → 23 confirmed, 0 refuted, 2 unverified. Narrowed to
  the two questions that actually decide the outcome: (1) is release-please's
  RC→stable changelog range a bug or configurable, and (2) do the leading
  alternatives accumulate changelog from the last *stable* across RCs.

**Verification caveat, recorded honestly.** Pass 2's final *synthesis* step
failed on a session-usage limit, but all 23 claims were already
adversarially verified before it did (0 refutations in pass 2), and the
load-bearing claims were re-checked by hand against the per-agent transcripts:
the Commitizen `changelog_merge_prerelease` fix, the Python Semantic Release
source-code trace, and the npm-team manual-workaround quote each appear in
multiple independent verifier transcripts quoting primary sources. cocogitto's
RC-range behavior did **not** survive into the verified top-25. The raw
extraction leaned toward "cocogitto shares the bug" on the strength of
cocogitto issue #362, but on re-check that issue concerns *version computation* from a
prerelease tag (not the changelog range) and was closed as completed on
2025-10-21, so it is no evidence either way.

## Findings: the candidate landscape

Fit of each researched tool against the template's fixed constraints
(hatch-vcs git-tag versioning with no static literal edits; uv/tox/prek;
GitHub Actions + PyPI Trusted Publishing; no Node runtime; squash-by-PR-title
Conventional Commits).

| Tool | Layer | Runtime | hatch-vcs fit | GitHub Release | Fixes RC changelog | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| release-please (incumbent) | Orchestrator | Pure GHA | Yes (git-tag sourced) | Yes (draft) | No | Baseline |
| Commitizen (`cz bump`) | Helper → Orchestrator | Python (installed) | Yes (`scm` provider; no version literal) | No (add `gh release`) | **Yes** (`changelog_merge_prerelease`) | Strongest replacement |
| Python Semantic Release | Orchestrator | Python (Docker action, no Node) | Yes if `importlib` + no `version_toml` | Immediate | No (shares the bug) | Python-native but no gain |
| cocogitto (`cog bump`) | Orchestrator | Rust (libgit2) | Yes (tag-based) | Via extra step | Unverified | Node-free, unproven on RC |
| knope | Orchestrator | Rust | Yes (tag-derived with empty `versioned_files`) | Yes (`Release` step) | No (starts from latest tag) | Rust orchestrator; supports CC and PR bot, but shares RC truncation |
| git-cliff | Changelog engine | Rust | Yes (tag-sourced) | No (pair with `gh release`) | **Range yes** (`ignore_tags`); no prerelease version calc (#1380) | Not an orchestrator |
| semantic-release (JS) | Orchestrator | Node | — | Immediate | No | Excluded by the no-Node constraint (as release-it was in ADR-002) |
| changesets | Orchestrator | Node | — | — | — | JS-ecosystem; extra changeset files |
| hatch-regex-commit | (version source) | Hatch plugin | **No** (static regex source, mutually exclusive with hatch-vcs) | No | No | Disqualified |

### Pain point 1: RC to stable changelog range

**Verdict: a genuine release-please limitation with no built-in config remedy.
Commitizen fixes it with one setting; git-cliff can produce the right range with
configuration but leaves prerelease *version* calculation to the orchestrator.**

Evidence for release-please (all primary):

- It finds "the last merged release PR and use[s] the associated commit sha as
  the previous marker from which to gather commits", with **no documented
  distinction between prerelease and stable** — so an intervening RC PR becomes
  the previous marker
  ([manifest-releaser.md](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md),
  [design.md](https://github.com/googleapis/release-please/blob/main/docs/design.md)).
- The `versioning` option (`default` / `always-bump-patch` / `always-bump-minor`)
  controls only the bump *size*, and `prerelease` / `prerelease-type` control
  only the prerelease label/number — **none re-anchor the changelog range to the
  last stable tag**
  ([customizing.md](https://github.com/googleapis/release-please/blob/main/docs/customizing.md)).
- Mishandling a prerelease as "latest" is maintainer-labeled `type: bug`
  ([#2267](https://github.com/googleapis/release-please/issues/2267)); clean
  prerelease→stable conversion is an **open, unresolved** feature request
  ([#2515](https://github.com/googleapis/release-please/issues/2515), open since
  Mar 2025) and there is no answer to "ignore `-rc` tags"
  ([#2605](https://github.com/googleapis/release-please/issues/2605)).
- Independent confirmation that this bites real projects: the **npm CLI team**
  works around the identical behavior by hand — "release-please only generates
  changelogs based on the diff from the previous prerelease. So when coming out
  of prerelease mode, we combine all the prerelease changelogs and manually
  update the notes of the GitHub Release after it has been created"
  ([npm/cli wiki](https://github.com/npm/cli/wiki/Release-Process)).

Per-alternative behavior:

- **Commitizen — fixes it.** `--merge-prerelease` / config
  `changelog_merge_prerelease` "Collects changes from prereleases into the next
  non-prerelease version"
  ([changelog docs](https://commitizen-tools.github.io/commitizen/commands/changelog/)).
  A bug where it was ignored during `cz bump --changelog`
  ([#1694](https://github.com/commitizen-tools/commitizen/issues/1694)) was
  **fixed in v4.11.3, 2026-01-13** ("fix the issue that
  `changelog_merge_prerelease` not working on `cz bump`",
  [CHANGELOG](https://github.com/commitizen-tools/commitizen/blob/master/CHANGELOG.md)).
  Reliability on the bump path is therefore recent — a real caveat.
- **Python Semantic Release — shares the bug.** Verified against PSR's source:
  it builds its tag lookup from **all** tags (RCs included), walks commits from
  HEAD until the first matching tag, and sets the released version's changelog
  `elements` to exactly that `unreleased` set — i.e. only commits since the last
  RC
  ([release_history.html](https://python-semantic-release.readthedocs.io/en/latest/_modules/semantic_release/changelog/release_history.html)).
- **cocogitto — unverified.** Did not reach the verified top-25; the issue
  first read as evidence
  ([#362](https://github.com/cocogitto/cocogitto/issues/362), closed) is about
  bump computation from prerelease tags, not the changelog range.
- **knope — shares the truncation behavior without changesets.** `PrepareRelease`
  natively parses Conventional Commits and supports tag-derived versioning
  without versioned files (fitting hatch-vcs), while Knope Bot provides release
  PRs. However, `PrepareRelease` documents the most recent SemVer tag as its
  unconditional starting point for commit gathering, with no mechanism analogous
  to `changelog_merge_prerelease` or `ignore_tags` to fold RC commits into a
  stable release — so an intervening RC tag truncates stable notes just like
  release-please unless maintainers manually author separate change files.
- **git-cliff — can produce the range, but does not version prereleases.**
  `ignore_tags` (or `--ignore-tags`) folds the matched tags' commits into the
  next tag, so ignoring `-rc` tags when cutting a stable yields notes from the
  last stable; an explicit commit range (`git cliff v1.1.0..v1.2.0`) does the
  same ([git config docs](https://git-cliff.org/docs/configuration/git)). What
  it lacks is prerelease *version calculation* for `--bumped-version`
  ([#1380](https://github.com/orhun/git-cliff/issues/1380), open; milestoned
  2.15.0), so the orchestrator must compute RC numbers and choose the tag
  filter per release (ignore RCs for a stable cut, not for an RC cut).

### Pain point 2: stale draft-release comment link

**Verdict: incidental to release-please's draft flow; a tag-push model
sidesteps it, but no researched tool "fixes the comment" because no other tool
posts that comment.**

The `untagged-<hash>` link exists only because release-please creates the
GitHub Release as a draft at merge time and comments once with the then-current
(draft) URL (see #143 / #152). Any pipeline that instead creates the git tag
first, builds artifacts, and then creates a **non-draft** GitHub Release with
assets already attached never has an `untagged-<hash>` phase — so both
Commitizen and git-cliff variants remove this class of problem as a side effect,
at the cost of the maintainer owning the tag→build→release sequencing. This is
not a reason to switch on its own; it is a bonus of *any* move away from the
draft-then-publish dance, and #143's option (2) ("have `finalize-release`
rewrite the comment") remains available **without** switching tools.

## Deep comparison: git-cliff vs Commitizen as replacements

Because both pain points and the hatch-vcs constraint point at these two tools,
they are compared here in the concrete shape a migration would take. The
yardstick is the five responsibilities and the gating contract above.

### git-cliff as a replacement

git-cliff is a **changelog engine** (plus a version *calculator* via
`--bumped-version`). It does not tag, does not create a GitHub Release, does not
open a PR, and does not decide whether to release. It therefore replaces exactly
**one** of release-please's five responsibilities (the changelog, and part of
the version math); everything else becomes bespoke workflow code.

A git-cliff pipeline is necessarily a **tag-push / manual-dispatch** model:

1. A maintainer (or a small script) creates and pushes the tag — which is
   ideal for hatch-vcs, since the tag is the version source of truth.
2. A workflow on `push: tags` runs `git-cliff --latest` for the release notes
   and `git-cliff` (full) to regenerate `CHANGELOG.md`, committed back.
3. Build / SBOM / executables run, then `gh release create <tag> … dist/*`
   publishes a **non-draft** release with assets already attached.

Effort is **high**: a new `cliff.toml` must reproduce the 11-section emoji
`changelog-sections` taxonomy; the "is there anything to release" gate, tag
creation, changelog commit-back, and release creation are all hand-written; and
pain point 1 is fixable only by hand — the orchestrator must compute RC version
numbers itself (#1380) and pass `--ignore-tags` for stable cuts. The net result
would be *more* custom workflow code than today, with pain point 1 solved by
that custom code rather than by the tool. git-cliff's realistic role is as the changelog
*component inside* a hand-rolled orchestrator, not as a drop-in replacement.

### Commitizen as a replacement

`cz bump` is a **release orchestrator**: in one command it computes the version
from commits, creates the git tag, and writes `CHANGELOG.md`. With
`version_provider = "scm"` it **never edits a version literal** (the version
lives only in the tag), matching hatch-vcs exactly — though with
`update_changelog_on_bump` it still writes `CHANGELOG.md` and makes a bump
commit. It does not open a Release PR and does not create a GitHub
Release, so a `gh release` step is added.

`cz bump` also signals "nothing to release", but it does so by raising
`NoneIncrementExit` with exit status 21 rather than a silent exit 0 (see
[Commitizen exit codes](https://commitizen-tools.github.io/commitizen/exit_codes/)).
In CI, the replacement workflow cannot treat status 21 as a failure, nor can it
simply swallow it: it must explicitly catch status 21 as a clean no-op and
synthesize a boolean job output (mirroring release-please's `release_created`) to
gate the fourteen downstream jobs (build, PyPI, Docker, Sigstore, etc.). Without
that custom status trap and output bridge, a no-bump push either fails CI on
exit 21 or runs the downstream release jobs after a blindly ignored error.

The `[tool.commitizen]` block grows from today's single `name` line back to a
release configuration (reversing ADR-004's deliberate reduction):

```toml
[tool.commitizen]
name = "cz_conventional_commits"
version_provider = "scm"           # no version literal; hatch-vcs compatible
tag_format = "v$version"
version_scheme = "semver2"         # v1.2.0-rc.0, not PEP 440 v1.2.0rc0
update_changelog_on_bump = true
changelog_merge_prerelease = true  # fixes pain point 1 (cz >= 4.11.3; template pins 4.17.0)
major_version_zero = true          # mirrors bump-minor-pre-major; 0.x only
```

`major_version_zero` is **not** a drop-in for release-please's
`bump-minor-pre-major`: release-please's option silently stops applying after
1.0, whereas Commitizen
[documents](https://commitizen-tools.github.io/commitizen/commands/bump/#--major-version-zero)
that `cz bump` fails on a 1.x+ version while it is set. The template would have
to render it only for pre-1.0 projects (or the migration would have to remove
it before the first 1.0 bump).

`version_scheme = "semver2"` matters: Commitizen defaults to `pep440`, which
tags prereleases as `v1.2.0rc0`, but the `docker-publish` job parses the tag
with docker/metadata-action's `type=semver`, which requires a valid SemVer
string. release-please emits SemVer prerelease tags today, so the sketch keeps
them.

The sketch is **not** changelog-complete as shown. `cz_conventional_commits`'
built-in parser (4.17.0) only extracts `feat`, `fix`, `refactor`, `perf`, and
breaking changes into changelog context, while the template's
`release-please-config.json` publishes emoji sections for `docs`, `test`,
`build`, `ci`, and `deps` too. Because a changelog template can only format
commits that the parser retained, a custom Jinja template cannot restore categories
filtered out by the built-in parser. Keeping the template's taxonomy requires
switching from `name = "cz_conventional_commits"` to `name = "cz_customize"` with
a full `[tool.commitizen.customize]` table (defining `schema_pattern`,
`bump_pattern`, `bump_map`, `commit_parser`, `changelog_pattern`, `change_type_map`,
and `change_type_order` — without `commit_parser`, changelog generation exits with
`NoPatternMapError`) or authoring a custom Commitizen plugin. Moreover, because
`cz_customize` does not inherit the built-in authoring prompts, retaining
interactive `cz commit` support requires recreating `questions` and
`message_template` in the config or maintaining a dedicated plugin. This adds
significant custom configuration or plugin maintenance that narrows the effort
gap with git-cliff.

Effort is **medium** and lower than git-cliff: no bespoke version math, the tool
is already installed, and the version calculation relies on Commitizen rather
than custom git log parsing; however, the workflow still needs custom shell
handling to trap exit 21 (`NoneIncrementExit`) into a `release_created` output
for the fourteen downstream jobs, and the changelog needs the `cz_customize`
parser table above (in `pyproject.toml` rather than a separate `cliff.toml`).
The real costs are architectural, not lines of code: it **reverses ADR-004**
(Commitizen becomes a release tool again — the tag/changelog conflict that
ADR-004 avoided is moot once release-please is gone, but the narrative must be
rewritten), and it **loses the reviewable Release PR** that ADR-002 valued.

### Effort and fit, side by side

| Dimension | git-cliff | Commitizen | release-please (today) |
| --- | --- | --- | --- |
| Replaces version calc | Partial (`--bumped-version`) | Yes (native) | Yes |
| Creates git tag | No (scripted) | Yes (`cz bump`) | Yes |
| Writes CHANGELOG | Yes (new `cliff.toml`) | Yes (needs `cz_customize` or plugin for docs/test/build/ci/deps) | Yes |
| "Should release?" gate | No (fully bespoke) | Partial (exits 21; needs custom trap + output bridge for 14 jobs) | Yes (`release_created`) |
| Creates GitHub Release | No (`gh release`) | No (`gh release`) | Yes (draft) |
| Reviewable Release PR | Lost | Lost | Yes (its model) |
| Fixes pain point 1 (RC) | With custom code (`ignore_tags` + own RC math) | Yes (one setting) | No |
| Fixes pain point 2 (link) | Incidental | Incidental | No (accepted) |
| Already in the stack | No | Yes | Yes |
| Net effort | High | Medium | Baseline |
| Reverses an ADR | No | Yes (ADR-004) | — |

**What both alternatives cost regardless:** the reviewable Release PR
disappears (release-please's signature feature per ADR-002), replaced by a
tag-push / dispatch trigger. **What both alternatives remove:** the
draft → un-draft dance *and* the phantom-PR reconciliation, so the workflow gets
simpler in those two places.

**What both alternatives must newly solve — credentials and triggers.** release-please
lands its changelog through a PR and creates the tag from the merge, so it needs only
`GITHUB_TOKEN`. A CI-driven replacement instead faces credential constraints depending
on the architecture:

- **Bypassing branch protection:** pushing a bump/changelog commit straight to `main`
  is rejected by protected branch rulesets (such as the `full` preset, ADR-021) unless
  the pushing identity is granted a bypass — requiring a PAT or GitHub App token with
  standing bypass permissions, which ADR-002 deliberately avoided;
- **Workflow trigger model:** if the design splits release steps across workflows
  (e.g. git-cliff's canonical `push: tags` workflow), a tag pushed using `GITHUB_TOKEN`
  does not trigger subsequent workflow runs due to GitHub's loop prevention, requiring
  a PAT or App token. Conversely, if Commitizen preserves the template's single-workflow
  fan-out where downstream jobs run in the same workflow and check out the new tag ref,
  no secondary workflow trigger is needed; and
- **Changelog ordering (git-cliff):** a changelog committed *after* the tag leaves the
  tagged commit without its own changelog entry.

Thus, a standing privileged credential (PAT or GitHub App token) is required if branch
protection must be bypassed or if the design relies on a separate tag-triggered workflow.
Running the bump locally is **not** a clean escape hatch under the `full` preset either:
its ruleset has `bypass_actors: []`, requires a PR, and allows only squash merges, so a
maintainer cannot push the bump commit to `main` directly, and squash-merging it through
a PR rewrites its SHA, leaving the locally created tag off `main`. A local flow would need a
two-step "changelog PR, then tag the merged SHA" sequence (e.g. calculating the next tag
and generating the changelog via `cz changelog --unreleased-version="<tag>"` in a PR,
then tagging the merged commit on `main`) or a ruleset bypass.

## Options under consideration

No option is selected. They are recorded for discussion.

1. **Stay on release-please; document and optionally work around.** Treat the
   RC→stable range as a rare edge case with a known manual remedy (concatenate
   prerelease sections, as the npm team does), mirroring how pain point 2 is
   already handled (#143 / #152). Optionally implement #143's option (2) to
   rewrite the stale comment. Lowest risk; keeps the Release PR; changes nothing
   structural. Refines ADR-002 with a documented limitation.
2. **Migrate to Commitizen (`cz bump`, `scm` provider).** Genuinely fixes pain
   point 1, stays Python-native, reuses an installed tool, and removes the draft
   dance and phantom-PR reconciliation. Costs: rebuild GitHub Release creation +
   SBOM/artifact attach around `gh release`, lose the Release PR, and reverse
   ADR-004. Medium effort on the most safety-critical workflow the template
   ships. Would supersede ADR-002's tool choice and reverse ADR-004.
3. **Adopt git-cliff inside a hand-rolled orchestrator.** Highest effort; fixes
   pain point 1 only through that orchestrator's own RC versioning and
   per-release `--ignore-tags` choice. Only worth considering if the changelog
   *formatting* (git-cliff's templating) becomes a first-class requirement
   independent of the release model. Not recommended on current evidence.
4. **Record research only; defer.** Keep this ADR at Proposed, change nothing,
   and revisit when git-cliff ships prerelease version calculation (#1380,
   2.15.0), or when the RC-release workflow becomes frequent enough that the manual workaround is
   painful in practice.

## Decision drivers and open questions

- **How often do we actually cut RC series?** Pain point 1 only bites when
  prereleases precede a stable. If RCs are rare, option 1 is likely sufficient.
- **How much is the reviewable Release PR worth?** It was a primary reason
  ADR-002 chose release-please. Options 2 and 3 both discard it.
- **Is reversing ADR-004 acceptable?** Option 2 re-promotes Commitizen to a
  release tool; the ADR-004 reasoning must be re-examined, not just overwritten.
- **Template blast radius.** `release.yml` fans out to every generated project;
  any change is validated only by rendering + `actionlint` until a live release
  exercises it (the ADR-002 validation limit and cobo#49 precedent).
- **Is a release credential acceptable?** Options 2 and 3 need a PAT or App
  token to push to protected `main` (and to trigger a tag workflow if split
  across workflows; see "What both alternatives must newly solve"), or a
  maintainer-local bump.
- **Unresolved by research:** cocogitto's RC-range changelog behavior; and
  whether a Commitizen migration can faithfully reproduce the tag → build →
  attach SBOM/provenance → publish ordering — an implementation spike would
  settle it.

## Consequences

- **If option 1 is chosen:** this ADR is Accepted as "no change; documented
  limitation"; ADR-002 gains a Consequences bullet for pain point 1 (parallel
  to the pain-point-2 bullet added by #152), and optionally a `finalize-release`
  comment-rewrite step lands for pain point 2. No workflow restructuring.
- **If option 2 is chosen:** this ADR supersedes ADR-002's tool selection and
  reverses ADR-004; `release.yml`, `pyproject.toml` `[tool.commitizen]`, the
  removal of `release-please-config.json` / `-manifest.json`, README, CLAUDE.md,
  and CONTRIBUTING (PyPI Trusted Publishing still targets `release.yml`) all
  change; a release credential (or a maintainer-local bump) is chosen; a live
  release must validate the new tag → build → attach → publish ordering.
- **If option 3 is chosen:** as option 2 plus a bespoke orchestrator and a
  `cliff.toml`, and RC version calculation stays hand-written until git-cliff
  ships #1380.
- **If option 4 is chosen:** status stays Proposed; nothing changes; the ADR is
  the durable record of why the alternatives were not adopted *yet*.

Until a decision is made, the pipeline is unchanged: release-please remains the
orchestrator, Commitizen remains a commit helper (ADR-004), and pain point 2
remains an accepted, documented cosmetic limitation (#143 / #152).

## Sources

Primary sources cited above, grouped by tool.

- release-please:
  [design.md](https://github.com/googleapis/release-please/blob/main/docs/design.md),
  [customizing.md](https://github.com/googleapis/release-please/blob/main/docs/customizing.md),
  [manifest-releaser.md](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md),
  [config schema](https://github.com/googleapis/release-please/blob/main/schemas/config.json),
  issues [#2267](https://github.com/googleapis/release-please/issues/2267),
  [#2447](https://github.com/googleapis/release-please/issues/2447),
  [#2515](https://github.com/googleapis/release-please/issues/2515),
  [#2605](https://github.com/googleapis/release-please/issues/2605),
  [#2769](https://github.com/googleapis/release-please/issues/2769).
- npm CLI (independent confirmation of pain point 1):
  [Release-Process wiki](https://github.com/npm/cli/wiki/Release-Process).
- Commitizen:
  [version_provider](https://commitizen-tools.github.io/commitizen/config/version_provider/),
  [bump](https://commitizen-tools.github.io/commitizen/commands/bump/),
  [changelog](https://commitizen-tools.github.io/commitizen/commands/changelog/),
  [exit codes](https://commitizen-tools.github.io/commitizen/exit_codes/),
  [cz_customize](https://commitizen-tools.github.io/commitizen/customization/config_file/),
  [issue #1694](https://github.com/commitizen-tools/commitizen/issues/1694),
  [CHANGELOG](https://github.com/commitizen-tools/commitizen/blob/master/CHANGELOG.md),
  [commitizen-action](https://github.com/commitizen-tools/commitizen-action).
- Python Semantic Release:
  [repo](https://github.com/python-semantic-release/python-semantic-release),
  [docs](https://python-semantic-release.readthedocs.io/en/latest/),
  [release_history source](https://python-semantic-release.readthedocs.io/en/latest/_modules/semantic_release/changelog/release_history.html).
- cocogitto:
  [repo](https://github.com/cocogitto/cocogitto),
  [bump docs](https://docs.cocogitto.io/guide/bump.html),
  [changelog docs](https://docs.cocogitto.io/guide/changelog.html),
  [issue #362](https://github.com/cocogitto/cocogitto/issues/362).
- knope:
  [repo](https://github.com/knope-dev/knope),
  [PrepareRelease](https://knope.tech/reference/config-file/steps/prepare-release/),
  [package versioning](https://knope.tech/reference/concepts/package/),
  [bot workflow](https://knope.tech/tutorials/bot-workflow/).
- git-cliff:
  [git configuration (`ignore_tags`/`count_tags`)](https://git-cliff.org/docs/configuration/git),
  [issue #1380](https://github.com/orhun/git-cliff/issues/1380),
  [issue #692](https://github.com/orhun/git-cliff/issues/692),
  [issue #588](https://github.com/orhun/git-cliff/issues/588).
- hatch-regex-commit:
  [PyPI](https://pypi.org/project/hatch-regex-commit),
  [repo](https://github.com/frankie567/hatch-regex-commit).
- Internal:
  [#143](https://github.com/hasansezertasan/copier-pyproject/issues/143),
  [#152](https://github.com/hasansezertasan/copier-pyproject/pull/152),
  [#318](https://github.com/hasansezertasan/copier-pyproject/pull/318),
  [#332](https://github.com/hasansezertasan/copier-pyproject/issues/332),
  [#339](https://github.com/hasansezertasan/copier-pyproject/pull/339),
  [ADR-002](002-release-please-for-release-automation.md),
  [ADR-004](004-commitizen-as-commit-helper-not-release-tool.md).
