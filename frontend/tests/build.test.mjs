import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { once } from 'node:events';

const dist = new URL('../dist/index.html', import.meta.url);

test('built synthetic HTML is served as an ordinary static HTTP page', { timeout: 10000 }, async () => {
  const html = await readFile(dist);
  assert.ok(html.length > 0);
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
