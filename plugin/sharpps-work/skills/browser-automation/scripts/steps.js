'use strict';
// Gap-free step helpers for Playwright scripts.
// Every step runs the same sequence, so the next action never starts early:
//   1. arm the waiters (responses, navigation) BEFORE acting, so nothing is missed
//   2. act
//   3. confirm: expected responses, URL, elements shown/hidden/text
//   4. network quiet: no request in flight and none new for `quietMs`
//   5. ready: elements the next step needs are visible
// There are no fixed sleeps. Every wait has a timeout and a named failure.
const fs = require('fs');
const path = require('path');
const { detectBrowser } = require('./detect-browser');

const EVIDENCE_DIR = process.env.EVIDENCE_DIR || 'evidence';
const DEFAULT_TIMEOUT = Number(process.env.STEP_TIMEOUT || 15000);
const DEFAULT_QUIET_MS = Number(process.env.STEP_QUIET_MS || 300);

const firstLine = (s) => String(s).split('\n')[0];
const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40);

// Launch the OS default browser (detected by detect-browser.js) in a fresh, isolated context.
// AUTOMATION_BROWSER overrides detection; PW_ENGINE / PW_CHANNEL / PW_EXECUTABLE pin the browser.
async function launch(options = {}) {
  const pw = require('playwright');
  const pinned = process.env.PW_ENGINE || process.env.PW_CHANNEL || process.env.PW_EXECUTABLE;
  const pick = pinned
    ? { id: process.env.PW_BROWSER_ID || process.env.PW_ENGINE || 'chromium', source: 'env', rawId: null,
        engine: process.env.PW_ENGINE || 'chromium', channel: process.env.PW_CHANNEL || null,
        executablePath: process.env.PW_EXECUTABLE || null, note: null }
    : detectBrowser({ override: process.env.AUTOMATION_BROWSER });
  if (pick.note) console.warn(`WARN: ${pick.note}`);
  console.log(`browser choice: ${pick.id} (${pick.source}${pick.rawId ? ': ' + pick.rawId : ''}) -> Playwright ${pick.engine}` +
    `${pick.channel ? ' channel=' + pick.channel : ''}`);
  const engine = pick.engine;
  const label = pick.id === 'unknown' ? 'chromium (bundled)' : pick.id;
  const launchOptions = { headless: !process.env.HEADED };
  if (pick.channel) launchOptions.channel = pick.channel;
  if (pick.executablePath) launchOptions.executablePath = pick.executablePath;

  let browser;
  let used = label;
  try {
    browser = await pw[engine].launch(launchOptions);
  } catch (e) {
    const pinned = process.env.PW_FALLBACK === '0';
    const alreadyBundledChromium = engine === 'chromium' && !launchOptions.channel && !launchOptions.executablePath;
    if (pinned || alreadyBundledChromium) throw e;
    console.warn(`WARN: browser "${label}" could not be launched by Playwright (${firstLine(e.message)}). ` +
      'Falling back to bundled chromium; results come from a different browser.');
    browser = await pw.chromium.launch({ headless: launchOptions.headless });
    used = 'chromium (fallback)';
  }
  const context = await browser.newContext(options.context || {});
  const page = await context.newPage();
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
  const ctx = { browser, context, page, state: track(page), n: 0 };
  console.log(`browser: ${used} ${browser.version()}`);
  return ctx;
}

async function close(ctx) { await ctx.browser.close(); }

// Track in-flight requests, failed requests and console errors for quiet-checks and failure reports.
function track(page) {
  const state = { inflight: new Set(), last: Date.now(), failed: [], consoleErrors: [] };
  const done = (r) => { state.inflight.delete(r); state.last = Date.now(); };
  page.on('request', (r) => { state.inflight.add(r); state.last = Date.now(); });
  page.on('requestfinished', done);
  page.on('requestfailed', (r) => {
    state.failed.push(`${r.method()} ${r.url()} ${(r.failure() || {}).errorText || ''}`.trim());
    done(r);
  });
  page.on('console', (m) => { if (m.type() === 'error') state.consoleErrors.push(m.text()); });
  page.on('pageerror', (e) => state.consoleErrors.push(String(e)));
  return state;
}

// Wait until nothing is in flight and nothing new started for `ms`. Catches background API calls
// that the UI fires after a click (refreshes, polling bursts, analytics) before the next step.
async function waitQuiet(ctx, ms = DEFAULT_QUIET_MS, timeout = DEFAULT_TIMEOUT) {
  const { page, state } = ctx;
  const start = Date.now();
  while (Date.now() - start < timeout) {
    if (state.inflight.size === 0 && Date.now() - state.last >= ms) return;
    await page.waitForTimeout(25); // polling interval of a condition loop, not a fixed delay
  }
  const pending = [...state.inflight].map((r) => `${r.method()} ${r.url()}`).join(', ');
  throw new Error(`network not quiet after ${timeout} ms; still in flight: ${pending}`);
}

