# Theseus Control Plane — narrative and build proposal

November 7, 2026. **Proposal for owner review, not an implementation report.**

## The promise

**An organization that can rewrite its software without silently rewriting its mandate.**

We want to build a human control plane for an organization of agents that reconstructs a business workflow from evidence, builds the tools to run it, and proves each improvement before adoption. A Deputy CEO translates the owner's intent into bounded work and returns evidence, unresolved questions and decisions worth the owner's attention.

The business value is a reusable migration path: source material → evidence model → executable process → controlled agents. The hackathon proof is one actual software task and one measured improvement cycle, not a claim to automate a whole company.

## One concrete software task

Proposed first slice: rebuild a small RecPlace-style renewal/discount decision service on the new architecture. Input: authorized policy fragments, anonymized source records and optionally a screen recording. Output: a running tool/API that returns a proposed action, its evidence, unresolved conflicts and whether approval is required. No real transaction or customer communication occurs in the demo.

This slice is a recommendation, not a confirmed dataset choice. Discounts appeared in prior project work; that does not authorize exporting all related records. If the needed source set is unavailable, use clearly labeled synthetic fixtures representing the same contract.

The coding task spans ingestion, schema, decision logic, permissions and tool interface. Build and test those together, rather than treating extracted knowledge as the final software result.

## Fit to the organizer's problem statements

| Challenge | Actual fit | Evidence required |
|---|---|---|
| The System That Gets Better — proposed primary | Coding agents build the tool, learn from a development failure, version a skill/tool/routing/context change, and retain only a validated improvement | Source revisions, reproducible baseline, development failure, candidate change, held-out before/after outcomes, accepted version and rejected/rolled-back alternative |
| Trust but Verify — supporting mechanism; possible primary only if this becomes the strongest implemented result | A separate verifier checks generated code and behavior against an owner-approved contract | Independently authored tests, isolated evaluator, immutable test version, seeded defect detection, gate that actually blocks or rolls back |
| Software Archaeology — conditional, not claimed by default | Reconstruct or port an existing authorized software behavior from traces, partial code or demonstrations | Observed-versus-inferred ledger, old/new replay on the same inputs, equivalence scope and mismatches |

A business knowledge graph alone does not establish any of these. Multi-provider agreement does not establish verifier independence or behavioral equivalence. Pick one primary challenge and earn the others only through observable behavior.

## One system, five partner products

| Partner | Proposed job | Submission proof |
|---|---|---|
| Meta Model API | Turn text, documents and relevant video into cited claims and workflow observations | Actual request/model version, redacted response, source span or timestamp and corrected extraction example |
| MongoDB | Persist sources, claims, contradictions, goals, rules, versions, agent contracts, runs and decisions | Running collection/query path plus the same decision trace before and after a change |
| Subquadratic | Classify candidate claim conflicts and route uncertain cases before expensive generative analysis | Actual Snap decisions, candidate IDs, evaluation against labeled cases, cost and missed-conflict measurements |
| Google DeepMind / Gemini | Lead the multi-file build and bounded improvement loop; optionally serve as runtime engineering agent behind Deputy CEO | Real diffs, tool runs, tests, versioned lessons and held-out results; distinguish development use from runtime calls |
| Fetch.ai | Expose the Deputy CEO through ASI:One and coordinate scoped tools/workers | Registered discoverable agent, Agent Chat Protocol, a complete conversational task with evidence and a human decision |

The submission selector permits multiple partners. It does not imply every partner is implemented or that every challenge is satisfied.

## Meta: useful multimodality

