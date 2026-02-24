import type { Asset, Job, ModelInfo, Settings } from './types'

type ApiError = Error & { status?: number }

async function readErrorDetail(resp: Response): Promise<string> {
  const contentType = resp.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    try {
      const data = (await resp.json()) as { detail?: unknown }
      if (typeof data?.detail === 'string') return data.detail
      return JSON.stringify(data)
    } catch {
      return resp.statusText
    }
  }
  try {
    return await resp.text()
  } catch {
    return resp.statusText
  }
}

async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, {
    ...init,
    headers: {
      'content-type': 'application/json',
      ...(init?.headers || {}),
    },
  })
  if (!resp.ok) {
    const err = new Error(await readErrorDetail(resp)) as ApiError
    err.status = resp.status
    throw err
  }
  return (await resp.json()) as T
}

async function apiGet<T>(path: string): Promise<T> {
  const resp = await fetch(path)
  if (!resp.ok) {
    const err = new Error(await readErrorDetail(resp)) as ApiError
    err.status = resp.status
    throw err
  }
  return (await resp.json()) as T
}

export const api = {
  getModels: () => apiGet<ModelInfo[]>('/api/models'),
  getSettings: () => apiGet<Settings>('/api/settings'),
  putSettings: (payload: Record<string, unknown>) =>
    apiJson<Settings>('/api/settings', { method: 'PUT', body: JSON.stringify(payload) }),
  testSettings: () => apiJson<Record<string, { ok: boolean; error?: string }>>('/api/settings/test', { method: 'POST', body: '{}' }),
  uploadVertexSa: async (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    const resp = await fetch('/api/settings/vertex-sa', { method: 'POST', body: fd })
    if (!resp.ok) throw new Error(await readErrorDetail(resp))
    return (await resp.json()) as { ok: boolean }
  },
  uploadAsset: async (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    const resp = await fetch('/api/assets/upload', { method: 'POST', body: fd })
    if (!resp.ok) throw new Error(await readErrorDetail(resp))
    return (await resp.json()) as Pick<Asset, 'id' | 'media_type' | 'origin' | 'mime_type' | 'width' | 'height' | 'duration_seconds'>
  },
  listAssets: (params?: { media_type?: string; origin?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams()
    if (params?.media_type) qs.set('media_type', params.media_type)
    if (params?.origin) qs.set('origin', params.origin)
    if (params?.limit != null) qs.set('limit', String(params.limit))
    if (params?.offset != null) qs.set('offset', String(params.offset))
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return apiGet<Asset[]>(`/api/assets${suffix}`)
  },
  getAsset: (id: string) => apiGet<Asset>(`/api/assets/${id}`),
  listJobs: (params?: { status?: string; job_type?: string; model_id?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams()
    if (params?.status) qs.set('status', params.status)
    if (params?.job_type) qs.set('job_type', params.job_type)
    if (params?.model_id) qs.set('model_id', params.model_id)
    if (params?.limit != null) qs.set('limit', String(params.limit))
    if (params?.offset != null) qs.set('offset', String(params.offset))
    const suffix = qs.toString() ? `?${qs.toString()}` : ''
    return apiGet<Job[]>(`/api/jobs${suffix}`)
  },
  getJob: (id: string) => apiGet<Job>(`/api/jobs/${id}`),
  createJob: (payload: Record<string, unknown>) =>
    apiJson<Job>('/api/jobs', { method: 'POST', body: JSON.stringify(payload) }),
  cancelJob: (id: string) => apiJson<{ ok: boolean }>(`/api/jobs/${id}/cancel`, { method: 'POST', body: '{}' }),
  cloneJob: (id: string, payload: Record<string, unknown>) =>
    apiJson<Job>(`/api/jobs/${id}/clone`, { method: 'POST', body: JSON.stringify(payload) }),
}

