# Performance tracking

Measures how much of a Requirements Intake requirement is genuinely this
project's own contribution versus the user's manual work, and what that
contribution was worth in time — so progress against `docs/vision.md`'s
goals is something the project can actually check over time, not just
assert. Scoped to **Requirements Intake only**: the Default Dashboard and
Important Metrics Dashboard flows are fixed, automated templates with no
per-requirement resolution judgment to score.

This is a **separate log from `logs/history.jsonl`**, at
`logs/performance-tracking.jsonl` — same git-committed, append-only,
never-edit-a-line-in-place discipline (concurrent teammates' appends must
never conflict), but a different content type: `history.jsonl` is an audit
trail of what was built; this is an assessment of how much of it held up
unchanged and what that was worth. Read `references/effort-estimation-rubric.md`
before scoring anything here — it defines every weight this file applies
and why they're estimates, never measurements.

## Why not just ask the user how long it would have taken manually

Estimating a full manual build well requires the same requirement analysis
this project has already done to build the thing — which tables, which
joins, which business logic. Asking the user to redo that judgment
independently, just to produce a time figure, duplicates real work for no
accuracy gain. Instead, comprehension time and build time are both scored
from the real, structural shape of what was actually discovered and built,
against `references/effort-estimation-rubric.md` — never a chart count,
never a flat per-type average, and never a number asked of the user as a
hypothetical.

The one thing that genuinely can't be known any other way — how long the
user's own manual fixes took — is asked directly, because it's recall of
real work they just did, not a hypothetical requiring fresh analysis.

**`manual_fix_minutes_reported` and `total_time_saved_minutes` measure two
different things and can never be directly compared, not just never
netted.** `total_time_saved_minutes` is a standardized benchmark — the
same rubric, applied the same way, meant to represent a generic
professional analyst's pace (see `references/effort-estimation-rubric.md`).
`manual_fix_minutes_reported` is one specific person's actual recall of
their own fix — and the person doing that manual review on this project is
a professional data analyst with deep, specific context on Recruit CRM,
Metabase, and this account's own data that a generic benchmark doesn't
assume. That's *why* it's reported faster than the standardized number
would predict for the same fix, not evidence the standardized number is
wrong — they're not measuring the same population. Report both, side by
side, per "Step 2" above, but never frame one as validating, contradicting,
or offsetting the other — they're not commensurable, by design.

## Requirement-unit outcomes

**A "requirement-unit" for `unit_type: "chart"` is a resolution batch, not
a resulting card** (v2.0 — see `references/effort-estimation-rubric.md`'s
changelog for why). Several numbered charts in Requirements Intake's output
can come from one batch — requirements resolved together, sharing
discovery/decisions, per `prompts/requirements-intake.md`'s "Resolving each
requirement" step 4 (e.g. 8 KPI metrics stated together for one tab). That
whole batch gets exactly one `requirement_pending`/`requirement_confirmed`
pair, with every card it produced listed in the entry's `cards` array (see
"Log schema" below) — not one pending/confirmed pair per card.
`dashboard_assembly`/`pivot_drilldown_dashboard`/`documentation` units are
unaffected by this — each is still its own single unit, never grouped with
a chart batch or with each other.

Every requirement-unit gets exactly one outcome, and every outcome gets
logged — **nothing is dropped from this record because the result wasn't a
clean success.**

- **`built_clean`** — every card in the batch (or the dashboard/document
  element, for a non-chart unit) shipped exactly as built, with no changes.
  Full comprehension credit and full build credit.
