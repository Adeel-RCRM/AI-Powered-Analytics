# Metric Glossary

Business-term definitions, confirmed with the user, mapped to the exact
column/filter that implements each one — kept **per account**. A mapping
confirmed for one account must never be assumed to hold for another (per
CLAUDE.md "Data discovery" and "Term/value mismatches" below); this file is
organized by account precisely so that rule is enforced by its structure,
not left to convention alone. Structural/definitional only — no customer
data.

**No answer here is ever obtained by querying live data, or by inferring it
from existing content.** Every value list, stage order, and term definition
below comes only from what the user confirms directly — never from
`mb field values`, `mb field summary`, `mb query` run to sample/check what's
actually in a column, **and never from reverse-engineering an existing
card's saved query** (a `CASE` expression's stage ordering, a filter's
literal values, etc. — see CLAUDE.md "Avoiding duplicate charts" and
`prompts/discovery.md` section 5). An old card that already encodes a
plausible-looking answer is still not a substitute for asking. If a term is
still unconfirmed when a chart needs it, the flow asks the user in-session,
with no priors, rather than checking the data — or existing content — itself
(see `prompts/discovery.md` section 4).

**Every confirmed answer gets written here immediately — in the same turn
it's confirmed, before moving on to the next question or building the
chart.** Holding a confirmed answer in conversation context to write back
later (or never) is exactly how "ask once per account" quietly turns into
"ask every time" — see `prompts/discovery.md` section 4, `prompts/
chart-generation.md`'s currency step, and `prompts/requirements-intake.md`'s
"When to actually ask a question".

## How this file is organized

- **Open questions (template)** — the standing list of business terms that
  typically need a confirmed answer before they can be used in a chart,
  for *any* account. This list is not itself account-specific; it's what to
  walk through the first time one of these terms comes up for a given
  account, and it stays here even after some accounts have answered it.
- **Account sections** (`## Account <number>`) — one per account this
  project has actually confirmed answers for, holding that account's own
  confirmed term mappings and any other per-account facts (hiring-stage
  order, currency, etc.). Before resolving a business term for account X,
  check X's own section first; never reuse another account's section, and
  never create a new account's section by copying an existing one's answers
  forward.
- **Unattributed** — mappings recorded before this file was organized by
  account, with no account number recoverable from how they were written.
  They are not usable for any specific account as-is — see that section.

## Open questions (template)

1. **"Active candidate"** — which column/value defines this?
   `candidates.employment_status`? A recent-activity window on
   `last_communication_on`? Something else? (Note: exact `employment_status`
   values are account-specific — confirm fresh per account.)

2. **"Placed" / "Closed" (a hire happened)** — is this
   `assign_job_candidate.hiring_stage` reaching a specific value (e.g.
   "Placed")? If so, what's this account's exact stage name, and where does
   it fall in the funnel order (needed for the stage-ordinal `CASE` ranking
   per CLAUDE.md)? Since `hiring_stage_date` timestamps can be seconds apart,
   the stage order must come from the user, not be inferred.

3. **"Call outcome" categories** — `call_logs.call_type_label` looks like
   the candidate column, but what are the actual outcome categories this
   account uses (e.g. Connected / No Answer / Voicemail), and does
   "duration > 1 minute" / "> 2 minutes" (seen in past requirements) mean
   `duration_in_seconds` thresholds at 60 / 120?

4. **"Assigned"** (a candidate assigned to a job) — does this mean a row
   simply exists in `assign_job_candidate` for that pair (any stage), or
   specifically reaching a named early stage (e.g. "Assigned" as a literal
   `hiring_stage` value)? `assign_job_candidate.assigned_by` also exists —
   is that relevant to the definition, or just metadata about who did it?

5. **"This month" / "recent"** — when a requirement doesn't specify a date
   column, which one resolves it by default? Candidates for "recent
   activity": `created_on`, `updated_on`, `last_communication_on` (candidates
   /contacts), `hiring_stage_date` (pipeline), `created_on`/`started_on`
   (calls). Likely different per entity — confirm per entity rather than
   one blanket rule.

6. **Funnel/hiring-stage values and order** — per CLAUDE.md, there is
   currently no numeric-order column, so both the **exact list** of stage
   names and their **funnel order** must come from the user directly,
   account by account — never from querying the field's live values. What
   is the complete list of this account's `hiring_stage` values, in real
   funnel order?

