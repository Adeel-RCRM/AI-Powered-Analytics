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

## Requirement-unit outcomes

Every requirement-unit from Requirements Intake's numbered recommendation
list gets exactly one outcome, and every outcome gets logged — **nothing is
dropped from this record because the result wasn't a clean success.**

- **`built_clean`** — the card/dashboard element shipped exactly as built,
  with no changes. Full comprehension credit and full build credit.
- **`built_modified`** — the user changed something after it was built.
  Credit is scored from a structural diff (see "Diffing" below), granular,
  never all-or-nothing: a card the user only tweaked one filter on keeps
  most of its build credit; one rebuilt from scratch keeps none. Full
  comprehension credit either way — figuring out what to build is a
  separate cost from getting the build exactly right.
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

**For `built_clean`/`built_modified` candidates** (anything that actually
gets a card created): `prompts/chart-generation.md` step 10 appends a
`requirement_pending` entry the moment the card is verified — see "Log
schema" below. This captures everything knowable at build time: the
comprehension score, a snapshot of the card's exact
`dataset_query`/`visualization_settings`/`click_behavior`, and the
question/iteration counts for this specific requirement-unit. No user
interaction needed for this step — it's bookkeeping, the same as the
existing `chart_created` history-log entry right next to it.

Dashboard assembly, a pivot table's dedicated drill-down dashboard, and a
companion documentation Document are each their own unit with their own
`requirement_pending` entry (`unit_type` values `dashboard_assembly`,
`pivot_drilldown_dashboard`, `documentation` respectively) — logged at the
point each is verified in `prompts/requirements-intake.md`'s "Assemble the
dashboard(s)" / "Add the documentation Document" steps. Their snapshots are
the dashboard's `dashcards`/`tabs`/`parameters`, or the Document's body,
respectively, in place of a card's `dataset_query`.

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
   `requirement_confirmed` entry (same `tracking_id`), re-fetch the current
   object (`mb card get <id> --full --json`, `mb dashboard get <id>
   --full --json`, or `mb document get <id> --full --json` per its
   `unit_type`) and diff it against the entry's snapshot, per "Diffing"
   below. This determines `built_clean` vs. `built_modified` and the
   retained/changed element sets on its own.
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
   `build_minutes_final`, `build_minutes_retained`, `pct_claude_build`, and
   `total_time_saved_minutes` per `references/effort-estimation-rubric.md`,
   and append a `requirement_confirmed` entry with the same `tracking_id`.
   Log `extra_manual_addition` entries per the user's answers in step 2.
4. **Feed `references/project-improvements.md`** for any
   `infeasible_tool_capability` or missed-original-requirement
   `extra_manual_addition` surfaced in this pass, per "Feeding back into
   the project" below.

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

A `built_modified` outcome does **not** automatically feed
`references/project-improvements.md` — normal, expected polish is not the
same as a capability gap. If a *pattern* of similar manual fixes recurs
across several confirmed entries, that's a finding for a future on-demand
project-improvement review to surface by actually reading this log, not
something logged reflexively at confirmation time.

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
`logs/history.jsonl`), `account`, `tracking_id`, and `type`.

**`requirement_pending`** (chart unit):
```json
{"timestamp": "2026-09-18T11:02:00+05:30", "type": "requirement_pending", "tracking_id": "92840-20260918T110200-placement-rate-by-client", "account": "92840", "unit_type": "chart", "requirement": "show placement rate by client", "source_type": "stated_ask", "rubric_version": "1.0", "matched_canonical_pattern": false, "entities_involved": 2, "new_discovery_required": false, "clarifying_questions_needed": 0, "comprehension_minutes": 6, "questions_asked_total": 1, "iterations_before_build": 0, "card_id": 75990, "build_elements_snapshot": {"joins": 1, "summarize_steps": 2, "custom_expressions": 1, "native_sql": false, "is_model": false, "filters": 1, "formatted_columns": 1, "stage_conversion_technique": false, "drilldowns_wired": 1}, "build_minutes_snapshot": 34, "dataset_query_snapshot": {"...": "..."}, "visualization_settings_snapshot": {"...": "..."}, "click_behavior_snapshot": {"...": "..."}, "status": "pending"}
```

**`requirement_confirmed`** (same `tracking_id` as its pending entry):
```json
{"timestamp": "2026-09-22T09:40:00+05:30", "type": "requirement_confirmed", "tracking_id": "92840-20260918T110200-placement-rate-by-client", "account": "92840", "unit_type": "chart", "outcome": "built_modified", "rubric_version": "1.0", "build_elements_final": {"joins": 1, "summarize_steps": 2, "custom_expressions": 1, "filters": 2, "formatted_columns": 1, "drilldowns_wired": 1}, "build_minutes_final": 37, "build_minutes_retained": 28, "pct_claude_build": 0.76, "pct_human_build": 0.24, "comprehension_minutes_credited": 6, "build_minutes_saved": 28, "total_time_saved_minutes": 34, "manual_fix_minutes_reported": 15, "what_changed_summary": "user added a client-status filter and adjusted the currency format", "status": "confirmed"}
```

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
`"documentation"` entries follow the same `requirement_pending` /
`requirement_confirmed` shape, with `dashboard_id`/`document_id` in place
of `card_id` and the relevant snapshot (`dashcards_snapshot`,
`document_body_snapshot`) in place of `dataset_query_snapshot`.
