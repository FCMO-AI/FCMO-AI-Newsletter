import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const script = readFileSync(process.env.SUBSCRIBE_SCRIPT || new URL('../site-src/assets/js/subscribe.js', import.meta.url), 'utf8');

function fixture(fetch, confirmation = 'opaque') {
  const error = { hidden: true, textContent: '' };
  const button = { disabled: false, textContent: 'Suscribirme' };
  const idle = { hidden: false };
  const hosted = { hidden: true, href: 'https://example.org/signup' };
  let emailFocused = false;
  let emailSelected = false;
  const email = { value: 'semilla@example.org', focus() { emailFocused = true; }, select() { emailSelected = true; } };
  const retryListeners = new Map();
  const retry = { closest: () => section, addEventListener: (event, listener) => retryListeners.set(event, listener) };
  let focused = false;
  const pending = { hidden: true, querySelector: () => ({ focus() { focused = true; } }) };
  const section = { dataset: {}, style: {}, getBoundingClientRect: () => ({ height: 300 }),
    querySelector: (selector) => ({ '[data-sub-idle]': idle, '[data-sub-pending]': pending, 'input[type="email"]': email })[selector] ?? null };
  const attrs = new Map();
  const listeners = new Map();
  const form = { action: '/injected-signup', dataset: { emailConfirmation: confirmation, busy: 'Enviando…', error: 'No se pudo confirmar.' },
    valid: true, reportValidity() { return this.valid; }, closest: () => section,
    querySelector: (selector) => ({ '[role="alert"]': error, 'button[type="submit"]': button, '.sub-error-link': hosted })[selector] ?? null,
    setAttribute: (key, value) => attrs.set(key, value), removeAttribute: (key) => attrs.delete(key),
    addEventListener: (event, listener) => listeners.set(event, listener) };
  vm.runInNewContext(script, { document: { querySelectorAll: (selector) => selector.startsWith('form') ? [form] : selector === '[data-sub-retry]' ? [retry] : [] },
    fetch, FormData: class {}, AbortController, setTimeout, clearTimeout });
  return { form, listeners, button, section, idle, pending, error, attrs, hosted, email, retryListeners,
    emailFocused: () => emailFocused, emailSelected: () => emailSelected, focused: () => focused };
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

test('retry returns from pending, clears reserved height and selects the preserved email', async () => {
  let calls = 0;
  const f = fixture(async () => { calls++; return { type: 'opaque', status: 0 }; });
  await f.listeners.get('submit')({ preventDefault() {} });
  assert.equal(f.section.dataset.state, 'pending');
  assert.equal(f.section.style.minHeight, '300px');
  const retry = f.retryListeners.get('click');
  assert.equal(typeof retry, 'function');
  retry();
  assert.equal(f.section.dataset.state, 'idle');
  assert.equal(f.pending.hidden, true);
  assert.equal(f.idle.hidden, false);
  assert.equal(f.section.style.minHeight, '');
  assert.equal(f.email.value, 'semilla@example.org');
  assert.equal(f.emailFocused(), true);
  assert.equal(f.emailSelected(), true);
  assert.equal(calls, 1);
  await f.listeners.get('submit')({ preventDefault() {} });
  assert.equal(calls, 2);
});

test('hosted error link appears on failure and hides during a successful retry', async () => {
  let complete;
  let calls = 0;
  const f = fixture(() => {
    if (++calls === 1) return Promise.reject(new Error('private provider trace'));
    return new Promise(resolve => { complete = resolve; });
  });
  assert.equal(f.hosted.hidden, true);
  await f.listeners.get('submit')({ preventDefault() {} });
  assert.equal(f.hosted.hidden, false);
  assert.equal(f.hosted.href, 'https://example.org/signup');
  assert.equal(f.error.hidden, false);
  const request = f.listeners.get('submit')({ preventDefault() {} });
  assert.equal(f.hosted.hidden, true);
  assert.equal(f.error.hidden, true);
  complete({ type: 'opaque', status: 0 });
  await request;
  assert.equal(f.hosted.hidden, true);
  assert.equal(f.section.dataset.state, 'pending');
});