- **`built_modified`** — at least one card in the batch changed after it
  was built. Credit is scored **per card**, from a structural diff (see
  "Diffing" below), granular, never all-or-nothing: a card the user only
  tweaked one filter on keeps most of its build credit; one rebuilt from
  scratch keeps none; an untouched card in the same batch keeps full
  credit — then the batch's `pct_claude_build` is the sum across every
  card in it (see `references/effort-estimation-rubric.md`'s "How the two
  combine"). Full comprehension credit either way — figuring out what to
  build is a separate cost from getting each card's build exactly right.
- **`infeasible_data`** — the account's actual data couldn't support the
  requirement (per `prompts/infeasible-requirement.md`). Not a miss on this
  project's part: full comprehension credit (correctly diagnosing this is
  real work a human would have had to do too), zero build credit since
  nothing was built. Logged immediately, in real time, at the point
  `prompts/infeasible-requirement.md`'s Step 1 is confirmed with the
  user — never deferred to a later confirmation pass.
- **`infeasible_tool_capability`** — the data genuinely supports it, but
  building it is beyond what this project's current prompts/scripts/
  patterns can produce (see `prompts/requirements-intake.md`'s "Resolving
  each requirement" for when this applies versus `infeasible_data`). A
  genuine gap, not a data problem. Zero credit either way, logged
  immediately when determined, and it feeds
  `references/project-improvements.md` (see "Feeding back into the
  project" below).
- **`extra_manual_addition`** — during confirmation, the user reports
  building something beyond what this project produced for the request.
  Ask which kind it is:
  - **Covering part of the original ask** that was silently missed — not
    flagged as infeasible at the time, just absent. A real gap: zero
    credit, and it feeds `references/project-improvements.md` the same as
    `infeasible_tool_capability`, since silently missing something is a
    worse failure mode than correctly flagging it.
  - **New scope** that came up after the original ask was already
    resolved. No bearing on this project's handling of the original
    requirement — logged as context only, no credit calculation involved
    (it was never asked of this project in the first place).

## Step 1 — as the requirement is resolved and built

**Drill-downs are part of the requirement, not an afterthought bolted on
after tracking already closed it out.** CLAUDE.md/`prompts/requirements-intake.md`
already sequence a dashboard's build correctly (cards → assembly →
documentation, if requested → **then** the drill-down yes/no confirmation,
once the dashboard is finalized) — but performance-tracking's own snapshot
must wait for that same finish line, not fire the moment each batch's
cards are individually built. Snapshotting before drill-downs are resolved
means either scoring an incomplete requirement, or a second disjointed
tracking pass bolted on later when drill-downs do land (confirmed
first-hand: this is exactly what happened on account 89060 — the 3 chart
batches and dashboard assembly got confirmed before drill-downs existed,
then 13 new drill-down cards had to be reconciled in as their own
separate, awkward follow-up instead of being part of one coherent
picture).

**For `built_clean`/`built_modified` candidates** (anything that actually
gets a card created): `prompts/chart-generation.md` step 10 records this
card's own build-time snapshot (`build_elements_snapshot`,
`build_minutes_snapshot`, `dataset_query_snapshot`,
`visualization_settings_snapshot`, `click_behavior_snapshot`) into the
current resolution batch's accumulating set of cards — it does **not**
append the `requirement_pending` entry itself, since a batch isn't
complete until every card it produces has been built and verified.

