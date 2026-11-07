# Theseus — 60 s video

Setu.Hackathon · task D01 · November 7, 2026, 13:53 PST.

Owner decisions: HyperFrames is the tool («но гиперфрейм вроде бы праивльно выбрал … берем»); generation waits
(«но генерацию не начинай пока - щас мы дообсудим с вивекой план демок и интерфейс утвердим и дальше двинемся»).
Nothing here has been checked, snapshotted, rendered or voiced yet.

- `index.html` — HyperFrames 0.8.188 composition, 1920×1080, 60 s, seven scenes from `reports/2-scenarios/DEMO-CHORD.md`
  (opening · codex and goals · culture · conflict · three levers · over time · close). Firny visual language: snow
  background, navy ink, glacier blue, amber for what is rebuilt; Geist, Instrument Serif, Geist Mono. Logo v8.
- Explainer scenes only. Live screen recordings of the running system are added after the demo interface is approved.
- Placeholders in amber mono `[ ]`: the goal from the founder's source, the count of discount conversations. The step-5
  chart is a labeled simulation with placeholder curves until the simulation runs.

Production plan (proven on Firny's videos, `~/Projects/anthropic-snowflake-hackathon/video/VIDEO_PLAYBOOK.md`):
`npm run check` → `npx hyperframes@0.8.188 snapshot` → look → `npm run render`. Voice: Gemini 3.8 Flash TTS (Google is a
partner), ElevenLabs `eleven_v3` as backup; music optional. Keys come from a secret store, never from files or chat.

## Draft run 1 — placeholders and voice (owner, 14:5x: «давай сделаем первый прогон с заглушками экрана - лого - чтобы понять как звук ложится … берем женский голос»)

- Order from `reports/2-scenarios/SCENARIO-S01-S06.md`: opening 0–7 s → S01–S06 as placeholder product windows with
  the logo and burned captions (7–45 s) → close with the banner line (45–52 s) → models-and-tools slide from Viveka,
  `assets/tech-slide.png`, last 8 s (owner: at least 5 s at the end).
- Voice: `tts/tts.py`, Gemini 3.8 Flash TTS, female voice Kore, key from `cortex secret` → `assets/voiceover.wav`
  (not committed). Renders go to `renders/` (not committed).
- The earlier explainer skeleton is in Git history (commit f46fd90).

## Draft run 2 (owner, 15:0x)

- Subtitles: «тот текст который и так внизу подписями показываешь … сделать просто читаемыми субтитрами как их обычно
  делают». Big headlines on the opening and close stay. Screen scenes get sentence-level subtitles: white bold text on a
  dark translucent box, raised above player controls.
- New thesis after S01: "From then on, hundreds of agents and people work at once. And you no longer have to watch them
  by reading hundreds of chats." Visual: a field of chat and agent-action chips that dims as the logo appears.
- All lines sped up ×1.12 (pitch kept) to fit. `tts/build.py` now synthesizes missing lines, places them, mixes the
  voice-over and rewrites scene timings, the SCENES block and subtitles in `index.html`; rerun it after any text change.
