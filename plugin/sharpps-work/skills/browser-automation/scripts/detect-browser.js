'use strict';
// Detect the OS default web browser and map it to a Playwright launch target.
// Node 18+, no dependencies. Detection picks the browser TYPE; Playwright still starts a new
// process with a clean temporary profile (the user's logins, tabs and extensions are not used).
//
//   node detect-browser.js                    print what would be chosen (JSON)
//   node detect-browser.js --override msedge  pretend the default is msedge
//   node detect-browser.js --from-id ChromeHTML   map a raw id without reading the OS
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

function run(cmd, args) {
  try {
    return execFileSync(cmd, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 5000 }).trim();
  } catch (_) { return ''; }
}
const osName = () => (process.platform === 'win32' ? 'windows' : process.platform === 'darwin' ? 'macos' : 'linux');

// ---- pure parsers (no OS access) ----
// `reg query` prints e.g. "    ProgId    REG_SZ    ChromeHTML"
function parseRegValue(text, name) {
  const m = new RegExp('^\\s*' + name + '\\s+REG_\\w+\\s+(.+?)\\s*$', 'm').exec(text || '');
  return m ? m[1] : '';
}
function exeFromCommand(cmd) {
  const m = /^"([^"]+)"/.exec(cmd || '') || /^(\S+)/.exec(cmd || '');
  return m ? m[1] : '';
}
function pickMacHandler(handlers) {
  for (const scheme of ['https', 'http']) {
    const h = (handlers || []).find((x) => x.LSHandlerURLScheme === scheme && x.LSHandlerRoleAll);
    if (h) return { id: h.LSHandlerRoleAll, source: `macos-launchservices (${scheme})` };
  }
  return null;
}
// Windows ProgId, macOS bundle id or Linux .desktop id -> browser id
function resolveBrowserId(raw) {
  const r = String(raw || '').toLowerCase();
  const table = [
    ['chrome', /^(chromehtml|google-chrome(-stable)?(\.desktop)?|com\.google\.chrome(\.desktop)?|chrome)$/],
    ['msedge', /^(msedgehtm|microsoft-edge(-stable)?(\.desktop)?|com\.microsoft\.edge(mac)?(\.desktop)?|msedge|edge)$/],
    ['firefox', /^(firefoxurl.*|firefox(-esr)?(\.desktop)?|org\.mozilla\.firefox(\.desktop)?)$/],
    ['safari', /^(com\.apple\.safari|safari|webkit)$/],
    ['brave', /^(bravehtml|brave(-browser)?(\.desktop)?|com\.brave\.browser(\.desktop)?)$/],
    ['vivaldi', /^(vivaldi(-stable)?(\.desktop)?|vivaldihtm.*|com\.vivaldi\.vivaldi)$/],
    ['opera', /^(operastable|opera(\.desktop)?|com\.operasoftware\.opera)$/],
    ['chromium', /^(chromium(-browser)?(\.desktop)?|org\.chromium\.chromium(\.desktop)?)$/],
  ];
  for (const [id, re] of table) if (re.test(r)) return id;
  return 'unknown';
}

// ---- OS reads ----
function readRawDefault(osn) {
  if (osn === 'windows') {
    for (const scheme of ['https', 'http']) {
      const out = run('reg', ['query',
        `HKCU\\Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations\\${scheme}\\UserChoice`, '/v', 'ProgId']);
      const id = parseRegValue(out, 'ProgId');
      if (id) return { id, source: `windows-registry (${scheme})` };
    }
    return null;
  }
  if (osn === 'macos') {
    const plist = path.join(os.homedir(), 'Library/Preferences/com.apple.LaunchServices/com.apple.launchservices.secure.plist');
    if (fs.existsSync(plist)) {
      try {
        const h = pickMacHandler(JSON.parse(run('plutil', ['-convert', 'json', '-o', '-', plist])).LSHandlers);
        if (h) return h;
      } catch (_) { /* fall through to the macOS default */ }
    }
    return { id: 'com.apple.safari', source: 'macos-default (no handler recorded)' };
  }
  const a = run('xdg-settings', ['get', 'default-web-browser']).split('\n')[0];
  if (a) return { id: a.trim(), source: 'xdg-settings' };
  const b = run('xdg-mime', ['query', 'default', 'x-scheme-handler/https']).split('\n')[0];
  if (b) return { id: b.trim(), source: 'xdg-mime' };
  return null;
}

