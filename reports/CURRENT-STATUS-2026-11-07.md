# Theseus Control Plane — current hackathon status

## Current checkpoint — November 7, 2026, 16:58 PST

**Demo readiness estimate: about 80% complete / 20% remaining.** This is a coordinator judgment across ten equally weighted demo workstreams, not engineering effort or full-product completion. The 15:07 and 14:49 sections below are historical checkpoints, superseded by this section.

| Workstream | Current readiness | Evidence and remaining work |
|---|---:|---|
| Lossless RecPlace import | 100% | Atlas import verified: 53,431 raw rows and 53,431 source records. Historical snapshot, not live company activity. |
| Model and provenance | 85% | Versioned mandate, decisions, citations and rollback path exist. Full cross-agent independent integration review remains. |
| Muse extraction | 80% | Demo evidence handoff complete; 3,351 **candidate-grade** claims from 994 source IDs in a 7,697 candidate-hash set. Local private packet; Atlas claims/source_chunks/extraction_runs are 0. No full-corpus distillation. |
| One-goal culture view | 70% | Reviewed discount/price norms and examples are linked to sources; historical CRM lacks reliable discount outcomes/reasons. No prevalence or broad culture score claimed. |
| SubQ review | 95% | Five recorded Snap 1.1 discount comparisons are in S03 with exact labels/probabilities; **zero proven contradictions**. Model outputs are review signals. |
| Human decision and improvement | 65% | S01–S06 demonstrate a versioned human decision and simulated outcome loop. Independent held-out improvement and actual organizational adoption remain unproved. |
| Outcome simulation | 100% | Five reproducible arms on synthetic leads; visible simulation labeling, no real business-lift claim. |
| Website and Organization Memory | 90% | Datamaster takeover commits `70419a9`, `91dd768`; `/#MEMORY` shows verified import separately from local candidates, metadata paging and bounded Opus Q&A. Two real questions (one grounded, one abstention), reset, 37/37 tests, independent desktop screenshot and HTTP 200 passed. F03 six-state final pass remains review. |
| Hosted Deputy CEO | 90% | Real ASI:One authenticated HTTPS bridge queried Atlas raw records, cited a source and saw a changed test record without restart. Owner gateway allowlisted; website Commit remains the action. Native Commit card rendered at 16:58 and its Review direction click opened `#S01` at 16:59. Bridge/tunnel and laptop must stay alive. |
| Demo and submission | 35% | Scenario and video draft exist. Final live rehearsal, final media/submission and publication checks remain. |

**Calculation:** `(100+85+80+70+95+65+100+90+90+35)/10 = 81%`, rounded to **about 80%**. This estimate is a demo planning signal. The live Deputy and website have separate acceptance paths; a successful read/search does not mean the Deputy can approve policy. Source URLs have not yet been published, so current citations use source and claim IDs. The temporary HTTPS bridge is authenticated and limited to the owner gateway. No raw client payload or secret is included in this report.

**Immediate path:** capture one complete live walkthrough from Organization Memory → grounded question → human Commit → S03 review → simulated outcome; keep the local app, bridge and tunnel running; check public artifacts for secrets before submission. Deputy implementation and acceptance are checkpointed in `4b490f3`; the hosted agent did not approve the owner's decision. Muse's evidence track has no P0. Argon's model limit is exhausted; Datamaster now owns `app/ui` and `app/api` and has closed F04. Detailed evidence: [Datamaster status](../docs/status/Viveka.Datamaster.md), [Muse handoff](../database/fixtures/evidence-handoff.json), [Deputy acceptance](../app/deputy/agentverse/MONGO-LIVE-VERIFICATION.md), [work log](../docs/WORKLOG.md).

## Live update — November 7, 2026, 15:07 PST

The detailed table below is the 14:49 checkpoint. **The current demo estimate remains about 60% complete / 40% remaining**, pending a fresh end-to-end review. Since that checkpoint:

