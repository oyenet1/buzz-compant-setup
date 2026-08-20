#!/usr/bin/env python3
"""
Video generation tools: Google Veo 3.1, Gemini Omni Flash, and HeyGen.

Outputs / job metadata land under data/exports/videos/.
Uses GOOGLE_API_KEY for Veo + Omni; HEYGEN_API_KEY for HeyGen.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger("video_gen")

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
if not os.path.exists(DATA_DIR) and os.path.exists("data"):
    DATA_DIR = "data"

VIDEOS_DIR = os.path.join(DATA_DIR, "exports", "videos")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "").strip()
HEYGEN_API_BASE = os.getenv("HEYGEN_API_BASE", "https://api.heygen.com").rstrip("/")

VEO_MODEL = os.getenv("VEO_MODEL", "veo-3.1-generate-preview").strip()
VEO_FAST_MODEL = os.getenv("VEO_FAST_MODEL", "veo-3.1-fast-generate-preview").strip()
OMNI_MODEL = os.getenv("OMNI_MODEL", "gemini-omni-flash-preview").strip()

HEYGEN_AVATAR_ID = os.getenv("HEYGEN_AVATAR_ID", "").strip()
HEYGEN_VOICE_ID = os.getenv("HEYGEN_VOICE_ID", "").strip()

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _httpx():
    import httpx
    return httpx


def _ensure_dir() -> str:
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    return VIDEOS_DIR


def _save_job(provider: str, payload: Dict[str, Any]) -> str:
    _ensure_dir()
    job_id = f"{provider}_{uuid.uuid4().hex[:10]}"
    path = os.path.join(VIDEOS_DIR, f"{job_id}.json")
    record = {
        "id": job_id,
        "provider": provider,
        "created_at": time.time(),
        **payload,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    return path


def list_video_jobs(limit: int = 20) -> Dict[str, Any]:
    _ensure_dir()
    files = sorted(
        [f for f in os.listdir(VIDEOS_DIR) if f.endswith(".json")],
        reverse=True,
    )[: max(1, min(int(limit or 20), 100))]
    jobs = []
    for name in files:
        try:
            with open(os.path.join(VIDEOS_DIR, name), "r", encoding="utf-8") as f:
                jobs.append(json.load(f))
        except Exception:
            continue
    return {"ok": True, "count": len(jobs), "jobs": jobs, "dir": VIDEOS_DIR}


def generate_omni_video(
    prompt: str,
    aspect_ratio: str = "16:9",
    previous_interaction_id: str = "",
) -> Dict[str, Any]:
    """Gemini Omni Flash via Interactions API (fast gen + conversational edit)."""
    if not GOOGLE_API_KEY:
        return {"ok": False, "error": "GOOGLE_API_KEY not set (required for Omni)"}
    if not prompt:
        return {"ok": False, "error": "prompt is required"}

    body: Dict[str, Any] = {
        "model": OMNI_MODEL,
        "input": prompt,
        "response_format": {"type": "video", "aspect_ratio": aspect_ratio or "16:9"},
    }
    if previous_interaction_id:
        body["previous_interaction_id"] = previous_interaction_id

    try:
        httpx = _httpx()
        with httpx.Client(timeout=180.0) as client:
            resp = client.post(
                f"{GEMINI_API_BASE}/interactions",
                params={"key": GOOGLE_API_KEY},
                headers={"Content-Type": "application/json"},
                json=body,
            )
            data = resp.json() if resp.content else {}
            if resp.status_code >= 400:
                return {
                    "ok": False,
                    "error": f"HTTP {resp.status_code}",
                    "body": str(data)[:800],
                }
            path = _save_job(
                "omni",
                {
                    "prompt": prompt,
                    "model": OMNI_MODEL,
                    "aspect_ratio": aspect_ratio,
                    "response": data,
                },
            )
            return {
                "ok": True,
                "provider": "gemini-omni-flash",
                "model": OMNI_MODEL,
                "job_file": path,
                "interaction_id": data.get("id") or data.get("name"),
                "status": data.get("status") or data.get("state") or "submitted",
                "raw": data,
                "note": "Prefer Omni for iterative/social clips; use Veo for cinematic/extension.",
            }
    except Exception as e:
        logger.exception("Omni video failed")
        return {"ok": False, "error": str(e)}


def generate_veo_video(
    prompt: str,
    fast: bool = False,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 6,
    resolution: str = "720p",
    poll: bool = True,
    max_wait_seconds: int = 180,
) -> Dict[str, Any]:
    """Google Veo 3.1 via predictLongRunning (async operation)."""
    if not GOOGLE_API_KEY:
        return {"ok": False, "error": "GOOGLE_API_KEY not set (required for Veo)"}
    if not prompt:
        return {"ok": False, "error": "prompt is required"}

    model = VEO_FAST_MODEL if fast else VEO_MODEL
    duration = int(duration_seconds or 6)
    if duration not in (4, 6, 8):
        duration = 6

    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "aspectRatio": aspect_ratio or "16:9",
            "resolution": resolution or "720p",
            "durationSeconds": duration,
            "sampleCount": 1,
        },
    }

    try:
        httpx = _httpx()
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{GEMINI_API_BASE}/models/{model}:predictLongRunning",
                headers={
                    "x-goog-api-key": GOOGLE_API_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            data = resp.json() if resp.content else {}
            if resp.status_code >= 400:
                return {
                    "ok": False,
                    "error": f"HTTP {resp.status_code}",
                    "body": str(data)[:800],
                }

            op_name = data.get("name") or ""
            result: Dict[str, Any] = {
                "ok": True,
                "provider": "veo",
                "model": model,
                "operation": op_name,
                "prompt": prompt,
                "status": "submitted",
                "done": bool(data.get("done")),
            }

            if poll and op_name and not data.get("done"):
                deadline = time.time() + max(30, int(max_wait_seconds or 180))
                while time.time() < deadline:
                    time.sleep(8)
                    op_resp = client.get(
                        f"{GEMINI_API_BASE}/{op_name}",
                        headers={"x-goog-api-key": GOOGLE_API_KEY},
                    )
                    op_data = op_resp.json() if op_resp.content else {}
                    if op_data.get("done"):
                        result["done"] = True
                        result["status"] = "completed" if not op_data.get("error") else "failed"
                        result["operation_result"] = op_data
                        break
                    result["status"] = "running"
                else:
                    result["status"] = "timeout_still_running"
                    result["note"] = (
                        f"Operation still running. Poll later with video_job_status "
                        f"or GET {GEMINI_API_BASE}/{op_name}"
                    )

            path = _save_job("veo", result)
            result["job_file"] = path
            return result
    except Exception as e:
        logger.exception("Veo video failed")
        return {"ok": False, "error": str(e)}


def generate_heygen_video(
    prompt: str = "",
    script: str = "",
    title: str = "Bonifade video",
    avatar_id: str = "",
    voice_id: str = "",
    use_agent: bool = True,
) -> Dict[str, Any]:
    """
    HeyGen avatar / agent video.
    - use_agent=True → POST /v3/video-agents (prompt-driven; preferred when available)
    - else → POST /v2/video/generate (avatar_id + voice_id + script required)
    """
    if not HEYGEN_API_KEY:
        return {"ok": False, "error": "HEYGEN_API_KEY not set"}

    text = (script or prompt or "").strip()
    if not text:
        return {"ok": False, "error": "prompt or script is required"}

    headers = {"X-Api-Key": HEYGEN_API_KEY, "Content-Type": "application/json"}

    try:
        httpx = _httpx()
        with httpx.Client(timeout=90.0) as client:
            if use_agent:
                resp = client.post(
                    f"{HEYGEN_API_BASE}/v3/video-agents",
                    headers=headers,
                    json={"prompt": text},
                )
                data = resp.json() if resp.content else {}
                if resp.status_code >= 400:
                    # Fall through to classic v2 if agent endpoint unavailable
                    logger.warning("HeyGen v3 agents failed (%s); trying v2 generate", resp.status_code)
                else:
                    path = _save_job(
                        "heygen",
                        {"mode": "video-agent", "prompt": text, "response": data},
                    )
                    return {
                        "ok": True,
                        "provider": "heygen",
                        "mode": "video-agent",
                        "job_file": path,
                        "session_id": (data.get("data") or {}).get("session_id") or data.get("session_id"),
                        "raw": data,
                    }

            av = avatar_id or HEYGEN_AVATAR_ID
            vo = voice_id or HEYGEN_VOICE_ID
            if not av or not vo:
                return {
                    "ok": False,
                    "error": (
                        "HeyGen avatar generate needs HEYGEN_AVATAR_ID and HEYGEN_VOICE_ID "
                        "(or pass avatar_id/voice_id). Or use video-agent mode with a working key."
                    ),
                    "hint": "List avatars: GET https://api.heygen.com/v2/avatars with X-Api-Key",
                }

            body = {
                "title": title or "Bonifade video",
                "video_inputs": [
                    {
                        "character": {"type": "avatar", "avatar_id": av, "avatar_style": "normal"},
                        "voice": {"type": "text", "input_text": text, "voice_id": vo},
                    }
                ],
                "dimension": {"width": 1280, "height": 720},
            }
            resp = client.post(
                f"{HEYGEN_API_BASE}/v2/video/generate",
                headers=headers,
                json=body,
            )
            data = resp.json() if resp.content else {}
            if resp.status_code >= 400 or data.get("error"):
                return {
                    "ok": False,
                    "error": f"HTTP {resp.status_code}",
                    "body": str(data)[:800],
                }
            video_id = (data.get("data") or {}).get("video_id")
            path = _save_job(
                "heygen",
                {"mode": "v2-generate", "script": text, "video_id": video_id, "response": data},
            )
            return {
                "ok": True,
                "provider": "heygen",
                "mode": "v2-generate",
                "video_id": video_id,
                "job_file": path,
                "status_url": f"{HEYGEN_API_BASE}/v1/video_status.get?video_id={video_id}" if video_id else None,
                "raw": data,
            }
    except Exception as e:
        logger.exception("HeyGen video failed")
        return {"ok": False, "error": str(e)}


def heygen_status(video_id: str = "", session_id: str = "") -> Dict[str, Any]:
    if not HEYGEN_API_KEY:
        return {"ok": False, "error": "HEYGEN_API_KEY not set"}
    try:
        httpx = _httpx()
        with httpx.Client(timeout=30.0) as client:
            if video_id:
                resp = client.get(
                    f"{HEYGEN_API_BASE}/v1/video_status.get",
                    headers={"X-Api-Key": HEYGEN_API_KEY},
                    params={"video_id": video_id},
                )
            elif session_id:
                resp = client.get(
                    f"{HEYGEN_API_BASE}/v3/video-agents/{session_id}",
                    headers={"X-Api-Key": HEYGEN_API_KEY},
                )
            else:
                return {"ok": False, "error": "video_id or session_id required"}
            data = resp.json() if resp.content else {}
            if resp.status_code >= 400:
                return {"ok": False, "error": f"HTTP {resp.status_code}", "body": str(data)[:500]}
            return {"ok": True, "raw": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def video_providers_status() -> Dict[str, Any]:
    return {
        "ok": True,
        "google_api_key_set": bool(GOOGLE_API_KEY),
        "heygen_api_key_set": bool(HEYGEN_API_KEY),
        "omni_model": OMNI_MODEL,
        "veo_model": VEO_MODEL,
        "veo_fast_model": VEO_FAST_MODEL,
        "heygen_avatar_configured": bool(HEYGEN_AVATAR_ID and HEYGEN_VOICE_ID),
        "exports_dir": VIDEOS_DIR,
    }
