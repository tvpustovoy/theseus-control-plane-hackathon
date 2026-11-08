# Running the live Deputy memory

Use the verified owner chat:

https://asi1.ai/chat/25649435-d828-4c23-98fd-b902f4c39ddf?from=profile&handle=theseus-deputy-ceo

The owner gateway is allowlisted. The agent always replies in English.

## Presenter prompts

1. `What data do we have about the organization? How many original records are loaded?`
2. `What is our discount strategy? Separate observed practice, documented principles and decisions that still need my approval.`
3. `Show Commit`

After confirming a direction in the app, ask: `Read the current state again. What mandate is active, and when was it synchronized?` Do not imply that the chat can approve the mandate itself.

## Keep running during the demo

- Local application: http://127.0.0.1:8765/
- Read bridge: 127.0.0.1:18765
- Current tunnel: https://tribunal-enabling-belle-previews.trycloudflare.com
- Bridge process tool session: 21382; tunnel tool session: 26232.
- Keep the laptop awake and online. Closing the bridge/tunnel breaks hosted retrieval. The quick tunnel URL changes if restarted.

## Restart if necessary

From the repository root, in one terminal:

```sh
database/private/.venv/bin/python app/deputy/agentverse/memory_bridge.py
```

In another:

```sh
cloudflared tunnel --url http://127.0.0.1:18765 --no-autoupdate
```

In Agentverse `.env`, preserve the private `THESEUS_MEMORY_TOKEN` and replace `THESEUS_MEMORY_URL` with the new HTTPS tunnel origin. Stop/start the hosted agent after saving. No Mongo credential belongs in this hosted environment now.

Secret files in ignored `database/private/`: `deputy-bridge-key`, `mongodb-uri` (local only), `deputy-mongodb-uri` (unused direct-attempt reader). Do not commit or print their values. The temporary reader/IP grant expire after six hours; the active bridge uses the existing import credential, whose expiry must also be respected.

## What is proven

Live counts/search and a changed test record were observed in ASI:One. Source identifiers are available; public source links are not yet published. State comes from the current application mirror. Raw data remains historical, simulated records remain simulated, and active demo defaults are not evidence of real organizational approval.
