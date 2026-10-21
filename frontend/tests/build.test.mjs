import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { once } from 'node:events';

const dist = new URL('../dist/index.html', import.meta.url);

test('built synthetic HTML is served as an ordinary static HTTP page', { timeout: 10000 }, async () => {
  const html = await readFile(dist);
  assert.ok(html.length > 0);
  const output = await readdir(new URL('../dist/', import.meta.url));
  assert.ok(!output.includes('server'), 'no request-time server artifact emitted');
  const server = createServer((request, response) => {
    if (request.url !== '/') { response.writeHead(404).end(); return; }
    response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    response.end(html);
  });
  try {
    server.listen(0, '127.0.0.1');
    await once(server, 'listening');
    const response = await fetch(`http://127.0.0.1:${server.address().port}/`, { signal: AbortSignal.timeout(5000) });
    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type'), /^text\/html/);
    const text = await response.text();
    assert.match(text, /xSPI-MC build probe/);
    assert.match(text, /data-evidence-class="local-synthetic"/);
    assert.match(text, /No purchase or licence offer/);
  } finally {
    server.closeAllConnections();
    await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
  }
});

// The real React client renderer owns event dispatch, scheduling and hook state.
// This bounded DOM host supplies only the elements/text/events used by this probe;
// it does not mock hooks or count transitions and is not browser hydration proof.
function domHost() {
  class Node {
    constructor(type, tag, owner) {
      this.nodeType = type; this.nodeName = tag; this.tagName = tag;
      this.ownerDocument = owner; this.childNodes = []; this.parentNode = null;
      this.namespaceURI = 'http://www.w3.org/1999/xhtml';
      this.style = {}; this.attrs = new Map(); this.events = new Map();
    }
    get firstChild() { return this.childNodes[0] ?? null; }
    get lastChild() { return this.childNodes.at(-1) ?? null; }
    get nextSibling() { return this.parentNode?.childNodes[this.parentNode.childNodes.indexOf(this) + 1] ?? null; }
    appendChild(child) { if (child.parentNode) child.parentNode.removeChild(child); child.parentNode = this; this.childNodes.push(child); return child; }
    insertBefore(child, before) { if (child.parentNode) child.parentNode.removeChild(child); const index = this.childNodes.indexOf(before); assert.ok(index >= 0); child.parentNode = this; this.childNodes.splice(index, 0, child); return child; }
    removeChild(child) { const index = this.childNodes.indexOf(child); assert.ok(index >= 0); this.childNodes.splice(index, 1); child.parentNode = null; return child; }
    set textContent(value) { this.childNodes.forEach(child => { child.parentNode = null; }); this.childNodes = []; if (value !== '') this.appendChild(this.ownerDocument.createTextNode(String(value))); }
    get textContent() { return this.nodeType === 3 ? this.nodeValue : this.childNodes.map(child => child.textContent).join(''); }
    setAttribute(name, value) { this.attrs.set(name, String(value)); }
    removeAttribute(name) { this.attrs.delete(name); }
    getAttribute(name) { return this.attrs.get(name) ?? null; }
    addEventListener(name, fn, options) { const capture = options === true || options?.capture === true; const key = `${name}:${capture}`; if (!this.events.has(key)) this.events.set(key, []); this.events.get(key).push(fn); }
    removeEventListener(name, fn, options) { const key = `${name}:${options === true || options?.capture === true}`; this.events.set(key, (this.events.get(key) ?? []).filter(item => item !== fn)); }
    contains(node) { return node === this || this.childNodes.some(child => child.contains(node)); }
  }
  const document = new Node(9, '#document', null);
  document.ownerDocument = document;
  document.createElement = tag => new Node(1, tag.toUpperCase(), document);
  document.createElementNS = (_, tag) => document.createElement(tag);
  document.createTextNode = value => Object.assign(new Node(3, '#text', document), { nodeValue: String(value) });
  document.documentElement = document.createElement('html');
  document.body = document.createElement('body');
  document.appendChild(document.documentElement); document.documentElement.appendChild(document.body);
  document.activeElement = document.body;
  const window = { document, HTMLElement: Node, HTMLIFrameElement: class {}, Node, addEventListener() {}, removeEventListener() {} };
  document.defaultView = window;
  return { document, window };
}

function findNode(root, predicate) {
  if (predicate(root)) return root;
  for (const child of root.childNodes) { const found = findNode(child, predicate); if (found) return found; }
}