// An action that never completes (a hanging evaluate, a blocked click) must not hang the run.
function withTimeout(promise, ms, what) {
  let timer;
  const deadline = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${what} did not complete within ${ms} ms`)), ms);
  });
  return Promise.race([promise, deadline]).finally(() => clearTimeout(timer));
}

function urlMatches(spec, url) {
  return spec instanceof RegExp ? spec.test(url) : url.includes(spec);
}

// spec: { act, responses, navigates, visible, hidden, text, ready, quietMs, timeout }
async function step(ctx, name, spec) {
  const { page, state } = ctx;
  const timeout = spec.timeout ?? DEFAULT_TIMEOUT;
  const no = ++ctx.n;
  const label = `step ${no} "${name}"`;
  const t0 = Date.now();
  const confirmed = [];
  let stage = 'arming waiters';
  state.failed = [];        // failure details are per step, not left over from earlier pages
  state.consoleErrors = [];

  try {
    // 1. arm waiters before acting (a response can arrive before an await placed after the click)
    const expected = (spec.responses || []).map((exp) => {
      const p = page.waitForResponse(
        (r) => urlMatches(exp.url, r.url()) && (!exp.method || r.request().method() === exp.method),
        { timeout });
      p.catch(() => {}); // surfaced below; avoid an unhandled rejection if act() throws first
      return { exp, p };
    });
    const nav = spec.navigates
      ? page.waitForURL(spec.navigates, { timeout, waitUntil: 'domcontentloaded' })
      : null;
    if (nav) nav.catch(() => {});

    // 2. act
    stage = 'action';
    await withTimeout(Promise.resolve().then(spec.act), timeout, 'the action');
    confirmed.push('action');

    // 3. confirm
    for (const { exp, p } of expected) {
      stage = `response ${exp.method || 'ANY'} ${exp.url}`;
      const res = await p;
      const allowed = exp.status === undefined ? res.ok()
        : [].concat(exp.status).includes(res.status());
      if (!allowed) {
        let body = '';
        try { body = (await res.text()).slice(0, 200); } catch (_) { /* body unavailable */ }
        throw new Error(`got status ${res.status()} for ${res.url()}; body: ${body}`);
      }
      if (exp.body) {
        const json = await res.json();
        if (!exp.body(json)) throw new Error(`response body did not match expectation: ${JSON.stringify(json).slice(0, 200)}`);
      }
      confirmed.push(stage);
    }
    if (nav) { stage = `navigation to ${spec.navigates}`; await nav; confirmed.push(stage); }
    for (const loc of spec.visible || []) { stage = `visible ${loc}`; await loc.waitFor({ state: 'visible', timeout }); confirmed.push(stage); }
    for (const loc of spec.hidden || []) { stage = `hidden ${loc}`; await loc.waitFor({ state: 'hidden', timeout }); confirmed.push(stage); }
    for (const t of spec.text || []) {
      stage = `text ${t.text} in ${t.locator}`;
      await t.locator.filter({ hasText: t.text }).first().waitFor({ state: 'visible', timeout });
      confirmed.push(stage);
    }

    // 4. network quiet, 5. ready for the next step
    const quietMs = spec.quietMs ?? DEFAULT_QUIET_MS;
    if (quietMs > 0) { stage = 'network quiet'; await waitQuiet(ctx, quietMs, timeout); confirmed.push(stage); }
    for (const loc of spec.ready || []) { stage = `ready ${loc}`; await loc.waitFor({ state: 'visible', timeout }); confirmed.push(stage); }
  } catch (e) {
    const shot = path.join(EVIDENCE_DIR, `${String(no).padStart(2, '0')}-${slug(name)}-FAILED.png`);
    try { await page.screenshot({ path: shot, fullPage: true }); } catch (_) { /* page may be gone */ }
    const pending = [...state.inflight].map((r) => `${r.method()} ${r.url()}`);
    const err = new Error(
      `${label} FAILED while waiting for: ${stage}\n` +
      `  cause: ${firstLine(e.message)}\n` +
      `  confirmed before failure: ${confirmed.join(' > ') || 'nothing'}\n` +
      `  in flight: ${pending.join(', ') || 'none'}\n` +
      `  failed requests: ${state.failed.join('; ') || 'none'}\n` +
      `  console errors: ${state.consoleErrors.join(' | ') || 'none'}\n` +
      `  screenshot: ${shot}`);
    err.step = label;
    throw err;
  }
  console.log(`ok  ${label} (${Date.now() - t0} ms)`);
}

// Navigate and wait until the page is usable.
async function goto(ctx, url, { ready = [], quietMs, timeout } = {}) {
  return step(ctx, `goto ${url}`, {
    act: () => ctx.page.goto(url, { waitUntil: 'domcontentloaded', timeout: timeout ?? DEFAULT_TIMEOUT }),
    ready, quietMs, timeout,
  });
}

module.exports = { launch, close, step, goto, waitQuiet, track };
