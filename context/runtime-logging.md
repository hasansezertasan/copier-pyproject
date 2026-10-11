# Runtime logging and initialization

## An unavailable home directory permits placeholders, not shared-temp logging

**Id:** 1488d613-3cce-4249-ade8-3a6dacbaceec
**Type:** decision
**Type:** constraint
**Status:** active
**Evidence:** confirmed
**Source:** [PR #126](https://github.com/hasansezertasan/copier-pyproject/pull/126), [rejection of the temporary-log fallback](https://github.com/hasansezertasan/copier-pyproject/pull/126#issuecomment-5168172412); commit [f47e6fc](https://github.com/hasansezertasan/copier-pyproject/commit/f47e6fc4aa885851b671eb33772b472abcb24f26)
**Verification:** corroborated — `core/dirs.py.jinja` distinguishes home resolution from placeholder paths, and `core/logging_setup.py.jinja` disables file logging when home resolution fails
**Revisit when:** logging initialization becomes lazy or the template adopts a verified user-private fallback directory

Logging attaches the console handler before attempting file logging. Failure to
resolve the home directory disables file logging entirely; file-system errors
with a resolved home also degrade to console-only logging. Directory values may
still use a temporary-directory-derived `Path` as a placeholder, but the template
does not automatically write logs there.

**Reason:** logger initialization can happen at module import, so unavailable or
unwritable home storage must not crash read-only commands. A predictable shared
temporary log path can be pre-created or symlinked by another local user; its
existence as a valid `Path` does not establish safe ownership for writes.

**Rejected alternative:** automatically log under a shared temporary project
directory when home resolution fails. The initial fallback was explicitly
rejected because it creates a local log-hijacking opportunity.

Lazy file-handler initialization was suggested, but the reviewed evidence does
not establish why it was not selected. The current cached logger accessor also
does not make module-level calls lazy: caching prevents repeated setup, not the
first import-time initialization.
