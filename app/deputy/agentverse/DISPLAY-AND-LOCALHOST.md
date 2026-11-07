# ASI:One cards, full website and localhost

Checked November 7, 2026. Owner direction: use both native cards and the full Theseus website, with navigation from the summary to its full record. This document separates the intended experience from verified implementation.

## What is documented

ASI:One-compatible clients render native interactive cards from ACP `MetadataContent`: form, review, detail, carousel or custom element trees. This is structured UI, not our HTML loaded into a webview. Card selections return to the agent as JSON text in direct interactions or planner-mediated prose. [Official card protocol](https://docs.agentverse.ai/documentation/advanced-usages/agent-driven-interactive-cards).

The documented primitives include headings, text, images, fields and buttons. A button submits `action.selection`; the primitive list does not document an `href`, arbitrary HTML, script or iframe. We therefore cannot promise that a card button directly opens a website. Validate that behavior in the actual client; a text link returned alongside the card is a candidate fallback, also to be tested. [Official primitives](https://docs.agentverse.ai/documentation/advanced-usages/element-tree-primitives).

## What localhost means here

- A hosted agent's localhost is its own runtime, not Taras's laptop. A normal HTTP call to that address cannot fetch our laptop's app.
- A URL opened in Taras's browser can address his local app. ASI:One link validation, clickability and navigation to HTTP localhost have not been tested. No specific ASI:One localhost ban was established by this documentation review; that is not proof of support.
- Other viewers' localhost is their own computer. A shared public demonstration would need a separately authorized hosted endpoint or a screen-share demonstration.
- Navigating to a page, embedding it, fetching it from another origin and letting a remote agent query its backend are distinct capabilities. One does not establish the others.

## Current project state and bounded design

Inspected `protocols.py` and `agent.py`: the hosted Deputy sends only `TextContent`, calls ASI:One for a proposal and explicitly has no Theseus backend connection. It currently implements neither native cards nor browser navigation.

Argon owns the complete local website. Viveka owns the native card adapter and agent/backend connection. Both surfaces must refer to the same record ID, version and evidence status; the website owns the detailed view. Keep a directly opened browser tab as the demo fallback. Preserve human authorization and exact-version checks in the backend: neither a selection nor planner prose alone establishes operational authority.

Before claiming the integrated experience, test one synthetic card, its returned selection, the exact full-view link, correct record/version rendering, and the independent data path. No raw client data, public tunnel, operational mutation or new deployment was required or performed for this review.
