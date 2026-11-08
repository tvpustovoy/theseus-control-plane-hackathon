# Deputy cards — basic demo coverage

November 7, 2026, evening · Viveka.Hackathon

Scope: native ASI:One cards and their website handoffs. This audit does not count website screens as implemented agent cards. Checked the current protocol against `reports/2-scenarios/LIVE-DEMO-3MIN.md`, exercised 13 prompt/state combinations locally, and reran the 20 existing contract checks (all passed). A local result is not a fresh ASI rendering check.

## Coverage

| Demo moment | Current agent card / handoff | Status |
|---|---|---|
| Organization Memory: what data was loaded? | A grounded text answer; no dedicated Memory card or deterministic `#MEMORY` navigation action | Missing card |
| Commit: propose and agree direction | `Commit · Set our course`; Review direction → S01, Let’s discuss → conversation | Implemented; earlier real ASI rendering and both actions verified |
| Current Commitments | A short current-state answer and `#COMMITMENTS` link, plus the card for the next workflow step | Link verified live; no dedicated commitments summary card |
| Culture / How We Work | No dedicated card or S02 action | Missing card; the website remains accessible from its navigation |
| Alignment review | `Make the rule measurable`; Review evidence → S03 and Review proposed change → S04 | Implemented; live rendering/evidence navigation verified |
| Proposed correction | Shares the same navigation card; it does not summarize the three proposed changes | Partial: website handoff exists, proposal-specific card missing |
| Approve / apply | `Review before applying`; Review & apply on website → S05, Review evidence → S03 | Implemented for approved-but-not-applied state; offline checked, fresh live rendering not checked in this audit |
| Commitment outcomes | `Commitment outcomes`; Review & apply on website → S05, View commitment outcomes → S06 | Implemented for active tool-v2 state; offline checked, fresh live rendering not checked in this audit |

There are four card variants, selected primarily by current workflow state. The existing flow can be navigated through the website, but it is not a complete set of agent cards for all demo moments.

## Exact prompt checks

- Pending direction: `What is our discount strategy? Separate facts, principles and decisions requiring my approval.` attaches Commit.
- Confirmed direction: `Show evidence`, `Show the proposed change`, or `Against the direction I confirmed, what do you recommend?` attaches the shared review card.
- `Show current commitments` produces the current snapshot link and relevant next-step card.
- Approved or active state: `What should we do next?` selects the appropriate apply/outcomes card.
- Current routing gaps: `Show our culture`, `Check alignment`, `Show the approval card`, `Show simulation results`, and `What changed?` do not deterministically attach a card. A reasoning answer is possible, but it is not a reliable card entry point.
- Natural wording about outcomes of a commitment is not a dedicated intent yet; the generic commitments matcher can select a status/next-step card. Explicit outcome navigation needs its own intent before the broad commitments matcher.

## Minimal remaining work, not dispatched by this audit

1. Add a compact Organization Memory card with a full-view link.
2. Give Current Commitments its own summary/action instead of only an adjacent link.
3. Add a proposal-specific summary and pre-approval review handoff to S05.
4. Recognize ordinary culture/alignment/apply/outcome requests and route by requested view as well as current state; preserve approval gates.
5. Rehearse the approved and active card variants in an isolated demo run, without altering the owner's current run just to manufacture a screenshot.

The owner requested **Commitment outcomes** / **View commitment outcomes**, with no “simulated” in the card title/button. The evidence row says `Test run; company outcomes not yet measured`. This is a wording change, not a conversion of test outputs into observed company outcomes. S06 remains an illustrative comparison and is not automatically recomputed for arbitrary edited goals.

All card actions are navigation/discussion requests. Human confirmation, approval and application remain separate website actions. Every existing navigation action includes an ordinary link and the validated originating chat URL for return.
