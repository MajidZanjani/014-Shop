// Local acceptance target requests only; this is not a production traffic policy.
export function allowedRequest(raw, origin) {
  try {
    const url = new URL(raw), base = new URL(origin);
    return base.protocol === 'http:' && ['127.0.0.1', 'localhost', 'staff.localhost'].includes(base.hostname)
      && !base.username && !base.password && base.port !== ''
      && url.origin === base.origin && url.protocol === 'http:' && !url.username && !url.password;
  } catch { return false; }
}
