# Theseus Control Plane — evidence the defense still needs (draft v0)

*Setu.Hackathon · task D01 · November 7, 2026, 12:57 PST. Each pitch beat and video shot is tied to one item here. State
is taken from `docs/status/*.md`, `docs/WORKLOG.md` and `reports/ORGANIZER-UPDATES.md` at 12:55 PST. Owners in this table
are proposals for the coordinator; this file assigns nothing.*

At 12:55 PST no product integration had been run. Argon reported Stage 1 (SCHEMA_READY) started on synthetic fixtures;
Muse Code runs without Ours MCP; the Agentverse agent is waiting for owner login.

| # | Evidence needed | Used in | Likely source | State at 12:55 | Risk |
|---|---|---|---|---|---|
| E1 | One real Meta Model API extraction: request, model version, redacted response, cited source span, one corrected extraction | Pitch Demo 1, video shot 2, slide 6 | Muse.Hackathon | not started; needs API key route and MongoDB source | medium |
| E2 | MongoDB collections with sources, claims, versions; the same decision trace before and after a change | Demo 1, Demo 5, shot 6 | Argon.Hackathon | SCHEMA_READY in progress; target `MONGODB_URI` missing | **high** — blocks E1, E5, E6 |
| E3 | Real SubQ Snap decisions on candidate pairs, with labeled cases, cost and missed-conflict count | Demo 1, shot 2, Q&A | Muse.Hackathon | not started; SubQ key and model availability open (D07) | medium |
| E4 | Argon build diff and a real failing development test | Demo 3, shot 4 | Argon.Hackathon | not started | medium |
| E5 | Versioned skill/context change; held-out before/after; a tempting shortcut that is blocked | Demo 4, shot 5, slide 5 | **independent verifier — unassigned** | not started | **high** — this is the core of The System That Gets Better |
| E6 | Owner adoption of version N+1 and a working rollback to N | Demo 5, shot 6 | Argon.Hackathon + verifier | not started | medium |
| E7 | Deputy CEO in ASI:One: one complete conversation with evidence and an owner decision | Demo 2, shot 3 | Taras + Viveka.Hackathon | brief ready; Agentverse login pending | medium; drop beat if absent |
| E8 | One proof per partner (five rows), from today's runs | "What is real", slide 6 | coordinator collects | none yet | high for partner prizes |
| E9 | Public repository URL | Close, shot 7, slide 7 | Taras (D08) | not published; needs owner's step-by-step confirmation | **high** — submission requires a public repo |
| E10 | Built-today vs. prepared-before list, with prior projects named | Q&A, README | coordinator + Setu | not written | **high** — rule: unclear separation means disqualification |
| E11 | All team members added on the submission page; each approved | Submission | Taras | team approval was not confirmed on November 4 | high |

## Data handling for every artifact

Client data was moved inside by the owner's decision; publication of raw data is not authorized. Screens, video frames,
slides and the public repo show synthetic or redacted inputs only. No keys, database URIs, account emails or private agent
messages in any frame.

## Proposed cut-off

15:30 PST: the coordinator and the owner freeze which beats are live. After that, Setu fills the pitch, video and slides
with real results only (task D02) and drops what is not there.
