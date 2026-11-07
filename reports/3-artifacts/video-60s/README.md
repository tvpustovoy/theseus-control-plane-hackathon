# Theseus — 60 s video (skeleton, not rendered)

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
