/* APIクライアント基礎実装 */

type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'DELETE'

const BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1'

type FetchOptions = {
  headers?: Record<string, string>
}

async function request<T>(method: HttpMethod, path: string, body?: unknown, options?: FetchOptions): Promise<T> {
  const url = `${BASE}${path}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers ?? {}),
  }

  const init: RequestInit = {
    method,
    headers,
  }
  if (body !== undefined) {
    init.body = JSON.stringify(body)
  }

  let resp: Response
  try {
    resp = await fetch(url, init)
  } catch (e) {
    throw new Error('NETWORK_ERROR')
  }

  const text = await resp.text()
  const isJson = (resp.headers.get('Content-Type') || '').includes('application/json')
  const data = isJson && text ? JSON.parse(text) : text

  if (!resp.ok) {
    const msg = (data && (data.error?.message || data.message)) || 'HTTP_ERROR'
    const err = new Error(msg) as Error & { status?: number; payload?: unknown }
    err.status = resp.status
    err.payload = data
    throw err
  }

  return data as T
}

export const api = {
  get: <T>(path: string, options?: FetchOptions) => request<T>('GET', path, undefined, options),
  post: <T>(path: string, body?: unknown, options?: FetchOptions) => request<T>('POST', path, body, options),
  patch: <T>(path: string, body?: unknown, options?: FetchOptions) => request<T>('PATCH', path, body, options),
  delete: <T>(path: string, options?: FetchOptions) => request<T>('DELETE', path, undefined, options),
}

export type { FetchOptions }

