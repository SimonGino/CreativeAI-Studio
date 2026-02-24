export type AuthMode = 'api_key' | 'vertex'

export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'canceled'

export type MediaType = 'image' | 'video'

export type AssetOrigin = 'upload' | 'generated'

export type ModelInfo = {
  model_id: string
  display_name?: string
  provider_id?: string
  provider_models?: Record<string, string>
  provider_model?: string
  media_type: MediaType
  auth_support: AuthMode[]
  auth_required?: AuthMode | null
  prompt_max_chars?: number
  resolution_presets?: string[] | null
  aspect_ratios?: string[] | null
  reference_image_supported?: boolean
  start_end_image_supported?: boolean
  extend_supported?: boolean
  extend_requires_vertex?: boolean
  duration_seconds?: number[] | null
}

export type Settings = {
  default_auth_mode: AuthMode
  google_api_key_present: boolean
  vertex_project_id: string | null
  vertex_location: string | null
  vertex_gcs_bucket: string | null
  vertex_sa_present: boolean
}

export type Asset = {
  id: string
  media_type: MediaType
  origin: AssetOrigin
  file_path: string
  mime_type: string
  size_bytes: number
  width: number | null
  height: number | null
  duration_seconds: number | null
  parent_asset_id: string | null
  source_job_id: string | null
  metadata: Record<string, unknown>
  created_at: string
}

export type Job = {
  id: string
  job_type: string
  model_id: string
  auth_mode: AuthMode
  status: JobStatus
  cancel_requested: number
  progress: number | null
  status_message: string | null
  params: Record<string, unknown>
  result: Record<string, unknown> | null
  error_message: string | null
  error_detail: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
  job_assets?: Array<{ job_id: string; asset_id: string; role: string }>
}