function which(name) {
  for (const dir of (process.env.PATH || '').split(path.delimiter)) {
    const p = path.join(dir, name);
    try { fs.accessSync(p, fs.constants.X_OK); return p; } catch (_) { /* keep looking */ }
  }
  return null;
}

// Chromium-based browsers without a Playwright channel (brave, vivaldi, opera) run by executable path.
function findExecutable(id, osn, progId) {
  const candidates = [];
  if (osn === 'windows') {
    if (progId) {
      const cmd = parseRegValue(run('reg', ['query', `HKCR\\${progId}\\shell\\open\\command`, '/ve']), '\\(Default\\)');
      if (cmd) candidates.push(exeFromCommand(cmd));
    }
    const rel = { brave: 'BraveSoftware\\Brave-Browser\\Application\\brave.exe', vivaldi: 'Vivaldi\\Application\\vivaldi.exe', opera: 'Programs\\Opera\\opera.exe' }[id];
    if (rel) for (const base of [process.env.ProgramFiles, process.env['ProgramFiles(x86)'], process.env.LOCALAPPDATA]) if (base) candidates.push(path.join(base, rel));
  } else if (osn === 'macos') {
    const app = { brave: 'Brave Browser', vivaldi: 'Vivaldi', opera: 'Opera' }[id];
    if (app) candidates.push(`/Applications/${app}.app/Contents/MacOS/${app}`);
  } else {
    for (const n of ({ brave: ['brave-browser', 'brave'], vivaldi: ['vivaldi', 'vivaldi-stable'], opera: ['opera'] }[id] || [])) {
      const p = which(n); if (p) candidates.push(p);
    }
  }
  return candidates.find((c) => c && fs.existsSync(c)) || null;
}

function detectBrowser({ override, fromId } = {}) {
  const osn = osName();
  let raw = null;
  let source = 'none';
  if (fromId) { raw = fromId; source = 'fromid'; }
  else if (override) { raw = override; source = 'override'; }
  else { const d = readRawDefault(osn); if (d) { raw = d.id; source = d.source; } }

  const id = raw ? resolveBrowserId(raw) : 'unknown';
  let engine = 'chromium';
  let channel = null;
  let executablePath = null;
  let note = null;
  if (id === 'chrome') channel = 'chrome';
  else if (id === 'msedge') channel = 'msedge';
  else if (id === 'firefox') { engine = 'firefox'; note = 'Playwright cannot drive the installed Firefox; it uses its own Firefox build (npx playwright install firefox).'; }
  else if (id === 'safari') { engine = 'webkit'; note = 'Playwright cannot drive Safari; it uses its own WebKit build (npx playwright install webkit).'; }
  else if (id === 'unknown') note = raw ? `Unrecognized browser '${raw}'; using bundled Chromium.` : 'No default browser could be detected; using bundled Chromium.';
  if (['brave', 'vivaldi', 'opera'].includes(id)) {
    executablePath = findExecutable(id, osn, source.startsWith('windows-registry') ? raw : null);
    if (!executablePath) note = `Could not locate the ${id} executable; using bundled Chromium.`;
  }
  return { os: osn, source, rawId: raw, id, engine, channel, executablePath, note };
}

module.exports = { detectBrowser, resolveBrowserId, parseRegValue, exeFromCommand, pickMacHandler };

if (require.main === module) {
  const arg = (name) => { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : undefined; };
  console.log(JSON.stringify(detectBrowser({ override: arg('--override') || process.env.AUTOMATION_BROWSER, fromId: arg('--from-id') })));
}
