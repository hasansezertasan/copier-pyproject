# ADR-020: Freeze shipped template pins from this repo's Renovate

## Status

Accepted (2026-08). Refines the `copier update` automation established in
[ADR-015](015-template-self-versioning-and-copier-update-automation.md); depends
on the shared Renovate preset `github>hasansezertasan/renovate-config:python`
that both this repo and every generated project extend.

## Context

Generated projects ("downstream adapters") receive template updates through
Renovate's [`copier` manager](https://docs.renovatebot.com/modules/manager/copier/)
(ADR-015): when this repo cuts a new tag, Renovate runs the real `copier update`
in the downstream and opens a PR with the re-rendered diff.

Every generated project also ships its own Renovate config (the same shared
preset), so downstream Renovate independently bumps the version literals the
template rendered into it — action SHAs in `.github/workflows/*`, `rev` pins in
`prek.toml`, tool versions in `mise.toml`, and any dependency pins.

The problem: **this repo's Renovate was bumping those same literals inside
`template/**` too**, on its own cadence. `copier update` is a git 3-way merge per
file:

- **base** = the old template render
- **ours** = the downstream's current file (with *its* Renovate bumps)
- **theirs** = the new template render (with *this repo's* Renovate bumps)

A pinned line only conflicts when both sides moved it to different values
(`base != theirs` **and** `ours != theirs`). Because both repos' bots advance the
same literals on independent schedules, they almost always diverge — so the
copier-update PR conflicts on nearly every release. Renovate does not even fail
its artifacts check on those conflicts
([renovate#31600](https://github.com/renovatebot/renovate/issues/31600), noted in
ADR-015), so a downstream PR can look mergeable while carrying `<<<<<<<` markers.

The template re-rendering those pins is itself the divergence generator:
downstream already owns those bumps.

## Decision

**Freeze the shipped pins from this repo's Renovate.** A disabled `packageRules`
entry in `.github/renovate.json` matches `template/**` and sets
`enabled: false`, so Renovate performs no version updates on any file under
`template/`:

```json
{
  "packageRules": [
    { "matchFileNames": ["template/**"], "enabled": false }
  ]
}
```

The shipped literals become **seed values only**. Each generated project owns
their bumps thereafter via its own Renovate. With `template/**` frozen,
`theirs == base` on every pin line, so the downstream's value always wins the
3-way merge cleanly — the conflict class is eliminated structurally, not merely
reduced.

`matchFileNames` + `enabled: false` is used rather than top-level `ignorePaths`
so the preset's default `ignorePaths` (node_modules, dist, …) is preserved
instead of replaced, and so the rule composes cleanly with the shared preset's
`customManagers`/`pinGitHubActionDigests` policy.

This repo's **own** root workflows (`.github/workflows/*.yml`), `prek.toml`, and
`mise.toml` stay Renovate-managed, so the template's own CI keeps current tool
versions. (The gitignored `example/` renders *from* `template/`, so it inherits
the frozen seed pins — valid, just not necessarily latest.)

In practice the confirmed conflict source was the **plain** `template/*.yml`
workflow files (e.g. PR #196 bumped `setup-uv` in both this repo's own workflows
and the shipped `template/.github/workflows/docs-*.yml`). The `.jinja`-suffixed
files (`prek.toml.jinja`, `*.yml.jinja`) are not matched by Renovate's stock
`github-actions`/regex managers, so freezing them is a safe no-op unless the
shared preset's `customManagers` are extended to reach them; the `template/**`
match covers every case either way.

## Consequences

- `copier update` PRs in downstream projects no longer conflict on version pins
  — the friction that motivated this ADR is gone.
- Newly-generated projects start with slightly-stale-but-valid seed pins; their
  own Renovate opens catch-up PRs on the first run, so staleness is transient and
  never a security regression for long.
- To ship less-stale seeds, refresh the `template/**` pins **deliberately** (by
  hand, or a one-off scoped Renovate run) right before cutting a template
  release. Accept that any such bump reintroduces conflicts only for projects
  that had not yet caught up — the opposite trade-off from the default freeze, so
  reach for it only when seed staleness actually matters.
- **Do not re-enable Renovate for `template/**`.** It reads as "the template's
  pins are falling behind," but re-managing them re-creates the conflict engine
  this ADR removed. A `CLAUDE.md` note guards against the well-intentioned undo.
- Alternatives considered:
  - **Auto-resolve in the downstream's favor** — a git `merge=ours` driver or
    copier `_exclude` on the volatile files. Rejected: `_exclude` is whole-file
    and would also block genuine template changes (a new hook, a new CI job) from
    propagating; a per-downstream merge driver is fragile to install and easy to
    lose.
  - **Converge by cadence** — group this repo's bumps and release immediately,
    hoping `ours ~= theirs` at update time. Rejected: only shrinks the race
    window; still races.
