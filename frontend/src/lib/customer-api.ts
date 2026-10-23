// Browser-only, same-origin transport. Never called during static compilation.
export class ApiError extends Error {
  constructor(public status: number) { super('Customer request failed'); }
}
const allowed = new Set([
  '/api/v1/cart/', '/api/v1/quotation-requests/',
  '/api/v1/customer/session/', '/api/v1/customer/request-code/',
  '/api/v1/customer/verify/', '/api/v1/customer/logout/', '/api/v1/configuration-drafts/',
]);
export async function customerRequest(path: string, method: 'GET' | 'POST' = 'GET', body?: unknown, csrf?: string): Promise<any> {
  if (!allowed.has(path) && !/^\/api\/v1\/(?:configuration-drafts|quotation-requests)\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/$/.test(path)) throw new Error('Unapproved customer endpoint');
  if (typeof window === 'undefined') throw new Error('Customer API is browser-only');
  if (method !== 'GET' && method !== 'POST') throw new Error('Unapproved method');
  if (method === 'POST' && !csrf) throw new Error('CSRF token required');
  const headers: Record<string,string> = { Accept: 'application/json' };
  if (method === 'POST') { headers['Content-Type'] = 'application/json'; headers['X-CSRFToken'] = csrf!; }
  const response = await window.fetch(path,{ method, credentials: 'same-origin', cache: 'no-store', redirect: 'error', headers,
    ...(method === 'POST' ? {body:JSON.stringify(body)} : {}), signal:AbortSignal.timeout(10000) });
  if (!response.ok) throw new ApiError(response.status);
  if (!response.headers.get('content-type')?.startsWith('application/json')) throw new Error('Unexpected customer response');
  return response.json();
}
