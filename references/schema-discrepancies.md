# Schema Discrepancies

A durable landing spot for a structural discrepancy flagged during live
discovery that wasn't resolved in the same turn — per CLAUDE.md's "Data
discovery" section. `references/schema-map.md` is deliberately stable and
never auto-updated mid-session; when discovery turns up something that looks
like a genuinely new structural fact (a core entity/column/FK shape
`schema-map.md` doesn't already document), it gets flagged to the user first.
If the user doesn't act on it in the same turn, it goes here instead of
evaporating when the session ends — so a future, deliberate edit to
`schema-map.md` has accumulated evidence to draw on rather than relying on
one session's one-off observation being remembered by someone.

This is **not** a place for per-account business-term facts (those go in
`references/metric-glossary.md`) or for account-specific custom (`cf`) fields
and row counts (those are deliberately excluded from `schema-map.md`
entirely, per that file's own "How to use this file" section, and don't
belong here either — this file is only for a possible *structural* gap in
the stable, cross-account schema documentation).

Append new entries under **Unresolved**, oldest first. When an entry is
acted on — folded into `schema-map.md` as a real, confirmed structural
change, or rejected as account-specific rather than structural — move it to
**Resolved** with a one-line note on the outcome and the date. Never edit or
delete an entry in place; only append the resolution underneath it.

## Unresolved

_(none yet)_

## Resolved

_(none yet)_
