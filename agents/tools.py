#!/usr/bin/env python3
"""
Swarm agent tools registry.

HOW TO ADD A NEW TOOL
---------------------
1. Write a function `tool_your_name(**kwargs) -> dict` (return {"ok": True/False, ...}).
2. Register it in TOOL_SPECS below with a short description and arg list.
3. Restart the orchestrator: ./manage.sh restart agent-orchestrator

Agents call tools with:

```tool
{"name": "generate_pdf", "args": {"title": "Proposal", "body": "...", "doc_type": "proposal"}}
```

Built-in examples: generate_pdf, list_pdf_exports, firecrawl_scrape (if key set).
Payment / bank-transfer tools are intentionally not supported.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, List, Optional

import pdf_export
import video_gen

logger = logging.getLogger("tools")

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "").strip()
FIRECRAWL_BASE = os.getenv("FIRECRAWL_API_BASE", "https://api.firecrawl.dev").rstrip("/")
ENABLE_AGENT_TOOLS = os.getenv("ENABLE_AGENT_TOOLS", "true").lower() in ("1", "true", "yes")


def _httpx():
    try:
        import httpx
        return httpx
    except ImportError as e:
        raise RuntimeError("httpx required for this tool") from e


# ─── Tools ────────────────────────────────────────────────────────────────────


def tool_generate_pdf(
    title: str,
    body: str,
    doc_type: str = "document",
    client_name: str = "",
    filename: str = "",
    sections: Optional[List[Dict[str, str]]] = None,
    footer_note: str = "",
) -> Dict[str, Any]:
    """Create a PDF proposal, quote, SOW, NDA draft, brief, etc."""
    return pdf_export.generate_pdf(
        title=title,
        body=body,
        doc_type=doc_type or "document",
        client_name=client_name or "",
        filename=filename or "",
        sections=sections,
        footer_note=footer_note or "",
    )


def tool_list_pdf_exports(limit: int = 20) -> Dict[str, Any]:
    return pdf_export.list_exports(limit=limit)


def tool_firecrawl_scrape(url: str) -> Dict[str, Any]:
    if not FIRECRAWL_API_KEY:
        return {"ok": False, "error": "FIRECRAWL_API_KEY not set"}
    try:
        httpx = _httpx()
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{FIRECRAWL_BASE}/v1/scrape",
                headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}"},
                json={"url": url, "formats": ["markdown"]},
            )
            if resp.status_code >= 400:
                return {"ok": False, "error": f"HTTP {resp.status_code}", "body": resp.text[:400]}
            data = resp.json()
            md = (data.get("data") or {}).get("markdown") or ""
            return {"ok": True, "url": url, "markdown": md[:12000]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_firecrawl_search(query: str, limit: int = 5) -> Dict[str, Any]:
    if not FIRECRAWL_API_KEY:
        return {"ok": False, "error": "FIRECRAWL_API_KEY not set"}
    try:
        httpx = _httpx()
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{FIRECRAWL_BASE}/v1/search",
                headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}"},
                json={"query": query, "limit": int(limit or 5)},
            )
            if resp.status_code >= 400:
                return {"ok": False, "error": f"HTTP {resp.status_code}", "body": resp.text[:400]}
            data = resp.json()
            results = data.get("data") or []
            slim = [
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "description": (r.get("description") or "")[:300],
                }
                for r in results[: int(limit or 5)]
            ]
            return {"ok": True, "query": query, "results": slim}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_generate_video_omni(
    prompt: str,
    aspect_ratio: str = "16:9",
    previous_interaction_id: str = "",
) -> Dict[str, Any]:
    return video_gen.generate_omni_video(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        previous_interaction_id=previous_interaction_id or "",
    )


def tool_generate_video_veo(
    prompt: str,
    fast: bool = False,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 6,
    resolution: str = "720p",
    poll: bool = True,
) -> Dict[str, Any]:
    return video_gen.generate_veo_video(
        prompt=prompt,
        fast=bool(fast),
        aspect_ratio=aspect_ratio,
        duration_seconds=duration_seconds,
        resolution=resolution,
        poll=bool(poll),
    )


def tool_generate_video_heygen(
    prompt: str = "",
    script: str = "",
    title: str = "Bonifade video",
    avatar_id: str = "",
    voice_id: str = "",
    use_agent: bool = True,
) -> Dict[str, Any]:
    return video_gen.generate_heygen_video(
        prompt=prompt,
        script=script,
        title=title,
        avatar_id=avatar_id,
        voice_id=voice_id,
        use_agent=bool(use_agent),
    )


def tool_heygen_status(video_id: str = "", session_id: str = "") -> Dict[str, Any]:
    return video_gen.heygen_status(video_id=video_id, session_id=session_id)


def tool_list_video_jobs(limit: int = 20) -> Dict[str, Any]:
    return video_gen.list_video_jobs(limit=limit)


def tool_video_providers_status() -> Dict[str, Any]:
    return video_gen.video_providers_status()


# ─── Registry (add new tools here) ─────────────────────────────────────────────

TOOL_SPECS: Dict[str, Dict[str, Any]] = {
    "generate_pdf": {
        "description": (
            "Generate a PDF file (proposal, quote, SOW, NDA draft, brief, report). "
            "Pass title + body (markdown-ish: # headings, - bullets). "
            "Saved to ./data/exports/ on the host."
        ),
        "handler": tool_generate_pdf,
        "args": ["title", "body", "doc_type?", "client_name?", "filename?", "sections?", "footer_note?"],
    },
    "list_pdf_exports": {
        "description": "List recently generated PDF files in data/exports/.",
        "handler": tool_list_pdf_exports,
        "args": ["limit?"],
    },
    "firecrawl_scrape": {
        "description": "Scrape a URL to markdown (needs FIRECRAWL_API_KEY).",
        "handler": tool_firecrawl_scrape,
        "args": ["url"],
    },
    "firecrawl_search": {
        "description": "Web search via Firecrawl (needs FIRECRAWL_API_KEY).",
        "handler": tool_firecrawl_search,
        "args": ["query", "limit?"],
    },
    "generate_video_omni": {
        "description": (
            "Generate/edit short video with Google Gemini Omni Flash (default video model). "
            "Needs GOOGLE_API_KEY. Pass previous_interaction_id to refine conversationally."
        ),
        "handler": tool_generate_video_omni,
        "args": ["prompt", "aspect_ratio?", "previous_interaction_id?"],
    },
    "generate_video_veo": {
        "description": (
            "Generate cinematic video with Google Veo 3.1 (native audio). "
            "Needs GOOGLE_API_KEY. Set fast=true for veo-3.1-fast. duration_seconds: 4|6|8."
        ),
        "handler": tool_generate_video_veo,
        "args": ["prompt", "fast?", "aspect_ratio?", "duration_seconds?", "resolution?", "poll?"],
    },
    "generate_video_heygen": {
        "description": (
            "Generate presenter/avatar video via HeyGen (needs HEYGEN_API_KEY). "
            "Default uses Video Agent (prompt). For classic avatar mode set use_agent=false "
            "and provide avatar_id + voice_id (or HEYGEN_AVATAR_ID / HEYGEN_VOICE_ID)."
        ),
        "handler": tool_generate_video_heygen,
        "args": ["prompt?", "script?", "title?", "avatar_id?", "voice_id?", "use_agent?"],
    },
    "heygen_status": {
        "description": "Check HeyGen video_id or video-agent session_id status.",
        "handler": tool_heygen_status,
        "args": ["video_id?", "session_id?"],
    },
    "list_video_jobs": {
        "description": "List recent video generation job records under data/exports/videos/.",
        "handler": tool_list_video_jobs,
        "args": ["limit?"],
    },
    "video_providers_status": {
        "description": "Show which video providers (Omni/Veo/HeyGen) are configured.",
        "handler": tool_video_providers_status,
        "args": [],
    },
}


def tool_catalog_for_prompt(agent_id: str = "") -> str:
    if not ENABLE_AGENT_TOOLS:
        return ""
    lines = [
        "You can call tools for real actions. To call a tool, reply with ONLY:",
        "```tool",
        '{"name": "<tool_name>", "args": { ... }}',
        "```",
        "After tool results arrive, continue. When finished, give the final answer (no tool block).",
        "For client deliverables (proposal, quote, SOW, NDA draft), prefer generate_pdf so a file is produced.",
        "For demo/ad videos: prefer generate_video_omni (fast/iterative), generate_video_veo (cinematic), "
        "or generate_video_heygen (presenter avatar).",
        "Do not invent file paths — use tool results. Payment collection tools do not exist.",
        "",
        "Available tools:",
    ]
    for name, spec in TOOL_SPECS.items():
        lines.append(f"- {name}: {spec['description']} args={spec['args']}")
    if agent_id:
        lines.append(f"\nActing as @{agent_id}.")
    return "\n".join(lines)


def execute_tool(name: str, args: Optional[Dict[str, Any]] = None, agent_id: str = "") -> Dict[str, Any]:
    args = dict(args or {})
    spec = TOOL_SPECS.get(name)
    if not spec:
        return {"ok": False, "error": f"Unknown tool: {name}", "known": list(TOOL_SPECS.keys())}
    handler: Callable = spec["handler"]
    try:
        result = handler(**args)
        return result if isinstance(result, dict) else {"ok": True, "result": result}
    except TypeError as e:
        return {"ok": False, "error": f"Bad args for {name}: {e}", "args": args}
    except Exception as e:
        logger.exception("Tool %s failed", name)
        return {"ok": False, "error": str(e)}
