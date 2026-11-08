# Returning from the dashboard as a conversation

November 7, 2026 · clipboard continuation implemented and checked in the browser

Taras clarified the request: return to the same ASI chat with a prepared **user draft**, not an automatically sent message or a proactive agent reply. He authorized a suitable working fallback.

## Implemented behavior

Bottom return actions now show **Copy & return to Deputy**, a paste hint and an expandable, editable suggested message. The draft depends on the current screen and displayed state. It describes the dashboard state without claiming that merely visiting a page approved or applied anything. S05 distinguishes awaiting a decision, approved but inactive, active, and rolled back.

Clicking copies the draft, including `@theseus-deputy-ceo`, and opens the exact validated `return_to` conversation. The owner pastes with ⌘V (Ctrl+V on Windows) and chooses whether to send. This is **not automatic input prefill**. No message, approval, or application is submitted by this action. The shared return helper supplies the bottom actions; the surrounding layout remains owned by Datamaster.

If the clipboard is blocked, the dashboard stays open with the draft selected and an ordinary return link. Invalid destinations and empty drafts are rejected. No extension, account permission, API credential or additional server route is required.

## Verification

- Browser: S03 → Copy & return → the same ASI conversation → paste. ASI displayed the intended English follow-up in the composer and resolved Theseus Deputy CEO as recipient. The draft was left **unsent**. No demo state was changed.
- Evidence: local browser screenshot retained privately, outside the public repository.
- Offline: `node app/ui/test_deputy_continuation.cjs` passes state wording, edited draft, exact return, clipboard failure, invalid destination and empty draft checks. `node --check app/ui/app.js` passes.
- Implemented in `app/ui/app.js` and `app/ui/styles.css`; no application restart was needed.

The official [ASI friend-collab announcement](https://asi1.ai/blog/your-ai-pitches-friend-collabs) describes its own feed cards opening a **new** chat with a prepared draft. It does not document an external URL for prefilling an **existing** conversation. No supported external same-chat prefill parameter was found in the reviewed sources; this is not proof that one cannot exist.

## Earlier investigation: proactive replies (not implemented)

The following protocol research addressed the earlier interpretation, before the owner clarified that the text should remain a user draft. It is not part of the shipped clipboard flow.

## What is established

- The current integration obtains the ASI conversation UUID from the owner gateway's `ctx.session`; the return URL round trip was verified live.
- The official [ACP tutorial](https://docs.asi1.ai/documentation/tutorials/agent-chat-protocol) stores the original sender by `ctx.session`, receives a later response from another agent, and replies to that original sender. This documents asynchronous continuation within a session.
- The official [uAgents context implementation](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py) supports proactive sending and places the context session into the signed message envelope.
- The standalone [send_message_raw helper](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py) creates a fresh UUID; calling it blindly would not preserve the current chat.
- [Chat Completions](https://docs.asi1.ai/documentation/build-with-asi-one/chat-completions) generates a reply from supplied messages. It is not documented as an API for inserting messages into a user's ASI website conversation.
- No documented URL parameter for opening an existing ASI chat and automatically sending a message was found in the reviewed official documentation. This is not proof that no such interface exists.

## Unimplemented alternative: proactive integration

1. Preserve an authenticated binding of the owner gateway, ASI session and application demo session when handing off to the website. Do not trust a return URL alone as message authority.
2. After a successful website action, record a bounded event containing the commitment ID/version, action, receipt and originating chat binding.
3. On Continue with Deputy, notify the hosted Deputy through an authenticated callback or a small event queue fetched through the existing bridge. Navigation and notification are separate operations.
4. The Deputy reads the authoritative state and sends one short ACP message, optionally with the next card, in the original session. The message is from the Deputy, never fabricated as a user message.
5. Deduplicate by event ID, reject stale run/version bindings, and do not treat opening/reloading a page as confirmation. Clicking Back without changing anything should not produce a false approval or repeat notification.

Example after a confirmed direction: “Your direction is saved. Let’s check how current practice lines up with it.” After application: “The change is active. Let’s review the outcomes of this commitment.” Use these only when receipts prove the corresponding transition.

## Remaining proof for that alternative

A bounded live test must establish that ASI:One displays a delayed second message from this hosted agent in the exact same browser conversation after the original reply has completed. Protocol support and HTTP delivery alone do not prove website rendering, routing, or session lifetime. Do not change a real commitment just to test delivery. The dashboard event bridge is not implemented or dispatched by this research note.
