import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const script = readFileSync(process.env.SUBSCRIBE_SCRIPT || new URL('../site-src/assets/js/subscribe.js', import.meta.url), 'utf8');

function fixture(fetch, confirmation = 'opaque') {
  const error = { hidden: true, textContent: '' };
  const button = { disabled: false, textContent: 'Suscribirme' };
  const idle = { hidden: false };
  let focused = false;
  const pending = { hidden: true, querySelector: () => ({ focus() { focused = true; } }) };
  const section = { dataset: {}, style: {}, getBoundingClientRect: () => ({ height: 300 }),
    querySelector: (selector) => selector === '[data-sub-idle]' ? idle : pending };
  const attrs = new Map();
  const listeners = new Map();
  const form = { action: '/injected-signup', dataset: { emailConfirmation: confirmation, busy: 'Enviando…', error: 'No se pudo confirmar.' },
    valid: true, reportValidity() { return this.valid; }, closest: () => section,
    querySelector: (selector) => selector === '[role="alert"]' ? error : button,
    setAttribute: (key, value) => attrs.set(key, value), removeAttribute: (key) => attrs.delete(key),
    addEventListener: (event, listener) => listeners.set(event, listener) };
  vm.runInNewContext(script, { document: { querySelectorAll: (selector) => selector.startsWith('form') ? [form] : [] },
    fetch, FormData: class {}, AbortController, setTimeout, clearTimeout });
  return { form, listeners, button, section, idle, pending, error, attrs, focused: () => focused };
}

test('opaque submission becomes pending and does not claim confirmation', async () => {
  let resolve;
  let calls = 0;
  const f = fixture((action, options) => {
    calls++;
    assert.equal(action, '/injected-signup');
    assert.equal(options.mode, 'no-cors');
    assert.equal(options.credentials, 'omit');
    return new Promise((done) => { resolve = done; });
  });
  const submit = f.listeners.get('submit');
  assert.equal(typeof submit, 'function');
  const first = submit({ preventDefault() {} });
  assert.equal(f.button.disabled, true);
  assert.equal(f.attrs.get('aria-busy'), 'true');
  await submit({ preventDefault() {} });
  assert.equal(calls, 1);
  resolve({ type: 'opaque', status: 0 });
  await first;
  assert.equal(f.section.dataset.state, 'pending');
  assert.equal(f.idle.hidden, true);
  assert.equal(f.pending.hidden, false);
  assert.equal(f.focused(), true);
  assert.equal(f.button.disabled, false);
  assert.equal(f.attrs.has('aria-busy'), false);
});

test('failure remains retryable and exposes no private error', async () => {
  let calls = 0;
  const f = fixture(async () => { calls++; throw new Error('private provider trace'); });
  const submit = f.listeners.get('submit');
  assert.equal(typeof submit, 'function');
  await submit({ preventDefault() {} });
  assert.equal(f.section.dataset.state, 'error');
  assert.equal(f.error.textContent, 'No se pudo confirmar.');
  assert.equal(f.pending.hidden, true);
  assert.equal(f.idle.hidden, false);
  assert.equal(f.button.disabled, false);
  await submit({ preventDefault() {} });
  assert.equal(calls, 2);
});

test('invalid consent or email does not submit', async () => {
  let calls = 0;
  const f = fixture(async () => { calls++; });
  f.form.valid = false;
  const submit = f.listeners.get('submit');
  assert.equal(typeof submit, 'function');
  await submit({ preventDefault() {} });
  assert.equal(calls, 0);
});

test('other providers keep native submission', () => {
  const native = fixture(() => assert.fail('must not fetch'), 'native');
  assert.equal(native.listeners.has('submit'), false);
});
