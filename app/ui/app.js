/**
 * Theseus Control Plane · Human-Facing Browser Application (S01..S06)
 * Implements all 10 acceptance checks in reports/2-scenarios/HUMAN-INTERFACE-REVIEW.md
 */

const stateStore = {
  data: null,
  currentFrame: "MEMORY",
  memoryOverview: null,
  memorySources: null,
  memoryType: "",
  memoryAnswer: null,
  memoryTurns: [],
  memoryBusy: false,
  selectedEvidenceId: null,
  drawerOpen: false,
  lastTriggerEl: null,
  s01EditOpen: false,
  s01Draft: {
    goal_text: null,
    principle_text: null,
    risk_text: null,
  },
  openQuestionCardId: null,
};

const HUMAN_REASON_LABELS = {
  longer_term: "Longer contract term",
  prepayment: "Upfront prepayment",
  referral: "Verified customer referral",
  volume: "Higher committed volume",
  other_with_text: "Other commitment (with written explanation)",
};

const HUMAN_VERDICT_LABELS = {
  insufficient_evidence: "Not enough evidence to decide",
  reviewed_no_proven_contradiction: "No proven contradiction (1× different scope/time, 3× insufficient evidence, 1× consistent low-conf)",
  possible_conflict: "Possible conflict — low confidence (29%)",
  contradicts: "Contradicts proposed rule (simulated preview)",
  different_scope: "The rule applies to a different situation",
  consistent: "Fits our agreement",
};

function esc(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderEnglishAnswer(value) {
  const letters = {а:'a',б:'b',в:'v',г:'g',д:'d',е:'e',ё:'yo',ж:'zh',з:'z',и:'i',й:'y',к:'k',л:'l',м:'m',н:'n',о:'o',п:'p',р:'r',с:'s',т:'t',у:'u',ф:'f',х:'kh',ц:'ts',ч:'ch',ш:'sh',щ:'shch',ъ:'',ы:'y',ь:'',э:'e',ю:'yu',я:'ya',і:'i',ї:'yi',є:'ye',ґ:'g'};
  const latin = String(value || '').replace(/[А-Яа-яЁёІіЇїЄєҐґ]/g, char => {
    const translated = letters[char.toLowerCase()] || '';
    return char === char.toUpperCase() ? translated.charAt(0).toUpperCase() + translated.slice(1) : translated;
  });
  return esc(latin).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\n/g, '<br>');
}

function validDeputyReturn(value) {
  if (typeof value !== 'string') return null;
  const match = value.trim().match(/^https:\/\/asi1\.ai\/chat\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/?$/i);
  return match ? `https://asi1.ai/chat/${match[1]}` : null;
}

function updateDeputyReturn() {
  const current = new URL(window.location.href);
  const values = current.searchParams.getAll('return_to');
  let target = values.length === 1 ? validDeputyReturn(values[0]) : null;
  try {
    if (!values.length) {
      target = validDeputyReturn(sessionStorage.getItem('theseus.deputyReturn'));
      if (target) {
        current.searchParams.set('return_to', target);
        window.history.replaceState(window.history.state, '', current);
      }
    }
    if (target) sessionStorage.setItem('theseus.deputyReturn', target);
    else if (values.length) sessionStorage.removeItem('theseus.deputyReturn');
  } catch (_) { /* URL persistence still works when storage is unavailable. */ }
  const link = document.getElementById('back-to-deputy');
  const connect = document.getElementById('connect-deputy');
  if (link) {
    link.hidden = !target;
    link.style.display = target ? '' : 'none';
    if (target) link.href = target;
    else link.removeAttribute('href');
  }
  connect.querySelector('summary').textContent = target ? 'Change connected chat' : 'Connect this chat';
  if (values.length && !target) {
    document.getElementById('deputy-connect-error').textContent = 'Invalid return address. Paste an exact ASI:One chat URL.';
  }
}

function deputyReturnAction() {
  const values = new URL(window.location.href).searchParams.getAll('return_to');
  let target = values.length === 1 ? validDeputyReturn(values[0]) : null;
  if (!values.length) {
    try { target = validDeputyReturn(sessionStorage.getItem('theseus.deputyReturn')); } catch (_) {}
  }
  if (!target) return '';
  const pasteKey = /Mac|iPhone|iPad/.test(navigator.platform) ? '⌘V' : 'Ctrl+V';
  return `<div class="deputy-continuation">
    <button type="button" class="btn btn-secondary" data-deputy-continue="${esc(target)}">Copy &amp; return to Deputy ↗</button>
    <small>Paste with ${pasteKey} in your chat, then send when ready.</small>
    <details><summary>Suggested message · edit if needed</summary>
      <textarea aria-label="Message to continue with Deputy" rows="3">${esc(deputyFollowUp(stateStore.currentFrame, stateStore.data))}</textarea>
    </details>
    <p class="deputy-copy-status" role="status" aria-live="polite" hidden></p>
    <a class="deputy-copy-fallback" href="${esc(target)}" hidden>Return to chat after copying →</a>
  </div>`;
}

// A draft for the owner, never an instruction to approve or send automatically.
// Describe the displayed state, not an action that the owner may not have taken.
function deputyFollowUp(frame, data) {
  const confirmed = data?.s01_commit?.mandate_status === 'committed_mandate';
  const application = data?.s05_application || {};
  let message;
  switch (frame) {
    case 'S01':
      message = confirmed
        ? 'The dashboard shows our direction is confirmed. What needs attention in the recent evidence? Show evidence and keep it brief.'
        : 'I have reviewed the proposed direction. What do I still need to decide? Show Commit and keep it brief.';
      break;
    case 'S02':
      message = `I have reviewed how we work. How do our habits compare with the ${confirmed ? 'confirmed' : 'proposed'} direction? Show evidence and keep it brief.`;
      break;
    case 'S03':
      message = 'I have reviewed the alignment check. What is the smallest change you recommend, and why? Show the proposed change and keep it brief.';
      break;
    case 'S04':
      message = 'I have reviewed the proposed change. What should we do next? Tell me what needs my approval before anything is applied.';
      break;
    case 'S05':
      if (application.active_runtime_version === 'tool-v2') {
        message = 'The dashboard shows the change is active. What should we do next? Show the outcomes of this commitment and distinguish test evidence from company outcomes.';
      } else if (application.rollback_receipt) {
        message = 'The dashboard shows the previous setup is restored. What is active now, and what should we do next? Keep it brief.';
      } else if (application.decision_record?.action === 'approve') {
        message = 'The dashboard shows approval, but the change is not active yet. What should we do next? Keep it brief.';
      } else {
        message = 'I have reviewed the decision page. What should we do next? Explain what still needs my decision; do not approve or apply anything for me.';
      }
      break;
    case 'S06':
      message = 'Let us review the outcomes of this commitment. What do we know from the test run, what is still unmeasured in the company, and what should we do next? Keep it brief.';
      break;
    case 'COMMITMENTS':
      message = 'I have reviewed our current commitments. Which one needs my attention next, and why? Show current commitments and keep it brief.';
      break;
    default:
      message = 'I have reviewed Organization Memory. What do our facts tell us about our discount strategy, and what still needs my decision? Keep it brief.';
  }
  return '@theseus-deputy-ceo ' + message;
}

async function continueWithDeputy(button) {
  const container = button.closest('.deputy-continuation');
  const target = validDeputyReturn(button.dataset.deputyContinue);
  const draft = container.querySelector('textarea');
  const status = container.querySelector('.deputy-copy-status');
  if (!target || !draft.value.trim()) {
    status.hidden = false;
    status.textContent = !target ? 'Connect a valid ASI:One chat first.' : 'Write a message before continuing.';
    return;
  }
  button.disabled = true;
  try {
    await navigator.clipboard.writeText(draft.value.trim());
    window.location.assign(target);
  } catch (_) {
    // Keep the draft visible and preserve the exact destination if copying is blocked.
    container.querySelector('details').open = true;
    status.hidden = false;
    status.textContent = 'Automatic copy was unavailable. Copy the selected message, return to chat, and paste it there.';
    container.querySelector('.deputy-copy-fallback').hidden = false;
    draft.focus();
    draft.select();
  } finally {
    button.disabled = false;
  }
}

document.addEventListener('click', (event) => {
  const button = event.target.closest('[data-deputy-continue]');
  if (button) continueWithDeputy(button);
});

function provenanceBadgeClass(cat) {
  const s = String(cat || "").toLowerCase();
  if (s.includes("simulation") || s.includes("prepared")) return "amber";
  if (s.includes("company") || s.includes("source")) return "teal";
  return "";
}

async function fetchState() {
  const res = await fetch("/api/state");
  const json = await res.json();
  if (json.ok === false) throw new Error(json.message || "Failed to load state");
  stateStore.data = json.state || json;
  const c = stateStore.data.s01_commit;
  if (stateStore.s01Draft.goal_text === null) {
    stateStore.s01Draft.goal_text = c.intent_and_goal.proposed_text;
  }
  if (stateStore.s01Draft.principle_text === null) {
    stateStore.s01Draft.principle_text = c.governing_principle.proposed_text;
  }
  if (stateStore.s01Draft.risk_text === null) {
    stateStore.s01Draft.risk_text = c.culture_to_protect.risk_to_watch;
  }
  renderAll();
}

async function postApi(path, payload) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  const json = await res.json();
  if (json.state) {
    stateStore.data = json.state;
  }
  if (!json.ok) {
    const err = new Error(json.message || "Operation failed");
    err.details = json.details;
    err.error_code = json.error;
    throw err;
  }
  return json;
}

function setFrameFromHash() {
  const hash = (window.location.hash || "#MEMORY").replace("#", "").toUpperCase();
  const valid = ["MEMORY", "COMMITMENTS", "S01", "S02", "S03", "S04", "S05", "S06"];
  stateStore.currentFrame = valid.includes(hash) ? hash : "MEMORY";
  // Keep evidence drawer closed on fresh route navigation
  closeEvidenceDrawer(false);
  renderAll();
  if (stateStore.currentFrame === "MEMORY") loadMemory();
}

function navigateToFrame(frameId) {
  window.location.hash = "#" + frameId;
}

async function loadMemory(cursor = null) {
  try {
    if (!stateStore.memoryOverview) {
      const overviewResponse = await fetch("/api/memory/overview");
      if (!overviewResponse.ok) throw new Error("Could not load Organization Memory status");
      stateStore.memoryOverview = await overviewResponse.json();
    }
    const params = new URLSearchParams({ limit: "12" });
    if (stateStore.memoryType) params.set("type", stateStore.memoryType);
    if (cursor) params.set("cursor", cursor);
    const sourceResponse = await fetch(`/api/memory/sources?${params}`);
    if (!sourceResponse.ok) throw new Error("Could not load source metadata");
    stateStore.memorySources = await sourceResponse.json();
    renderAll();
  } catch (error) {
    stateStore.memorySources = { items: [], error: error.message };
    renderAll();
  }
}

