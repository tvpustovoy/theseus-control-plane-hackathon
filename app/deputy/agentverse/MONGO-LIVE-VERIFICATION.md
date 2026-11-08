# Deputy MongoDB connection — 7 November 2026

Owner: Viveka.Hackathon. User priority: working live agent first, then dashboards; no video work.

## Completed

- Created `theseus_deputy_demo.memory` in Atlas from the sanitized culture/rules brief: 12 unique claims, one context record and one test record.
- Did not modify raw data or grant the hosted agent access to private source collections.
- Created a temporary collection-scoped read user and a six-hour exact-IP allowance for Agentverse.
- Installed fresh-read reasoning code, with a fixed collection/filter and explicit coverage, provenance and failure boundaries.
- Four offline tests pass: fresh reads on consecutive requests, fixed public-safe scope, no silent overflow, no secret leakage in errors, and honest unconfigured state.
- Verified that the proposed GitHub source URL is not yet published (404); removed it from all demo records. Source identifiers remain available.
- User completed the manual password update; local read with the hosted reader credential returned 14 records. Attempted read of `theseus_recplace.raw_records` was denied (Atlas error code 8000). The broad import credential was never installed in Agentverse.

## Live acceptance — passed 16:48–16:50 PST

- Owner explicitly approved a Cloudflare HTTPS bridge and expanded scope to all RecPlace records. Direct hosted PyMongo blocked; local PyMongo worked. The bridge is the active route.
- Hosted startup log reports `ATLAS_MEMORY_STATUS connected=True`.
- ASI:One fresh count returned **53,431 raw records** at `2026-11-08T00:48:53Z` and ran actual database searches. It cited claim C228-2b8eb61aeb and source src:5ba65d172a9d76ce70ba, separating observed evidence from policy.
- Changed only `connectivity-test` in the demo collection from HARBOR-7 to COMPASS-42 at `2026-11-08T00:49:45.308442+00:00`. The next ASI reply returned COMPASS-42 and the exact update timestamp without a restart.
- A Russian discount-strategy question received an English answer. The agent is configured for English only.
- Public requests without the bridge credential receive HTTP 401. Unauthorized collection, `$where` filter and delete-operation tests were rejected. Seven offline freshness/failure/transport tests pass.
- The original source URL returned 404, so the agent currently cites source/claim identifiers, not a fabricated public source link.
- Commit regression fixed at 16:58 PST: ASI prefixes the incoming command with a mention, so an anchored `Show Commit` matcher fell through to the LLM. The corrected explicit-command matcher renders the native three-row card and includes a plain local-app link. The website opened successfully; the Agree Direction view was verified at #S01. No approval action was taken.
- At 16:59 PST, clicking the native card's **Review direction** button returned the correct `http://127.0.0.1:8765/#S01` link and explicitly said that no approval occurred in chat.

## Remaining boundaries

- This is live read/search, not autonomous policy approval or execution. Use the website for Commit.
- Source/record excerpts are bounded and explicitly marked. Keyword search is not exhaustive semantic analysis.
- Atlas `claims`, `source_chunks` and `extraction_runs` were empty at the checked snapshot, while Muse's extraction packet is local; this discrepancy was reported to the coordinator. Do not label 3,351 local claims as a persisted Atlas count until import is verified.
- The owner ASI gateway is allowlisted. A different conversation gateway requires an explicit identity check before access expansion.

## Important boundary

Live means a fresh Mongo query, not a live stream of the entire company. The source corpus remains a historical import. The small curated brief supplies context; read tools search the full permitted RecPlace collections. The current website state is read from its observed mirror, with version/sync time and demo provenance retained.
