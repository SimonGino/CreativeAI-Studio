export type AuthMode = 'api_key'

export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'canceled'

export type MediaType = 'image' | 'video'

export type AssetOrigin = 'upload' | 'generated'

export type ModelInfo = {
  model_id: string
  display_name?: string
  coming_soon?: boolean
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
  max_reference_images?: number | null
  sequential_image_generation_supported?: boolean
  max_output_images?: number | null
  max_total_images?: number | null
  start_end_image_supported?: boolean
  extend_supported?: boolean
  duration_seconds?: number[] | null
}

export type Settings = {
  default_auth_mode: AuthMode
  google_api_key_present: boolean
  ark_api_key_present: boolean
}

export type JobOutput = {
  asset_id: string
  media_type?: MediaType
  role?: string
  index?: number
}

export type JobResult = {
  output_asset_id?: string
  outputs?: JobOutput[]
  [key: string]: unknown
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
  source_model_id: string | null
  source_model_name: string | null
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
  result: JobResult | null
  error_message: string | null
  error_detail: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
  job_assets?: Array<{ job_id: string; asset_id: string; role: string }>
}
