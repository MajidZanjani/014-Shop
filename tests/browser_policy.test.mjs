import test from 'node:test';
import assert from 'node:assert/strict';
import { allowedRequest } from '../scripts/browser_policy.mjs';
test('only exact owned loopback origin is allowed', () => {
  for (const host of ['localhost', '127.0.0.1']) {
    const base = `http://${host}:18473`;
    assert.equal(allowedRequest(base + '/purchase/access/', base), true);
    for (const url of ['https://example.invalid/x', 'http://127.0.0.1:18474/', 'http://user:pass@'+host+':18473/',
      'data:text/html,private', 'file:///etc/passwd', 'http://[::1]:18473/', 'not-a-url']) {
      assert.equal(allowedRequest(url, base), false);
    }
  }
  for (const origin of ['https://localhost:18473', 'http://example.invalid:18473', 'http://localhost',
    'http://user:pass@localhost:18473', 'not-an-origin']) {
    assert.equal(allowedRequest(origin, origin), false);
  }
});
