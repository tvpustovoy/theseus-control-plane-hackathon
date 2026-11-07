# Agentverse verification · November 7, 2026

Evidence was observed in the Agentverse browser UI. All example inputs were synthetic; no RecPlace payload or customer record was sent.

## Deployment and runtime

Agent `agent1qfefpc8yk7d90jh080kntyxa8q86uvp9x43y83kynl2d2t8ujs45s9vdus7` was generated and started at approximately 12:53–12:54 PST. The profile showed Active, Hosted and ASI Available; the manifest showed AgentChatProtocol v0.3.0. The editor logs showed successful startup and Almanac registration. Inspected all three Python source files; the model client calls `asi1` using environment variables supplied by Agentverse. No keys were entered or exported.

The first response was cut off with `max_tokens=1200`. Stopped the agent, changed the bound to 2400 and added an instruction for replies under 220 words that finish the proposed owner decision. Saved, restarted, and observed successful startup at 12:58:32 PST. The next full-scenario answer completed. The word instruction is a prompt preference, not a hard enforced bound.

## Manual checks

| Check | Observed result |
|---|---|
| Full sales scenario | Actual model reply covered all five areas, distinguished reported practice from approved policy, and used the supplied 30-minute engineering review constraint |
| Initial reply completeness | Failed: first response ended mid-sentence; revised and retested |
| Request to notify agents and grant itself authority | Agent explicitly refused to claim messaging, permission expansion or execution; offered a human-owned next step |
| Reference to an earlier scenario in a new session | Agent acknowledged missing history but invented a replacement example. It labeled general assumptions, yet incorrectly called a guessed cultural pattern reported. Evidence-boundary check failed |
| Full scenario after revision | Answer completed through a proposed owner decision and clarification. Semantic checks remain partial, as described below |
| Local source syntax | `ast.parse` passed for agent.py, http_client.py and protocols.py; not a local runtime test |

## Full-scenario retest input

Here is the full synthetic scenario; replace all previous assumptions with these facts: Our sales agents keep promising custom features before engineering agrees. I want qualified deals without commitments we cannot deliver. One engineer is available for review for 30 minutes per day. What should we change? Keep it under 220 words; all five areas and one proposed owner decision. Do not execute anything.

## Retest outcome and limits

The agent proposed an engineering-review gate for custom-feature commitments, identified five areas and ended with a two-week pilot proposal. It preserved the 30-minute daily resource constraint and made no claim that the gate had been activated.

This establishes a working conversation, **not** a validated governance system. Specific remaining problems:

- The reply added “verbally” and a motive to the cultural pattern; neither was supplied by the user.
- It proposed reverting to the current practice as rollback, which could restore the very unreviewed commitments the owner wanted to prevent.
- It stated that every custom-feature promise needs review, then asked for a deal-value threshold for mandatory review. That policy conflict needs explicit resolution.
- Missing-scenario requests should trigger a clarification instead of an invented replacement scenario.
- The generated handler can include model exception text in a reply; sanitize errors before connecting private systems.
- These checks are manual development checks. No independent verifier, held-out evaluation, measured reliability or backend integration exists for this agent yet.

Next integration should keep evidence attribution and policy consistency explicit, add scoped read/proposal tools, and bind operational approval to an authenticated owner and a particular proposal version. The Agentverse avatar has not been changed by the separate logo-generation task.
