# Theseus Control Plane — demo scenario on the six product states S01–S06 (v2)

*Setu.Hackathon · task D01 · November 7, 2026, 14:33 PST. Rebuilt on the field map from Viveka.Hackathon (owner request:
«передай то что мы запланировали Сету - чтобы он сценарий делал опираясь на эти поля») and
`reports/2-scenarios/DEMO-INTERFACES.md`. Supersedes the beat table in `DEMO-CHORD.md`; the chord itself is unchanged.
Product actions below are acceptance targets for the screens Argon builds, not claims that they already work.*

**Operator:** our agents press the buttons (owner, 14:36: «сами и нажимайте на кнопки»). Setu drives the Theseus website
in recordings and on stage; the human role in the story is the founder, addressed as "you". The Deputy CEO guides and
explains.
**Surfaces:** a compact ASI:One card (Fetch Deputy CEO) and the full Theseus website record — same record ID and version
on both. Card→website navigation and localhost links in ASI:One are **untested**; the honest fallback is a browser tab
Taras opens directly. The hosted Deputy is text-only and not backend-connected today.

## Readiness labels

`live` — runs on stage against the product · `recorded` — a real run captured earlier today · `fixture` — product screen
on prepared data, labeled · `simulation` — computed synthetic run, labeled SIMULATION. Every number on screen carries its source/version and observed / inferred / simulated.

## Core lines

- Question: *When your AI-native organization keeps changing — thousands of agents and people at work — how do you notice
  it no longer matches what you intended, without slowing it down?*
- Promise (banner wording): **Let AI employees improve your company. Keep your goals, rules, and culture.**
- Loop: **Commit → Observe → Decide → Track → renew the commitment at the next meeting.**

## One record chain across all six frames

Placeholder IDs — replace with the product's real ones before capture. The same IDs appear on the card and the website.

| Object | Placeholder | Created in | Used in |
|---|---|---|---|
| Meeting source | `MTG-1` | before S01 | S01 |
| Committed mandate: intent, goal, principle, guardrail, scope | `MANDATE-1 v1` | S01 | S03, S06 |
| Culture pattern | `PAT-1` | S02 | S03 |
| SubQ review | `REV-1` (rubric `RUB-1 v1`) | S03 | S04, S06 |
| Correction proposal (three diffs) | `PROP-1`, candidate `v2` | S04 | S05 |
| Activation record | `ACT-1` | S05 | S06 |
| Simulation runs | `SIM-1` (before) / `SIM-2` (after, same leads and seed) | S06 | S06, next Commit |

## 3-minute live script

| Time | Frame | Spoken (draft) | ASI:One card fields | Full Theseus screen fields | Operator does (as the founder) | Visible result | Readiness now → target |
|---|---|---|---|---|---|---|---|
| 0:00–0:20 | **Opening** (logo v8) | "Your AI-native organization changes every hour — thousands of agents and people, each making a sensible local choice. Like the ship of Theseus, plank by plank, it becomes a different ship. How do you notice it no longer matches what you intended — without slowing down?" | — | — | — | Logo v8, question | slide, ready |
| 0:20–0:50 | **S01 · Commit** | "It starts where a founder actually sets direction — a meeting. The Deputy drafts what it heard: the intent, the goal, the principle — discounts can be flexible, but never a substitute for value — and the culture to protect. You edit it and commit. Now Theseus has a mandate: what it watches, with what coverage. And note: saved is not the same as watching." | intent · goal · governing principle · cultural guardrail · proposed monitoring scope | cited meeting source `MTG-1` · editable draft · owner · version `MANDATE-1 v1` and effective time · scope and cadence · data coverage · **actual monitoring state** (configured / partial / active) | edits one field, clicks **Commit** | committed version and effective time appear; monitoring state shows its real value, not "active" by default | not built → `live` UI; intent, goal and principle extracted from the founder Vladimir's own texts via the Meta Model API (owner: the words are in the texts; attach the source episode) |
| 0:50–1:15 | **S02 · Culture** | "Then it watches what people and agents actually do. Here is a practice that keeps coming back: discounts raised as the first answer to a price objection — this many times, across this many people, out of this many conversations. Here are examples — and counterexamples. Observed culture is not policy, and a request is not a granted discount." | emerging practice · frequency / denominator · evidence status | independent episodes and actors · examples · counterexamples · source drawer (`PAT-1`) | opens one episode in the evidence drawer | source, quote location and actor type shown; requests and granted discounts counted separately | not built → `live` UI on `observed` counts from the Meta extraction over the imported data |
| 1:15–1:40 | **S03 · Drift** | "Now the moment that matters: the committed principle next to the behavior. SubQ checks it against the version you approved — and it may say 'contradicts', or honestly 'insufficient evidence'. You can challenge it." | applicable committed rule · selected behavior · SubQ verdict | reference `MANDATE-1 v1` and effective period · scope · citations · rubric `RUB-1 v1` and model version · verdict among consistent / contradicts / different scope / insufficient evidence | reads the basis; accepts or challenges the interpretation | `REV-1` with its verdict; a compact five-area reading of the issue (Purpose · Rules incl. culture · Resources · Relationships · Progress) | a real SubQ call has been made → `live` or `recorded`; "insufficient evidence" is shown if that is the true verdict |
| 1:40–2:05 | **S04 · Correction** | "The Deputy doesn't just report — it proposes one correction on three levels. For the sales agents: a rule change. For the human sellers: an onboarding section. And for the environment: one required field in our demo CRM — why this discount? Nothing activates silently." | one proposed correction · affected areas | three diffs: agent rule/skill v1→v2 · human onboarding section · required `discount_justification` field in the demo CRM · rationale · dependencies and resources · affected people (`PROP-1`) | inspects each diff | three diffs side by side, candidate `v2` marked "proposed" | offline proposal tools exist → `live` UI; Fetch card `live` only if the bridge is connected, else the app card, labeled |
| 2:05–2:30 | **S05 · Decision and application** | "You approve this exact version. Approval is not activation: checks run first, then it applies. Watch the CRM: a discount without a reason is rejected; with a reason, it goes through." | exact candidate version · actual status | approve / revise / reject · permission and check results · activation state · audit evidence (`ACT-1`) · demo CRM form | clicks **Approve v2**; tries a discount without a reason, then with one | checks pass, status goes approved → applied; CRM rejects the empty reason and accepts a valid one; received → understood → applied shown, observed still pending | offline activation/rollback exist → `live` in the demo environment; onboarding stays "proposed" unless actually delivered |
| 2:30–2:50 | **S06 · Outcome** | "And then Theseus tracks it. This is a simulation — same leads, same seed, before and after. The share of discounts with a value reason moved from Y to X. The agents changed at once; for human sellers we only show what the simulation models. You can keep it, roll it back, or take it to the next meeting." | run status · main measured change | **SIMULATION** label · matched runs `SIM-1`/`SIM-2` · metrics with denominators · committed and intervention versions · keep / rollback state | chooses **Keep** (or rolls back) | the chosen state is saved; "observed in behavior" filled for the simulated run; a link back to Commit for the next meeting | harness exists (12/12 tests, five arms, modeled agent and human actors) → `simulation`, MongoDB-backed and drawn in the UI |
| 2:50–3:00 | **Close** | "Theseus doesn't slow your company down. It shows you where it turned. Let AI employees improve your company — keep your goals, rules, and culture." | — | partner slide (one) for 3 s, then banner line | — | logo v8 + banner line + repo URL | slide, ready; partner rows only for real calls |

