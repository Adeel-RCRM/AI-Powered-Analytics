# Documentation

Full method and known gotchas for building a dashboard's companion
Document. The policy-level rules — when to build one, where it lives, its
required sections — are in CLAUDE.md's "Dashboard documentation" section;
this file is the how-to it points to.

## Ground every chart explanation in its real query — never in its name alone

A chart's name and display type are not a reliable description of what it
computes. Before writing "What each chart means" for any card, pull its
actual logic:

```bash
mb card get <card-id> --full --max-bytes 0 --json --profile <name>
```

Read `dataset_query` end to end:

- **Aggregation** — what's actually being counted/summed, and any named
  intermediate steps. Per CLAUDE.md's "Query transparency," a well-built
  card already names these (e.g. "FTSO to Placements", "FTSOs") — read them
  off directly rather than reverse-engineering the raw MBQL.
- **Breakout** — the real grouping dimension(s), not just what the chart's
  axis label implies.
- **Filter** — every hardcoded condition baked into the query (a status
  filter, a duration threshold, a specific hiring-stage value) belongs in
  the explanation, not just in the query.
- **Joins** — what's joined in and why (a lookup table brought in only for
  a filter/breakout dimension vs. something that changes which rows are
  included at all).
- **`source-card`** — if the card is built on another saved question or
  Model, open that one too (recursively, until you hit a real table or a
  native-SQL base). The base card's own filters/logic still determine every
  number the dependent chart shows — exactly per CLAUDE.md's "Query
  transparency" section on Models: "that logic still affects every number
  the chart produces, so it can't just be left implicit."

Translate what you find into plain business language for the Document text
— no raw SQL or bare field-id dump — but **every sentence must be
traceable to something actually in the query.** Do not add:

