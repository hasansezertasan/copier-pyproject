# Rationale records

## context/ is the source of the why; docs/adr/ is a frozen archive

**Id:** 02752a37-648d-4154-8548-aab28f054789
**Type:** decision
**Status:** needs-review
**Evidence:** confirmed
**Source:** maintainer decision, 2026-10-12, while reviewing [PR #386](https://github.com/hasansezertasan/copier-pyproject/pull/386)
**Revisit when:** the ADR archive is removed, or the Keep the Why dashboard and docs site are dropped

The project's rationale lives in `context/`, recorded with Keep the Why: one
entry per decision, written through the `keep-the-why` skill. The ADRs in
`docs/adr/` were carried into `context/` entries that cite them and are kept
unchanged as a frozen archive: no new ADRs are written. The archive exists only
so the `ADR-NNN` citations across `AGENTS.md`, `docs/template-architecture.md`,
`copier.yml`, the tests and the shipped template keep resolving. It is meant to
be deleted once those citations point at `context/` entries.

**Reason:** an entry records one decision with its own Evidence and Status,
where an ADR bundles several decisions under one status. The skill captures
rationale continuously during agent sessions, where an ADR waits for someone to
write one. The live dashboard, its badge and the docs site's "Why it is built
this way" section all read `context/`.

**Rejected alternative:** keep writing ADRs and mirror each one into
`context/`. Two living copies of the same rationale drift apart.

**Rejected alternative:** delete `docs/adr/` immediately. The ADR numbers are
cited throughout the repository and in template files that ship to generated
projects, so every citation would have to be rewritten first.

**Consequence:** the archive is deleted (issue #398). Every `ADR-NNN` `Source`
line links the last revision that carries the record, and `git show
<sha>:docs/adr/<file>` reads it offline. What the entries do not carry as fields
is the ADRs' own lifecycle, kept here:

- Dates: ADR-001 to 005, 036 and the tested-documentation 028 carried no date;
  006 to 008 are 2026-06; 009 to 012 are
  2026-07; 013 to 029 are 2026-08; 030 to 035 are 2026-09; 039 is 2026-10.
  ADR-038 was renumbered from 027 and refreshed on 2026-10-05. ADR-037 is a
  research record under discussion, never decided.
- Most ADRs stayed `Proposed` and were never promoted to `Accepted`, so the
  status field was not maintained and says little about whether a decision held.
- Numbers were reused: 020, 028 (four), 032 and 035 each name two or more
  different records, told apart by title.
- Supersession: ADR-003 in part (Pants and Trunk removed, 2026-06); 007
  supersedes the single `include_pycrucible` toggle; 012 supersedes the gibo
  workflow; 016 supersedes the `minimal`/`standard`/`full`/`custom` presets of
  PR #141; 017 supersedes its own in-repo-generation design; 018 in part by 021;
  023 §3 and §4 (2026-10); 026 in part by the per-component 028.
