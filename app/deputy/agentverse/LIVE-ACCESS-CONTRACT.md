# Deputy CEO: open-ended questions over current data

Prepared by Viveka.Hackathon, 7 November 2026.

## Live implementation — accepted route at 16:50 PST

Taras expanded the authorized scope to **all RecPlace records** and required English replies. The direct hosted PyMongo attempt did not complete; local Mongo reads succeeded. With explicit owner approval, the working route is:

`owner's ASI:One conversation → hosted Deputy read tools → authenticated Cloudflare HTTPS bridge → MongoDB Atlas`

The bridge binds to `127.0.0.1:18765`. Only its `/memory` and `/query` read operations are tunneled. The application on port 8765 is not exposed. Hosted code receives a bridge token, not the broad Mongo credential. The adapter fixes the database and permits only named collections, literal search, bounded record lookup, scalar equality filters and counts; no arbitrary operators, pipelines, code or writes.

The public agent now checks the signed protocol sender against the owner's observed ASI conversation gateway. Other senders receive no organizational data. Use the already-tested owner chat for the demo; do not promise arbitrary visitors access.

Verified in ASI:One: fresh raw-record count 53,431; live search; source-linked discount answer; test marker changed from HARBOR-7 to COMPASS-42 without restarting the agent; English answer to a Russian question. Fresh `deputy_public_state` uses the single `deputy_mirror:recplace:current` record, not old sessions. An active demo baseline alone is not proof of real company approval.

**Operational dependency:** this laptop, the bridge process, the tunnel and Internet must remain available. The temporary direct Mongo read user and the Agentverse exact-IP allowance remain unused by this route and expire automatically. The local bridge currently uses the existing import credential; the HTTP contract enforces read-only operations. A permanent deployment should replace it with a database-level read-only credential.

See `MONGO-LIVE-VERIFICATION.md` for checks and `RUN-LIVE-MEMORY.md` for operation. The narrower original attempt below is retained as history, not current scope.

## Original 14-record direct-access attempt

Taras selected direct MongoDB access for the first working slice. The broader tool-loop design below is a follow-on, not the implementation currently being installed.

`ASI:One → hosted Deputy → PyMongo → theseus_deputy_demo.memory → ASI reasoning → answer`

- A fresh read runs on each reasoning request. No cached answer, hard-coded question routing, arbitrary query execution or new backend service is used.
- The collection contains 12 distinct source-linked, sanitized claims, one coverage/direction brief and one explicitly marked connectivity-test record: 14 records total. It is a curated subset, not the entire organizational database.
- The approved temporary user can only read this collection, on the named cluster, for six hours. Agentverse receives the scoped URI through its environment. It never receives the broad import credential.
- The Atlas allowlist contains the observed Agentverse egress IP `35.234.133.181/32`, expiring after six hours. Do not expand to all IPs as a fallback.
- Retrieval fails closed on errors or if the reviewed collection exceeds 40 records / 60,000 serialized characters. This is an intentionally small demo reader; expanding it requires retrieval design, not silently truncating the organization.
- Source references retain claim IDs, source IDs, hashes and character offsets. Raw client text and names are excluded. Public source URLs must be verified before adding them.
- The direction brief is a dated snapshot. Website Commit state is not yet mirrored into this collection, and chat remains unable to approve or execute changes.

Verification is tracked in `MONGO-LIVE-VERIFICATION.md`; configuration alone must not be called a successful live answer.

The owner wants free-form questions, as in Firny, not a fixed menu of summaries. Expand the permitted data scope gradually; do not restrict the question vocabulary to the demo script.

## Smallest useful implementation

`ASI:One conversation → Deputy tool loop → scoped read adapter → MongoDB + current demo runtime`

Use the existing ASI model to choose tools and explain results. No second reasoning service, new vector database, or orchestration framework is required for the first slice. A narrow authenticated API can carry these tool calls; MCP is an optional compatible wrapper, not a prerequisite. Do not expose the current localhost application wholesale.

| Tool | What it permits |
|---|---|
| `describe_data` | Discover approved datasets, field meanings, dates, provenance and gaps. Include active runtime/session state as a separately named dataset. |
| `query_data` | Search, filter, sort, count and group permitted records. Execute validated structured requests, not arbitrary Python, JavaScript or unrestricted Mongo pipelines. |
| `read_evidence` | Open a bounded, authorized source excerpt or decision receipt by identifier. Return provenance, source time and whether the text is truncated. |

The model can make several bounded calls: inspect schema → count/filter → read supporting examples → answer with source references. Numerical questions require database calculations, not estimates from retrieved snippets. “Why?” answers distinguish source statements from the model's inference; no matching records does not prove an event never happened.

