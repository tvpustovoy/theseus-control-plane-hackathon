# Judges' guide — Theseus Control Plane

**Start here:** [English status report](reports/CURRENT-STATUS-2026-11-07.en.html) · [three-minute live demo script](reports/2-scenarios/LIVE-DEMO-3MIN.md) · [application](app/README.md).

## What to look for

Theseus is a human control plane for an agent organization. The hackathon demo follows **one goal**: grow sales while protecting value and margin. It makes the linked discount rules, observed practice, uncertainty and proposed changes visible to the owner. The owner decides; agents investigate and propose.

1. **Organization Memory:** Open `http://127.0.0.1:8765/#MEMORY` during the live demo. It separates 53,431 verified raw RecPlace rows and matching source records in MongoDB Atlas from Muse's partial local extraction: 3,351 candidate claims from 994 source IDs within a 7,697 candidate-hash set. Browse source metadata and ask a grounded question. The interface abstains when evidence is missing.
2. **Human decision:** Follow the Deputy CEO's native **Review direction** card to `#S01`. The owner reviews and commits a versioned direction and discount principle. Explore `#S02` culture and `#S03` alignment with source references and actual SubQ results.
3. **Change and outcome:** Continue through `#S04`–`#S06`. The comparison is explicitly a **simulation** on synthetic leads, not observed post-deployment business lift.

## Where the evidence and code live

| Area | Open |
|---|---|
| Raw import contract and verification | [database/INGESTION-CONTRACT.md](database/INGESTION-CONTRACT.md), [Argon status](docs/status/Argon.Hackathon.md) |
| Source-linked extraction and culture | [Muse handoff](database/fixtures/evidence-handoff.json), [culture and rules brief](database/fixtures/culture-rules-brief.json), [Muse status](docs/status/Muse.Hackathon.md) |
| Five real SubQ discount comparisons | [review packet](database/fixtures/review-packet-subq-discount.json); zero proven contradictions |
| Web control plane and bounded Q&A | [app/ui](app/ui/), [Organization Memory API](app/api/organization_memory.py), [its tests](app/api/test_organization_memory.py) |
| Hosted Fetch.ai Deputy and authenticated read bridge | [Agentverse implementation](app/deputy/agentverse/), [live acceptance](app/deputy/agentverse/MONGO-LIVE-VERIFICATION.md), [freshness screenshot](reports/evidence/deputy-live-mongo-freshness.png), [Commit card screenshot](reports/evidence/deputy-live-commit-card.png) |
| Reproducible outcome simulation | [simulation code](app/runtime/simulation.py), [method and limits](docs/status/Argon.Hackathon.md) |
| How work progressed | [work log](docs/WORKLOG.md), [task board](docs/WORKBOARD.md), [decisions](docs/DECISIONS.md) |

## Reproduce and interpret

From the repository root, run `python3 -m unittest discover -s app -p 'test_*.py' -q`. The last live application checkpoint reported **37/37 passing tests**. The local server command is `database/private/.venv/bin/python -m app.api.server --host 127.0.0.1 --port 8765`; it requires private Atlas credentials and imported data, which are intentionally absent from this public repository. The hosted Deputy additionally requires the local authenticated bridge and tunnel described in its [operator runbook](app/deputy/agentverse/RUN-LIVE-MEMORY.md).

**Evidence boundaries:** the Atlas corpus is a historical snapshot; Muse's 3,351 claims are local candidates, not persisted Atlas claims or verified frequencies. CRM discount outcomes and revenue semantics are unverified. SubQ outputs are review signals. The Deputy searches the allowed raw records but cannot approve or execute a policy change. Source identifiers are available; public source URLs are not yet published. The [full report](reports/CURRENT-STATUS-2026-11-07.md) distinguishes these observations from inference and simulation.