import { mkdtemp, rm, writeFile, cp, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
const project = fileURLToPath(new URL('../', import.meta.url));

function astroBuild(cwd) {
  return spawnSync(process.execPath, [join(project, 'node_modules/.bin/astro'), 'build', '--force'], {
    cwd, timeout: 30000, encoding: 'utf8', maxBuffer: 1024 * 1024,
    env: { ...process.env, ASTRO_TELEMETRY_DISABLED: '1' },
  });
}

test('Markdown collection changes reach HTML; unknown fields and invalid types fail the build', { timeout: 120000 }, async () => {
  const scratch = await mkdtemp(join(project, '.probe-test-'));
  try {
    for (const file of ['package.json', 'astro.config.mjs', 'tsconfig.json', 'src']) {
      await cp(join(project, file), join(scratch, file), { recursive: true });
    }
    // Native module resolution finds the installed graph in the parent frontend.
    const markdown = join(scratch, 'src/content/probes/skeleton.md');
    const original = await readFile(markdown, 'utf8');
    await writeFile(markdown, original.replace('xSPI-MC build probe', 'Changed synthetic Markdown title'));
    const changed = astroBuild(scratch);
    assert.equal(changed.status, 0, changed.stdout + changed.stderr);
    const html = await readFile(join(scratch, 'dist/index.html'), 'utf8');
    assert.match(html, /Changed synthetic Markdown title/);
    assert.match(html, /astro-island/);
    assert.match(html, /client="load"/);
    assert.match(html, /Synthetic count:.*0/);
    const assets = await readdir(join(scratch, 'dist/_astro'));
    assert.ok(assets.some(name => name.endsWith('.js')), 'real island hydration assets emitted');
    for (const malformed of [original.replace('evidence_class:', 'unknown_field: private\nevidence_class:'), original.replace('title: xSPI-MC build probe', 'title: 123')]) {
      await writeFile(markdown, malformed);
      const rejected = astroBuild(scratch);
      assert.notEqual(rejected.status, 0, 'invalid schema must reject the actual build');
      assert.match(rejected.stdout + rejected.stderr, /schema|unrecognized|invalid|expected/i);
    }
  } finally { await rm(scratch, { recursive: true, force: true }); }
});

test('real React event dispatch updates the component hook state', { timeout: 10000 }, async () => {
  const host = domHost();
  const previous = { window: globalThis.window, document: globalThis.document, act: globalThis.IS_REACT_ACT_ENVIRONMENT };
  const scratch = await mkdtemp(join(project, '.probe-test-'));
  let root;
  try {
    globalThis.window = host.window; globalThis.document = host.document;
    globalThis.IS_REACT_ACT_ENVIRONMENT = true;
    const { default: ts } = await import('typescript');
    const source = await readFile(join(project, 'src/components/BuildProbe.tsx'), 'utf8');
    const compiled = ts.transpileModule(source, { compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } });
    const modulePath = join(scratch, 'probe.mjs'); await writeFile(modulePath, compiled.outputText);
    const { default: Probe } = await import(pathToFileURL(modulePath));
    const { act, createElement } = await import('react');
    const { createRoot } = await import('react-dom/client');
    const container = host.document.createElement('div'); host.document.body.appendChild(container);
    const errors = [];
    root = createRoot(container, { onUncaughtError: error => errors.push(error), onRecoverableError: error => errors.push(error) });
    await act(async () => root.render(createElement(Probe)));
    assert.match(container.textContent, /Synthetic count: 0/);
    const button = findNode(container, node => node.tagName === 'BUTTON');
    assert.ok(button); assert.equal(button.textContent, 'Increment synthetic counter');
    const click = { type: 'click', target: button, button: 0, bubbles: true, timeStamp: Date.now(), preventDefault() {}, stopPropagation() {} };
    await act(async () => {
      for (const listener of container.events.get('click:true') ?? []) listener(click);
      for (const listener of container.events.get('click:false') ?? []) listener(click);
    });
    assert.match(container.textContent, /Synthetic count: 1/);
    assert.equal(errors.length, 0, errors.map(String).join('\n'));
    await act(async () => root.unmount()); root = null;
  } finally {
    if (root) { const { act } = await import('react'); await act(async () => root.unmount()); }
    globalThis.window = previous.window; globalThis.document = previous.document;
    globalThis.IS_REACT_ACT_ENVIRONMENT = previous.act;
    await rm(scratch, { recursive: true, force: true });
  }
});