function renderMemory() {
  const o = stateStore.memoryOverview;
  if (!o) return `<div class="card"><h2>Organization Memory</h2><p class="muted">Loading verified data status…</p></div>`;
  const snapshot = o.snapshot || {};
  const dist = o.distillation || {};
  const review = o.review || {};
  const atlasDerived = o.atlas_derived || {};
  const rows = (stateStore.memorySources?.items || []).map(item => `
    <tr><td class="mono">${esc(item.source_id)}</td><td>${esc(item.source_type)}</td>
    <td>${esc(item.day || "Unknown")}</td><td>${esc(item.source_version)}</td></tr>`).join("");
  const types = ["", "sales_conversation", "crm_record", "normative", "founder_meeting", "unknown"];
  return `<div class="memory-page">
    <div class="card memory-hero">
      <h2>Organization Memory</h2>
      <p>Ask a question about the company, grounded in available evidence.</p>
      <p class="muted">Coverage is partial. Imported records and candidate claims are not verified business outcomes.</p>
      <div class="memory-metrics">
        <div><strong>${snapshot.state === "verified_snapshot" ? Number(snapshot.raw_records).toLocaleString() : "—"}</strong><span>raw rows · verified import</span></div>
        <div><strong>${snapshot.state === "verified_snapshot" ? Number(snapshot.sources).toLocaleString() : "—"}</strong><span>source records · verified import</span></div>
        <div><strong>${dist.state === "partial_candidate_grade" ? Number(dist.candidate_claims).toLocaleString() : "—"}</strong><span>candidate claims · partial extraction</span></div>
        <div><strong>${review.discount_pairs ?? "—"}</strong><span>discount pairs · ${review.proven_contradictions ?? "—"} proven contradictions</span></div>
      </div>
      <details class="page-more"><summary>More · Data coverage and verification</summary><p>${esc(o.scope)}</p>
      <p class="memory-provenance">Import verified ${esc(snapshot.verified_at || "date unavailable")} · Muse checkpoint batch ${esc(dist.batch || "unavailable")}: ${esc(dist.distinct_source_ids || "—")} distinct source IDs / ${esc(dist.candidate_text_hashes || "—")} candidate text hashes. Candidate claims are in a local private packet, not Atlas facts or confirmed frequencies.</p>
      <p class="memory-provenance">Atlas derived collections now: ${esc(atlasDerived.claims ?? "—")} claims · ${esc(atlasDerived.source_chunks ?? "—")} source chunks · ${esc(atlasDerived.extraction_runs ?? "—")} extraction runs.</p></details>
    </div>
    <details id="memory-inventory" class="card page-more memory-inventory"><summary>More · Browse source records</summary>
      <p class="muted">Metadata only. The imported source text and client details are kept out of this demo browser.</p>
      <label for="memory-type">Source type</label>
      <select id="memory-type">${types.map(type => `<option value="${esc(type)}" ${type === stateStore.memoryType ? "selected" : ""}>${esc(type || "All source types")}</option>`).join("")}</select>
      ${stateStore.memorySources?.error ? `<p role="alert">${esc(stateStore.memorySources.error)}</p>` : ""}
      <div class="memory-table-wrap"><table class="memory-table"><thead><tr><th>Source ID</th><th>Type</th><th>Day</th><th>Version</th></tr></thead><tbody>${rows || `<tr><td colspan="4">No source metadata in this page.</td></tr>`}</tbody></table></div>
      ${stateStore.memorySources?.next_cursor ? `<button class="btn secondary" id="memory-next" type="button">Next 12 sources →</button>` : ""}
    </details>
    <div class="card">
      <h3>Ask about your company</h3>
      <p class="muted">Ask in any language; answers are in English. Claude can count CRM clients and find names matching your keywords, using live database results and selected evidence. Queries and answers are logged privately.</p>
      ${stateStore.memoryTurns.map(turn => `<div class="subcard memory-answer"><strong>Your question</strong><p>${esc(turn.question)}</p><strong>Answer · ${esc(turn.model)}</strong><p>${renderEnglishAnswer(turn.answer)}</p><div class="memory-citations">${[...new Set(turn.citation_ids || [])].map(id => stateStore.data?.evidence_catalog?.[id] ? renderCiteButton(id, id) : `<span class="status-pill mono">${esc(id)}</span>`).join(" ")}</div></div>`).join("")}
      ${stateStore.memoryTurns.length ? `<p class="muted">You can ask a follow-up. The last two question/answer pairs are included as context.</p><button class="btn secondary" id="memory-new-chat" type="button" ${stateStore.memoryBusy ? "disabled" : ""}>New conversation</button>` : ""}
      <form id="memory-ask-form"><label for="memory-question">${stateStore.memoryTurns.length ? "Follow-up question" : "Your question"}</label><textarea id="memory-question" maxlength="600" required placeholder="${stateStore.memoryTurns.length ? "What should we verify first, and why?" : "What do we know about discounts and customer commitments?"}"></textarea>
      <button class="btn" type="submit" ${stateStore.memoryBusy ? "disabled" : ""}>${stateStore.memoryBusy ? "Asking…" : "Ask"}</button></form>
      ${stateStore.memoryAnswer ? `<div class="subcard memory-answer"><strong>Answer · ${esc(stateStore.memoryAnswer.model || "")}</strong><p>${esc(stateStore.memoryAnswer.answer || stateStore.memoryAnswer.error || "").replace(/\n/g, "<br>")}</p><div class="memory-citations">${(stateStore.memoryAnswer.citation_ids || []).map(id => stateStore.data?.evidence_catalog?.[id] ? renderCiteButton(id, id) : `<span class="status-pill mono">${esc(id)}</span>`).join(" ")}</div></div>` : ""}
    </div>
  </div>`;
}

async function askMemory(question) {
  stateStore.memoryBusy = true;
  stateStore.memoryAnswer = null;
  renderAll();
  try {
    const response = await fetch("/api/memory/ask", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, previous_run_id: stateStore.memoryTurns.at(-1)?.run_id || null }),
    });
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.message || "The model request failed");
    stateStore.memoryTurns.push({ question, ...result });
    stateStore.memoryAnswer = null;
  } catch (error) {
    stateStore.memoryAnswer = { error: error.message };
  } finally {
    stateStore.memoryBusy = false;
    renderAll();
  }
}

function openEvidenceDrawer(evidenceId, triggerEl) {
  if (!stateStore.data) return;
  if (triggerEl) {
    stateStore.lastTriggerEl = triggerEl;
  }
  stateStore.selectedEvidenceId = evidenceId;
  stateStore.drawerOpen = true;
  renderDrawer();
  const closeBtn = document.getElementById("close-drawer-btn");
  if (closeBtn) closeBtn.focus();
}

function closeEvidenceDrawer(restoreFocus = true) {
  stateStore.drawerOpen = false;
  renderDrawer();
  if (restoreFocus && stateStore.lastTriggerEl && typeof stateStore.lastTriggerEl.focus === "function") {
    stateStore.lastTriggerEl.focus();
  }
}

function renderDrawer() {
  const layoutEl = document.getElementById("app-layout");
  const drawerEl = document.getElementById("evidence-drawer");
  const titleEl = document.getElementById("drawer-title");
  const kickerEl = document.getElementById("drawer-kicker");
  const provEl = document.getElementById("drawer-provenance");
  const bodyEl = document.getElementById("drawer-body");

  if (!layoutEl || !drawerEl) return;

  if (!stateStore.drawerOpen || !stateStore.data || !stateStore.selectedEvidenceId) {
    layoutEl.classList.add("drawer-closed");
    drawerEl.hidden = true;
    return;
  }

  const catalog = stateStore.data.evidence_catalog || {};
  const item = catalog[stateStore.selectedEvidenceId];
  if (!item) {
    layoutEl.classList.add("drawer-closed");
    drawerEl.hidden = true;
    return;
  }

  layoutEl.classList.remove("drawer-closed");
  drawerEl.hidden = false;

  const isDataConnection = item.evidence_id === "ev:import-live-20261107-full";
  kickerEl.textContent = isDataConnection ? "Data Connection" : "Why this recommendation?";
  titleEl.textContent = item.title;
  const catLabel = item.evidence_category || "Company evidence";
  provEl.textContent = catLabel;
  provEl.className = "status-pill " + provenanceBadgeClass(catLabel);

  bodyEl.innerHTML = `
    <div class="subcard highlight-glacier" style="margin-bottom: 12px;">
      <p style="margin: 0; font-size: 0.9rem; color: var(--theseus-ink);">${esc(item.summary)}</p>
    </div>
    <details style="margin-top: 10px;">
      <summary style="cursor: pointer; font-weight: 600; font-size: 0.82rem; color: var(--theseus-ink);">
        Technical details (IDs, hashes &amp; JSON)
      </summary>
      <div class="subcard" style="margin-top: 8px; font-size: 0.78rem;">
        <div><strong>Evidence ID:</strong> <span class="mono">${esc(item.evidence_id)}</span></div>
        <div><strong>Source reference:</strong> <span class="mono">${esc(item.source_id)}</span></div>
        <div><strong>Version:</strong> <span class="mono">${esc(item.version)}</span></div>
        <pre class="mono" style="background:#f4f7fa; padding:10px; border-radius:8px; overflow-x:auto; font-size:0.73rem; margin-top:8px;">${esc(JSON.stringify(item.details, null, 2))}</pre>
      </div>
    </details>
  `;
}

function renderCiteButton(evidenceId, customLabel) {
  const cat = (stateStore.data && stateStore.data.evidence_catalog) || {};
  const item = cat[evidenceId];
  const label = customLabel || (item && item.human_label) || "See source";
  return `<button type="button" class="cite-btn" data-evidence-id="${esc(evidenceId)}">${esc(label)}</button>`;
}

function captureS01DraftInputs() {
  const gEl = document.getElementById("s01-goal-input");
  const pEl = document.getElementById("s01-principle-input");
  const rEl = document.getElementById("s01-risk-input");
  if (gEl) stateStore.s01Draft.goal_text = gEl.value;
  if (pEl) stateStore.s01Draft.principle_text = pEl.value;
  if (rEl) stateStore.s01Draft.risk_text = rEl.value;
}

/* =========================================================================
   S01: Agree our direction (fits 1280x800 first viewport without scroll)
   ========================================================================= */