**The batch's `requirement_pending` entry itself does not get appended
until the *dashboard* those cards land on is fully finalized** — every
batch feeding that dashboard built and verified, the dashboard assembled,
its companion documentation Document resolved if the user asked for one,
**and the drill-down yes/no question asked and resolved** (drill-downs
actually wired, or the user explicitly declined them) — see "Log schema"
below. If the user declines drill-downs, that's still a resolution: log
the batch's `requirement_pending` entry as soon as that "no" is given,
with `build_elements_snapshot.drilldowns_wired: 0` for every card (not a
placeholder waiting on a future "yes"). This captures everything knowable
at build time in one coherent snapshot: the comprehension score (scored
once for the batch, per `references/effort-estimation-rubric.md`), the
`cards` array (one element per resulting card, each with its own snapshot
— including `click_behavior_snapshot` and a real `drilldowns_wired` count
if drill-downs were built), and the question/iteration counts for the
batch. No user interaction needed for the logging itself — it's
bookkeeping, the same as the existing `chart_created` history-log entries
right next to it (one `chart_created` entry per card still gets logged
individually, per CLAUDE.md "History log", at actual build time — only
performance-tracking's own entry waits for the full picture).

Dashboard assembly, a pivot table's dedicated drill-down dashboard, and a
companion documentation Document are each their own unit with their own
`requirement_pending` entry (`unit_type` values `dashboard_assembly`,
`pivot_drilldown_dashboard`, `documentation` respectively). **Their
`chart_created`/`dashboard_created`/`dashboard_updated` entries in
`logs/history.jsonl` still fire at the point each is actually verified**
(CLAUDE.md "History log" is unaffected by this) — only the
performance-tracking `requirement_pending` entry waits, same as the chart
batches above, since `dashboard_assembly`'s own snapshot is the
dashboard's `dashcards` (which carries each dashcard's `click_behavior`)
and would otherwise be taken mid-way through the requirement, before
drill-downs exist. Their snapshots are the dashboard's
`dashcards`/`tabs`/`parameters`, or the Document's body, respectively, in
place of a card's `dataset_query`.

**For `infeasible_data`/`infeasible_tool_capability`:** log a single,
complete `requirement_outcome` entry immediately when determined — there's
no future unknown to wait on, so there's no pending phase. `infeasible_data`
entries are created once `prompts/infeasible-requirement.md`'s Step 1 is
confirmed with the user. `infeasible_tool_capability` entries are created
the moment resolution concludes the gap is in this project itself, not the
account's data.

## Step 2 — the confirmation flow

**Trigger:** either the user says their manual pass on an account's work is
done and asks to confirm (in this session or a later one), or a new session
proactively surfaces unconfirmed pending entries (see "Pending-entry check"
below) and the user agrees to confirm now.

Once triggered, for the account in question:

1. **Re-fetch and diff automatically — don't ask the user to describe what
   changed.** For every `requirement_pending` entry with no matching
   `requirement_confirmed` entry (same `tracking_id`): for a `chart` batch,
   re-fetch and diff **every card in its `cards` array** individually
   (`mb card get <id> --full --json`) against that card's own snapshot; for
   `dashboard_assembly`/`pivot_drilldown_dashboard`/`documentation`,
   re-fetch the one dashboard/document (`mb dashboard get <id> --full
   --json` / `mb document get <id> --full --json`) as before. Diff per
   "Diffing" below. This determines each card's own retained/changed
   element set, which rolls up into the batch's overall `built_clean` vs.
   `built_modified` outcome (any one card changed → `built_modified` for
   the batch) and its summed `pct_claude_build`.
