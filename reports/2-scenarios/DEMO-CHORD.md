# Theseus Control Plane — the demo chord: script and demo specifics (v1)

*Setu.Hackathon · task D01 · November 7, 2026, 13:31 PST. Built on the owner's direction in Setu's chat at about 13:30.
This file supersedes the story in `reports/1-concept/PITCH-3MIN.md` and `reports/2-scenarios/VIDEO-60S.md` (kept as
history). Every number in brackets `[ ]` is a placeholder until a real run fills it. Nothing below has run yet.*

## The main question (owner's words, translated)

> When your AI-native organization keeps changing — thousands of agents and people at work — how do you notice that it
> has become different and no longer matches what you intended? You need a **human-facing control plane**, so you keep
> noticing what matters **without slowing down**.

## The chord — five steps, everything else is built around them

1. **Codex and goals.** Extract the codex and the goals from the founder's files, and keep them current from what
   happens, including live meetings (owner, 13:33: «кодекс и цели я бы сказал даже»).
2. **Culture.** Extract the real culture: repeated, significant behavior in the actions of agents and people.
3. **Conflict.** Detect where culture contradicts the codex or works against the goals, and present the change at the
   level of a conflict between laws, goals and culture.
4. **Proposal — three levers, one decision.** Through the Deputy CEO agent, Theseus proposes a correction on three levels
   at once (owner, 13:34: «супер важно»):
   - **Sales agents** — edit their rules: the discount skill gets version 2.
   - **Human sellers** — onboard them: the onboarding gets a section on when a discount is allowed and what it must buy.
   - **The environment** — add a required CRM field "discount justification", which changes behavior by itself because
     every seller and every agent must fill it in.
   We correct the behavior of people and agents by changing their rules, their onboarding and their environment.
5. **Tracking.** Follow each corrective change over time, lever by lever, and show its effect directly: did the culture
   of agents and of people move back toward the codex and the goals?

The case: discounts. Codex: *discounts can be flexible*; *we do not flood people with discounts, substituting price for
value*. Culture found in the deal flow: discounts applied unsystematically, often as the first answer to a price
objection. This is what actually happened in the original project.

## Evidence check, 13:26 PST — what the data supports (Viveka.Datamaster, relayed by the coordinator)

Source references only, no client payload:

- **Codex.** Founder decisions and remarks about discount *conditions* exist in `model.FIELD_FACTS` (episodes 187, 80901,
  79523). A possible "do not offer a discount first" utterance (`core.SRC_UTTERANCES` ep 78324, ord 16) needs attribution
  review. A direct founder statement combining *flexible discounts* with *do not substitute price for value* is **not
  verified** — it needs a source from the owner (e.g. the call with the founders) or is said as the owner's framing.
- **Culture.** Discount requests and reasons appear in conversations (`model.FIELD_FACTS` episodes 960, 964, 765, 81353;
  links in `core.DOC_CRM_LINKS`). They do not prove a discount was applied.
- **CRM.** All 6,102 `raw.CRM_DEALS` rows and `raw.CRM_DEAL_STAGE_EVENTS` have **no discount or reason field**. No CRM
  discount events exist.

**What this changes in the story.** "Discounts are applied unsystematically" stays a hypothesis until today's extraction
measures it. But the CRM finding sharpens step 4: the discount culture lives only in conversations, so the system of
record is blind to it — which is exactly why the environment lever (a required "discount justification" field) is the
right proposal. Proposed wording for step 2 on stage: "Discount talk lives in calls and chats — `[N]` conversations — and
nowhere in the CRM. The rule the founder cares about is invisible to the system that runs the deals."

**Step 5 "over time".** Decided by the owner at 13:41: a labeled simulation with our sales agents on synthetic leads.

## 3-minute live script