- Muse has produced **68 quote-gated claims from 73 distinct sources** (last verified count) and shifted to price, discount and sales evidence. A single transcript documents a price negotiation and agreement; signing, payment and a CRM join are unknown. Earlier CRM revenue and paid-client figures were superseded after snapshot and redacted-key checks; the semantics of `revenue_total` remain unverified. **Do not use those figures as realized sales.**
- Viveka.Hackathon completed the [human interface review](2-scenarios/HUMAN-INTERFACE-REVIEW.md). Argon acknowledged all ten checks at 15:07 and is implementing a human-readable first viewport, closed technical evidence, clear real-versus-simulated labels, and corrected S03/S05 decision states. These corrections are **in progress, not accepted yet**.
- Setu rendered a first 60-second video with placeholder screens and Gemini female TTS. Real screen capture and the final submission remain.
- The shared checkout has local Setu commits `46dd4bc`, `60f4eab` and Muse commits `4c75a4d`, `9ef9ac5`. Argon's UI is still uncommitted. Push status for these newer commits has not been independently verified.

The earlier rows below retain their original checkpoint values for auditability; use this update for the current state.

**Checkpoint:** November 7, 2026, 14:49 PST (corrected after owner review of S01). **Coordinator estimate:** about **60% of the hackathon demo plan is complete; about 40% remains**. This is a readiness estimate across ten equally weighted workstreams below, not an estimate of engineering hours or of the full product vision. Several completed components are pilots or simulations. The end-to-end claim is **not yet demo-accepted**.

## What we set out to show

We would copy RecPlace's primary records unchanged into MongoDB; derive traceable claims from source material; detect candidate conflicts; let a human see the organization's goals, explicit rules, emergent culture, resources, relationships and progress; approve a change in agents, tools or context; independently test the change, activate or roll it back; and observe the result. A Fetch.ai Deputy CEO would summarize the state and propose action, while a website would show the complete evidence and controls. The hackathon proof is one narrow discount-policy case, not a claim that an entire organization already runs this way.

## Done, partial and missing

| Workstream | Readiness | Evidence and remaining work |
|---|---:|---|
| 1. Unchanged raw RecPlace transfer | 100% | Live Atlas `theseus_recplace` has **53,431 raw records and 53,431 source records**; the seven source-table counts and completed import run were checked against Atlas. Argon's source-to-Atlas multiset hash comparison is recorded in private evidence. This is the raw layer, not newly extracted facts. |
| 2. Model, provenance and versioning | 80% | Schema/adapter, source references, versioned rules and decisions, activation/rollback receipts and a traceable review packet exist. The complete cross-agent chain still needs a final integration review. |
| 3. New fact extraction with Meta | 70% | Muse Code used a Meta model through its API-backed session on three private owner-approved records, producing **18 quote-gated candidate claims**, three rejected candidates and one review signal. The owner confirms Meta API use; the billing screenshot shows **$73.53 of $100 credits remaining**. The standalone `app/extraction/meta_adapter.py` path has not been evidenced as invoked. That separate adapter is not a prerequisite to count Muse's Meta-backed work in this demo. Muse has since identified the founder episode `src:d7d9e58795f8d6ff5b34` (source text SHA-256 `00802831fcf1e631242156e4dba714ddc609078a990fa2f2da2168964ee171a0`) and prepared a deduplicated 40-source follow-up batch locally; no additional source text has been sent to a model. |
| 4. Emergent culture measurement | 35% | The interface shows recurring-practice cards with provenance and limits. The historic CRM dataset does not record why a discount was given, so compliance with the proposed rule cannot yet be measured directly. A demo CRM field captures that reason prospectively. |
| 5. SubQ conflict review | 55% | A deterministic prefilter reduced **153 pairs to 41 candidates**; eight filtered cross-source pairs were manually audited with zero misses in that small sample. One real `subq-snap-1.1` call returned low-confidence competing interpretations, so the result is **possible conflict**, not a proven contradiction. A source-linked review packet exists; S03 must display that distinction faithfully. |
| 6. Human decision and safe improvement gate | 50% | Local approval, activation and rollback flows exist. **Blocking correction:** the current server seeds a `24/24` held-out pass at startup rather than deriving it from an independent held-out run. It must be removed, clearly labeled as a fixture, or replaced with reproducible evaluation before claiming verified improvement. No independent verifier has been assigned. |
| 7. Outcome simulation | 100% | Argon's fixed-seed, five-arm comparison on 120 **synthetic** leads has run; Atlas has five simulation runs, 600 simulation events and 360 demo CRM documents. The UI labels synthetic weeks and leads. The method and limitations are recorded below. This proves the demo loop mechanics, not a real business lift. |
| 8. Six-screen Theseus website | 45% | Argon implemented S01–S06 on `http://127.0.0.1:8765/` with live Atlas backend. The coordinator independently ran **22 application tests: all passed**, and checked that `/api/state` returned `mongodb_atlas` plus all six state keys. The owner inspected S01 and rejected its human usability: internal IDs, technical fields and raw import JSON dominate the decision. Viveka.Hackathon is reviewing the human-facing design; Argon will implement the prioritized corrections. UI files are presently uncommitted. |
| 9. Fetch.ai Deputy CEO and cards | 20% | A hosted, proposal-only Agentverse agent answers manual text ACP tests. It is **not connected to Theseus data or controls**. Native ASI:One cards, record deep links and browser handoff remain unverified. Earlier manual tests also found unsupported evidence claims, so they are not accepted as grounded product behavior. |
| 10. Demo, video and submission | 35% | Setu has drafted the S01–S06 script and a one-minute shot list; partner slide and reporting scaffold exist. Six-screen capture, final video, updated partner/use disclosure, and submission are still outstanding. |

