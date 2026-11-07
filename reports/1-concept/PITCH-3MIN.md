# Theseus Control Plane — 3-minute live pitch (draft v0)

> **Superseded at 13:31 PST by `reports/2-scenarios/DEMO-CHORD.md`** (owner's demo chord: codex → culture → conflict → proposal for people, agents and environment → tracking over time). Kept as history.


*Setu.Hackathon · task D01 · November 7, 2026, 12:57 PST. Draft for owner review. Every line marked `[E#]` depends on
evidence listed in `reports/3-artifacts/EVIDENCE-GAPS.md`; if that evidence is not real by the cut-off, the line is cut or
said as "planned", never shown as working.*

Judging (round 1): ~3 min live demo + 1–2 min questions. Weights: technical demo 35%, complexity 30%, usefulness 20%,
creativity 15%. So: two-thirds of the time is the live system, not slides. The product must not read as a dashboard.

## Core line

**Theseus Control Plane — let your agents improve the system, while you decide what must remain true.**

## Timeline

| Time | Beat | On screen | Spoken (draft) |
|---|---|---|---|
| 0:00–0:20 | **Hook** | Title slide: ship, one plank highlighted | "Agents now rewrite our software every day. Code, skills, context — plank by plank. The old question returns: when every plank is replaced, is it still your ship? We built the part that keeps it yours." |
| 0:20–0:35 | **What it is** | One-line loop: source → claim → decision → build → held-out check → adopt or roll back | "Theseus is a control plane for an organization of agents. Agents propose improvements. Nothing is adopted until it passes cases the builder never saw. The owner decides what must stay true." |
| 0:35–0:55 | **Demo 1 · Evidence** | Meta extraction with cited span; MongoDB record; SubQ flags a conflict `[E1][E2][E3]` | "We start from real process sources. Meta Muse extracts claims with citations. MongoDB keeps every source and version. SubQ Snap flags where two sources contradict each other — cheaply, before any expensive reasoning." |
| 0:55–1:15 | **Demo 2 · Owner decision** | Deputy CEO in ASI:One asks one question; owner answers `[E7]` | "The Deputy CEO, an agent on Fetch.ai, does not decide. It brings the owner one question with evidence. The owner clarifies the rule once." |
| 1:15–1:35 | **Demo 3 · Build and failure** | Argon diff; a development test fails `[E4]` | "Gemini 4 Argon builds the tool. A test fails: the agent assumed the newest record always wins." |
| 1:35–2:05 | **Demo 4 · Improvement gate** — the memorable moment | Versioned skill change; held-out before/after; tempting shortcut blocked `[E5]` | "The system proposes a versioned fix to its own skill. An independent check runs cases the builder never saw. The real fix passes. A shortcut that just drops conflicting evidence scores well on the dev tests — and is blocked." |
| 2:05–2:20 | **Demo 5 · Adopt and roll back** | Owner accepts version N+1; new case runs; rollback restores N `[E6]` | "The owner adopts it. The tool runs a new case and shows which rule version it used. One command rolls it back." |
| 2:20–2:45 | **What is real** | Partner table: five products, what each did today, one number each `[E8]` | "Built today, all five partners do a real job: Meta extracts, MongoDB remembers, SubQ filters conflicts, Gemini builds and improves, Fetch.ai carries the owner's voice." |
| 2:45–3:00 | **Close** | Core line + repo URL `[E9]` | "Your agents can replace every plank. Theseus makes sure the ship still goes where you said. Let your agents improve the system — you decide what must remain true." |

## Fallback cut (if the full cycle is not live by the cut-off)

Decide at the cut-off (proposed 15:30 PST) which beats are live. Rules:

- A beat whose evidence exists only as a recorded run is shown as a recording and called "recorded earlier today".
- A beat with no evidence is dropped from the demo and named once in "What is next", with no screenshot.
- Minimum viable demo, in priority order: **Demo 4** (held-out gate, it carries the problem statement) → Demo 1 →
  Demo 3 → Demo 5 → Demo 2. If only Demo 1 works, the pitch switches to the Software Archaeology framing only with the
  owner's word; we do not claim The System That Gets Better without a held-out result.

## Words to avoid on stage

- "dashboard", "monitoring" — the main function is the adoption gate, not viewing.
- "fully autonomous", "self-governing" — the owner decides; agents propose.
- Any percentage or saving not measured today.
- The client's name or any raw client record (see `EVIDENCE-GAPS.md`, data handling).

## Two candidate demo stories — the beats above fit either

The project documents hold two plans; neither has run yet (coordinator, 12:56 PST).

| Beat | A · Spending-limit conflict (`docs/ARCHITECTURE.md`, "First demo boundary") | B · Renewal/discount service (`docs/FRAME.md`, "Demo story") |
|---|---|---|
| Demo 1 · Evidence | Two sourced claims disagree on a spending limit (synthetic) | A written rule and a conflicting practice from real sources |
| Demo 2 · Owner decision | Owner picks the limit and its scope | Owner clarifies the rule's scope |
| Demo 3 · Build | A scoped agent role is compiled from the decision | Argon builds the tool; a development test fails |
| Demo 4 · Gate | In-scope action runs; out-of-scope attempt is blocked | Versioned skill fix passes held-out cases; shortcut blocked |
| Demo 5 · Adopt / roll back | Proposed scope approved as an exact version | Version N+1 adopted; rollback to N |
| Best-fit track | Trust but Verify (authority enforcement) | The System That Gets Better (held-out improvement) |

A is smaller and synthetic, so it is more likely to run by the cut-off. It does not by itself show a versioned
improvement checked on held-out cases, which the primary track asks for. A + one improvement cycle on the same limit
rule would cover both. Choice belongs to the owner.

## Open for the owner

0. Story A, B, or A plus one improvement cycle.
1. Who speaks the 3 minutes and who drives the screen.
2. Whether the real client and process (renewal/discount decision) may be named on stage, or stay "a real company's
   sales process". Client data moves to MongoDB by the owner's decision of November 7; publication of raw data is not
   authorized (`docs/RECPLACE-SOURCES.md`, `docs/DATA-HANDLING.md`).
3. Cut-off time for freezing the demo (proposed 15:30).