function renderS01(d) {
  const c = d.s01_commit;
  const sc = c.summary_copy || {};
  const isCommitted = c.mandate_status === "committed_mandate";

  const statusPill = isCommitted
    ? `<span class="status-pill teal">Direction saved (${esc(c.committed_version || "mandate-v2")})</span>`
    : `<span class="status-pill amber">Pending your confirmation (${esc(c.draft_version || "mandate-v2-draft")})</span>`;

  const monitoringPill = `<span class="status-pill ${c.monitoring_status.includes("active") ? "teal" : "amber"}">${esc(c.human_monitoring_status || "Monitoring is partial: discount outcomes are missing")}</span>`;

  return `
    <div class="card" style="padding: 18px 22px;">
      <div class="card-header" style="margin-bottom: 10px; padding-bottom: 10px;">
        <div>
          <h2 class="card-title" style="margin-bottom: 2px;">${esc(sc.heading || "Agree our direction")}</h2>
        </div>
        <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
          ${statusPill}
          ${monitoringPill}
        </div>
      </div>

      <ul class="direction-summary-list">
        <li>
          <strong>Goal:</strong> ${esc(sc.goal_summary || "Protect margin while growing sales.")}
          <span class="muted">(${esc(c.intent_and_goal.human_provenance || "Based on source evidence and your stated intent")})</span>
        </li>
        <li>
          <strong>Principle:</strong> ${esc(sc.principle_summary || "Every discount should receive an explicit customer commitment in return.")}
        </li>
        <li style="border-left: 4px solid var(--theseus-glacier, #3fa6e8); background: #eef7fd;">
          <strong>Your decision:</strong> ${esc(sc.decision_prompt || "Confirm this direction and the monitoring scope. Monitoring remains partial until the missing signal is connected.")}
          ${isCommitted && c.effective_time ? `<div class="muted" style="margin-top:4px;">Confirmed today at ${esc(c.effective_time)} · Reference saved (does not guarantee active CRM monitoring until Step 5).</div>` : ""}
        </li>
      </ul>

      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-top: 12px;">
        <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
          <button type="button" class="btn btn-amber" id="btn-commit-mandate" onclick="handleCommitMandate()">
            ${isCommitted ? "Update confirmed direction &amp; monitoring scope" : "Confirm direction &amp; monitoring scope"}
          </button>
          ${deputyReturnAction()}
          <button type="button" class="btn btn-secondary" onclick="toggleS01Edit()">
            ${stateStore.s01EditOpen ? "Hide edit fields" : "Edit direction"}
          </button>
          <button type="button" class="btn btn-secondary" data-evidence-id="ev:codex-ep-187">
            Why these recommendations?
          </button>
        </div>
        ${isCommitted ? `<button type="button" class="btn btn-teal" onclick="navigateToFrame('S03')">Review alignment →</button>` : ""}
      </div>

      ${stateStore.s01EditOpen ? `
        <div class="subcard" style="margin-top: 14px;">
          <h4 style="margin-top:0;">Edit direction before confirming</h4>
          <div class="form-field">
            <label for="s01-goal-input">Goal &amp; quantitative target (draft until confirmed)</label>
            <textarea id="s01-goal-input" rows="2" oninput="captureS01DraftInputs()">${esc(stateStore.s01Draft.goal_text)}</textarea>
          </div>
          <div class="form-field">
            <label for="s01-principle-input">Principle &amp; agent autonomy boundary (draft until confirmed)</label>
            <textarea id="s01-principle-input" rows="2" oninput="captureS01DraftInputs()">${esc(stateStore.s01Draft.principle_text)}</textarea>
          </div>
          <div class="form-field" style="margin-bottom:0;">
            <label for="s01-risk-input">Cultural risk hypothesis to watch</label>
            <textarea id="s01-risk-input" rows="2" oninput="captureS01DraftInputs()">${esc(stateStore.s01Draft.risk_text)}</textarea>
          </div>
        </div>
      ` : ""}

      <details class="page-more"><summary>More · Culture, risks and monitoring coverage</summary><ul class="direction-summary-list">        <li>
          <strong>Culture to protect:</strong> ${esc(c.culture_to_protect.protect)}
        </li>
        <li style="border-left: 4px solid var(--theseus-amber, #f5bf45); background: #fffdf8;">
          <strong>Risk to watch — hypothesis:</strong> ${esc(sc.risk_hypothesis_summary || c.culture_to_protect.risk_to_watch)}
        </li>
        <li>
          <strong>What Theseus can see:</strong> ${esc(sc.visibility_summary || "Sales conversations and CRM records. Discount outcomes and reasons are currently missing from the CRM.")}
        </li>
</ul></details>
      <details style="margin-top: 12px;">
        <summary style="cursor:pointer; font-weight:600; font-size:0.84rem; color:var(--theseus-ink);">
          More · Full terms, changes and sources
        </summary>
        <div class="grid-2" style="margin-top: 10px;">
          <div class="subcard">
            <h4>What changes from the previous agreement</h4>
            <div class="diff-box diff-old"><strong>Previous goal:</strong> ${esc(c.intent_and_goal.previous_text)}</div>
            <div class="diff-box diff-new"><strong>Proposed goal (draft terms):</strong> ${esc(c.intent_and_goal.proposed_text)}</div>
            <div class="diff-box diff-old" style="margin-top:8px;"><strong>Previous principle:</strong> ${esc(c.governing_principle.previous_text)}</div>
            <div class="diff-box diff-new"><strong>Proposed principle (draft terms):</strong> ${esc(c.governing_principle.proposed_text)}</div>
            <p class="muted" style="margin: 8px 0 0;"><strong>Authority boundary:</strong> ${esc(c.governing_principle.authority_boundary)}</p>
          </div>
          <div class="subcard">
            <h4>Sources, attribution notes &amp; technical details</h4>
            <p class="muted" style="margin-top:0;">${esc(c.governing_principle.provenance_note)}</p>
            <div style="margin-bottom: 10px;">
              ${renderCiteButton("ev:codex-ep-187", "See source: discount conditions")}
              ${renderCiteButton("ev:codex-ep-80901", "See source: founder direction & value framing")}
              ${renderCiteButton("ev:codex-ep-78324", "See source: training guidance (attribution review)")}
              ${renderCiteButton("ev:culture-crm-blindness", "See source: CRM data completeness check")}
            </div>
            <div class="mono muted" style="font-size:0.74rem;">
              Active version ID: ${esc(c.committed_version)} · Draft ID: ${esc(c.draft_version)} · Goal ID: ${esc(c.intent_and_goal.id)} · Rule ID: ${esc(c.governing_principle.id)}
            </div>
          </div>
        </div>
      </details>
    </div>
  `;
}

function toggleS01Edit() {
  captureS01DraftInputs();
  stateStore.s01EditOpen = !stateStore.s01EditOpen;
  renderAll();
}