7. **Term/value mismatches** — when a requirement uses wording that doesn't
   exactly match a value already confirmed here or in the schema (e.g. a
   requirement says "Internal Review Required" but no confirmed stage list
   has that exact name), the fix is to ask the user which real value it maps
   to — never to query the field live to check what actually exists. Log the
   confirmed mapping under this account's own section once answered, so the
   same mismatch doesn't get re-asked next time.

8. **Currency** — per CLAUDE.md "Value formatting", monetary fields
   (`deal_value`, `budget_allocated`, `cost_in_currency`, salary/package
   fields, etc.) must be chart-formatted with the right currency symbol, and
   that currency is never assumed. Which ISO 4217 currency code applies
   (e.g. USD, EUR, GBP, INR) for this account?

## Account sections

No account has a fully confirmed set of answers yet. Add a `## Account
<number>` section here the first time a term is confirmed for that account,
in this shape:

```markdown
## Account 662

**Confirmed term mappings:**
- "Open positions" → `job_status_label = 'Open'`

**Hiring-stage order:** (fill in once confirmed, per "Open questions" #6)

**Currency:** (fill in once confirmed, per "Open questions" #8)
```

## Account 92840

**Confirmed term mappings:**
- "Jobs created" (team-member activity) → `jobs_92840.owner_id`/`owner_name`, `created_on` — full credit to job owner only, never split (client's own rule: job creation credit is always one person).
- "Sent to client" / "interviews" / "offers" / "placements" (team-member activity credit) → counted from `assign_job_candidate_92840` rows reaching the relevant `hiring_stage` value; each event's credit is split between `job_owner_id`/`job_owner_name` and `candidate_owner_id`/`candidate_owner_name`: **full credit to one person if job owner = candidate owner on that row, otherwise 0.5 credit each** (client's explicit rule, confirmed 2026-09-10 call transcript + 2026-09-17 session).
- "Billing" / deal revenue credit (team-member activity + leaderboard) → same job-owner/candidate-owner 50/50-or-full split, but derived via `deals_92840.join_for_jobs_table → jobs_92840.owner` (job side) and `deals_92840.join_for_candidates_table → candidates_92840.owner` (candidate side) — **only for deals that actually have a job link**. Deals with no job link (60 of 130, 46%, confirmed 2026-09-17) are **excluded from the split-credit/leaderboard view entirely** — user's explicit choice — and surface only in the separate deals-not-linked-to-a-job data-accuracy report.
- `deals_92840.deal_value` is **repeated in full on every duplicate-id collaborator row**, not split (confirmed live 2026-09-17 per CLAUDE.md's Deals verification step) — always dedupe to one row per `id` (e.g. `MIN(deal_value)` grouped by `id`) before summing.
- Old "Owner Activity" dashboard cards ("Activity By Job Owner", "Activity By Candidate Owner") → kept as-is; new combined split-credit cards are added alongside them, not a replacement (user's explicit choice, 2026-09-17).

**Hiring-stage values (confirmed by user, 2026-09-17):** Assigned, Candidate Canceled Interview, Candidate Not Interested, Candidate Passed Post Interview, Client Passed Post Interview, Client Passed Pre Interview, Completed Interview, I rejected not a fit, Interview Scheduled, Interviewed Not Offered, MIA after submitting, Off Market Candidate took Different Job, Offered, On Hold, Placed, Reverse Market Created Opening, Sent to Client, Terminated, Turndown. **Funnel order not yet confirmed** (list given alphabetically, not by funnel progression) — ask separately if a future chart needs the ordinal current-stage `CASE` ranking (none of account 92840's charts built so far need it — each uses a single named stage as a direct filter, not a "furthest stage reached" calculation).
- "Interviews" (team-member activity metric) → `hiring_stage = 'Interview Scheduled'` only — user explicitly confirmed not to also count "Completed Interview" separately.
- "Sent to client" → `hiring_stage = 'Sent to Client'`.
- "Offers" → `hiring_stage = 'Offered'`.
- "Placements" → `hiring_stage = 'Placed'`.

**Deal-stage values (confirmed by user, 2026-09-17):** Lost, Pending Start, Started Hasn't Paid, Won — exactly 4 values, given in this order. "Won" is the final/paid stage (money received) — resolves the transcript's informal "Won vs. Paid" ambiguity; there is no separate literal "Paid" value.

**Currency:** USD (confirmed 2026-09-17).

**Revenue-credited time axis (confirmed 2026-09-17):** when breaking down "Revenue Credited by Team Member" by week/month/year, use `deals_92840.close_date` (revenue recognized when the deal closed/won) — not `created_on` (deal-record-creation date).

## Account 89060

**Confirmed term mappings (Cleveland Clinic dashboard, confirmed 2026-09-18):**
- "Job Owner" (client's stated attribution field for all dashboard metrics) → `assign_job_candidate_89060.job_owner_name`/`job_owner_id` for hiring-stage-based metrics (field exists and is otherwise unused by this account's other dashboards). **Does not exist as a joinable concept on `call_logs_89060` or `text_messages_89060`** (no job-owner field, no FK to jobs on either table) — for metrics built on those two tables (Phone Screens, Cold Calls, Texts), the client confirmed (2026-09-18, in-session) to instead hardcode the filter to the 3 named team members by exact name (`team_member IN ('Gabrielle Weisend','Jimi Silverlain','Nicholas Gonzales')`) rather than attempt a Job Owner join. (Source: user-confirmed in chat; Confirmed: 2026-09-18; Status: asserted)
- Team scoping mechanism → hardcoded `team_member IN ('Gabrielle Weisend','Jimi Silverlain','Nicholas Gonzales')`, **not** the `teams_89060.teams = 'Cleveland Clinic'` tag, even though Gabrielle Weisend already carries that tag — user explicitly chose the hardcoded-names approach over the team-tag approach when asked. (Source: user-confirmed in chat; Confirmed: 2026-09-18; Status: asserted)
- "Cold Calls" (renamed from "Calls Made") → `call_logs_89060.call_type_label = 'Cold Call'` (verified live: 2,482 rows account-wide). Note: the raw `call_type` field has no "Cold Call" value at all (only "Incoming call"/"Missed call"/"Outgoing call") — the client's "call type 'Cold Call'" language refers to `call_type_label`, not `call_type`. (Source: user-stated in email + verified against live field values; Confirmed: 2026-09-18; Status: asserted)
- "Emails Sent" → `notes_89060.note_label = 'Email Sent'` (client said "note type 'emails sent'" — matches this account's existing `note_label` category used elsewhere on this account's other dashboards). Scoped by Job Owner via `notes_89060.job_owner_id` (no `job_owner_name` text field exists on this table — join numeric id to `teams_89060.id`, mirroring this account's existing `text_messages_89060`-to-Teams id-based join pattern). (Source: user-stated in email; Confirmed: 2026-09-18; Status: asserted)
- "Client Interviews Completed" (renamed from "HM Interviews") → `hiring_stage IN ('HM Interview Complete - Pending Feedback', 'Onsite Interview Completed - Pending Feedback', 'Interview Completed; Awaiting Feedback')`. The client's stated stage names used an en-dash and slightly different wording/casing than the account's real values — corrected to the account's actual literal strings after verifying against the live 38-value hiring_stage list. The third stage is a substitute for the client's stated "Final Interview Completed", which **does not exist** in this account's hiring_stage list at all — see next entry. (Source: user-stated in email, corrected + Confirmed: 2026-09-18; Status: asserted)
- "Final Interview Completed" (client's stated stage name, used for "Client Interviews Completed" and as the sole numerator of "Final Interviews to Accepts") → **no matching value exists** in this account's hiring_stage list (38 values checked live, 2026-09-18). User confirmed in-session to substitute `hiring_stage = 'Interview Completed; Awaiting Feedback'` instead. **Caveat: this stage has only 3 records account-wide** (well under this project's ~20-record data-quality threshold) — both cards depending on it will likely show thin/noisy numbers until volume grows or the client corrects which stage they actually mean. (Source: user-confirmed substitution in chat; Confirmed: 2026-09-18; Status: caveat — thin data, worth reconfirming with the client directly)
  - **Superseded for "Final Interviews to Accepts" only (2026-09-18):** during manual review, the user edited card 76242 (both its base filter and its "Interview Completed Count" aggregation) to use the client's literal `hiring_stage = 'Final Interview Completed'` directly instead of the substitute — then, after being told this makes the card return `[0, 0, null]` live (the stage still has zero matching rows), explicitly chose to keep it that way rather than revert. So for this one card only, the mapping is now `hiring_stage = 'Final Interview Completed'` (zero rows, by the user's own informed choice) — **not** the substitute above. "Client Interviews Completed" (card 76235) was untouched and still uses the substitute as its third IN-list value. (Source: user decision in chat; Confirmed: 2026-09-18; Status: caveat — card intentionally returns 0 until this stage exists or the client corrects which stage they mean)

**Users (Cleveland Clinic team, checked live against `teams_89060` 2026-09-18):** Gabrielle Weisend exists (id 157409, active, already tagged `teams = 'Cleveland Clinic'`). Jimi Silverlain and Nicholas Gonzales have **no matching Teams record** under those exact names — likely still being onboarded into Recruit CRM itself (outside this project's scope). Re-check before reusing the hardcoded-name filter above if this dashboard is revisited later — if they've since been added under a slightly different spelling, the hardcoded filter won't pick them up silently.

**Status update (2026-09-18, during drill-down build):** the risk flagged above has materialized — verified live (`mb card query` on all 14 report cards, no date restriction) that **none of the 3 hardcoded team-member names match any owner/attribution field** (`job_owner_name`, `call_from_name`, `owner_name`) on a single row of real data, even though the underlying tables have substantial real data (91K+ union rows, 5,636 real Resume-Submitted records, 2,486 real Cold Calls, etc.). **Every metric on this dashboard currently returns 0.** This is not a build defect — the dashboard and its drill-downs were built and verified correctly against the confirmed team-scoping definition above; the definition itself doesn't match this account's real attribution data. **User's decision (2026-09-18): treat the current build as complete as delivered — do not block or reopen this requirement over it.** Reconfirming the correct attribution field/values with the client is explicitly deferred to a future session, to be handled as its own new requirement, not a fix to this one. (Source: user decision in chat; Status: caveat — dashboard is fully built and wired but shows all zeros until the team-scoping definition is reconfirmed with the client)

**Hiring-stage order:** not yet confirmed (no chart built for this account so far has needed furthest-stage-reached ordinal ranking — every stage reference used is a direct point-in-time filter).

**Currency:** not yet confirmed — no monetary field appears on the Cleveland Clinic dashboard.

## Account 662

**Currency:** USD (confirmed via `scripts/create_default_dashboard.py --currency`, 2026-09-24).

## Unattributed (predates per-account structure — reconfirm before use)

These mappings were recorded before this file separated answers by account.
No account number is recoverable from how most of them were written, so
**they must not be assumed to apply to any specific account, including the
one a current session happens to be working on.** If a similar term comes
up for any account, ask the user fresh per "When to actually ask a
question" (`prompts/requirements-intake.md`) and record the confirmed
answer under that account's own section above — don't reuse one of these
entries as if it were already confirmed for that account.

- "Sent to the client" / "Send to the client" → `hiring_stage = 'Send to the client'` (exact literal, stage 7)
- "Internal Review Required" → `hiring_stage = 'Internal Review'` (stage 31) — wording doesn't match exactly, confirmed by user
- "Submitted - Not Yet Presented" → no matching stage; user said to ignore/drop this condition when it comes up
- "Open positions" → `job_status_label = 'Open'`
- "User who set the status" (on `assign_job_candidate_53181`, i.e. **account 53181** — the one entry here with a recoverable account number; move it to its own `## Account 53181` section once that account's other answers are confirmed) → `updated_by` (not `assigned_by`)
- "The manager" (in "positions not owned by the manager") → the candidate's owner field (`candidate_owner_name`); "not owned by the manager" = `job_owner_name <> candidate_owner_name` (position owner differs from the candidate's owner)

## How to answer

Reply inline, e.g.:

> 1. Active candidate = `employment_status` in ('Unemployed','Actively
>    Looking') OR `last_communication_on` within 90 days
> 2. Placed = hiring_stage = 'Placed', which is the last stage before
>    Rejected/Withdrawn in the funnel
> ...

Anything left unanswered stays an open question — `prompts/requirements-intake.md`
will still ask about it live the first time a requirement actually needs
that specific definition, per its "When to actually ask a question" rule
(never as a blanket upfront hedge).
