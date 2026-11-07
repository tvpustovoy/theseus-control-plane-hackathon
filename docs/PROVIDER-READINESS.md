# Provider readiness · preparation observations, November 7, 2026

These are preparation observations, not integration tests in this repository. Balances can change.

| Provider | Observed | Still needed for this app |
|---|---|---|
| Meta | Owner confirmed $100 free credits active | Scoped local credential configuration, model choice and a minimal extraction test |
| SubQ | Event access approved; $20 total credit observed; model listing succeeded | Validate the exact model and consistency-review contract; no generation/decision test completed here |
| MongoDB | $100 credit activated | Cluster/database provisioning, scoped access and persistence test; no cluster created yet |
| Google | Subscription-backed Antigravity CLI smoke test succeeded during prep | Optional development fallback; this is not a Gemini API grant |
| Fetch.ai | Hackathon materials available | SDK/protocol choice, registration and bounded onboarding demo |

The available SubQ model list included `subq-snap-1.1`, `subq-snap-latest` and `subq-snap-preview`. Do not equate `subq-snap-preview` with `subq-preview`, or infer context length and free-text behavior from the name. Test the authorized contract before implementation.

Credentials and account identifiers stay in the private preparation workspace; none have been copied here.