2. **Ask only what the diff can't tell you:**
   - For anything that came back `built_modified`: briefly confirm the diff
     read correctly (e.g. "Looks like you changed the filter on 'Placement
     Rate by Client' and rebuilt 'Owner Activity Trend' — is that right?"),
     and ask how long the manual fixes took, in total, across everything
     changed for this account's request — the user's own estimate of real
     work they just did, not a hypothetical.
   - Ask whether any additional cards/dashboards were created beyond what
     this project built, and if so, which kind (`extra_manual_addition`'s
     two sub-cases above).
3. **Score and log.** For each `requirement_pending` entry, compute
   `build_minutes_final`/`build_minutes_retained` **per card**, sum them
   into `build_minutes_final_total`/`build_minutes_retained_total`, then
   `pct_claude_build` and `total_time_saved_minutes` for the whole batch,
   per `references/effort-estimation-rubric.md`, and append a
   `requirement_confirmed` entry with the same `tracking_id`. Log
   `extra_manual_addition` entries per the user's answers in step 2.
4. **Root-cause every `built_modified` card** per "Feeding back into the
   project" below — this is not optional cleanup, it's how
   `pct_claude_build` actually improves over time instead of just being
   measured. Apply the fix (a reference-file correction) or log it (a
   `project-improvements.md` entry) in this same turn, before moving on.
5. **Feed `references/project-improvements.md`** for any
   `infeasible_tool_capability` or missed-original-requirement
   `extra_manual_addition` surfaced in this pass, per "Feeding back into
   the project" below.
6. **Report a complete metric profile, every time** — after logging any
   `requirement_pending` or `requirement_confirmed` entry (single-entry or
   a summary across several), show all of: `outcome`, `comprehension`,
   `build` (retained/final), `pct_claude_build`, `total_time_saved_minutes`,
   and **`manual_fix_minutes_reported`**. Never omit the manual-fix figure
   from a summary — CLAUDE.md "Performance tracking" already says it's
   tracked as "its own honest number" and never netted against time saved,
   but tracking it in the log and actually *showing* it are different
   things; a summary that only surfaces `total_time_saved_minutes` tells
   half the story and was confirmed missing once already (account 89060,
   2026-09-18 — the log had the real 20-minute manual-fix figure the whole
   time, the reported summary just never displayed it). Show times in
   hours/minutes for readability, not raw decimal minutes (keep the raw
   figures in the JSONL log itself, where exact arithmetic matters).

Don't attempt any part of this flow before the user has actually had a
chance to make manual changes — asking immediately after the dashboard is
assembled defeats the purpose of measuring what genuinely survived
untouched.

## Diffing a card/dashboard against its snapshot

Compare **structurally, semantically** — not byte-for-byte. Internal id
reordering or incidental key ordering differences don't count as a change;
the question is whether the same logical operation is still there.

**Strip every `lib/uuid` before comparing anything.** Confirmed live
(2026-09-18, account 662 test run): Metabase re-mints a fresh `lib/uuid` on
every clause of every save, even when nothing about the clause itself
changed. A direct equality check on the raw JSON — including a join,
aggregation, or breakout that is otherwise byte-identical — reports it as
changed purely because its `lib/uuid`s differ, which would wrongly zero out
credit for work that's actually untouched. Recursively strip `lib/uuid`
keys from both the snapshot and the current object before comparing
anything else in this section.

- **Joins** — match by table + join condition. Same table, same condition:
  retained. A changed condition, an added/removed join: not retained.
- **Summarize/aggregation steps** — match by aggregation function + field +
  name. A changed function or field: not retained.
- **Custom expressions** — match by formula. Any edit to the formula: not
  retained.
- **Filters** — match by field + operator + value. Any change: not
  retained.
- **Chart type/`display`** — retained only if identical.
- **`visualization_settings`** (`series_settings`, `column_settings`,
  `graph.show_values`, etc.) — compare key by key; an unchanged key is
  retained even if unrelated keys changed elsewhere.
- **`click_behavior`** per dashcard — compare the whole configured
  behavior; any edit to its target or parameter mapping: not retained.
- **Dashboard-level** (`unit_type: dashboard_assembly`) — compare
  `dashcards` layout, `tabs`, and `parameters` the same way: an added
  dashcard or a remapped filter is a change; an untouched card's position
  and mappings are retained. (A dashboard this project assembles should
  never lose an existing element per hard constraint 7 — a removal here
  would be surprising and worth flagging to the user directly, not just
  silently scoring it as "not retained.")

Score `build_minutes_final` against everything present in the current
state; score `build_minutes_retained` against only the elements that
matched. An element present in the snapshot but absent from the current
state simply isn't part of `build_minutes_final` at all — it needs no
separate handling.

## Feeding back into the project

An `infeasible_tool_capability` outcome, or an `extra_manual_addition`
classified as covering a missed original requirement, means this project
itself has a real gap — not the account's data, not a one-off. Log it to
`references/project-improvements.md` per `prompts/project-improvement.md`'s
"Log it" step, same as any other project-improvement finding, citing the
account and the specific requirement that exposed the gap. This happens as
part of Requirements Intake itself the moment the outcome is determined —
it does not require, and is not part of, the separate on-demand "Project
improvement review" CLAUDE.md describes.

**Every `built_modified` card gets a root-cause check, not just a score.**
Scoring `pct_claude_build` and moving on treats a manual fix as a one-time
cost; it does nothing to stop the *same* fix being needed on the next
similar card. The point of tracking this at all is to shrink
`pct_human_build` over time, not just report it — so as part of Step 2, for
every card that came back `built_modified`, ask **why** the change was
needed, using the diff plus a brief look at what the original build was
based on:

- **A business-term/stage/value mapping that was guessed, stale, or never
  confirmed** — fix it at the source, in the same turn: correct or add the
  entry in `references/metric-glossary.md` (per that file's own
  append-only `Superseded` convention if it contradicts an existing entry),
  `references/canonical-patterns.md`, or `references/schema-map.md`,
  whichever actually owns the fact that was wrong.
- **A caveat that existed but wasn't surfaced prominently enough for the
  user to catch before it required a live fix** (e.g. a chart built on a
  glossary entry already tagged `caveat` — thin data, a substituted value)
  — the fix isn't the glossary entry itself, it's *how loudly this project
  surfaces a caveat-status build* when first reporting the card back to the
  user. That's a prompt-level gap: log it to
  `references/project-improvements.md` per `prompts/project-improvement.md`'s
  "Log it" step, same bar as an `infeasible_tool_capability` finding —
  this widens that feed beyond the two outcome types in "Requirement-unit
  outcomes" above to any `built_modified` case whose root cause is fixable
  at the source, not just infeasibility or a missed original requirement.
- **A missing canonical pattern** this account's shape should have matched
  (a repeatable chart construction this project builds often enough that it
  belongs in `references/canonical-patterns.md`, per that file's own
  criteria) — log it the same way.
- **Genuinely cosmetic preference with no fixable source** (a color, a
  column alignment, a row-highlight style with no "correct" answer this
  project could have known in advance) — no fix applies. Say so explicitly
  rather than silently skipping the check; that absence is itself the
  finding for this card. **Before concluding this, check whether the same
  visualization-settings change shows up on more than one card in the same
  batch (or account).** One card's color choice really might be arbitrary;
  the *same* setting applied independently to two or more cards is
  evidence of an actual standard the user expects by default, not a
  one-off — that's `core-function-quality`/`consistency` territory, fixable
  by encoding the pattern as a default in CLAUDE.md's "Chart creation"
  formatting conventions (see "Data labels"/"Table formatting" for the
  existing shape this kind of rule takes), not a dead end. Confirmed
  missed once already: two `table`-display cards on account 89060 got the
  identical center-align/date-cleanup/row-highlight treatment by hand, and
  it was first scored `fixable: false` before the user caught it — see
  `references/project-improvements.md`, 2026-09-18.

Record which of these applied directly on the card's own element inside
`requirement_confirmed`'s `cards` array, via a `root_cause` object (see
"Log schema" below) — `fixable`, `fix_type`, and what was actually done
(or the `references/project-improvements.md` entry it became). A change
scored and left with `fixable: false, fix_type: "none_cosmetic"` needs no
further action. Anything else needs the fix actually applied — in the same
turn, same as any other confirmed answer this project writes back
immediately — not deferred to a future on-demand project-improvement
review. A recurring *pattern* across several already-`fixable: false`
cosmetic entries is still fair game for that on-demand review to surface
later; this per-card check doesn't replace it, it catches the cases that
shouldn't wait that long.

