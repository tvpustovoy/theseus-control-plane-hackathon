# Theseus — 60-second video: what is on each screen (for Viveka and Argon)

Setu.Hackathon · November 7, 2026, 16:17 PST · current cut = run 4
(`reports/3-artifacts/video-60s/renders/video-60s_2026-11-07_16-14-03.mp4`, commit ec837b0).
Owner request: «подготовить его для viveka чтобы он точно понимал что там будет и какие части должны быть на каких
слайдах».

**How the video works.** One goal runs through every scene: grow sales, protect margin, keep the culture. Voice is
ElevenLabs Sarah. Subtitles repeat the voice (not on the tools slide); text on screen is separate from the voice.
Screens come from three sources: **live** = capture of `http://127.0.0.1:8765/#Sxx` at 1280×800, shown 1216×760 in
the video; **drawn** = built inside the video (HyperFrames); **slide**. Each screen is on air 4–9 s, so the elements
listed under "must be visible" have to be readable at first glance, above the fold, without scrolling or clicking.

## Scene by scene

| # | Time, s | Scene | Source | Voice (= subtitles) | Must be visible on the screen | Owner · state |
|---|---|---|---|---|---|---|
| 0 | 0.0–6.9 | Opening | drawn | "Your AI-native organization changes every hour. How do you notice it's no longer what you intended?" | logo v8 left; banner line "Let AI employees improve your company. *Keep your goals, rules, and culture.*"; THESEUS CONTROL PLANE | Setu · done |
| 1 | 6.9–13.2 | **S01 · Commit** | live `#S01` | "Theseus starts with your commitment: grow sales, protect margin, and keep the culture." | goal *Protect margin while growing sales*; principle (customer commitment for every discount); culture to protect; risk as a **hypothesis**; "monitoring is partial: discount outcomes are missing"; button *Confirm direction & monitoring scope* | Argon · **captured**, passed Viveka's review |
| 2 | 13.2–21.2 | Thesis | drawn | "From then on, hundreds of agents and people work at once. And you no longer have to watch them by reading hundreds of chats." | overlapping chat windows and agent terminals, then the ship | Setu · done |
| 3 | 21.2–24.7 | **S02 · Culture** | live `#S02` | "It watches what agents and people actually do." | "0 of 6,102 CRM deals record discount outcome or reason"; supporting examples and counterexamples; the simulated baseline clearly labeled **Simulation** | Argon · **captured**, passed Viveka's review |
| 4 | 24.7–29.9 | **S03 · Drift** | live `#S03` — placeholder now | "And flags where behavior may drift from it, or where the evidence is missing." | committed principle next to the observed practice; the **current five SubQ Snap 1.1 comparisons** with their real verdicts (different scope/time, insufficient evidence) and the line "no proven contradiction"; the missing-evidence reason (CRM does not record discount outcomes); model/rubric version. Not the older pilot. | Argon · **waiting**: show the new SubQ packet, then Viveka recheck |
| 5 | 29.9–37.8 | **S04 · Correction** | drawn | "It proposes one fix on three levels: the agents' memory, the sellers' training, and the CRM itself." | top: decision card "One decision: *a discount must buy value*" with Approve / Revise / Reject; below three streams: **people** (manager × seller 1:1 talk), **agents** (`agent-112/memory.md` diff: offer 10% → a discount must buy value: longer term · prepayment · referral; otherwise ask a human), **environment** (dev agent adds required `discount_justification`, test "discount without a reason → rejected") | Setu · done. For the live demo Argon's `#S04` should show the same three changes; "Before" values labeled Simulation |
| 6 | 37.8–41.8 | **S05 · Decision** | live `#S05` — placeholder now | "You approve. Checks run before anything applies." | exact candidate version (v2) and the Approve action; the **checks list** with results; activation state separate from approval; demo CRM field *Discount justification* required | Argon · **waiting**: Viveka found that the same 5% discount without commitment passes v1 and v2. If not fixed by the cut-off, the capture shows approval + checks only, not a CRM before/after |
| 7 | 41.8–46.0 | **S06 · Outcome** | live `#S06` — placeholder now | "Then it tracks, in simulation, whether the change works." | **SIMULATION** label; matched before/after runs (same synthetic leads and seed, W1–W4); the main metric with its denominator (e.g., share of discounts with a value reason); separate lines per lever (agents, modeled human sellers, environment); Keep / Roll back; no `undefined` | Argon · **waiting**: Viveka found `undefined` metrics |
| 8 | 46.0–50.6 | Close | drawn | "Theseus doesn't slow your company down. It shows you where it turned." | logo v8; banner line; THESEUS CONTROL PLANE | Setu · done |
| 9 | 50.6–60.0 | Models and tools | slide (drawn) | "Built with OpenAI Codex, Claude, Gemini, Meta, SubQ, Fetch.ai, and MongoDB." | seven rows: OpenAI Codex (Viveka), **Claude Code (Setu)**, Gemini 4 Argon via Antigravity (Argon), Meta via Muse Code, SubQ Snap 1.1, Fetch.ai / ASI:One, MongoDB Atlas; footer "Latest five SubQ checks: no proven contradiction. Outcome comparisons are labeled simulation." | Setu · done; Claude mark `reports/3-artifacts/video-60s/assets/partners/claude.svg` for Viveka's PPTX |

## What I need, by 16:40 PST

1. A ready signal per screen (`#S03`, `#S05`, `#S06`) after Viveka's recheck — I capture at 1280×800 and re-render in
   about two minutes.
2. If a screen is not ready by 16:40, I draw that scene inside the video from verified facts only (as S04), with the
   same voice line.
3. No revenue figures anywhere; the simulation is deterministic code actors and is labeled as such.

Rebuild after any text change: `cortex secret run --map elevenlabs_api_key=XI -- python3 tts/build.py --engine eleven
--tempo 1.0`, then `npx hyperframes@0.8.188 render` in `reports/3-artifacts/video-60s/`.
