# Canonical Patterns

Recurring, genuinely reusable chart/query *shapes* this project has already
built and verified — not business-term definitions (those go in
`references/metric-glossary.md`) and not structural schema facts (those go in
`references/schema-map.md`). A pattern here is a **construction**: which
entities it joins, what it ranks/summarizes and how, and when it does (and
doesn't) apply — the kind of thing `prompts/requirements-intake.md`'s
resolution ladder checks first, before falling back to schema/glossary
lookups or live discovery.

## How this file is organized

Each pattern is its own subsection, named for what it computes — not for the
one chart it was first built for. Include:

- **Applies to** — the entity/table shape this pattern needs (e.g. "any
  account with a `hiring_stage`-style pipeline table").
- **Construction** — the reusable logic in plain terms: which tables it
  joins, what it ranks or summarizes, and the key steps (per CLAUDE.md "Query
  transparency" — name the steps, don't just describe a black box).
- **Confirmed on** — which account(s) this has actually been built and
  verified for.
- **When NOT to reuse it** — the specific conditions that mean this shape
  doesn't apply (a different join cardinality, a business rule that varies by
  account, etc.) — reusing a pattern where it doesn't actually fit is worse
  than not having one.

## Adding a new pattern

Only after a chart is built and verified (`prompts/chart-generation.md` step
7/8) and its underlying logic is genuinely reusable across more than one
likely question or account — not for a true one-off (see CLAUDE.md "Chart
creation" for the same reusability bar applied to Models). Append a new
subsection here rather than editing an existing one if a later account's
version of the same idea has a materially different construction — note the
difference under "When NOT to reuse it" on the original instead of silently
overwriting it.

---

## Outreach/engagement activity classification via UNION across heterogeneous log tables

- **Applies to** — an account where "outreach activity" or "engagement
  activity" spans more than one physically distinct log table (e.g. calls
  in a call-log table, texts in a messaging table, emails/other channels
  logged as notes with a label field) and needs a single unified
  id/owner/timestamp/category feed — for a breakdown table, a pie by
  activity type, or any chart that needs to treat these as one metric
  family. Requires native SQL (a `UNION ALL` across heterogeneous sources
  isn't expressible in MBQL) — build as a **Model**, never a one-off native
  SQL question, since this shape is inherently meant to back more than one
  chart.
- **Construction** — one `SELECT ... UNION ALL ...` per outreach category,
  each branch projecting the same four columns in the same order
  (`id`, an owner/rep name — joined from a teams/users table where the
  source table only carries a raw `created_by`/FK id, not a name — a
  timestamp column, and a literal string naming that branch's
  `outreach_type`), filtered to the specific value(s) that define that
  category on its source table (e.g. `call_type_label = 'Cold Call'` on a
  call-log table, `note_label = 'Email Sent'` on a notes table). The
  resulting Model's own single column set (`id`, `owner_name`,
  `created_on`, `outreach_type`) is what every chart built on it then
  breaks out/aggregates by — no further per-branch logic needed downstream.
- **Confirmed on** — account 89060 (Cleveland Clinic). Two verified
  instances share this exact shape but intentionally diverge on which
  literal filter values define each branch:
  - Model #52671 ("Outreach Activity") — the account's general-purpose
    version: `Calls made` (`call_type = 'Outgoing call'`), `Texts sent`,
    `Emails Sent`, plus several further notes-based categories
    (`LinkedIn Messages Sent`, `Indeed Messages Sent`, connect-type
    variants, etc.).
  - Model #76245 ("Outreach Activity - Cold Calls Variant") — built for
    a different chart's specific need (Weekly Outreach, Outreach Activity
    pie): reuses #52671's `Texts sent`/`Emails Sent` branches verbatim, but
    swaps the Calls branch for `Cold Calls` (`call_type_label = 'Cold
    Call'`), a value #52671's own `Calls made` branch couldn't produce by
    filtering its output — that definition is baked into #52671's own
    native SQL, and #52671 is pre-existing content this project doesn't
    modify. Built as a new Model rather than editing #52671, per hard
    constraint 7.
- **When NOT to reuse it** — the *construction* (UNION shape, four-column
  branch contract, Model-not-one-off) generalizes; the **specific literal
  filter value(s) per branch do not** — confirm what actually defines each
  outreach category on this account's own data (via the user, not by
  querying live values) before reusing this shape, even for a second chart
  on the *same* account, exactly as #76245 needed a different Calls
  definition than #52671 despite both being "outreach activity" on the same
  account. Never assume another account's table/column names, label values,
  or even which categories exist — confirm structure via `mb table fields`
  and category values via the user/`references/metric-glossary.md` per the
  usual discovery rules before applying this shape elsewhere.
