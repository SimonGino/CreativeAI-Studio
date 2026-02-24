# Doubao Seedream Ark Integration Design

**Date:** 2026-02-24

**Goal:** Add Volcengine Ark (Doubao Seedream 4.5/4.0) image generation via OpenAI-compatible SDK, including multi-reference input and sequential multi-image output, while preserving Google/Vertex support.

## Scope (Validated)

- Add models:
  - `doubao-seedream-4-5-251128` -> `Doubao-Seedream-4.5`
  - `doubao-seedream-4-0-250828` -> `Doubao-Seedream-4.0`
- Use Ark API Key (`ark_api_key`) via OpenAI Python SDK (`base_url=https://ark.cn-beijing.volces.com/api/v3`)
- New provider class: `VolcengineArkProvider`
- Image modes:
  - text-to-image (single output)
  - image-to-image (single reference -> single output)
  - multi-reference image-to-image (N references -> single output)
  - sequential multi-image generation (`max_images`)
- UI output count limit: max `5` images (backend still validates against provider limits)

## Architecture

### Provider Dispatch

- Keep `provider_id` in `catalog/models.json` as the dispatch key.
- Refactor runner from single provider instance to a provider registry:
  - `google` -> `GoogleProvider`
  - `volcengine_ark` -> `VolcengineArkProvider`
- Runner resolves the provider from the selected model's `provider_id`.

### Result Model (Unified Outputs)

- Replace single-image-specific result shape with unified output list:
  - `job.result.outputs = [{ asset_id, media_type, role, index }]`
- This supports single and multi-image outputs uniformly.
- Existing single-output UI should migrate to `outputs[]`.

## Image Generation Parameter Model

### Normalized Input Params (`image.generate`)

- `prompt: string`
- `aspect_ratio: string`
- `image_size: string`
- `reference_image_asset_ids?: string[]` (canonical)
- `reference_image_asset_id?: string` (legacy input, normalized to array)
- `watermark?: boolean`
- `sequential_image_generation?: "disabled" | "auto"`
- `sequential_image_generation_options?: { max_images?: number }`

### Frontend Constraints

- Output count control: `1..5`
- Mapping:
  - `1` -> `sequential_image_generation = "disabled"`
  - `2..5` -> `sequential_image_generation = "auto"` and `max_images = N`
- Watermark switch default: `true`

## Volcengine Ark Provider Behavior

- Build `OpenAI` client with `base_url` + `ark_api_key`.
- Call `client.images.generate(...)`.
- Send reference images through `extra_body.image`:
  - one item -> string URL/base64 data URL
  - multiple items -> string array
- Send sequential generation options via `extra_body`.
- Accept provider response in URL form (download in runner), and handle `b64_json` if returned.

## Runner & Asset Persistence

- Runner calls provider `generate_image(...)` and receives a list of outputs.
- For each output:
  - download/decode bytes
  - store as generated asset
  - insert into assets repo
  - link via `job_assets` role=`output`
- Persist `job.result.outputs[]` preserving provider order.

## Settings & Connectivity Tests

- Add `ark_api_key` storage/read/write in settings API.
- Add `/api/settings/test` check for Ark connectivity:
  - instantiate Ark OpenAI client
  - execute lightweight image API probe (safe/minimal request) or a cheap capability probe if supported
- Frontend settings page renders per-check status rows instead of raw JSON textarea only.

## Testing Strategy

- Backend unit tests:
  - `VolcengineArkProvider` request shaping and response parsing
  - Runner multi-output image persistence and `outputs[]` result
  - Validation for normalized reference image arrays and sequential options
  - Settings API for `ark_api_key` and Ark test endpoint result key
- Frontend tests (or targeted component logic tests if present):
  - Settings page per-target test rendering
  - Generate page output count -> payload mapping
  - Multi-reference selection payload shape

## Notes

- `ark_api_key` naming is preferred over model-family-specific key names.
- Backend enforces provider constraints; frontend adds user-friendly limits (max 5 images).
