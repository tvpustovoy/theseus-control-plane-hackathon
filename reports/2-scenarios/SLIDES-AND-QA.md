# Theseus Control Plane — slides and Q&A (draft v0)

> **Superseded at 13:31 PST by `reports/2-scenarios/DEMO-CHORD.md`** (owner's demo chord: codex → culture → conflict → proposal for people, agents and environment → tracking over time). Kept as history.


*Setu.Hackathon · task D01 · November 7, 2026. Slides support the live demo; they are not the demo. Seven slides at
most, so that at least two of the three minutes stay on the running system.*

## Slides

1. **Title.** Theseus Control Plane. "Let your agents improve the system — you decide what must remain true." Team names.
2. **Problem.** Organizations of agents now change their own code, skills and context daily. Each change is local; the
   mandate drifts silently. Track: The System That Gets Better.
3. **The loop.** One diagram: source → cited claim → contradiction flag → owner decision → build → development failure →
   versioned improvement → held-out check → adopt or roll back. Every owner decision passes four states: received →
   understood → applied → observed in behavior.
4. **Live demo.** Switch to the system.
5. **Evidence.** Held-out before/after for the candidate and for the blocked shortcut; rollback shown. Numbers only from
   today's runs `[E5][E6]`.
6. **Five partners, five jobs.** Meta — extraction with citations · MongoDB — sources, versions, decisions · SubQ —
   contradiction filter · Gemini — build and improvement loop · Fetch.ai — Deputy CEO in ASI:One. One proof per row `[E8]`.
7. **Where it goes.** The light framework above the loop: Purpose, Rules, Resources, Relationships, Progress — what the
   owner sees and preserves, and what the owner directs. Built today vs. prepared before. Repo URL.

## Q&A — likely questions and draft answers

| Question | Draft answer |
|---|---|
| How is the held-out check independent if your own system built it? | The final cases are kept outside the builder's workspace and written by a separate verifier; once revealed they become regression tests, not held-out. *Depends on E5: the independent verifier is not yet assigned.* |
| What did you build today and what existed before? | Code written today: `[list from E10]`. Prepared before: role packets, contracts, the five-area framework as an idea. Earlier projects (FIRN and others) are prior work and not part of today's code. |
| Is this a dashboard? | No. The main function is the adoption gate: a change is adopted or blocked on evidence, and can be rolled back. Views exist only to support that decision. |
| Why five partners — isn't that a sponsor checklist? | Each does one job the loop needs and has one proof: extraction, memory and versions, cheap conflict routing, building and improving, the owner's channel. If a partner's proof is missing, we say so. |
| What if SubQ misses a contradiction? | A low conflict score never authorizes action on its own. Critical claims escalate to a generative model or the owner; we measure missed conflicts on labeled cases `[E3]`. |
| How do you stop the agent from approving its own authority? | Approval is bound to the authenticated owner and an exact version; the Deputy CEO can only propose. Chat text alone is not approval. |
| What is "culture" in your system? | Repeated behaviors that were never approved as rules. We show them as hypotheses with examples and counterexamples; one anomaly is not a norm. |
| Whose data is this? Can we see it? | A real company's sales process, used with permission inside our environment. Public artifacts use synthetic or redacted inputs only. |
| What does it cost to run? | Report only measured tokens and money from today's runs `[E3][E5]`; no projected savings. |
| Who is the customer? | A founder or operator running an organization of agents who needs to keep the mandate while agents change the system. First case: our own work with a real client process. |

Answers marked with `[E#]` are said only if the evidence exists by the cut-off.