Current Meta documentation lists Muse Spark 1.3 for volume-sensitive work and Wonder for harder multi-file/long-running reasoning. Spark can combine text, images, video, audio and PDFs; structured output can constrain the result shape. [Models](https://dev.meta.ai/docs/models), [selection](https://dev.meta.ai/docs/choose-a-model), [structured output](https://dev.meta.ai/docs/structured-output).

Recommended use: Spark extracts candidate claims with entity, attribute, value, scope, validity time, source and uncertainty. Wonder is an escalation option if a real difficult reconstruction justifies it. Validate accuracy on our examples before selecting a default.

Add one short video only if it contains missing operational evidence: a screen walkthrough of a renewal, an approval step, or an explanation of an exception. Capture what was visible, what was said and what the model inferred as distinct records. A timestamp is a pointer to inspect, not proof of accuracy. A demonstration of one exception must not become universal authority.

Meta's media guide supports reading video together with its audio. Its model selection guide warns of degraded audio quality on Spark 1.3 and suggests Spark 1.2 or Voice Transcribe for audio workloads. Pilot an actual clip; do not process an entire archive on assumption. [Media](https://dev.meta.ai/docs/media-understanding), [audio caveat](https://dev.meta.ai/docs/choose-a-model).

## SubQ: reduce expensive work without hiding contradictions

Snap's Decisions API returns typed decisions/probabilities rather than open-ended explanations. That suits a routing gate. [Decisions API](https://docs.subq.ai/endpoints/decisions-api/).

1. Normalize entities, units, dates and aliases; retain the original claim and source.
2. Generate candidate comparisons using entity + attribute + compatible scope/time, with semantic neighbors for uncertain matches. Deterministic duplicate and numerical checks happen first.
3. Send evidence bundles to Snap with fixed options: consistent, contradictory, different scope/time, insufficient evidence. Keep the candidate/source IDs outside the classifier for traceability.
4. Escalate contradictions, ambiguity and critical claims to a generative model or human. A low conflict score cannot silently authorize an action.
5. Audit a sample of filtered-out candidates; evaluate cross-group misses. Partitioning can lose conflicts before Snap sees them.

Measure candidate recall and classification recall separately. Compare the same blocked candidates with (A) direct generative review and (B) Snap plus selective escalation, using the same labeled set. Report total tokens, money, latency and missed conflicts. Cost falls only if the Snap cost is smaller than the generative work avoided; it is not guaranteed. No percentage saved is claimed yet.

## Google: apply the five patterns to the real task

The supplied builder guide recommends Argon for architecture/coding, Flash for smaller tasks, Interactions API for new integrations and an event-provisioned account. These are guide capabilities, not confirmation of our account access. [Google guide](https://docs.google.com/document/d/1kN0n6hPNNTIHMVqf5-hDACrZuIg4KFrWiYpla4WQW8w/edit).

1. **Intent first:** give Argon one engineering brief: the tool contract, repository boundaries, available sources, budgets and the owner decisions it cannot make. Confirm access and settle consequential ambiguities before a long run.
2. **Verification loop:** record the baseline; expose development tests and feedback. Freeze independent validation, with a final test set the builder never sees. Repeatedly optimizing against the same revealed cases is not held-out validation.
3. **Multimodal references:** use Meta to ingest the business recording; use Argon on a recording of our broken UI/test run when visual debugging is needed. Each serves a different concrete job.
4. **Orchestration:** Argon owns interfaces and integration; Flash can take a bounded leaf task after the contracts are fixed. Add media models only if the product needs their output. Start with one worker and one verifier before expanding.
5. **Lessons:** propose a versioned skill or AGENTS.md change after a failure, evaluate it, then adopt it. Unverified lessons stay candidates. Generate an architecture walkthrough from the implemented system for the demo.

Our subscription CLI access and the event/API route are distinct. Decide which route will actually power the demo; do not make a server depend on unverified subscription automation.

## Fetch.ai Deputy CEO

Deputy CEO is an interface to governed actions, not an unrestricted database shell. Suggested tools: summarize_state, explain_conflict, propose_goal_change, propose_rule_change, request_build, get_evaluation, approve_version and revoke_authority. Enforce identity, scope and permissions in the application. Approval is bound to an authenticated owner and an exact version; chat text alone is insufficient.

The agent assembles a brief from the database, asks for the consequential decision, dispatches a bounded job, and returns a linked evidence bundle. It cannot approve its own expansion of authority. For long work, return a run ID and retrievable progress rather than a fictitious immediate completion.

Fetch's guide requires Agentverse registration, Agent Chat Protocol, discovery and a complete primary workflow within ASI:One, plus a public runnable repository. Interactive cards are optional. It also requires a separate submission through the event's ASI:One submission agent. [Fetch guide](https://docs.google.com/document/d/1z7ybvx9I80KI-n4DEieN9i11Zoj4ki4TTvtUWqnULQQ/edit).

## The confirmed upper framework: five areas, two directions each

| Area | See and preserve | Direct |
|---|---|---|
| Purpose | Shared model, provenance, memory and unknowns | Owner's mission and boundaries |
| Rules | Emergent practices, exceptions, contradictions and counterexamples | Explicit policies, permissions and acceptance criteria |
| Resources | Spend, repeated work, recovery and human attention used | Budgets, priorities and autonomy limits |
| Relationships | Commitments to customers/people and unresolved expectations | Representation, owner voice and escalation |
| Progress | Failures, experiments, measured learning and regressions | Goal tree, delivery and adoption/rejection of changes |

This is an organizing lens for Deputy CEO and the overview, not a promise to finish ten modules today. Show received → interpreted → applied → observed for a human decision. Repeated behavior may support a culture hypothesis; a single anomaly does not establish a norm.

## Demo story: one complete cycle

All figures and records below are illustrative until replaced by authorized evidence.

1. Owner: rebuild the renewal tool, preserve approval limits and existing customer commitments.
2. Meta extracts one written rule and a conflicting practice from a short recording. MongoDB preserves both sources.
3. Candidate matching and SubQ flag the conflict; Deputy CEO brings the evidence to the owner. Owner clarifies the rule's scope.
4. Argon builds the tool. A development test exposes the bad assumption that the newest record always wins.
5. The system proposes a versioned change to its evidence-resolution skill: check validity time, scope and authority before precedence. A repeated shortcut is shown as a culture hypothesis if there are enough observed examples.
6. An independent evaluator checks unseen cases plus regression invariants. A useful candidate is eligible for adoption; a tempting shortcut that discards conflicting evidence is blocked. Show actual results, including failure if the candidate does not improve.
7. Owner accepts the validated version within scope. Deputy CEO runs the tool on a new case and shows its outcome, evidence, cost and active rule version. A rollback restores a known previous version if a release fails.

The memorable moment: the owner corrects a principle once, and the audience sees a new executable behavior pass a test the builder did not write for itself.

## Narrative / mythic frame — a proposal

**The Ship of Theseus, with a human at the helm.** The organization replaces its planks — code, skills, context and workers — while underway. Theseus preserves the chain of decisions that explains why it is still carrying out the owner's mission. Deputy CEO is the first officer; it helps the captain exercise authority rather than becoming the captain.

This metaphor is a framing device, not an argument that identity or safety is solved. Public language remains concrete: mission, evidence, commitments, tests and authority. Do not force a nautical UI or mythological role names onto the implementation.

Candidate external line: **Theseus Control Plane — let your agents improve the system, while you decide what must remain true.**

## Scope and approval

Recommended core: one source-backed software slice, one learning loop, one independent gate, one Deputy CEO conversation. Video is a bounded evidence input if relevant. A general agent marketplace, full company migration, full video archive and elaborate dashboard are outside the first demo.

Next approval should settle the concrete process/dataset, primary challenge and this build sequence. No publishing, model calls, cloud provisioning or uploads are implied by this proposal. After approval: freeze the contract/evaluation → validate provider access → implement the slice → run the improvement cycle → expose it through ASI:One → package evidence and publish.