| Time | Step | On screen | Spoken (draft) |
|---|---|---|---|
| 0:00–0:25 | **Opening** | Logo v8 (`styles/theseus-logo-v8-spacesuit.png`, owner-selected 13:28): half-rebuilt ship, human at the helm | "Your AI-native organization changes every hour — thousands of agents and people, each making a sensible local choice. Like the ship of Theseus, plank by plank, it becomes a different ship. How do you notice it no longer matches what you intended — without slowing it down? You need a human-facing control plane. This is Theseus." |
| 0:25–0:50 | **1 · Codex and goals** | Founder's files and a meeting transcript → codex and goals with citations; v1 → v2 diff after the latest meeting `[E1][E2]` | "Theseus reads the founder's own words — documents and live meetings — and keeps a living codex and the goals behind it. Here: discounts can be flexible, but we never flood people with discounts in place of value; and the goal is `[goal from source]`. The latest meeting refined it; Theseus shows exactly what changed." |
| 0:50–1:15 | **2 · Culture** | Deal flow → repeated behaviors ranked by how often and how much they matter: "discount as the first answer to a price objection — `[N]` deals, `[M]` sellers and agents" `[E3]` | "Then it watches what people and agents actually do — `[N]` deals, calls and chats — and extracts the real culture: behavior that repeats and matters. Nobody wrote this rule. It grew." |
| 1:15–1:35 | **3 · Conflict** | Codex principle against culture norm; verdict "contradicts"; one-line reading in five areas `[E4]` | "And here is the moment you need: your organization has become different. The codex says one thing, the culture another. Margin is leaking, customers are learning to wait for a discount." |
| 1:35–2:15 | **4 · Proposal** | Deputy CEO in ASI:One proposes three levers side by side — **agents:** discount skill v1 → v2 diff · **people:** new onboarding section for sellers · **environment:** required CRM field "discount justification"; owner approves `[E5][E6]` | "The Deputy CEO doesn't just report — it proposes one correction on three levels. For the sales agents: we edit their rules. For the human sellers: we update their onboarding. And for the environment: one required field in the CRM — why this discount? Every seller and every agent has to answer it before giving one. Behavior changes without a single lecture." |
| 2:15–2:45 | **5 · Tracking** | Timeline per lever (agents · people · environment): share of discounts with a value justification and share consistent with the codex, before and after each change, with markers; keep or roll back `[E7]` | "Then Theseus follows each lever over time. After the field went in, `[X]`% of discounts carried a value reason, up from `[Y]`%. The agents' new rules moved them at once; the people's onboarding is slower — so it stays a candidate. Every change is versioned; anything that doesn't work rolls back." |
| 2:45–3:00 | **Close** | Logo + core line + repo URL `[E9]` | "Theseus doesn't slow your ship down. It shows you where it turned. Let your agents rebuild the ship — keep the helm." |

## 60-second video

| Time | Shot | Voice-over |
|---|---|---|
| 0–8 s | Logo v5 | "Your AI-native organization changes every hour. How do you notice it's no longer what you intended?" |
| 8–18 s | Codex and goals with citations, v1 → v2 diff | "Theseus keeps a living codex and goals from the founder's own words." |
| 18–28 s | Culture: the repeated discount behavior | "It extracts the real culture from what agents and people do." |
| 28–36 s | Conflict card | "And shows where culture contradicts the codex." |
| 36–48 s | Three levers: agent rules v2 · seller onboarding · CRM field appears | "It proposes one fix on three levels: the agents' rules, the people's onboarding, and the environment itself." |
| 48–56 s | Timeline with intervention markers | "Then it tracks whether the change actually worked." |
| 56–60 s | Core line | "Theseus. Let your agents rebuild the ship — keep the helm." |

## Video production (owner, 13:53 PST)

HyperFrames 0.8.188 + GSAP, as in Firny's videos; skeleton at `reports/3-artifacts/video-60s/`. Voice: Gemini 3.8 Flash
TTS, ElevenLabs `eleven_v3` as backup. Generation waits until the owner and Viveka approve the demo plan and the interface.

## Demo specifics, step by step

