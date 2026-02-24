from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from creativeai_studio.api.deps import AppContext, get_ctx

router = APIRouter(prefix="/settings")


@router.get("")
def get_settings(ctx: AppContext = Depends(get_ctx)):
    default_auth = (ctx.settings.get_json("default_auth_mode") or {"mode": "api_key"}).get(
        "mode", "api_key"
    )

    has_api_key = ctx.settings.get_str("google_api_key") is not None
    vertex_bucket = ctx.settings.get_str("vertex_gcs_bucket")
    vertex_location = ctx.settings.get_str("vertex_location")
    vertex_project = ctx.settings.get_str("vertex_project_id")
    vertex_sa_path = ctx.settings.get_str("vertex_sa_path")

    return {
        "default_auth_mode": default_auth,
        "google_api_key_present": has_api_key,
        "vertex_project_id": vertex_project,
        "vertex_location": vertex_location,
        "vertex_gcs_bucket": vertex_bucket,
        "vertex_sa_present": bool(vertex_sa_path),
    }


@router.put("")
def put_settings(payload: dict, ctx: AppContext = Depends(get_ctx)):
    mode = payload.get("default_auth_mode")
    if mode in ("api_key", "vertex"):
        ctx.settings.set_json("default_auth_mode", {"mode": mode})

    if "vertex_project_id" in payload:
        ctx.settings.set_str("vertex_project_id", str(payload["vertex_project_id"]))
    if "vertex_location" in payload:
        ctx.settings.set_str("vertex_location", str(payload["vertex_location"]))
    if "vertex_gcs_bucket" in payload:
        bucket = str(payload["vertex_gcs_bucket"])
        if bucket.startswith("gs://"):
            raise HTTPException(status_code=400, detail="vertex_gcs_bucket must not include gs://")
        ctx.settings.set_str("vertex_gcs_bucket", bucket)

    if "google_api_key" in payload and payload["google_api_key"]:
        ctx.settings.set_str("google_api_key", str(payload["google_api_key"]))

    return get_settings(ctx)


@router.post("/test")
def test_settings(ctx: AppContext = Depends(get_ctx)):
    results: dict[str, dict] = {}

    api_key = ctx.settings.get_str("google_api_key")
    if api_key:
        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            client.models.list(config={"page_size": 1})
            results["api_key"] = {"ok": True}
        except Exception as e:  # noqa: BLE001
            results["api_key"] = {"ok": False, "error": str(e)}
    else:
        results["api_key"] = {"ok": False, "error": "google_api_key not set"}

    vertex_sa_path = ctx.settings.get_str("vertex_sa_path")
    vertex_project = ctx.settings.get_str("vertex_project_id")
    vertex_location = ctx.settings.get_str("vertex_location")
    if vertex_sa_path and vertex_project and vertex_location:
        try:
            from google import genai
            from google.oauth2.service_account import Credentials

            credentials = Credentials.from_service_account_file(
                vertex_sa_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            client = genai.Client(
                vertexai=True,
                project=vertex_project,
                location=vertex_location,
                credentials=credentials,
            )
            client.models.list(config={"page_size": 1})
            results["vertex"] = {"ok": True}
        except Exception as e:  # noqa: BLE001
            results["vertex"] = {"ok": False, "error": str(e)}
    else:
        results["vertex"] = {
            "ok": False,
            "error": "vertex_sa_path/vertex_project_id/vertex_location not set",
        }

    bucket = ctx.settings.get_str("vertex_gcs_bucket")
    if bucket and vertex_sa_path:
        try:
            import uuid

            from google.cloud import storage
            from google.oauth2.service_account import Credentials

            credentials = Credentials.from_service_account_file(
                vertex_sa_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            gcs = storage.Client(project=vertex_project, credentials=credentials)
            blob = gcs.bucket(bucket).blob(f"creativeai-studio/_test/{uuid.uuid4().hex}.txt")
            blob.upload_from_string("ok", content_type="text/plain")
            blob.delete()
            results["gcs"] = {"ok": True}
        except Exception as e:  # noqa: BLE001
            results["gcs"] = {"ok": False, "error": str(e)}
    else:
        results["gcs"] = {"ok": False, "error": "vertex_gcs_bucket/vertex_sa_path not set"}

    return results


@router.post("/vertex-sa")
async def upload_vertex_sa(
    file: UploadFile = File(...),
    ctx: AppContext = Depends(get_ctx),
):
    raw = await file.read()
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid JSON")

    out_path = ctx.cfg.data_dir / "credentials" / "vertex-sa.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    ctx.settings.set_str("vertex_sa_path", str(out_path))
    if isinstance(data, dict) and data.get("project_id"):
        ctx.settings.set_str("vertex_project_id", str(data["project_id"]))

    return {"ok": True}