Every result carries `organization_id`, `data_as_of`, `retrieved_at`, `provenance`, `record/version refs`, `coverage/limitations`, and `demo_session_id` when relevant. “Live retrieval” means a fresh query of stored data; the underlying RecPlace import remains a historical snapshot unless a new source has actually arrived.

## What can be reused, and what is missing

For the strategy-first demo, a generic query must cover both the current approved direction and the evidence behind historical practice. If retrieval finds only partial guidance, say “I did not find a single approved strategy in the accessible records” and cite that scope; do not force the absence claim to fit a script. Return a proposal for human review, not an already-active strategy. Exact-version approval and activation remain in the app.

The minimum network connection is a narrow authenticated read API reachable by the hosted Deputy. The local app already has a Mongo adapter; the Deputy cannot reach the owner's laptop through its own localhost. Keep the Mongo credential on the service side and return only the caller's permitted dataset. A public-safe demo dataset can be exposed to the public agent; private organizational answers require a verified owner session. This design does not authorize a tunnel or an Atlas access change.

In the current file ownership, Argon's backend area supplies the bounded read API and current runtime state, while Viveka's hosted client adds tool definitions, executes returned tool calls and feeds their results back to ASI. New records and changed rule state must appear on a subsequent query. A draft/Commit handoff, period-scoped review and simulation execution are additional cycle capabilities, not things that appear automatically from a Mongo connection.

Firny already implements the pattern in `recplace-data-app/services/mcp_tools.py`: table/column discovery, read-only queries, entity search, adjacent relations, and bounded source reads. Reuse the contract and policy principles; its DuckDB SQL executor is not a MongoDB adapter and must not silently bypass this hackathon's raw-first Mongo workflow.

Theseus has `MongoStorageBackend` in `database/adapter.py`, but it also exposes writes and is not a ready public-agent boundary. Current actual collections include `raw_records`, `sources`, `source_chunks`, `claims`, `review_signals`, `decisions`, and simulation/demo records. Do not promise every collection in the older proposed SCHEMA.md exists or is populated.

The current active mandate, active tool pointer, challenges and runtime event list are partly in application memory; a Mongo-only query cannot reliably answer “What rule is active now?”. The adapter must read the current controller for these questions until runtime persistence is implemented. Keep these results separate from historical decision receipts and prepared simulation reports.

The hosted `http_client.py` currently calls ASI without `tools` and returns only text. Add bounded tool-call handling there, and implement the read adapter in the backend owner's area after coordination. Official ASI [tool calling](https://docs.asi1.ai/documentation/build-with-asi-one/tool-calling) supports this pattern. Agentverse also documents [MCP, HTTP and PyMongo imports](https://docs.agentverse.ai/documentation/advanced-usages/allowed-imports); available imports do not establish network reachability or permission to disclose data.

## Access stages

1. Public demo: approved sanitized/synthetic records and current isolated demo state. General questions already allowed within this scope.
2. Owner-only evidence: specified private RecPlace collections/fields and excerpts, after an authenticated owner binding and explicit transmission scope for Fetch/ASI processing.
3. Proposal creation: a separate write capability with its own audit; no implicit approval or application.
4. Application: stays in the human decision flow and requires the exact approved version. It is outside the first data-question integration.

The public agent profile is reachable by other people. A database read-only key alone does **not** protect confidentiality. The service must establish the caller through verified identity/session evidence, never through a name or “I am Taras” in a prompt. Until that is proven, all public chat callers receive only the approved demo dataset. Do not grant the hosted agent the existing full Mongo credential or change Atlas network access as part of this design.

Enforce organization/session scope outside model arguments; allowlisted fields/operators, bounded rows/bytes/time and tool rounds; no `$out`, `$merge`, `$where`, code execution or unscoped joins. Source text is evidence, never an instruction. Audit data access without copying raw client content into public logs.

## Acceptance before saying it works

- An unprepared factual question returns cited records; an aggregate agrees with a direct controlled count.
- A new record in the permitted demo scope changes the answer on a subsequent query, with a new timestamp.
- Missing evidence produces an explicit gap; simulation never becomes an observed company fact.
- Questions about the active rule agree with the current demo session, including after restart/reset.
- An unauthorized caller, another organization, unsupported operators and mutation requests are rejected outside the model.
- The same question can open its full evidence view without exposing private source content in a public URL.

Responsibility map, not a new assignment: Argon owns backend/runtime access; Viveka owns the hosted Deputy tool loop and card bindings; the coordinator sequences any authorized integration. No keys, public endpoint, new agent or task were created by this document.