- Causal or comparative narrative between charts ("a drop here shows up in
  X a few weeks later", "this feeds into that") unless the user or source
  material stated that connection directly — a query only tells you what a
  number counts, never why it moves or what it predicts.
- Framing about who the dashboard is "for" or why it "exists" beyond what
  the chart selection itself supports, unless there's a recorded
  requirement (`logs/history.jsonl`'s `recommendations_presented` entry, or
  a stated ask earlier in the conversation) to ground it in.

If something about a chart's logic is genuinely unclear from its query
(e.g. a field whose business meaning isn't obvious from its name), say so
as a stated caveat rather than guessing — the same "never fabricate"
standard as everywhere else in this project.

## Determine per-chart filter applicability from the real parameter_mappings — never assume a blanket list

A dashboard's filters do not uniformly apply to every card on it. Pull both:

```bash
mb dashboard get <dashboard-id> --fields parameters --json --profile <name>
mb dashboard get <dashboard-id> --full --max-bytes 0 --json --profile <name>   # for dashcards[].parameter_mappings
```

- `parameters` is the dashboard's actual filter list — use it, not an
  assumed or remembered set carried over from a different dashboard. This
  project has shipped dashboards with anywhere from 3 to 5+ filters; don't
  guess the count.
- Each dashcard's `parameter_mappings` says which of those filters are
  actually wired to that specific card, and onto which of its columns. A
  card can be missing a mapping entirely (the filter has no effect on it),
  or a trend chart can have its date breakout hardcoded to a fixed bucket
  with no `temporal-unit` parameter mapped at all — meaning the dashboard's
  Time-grouping control silently does nothing to it. Check this per card,
  not once for the whole dashboard.
- State filter applicability per section in the Document (a short "Filters
  that apply: ..." line is enough) and call out any exception plainly,
  rather than writing one generic "How to use it" paragraph that implies
  every filter reaches every chart.

## Describe each chart's drill-down from its real `click_behavior` — never a generic "everything is clickable" line

If the dashboard has drill-downs wired (per CLAUDE.md's "Drill-downs"
section), the Document must say where each one actually goes and what
carries through — not just assert that charts are clickable. Pull it from
the same full dashboard fetch used for filter applicability:

```bash
mb dashboard get <dashboard-id> --full --max-bytes 0 --json --profile <name>
# per dashcard: visualization_settings.click_behavior (dashcard-level), or
# visualization_settings.column_settings["[\"name\",\"<col>\"]"].click_behavior (per-column)
```

For each dashcard's `click_behavior`, resolve and state in plain terms:

- **Where it goes.** `linkType: "dashboard"` or `"question"` plus
  `targetId` names the destination — resolve that id (`mb dashboard get
  <targetId> --fields name` or `mb card get <targetId> --fields
  name,display`) and use its real name, not "a detail view." A pivot
  table's dedicated drill-down dashboard (per CLAUDE.md's "Drill-downs for
  a pivot table") is a distinct case worth calling out explicitly — it has
  its own independent filters, separate from the ones on the dashboard the
  reader started on.
- **What carries through.** `parameterMapping` says exactly which
  dashboard filters or clicked columns get forwarded as pre-set filters on
  the destination, and onto which of its fields. **This is not uniform
  even within one logical group of charts** — a scalar, its by-category
  breakdown, and its trend-over-time sibling can each forward a different
  subset (a trend chart often forwards only the clicked date and none of
  the dashboard's other filters, exactly mirroring the same kind of gap
  documented under "Determine per-chart filter applicability" above). Say
  so plainly rather than describing one representative chart's behavior
  and assuming the rest of its group matches.
- **Group by identical target + mapping, not by chart family.** Charts
  that share a heading in "What each chart means" often do share one
  drill-down target too, but verify it per card rather than assuming — two
  charts with very similar names can still point at different targets, or
  the same target with different fields mapped.

A short "Clicking through: ..." line per section (mirroring the "Filters
that apply: ..." line) is enough — name the real destination, list what
carries through, and flag any chart in the section whose behavior differs
from its siblings.

If a chart in scope for a drill-down (per CLAUDE.md's "Drill-downs"
section) has no `click_behavior` at all, say so as a stated fact ("this
chart has no drill-down wired") rather than omitting it from the Document
or implying it behaves like its neighbors.

### Don't stop at the first hop — check whether the destination itself has a further layer

A chart's `click_behavior` only describes the *first* click. **Always open
the destination card/dashboard itself and check its own
`visualization_settings` before writing the drill-down description as
finished** — it routinely has a second (or third) layer that a
first-hop-only description would silently miss:

```bash
mb card get <target-id> --full --max-bytes 0 --json --profile <name>
# or: mb dashboard get <target-id> --full --max-bytes 0 --json --profile <name>
```

Look for, on the *destination's* own `visualization_settings`:

- **`column_settings[...].click_behavior`** — the destination table itself
  has further click-through wired (another internal Metabase hop).
- **`column_settings[...].view_as: "link"`** — a column whose own cell
  value is a URL, styled with a friendlier `link_text` (e.g. a person's
  name instead of the raw link). Confirmed on account 101731: every detail
  table this project's automated dashboard scripts build carries "Profile"
  columns like this (`candidate_profile`, `job_profile`,
  `company_profile`, sometimes `contact_profile`/`deal_profile`) whose raw
  value is a live `app.recruitcrm.io/...` URL — a real second layer that
  leaves Metabase entirely and opens the record in the Recruit CRM
  application itself, not another Metabase view. **Confirm this by reading
  one real row's value** (`mb card query <target-id> --json`, one row is
  enough) rather than assuming every `view_as: "link"` column behaves the
  same way or points somewhere sensible.
- **Which specific link columns are actually present, on this table.**
  Don't assume a uniform "Candidate/Job/Company" set — it varies by table.
  Confirmed on account 101731: a `Calls` detail table had only one profile
  link (the related contact/candidate — no job or company link at all); a
  `Client Meetings & Visits` detail table had five (Candidate, Contact,
  Deal, Job, Company — because one row can be associated with any of those
  entity types, and only the matching column is populated on a given row);
  most others had exactly three (Candidate, Job, Company). State the real
  set per destination table, not a copy-pasted assumption from a different
  section.

If the destination is itself a full dashboard (the pivot / multi-chart
case, not a single detail question), it can have its own drill-downs wired
on top of its own charts, and its own filter panel is already a distinct
step in the chain — count it as its own step when describing how many
clicks it takes to reach an individual record (see the worked account
101731 example: the two FTSO sections take three steps — chart → dedicated
drill-down dashboard with its own filters → a Profile-link column into
Recruit CRM — while every other section takes two). State the actual
number of steps, not a blanket "click through for detail" that reads the
same whether there's one hop or three.

## Known Metabase gotchas (confirmed on v1.63.16 — re-verify if the instance is on a materially different version)

- **Embedding an existing card in a Document clones it — even when
  `cardEmbed.attrs.id` is a plain positive id for a card that already
  exists.** This is intended Metabase product behavior, not a mistake in
  the request body: `mb document create`/`update` runs the same
  "clone a readable card" path used by `POST /api/card/:id/copy` for every
  card referenced in the body, producing a new **document-owned** card
  (`document_id` set to the document's id) with a fresh id, independent of
  the source card. Confirmed by reading Metabase's own PR history
  (`metabase/metabase#80775`: "Saving a document clones every embedded
  existing card into a document-owned card row").
  - The clone is a byte-for-byte copy of the source card's `dataset_query`
    at the moment of embedding — accurate on creation, but **not kept in
    sync** if the original card is edited afterward. If a report card
    changes after its Document is built, the Document's embedded copy will
    silently drift out of date; this project has no mechanism yet to
    detect that (a real gap — a candidate for
    `references/project-improvements.md` if it bites in practice).
  - These clones don't need their own collection placement. They carry
    `document_id` and, confirmed on account 101731's "Shared Collection
    101731" (2026-09-23), do not surface in a normal `mb collection items
    <id>` listing — they live alongside the document, not as separate
    discoverable content. Don't move, rename, or otherwise organize them.
  - **On any `mb document update` after the first `create`, re-fetch the
    live document first** (`mb document get <id> --full --max-bytes 0
    --json`) and reuse the clone ids already sitting in its `cardEmbed`
    nodes — never the original source-card ids again. Re-referencing the
    original ids on a later update clones them a second time, orphaning
    the first batch (still present, still `document_id`-tagged to this
    document, but no longer referenced by any node in the body) instead of
    editing them in place.
  - The mapping from original card id to clone id is **not**
    document-position order. The server appears to assign clone ids by
    processing the *set* of unique original ids in ascending numeric
    order, then substituting them back into every position that referenced
    them — confirmed on account 101731 (25 embeds; clone ids landed in
    sorted-original-id order, not the order the cards appeared in the
    document). Don't assume the first `cardEmbed` in the document got the
    first clone id — walk the live document's actual `cardEmbed` nodes
    (see `mb document get --full`) to build the real mapping instead of
    guessing it from creation order or original-id order.
