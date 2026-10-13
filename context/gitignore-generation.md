# .gitignore generation

## cobo generates the gitignore with a hash-sealed fence and lockfiles

**Id:** 3e3bc38e-bc1e-4e65-b74d-e91848262157
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-012 ([`docs/adr/012-cobo-for-gitignore-generation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/012-cobo-for-gitignore-generation.md))
**Revisit when:** `github/gitignore` stops being the boilerplate source, or cobo changes its fence or lock format
**See:** ci-topology.md#network-dependent-checks-run-on-a-weekly-cron-never-in-the-merge-gate — 3e5b9525-9087-4125-b19f-80f6c226c01f — as of 2026-10-11

cobo fetches the same `github/gitignore` boilerplates the previous gibo
workflow stacked, but writes them inside a sha256-sealed fence and records the
upstream commit and per-file blobs in `cobo.lock`. The repository root lock
carries two fragments — the template source and this repository's own
`.gitignore` (dogfooding) — and `template/cobo.lock` ships verbatim so a
generated project's gitignore is drift-checkable. cobo is always-included
tooling (a mise `pipx:` tool, Renovate-tracked), with no toggle. The project's
own overrides (the freezer spec negation, the C-extension ignore) sit below the
end fence, where cobo preserves them; the negation still lands after the fenced
`*.spec` ignore, so it wins.

**Reason:** gibo was run by hand with no lockfile, no pin the tooling
understood and no way to detect upstream drift, and the overrides were injected
inside the boilerplate it generated.

**Rejected alternative:** keep gibo — the gaps above.

**Consequence:** the cobo-managed `.gitignore` is excluded from the
`trailing-whitespace` hook, because upstream ships trailing whitespace on some
comment lines and trimming inside the fence breaks the seal; `cobo.lock` is
`linguist-generated` and carries its own 2-space EditorConfig stanza (taplo's
`*.toml` glob does not cover `.lock`). Regeneration is `cobo update` followed
by `cobo sync`; a hand edit inside the fence breaks the sha256.

## The seal keeps the two macOS CR patterns; the render still strips them

**Id:** a5df0a9c-aa53-4a8c-add6-566326352a0e
**Type:** decision
**Type:** workaround
**Status:** active
**Evidence:** confirmed
**Source:** ADR-012 §1 ([`docs/adr/012-cobo-for-gitignore-generation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/012-cobo-for-gitignore-generation.md)); cobo#120/#121 (the upstreamed `--eol lf` policy), [cobo#124](https://github.com/hasansezertasan/cobo/issues/124), [issue #111](https://github.com/hasansezertasan/copier-pyproject/issues/111), [issue #393](https://github.com/hasansezertasan/copier-pyproject/issues/393)
**Revisit when:** the Copier render preserves a lone carriage return in this file (the cobo half — normalize terminators only, not a mid-line CR — already shipped in cobo 0.6.0)

The fence is sealed with cobo's `--eol lf` policy, persisted as `eol = "lf"` on
the lock fragment. Since cobo 0.6.0 that policy normalizes terminators only
(`CRLF` → `LF`) and keeps a mid-line lone CR — so the sealed
`template/.gitignore.jinja` carries the macOS boilerplate's two carriage-return
filenames (`Icon␍`, `.HFS+ Private Directory Data␍`) byte-intact, and the old
"seal LF-normalizes them into `Icon[`/`]`" description is stale. The corruption
moved one stage down the pipeline: Copier renders `.gitignore.jinja` through
Jinja, whose lexer normalizes a lone `\r` to `\n` at scaffold time (verified by
rendering a CR-bearing probe template with the pinned copier). Every rendered
project therefore still checks out the split `Icon[` (unterminated class,
matches nothing, inert) / `]` (a literal pattern matching a file or directory
named `]` at any depth — a non-issue in practice, and no post-fence `!]`
override: it would stamp noise on every generated project for a filename that
essentially never exists) pair — and, because the fence sha256 covers the
CR-bearing bytes, additionally reports `up to date; locally modified` on
`cobo check`. An up-to-date `cobo sync` still succeeds as a no-op, but a later
sync that must apply upstream drift fails without `--force` on the
locally-modified block — until fence verification tolerates the
render-stripped CR (verified by rendering the template and running
`cobo check` and `cobo sync` against the shipped lock).

**Reason:** the template enforces LF everywhere (`.gitattributes`,
EditorConfig, ruff) and there is no LF-only pattern that matches `Icon␍`
precisely (`Icon?` over-matches), so fidelity genuinely requires the CR, and
the CR cannot survive the Jinja render. These are legacy HFS resource-fork
artifacts modern macOS rarely creates and almost never commits — an accepted
tradeoff, not "harmless".

**Rejected alternative:** seal byte-exact and keep the CR — fights the LF
invariant and is re-corrupted by the render anyway.

**Consequence:** the remaining fix is render-side or check-side, not
seal-side: either a Copier/Jinja newline carve-out scoped to this file, or
cobo fence verification that treats a render-stripped lone CR as clean under
`eol = "lf"`. Until then, refreshes come from a template-side `cobo sync`,
never from a local `cobo dump` in a generated project (whose bytes
`copier update` can never reproduce) — that rule is recorded in the NOTE below
the fence in `template/.gitignore.jinja`.

## Node and GitHubPages ride always-on in the seal

**Id:** 00d055c4-152a-4b0d-b0b6-a8ecf6bdc557
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** [issue #393](https://github.com/hasansezertasan/copier-pyproject/issues/393)
**Revisit when:** a fragment arrives that only a subset of generated projects can use without tripping their drift check

The seal pins seven `github/gitignore` boilerplates
(`macOS`, `Windows`, `Linux`, `VisualStudioCode`, `Python`, `Node`,
`GitHubPages` @ `0e5d690`) — unconditionally, with no toggle. Downstream
projects that publish docs to Pages or touch any JS tooling used to hand-add
`Node` + `GitHubPages` ad hoc and diverge from the template until the next
`copier update` clobbered them.

**Reason:** a fragment gated on a toggle (e.g. `GitHubPages` on
`include_docs`) would need a Jinja-conditional seal *and* a Jinja-templated
`cobo.lock`, with drift-check edge cases for every answers combination; the
`VisualStudioCode` precedent already established that always-on is acceptable.
Deciding once here beats every project hand-editing the seal.

**Rejected alternative:** gate `GitHubPages` on `include_docs` — leaner seal
for non-docs projects, rejected for the lock-templating complexity above.

**Consequence:** the refresh re-pinned `57286c3` → `0e5d690` at the same time
(only `Python.gitignore` had changed upstream: `UV` → `uv`, mkdocs/Zensical,
a VSCode comment rewrap). Both root-lock fragments (`template/.gitignore.jinja`
and the dogfooded repo `.gitignore`) carry the same seven files, and
`template/cobo.lock` ships the same set to generated projects. The pin refresh
also surfaced the seal-keeps/render-strips CR split above, whose check-side
follow-up lives in the cobo tracker, not here.
