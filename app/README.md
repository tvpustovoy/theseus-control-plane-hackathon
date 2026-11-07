# Application code

Planned modules live here; no provider integration is implemented yet.

| Module | Input → output | Constraint |
|---|---|---|
| Ingestion | Authorized source → immutable source record | Record origin, hash, time, consent and sensitivity |
| Meta extraction | Source → candidate claims and proposed structure | Preserve exact evidence spans; do not auto-accept |
| Model assembly | Reviewed claims → versioned entities and relationships | Keep conflicting claims and provenance |
| SubQ review | Explicit claim pair + source evidence → review signal | Method/model/output contract to be validated |
| Human review | Pending proposal → signed decision | Capture who, what, why and applicable version |
| Agent compiler | Goals + model + authority → proposed agent specification | Default-deny capabilities; approval before activation |
| Fetch.ai adapter | External agent intent → proposed role and structure | External agent has no automatic write authority |
| Governance view | Goals, rules, culture hypotheses, evolution → human decisions | Show propagation and behavioral evidence separately |

First vertical slice: one synthetic source, cited Meta claims, MongoDB persistence and a human review decision. Choose the application stack before adding dependencies. Database contracts are in `../database/SCHEMA.md`.
