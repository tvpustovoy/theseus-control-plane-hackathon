# Theseus three minute live demo

Owner review draft, 7 November 2026. This revision incorporates Taras's request to start with the organization reconstructed from evidence, prove it through a factual agent answer, and then demonstrate a human-directed change with a live simulation. It supersedes the earlier card-first sequence. No new implementation tasks are assigned by this document.

## Narrative

AI employees can improve a company while quietly changing how it works. Theseus gives its owner an evidence-backed view of the organization, a way to set its direction, and a way to check whether a decision changes behavior.

The story follows one thread: ask what discount strategy is actually established; inspect the evidence and propose a direction if no authoritative current agreement is found; have the owner confirm it; compare the preceding two weeks with that direction; change the mechanisms that govern discounts; then simulate the next two weeks and check again. New decisions and events become evidence for the next cycle. The Commit emerges from the conversation rather than arriving as a prewritten answer to an unrelated question.

The Ship of Theseus is the framing, not a separate mythology lecture: the company can replace its processes while the human keeps the helm.

## Current readiness

- Verified: 53,431 original records imported into MongoDB Atlas, across seven raw tables; source/target digest verification is recorded. These are records, not 53,431 unique documents.
- Extraction continues. Muse's latest inspected batch-35 report records 3,223 quote-checked claims and 982 distinct text hashes covered out of 7,697. These are a dated extraction checkpoint, not a fresh MongoDB count, exhaustive organizational knowledge, or proof that every claim is true. A later checkpoint may supersede them.
- Verified at 16:50 PST: hosted Deputy live MongoDB counts/search through an authenticated HTTPS bridge; 53,431 raw records counted in ASI:One; source-ID answer; changed test record visible on the next question without restart; English replies even to Russian questions. Use the tested owner chat in `app/deputy/agentverse/RUN-LIVE-MEMORY.md`. Keep the laptop, bridge and tunnel running.
- Deputy facts come from both the curated brief and live query tools over the permitted RecPlace collections. Atlas claims/source_chunks/extraction_runs were empty at this check; Muse's local packet count must be labeled as a local extraction artifact until persistence is verified.
- The native Commit card is a recorded draft; its ASI mention-prefix regression was fixed and the card rendered again at 16:58 PST. A plain local-app link is also present. The local Agree Direction screen was verified. The current state mirror is read separately. The v1 demo runtime default is not evidence of an approved company-wide discount strategy.
- Still requires acceptance: the Organization Memory overview and the live simulation trigger/results path, owned by Argon/coordinator.
- Previously reported and not yet independently accepted as fixed: same-input customer-commitment enforcement, S06 metric binding, and repeatable session reset.
- The existing source documents, model reviews and imported data can be prepared before the talk. Interactions, queries, mutations and any claimed fresh simulation run must happen in the running application. A video or screenshot is not a replacement for this live demonstration.

## Opening screen: Organization Memory

Use one compact view in the Theseus application, before Commit. This is a proposed screen, not an implemented route. Existing Data connection/import evidence can supply its verified-import details but is not yet the complete view.

Top line: organization name, source snapshot date, latest extraction checkpoint, and actual retrieval time. Display partial coverage clearly.

| Area | What the human sees | Interaction / source of truth |
|---|---|---|
| Original evidence | 53,431 imported records; seven raw tables; 6,102 CRM deal records; categories for conversations, CRM history, founder material and training documents | Open the import receipt and source inventory; use verified import metadata |
| Extracted knowledge | Counts of observed claims and stated norms, separately; explicit distinction between a quoted norm and a human-approved active rule | Open an extracted item, its approved display excerpt, date and source reference |
| Coverage and uncertainty | How much of the selected corpus is processed; sources still pending; missing discount outcomes/reasons in the historical CRM | Use real denominators and explicit snapshot labels; no invented completion percentage |
| Recent activity | Last extraction checkpoint, human decision, active rule version, and new demo transaction events | Read current run state; label synthetic demo events separately from company history |

An answer should connect to an item and then to its supporting source. Avoid a decorative knowledge graph unless its nodes and links correspond to stored entities and relations.

Do not derive global counts from a limited record sample. The existing API takes at most 25 claims/signals and combines that length with an older packet count; that field is not an authoritative aggregate for this overview. Backend queries or a verified checkpoint manifest must supply the totals.

Only approved public-safe excerpts may appear on the projected screen. No private contact details, credentials or raw client payloads.

## Timed performance

The presenter is Taras. Two surfaces: Theseus web app and the Deputy chat. One tested question, one human policy decision, one changed transaction, one small simulation. Budget approximately 230 spoken words plus interaction time.

