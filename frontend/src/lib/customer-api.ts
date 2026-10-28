// Browser-only, same-origin transport. Never called during static compilation.
export class ApiError extends Error {
  constructor(public status: number, public recoveryPending = false) { super('Customer request failed'); }
}
export type AccessDenial = 401 | 403 | 'recovery';
const allowed = new Set([
  '/api/v1/cart/', '/api/v1/quotation-requests/',
  '/api/v1/customer/session/', '/api/v1/customer/request-code/',
  '/api/v1/customer/verify/', '/api/v1/customer/logout/', '/api/v1/configuration-drafts/',
]);
let accessContext: string | null = null;
let recoveryGeneration = {};
export async function customerRequest(path: string, method: 'GET' | 'POST' = 'GET', body?: unknown, csrf?: string): Promise<any> {
  if (!allowed.has(path) && !/^\/api\/v1\/(?:configuration-drafts|quotation-requests)\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/$/.test(path)) throw new Error('Unapproved customer endpoint');
  if (typeof window === 'undefined') throw new Error('Customer API is browser-only');
  if (method !== 'GET' && method !== 'POST') throw new Error('Unapproved method');
  if (method === 'POST' && !csrf) throw new Error('CSRF token required');
  const headers: Record<string,string> = { Accept: 'application/json' };
  if (method === 'POST') { headers['Content-Type'] = 'application/json'; headers['X-CSRFToken'] = csrf!; }
  const expectedContext = accessContext;
  const expectedRecovery = recoveryGeneration;
  const response = await window.fetch(path,{ method, credentials: 'same-origin', cache: 'no-store', redirect: 'error', headers,
    ...(method === 'POST' ? {body:JSON.stringify(body)} : {}), signal:AbortSignal.timeout(10000) });
  if (!response.ok) {
    // Fixed server signal only; arbitrary error bodies stay unread and private.
    const recoveryPending=response.status===503&&response.headers?.get('X-Shop-Access-Recovery')==='pending';
    if(recoveryPending){accessContext=null;recoveryGeneration={};}
    throw new ApiError(response.status,recoveryPending||expectedRecovery!==recoveryGeneration);
  }
  if(expectedRecovery!==recoveryGeneration)throw new ApiError(403,true);
  if (!response.headers.get('content-type')?.startsWith('application/json')) throw new Error('Unexpected customer response');
  const rebase=path==='/api/v1/customer/session/'||path==='/api/v1/customer/verify/'||path==='/api/v1/customer/logout/';
  const protectedResource=!path.startsWith('/api/v1/customer/');
  const incoming=response.headers.get('X-Shop-Access-Context');
  if ((rebase||protectedResource)&&(!incoming||!/^[a-f0-9]{64}$/.test(incoming)))throw new ApiError(403);
  const contextMatches=()=>expectedContext!==null&&expectedContext===accessContext&&incoming===expectedContext;
  if(protectedResource&&!contextMatches())throw new ApiError(403);
  const value=await response.json();
  if(expectedRecovery!==recoveryGeneration)throw new ApiError(403,true);
  if(protectedResource&&!contextMatches())throw new ApiError(403);
  if(rebase)accessContext=incoming;
  return value;
}