| Step | Input | What runs | Partner | On screen | Evidence |
|---|---|---|---|---|---|
| 1 · Codex and goals | Founder's files about sales and discounts; one meeting transcript as the "update" | Extract principles and goals with entity, scope, citation; store versions; re-extract on the new meeting and diff | **Meta** (extraction from text; transcript via Meta audio/Voice Transcribe if a recording is used) · **MongoDB** (codex collection with versions) | Codex v1 and v2 side by side, each principle with its quote | E1, E2 |
| 2 · Culture | Deals, stage events, discount events, calls/chats (RecPlace raw in MongoDB, anonymized on screen); and/or actions logged by our sales agents | Extract discount events and the stated reasons; group repeated behaviors (same situation → same action) and rank by frequency, number of actors and money | **Meta** (reasons from conversations) · **MongoDB** aggregation (repetition, actors, amounts) | Ranked list of norms, each with count, actors, examples and counterexamples | E3 |
| 3 · Conflict | Codex principles and goals × culture norms | Classify each pair: consistent · contradicts · different scope · insufficient evidence; escalate contradictions | **SubQ Snap** (typed decisions) · generative check on the escalated ones | Conflict card: principle, norm, evidence, verdict, what is at stake, five-area reading | E4 |
| 4 · Proposal | The conflict card | Deputy CEO presents the conflict and one correction on three levers; on the owner's approval Gemini drafts and Argon applies: **agents** — discount skill v2 (when a discount is allowed, what it must buy, escalate otherwise); **people** — onboarding section for human sellers; **environment** — CRM schema change: required `discount_justification` (longer term · prepayment · referral · volume · other with text) | **Fetch.ai** (Deputy CEO in ASI:One) · **Gemini** (drafts; Argon builds the field and the skill) · **MongoDB** (each lever stored as a versioned change) | ASI:One conversation; then three diffs side by side: skill v1→v2, onboarding, CRM form with the new field | E5, E6 |
| 5 · Tracking | Interventions as versioned events; discount events after each | Per period: share of discounts with a value justification; share consistent with the codex; average discount; effect per intervention; keep / roll back | **MongoDB** (time series of interventions and metrics) | Timeline with intervention markers and a verdict per intervention | E7 |

## Where the "over time" in step 5 comes from — decided: simulation (owner, 13:41 PST: «шаг 5 - симуляция да»)

- **Real history.** If the original project's records contain the moment when discount practice or the CRM changed,
  show the real before/after. Strongest; needs the owner to point to that moment and confirm it is in today's import.
- **Simulated weeks with our sales agents.** Run a small set of sales agents on synthetic leads built from real deal
  patterns: `[k]` simulated weeks before the CRM field, `[k]` after. Their logged actions feed step 2, so "culture from
  agents' actions" is literal. Must be labeled "simulation" on screen.
- Both: real history for the people's culture (steps 2–3), simulation for the intervention effect (step 5).

## Minimum that must run by the cut-off (proposed 15:30 PST)

Steps 1–3 on real data with real Meta, MongoDB and SubQ calls, plus the CRM field change and the step-5 timeline from
one of the sources above. The Deputy CEO conversation in ASI:One is shown live if the Agentverse agent is up; otherwise
the same proposal card is shown in our app and the Fetch.ai part is said as "next". The track claim "The System That
Gets Better" rests on step 5: a versioned change to the environment and the agents, measured, kept or rolled back.

## Data handling

Client data moves into MongoDB by the owner's decision of November 7; raw records are never published. On screen and in
the public repo: aggregates, anonymized examples, synthetic fixtures. Placeholders `[ ]` are replaced only with numbers
from today's runs.

## Open for the owner

1. Source of the founder's words on discounts: which files, and which meeting is the "live update".
2. Is there a real moment in the history when discount practice changed — or do we simulate step 5?
3. Is the CRM in the demo the client's real CRM (we only show a proposed change) or our own demo CRM (we apply it)?
4. Naming the client on stage.
