// Offline checks: no requests, clipboard access, approvals or real navigation.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(__dirname + '/app.js', 'utf8');
const copied = [], navigated = [];
const sandbox = {
  URL, console,
  document: { addEventListener() {} },
  navigator: { platform: 'MacIntel', clipboard: { async writeText(text) { copied.push(text); } } },
  window: { addEventListener() {}, location: { assign(url) { navigated.push(url); } } },
};
vm.createContext(sandbox);
vm.runInContext(source, sandbox);
const draft = { value: 'My edited follow-up', focus() {}, select() {} };
const status = { hidden: true, textContent: '' };
const details = { open: false }, fallback = { hidden: true };
const elements = { textarea: draft, '.deputy-copy-status': status, details, '.deputy-copy-fallback': fallback };
const button = {
  disabled: false,
  dataset: { deputyContinue: 'https://asi1.ai/chat/00000000-1111-2222-3333-444444444444' },
  closest() { return { querySelector(selector) { return elements[selector]; } }; },
};

(async () => {
  assert.match(sandbox.deputyFollowUp('S01', {}), /proposed direction/);
  assert.doesNotMatch(sandbox.deputyFollowUp('S01', {}), /is confirmed/);
  assert.match(sandbox.deputyFollowUp('S01', {s01_commit: {mandate_status: 'committed_mandate'}}), /shows our direction is confirmed/);
  assert.match(sandbox.deputyFollowUp('S05', {s05_application: {decision_record: {action: 'approve'}, active_runtime_version: 'tool-v1'}}), /not active yet/);
  assert.match(sandbox.deputyFollowUp('S05', {s05_application: {active_runtime_version: 'tool-v2'}}), /change is active/);
  assert.match(sandbox.deputyFollowUp('S05', {s05_application: {rollback_receipt: {}, active_runtime_version: 'tool-v1'}}), /previous setup is restored/);
  assert.match(sandbox.deputyFollowUp('S06', {}), /still unmeasured in the company/);

  await sandbox.continueWithDeputy(button);
  assert.deepEqual(copied, ['My edited follow-up']);
  assert.deepEqual(navigated, [button.dataset.deputyContinue]);
  assert.equal(button.disabled, false);

  sandbox.navigator.clipboard.writeText = async () => { throw new Error('Clipboard denied'); };
  await sandbox.continueWithDeputy(button);
  assert.equal(navigated.length, 1, 'Copy failure must not navigate away from the draft');
  assert.equal(details.open, true);
  assert.equal(fallback.hidden, false);
  assert.match(status.textContent, /Automatic copy was unavailable/);

  button.dataset.deputyContinue = 'https://asi1.ai.evil.example/chat/00000000-1111-2222-3333-444444444444';
  await sandbox.continueWithDeputy(button);
  assert.equal(navigated.length, 1, 'Untrusted return destination must be rejected');
  assert.match(status.textContent, /valid ASI:One chat/);
  button.dataset.deputyContinue = 'https://asi1.ai/chat/00000000-1111-2222-3333-444444444444';
  draft.value = '   ';
  await sandbox.continueWithDeputy(button);
  assert.equal(navigated.length, 1);
  assert.match(status.textContent, /Write a message/);
  console.log('Continuation checks passed: state wording, edited draft, exact return, copy failure, invalid URL, empty message.');
})().catch(error => { console.error(error); process.exitCode = 1; });