## Pending-entry check (Step 0 hook)

Early in any session, after configuration is verified (CLAUDE.md Step 0),
scan `logs/performance-tracking.jsonl` for `requirement_pending` entries
with no `requirement_confirmed` entry sharing their `tracking_id`. If any
exist, tell the user plainly which account(s) and how many are waiting
(e.g. "Account 92840 has 4 unconfirmed performance-tracking entries from
2026-09-15 — want to confirm them now, or later?") and proceed based on
their answer. This is the actual fix for a session ending before
confirmation happens — don't rely on the user remembering to bring it up
unprompted.

## Log schema

All entries share `timestamp` (TZ="Asia/Kolkata", same convention as
`logs/history.jsonl`), `account`, `tracking_id`, and `type`. A `chart` unit
may carry a `supersedes` array (see "Superseding an older entry" below).

**`requirement_pending`** (chart unit — v2.0, one entry per resolution
batch, `cards` holds one element per resulting card):
```json
{"timestamp": "2026-09-18T11:02:00+05:30", "type": "requirement_pending", "tracking_id": "92840-20260918T110200-client-conversion-metrics", "account": "92840", "unit_type": "chart", "requirement": "show placement rate and interview-to-offer rate by client", "source_type": "stated_ask", "rubric_version": "2.0", "matched_canonical_pattern": false, "entities_involved": 2, "new_discovery_required": false, "clarifying_questions_needed": 0, "comprehension_minutes": 6, "questions_asked_total": 1, "iterations_before_build": 0, "cards": [{"card_id": 75990, "name": "Placement Rate by Client", "build_elements_snapshot": {"joins": 1, "summarize_steps": 2, "custom_expressions": 1, "native_sql": false, "is_model": false, "filters": 1, "formatted_columns": 1, "stage_conversion_technique": false, "drilldowns_wired": 1}, "build_minutes_snapshot": 4.08, "dataset_query_snapshot": {"...": "..."}, "visualization_settings_snapshot": {"...": "..."}, "click_behavior_snapshot": {"...": "..."}}, {"card_id": 75991, "name": "Interview-to-Offer Rate by Client", "build_elements_snapshot": {"joins": 1, "summarize_steps": 2, "custom_expressions": 1, "native_sql": false, "is_model": false, "filters": 1, "formatted_columns": 1, "stage_conversion_technique": false, "drilldowns_wired": 0}, "build_minutes_snapshot": 2.28, "dataset_query_snapshot": {"...": "..."}, "visualization_settings_snapshot": {"...": "..."}, "click_behavior_snapshot": null}], "build_minutes_snapshot_total": 6.36, "status": "pending"}
```

**`requirement_confirmed`** (same `tracking_id` as its pending entry; each
element of `cards` carries its own diff result **and its own `root_cause`**
for anything `built_modified`, the top level sums the numeric fields):
```json
{"timestamp": "2026-09-22T09:40:00+05:30", "type": "requirement_confirmed", "tracking_id": "92840-20260918T110200-client-conversion-metrics", "account": "92840", "unit_type": "chart", "outcome": "built_modified", "rubric_version": "2.0", "cards": [{"card_id": 75990, "name": "Placement Rate by Client", "outcome": "built_modified", "build_elements_final": {"joins": 1, "summarize_steps": 2, "custom_expressions": 1, "filters": 2, "formatted_columns": 1, "drilldowns_wired": 1}, "build_minutes_final": 4.44, "build_minutes_retained": 3.36, "what_changed_summary": "user added a client-status filter and adjusted the currency format", "root_cause": {"fixable": true, "fix_type": "reference_update", "fix_applied": "the client-status filter reflects a segment definition ('active client' = status in Active/Renewing) that was never asked about up front -- added to references/metric-glossary.md Account 92840 section so the next client-facing card defaults to it instead of a plain client list"}}, {"card_id": 75991, "name": "Interview-to-Offer Rate by Client", "outcome": "built_clean", "build_elements_final": {"joins": 1, "summarize_steps": 2, "custom_expressions": 1, "filters": 1, "formatted_columns": 1, "drilldowns_wired": 0}, "build_minutes_final": 2.28, "build_minutes_retained": 2.28, "what_changed_summary": "no changes"}], "build_minutes_final_total": 6.72, "build_minutes_retained_total": 5.64, "pct_claude_build": 0.84, "pct_human_build": 0.16, "comprehension_minutes_credited": 6, "build_minutes_saved": 5.64, "total_time_saved_minutes": 11.64, "manual_fix_minutes_reported": 15, "status": "confirmed"}
```
A card with no `root_cause` field is `built_clean` (nothing to root-cause).
A `built_modified` card's `root_cause.fixable: false` still carries the
object — e.g. `{"fixable": false, "fix_type": "none_cosmetic", "fix_applied": null}`
— so "was this checked" stays visible in the log, not just "was it fixed."

**`requirement_outcome`** (infeasible or extra-addition — single entry, no
pending phase):
```json
{"timestamp": "2026-09-18T11:10:00+05:30", "type": "requirement_outcome", "tracking_id": "92840-20260918T111000-at-risk-deals", "account": "92840", "unit_type": "chart", "outcome": "infeasible_data", "requirement": "flag at-risk deals", "reason": "definition rests on a 'Lost' stage this account has zero deals in, confirmed with user", "comprehension_minutes_credited": 5, "build_minutes_saved": 0, "total_time_saved_minutes": 5, "status": "confirmed"}
```
```json
{"timestamp": "2026-09-22T09:45:00+05:30", "type": "requirement_outcome", "tracking_id": "92840-20260922T094500-recruiter-load-balance", "account": "92840", "unit_type": "chart", "outcome": "infeasible_tool_capability", "requirement": "auto-balance recommended recruiter workload", "reason": "requires an optimization/assignment computation no combination of MBQL, native SQL, and this project's documented patterns can express", "total_time_saved_minutes": 0, "status": "confirmed", "project_improvement_logged": true}
```
```json
{"timestamp": "2026-09-22T09:50:00+05:30", "type": "requirement_outcome", "tracking_id": "92840-20260922T095000-extra-1", "account": "92840", "unit_type": "extra_manual_addition", "outcome": "extra_manual_addition", "classification": "missed_original_requirement", "description": "user built a 'Stale Jobs' table that covered part of the original 'pipeline health' ask this project never attempted or flagged", "total_time_saved_minutes": 0, "status": "confirmed", "project_improvement_logged": true}
```

`unit_type: "dashboard_assembly"` / `"pivot_drilldown_dashboard"` /
`"documentation"` entries stay single-unit (no `cards` array, unaffected by
the v2.0 batch grouping) and follow the pre-v2.0 `requirement_pending` /
`requirement_confirmed` shape directly: `dashboard_id`/`document_id` in
place of `card_id`/`cards`, and the relevant snapshot (`dashcards_snapshot`,
`document_body_snapshot`) in place of `dataset_query_snapshot`. Their
weights stay at v1.0 numbers even under `rubric_version: "2.0"` — see
`references/effort-estimation-rubric.md`'s build-time factors.

## Superseding an older entry

**This log is append-only — an old entry is never edited or deleted, even
when it's re-scored under a newer rubric version.** When a `chart` unit's
underlying cards get re-scored under a newer model (e.g. account 89060's 15
v1.0 per-card entries collapsed into v2.0 per-batch entries, 2026-09-18, at
the user's explicit request), append the new `requirement_confirmed`
entries with a `supersedes` array listing every old `tracking_id` they
replace:

```json
{"...": "...", "tracking_id": "89060-20260918T190500-hiring-activity-metrics", "supersedes": ["89060-20260918T080520-phone-screens", "89060-20260918T080520-resume-submits", "89060-20260918T080520-client-interviews-completed", "89060-20260918T080520-offers-extended", "89060-20260918T080520-offers-accepts", "89060-20260918T080520-offer-declines", "89060-20260918T080520-offers-rescinded", "89060-20260918T080520-post-accept-declines"], "...": "..."}
```

Any `tracking_id` appearing in another entry's `supersedes` list is excluded
from totals/aggregation — its replacement entry is the authoritative one for
that work. The superseded entries themselves stay in the file exactly as
written, readable as "what that version thought this was worth," the same
append-only spirit as `references/metric-glossary.md`'s `Superseded` notes.
Don't supersede an entry casually — only when the user explicitly asks for
a re-score under a newer model, the same bar as retroactively touching any
other git-committed record in this project.