Optional, before S01 or in Q&A: **import receipt** — 53,431 raw records copied as-is into MongoDB Atlas, counts and
digests reconciled (`recorded`, verified by the coordinator at 14:13). No private raw records on screen.

## 60-second video — shots from verified frames

| Time | Shot | Voice-over |
|---|---|---|
| 0–6 s | Logo v8 | "Your AI-native organization changes every hour. How do you notice it's no longer what you intended?" |
| 6–14 s | S01 Commit: Commit click, version and monitoring state | "Theseus starts with a commitment: your goals, your principles, the culture to protect." |
| 14–22 s | S02 Culture: pattern with denominator, evidence drawer | "It watches what agents and people actually do." |
| 22–30 s | S03 Drift: SubQ verdict beside the committed principle | "And shows where behavior drifts from what you committed to." |
| 30–38 s | S04 Correction: three diffs | "It proposes one fix on three levels: agent rules, people's onboarding, the environment." |
| 38–46 s | S05: Approve, CRM rejects a discount without a reason | "You approve. Checks run. The new rule applies." |
| 46–54 s | S06: SIMULATION before/after, Keep | "Then it tracks whether the change actually worked." |
| 54–60 s | Banner line + logo | "Let AI employees improve your company. Keep your goals, rules, and culture." |

Production: HyperFrames composition (`reports/3-artifacts/video-60s/`) with the screen captures placed into it; voice
Gemini 3.8 Flash TTS, ElevenLabs as backup. Generation waits for the owner's approval of the interface.

## Partner slide (one)

| Partner | Job in Theseus | Shown only if |
|---|---|---|
| Meta | meeting and conversation extraction with citations | in use via the Meta Model API |
| MongoDB | raw layer, versions, decisions, runs | verified (import receipt) |
| SubQ | drift review against the committed rubric | real call made |
| Gemini / Antigravity | built the app and backend; drafts the correction | true today (development use) — runtime use only if called |
| Fetch.ai | Deputy CEO in ASI:One | hosted agent verified; cards/bridge only if tested |

## Readiness gaps (14:37 PST, after the owner's answers)

Owner, 14:36: Meta works through the API («мы уже работаем через API - все ок»); one SubQ call has been made («уже был
один вызов»); the value principle is Vladimir's own words from the texts («считаем что мы их там нашли»).

1. **Theseus UI, all six states** — Argon building; capture needs the localhost address and a stable route per frame.
2. **Demo CRM validation** in S05 — target; not yet in the backend.
3. **S06** — simulation harness exists; needs MongoDB-backed runs and the chart.
4. **Fetch cards and card→website navigation** — untested; fallback is the browser tab.
5. **Real record IDs** for the chain above, and the source episode for Vladimir's principle — from Argon and Muse before
   capture.
