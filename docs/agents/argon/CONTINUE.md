# Argon.Hackathon · Durable Handoff & Checkpoint (`CONTINUE.md`)

ॐ हुं हनुमते नमः  
`om hum hanumate namah`

- **Updated at:** `2026-11-07T15:21:30-08:00 (America/Los_Angeles)`
- **Role / Identity:** `Argon.Hackathon` (`cid`: `9E0BE0F07C11F4628287FCF77B76F4485D92E0FDCD1BCA5183E9E3B7698F22B5`)
- **Write Area:** `database/` (except `database/fixtures/`), `app/model/`, `app/runtime/`, `app/control/`, `app/deputy/` (excluding reserved `app/deputy/agentverse/`), `app/ui/`, `app/api/`, `docs/status/Argon.Hackathon.md`, `docs/agents/argon/CONTINUE.md`.

## NOW
- Completed the full **Human-Facing Interface Review redesign (`reports/2-scenarios/HUMAN-INTERFACE-REVIEW.md`, all 10 acceptance checks)**, truthful `S03`/`S05` evidence boundaries (`simulated_demo_gate` instead of any claimed independent held-out benchmark), and live `review-packet-v1` integration (`app/verification/packet_io.py` on `a05-demo-packet.json` with fallback to `database/fixtures/review-packet-synthetic.json`).
- Running live on **`http://127.0.0.1:8765/`** (`#S01`..`#S06`) connected to **MongoDB Atlas (`theseus_recplace`)**.
- Command to start/restart server:
  ```bash
  database/private/.venv/bin/python -m app.api.server --host 127.0.0.1 --port 8765
  ```
  *(Fallback if Atlas venv is absent: `python3 -m app.api.server --host 127.0.0.1 --port 8765`)*

## DONE
1. **Stage 1 (`SCHEMA_READY`) & Stage 2 (`RAW_IMPORT_VERIFIED` — Accepted by Coordinator):**
   - Lossless transfer of all `53,431` `raw.*` rows across 7 tables from `firn-duckdb` into MongoDB Atlas `theseus_recplace.raw_records` and `53,431` deterministic `sources` documents, with 100% multiset SHA-256 digest match (`theseus-raw-canonical-v1`) and `facts_created_count = 0`.
2. **Step 4 & Step 5 Deterministic Simulation Harness (`app/runtime/simulation.py`):**
   - Fixed-seed (`seed=20261107`) 120-lead synthetic cohort (`60` `sales_agent` + `60` `simulated_human_seller`) across `W1..W4` and 5 counterfactual arms (`before`, `agent_rule_only`, `onboarding_only`, `crm_field_only`, `combined`).
   - Explicit limitation recorded in code, UI, and status: deterministic code actors and chosen distributions (not live LLM sales agents and not calibrated from RecPlace historical CRM since `0/6,102` historical CRM deals record discounts).
3. **Theseus Control Plane Localhost Web Application (`S01..S06`) + `HUMAN-INTERFACE-REVIEW.md` Redesign:**
   - **`S01` (`Agree our direction`):** Fits `1280 × 800` first viewport without scroll; human-facing summary (Goal, Principle, Culture to protect, Risk hypothesis, What Theseus can see, Your decision) + primary `Confirm direction & monitoring scope` button, `Edit direction`, and `Why these recommendations?`. Saving direction keeps monitoring status `Monitoring: partial — discount outcomes missing` until Step 5 application.
   - **Evidence Drawer closed by default:** Fresh navigation starts with `#evidence-drawer` closed (`hidden` + `.layout.drawer-closed`); keyboard `Escape` and `Close (Esc)` return focus to the trigger without losing draft edits; import receipt moved to secondary `Data connection` header button.
   - **`S02` (`How we are working`):** Separates **Company evidence** (`0 of 6,102 CRM deals record discount outcome or reason` — data completeness gap, not discount frequency; customer request vs. seller offer vs. granted discount kept distinct) from **Simulation** (`84/120` synthetic leads).
   - **`S03` (`Does this fit our agreement?`):** Visibly compares against active agreement (`mandate-v1`), labels unapproved `v2` comparison as **`Preview against proposed rule`**, wires `app.verification.packet_io` (`load_packet`/`summarize`) for the recorded **SubQ Snap 1.1** response (`possible_conflict`, `46.4%` contradictory vs `40.4%` different scope/time, confidence `28.6%`, `rule_status="unapproved_training_norm"`), and preserves the original model assessment when the founder records a **`Question this finding`** review note + reason.
   - **`S04` (`Change how work happens`) & `S05` (`Your decision, then execution`):** Presents the three-lever correction (`rule-v2`, `onboarding-v2`, `crm-v2`), labels production CRM/training cost as `Not estimated`, labels external chat bridge as `External chat connection pending verification`, supports `Approve this correction` / `Request changes` / `Reject`, labels the pre-application check honestly as `Tested in simulation` (`split="simulated_demo_gate"`), enables `Apply in demo` only after approval, shows `Roll back to previous baseline` only when `tool-v2` is active, and includes the interactive Demo CRM form enforcing `Reason for discount`.
   - **`S06` (`Did the change help?`):** Prominent `SIMULATION` banner, matched 120-lead before/after summary cards with denominators, clear distinction between simulation recommendation and active demo runtime state, and local horizontal scrolling for expandable detail tables.

## NOT DONE / HONEST LIMITATIONS
- Independent real-world held-out benchmark for `tool-v2` has not been run (explicitly labeled `simulated_demo_gate` / `Tested in simulation`).
- Real human seller compliance after `onboarding-v2` is modeled in simulation (`61.7% -> 70.0%`), not yet observed in production.
- Hosted Fetch.ai Agentverse / ASI:One link opening to localhost is owned by `Viveka.Hackathon` and marked `External chat connection pending verification` in `S04`.

## CHECKS & BLOCKERS
- `python3 -m unittest discover -s app -p "test_*.py" -v` → **27/27 tests passed (`OK`, 0.358s)**.
- `python3 -m unittest discover -s reports/tests -v` → **7/7 tests passed (`OK`)**.
- `python3 reports/build.py --check` → **`Tracker validated: 25 tasks; no dispatch performed.`**
- Live HTTP check on `http://127.0.0.1:8765/` and `http://127.0.0.1:8765/api/state` → **`200 OK` (`backend_mode: "mongodb_atlas"`)**.
- **Blockers:** None.

## NEXT EXACT STEP
- Stage only Argon's assigned files (`database/`, `app/model/`, `app/control/`, `app/runtime/`, `app/deputy/` excluding `agentverse/`, `app/ui/`, `app/api/`, `docs/status/Argon.Hackathon.md`, `docs/agents/argon/CONTINUE.md`), create the single owner-authorized local Git commit, and send the commit SHA + paths to `Viveka.HackatonCoordinator`.