**Calculation:** `(100 + 80 + 70 + 35 + 55 + 50 + 100 + 45 + 20 + 35) / 10 = 59%`, rounded to **about 60% complete / 40% remaining**. The workstreams are equal-weighted for a quick coordination signal. This is not a prediction that only 40% of the remaining time is needed. The full five-area product remains at prototype stage.

## Argon's simulation method — recorded handoff

Argon recorded the method in [`docs/status/Argon.Hackathon.md`](../docs/status/Argon.Hackathon.md) under “Step 4 & Step 5 Deterministic Simulation Harness + Demo CRM Field” and implemented it in [`app/runtime/simulation.py`](../app/runtime/simulation.py). It is reproducible with seed `20261107`:

1. Generate 120 synthetic leads over four synthetic weeks (`W1`–`W4`): 60 assigned to rule-driven `sales_agent` actors and 60 to `simulated_human_seller` actors. The generator uses explicit probability/distribution choices in code; it does **not** load real RecPlace client payloads or estimate those probabilities from RecPlace data.
2. Run the same lead cohort through five configurations: before, agent rule only, human onboarding only, required CRM justification field only, and all three changes combined. The agent rule changes immediate discounting to commitment-based discounting; human onboarding has a modeled adoption ramp; CRM v2 requires a justification or blocks/changes the attempted discount.
3. Record each simulated decision and calculate counts, denominators, discount/value-exchange shares, consistency and per-lever keep/keep-candidate verdicts from stored events. Persist the five runs, 600 events and 360 demo CRM records to Atlas. Every record and metric carries `provenance="simulated"` and the on-screen `SIMULATION · synthetic leads · synthetic weeks` label.

The actors are deterministic code models, **not live LLM sales agents**. This is a counterfactual demonstration of how three levers would be measured, not an observed post-intervention effect or proof that the assumed probabilities match real sales behavior.

## Critical path to a truthful demo

1. **Correct S05 evidence:** remove or explicitly mark the startup-seeded `24/24` held-out pass. Run a genuinely independent held-out check if the demo claims *The System That Gets Better*; otherwise show a candidate awaiting evaluation. Keep approval separate from activation.
2. **Connect S03 to the real review packet:** preserve exact source links and show the low-confidence SubQ result as a candidate review, while keeping synthetic examples visibly synthetic.
3. **Make the website human-facing:** apply Viveka.Hackathon's review to S01–S06, with one clear decision per screen and progressive disclosure for evidence, IDs and raw import receipts. Then connect the hosted Deputy CEO to bounded data/cards or present it honestly as a separate text-only prototype.
4. **Capture and submit:** update Setu's scenario from actual screen states, record the short video, refresh the partner slide and built-today disclosure, then submit the project.

## Collaboration and publication state

The public GitHub repository is [`tvpustovoy/theseus-control-plane-hackathon`](https://github.com/tvpustovoy/theseus-control-plane-hackathon). Commits `f46fd90` and `9d14608` are pushed. Current Argon UI and Setu scenario work is still in the shared checkout and not yet pushed. Argon has been asked to make a substantive commit himself in an exclusive Git-index window; Muse will do the same afterward. Their own commits are **pending**, not already credited. Private RecPlace material and credentials remain in ignored local storage.

The locally generated `reports/STATUS.html` and older `README.md` / `docs/PLAN.md` contain earlier-stage language. Use this checkpoint with current agent status files and fresh tests for today's state; reconcile those older summaries before external circulation.
