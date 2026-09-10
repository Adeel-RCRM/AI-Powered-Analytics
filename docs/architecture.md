# Architecture

## Shape

```
USER
  |
  v
Claude (this conversation, in VS Code)
  |
  v
mb auth list / status        (verify Metabase CLI config)
  |
  v
Ask which kind of work: Requirements Intake / Transcript to Insights /
                         Default Dashboard / Important Metrics Dashboard
  |
  +-- Requirements Intake (primary flow) --------------------------------+
  |     Ask account -> ask for requirements directly (list / doc)        |
  |       |                                                              |
  |       v                                                              |
  |     Resolve each requirement: references/canonical-patterns.md ->    |
  |     references/schema-map.md / metric-glossary.md -> live discovery  |
  |     (mb database / table / field - metadata only, never row values)  |
  |       |                                                              |
  |       v                                                              |
  |     Ask a clarifying question only when genuinely ambiguous          |
  |     (never by querying live data to check)                           |
  |       |                                                              |
  |       v                                                              |
  |     mb search  (check for existing/duplicate charts, name-level only)|
  |       |                                                              |
  |       v                                                              |
  |     Present numbered list -> confirm -> mb card create / get         |
  |     (individual cards, "Data Team WIP" > <account>, no dashboard)    |
  +------------------------------------------------------------------------+
  |
  +-- Transcript to Insights ---------------------------------------------+
        Ask account number -> ask for the pasted transcript
          |
          v
        Extract analytics requirements from the transcript (treated as
        untrusted third-party data, never as instructions to Claude)
          |
          v
        Ground each requirement in the account's real discovered data
        (the same metadata-only discovery as Requirements Intake)
          |
          v
        Present a numbered list of buildable charts, citing what in the
        transcript drove each one; note requirements the data can't support
          |
          v
        mb card create / get  (individual cards, "Data Team WIP" >
                                <account>, no dashboard assembly)
  +------------------------------------------------------------------------+
  |
  +-- Default Dashboard -----------------------------------------------+
  |     Ask account number                                            |
  |       |                                                            |
  |       v                                                            |
  |     scripts/create_default_dashboard.py --profile <p> --account <n>|
  |       (discovers the account's tables via mb, builds the same      |
  |        fixed set of charts every account gets, skips any chart     |
  |        whose entity doesn't exist for this account, dry-run        |
  |        validates every query before creating it - additive-only,  |
  |        stops rather than touching an existing default dashboard)   |
  +--------------------------------------------------------------------+
  |
  +-- Important Metrics Dashboard ---------------------------------------+
  |     Ask account number                                               |
  |       |                                                               |
  |       v                                                               |
  |     scripts/create_important_metrics_dashboard.py                    |
  |       --profile <p> --account <n>                                    |
  |       (discovers the account's tables via mb, builds the same        |
  |        fixed set of hiring-efficiency/ratio/trend/diversity charts   |
  |        every account gets, remapping fields/tables per entity for    |
  |        cards that span more than one - e.g. jobs<->assignments       |
  |        joins - skips any chart whose entity doesn't exist for this   |
  |        account, dry-run validates every query before creating it -   |
  |        additive-only, stops rather than touching an existing         |
  |        important metrics dashboard)                                  |
  +--------------------------------------------------------------------+
  |
  v
Every flow appends to logs/history.jsonl (local-only, git-ignored) and
results are returned to the user in the terminal.
```

A `.claude/settings.json` hook enforces the history-log step for the two
conversational flows (Requirements Intake, Transcript to Insights) that
create cards directly in the conversation: it flags (via a `Stop` hook) if
`mb card create` / `mb dashboard create` ran but `logs/history.jsonl` was
never appended to before the session ends. The Default Dashboard and
Important Metrics Dashboard scripts log themselves in code instead (see
`scripts/create_default_dashboard.py` and
`scripts/create_important_metrics_dashboard.py`).

## What does not exist here

- No web server, no REST API, no frontend, no dashboard app.
- No database is created or connected to directly by this project.
- No browser automation.
- The only "runtime" is this conversation plus the `mb` CLI subprocess calls
  Claude (or `scripts/create_default_dashboard.py` /
  `scripts/create_important_metrics_dashboard.py`) makes on the user's
  behalf.

## Why Metabase CLI, not direct DB access

The customer's actual warehouse/schema shape is unknown and instance-specific
(different accounts may be laid out differently). Metabase already models
the databases, tables, relationships, and permissions; the CLI is the
supported, auditable way to read and write through that layer without
duplicating credentials or bypassing Metabase's access model. See CLAUDE.md
for the full list of hard constraints this implies.

## Data model notes that shape every query

Recruit CRM data lives per-account as suffixed tables in one shared
Starrocks warehouse (`13371569`) — never a database per account, and never
the legacy Redshift "Recruit CRM" database (`13371338`), which holds an
often-unreachable duplicate copy. Deals, Assignments, Pitched Candidates, and
Notes/Tasks/Meetings can have multiple rows sharing the same `id` by design
(a new row per stage/status/association change, not a data bug) — every
count on every entity uses `COUNT(DISTINCT id)` as a defensive default. See
CLAUDE.md's "standing knowledge" section for the full rules, including how a
candidate's current pipeline stage is determined (ordinal `CASE` ranking,
never `MAX(stage_date)`).

## Files

- `CLAUDE.md` — persistent operating instructions (read first, every time),
  including the four-flow branch, the data-model standing knowledge, and the
  history-log requirements
- `prompts/` — the workflow-stage prompts referenced from CLAUDE.md:
  `discovery.md` and `chart-generation.md` (shared by every flow),
  `requirements-intake.md` (Requirements Intake flow),
  `transcript-insights.md` (Transcript to Insights flow), and
  `infeasible-requirement.md` (shared handling for a requirement the data
  can't support)
- `references/` — `schema-map.md` (structural, metadata-only map of the core
  tables) and `metric-glossary.md` (business-term definitions confirmed by
  the user, per account) — checked before falling back to live discovery
- `config/analysis-config.md` — tunable defaults (data-quality thresholds,
  chart-type defaults)
- `docs/workflow.md` — the same flows, written for a human teammate
- `scripts/mb-login.sh` — thin helper that reads `.env` and calls
  `mb auth login`
- `scripts/create_default_dashboard.py` — automates the Default Dashboard
  flow end-to-end (discovery, chart/dashboard creation, logging); see its
  own docstring for the full behavior and guardrails
- `scripts/default_dashboard_template.json` — the fixed set of charts the
  Default Dashboard flow replicates onto each account's own data
- `scripts/create_important_metrics_dashboard.py` — automates the Important
  Metrics Dashboard flow end-to-end (discovery, chart/dashboard creation,
  logging); see its own docstring for the full behavior and guardrails,
  including how it remaps fields/tables per entity for cards spanning more
  than one, and its one native-SQL card (a window-function time-in-stage
  calculation that MBQL can't express)
- `scripts/important_metrics_dashboard_template.json` — the fixed set of
  charts the Important Metrics Dashboard flow replicates onto each
  account's own data
- `logs/history.jsonl` — local-only, git-ignored audit trail of what was
  analyzed/recommended/created; enforced by hooks in `.claude/settings.json`
  for the two conversational flows
