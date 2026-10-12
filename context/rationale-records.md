# Rationale records

## context/ is the source of the why; docs/adr/ is a frozen archive

**Id:** 02752a37-648d-4154-8548-aab28f054789
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** maintainer decision, 2026-10-12, while reviewing [PR #386](https://github.com/hasansezertasan/copier-pyproject/pull/386)
**Revisit when:** the ADR archive is removed, or the Keep the Why dashboard and docs site are dropped

The project's rationale lives in `context/`, recorded with Keep the Why: one
entry per decision, written through the `keep-the-why` skill. The 43 ADRs in
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