async function handleCommitMandate() {
  captureS01DraftInputs();
  const btn = document.getElementById("btn-commit-mandate");
  if (btn) btn.disabled = true;
  try {
    await postApi("/api/commit", {
      goal_text: stateStore.s01Draft.goal_text,
      principle_text: stateStore.s01Draft.principle_text,
      risk_text: stateStore.s01Draft.risk_text,
    });
    renderAll();
  } catch (err) {
    alert("Could not save direction: " + err.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}

/* =========================================================================
   S02: Culture — How we are working (Separates Company Evidence from Simulation)
   ========================================================================= */
function renderS02(d) {
  const s02 = d.s02_culture;
  const companyPatterns = s02.patterns.filter((p) => String(p.provenance).startsWith("observed"));
  const simPatterns = s02.patterns.filter((p) => p.provenance === "simulated");

  const renderPatternCard = (p, isSim) => `
    <div class="subcard ${isSim ? "highlight-amber" : "highlight-teal"}" style="margin-bottom: 14px;">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px; flex-wrap:wrap;">
        <h4 style="margin:0; font-size:1.02rem;">${isSim ? 'Discount behavior in the simulated baseline' : 'Discount outcomes are not established in CRM'}</h4>
        <span class="status-pill ${isSim ? "amber" : "teal"}">${isSim ? "Simulation" : "Company evidence"}</span>
      </div>

      <p class="muted">${isSim ? 'Illustrative scenario, not observed company behavior.' : 'Sales conversations show discount requests. CRM data does not yet establish discounts granted or their reasons.'}</p>
      <details class="page-more"><summary>More · Counts, limitations and examples</summary>      <div style="margin: 10px 0; padding: 10px 12px; background:#ffffff; border-radius:8px; border:1px solid var(--theseus-ice);">
        <div style="font-weight:700; font-size:0.95rem;">${esc(p.frequency_label)}</div>
        <div class="muted" style="margin-top:2px;">Scope inspected: ${esc(p.distinct_actors)}</div>
      </div>

      <p class="muted" style="margin: 8px 0;">
        <strong>What is known vs. unknown:</strong> ${esc(p.confidence_limit)}
      </p>

<p class="muted">${esc(p.title)}</p><div class="grid-2" style="margin-top:10px;">
        <div style="background:#ffffff; padding:10px 12px; border-radius:8px; border:1px solid var(--theseus-ice);">
          <div style="font-size:0.78rem; font-weight:700; margin-bottom:6px;">Supporting examples</div>
          ${p.examples.map((ex) => `<div>${renderCiteButton(ex.evidence_id, ex.label)}</div>`).join("")}
        </div>
        <div style="background:#ffffff; padding:10px 12px; border-radius:8px; border:1px solid var(--theseus-ice);">
          <div style="font-size:0.78rem; font-weight:700; margin-bottom:6px;">Counterexamples / conditions</div>
          ${p.counterexamples.map((cx) => `<div>${renderCiteButton(cx.evidence_id, cx.label)}</div>`).join("")}
        </div>
      </div>

      <details style="margin-top: 8px;">
        <summary class="muted" style="cursor:pointer; font-size:0.78rem;">Technical details (pattern ID &amp; denominator)</summary>
        <div class="mono muted" style="margin-top:4px; font-size:0.74rem;">
          Pattern ID: ${esc(p.pattern_id)} · Numerator/Denominator: ${p.numerator} / ${p.denominator} · Provenance: ${esc(p.provenance)}
        </div>
      </details></details>
    </div>
  `;

  return `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 class="card-title">How we are working</h2>
          <p class="muted" style="margin:0;">
            Which recurring practices are supported by company evidence, and what remains unknown?
            <strong>Discount request</strong> (customer asks), <strong>offer</strong> (seller proposes), and <strong>granted discount</strong> (recorded deal outcome) are kept strictly distinct.
          </p>
        </div>
        <span class="status-pill">${esc(s02.human_reference_label)}</span>
      </div>

      <h3 style="font-size:1rem; margin: 0 0 8px;">Observed sales practices</h3>
      ${companyPatterns.map((p) => renderPatternCard(p, false)).join("")}

      <details class="page-more"><summary>More · Simulated practices (120 synthetic leads)</summary>
      ${simPatterns.map((p) => renderPatternCard(p, true)).join("")}
      </details>

      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-top: 14px;">
        <button type="button" class="btn btn-secondary" data-evidence-id="ev:culture-crm-blindness">
          See examples
        </button>
        <button type="button" class="btn btn-amber" onclick="navigateToFrame('S03')">
          Review possible drift →
        </button>
        ${deputyReturnAction()}
      </div>
    </div>
  `;
}

/* =========================================================================
   S03: Drift — Does this fit our agreement?
   ========================================================================= */
function renderS03(d) {
  const s03 = d.s03_drift;
  const isPreview = s03.is_preview_against_unapproved_rule;

  const cardsHtml = s03.cards.map((card) => {
    const originalHumanVerdict = card.human_verdict || HUMAN_VERDICT_LABELS[card.subq_verdict] || card.subq_verdict;
    const hasQuestion = Boolean(card.owner_override_verdict);
    const isQuestionOpen = stateStore.openQuestionCardId === card.card_id;

    let probHtml = "";
    if (Array.isArray(card.subq_pairs) && card.subq_pairs.length > 0) {
      const pairsRows = card.subq_pairs.map((pr) => {
        const vp = pr.probabilities || {};
        return `
          <div style="padding:8px 10px; border-bottom:1px solid var(--theseus-ice); font-size:0.8rem;">
            <div style="display:flex; justify-content:space-between; gap:8px; flex-wrap:wrap;">
              <strong>Pair ${pr.pair_index} (${esc(pr.pair_id)}): ${esc(pr.fixed_question)}</strong>
              <span class="status-pill">${esc(pr.verdict_label)} (conf ${Math.round((pr.confidence || 0) * 1000) / 10}%)</span>
            </div>
            <div class="muted" style="margin-top:4px;">
              <strong>Claim A [${esc(pr.claim_a.stage)} · ${esc(pr.claim_a.mandate_status)}]:</strong> ${esc(pr.claim_a.statement_sanitized)}
            </div>
            <div class="muted" style="margin-top:2px;">
              <strong>Claim B [${esc(pr.claim_b.stage)} · ${esc(pr.claim_b.mandate_status)}]:</strong> ${esc(pr.claim_b.statement_sanitized)}
            </div>
            <div class="mono muted" style="margin-top:3px; font-size:0.73rem;">
              SubQ Snap 1.1: insufficient_evidence=${Math.round((vp.insufficient_evidence || 0) * 1000) / 10}% ·
              different_scope_time=${Math.round((vp.different_scope_time || 0) * 1000) / 10}% ·
              consistent=${Math.round((vp.consistent || 0) * 1000) / 10}% ·
              contradictory=${Math.round((vp.contradictory || 0) * 1000) / 10}%
            </div>
          </div>
        `;
      }).join("");
      probHtml = `
        <div class="subcard" style="margin-top:8px; background:#ffffff; font-size:0.82rem;">
          <div style="margin-bottom:6px;">
            <strong>Recorded SubQ Snap 1.1 discount comparisons (5 pairs over 9 claims · 0 proven contradictions):</strong>
            <span class="muted">Per-claim status: 1 proposed founder principle (UNAPPROVED), 2 unapproved SOP/training norms, 6 observed acts (no blanket rule label).</span>
          </div>
          ${pairsRows}
        </div>
      `;
    } else if (card.subq_probabilities) {
      const p = card.subq_probabilities;
      probHtml = `
        <div class="subcard" style="margin-top:8px; background:#ffffff; font-size:0.82rem;">
          <strong>Recorded SubQ Snap 1.1 score breakdown:</strong>
          Contradictory: <strong>${Math.round(p.contradictory * 1000) / 10}%</strong> ·
          Different situation/scope: <strong>${Math.round(p.different_scope_time * 1000) / 10}%</strong> ·
          Not enough evidence: <strong>${Math.round(p.insufficient_evidence * 1000) / 10}%</strong> ·
          Confidence: <strong>${Math.round((card.subq_confidence || 0.286) * 1000) / 10}%</strong> (Uncertainty: ${Math.round((card.subq_uncertainty || 0.714) * 1000) / 10}%)
        </div>
      `;
    }

    return `
      <details class="alignment-finding" ${isQuestionOpen ? 'open' : ''}><summary>
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px; flex-wrap:wrap;">
          <div>
            <span class="status-pill ${provenanceBadgeClass(card.evidence_category)}">${esc(card.evidence_category)}</span>
            <h4 style="margin:6px 0 4px; font-size:1.04rem;">${esc({
              'drift-card-real-crm-blindness': 'CRM: discount outcomes remain unverified',
              'drift-card-subq-snap-pilot': 'Five comparisons: no proven contradiction',
              'drift-card-reactive-discount-conflict': 'Simulation: reactive discounts conflict with the rule',
            }[card.card_id] || card.title)}</h4>
          </div>
          <div style="text-align:right;">
            <div class="muted" style="font-size:0.74rem;">Model assessment</div>
            <span class="status-pill ${card.subq_verdict === "contradicts" || card.subq_verdict === "possible_conflict" ? "amber" : ""}">
              ${esc(originalHumanVerdict)}
            </span>
          </div>
        </div>

        </summary><div class="alignment-finding-body"><p class="muted">${esc(card.title)}</p>
        <p style="margin: 8px 0; font-size:0.9rem;">${esc(card.what_is_at_stake)}</p>
        <div class="muted" style="font-size:0.82rem;">
          <strong>Rule compared:</strong> ${esc(card.rule_ref)} · <strong>Observed/tested scope:</strong> ${esc(card.pattern_ref)}
        </div>
        <details class="page-more"><summary>More · Model assessment and evidence</summary>${probHtml}</details>

        ${hasQuestion ? `
          <div class="subcard highlight-teal" style="margin-top:10px; background:#ffffff;">
            <div style="font-size:0.84rem;">
              <strong>Your recorded review decision:</strong>
              <span class="status-pill teal">${esc(card.owner_override_human_label || card.owner_override_verdict)}</span>
              <span class="muted" style="margin-left:6px;">(Original model assessment "${esc(originalHumanVerdict)}" is preserved above for audit)</span>
            </div>
            <div class="muted" style="margin-top:4px;"><strong>Your reason:</strong> ${esc(card.owner_override_reason)}</div>
          </div>
        ` : ""}

        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-top:10px;">
          <div>
            ${card.evidence_ids.map((eid) => renderCiteButton(eid)).join("")}
          </div>
          <button type="button" class="btn btn-secondary btn-sm" data-toggle-question-card="${esc(card.card_id)}">
            ${isQuestionOpen ? "Cancel" : "Question this finding"}
          </button>
        </div>

        ${isQuestionOpen ? `
          <div class="subcard" style="margin-top:10px; background:#ffffff;">
            <h4 style="margin-top:0; font-size:0.9rem;">Question this finding (preserves original model assessment)</h4>
            <div class="grid-2">
              <div class="form-field" style="margin-bottom:8px;">
                <label for="q-verdict-${esc(card.card_id)}">Your assessment</label>
                <select id="q-verdict-${esc(card.card_id)}">
                  <option value="insufficient_evidence">Not enough evidence to decide</option>
                  <option value="different_scope">The rule applies to a different situation</option>
                  <option value="consistent">Fits our agreement</option>
                  <option value="contradicts">Contradicts our agreement</option>
                </select>
              </div>
              <div class="form-field" style="margin-bottom:8px;">
                <label for="q-reason-${esc(card.card_id)}">Reason for questioning</label>
                <input type="text" id="q-reason-${esc(card.card_id)}" placeholder="e.g., Training norm was never approved as company rule" value="Training norm was not confirmed as a binding rule; CRM outcome data is missing." />
              </div>
            </div>
            <button type="button" class="btn btn-sm" data-submit-question-card="${esc(card.card_id)}">
              Save my review note
            </button>
          </div>
        ` : ""}

        <details style="margin-top:8px;">
          <summary class="muted" style="cursor:pointer; font-size:0.78rem;">Technical details (card ID, rule ID &amp; rubric)</summary>
          <div class="mono muted" style="margin-top:4px; font-size:0.74rem;">
            Card ID: ${esc(card.card_id)} · Rule ID: ${esc(card.technical_rule_id)} · Raw verdict: ${esc(card.subq_verdict)}
          </div>
        </details>
      </div></details>
    `;
  }).join("");

  const fiveArea = s03.five_area_reading || {};
  const fiveHtml = Object.entries(fiveArea).map(([area, text]) => `
    <div class="subcard">
      <div class="card-kicker">${esc(area)}</div>
      <p style="margin:6px 0 0; font-size:0.82rem;">${esc(text)}</p>
    </div>
  `).join("");

  return `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 class="card-title">Does this fit our agreement?</h2>
          <p class="muted" style="margin:0;">${esc(s03.historical_scope_note)}</p>
        </div>
        <span class="status-pill ${isPreview ? "amber" : "teal"}">
          ${isPreview ? "Preview against proposed rule" : "Compared against confirmed direction"}
        </span>
      </div>

      <div class="subcard ${isPreview ? "highlight-amber" : "highlight-teal"}" style="margin-bottom: 14px;">
        <div><strong>${esc(s03.active_reference_label)}</strong></div>
        <div class="muted" style="margin-top:2px;">${esc(s03.proposed_reference_label)}</div>
      </div>

      ${cardsHtml}

      <details class="page-more"><summary>More · Impact across the business</summary>
        <div class="grid-5">
          ${fiveHtml}
        </div>
      </details>

      <div style="display:flex; justify-content:flex-end; gap:8px; flex-wrap:wrap; margin-top: 14px;">
        <button type="button" class="btn btn-amber" onclick="navigateToFrame('S04')">
          Review a correction →
        </button>
        ${deputyReturnAction()}
      </div>
    </div>
  `;
}

function toggleQuestionFinding(cardId) {
  stateStore.openQuestionCardId = stateStore.openQuestionCardId === cardId ? null : cardId;
  renderAll();
}

async function submitQuestionFinding(cardId) {
  const sel = document.getElementById("q-verdict-" + cardId);
  const rsn = document.getElementById("q-reason-" + cardId);
  const verdict = sel ? sel.value : "different_scope";
  const reason = rsn ? rsn.value : "Founder recorded a review note.";
  try {
    await postApi("/api/drift/override", { card_id: cardId, verdict, reason });
    stateStore.openQuestionCardId = null;
    renderAll();
  } catch (err) {
    alert("Could not save review note: " + err.message);
  }
}

/* =========================================================================
   S04: Correction — Change how work happens
   ========================================================================= */
function renderS04(d) {
  const s04 = d.s04_proposal;
  const diffs = s04.three_lever_diffs || {};
  const cc = d.s05_application.cross_cutting_states || {};

  const leverCards = [
    {
      num: "Change 1 · Automated Sales Agents",
      title: "Agent discount rule: 5% ceiling + required customer commitment",
      affected: "Automated sales agents (3 modeled agents)",
      authority: "Requires founder approval before updating active agent runtime",
      readiness: (cc.sales_agents_rule_v2 && cc.sales_agents_rule_v2.applied) || "Proposed change — not applied",
      before: (diffs.sales_agents_rule && diffs.sales_agents_rule.before_summary) || "Up to 5% automatic discount without checking whether the customer offered any commitment in return.",
      after: (diffs.sales_agents_rule && diffs.sales_agents_rule.after_summary) || "Any discount (even up to 5%) requires a verified customer commitment (longer term, prepayment, referral, or volume); >5% escalates to a human.",
      beforeBadge: "Simulation baseline",
      cost: "Ready in sandbox (0 extra LLM calls)",
      tech: "rule-v1 → rule-v2 · app/runtime/__init__.py",
    },
    {
      num: "Change 2 · Human Sales Team",
      title: "Seller guidance: value-first objection handling before price concessions",
      affected: "Human account executives (3 modeled sellers in simulation)",
      authority: "Sales leadership rollout following founder approval",
      readiness: (cc.human_sellers_onboarding_v2 && cc.human_sellers_onboarding_v2.applied) || "Proposed change — not applied",
      before: "Modeled in simulation (not a measured historical company rate): sellers offer 10–15% discounts on the first price objection without recording a reason in CRM.",
      after: (diffs.human_sellers_onboarding && diffs.human_sellers_onboarding.after_summary) || "Confirm customer need and value first; offer a discount only in exchange for term, prepayment, volume, or referral, and record the reason in CRM.",
      beforeBadge: "Simulation",
      cost: "Team enablement & coaching effort: Not estimated",
      tech: "onboarding-v1 → onboarding-v2 · Sales Playbook",
    },
    {
      num: "Change 3 · CRM Environment",
      title: "Required CRM field: Reason for discount",
      affected: "Every discounted deal saved in the CRM",
      authority: "Requires founder approval before enabling in CRM",
      readiness: (cc.environment_crm_field_v2 && cc.environment_crm_field_v2.applied) || "Proposed change — not applied",
      before: "Company evidence: 0 of 6,102 CRM deals record a discount reason; discounted deals can be saved with no explanation.",
      after: (diffs.environment_crm_schema && diffs.environment_crm_schema.after_summary) || "Whenever a discount is above 0%, the CRM requires a 'Reason for discount' (Longer contract term, Upfront prepayment, Verified customer referral, Higher committed volume, or Other with written explanation).",
      beforeBadge: "Company evidence",
      cost: "Ready in Demo CRM sandbox · Production CRM migration effort/budget: Not estimated",
      tech: "crm-v1 → crm-v2 · discount_justification required field",
    },
  ];

  const rowsHtml = Object.values(cc).map((row) => `
    <tr>
      <td><strong>${esc(row.lever)}</strong><div class="muted">${esc(row.actor_scope)}</div></td>
      <td>${esc(row.received)}</td>
      <td>${esc(row.understood)}</td>
      <td><span class="status-pill ${row.applied.includes("Active") || row.applied.includes("Applied") ? "teal" : "amber"}">${esc(row.applied)}</span></td>
      <td>${esc(row.observed_in_behavior)}</td>
    </tr>
  `).join("");

  return `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 class="card-title">Change how work happens</h2>
          <p class="muted" style="margin:0;">
            What changes, who is affected, and what it requires across agents, human sellers, and the CRM environment.
          </p>
        </div>

      </div>

      <div class="grid-3">
        ${leverCards.map((c, index) => `
          <div class="subcard change-lane change-lane-${index}">
            <div class="change-lane-label"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${[
              '<rect x="4" y="7" width="16" height="13" rx="3"/><path d="M12 3v4M8 12h.01M16 12h.01M8 16h8M2 11v5M22 11v5"/>',
              '<circle cx="9" cy="7" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M17 4a3 3 0 0 1 0 6M18 14a5 5 0 0 1 3 4v3"/>',
              '<rect x="3" y="3" width="18" height="14" rx="2"/><path d="M8 21h8M12 17v4M3 8h18M8 8v9"/>'
            ][index]}</svg><span>${['Agents', 'People', 'Environment'][index]}</span></div>
            <h4 style="margin-top:4px;">${esc(c.title)}</h4>
            <div class="muted" style="font-size:0.8rem; margin-bottom:6px;">
              <strong>Who is affected:</strong> ${esc(c.affected)}<br/>
              <strong>Readiness:</strong> ${esc(c.readiness)}<br/>
              <strong>Effort / cost:</strong> ${esc(c.cost)}
            </div>
            <details class="page-more"><summary>More · Previous approach</summary><div class="diff-box diff-old">
              <strong>Before:</strong>
              <span class="status-pill ${c.beforeBadge.includes("Simulation") ? "amber" : "teal"}" style="margin:0 4px;">${esc(c.beforeBadge)}</span>
              ${esc(c.before)}
            </div>
            </details><div class="diff-box diff-new"><strong>After (proposed):</strong> ${esc(c.after)}</div>
            <details style="margin-top:8px;">
              <summary class="muted" style="cursor:pointer; font-size:0.76rem;">Technical diff ID</summary>
              <div class="mono muted" style="font-size:0.73rem; margin-top:4px;">${esc(c.tech)}</div>
            </details>
          </div>
        `).join("")}
      </div>

      <details style="margin-top: 14px;">
        <summary style="cursor:pointer; font-weight:600; font-size:0.86rem; color:var(--theseus-ink);">
          More · Rollout stages and evidence
        </summary>
        <div class="table-scroll" style="margin-top:10px;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Change Lever &amp; Affected Group</th>
                <th>Proposed</th>
                <th>Tested / Understood</th>
                <th>Applied Status</th>
                <th>Observed after Application</th>
              </tr>
            </thead>
            <tbody>
              ${rowsHtml}
            </tbody>
          </table>
        </div>
      </details>

      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-top: 16px;">
        <div>
          ${renderCiteButton("ev:codex-ep-80901", "See source: founder direction")}
          ${renderCiteButton("ev:culture-crm-blindness", "See source: CRM data completeness check")}
        </div>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
          <button type="button" class="btn btn-secondary" onclick="navigateToFrame('S05')">
            Request changes
          </button>
          <button type="button" class="btn btn-amber" onclick="navigateToFrame('S05')">
            Review decision →
          </button>
          ${deputyReturnAction()}
        </div>
      </div>
    </div>
  `;
}

/* =========================================================================
   S05: Apply — Your decision, then execution + Embedded Demo CRM
   ========================================================================= */
function renderS05(d) {
  const s05 = d.s05_application;
  const dec = s05.decision_record;
  const evalRep = s05.evaluation_report;
  const act = s05.activation_receipt;
  const rb = s05.rollback_receipt;
  const isApproved = dec && dec.action === "approve";
  const isApplied = s05.active_runtime_version === "tool-v2";

  let decisionBanner = `<span class="status-pill amber">Awaiting your decision</span>`;
  if (dec) {
    const pillClass = dec.action === "approve" ? "teal" : (dec.action === "reject" ? "danger" : "amber");
    decisionBanner = `<span class="status-pill ${pillClass}">${esc(dec.human_decision_label || dec.action)}</span>`;
  }

  const subRows = (s05.crm_submissions || []).map((s) => `
    <tr>
      <td class="mono">${esc(s.deal_id)}</td>
      <td>${s.actor_type === "sales_agent" ? "Automated sales agent" : "Human seller"}</td>
      <td>${Number(s.list_amount_rub).toLocaleString()} → <strong>${Number(s.final_amount_rub).toLocaleString()} RUB</strong></td>
      <td><strong>${s.discount_pct}%</strong></td>
      <td><span class="status-pill teal">${esc(HUMAN_REASON_LABELS[s.discount_justification] || s.discount_justification || "None")}</span></td>
      <td>
        <span class="status-pill ${s.tool_allowed ? "teal" : "amber"}">
          ${s.tool_allowed ? "Allowed by active rule" : "Escalated: " + esc((s.tool_reasons || []).join(", "))}
        </span>
      </td>
    </tr>
  `).join("");

  return `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 class="card-title">Your decision, then execution</h2>
          <p class="muted" style="margin:0;">
            Approval and application are separate steps: first record your decision, then apply the approved change in the demo environment.
          </p>
        </div>
        <span class="status-pill ${isApplied ? "teal" : "amber"}">
          ${esc(s05.human_active_runtime_label)}
        </span>
      </div>

      <div class="grid-2">
        <div class="subcard highlight-amber">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <h4 style="margin:0;">1. Your decision on the three-part correction</h4>
            ${decisionBanner}
          </div>
          <p class="muted" style="margin: 8px 0;">
            Decide whether to approve the agent discount rule (5% cap + customer commitment), seller guidance, and the required "Reason for discount" CRM field.
          </p>
          <div class="form-field">
            <label for="decide-rationale">Decision note (saved in audit log)</label>
            <input type="text" id="decide-rationale" value="${esc(dec ? dec.rationale : "Approve agent discount rule, seller guidance, and required Reason for discount field in CRM.")}" />
          </div>
          <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <button type="button" class="btn btn-amber" onclick="handleProposalDecision('approve')">
              Approve this correction
            </button>
            <button type="button" class="btn btn-secondary" onclick="handleProposalDecision('request_clarification')">
              Request changes
            </button>
            <button type="button" class="btn btn-secondary" onclick="handleProposalDecision('reject')">
              Reject
            </button>

          </div>
          ${dec ? `
            <div style="margin-top:10px; font-size:0.84rem;">
              <strong>Saved decision:</strong> ${esc(dec.human_decision_label || dec.action)} · <span class="muted">${esc(dec.rationale)}</span>
            </div>
          ` : ""}
        </div>

        <div class="subcard highlight-teal">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <h4 style="margin:0;">2. Simulation check &amp; application</h4>
            <span class="status-pill ${isApplied ? "teal" : "amber"}">
              ${isApplied ? "Applied in demo" : (isApproved ? "Ready to apply in demo" : "Locked until approved")}
            </span>
          </div>
          <div style="margin: 10px 0; padding: 10px; background:#ffffff; border-radius:8px; border:1px solid var(--theseus-ice); font-size:0.84rem;">
            <div><strong>Pre-application check:</strong> <span class="status-pill amber">Tested in simulation</span></div>
            <div style="margin-top:4px;">60 of 60 simulated agent leads matched the proposed rule with 0 regressions.</div>
            <div class="muted" style="margin-top:2px; font-size:0.78rem;">${esc(evalRep.limitations || "Prepared simulation gate on 60 synthetic agent leads; not an independent held-out real-world benchmark.")}</div>
          </div>

          ${!isApproved ? `
            <p class="muted" style="margin: 8px 0;">
              <strong>Why application is unavailable:</strong> Please click <strong>Approve this correction</strong> in Step 1 on the left before applying the change in the demo environment.
            </p>
          ` : ""}

          <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
            <button type="button" class="btn btn-teal" onclick="handleActivateCandidate()" ${!isApproved || isApplied ? "disabled" : ""}>
              ${isApplied ? "Applied in demo ✓" : "Apply in demo"}
            </button>

            ${isApplied ? `
              <button type="button" class="btn btn-secondary" onclick="handleRollbackCandidate()">
                Roll back to previous baseline
              </button>
            ` : ""}
          </div>

          ${act && isApplied ? `
            <div style="margin-top:10px; font-size:0.84rem; color:#14594f;">
              <strong>Active in demo:</strong> Agent rule and required CRM field are now active (applied at ${esc(act.applied_at)}).
            </div>
          ` : ""}
          ${rb && !isApplied ? `
            <div style="margin-top:10px; font-size:0.84rem; color:#8a1f1f;">
              <strong>Rolled back:</strong> Restored previous baseline rule at ${esc(rb.applied_at)}.
            </div>
          ` : ""}
        </div>
      </div>

      <div class="page-actions"><a class="btn btn-secondary" href="#S06">View outcomes</a>${deputyReturnAction()}</div>
      <details style="margin-top:10px;">
        <summary class="muted" style="cursor:pointer; font-size:0.8rem;">More · Decision record and receipts</summary>
        <div class="mono muted" style="margin-top:4px; font-size:0.74rem;">
          Active runtime ID: ${esc(s05.active_runtime_version)} ·
          Decision ID: ${esc(dec ? dec.decision_id : "none")} ·
          Evaluation ID: ${esc(evalRep.evaluation_id)} (${esc(evalRep.split)}) ·
          Activation receipt: ${esc(act ? act.receipt_id : "none")}
        </div>
      </details>
    </div>

    <details id="crm-test-panel" class="card page-more"><summary>More · Test the change in Demo CRM</summary>
      <div class="card-header">
        <div>
          <div class="card-kicker">Interactive Verification · Same-Input Before / After Demo CRM Check</div>
          <h3 class="card-title" style="font-size:1.15rem;">Test the same 5% discount before &amp; after applying the correction</h3>
          <p class="muted" style="margin:0;">
            ${isApplied
              ? "Updated rule (tool-v2 + crm-v2) is ACTIVE: saving a 5% discount with no customer commitment is now BLOCKED. Select 'Upfront prepayment' or 'Longer contract term' to pass."
              : "Baseline rule (tool-v1 + crm-v1) is ACTIVE: saving a 5% discount with no customer commitment currently PASSES. Approve & apply above, then click Save again with the exact same input to see it blocked."}
          </p>
        </div>
        <span class="status-pill ${isApplied ? "teal" : "amber"}">
          ${isApplied ? "Active: crm-v2 + tool-v2 (commitment required)" : "Baseline: crm-v1 + tool-v1 (no commitment required)"}
        </span>
      </div>

      <div class="grid-3">
        <div class="form-field">
          <label for="crm-deal-code">Deal reference</label>
          <input type="text" id="crm-deal-code" value="DEMO-${101 + (s05.crm_submissions || []).length}" />
        </div>
        <div class="form-field">
          <label for="crm-actor-type">Seller type</label>
          <select id="crm-actor-type">
            <option value="sales_agent">Automated sales agent (5% cap)</option>
            <option value="simulated_human_seller">Human seller</option>
          </select>
        </div>
        <div class="form-field">
          <label for="crm-list-amount">List amount (RUB)</label>
          <input type="number" id="crm-list-amount" value="300000" step="10000" />
        </div>
      </div>

      <div class="grid-3">
        <div class="form-field">
          <label for="crm-discount-pct">Proposed discount (%)</label>
          <input type="number" id="crm-discount-pct" value="5" min="0" max="50" step="1" />
        </div>
        <div class="form-field">
          <label for="crm-justification">Reason for discount (${isApplied ? "required in crm-v2 when discount &gt; 0%" : "optional in baseline crm-v1"})</label>
          <select id="crm-justification">
            <option value="" selected>-- No customer commitment selected (passes in v1, blocked in v2) --</option>
            <option value="prepayment">Upfront prepayment (customer commitment)</option>
            <option value="longer_term">Longer contract term (customer commitment)</option>
            <option value="referral">Verified customer referral (customer commitment)</option>
            <option value="volume">Higher committed volume (customer commitment)</option>
            <option value="other_with_text">Other reason (requires written explanation)</option>
          </select>
        </div>
        <div class="form-field">
          <label for="crm-justification-text">Written explanation (required if "Other reason")</label>
          <input type="text" id="crm-justification-text" placeholder="Customer commitment details..." />
        </div>
      </div>

      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
          <button type="button" class="btn" onclick="handleSubmitCrmDeal()">
            Save deal in Demo CRM
          </button>
          <span id="crm-feedback" style="font-size:0.85rem; font-weight:600;"></span>
        </div>
        <button type="button" class="btn btn-amber" onclick="navigateToFrame('S06')">
          See outcomes (Step 6) →
        </button>
        ${deputyReturnAction()}
      </div>

      ${subRows ? `
        <div class="table-scroll" style="margin-top:14px;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Deal</th>
                <th>Seller Type</th>
                <th>Amount</th>
                <th>Discount</th>
                <th>Reason for Discount</th>
                <th>Rule Check</th>
              </tr>
            </thead>
            <tbody>${subRows}</tbody>
          </table>
        </div>
      ` : ""}
    </details>
  `;
}

async function handleProposalDecision(decision) {
  const rEl = document.getElementById("decide-rationale");
  const rationale = rEl ? rEl.value : "";
  try {
    await postApi("/api/decide/approve", { decision, rationale });
    renderAll();
  } catch (err) {
    alert("Could not record decision: " + err.message);
  }
}

async function handleActivateCandidate() {
  try {
    await postApi("/api/decide/activate", {});
    renderAll();
  } catch (err) {
    alert("Application blocked: " + err.message);
  }
}

async function handleRollbackCandidate() {
  try {
    await postApi("/api/decide/rollback", {
      rationale: "Founder rolled back from updated rule to previous baseline.",
    });
    renderAll();
  } catch (err) {
    alert("Rollback failed: " + err.message);
  }
}

async function handleSubmitCrmDeal() {
  const payload = {
    deal_code: document.getElementById("crm-deal-code").value,
    actor_type: document.getElementById("crm-actor-type").value,
    list_amount_rub: Number(document.getElementById("crm-list-amount").value || 300000),
    discount_pct: Number(document.getElementById("crm-discount-pct").value || 0),
    discount_justification: document.getElementById("crm-justification").value || null,
    justification_text: document.getElementById("crm-justification-text").value || null,
  };
  try {
    const res = await postApi("/api/crm/submit", payload);
    renderAll();
    const fb = document.getElementById("crm-feedback");
    if (fb) {
      fb.style.color = "#14594f";
      const rLabel = HUMAN_REASON_LABELS[res.deal.discount_justification] || "No customer commitment recorded";
      fb.textContent = `✓ Saved ${res.deal.deal_id} under ${res.deal.crm_schema_version} / ${res.deal.active_tool_version} (${rLabel})`;
    }
  } catch (err) {
    renderAll();
    const fb = document.getElementById("crm-feedback");
    if (fb) {
      fb.style.color = "#8a1f1f";
      fb.textContent = `✗ Blocked by ${stateStore.data && stateStore.data.s05_application ? stateStore.data.s05_application.active_crm_schema_version + " / " + stateStore.data.s05_application.active_runtime_version : "CRM"}: ${err.message}`;
    }
  }
}

async function handleResetDemoSession() {
  try {
    const res = await postApi("/api/reset", {});
    stateStore.s01EditOpen = false;
    stateStore.openQuestionCardId = null;
    const c = stateStore.data.s01_commit;
    stateStore.s01Draft.goal_text = c.intent_and_goal.proposed_text;
    stateStore.s01Draft.principle_text = c.governing_principle.proposed_text;
    stateStore.s01Draft.risk_text = c.culture_to_protect.risk_to_watch;
    closeEvidenceDrawer(false);
    navigateToFrame("S01");
    renderAll();
    console.info("Reset demo session to C0:", res.reset);
  } catch (err) {
    alert("Reset failed: " + err.message);
  }
}

async function handleRunFreshSimulation() {
  const btn = document.getElementById("run-fresh-sim-btn");
  if (btn) btn.disabled = true;
  try {
    await postApi("/api/simulate/run", { seed: 20261107 });
    renderAll();
  } catch (err) {
    alert("Simulation run failed: " + err.message);
  } finally {
    const b2 = document.getElementById("run-fresh-sim-btn");
    if (b2) b2.disabled = false;
  }
}

/* =========================================================================
   S06: Outcome — Did the change help? (Simulation clearly labeled)
   ========================================================================= */
function renderS06(d) {
  const s06 = d.s06_track;
  const ui = s06.ui_metrics || {};
  const arms = ui.arms || {};
  const before = (arms.before && arms.before.overall) || {
    leads_total: 120,
    discounted_count: 84,
    justified_discount_count: 26,
    value_exchange_discount_count: 26,
    codex_consistent_count: 62,
    discount_offer_rate_pct: 70.0,
    justified_discount_share_pct: 31.0,
    value_exchange_share_pct: 31.0,
    codex_consistency_rate_pct: 51.7,
    avg_discount_pct_when_offered: 12.98,
  };
  const combined = (arms.combined && arms.combined.overall) || {
    leads_total: 120,
    discounted_count: 68,
    justified_discount_count: 68,
    value_exchange_discount_count: 64,
    codex_consistent_count: 116,
    discount_offer_rate_pct: 56.7,
    justified_discount_share_pct: 100.0,
    value_exchange_share_pct: 94.1,
    codex_consistency_rate_pct: 96.7,
    avg_discount_pct_when_offered: 7.42,
  };
  const isApplied = Boolean(s06.is_candidate_active_in_runtime);

  const armDisplayNames = {
    before: "Baseline (before changes)",
    agent_rule_only: "Agent rule change only",
    onboarding_only: "Seller guidance change only",
    crm_field_only: "Required CRM field only",
    combined: "All three changes combined",
  };

  const armRows = ["before", "agent_rule_only", "onboarding_only", "crm_field_only", "combined"].map((k) => {
    const m = (arms[k] && arms[k].overall) || before;
    const rec = k === "before"
      ? "Baseline reference"
      : (k === "onboarding_only" ? "Recommendation: Keep candidate (needs real-team observation)" : "Recommendation: Keep");
    return `
      <tr>
        <td><strong>${esc(armDisplayNames[k] || k)}</strong></td>
        <td>${m.discounted_count} / ${m.leads_total} (${m.discount_offer_rate_pct}%)</td>
        <td><strong>${m.justified_discount_count} / ${m.discounted_count}</strong> (${m.justified_discount_share_pct}%)</td>
        <td><strong>${m.value_exchange_discount_count} / ${m.discounted_count}</strong> (${m.value_exchange_share_pct}%)</td>
        <td><strong>${m.codex_consistent_count} / ${m.leads_total}</strong> (${m.codex_consistency_rate_pct}%)</td>
        <td>${m.avg_discount_pct_when_offered}%</td>
        <td><span class="status-pill ${k === "before" ? "" : (k === "onboarding_only" ? "amber" : "teal")}">${esc(rec)}</span></td>
      </tr>
    `;
  }).join("");

  const weeklyList = Array.isArray(ui.weekly_timeline) ? ui.weekly_timeline : [];
  const weekRows = weeklyList.map((wk) => {
    const all = wk.overall || before;
    return `
      <tr>
        <td><strong>${esc(wk.period)}</strong> · ${esc(wk.stage_label)}</td>
        <td><strong>${all.justified_discount_count} / ${all.discounted_count}</strong> (${all.justified_discount_share_pct}%)</td>
        <td><strong>${all.value_exchange_discount_count} / ${all.discounted_count}</strong> (${all.value_exchange_share_pct}%)</td>
        <td><strong>${all.codex_consistent_count} / ${all.leads_total}</strong> (${all.codex_consistency_rate_pct}%)</td>
      </tr>
    `;
  }).join("");

  return `
    <div class="sim-banner">
      <span>SIMULATION · 120 synthetic leads · Business outcomes not yet measured</span>
      <span class="status-pill ${isApplied ? "teal" : "amber"}">
        ${isApplied ? "Candidate currently applied in demo" : "Evaluated in simulation only — baseline rule is still active in demo"}
      </span>
    </div>

    <div class="card">
      <div class="card-header">
        <div>
          <h2 class="card-title">Did the change help?</h2>
          <p class="muted" style="margin:0;">
            Matched comparison on the same 120 synthetic leads (60 automated sales agent leads + 60 modeled human seller leads).
          </p>
        </div>
        <div style="display:flex; gap:8px; align-items:center;">

          <span class="status-pill amber">Simulation</span>
        </div>
      </div>

      <div class="grid-3">
        <div class="subcard highlight-teal">
          <div class="card-kicker">Metric 1 · Customer Commitment for Discounts</div>
          <h4 style="margin:6px 0; font-size:1.15rem;">
            ${before.value_exchange_discount_count}/${before.discounted_count} (${before.value_exchange_share_pct}%)
            → <strong>${combined.value_exchange_discount_count}/${combined.discounted_count} (${combined.value_exchange_share_pct}%)</strong>
          </h4>
          <p class="muted" style="margin:0;">
            Share of offered discounts backed by longer term, prepayment, volume, or referral across the 120-lead simulated cohort.
          </p>
        </div>

        <div class="subcard highlight-glacier">
          <div class="card-kicker">Metric 2 · Deals Matching Agreed Direction</div>
          <h4 style="margin:6px 0; font-size:1.15rem;">
            ${before.codex_consistent_count}/${before.leads_total} (${before.codex_consistency_rate_pct}%)
            → <strong>${combined.codex_consistent_count}/${combined.leads_total} (${combined.codex_consistency_rate_pct}%)</strong>
          </h4>
          <p class="muted" style="margin:0;">
            Automated sales agents reach 60/60 (100%) immediately when the rule is updated; required CRM field blocks unreasoned deal entry.
          </p>
        </div>

        <div class="subcard highlight-amber">
          <div class="card-kicker">Metric 3 · Average Discount When Offered</div>
          <h4 style="margin:6px 0; font-size:1.15rem;">
            ${before.avg_discount_pct_when_offered}% → <strong>${combined.avg_discount_pct_when_offered}%</strong>
          </h4>
          <p class="muted" style="margin:0;">
            <strong>What remains uncertain:</strong> Human seller guidance improves modeled consistency from 61.7% (37/60) to 70.0% (42/60), but real human compliance has not yet been observed in production.
          </p>
        </div>
      </div>

      <div class="subcard" style="margin-top: 14px;">
        <h4 style="margin-top:0;">Conclusion &amp; recommendation from simulation</h4>
        <p style="margin: 4px 0; font-size:0.9rem;">
          In simulation, combining the <strong>agent discount rule</strong> (Recommendation: <strong>Keep</strong>) and the <strong>required CRM "Reason for discount" field</strong> (Recommendation: <strong>Keep</strong>) eliminates unrecorded discounts (${combined.justified_discount_count}/${combined.discounted_count} recorded with reason). <strong>Seller guidance alone</strong> (Recommendation: <strong>Keep candidate — monitor real team</strong>) helps gradually but cannot replace the structural CRM requirement.
        </p>
        <p class="muted" style="margin: 4px 0 0;">
          ${isApplied
            ? "The three-part correction is currently applied in the demo runtime. You can keep it active and return to direction review, or roll back to the previous baseline below."
            : "Note: The proposed correction has not been applied to the active demo runtime yet (baseline rule is still active). To apply it in the demo, use Step 5."}
        </p>
      </div>

      <details style="margin-top: 14px;">
        <summary style="cursor:pointer; font-weight:600; font-size:0.86rem; color:var(--theseus-ink);">
          More · Simulation breakdown, timeline and rerun
        </summary>
<p class="muted">Seed: ${esc(ui.seed || 20261107)} · Run: ${esc(ui.last_simulation_run_at || "")}</p>          <button type="button" class="btn btn-secondary btn-sm" id="run-fresh-sim-btn" onclick="handleRunFreshSimulation()">
            Re-run matched simulation (seed 20261107)
          </button>
        <div class="table-scroll" style="margin-top:10px;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Simulation Cohort Arm (120 leads each)</th>
                <th>Discounts Offered</th>
                <th>CRM Reason Recorded</th>
                <th>Backed by Customer Commitment</th>
                <th>Fits Agreed Direction</th>
                <th>Avg Discount</th>
                <th>Simulation Recommendation</th>
              </tr>
            </thead>
            <tbody>${armRows}</tbody>
          </table>
        </div>

        <div class="table-scroll" style="margin-top:14px;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Synthetic Week &amp; Stage</th>
                <th>CRM Reason Recorded</th>
                <th>Backed by Customer Commitment</th>
                <th>Fits Agreed Direction</th>
              </tr>
            </thead>
            <tbody>${weekRows}</tbody>
          </table>
        </div>
      </details>

      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-top: 16px;">
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
          ${!isApplied ? `
            <button type="button" class="btn btn-secondary" onclick="navigateToFrame('S05')">
              Review implementation decision
            </button>
          ` : `
            <button type="button" class="btn btn-secondary" onclick="handleRollbackCandidate()">
              Roll back to previous baseline
            </button>
          `}
        </div>
        <button type="button" class="btn btn-amber" onclick="navigateToFrame('S01')">
          Review agreement
        </button>
        ${deputyReturnAction()}
      </div>
    </div>
  `;
}

function commitmentRows(d) {
  const c = d.s01_commit;
  const confirmed = c.mandate_status === 'committed_mandate';
  const version = c.committed_version;
  const common = { version, confirmed, confirmedAt: c.effective_time, approvedBy: c.approved_by };
  return [
    { ...common, id: confirmed ? c.intent_and_goal.id : 'goal-v1:quarterly-pipeline', kind: 'Goal',
      text: confirmed ? c.intent_and_goal.proposed_text : c.intent_and_goal.previous_text,
      target: confirmed ? c.intent_and_goal.success_measure : 'Quarterly pipeline targets; numeric target not recorded in this baseline.',
      metric: 'avg_discount_pct_when_offered', metricLabel: 'Average offered discount', gap: 'Verified revenue and list-price realization are not measured. Offered discount is a simulation proxy.' },
    { ...common, id: confirmed ? c.governing_principle.id : 'codex-v1:flexible-discounts', kind: 'Rule / principle',
      text: confirmed ? c.governing_principle.proposed_text : c.governing_principle.previous_text,
      target: confirmed ? c.governing_principle.authority_boundary : 'Flexible seller discounts; proposed reciprocity rule remains unconfirmed.',
      metric: 'value_exchange_share_pct', metricLabel: 'Discounts with customer commitment', gap: 'Historical CRM discount outcomes and reciprocity are not established.' },
    { ...common, id: 'culture:value-before-price', kind: 'Culture', text: c.culture_to_protect.protect,
      target: c.culture_to_protect.risk_to_watch, pending: !confirmed, metric: null,
      gap: 'No direct culture-outcome metric. Conversation evidence and risk hypotheses require review.' },
    { ...common, id: 'monitoring:discount-exceptions', kind: 'Monitoring', text: c.monitoring_mandate.signals_watched.join('; '),
      target: c.monitoring_mandate.escalation_criteria, pending: !confirmed, metric: null,
      gap: c.monitoring_mandate.known_coverage_gap }
  ];
}

function commitmentList(d) {
  if (Array.isArray(d.commitments)) return d.commitments.map(row => ({
    ...row, confirmedAt: row.confirmed_at || row.accepted_at || null,
    changedAt: row.updated_at || row.confirmed_at || row.accepted_at || null,
    confirmed: row.status === 'confirmed', pending: row.status === 'proposed',
  }));
  const c = d.s01_commit;
  const confirmed = c.mandate_status === 'committed_mandate';
  const sections = commitmentRows(d);
  return [{
    id: 'mandate:' + d.organization_id, key: 'snapshot:mandate', kind: 'Agreement',
    text: sections[0].text?.split(/(?<=[.!?])\s/)[0] || 'Current direction',
    version: c.committed_version, confirmed, approvedBy: c.approved_by,
    confirmedAt: confirmed ? c.effective_time : null,
    changedAt: confirmed ? c.effective_time : null, sections,
  }];
}

function commitmentSeenKey(d) {
  return 'theseus.commitments.reviewed.packages.' + d.organization_id + '.' + d.demo_session_id;
}

function commitmentFingerprint(row) {
  const value = JSON.stringify([row.text, row.target, row.version, row.confirmed, row.pending, row.changedAt, row.sections]);
  let hash = 2166136261;
  for (let i = 0; i < value.length; i++) hash = Math.imul(hash ^ value.charCodeAt(i), 16777619);
  return (hash >>> 0).toString(16);
}

function commitmentReviewState(d, rows) {
  let seen = null;
  try { seen = JSON.parse(localStorage.getItem(commitmentSeenKey(d))); } catch (_) {}
  if (!seen || typeof seen !== 'object' || Array.isArray(seen)) {
    seen = Object.fromEntries(rows.map(row => [row.key || row.id, commitmentFingerprint(row)]));
    try { localStorage.setItem(commitmentSeenKey(d), JSON.stringify(seen)); } catch (_) {}
  }
  return seen;
}

function markCommitmentsReviewed() {
  const d = stateStore.data;
  const seen = Object.fromEntries(commitmentList(d).map(row => [row.key || row.id, commitmentFingerprint(row)]));
  try { localStorage.setItem(commitmentSeenKey(d), JSON.stringify(seen)); }
  catch (_) { alert('This browser cannot save review markers.'); return; }
  renderAll();
}

function commitmentDate(value) {
  if (!value) return 'Date not recorded';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Date not recorded' :
    date.toLocaleString('en-US', {month:'short', day:'numeric', year:'numeric', hour:'2-digit', minute:'2-digit'});
}

async function refreshCommitments() {
  try { await fetchState(); }
  catch (_) {
    const feedback = document.getElementById('commitments-feedback');
    if (feedback) feedback.textContent = 'Could not refresh. Your displayed list is unchanged; try again.';
  }
}

async function checkCommitmentUpdates() {
  if (document.hidden || stateStore.currentFrame !== 'COMMITMENTS') return;
  try {
    const response = await fetch('/api/state');
    if (!response.ok) return;
    const payload = await response.json();
    const next = payload.state || payload;
    if (JSON.stringify(commitmentList(next)) !== JSON.stringify(commitmentList(stateStore.data))) {
      stateStore.data = next;
      renderAll();
    }
  } catch (_) { /* Keep the last successfully loaded list; manual refresh reports errors. */ }
}

function renderCommitments(d) {
  const rows = commitmentList(d).map((row, index) => ({ ...row, displayNumber: index + 1 }));
  const seen = commitmentReviewState(d, rows);
  const changes = row => !Object.hasOwn(seen, row.key || row.id) ? 'New' :
    seen[row.key || row.id] !== commitmentFingerprint(row) ? 'Updated' : '';
  rows.sort((a,b) => Number(Boolean(changes(b))) - Number(Boolean(changes(a))) ||
    (Date.parse(b.changedAt) || 0) - (Date.parse(a.changedAt) || 0));
  const changedCount = rows.filter(changes).length;
  const c = d.s01_commit;
  return `<section class="commitments-page" aria-labelledby="commitments-title">
    <header class="commitments-heading"><div><h2 id="commitments-title">Commitments</h2>
    <p>${Array.isArray(d.commitments) ? 'What we agreed, and when.' : 'One agreement · One goal, with a rule, a cultural principle and monitoring.'}</p></div>
    <a class="btn btn-secondary" href="#S01">Review direction</a></header>
    <div class="commitments-toolbar">
      <span role="status">${changedCount ? `<strong>${changedCount} new or updated since your last review</strong>` : `${rows.length} ${rows.length === 1 ? 'commitment' : 'commitments'} · Latest first`}</span>
      <div><button class="btn btn-secondary" onclick="refreshCommitments()">Refresh</button>
      ${changedCount ? '<button class="btn btn-secondary" onclick="markCommitmentsReviewed()">Mark as reviewed</button>' : ''}</div>
    </div>
    <p id="commitments-feedback" role="status"></p>
    <div class="commitments-columns" aria-hidden="true"><span>Commitment</span><span>${Array.isArray(d.commitments) ? 'Accepted' : 'Last confirmed'}</span><span>Status</span><span></span></div>
    <div class="commitments-list">${rows.length ? rows.map(row => {
      const change = changes(row);
      const status = row.status || (row.pending ? 'Proposed' : row.confirmed ? 'Confirmed' : 'Baseline');
      return `<details class="commitment-item ${change ? 'has-change' : ''}">
        <summary><span class="commitment-main"><span class="commitment-kind"><strong>${row.displayNumber}.</strong> ${esc(row.kind || 'Commitment')}${change ? ` <b class="commitment-change">${change}</b>` : ''}</span>
        <span class="commitment-text">${esc(row.text)}</span></span>
        <span class="commitment-date">${esc(commitmentDate(row.confirmedAt))}</span>
        <span class="commitment-status">${esc(status)}</span><span class="commitment-row-actions"><a class="btn btn-secondary commitment-implementation" href="#S05">Implementation</a><a class="btn btn-secondary" href="#S06">Outcomes</a><span class="commitment-expand" aria-hidden="true"></span></span></summary>
        <div class="commitment-detail">
          ${(row.sections || []).map(section => `<details class="commitment-section"><summary>
            <strong>${esc(section.kind)}${section.pending ? ' · Proposed' : ''}</strong><span class="commitment-preview">${esc(section.text)}</span><span class="commitment-expand" aria-hidden="true"></span></summary>
            <div class="commitment-section-body"><p>${esc(section.text)}</p><p><strong>Target:</strong> ${esc(section.target)}</p><p class="muted"><strong>Evidence gap:</strong> ${esc(section.gap)}</p></div></details>`).join('')}
          ${row.target ? `<p><strong>Target / constraint</strong><br>${esc(row.target)}</p>` : ''}
          ${row.gap ? `<p><strong>Evidence still needed</strong><br>${esc(row.gap)}</p>` : ''}
          <details class="commitment-reference"><summary>Record details</summary><p class="muted">Reference: ${esc(row.id)} · ${esc(row.version || c.committed_version)}<br>
          Confirmed by: ${esc(row.approvedBy || row.confirmed_by || 'Not recorded')}</p></details>
          ${row.changedAt && row.changedAt !== row.confirmedAt ? `<p class="muted">Updated: ${esc(commitmentDate(row.changedAt))}</p>` : ''}
          ${validDeputyReturn(row.source_chat_url) ? `<a class="cite-btn" href="${esc(validDeputyReturn(row.source_chat_url))}">Open source conversation</a>` : ''}
        </div></details>`;
    }).join('') : '<p>No commitments recorded yet.</p>'}</div>
    <footer class="commitments-footer">
      <p class="muted">${Array.isArray(d.commitments) ? 'Acceptance confirms direction; applying a change is a separate decision.' : 'Current agreement snapshot. Earlier acceptance dates were not retained. Updates to these items are not new commitments.'}
      Dates use your local time. New / Updated markers stay until you mark them reviewed.</p>
      <div class="commitments-links"><a href="#S05">Implementation status</a><a href="#S06">Simulation results</a>${deputyReturnAction()}</div>
    </footer></section>`;
}

function renderAll() {
  const d = stateStore.data;
  if (!d) return;
  const scoped = ['S01', 'S03', 'S04', 'S05', 'S06'].includes(stateStore.currentFrame);
  document.getElementById('commitment-navigation').hidden = !scoped;
  document.getElementById('selected-commitment-title').textContent =
    'Commitment 1 · ' + (commitmentList(d)[0]?.text || 'Current agreement');

  // Update active nav button
  document.querySelectorAll("#frame-nav .nav-btn").forEach((btn) => {
    const f = btn.getAttribute("data-frame");
    if (f === stateStore.currentFrame) {
      btn.classList.add("active");
      btn.setAttribute('aria-current', 'page');
    } else {
      btn.classList.remove("active");
      btn.removeAttribute('aria-current');
    }
  });

  // Update header badge with human-friendly label
  const badge = document.getElementById("backend-badge");
  if (badge) {
    badge.textContent = d.backend_mode === "mongodb_atlas" ? "Data connection: Verified" : "Data connection: Local snapshot";
  }

  const stage = document.getElementById("main-stage");
  if (!stage) return;
  const openPanels = stage.dataset.frame === stateStore.currentFrame
    ? [...stage.querySelectorAll('details[id][open]')].map(panel => panel.id) : [];
  stage.dataset.frame = stateStore.currentFrame;

  switch (stateStore.currentFrame) {
    case "COMMITMENTS":
      stage.innerHTML = renderCommitments(d);
      break;
    case "MEMORY":
      stage.innerHTML = renderMemory();
      if (stage.querySelector('.memory-inventory')) {
        stage.querySelector('.memory-page').append(stage.querySelector('.memory-inventory'));
      }
      break;
    case "S01":
      stage.innerHTML = renderS01(d);
      break;
    case "S02":
      stage.innerHTML = renderS02(d);
      break;
    case "S03":
      stage.innerHTML = renderS03(d);
      break;
    case "S04":
      stage.innerHTML = renderS04(d);
      break;
    case "S05":
      stage.innerHTML = renderS05(d);
      break;
    case "S06":
      stage.innerHTML = renderS06(d) + `<details class="card page-more"><summary>More · Commitment references and measurement limits</summary>
        <p>${d.s01_commit.mandate_status === 'committed_mandate' ? 'Confirmed direction' : 'Proposed direction preview'} · ${esc(d.s01_commit.mandate_status === 'committed_mandate' ? d.s01_commit.committed_version : d.s01_commit.draft_version)}</p>
        <p class="mono">${esc(d.s01_commit.intent_and_goal.id)} · ${esc(d.s01_commit.governing_principle.id)}</p>
        <p>Discount rate and average discount are goal proxies. Customer commitment and justification measure rule behavior; consistency is a simulated rule check. The references link this illustrative scenario to the current direction; the fixed simulation is not recalculated when wording changes. Culture and real revenue effects remain unmeasured.</p>
        <a class="cite-btn" href="#COMMITMENTS">View commitments, targets and evidence gaps</a></details>`;
      break;
    default:
      stage.innerHTML = renderS01(d);
  }

  for (const id of openPanels) {
    const panel = document.getElementById(id);
    if (panel) panel.open = true;
  }
  renderDrawer();
}

window.addEventListener("hashchange", setFrameFromHash);
window.addEventListener("keydown", (ev) => {
  if (ev.key === "Escape" && stateStore.drawerOpen) {
    closeEvidenceDrawer(true);
  }
});

window.addEventListener("DOMContentLoaded", () => {
  updateDeputyReturn();
  document.getElementById('connect-deputy-form').addEventListener('submit', (event) => {
    event.preventDefault();
    const target = validDeputyReturn(document.getElementById('deputy-chat-url').value);
    const error = document.getElementById('deputy-connect-error');
    if (!target) {
      error.textContent = 'Use https://asi1.ai/chat/ followed by the chat UUID.';
      return;
    }
    const current = new URL(window.location.href);
    current.searchParams.set('return_to', target);
    window.history.replaceState(window.history.state, '', current);
    error.textContent = '';
    document.getElementById('connect-deputy').open = false;
    updateDeputyReturn();
  });
  const receiptBtn = document.getElementById("open-import-receipt-btn");
  if (receiptBtn) {
    receiptBtn.addEventListener("click", () => {
      openEvidenceDrawer("ev:import-live-20261107-full", receiptBtn);
    });
  }
  const resetBtn = document.getElementById("reset-demo-btn");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      handleResetDemoSession();
    });
  }
  const closeBtn = document.getElementById("close-drawer-btn");
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      closeEvidenceDrawer(true);
    });
  }
  const stageEl = document.getElementById("main-stage");
  if (stageEl) {
    stageEl.addEventListener("change", (ev) => {
      if (ev.target.id === "memory-type") {
        stateStore.memoryType = ev.target.value;
        loadMemory();
      }
    });
    stageEl.addEventListener("submit", (ev) => {
      if (ev.target.id === "memory-ask-form") {
        ev.preventDefault();
        askMemory(document.getElementById("memory-question").value);
      }
    });
    stageEl.addEventListener("click", (ev) => {
      if (ev.target.id === "memory-new-chat" && !stateStore.memoryBusy) {
        stateStore.memoryTurns = [];
        stateStore.memoryAnswer = null;
        renderAll();
        return;
      }
      if (ev.target.id === "memory-next") {
        loadMemory(stateStore.memorySources?.next_cursor);
        return;
      }
      const evBtn = ev.target.closest("[data-evidence-id]");
      if (evBtn) {
        openEvidenceDrawer(evBtn.getAttribute("data-evidence-id"), evBtn);
        return;
      }
      const qToggleBtn = ev.target.closest("[data-toggle-question-card]");
      if (qToggleBtn) {
        toggleQuestionFinding(qToggleBtn.getAttribute("data-toggle-question-card"));
        return;
      }
      const qSubmitBtn = ev.target.closest("[data-submit-question-card]");
      if (qSubmitBtn) {
        submitQuestionFinding(qSubmitBtn.getAttribute("data-submit-question-card"));
        return;
      }
    });
  }
  const hash = (window.location.hash || "#MEMORY").replace("#", "").toUpperCase();
  const valid = ["MEMORY", "COMMITMENTS", "S01", "S02", "S03", "S04", "S05", "S06"];
  stateStore.currentFrame = valid.includes(hash) ? hash : "MEMORY";
  fetchState().then(() => {
    if (stateStore.currentFrame === "MEMORY") loadMemory();
    window.addEventListener('focus', checkCommitmentUpdates);
    window.setInterval(checkCommitmentUpdates, 15000);
  }).catch((err) => {
    const stage = document.getElementById("main-stage");
    if (stage) {
      stage.innerHTML = `<div class="card"><h3>Error loading state</h3><p class="muted">${esc(err.message)}</p></div>`;
    }
  });
});
