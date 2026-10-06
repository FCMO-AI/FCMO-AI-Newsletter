// Thin client for the 7.1 API. Cookie session, CSRF header on writes, plain errors.
let csrf = ''
export const setCsrf = v => { csrf = v }
export class ApiError extends Error { constructor (status, data) { super(`api ${status}`); this.status = status; this.data = data } }

export async function api (method, url, body, opts = {}) {
  const headers = { accept: 'application/json' }
  if (method !== 'GET') headers['x-csrf-token'] = csrf
  let payload
  if (body instanceof Blob) { payload = body; headers['content-type'] = body.type; Object.assign(headers, opts.headers || {}) } else if (body !== undefined) { payload = JSON.stringify(body); headers['content-type'] = 'application/json' }
  let res
  try { res = await fetch(url, { method, headers, body: payload, credentials: 'same-origin' }) } catch (e) { throw new ApiError(0, { error: 'network' }) }
  let data = null
  try { data = await res.json() } catch { /* empty body */ }
  if (res.status === 401 && !url.endsWith('/login') && !url.endsWith('/api/me')) window.dispatchEvent(new CustomEvent('studio:unauth'))
  if (!res.ok) throw new ApiError(res.status, data)
  return data
}
export const get = u => api('GET', u)
export const post = (u, b) => api('POST', u, b === undefined ? {} : b)
export const put = (u, b) => api('PUT', u, b)
export const del = u => api('DELETE', u)
