# Theseus / Part II / Tools and evidence

**Presentation update: one slide only, at the owner's request.** The HTML, live deck and PowerPoint now contain the same single partner overview. The eight-slide script below is retained as background research, not the presentation running order. Interface ownership and build order are in [DEMO-INTERFACES.md](DEMO-INTERFACES.md).

November 7, 2026. Companion to [DEMO-CHORD.html](DEMO-CHORD.html), following the owner's five-step chord and Firny visual direction.

- [HTML presentation](TOOLS-PART-II.html)
- [Editable PowerPoint](THESEUS-PART-II-TOOLS.pptx)
- Live presentation: `artifact_2LGWeXxPoThPVWcVQB0NuBUhNYsHSFC7`

## SubQ placement

Primary: **step 3, conflict review**, between cited extraction and a proposed intervention. Secondary: **step 5**, reusing the versioned rubric on comparable new episodes.

The proposed Snap pipeline is deterministic scope selection, exact deduplication, a cited comparison packet, structured judgments, and selective escalation. This aims to reduce repeated context and generative review calls. No token-saving percentage, accuracy or latency result has been measured.

Snap supports structured choice/score questions through the Decisions API. Add explicit different-scope and insufficient-evidence outcomes. A separate choice can select from supplied passage IDs; the application retrieves the corresponding quote. Keep model confidence separate from empirically calibrated error rates. Source: [SubQ Decisions API](https://docs.subq.ai/endpoints/decisions-api/).

Optional long-context audit: use `subq-preview` to review a wider dossier at the same step only after access is verified. `subq-snap-preview` is a different model. The inspected preparation inventory confirms only Snap IDs. Source: [SubQ models](https://docs.subq.ai/using-the-api/models/).

## The evidence correction

The latest chord's evidence check distinguishes discount requests from granted discounts. The broad founder rule still needs a verified source or explicit owner framing. CRM discount events and an intervention date are absent from the inspected source evidence. Therefore:

- Do not announce observed margin leakage, learned customer discount-seeking, or measured cultural drift without new evidence.
- Show a lack of observability as a finding and the CRM field as a proposed response.
- Label before/after agent simulation explicitly. It does not prove human behavior or commercial impact.
- Keep approval, executable verification and rollback separate from a model's consistency score.

## Slide script

### 1. Tools behind the Theseus loop

Part II · How the five-step demo is built

- **01  Codex and goals:** Meta extracts evidence. MongoDB keeps versions.
- **02  Culture:** Meta identifies episodes. Code measures recurrence.
- **03  Conflict:** SubQ tests rule applicability and evidence.
- **04  Proposal:** Fetch.ai presents options. Gemini builds changes.
- **05  Tracking:** MongoDB stores events. SubQ repeats the rubric.

Architecture roles. Delivery evidence appears on the final slide.

Speaker note: Source: reports/2-scenarios/DEMO-CHORD.html and DEMO-CHORD.md, inspected November 7, 2026. This is a design map, not a claim that all runtime integrations are complete. Google/Gemini currently contributes as the development agent Argon. Brand artwork is the owner-selected styles/theseus-logo-v8-spacesuit.png.

### 2. Evidence extraction and durable memory

Steps 1–2 · Meta Model API and MongoDB

- **Meta:** Inputs: founder documents, calls and chats. Outputs: cited principles, goals and behavior episodes. A new recording updates the evidence model. Why: one multimodal extraction path.
- **MongoDB:** Keep raw records unchanged with provenance. Store claims, rule versions and counterexamples. Link later decisions and observed outcomes. Why: every conclusion needs a traceable history.

A request, offer and granted discount are different events.

Speaker note: Proposed runtime roles based on DEMO-CHORD. Meta model modality support: https://dev.meta.ai/docs/models (checked November 7, 2026). Local schema, adapter and importer exist; Atlas raw import and new Meta extraction are not verified by this snapshot. Video extraction is an option only after authorized material and a successful call exist. Repeated behavior requires multiple independent episodes, not duplicated transcripts.

### 3. SubQ tests the suspected conflict

Step 3 · After extraction, before the Deputy CEO proposes a change

- **The comparison packet:** Rule version and scope, cited episodes, time window and counterexamples.
- **The questions:** Does this rule apply? Does the evidence support the behavior claim?
- **The possible outcomes:** Consistent · Contradicts · Different scope · Insufficient evidence
- **The retained evidence:** Source IDs, rule version, rubric version and model output.

Why Snap: structured choices under one rubric. Evidence and approval stay in the application.

Speaker note: Proposed use of SubQ Snap Decisions API: https://docs.subq.ai/endpoints/decisions-api/. Use choice questions with an explicit insufficient_evidence class. A separate best_passage choice may select among supplied source labels. Snap returns structured judgments, not a generated narrative explanation. Its confidence is not a calibrated probability that the organization violates policy. No SubQ product evaluation run is claimed. This is a consistency screen, not an independent software correctness verifier.

### 4. A small packet before a model call

Proposed cost control for step 3

- **01  Scope in code:** Match topic, organization, actor, deal and the rule's effective period.
- **02  Prepare evidence:** Collapse exact duplicates. Retain counts, order, exceptions and counterexamples.
- **03  Ask SubQ Snap:** Classify one clear decision using a versioned rubric.
- **04  Escalate selectively:** Send ambiguous or consequential cases for deeper review and human resolution.

Measure token use and missed conflicts against a labeled baseline before claiming savings.

Speaker note: Architecture proposal, not measured performance. Deterministic retrieval/deduplication is the first token-saving mechanism; Snap is a model call itself. Do not do an all-pairs comparison between every rule and every raw record. Keep samples of filtered-out cases to measure misses. Reuse a result only when packet, scope, rule, rubric and model version match. Models distinction: https://docs.subq.ai/using-the-api/models/. Long-context subq-preview can optionally review a wider dossier at step 3 after account access is verified; subq-snap-preview is a different model family. The inspected setup inventory lists Snap IDs only. No reduction percentage or latency claim.

### 5. A missing signal is a useful finding

Discount case · Evidence boundary from the updated demo

- **What the sources support:** Conversations contain discount requests and reasons.
- **What the CRM lacks:** A discount field, a reason field and recorded discount events.
- **What we cannot conclude:** A request does not establish that a discount was granted.
- **The useful next step:** Propose a required reason field and record the actual outcome.

Illustrative SubQ outcome: “Insufficient evidence of a granted discount.” No live result claimed.

Speaker note: DEMO-CHORD.html evidence check relayed from Datamaster at 13:26: all 6,102 raw CRM deal rows and stage history contain no discount/reason field, and conversation references do not prove application. No client identifiers or quotes reproduced. The broad founder phrase combining flexible discounts and value-first selling is not source-verified; present it as the owner's framing or supply a source. Margin leakage and customers waiting for a discount are hypotheses, not findings. Missing CRM telemetry motivates a proposal but does not prove the required field improves commercial outcomes.

### 6. One proposal, three levers

Step 4 · Fetch.ai reaches the owner; Gemini helps build the correction

- **Agents:** Version the discount rule and the executable skill.
- **People:** Propose an onboarding update with concrete examples.
- **Environment:** Add a required justification field to the demo CRM.

Why Gemini: code and verification. Why Fetch.ai: the owner's conversation. Human approval comes first.

Speaker note: Fetch.ai Agentverse hosts the proposal-only Deputy CEO. Direct Agent Chat Protocol replies were verified; a separate ASI:One conversation and backend integration are pending. Gemini/Argon is verified as a development contributor to the local schema/importer/governance scaffold, not as a proven runtime model call in this product. Actual model-generated fixes and held-out adoption require separate recorded evidence. Existing Python ScopedDeputyCEOTools allows organization overview, conflicts, evidence trace, proposals, diffs and behavior summary, and denies direct activation. Sources: app/deputy/agentverse/VERIFICATION.md, app/deputy/__init__.py, docs/status/Argon.Hackathon.md. Real customer CRM writes are not authorized by this demo proposal.

### 7. The same rubric follows the change

Step 5 · MongoDB event history with repeat SubQ checks

- **Version the intervention:** Record agent-rule, onboarding and CRM changes separately.
- **Compare comparable episodes:** Keep rule scope and time windows explicit. Retain unknown outcomes.
- **Measure behavior:** Report justification coverage and assessed consistency with denominators.
- **Keep or roll back:** Require human review plus executable checks on unseen cases.

Current before/after plan: labeled agent simulation. Human behavior and commercial impact remain unproven.

Speaker note: Proposed recurring SubQ role: use the same versioned criterion for eligible new episodes and store outputs with evidence references. An explicit rule change requires labeling or rerunning comparable samples; silent rubric drift invalidates before/after comparison. Separate filling a reason field from providing a value-based reason and from business outcomes. Do not infer causality from a simple before/after trend. As DEMO-CHORD states, no historical CRM intervention point is verified, so agent simulation must be labeled. Simulated agents cannot demonstrate actual human onboarding impact. SubQ judgments do not replace held-out executable software tests.

### 8. Delivery evidence today

Verified setup and development work, with remaining runtime proof

- **Google / Gemini:** Argon built the local schema, importer and control scaffold. / Runtime improvement loop still to prove.
- **Meta:** Muse Code works as a development agent. / Fresh cited extraction still to prove.
- **MongoDB:** Atlas cluster exists. Source preflight and local adapter checked. / Verified raw import still pending.
- **Subquadratic:** Snap model IDs confirmed in setup. / Step 3 request, verdicts and evaluation pending.
- **Fetch.ai:** Hosted Deputy CEO answered direct ACP tests. / Backend and separate ASI:One demo pending.

Snapshot: November 7, 2026. The five-step end-to-end demo has not yet run.

Speaker note: Evidence snapshot from reports/2-scenarios/DEMO-CHORD.html (13:34), docs/status/Viveka.HackatonCoordinator.md (source preflight 13:29), docs/status/Argon.Hackathon.md and Muse.Hackathon.md, app/deputy/agentverse/VERIFICATION.md, and the setup GET /v1/models inventory. No API keys, private payload, account emails or credential paths included. This deck does not claim five runtime integrations are complete. Refresh this slide only when actual request/response, version, source and evaluation artifacts exist.

## Reuse and current proof

Firny's visual family and the existing v8 ship mark are reused. This work adds the Part II narrative, editable slide content and local HTML presentation. It makes no provider call, imports no client payload, and publishes nothing. Runtime-use claims remain conditional on the final evidence slide. SubQ's role is a proposed consistency review, not a claimed independent software verifier.

