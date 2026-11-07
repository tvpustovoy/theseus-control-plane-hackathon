# Worker check-ins and shared write areas

Status: coordination protocol prepared November 7, 2026. It records the owner's request relayed to the coordinator by Viveka.Hackathon. A check-in is a status record, not a new implementation assignment.

## When to check in

Muse.Hackathon and Argon.Hackathon should write a short update at the start of an authorized task, after each meaningful checkpoint, as soon as a blocker appears, and before stopping. During active work, aim for another update after roughly 15 minutes without a recent record. Do not create empty repetitive reports. Onboarding and access setup may be recorded as setup, with no task ID or implementation claim.

Each worker self-triggers the approximate 15-minute check-in while actively working; it must not wait for a coordinator timer. Each worker writes **only its own** `docs/status/<identity>.md` in English. Include local timestamp, authorized task/stage (or `onboarding, no implementation task`), completed work, changed file paths, verification performed, blocker or uncertainty, and next step. After saving, send a short Ours pointer to the coordinator, e.g. `STATUS Muse.Hackathon — docs/status/Muse.Hackathon.md updated; blocker: ...`. The Ours pointer is a notification, not the durable report. Do not put credentials or client payloads in either place.

The coordinator checks the file, confirms what was actually observed, and updates shared task state only after the authorization and evidence gates in `docs/COLLABORATION.md`. Keep prepared, assigned, acknowledged, implemented and verified distinct. `git checkout`, a new branch or a commit is not required for each ping.

The live Ours monitor wakes on new mail. It does **not** provide a fixed 15-minute timer. On each later wake, the coordinator checks the last verified timestamps and may remind an active worker when overdue. It can also request a check-in while its session is actively coordinating. It must not claim that automatic timed pings are running or create a permanent automation for this protocol. Record which worker actually received and acknowledged the protocol; a prepared file alone is not delivery.

## Reserved area

`app/deputy/agentverse/` is reserved for the parallel initial Fetch.ai Agentverse agent work by Taras and Viveka.Hackathon. Argon.Hackathon must not edit that area concurrently. This reservation records the work boundary; it does not assert that files already exist or that the Agentverse agent is complete. Before Argon starts later Deputy CEO integration, coordinate handoff of this area with the owner.

No check-in protocol or reserved area authorizes the coordinator to dispatch new implementation work. Taras issues that authorization separately.
