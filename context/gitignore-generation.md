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

## The fence is LF-sealed, which corrupts two macOS character-class patterns

**Id:** a5df0a9c-aa53-4a8c-add6-566326352a0e
**Type:** decision
**Type:** workaround
**Status:** active
**Evidence:** confirmed
**Source:** ADR-012 §1 ([`docs/adr/012-cobo-for-gitignore-generation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/012-cobo-for-gitignore-generation.md)); cobo#120/#121 (the upstreamed `--eol lf` policy), [cobo#124](https://github.com/hasansezertasan/cobo/issues/124), [issue #111](https://github.com/hasansezertasan/copier-pyproject/issues/111)
**Revisit when:** cobo#124 ships (normalize terminators only, not a mid-line CR) *and* the Copier render preserves a lone carriage return in this file

The fence is sealed with cobo's `--eol lf` policy, persisted as `eol = "lf"` on
the lock fragment. The macOS boilerplate encodes two filenames that end in a
carriage return (`Icon␍`, `.HFS+ Private Directory Data␍`) as single-line
character classes; LF normalization splits each into an unterminated `Icon[`
(matches nothing, inert) and an orphan `]` (ignores a file literally named
`]`). Those two patterns are knowingly broken in every generated project.

**Reason:** the template enforces LF everywhere (`.gitattributes`,
EditorConfig, ruff), `editorconfig-checker` fails on an embedded CR, and —
decisively — Copier renders `.gitignore.jinja` through Jinja, whose lexer
normalizes a lone `\r` to `\n` at scaffold time. A byte-exact (`preserve`) seal
would therefore report `locally modified` forever in every generated project.
There is no LF-only pattern that matches `Icon␍` precisely (`Icon?` over-matches),
so fidelity genuinely requires the CR, and the CR cannot survive the render.
These are legacy HFS resource-fork artifacts modern macOS rarely creates and
almost never commits — an accepted tradeoff, not "harmless".

**Rejected alternative:** seal byte-exact and keep the CR — fights the LF
invariant and is re-corrupted by the render anyway.

**Consequence:** the cobo-level fix is necessary but not sufficient; restoring
the patterns additionally needs a render that preserves the CR (a raw wrap or a
Copier newline carve-out scoped to this file).
