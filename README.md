# Theseus Control Plane — Hackathon

**From raw data to an evidence-backed organization of agents, under human control.**

AIE Code Hackathon · November 7, 2026 · San Francisco.

This public workspace contains the hackathon prototype, a verified 53,431-record RecPlace raw import to MongoDB Atlas, a one-goal evidence and SubQ review, the human-facing Organization Memory and decision screens, and a hosted Fetch.ai Deputy with authenticated live read access. [Judges: start here](JUDGES.md). For current readiness and limits, see the [English report](reports/CURRENT-STATUS-2026-11-07.en.html).

Agent entry points: [Muse](docs/agents/muse/START-HERE.md), [Argon](docs/agents/argon/START-HERE.md). Start with orientation; the owner opens implementation stages. Read [RecPlace sources](docs/RECPLACE-SOURCES.md) and the shared [ingestion contract](database/INGESTION-CONTRACT.md).

The latest narrative and scope proposal is [FRAME.md](docs/FRAME.md): a human-directed organization that rebuilds its tools and proves each improvement, with a Deputy CEO reachable through Fetch.ai.

## Four working areas

| Folder | Responsibility | Start here |
|---|---|---|
| `app/` | Application code, extraction, review and agent workflows | [Application](app/README.md) |
| `database/` | Data model, indexes, queries and synthetic fixtures | [Database](database/README.md) |
| `docs/` | Architecture, decisions, implementation plan and work log | [Plan](docs/PLAN.md) |
| `reports/` | Outcomes, concept, demo scripts, submission materials and progress dashboard | [Delivery protocol](reports/README.md) |

## The proposed process

RecPlace primary records → verified unchanged copy in MongoDB → Meta extracts new candidate facts with source evidence → SubQ helps identify conflicting claims → a human resolves or preserves uncertainty → compile bounded agents → add an external Fetch.ai agent through an explicit intent and approval process. New material later repeats this process incrementally, preserving prior versions.

SubQ's exact verification method is an open design decision. Model agreement alone is not proof. Agents must inherit explicit goals, rules and authority; proposed changes remain reviewable.

## Progress dashboard

The local [dashboard](reports/STATUS.html) is generated from task and event records with `python3 reports/build.py`. The coordinator owns those records. Completed outcomes require evidence; sponsor account setup does not count as product completion.

## Start building

1. Read your agent entry point, [plan](docs/PLAN.md), [ingestion contract](database/INGESTION-CONTRACT.md) and [open decisions](docs/DECISIONS.md).
2. Argon prepares schema/adapter and the verified raw import; Muse prepares extraction in parallel on fixtures, then runs the authorized real pilot from MongoDB.
3. Attach reproducible, sanitized evidence before marking an outcome `done`.

No private source data, credentials, provider account identifiers or client traces belong in this repository. Use `database/private/` for ignored local inputs and `.env` for local credentials. See [data handling](docs/DATA-HANDLING.md).

The application runs locally for the demo; public hosting has not been configured. Private RecPlace data and credentials remain outside Git. No open-source license has been selected yet.