| Time | Screen and action | Spoken English | Visible proof |
|---|---|---|---|
| 0:00–0:20 | Organization Memory: point to evidence inventory and partial coverage. | “AI employees can improve your company while quietly changing how it works. Theseus keeps the human at the helm. We start with the company's own records: calls, CRM history, and internal documents.” | Real imported records, extracted knowledge and visible coverage; no claim that the entire organization is already modeled. |
| 0:20–0:45 | Ask Deputy: **What is our strategy on discounts?** Open one returned source reference and the proposed direction. | “The deputy checks the current agreement and the evidence behind our practice. Where the strategy is not yet explicit, it proposes one from what the organization already knows.” | A fresh scoped query, supported answer and usable citation. “No agreed strategy found” must follow retrieval; it is never a scripted forced answer. If an approved strategy exists, show it and propose clarification instead. |
| 0:45–1:10 | S01 Commit: review the proposed strategy, refine if needed, then confirm direction and monitoring scope. | “I choose the direction: grow sales while protecting value. A discount should earn something in return, such as prepayment or a longer commitment. This becomes our agreement going forward.” | Human approval of the exact proposed version and effective time; active monitoring limits stay visible. |
| 1:10–1:35 | Run an evidence review of the preceding two weeks in the available snapshot; S02/S03, then S04 proposal. | “Now compare recent practice with that direction. Theseus shows what fits, what does not, and what our records cannot establish. Here, the CRM needs to capture why a discount is given.” | Display actual event-date range and coverage. This is retrospective alignment with the new direction, not a claim that staff violated a rule before it existed. SubQ's recorded five-call result remains distinct from any fresh period-scoped review. Missing fields do not prove discount abuse. |
| 1:35–2:25 | S05: test a synthetic 5% discount without customer commitment under v1. Approve and apply the correction. Repeat identical input under v2. Add declared prepayment and repeat. | “Watch the same request before and after my decision. Approval and application are separate. Once applied, the rule blocks a discount without a customer commitment. Add prepayment, and it passes. The system records the reason and the rule version.” | Same-input behavior changes; rejection writes no successful CRM deal; accepted synthetic deal produces a new record and audit event. Prepayment is declared demo input, not a verified real payment. |
| 2:25–2:50 | S06: **Simulate next 2 weeks**, then repeat the alignment review over the resulting events. Show intervention status and one computed measure. | “Let two weeks of simulated work pass. We check again: did the changes reach the workflow, and is behavior staying aligned? The results guide our next decision.” | A fresh two-week simulation with a declared start/end, matched baseline/candidate inputs and explicit Simulation label. Report application status separately from observed simulated behavior. Do not relabel the existing W1–W4 report as a new two-week run. |
| 2:50–3:00 | Return to current activity / direction; show the new decision and transaction in memory. | “The company changes, the evidence grows, and the human keeps the helm. That is Theseus.” | The decision and new behavior become evidence for the next cycle. |

The opening agent question is a reproducible demonstration, not a hard-coded question route. Its implementation must support general questions over the allowed data. In Q&A, try a second question such as “What evidence is missing?” or “Why did that last deal fail?” without changing the adapter.

## Meaning of the repeated check

The first comparison asks how prior practice aligns with the newly chosen direction. The second examines events generated after application under that direction. A true historical breach requires an applicable approved rule already in force at the event time. “Latest two weeks” must use event dates in the available source snapshot, not assume this imported corpus covers the two weeks before the hackathon.

The proposed interface change makes the decision operational: the CRM records the discount, reciprocal commitment and any required approval; the same rule is enforced for agent tool calls. The final screen shows each change's version and application state beside measured behavior. A displayed form alone is not proof that agents obey, and delivered seller guidance is not proof of human adoption.

## What this demonstrates

1. Organization memory comes from traceable company evidence.
2. A conversational Deputy can retrieve facts and explain their limits.
3. Human intent becomes an explicit, versioned agreement.
4. That agreement changes an executable mechanism and the data it collects.
5. A fresh simulation tests consequences before any claim of business improvement.
6. New events close the loop back into the organization's memory.

The five areas remain the upper frame: Purpose (sales goal), Rules (principle and culture), Resources (margin), Relationships (customer commitment), Progress (measurement and the next review). Do not spend the three minutes teaching five separate modules.

## Required preparation

- Keep the accepted read-tool bridge running as described in [RUN-LIVE-MEMORY.md](../../app/deputy/agentverse/RUN-LIVE-MEMORY.md). The owner's verified ASI gateway is allowlisted; other public callers receive no organizational data.
- Add the overview and source-link path. Reconcile counts to their actual store/checkpoint, not model narration.
- Verify the same-input runtime transition and fresh simulation button before writing “works live”.
- Implement/reset an isolated run from C0 using [LIVE-DEMO-RESET-CONTRACT.md](LIVE-DEMO-RESET-CONTRACT.md). Never clear the shared company database.
- Rehearse twice from a fresh run. Record versions, run IDs, query citations, semantic outcomes and elapsed time. No background ingestion should change the prepared evidence packet halfway through a rehearsal.
- Keep evidence panels closed initially and prefill the synthetic deal. Open the two required tabs; hide unrelated browser material.

## Live-only contingency

If ASI is slow, switch once to the already running app and use its evidence views; be explicit that the conversational step is unavailable. If a required backend operation fails, show the failure honestly and continue only with working interactions. Do not replace the live loop with a video or claim that a cached answer/report was freshly computed.

Do not start the presentation with an unaccepted before/after transition or call a missing simulation trigger. If these gates remain open, shorten the demonstrated scope in agreement with Taras before the talk.

## Ownership

Argon owns the existing app/API/runtime area. Viveka owns the hosted Deputy and this runbook. Setu owns the narrative adaptation and presentation materials; the coordinator sequences authorized work and acceptance. This document prepares the next agreed scope; it does not dispatch it.
