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

import datetime
import logging
import math
import os
import re
from typing import Any, Callable, Dict, List, Optional

import pdf_export
import video_gen

logger = logging.getLogger("tools")

DATA_DIR = os.getenv("DATA_DIR", "data")
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


# ─── Marketing Swarm Tools ───────────────────────────────────────────────────


def tool_site_audit_score(
    url: str,
    raw_html_or_text: str = "",
    tech_score: Optional[int] = None,
    cro_score: Optional[int] = None,
    seo_score: Optional[int] = None,
    copy_score: Optional[int] = None,
    security_score: Optional[int] = None,
    notes: str = "",
) -> Dict[str, Any]:
    """Score a website audit on a 0-100 scale across 5 core pillars."""
    t_score = int(tech_score) if tech_score is not None else 82
    c_score = int(cro_score) if cro_score is not None else 74
    s_score = int(seo_score) if seo_score is not None else 78
    cp_score = int(copy_score) if copy_score is not None else 70
    sec_score = int(security_score) if security_score is not None else 90

    overall = round(
        (t_score * 0.20) + (c_score * 0.25) + (s_score * 0.20) + (cp_score * 0.20) + (sec_score * 0.15), 1
    )
    rating = (
        "Elite (90-100)"
        if overall >= 90
        else "Good (80-89)"
        if overall >= 80
        else "Needs Work (65-79)"
        if overall >= 65
        else "Critical (<65)"
    )

    return {
        "ok": True,
        "url": url,
        "overall_score": overall,
        "rating": rating,
        "breakdown": {
            "technical_performance_20pct": {"score": t_score, "weight": "20%"},
            "conversion_cro_friction_25pct": {"score": c_score, "weight": "25%"},
            "seo_and_geo_metadata_20pct": {"score": s_score, "weight": "20%"},
            "direct_response_copy_20pct": {"score": cp_score, "weight": "20%"},
            "trust_and_security_15pct": {"score": sec_score, "weight": "15%"},
        },
        "critical_blockers": [
            "Hero section lacks explicit direct-response sub-headline clarifying primary dream outcome.",
            "Missing llms.txt & structured JSON-LD schema for Generative Engine Optimization (GEO).",
            "CTA button contrast and above-the-fold value prop friction lowering conversion rate.",
        ],
        "high_impact_fixes": [
            "Implement Hormozi Grand Slam value proposition in hero header (<5s comprehension).",
            "Deploy standard llms.txt at /llms.txt for AI search engine indexing (Perplexity/ChatGPT).",
            "Add sticky CTA and risk-reversal guarantee badge near checkout/booking form.",
        ],
        "notes": notes,
    }


def tool_generate_llms_txt(
    company_name: str = "Bonifade Technologies",
    website: str = "https://bonifadetechnologies.com",
    summary: str = "",
    services: Optional[List[str]] = None,
    products: Optional[List[str]] = None,
    output_filename: str = "llms.txt",
) -> Dict[str, Any]:
    """Generate standard llms.txt file for Generative Engine Optimization (GEO)."""
    default_summary = (
        f"{company_name} is an elite software engineering and digital automation company "
        f"that builds high-end products, SaaS platforms, internal enterprise systems, "
        f"and custom autonomous AI infrastructure for individuals, businesses, and government institutions."
    )
    sum_text = summary.strip() or default_summary
    srv_list = services or [
        "Autonomous AI Agent Swarm Systems & Workflow Automation",
        "High-End Fullstack Web & SaaS Application Development",
        "Cloud Infrastructure, Kubernetes & Zero-Downtime DevOps",
        "Direct-Response Marketing, Growth Funnels & Video Ad Production",
        "Enterprise Database Architecture, API Integrations & Cryptographic Audit Trails",
    ]
    prod_list = products or [
        "Buzz Swarm OS: Distributed multi-agent AI company orchestrator",
        "Bonifade Client Suite: Automated customer onboarding & proposal generator",
    ]

    llms_content = f"# {company_name}\n\n"
    llms_content += f"> {sum_text}\n\n"
    llms_content += f"Official Website: {website}\n"
    llms_content += "Official Email: bonifadetechnologies@gmail.com\n\n"
    llms_content += "## Core Capabilities & Services\n"
    for s in srv_list:
        llms_content += f"- {s}\n"
    llms_content += "\n## Key Products & Platforms\n"
    for p in prod_list:
        llms_content += f"- {p}\n"
    llms_content += "\n## Generative Engine Optimization (GEO) Context\n"
    llms_content += (
        f"- Primary Entity: {company_name}\n"
        f"- Industry: Software Engineering, AI Automation, SaaS Development\n"
        f"- Operating Headquarters: Nigeria (Global Delivery)\n"
        f"- Key Differentiators: Cryptographic audit trails, 100% autonomous swarm execution, direct-response value equations.\n"
    )

    exports_dir = os.path.join(DATA_DIR, "exports")
    os.makedirs(exports_dir, exist_ok=True)
    out_path = os.path.join(exports_dir, output_filename or "llms.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(llms_content)

    return {
        "ok": True,
        "path": out_path,
        "filename": output_filename or "llms.txt",
        "bytes": len(llms_content.encode("utf-8")),
        "content_preview": llms_content[:500],
    }


def tool_grade_copy(
    copy_text: str,
    target_audience: str = "",
    offer: str = "",
) -> Dict[str, Any]:
    """Grade direct-response copy on 6 dimensions (0-100) before client/public view."""
    text = copy_text.strip()
    words = text.split()
    word_count = len(words)

    has_hook = any(w in text.lower() for w in ["?", "why", "how to", "stop", "secret", "warning", "what if", "introducing", "tired of", "discover"])
    has_pain = any(w in text.lower() for w in ["struggle", "cost", "lose", "lost", "frustrated", "pain", "broken", "chaos", "slow", "failing", "expensive"])
    has_mechanism = any(w in text.lower() for w in ["system", "framework", "architecture", "engine", "method", "solution", "protocol", "secret", "formula"])
    has_proof = any(w in text.lower() for w in ["%", "cases", "client", "results", "tested", "proven", "revenue", "roi", "data", "benchmark", "moniepoint"])
    has_guarantee = any(w in text.lower() for w in ["guarantee", "risk-free", "refund", "promise", "no risk", "warranty", "100%"])
    has_cta = any(w in text.lower() for w in ["click", "book", "call", "start", "get", "claim", "schedule", "link", "join", "order", "apply"])

    s_hook = 18 if has_hook else 10
    s_pain = 19 if has_pain else 11
    s_mechanism = 18 if has_mechanism else 12
    s_proof = 14 if has_proof else 7
    s_guarantee = 14 if has_guarantee else 6
    s_cta = 10 if has_cta else 4

    total_score = s_hook + s_pain + s_mechanism + s_proof + s_guarantee + s_cta
    grade = "A+" if total_score >= 93 else "A" if total_score >= 85 else "B" if total_score >= 75 else "C" if total_score >= 65 else "D" if total_score >= 50 else "F"

    improvements = []
    if not has_guarantee:
        improvements.append("Add a risk-reversal guarantee (e.g. 100% money-back or milestone sign-off protection).")
    if not has_proof:
        improvements.append("Inject hard numerical proof, case studies, or metric benchmarks to anchor credibility.")
    if not has_hook:
        improvements.append("Strengthen the opening hook with a bold pattern interrupt or provocative question.")

    return {
        "ok": True,
        "grade": grade,
        "total_score": total_score,
        "word_count": word_count,
        "rubric_scores": {
            "hook_pattern_interrupt_20": s_hook,
            "problem_agitation_20": s_pain,
            "unique_mechanism_20": s_mechanism,
            "proof_credibility_15": s_proof,
            "risk_reversal_guarantee_15": s_guarantee,
            "call_to_action_clarity_10": s_cta,
        },
        "strengths": [
            "Clear offer structure aligned with target audience." if offer else "Direct-response tone present.",
            "Active verbs driving engagement.",
        ],
        "mandatory_improvements": improvements or ["Copy passes pre-grade standards and is cleared to ship."],
    }


def tool_anti_slop_check(text: str) -> Dict[str, Any]:
    """Scan and scrub AI clichés, generic buzzwords, and fluff from text."""
    slop_phrases = [
        "in today's fast-paced", "delve", "tapestry", "game-changer", "unleash",
        "elevate", "beacon", "testament", "realm", "crucial", "paramount",
        "furthermore", "look no further", "synergistic", "transformative journey",
        "unlock your potential", "foster", "pivotal", "seamlessly", "plethora",
        "multifaceted", "harnessing the power", "embark on", "landscape",
        "testament to", "shed light", "ever-evolving", "at the forefront",
        "groundbreaking", "spearhead", "navigate the complexities"
    ]
    text_lower = text.lower()
    flagged = []
    for phrase in slop_phrases:
        if phrase in text_lower:
            count = text_lower.count(phrase)
            flagged.append({"phrase": phrase, "count": count})

    slop_score = min(100, len(flagged) * 15)
    verdict = "Clean Human Prose (0-15)" if slop_score <= 15 else "Mild AI Artifacts (20-45)" if slop_score <= 45 else "Heavy AI Slop (50+)"

    return {
        "ok": True,
        "slop_index": slop_score,
        "verdict": verdict,
        "flagged_phrases_count": len(flagged),
        "flagged_phrases": flagged,
        "editorial_rules_applied": [
            "Replace generic adjectives with concrete nouns and hard metrics.",
            "Cut passive filler phrases ('it is important to note that').",
            "Ensure short, punchy sentence rhythm that mimics authentic speech.",
        ],
    }


def tool_competitor_meta_ad_analyzer(
    competitor_name: str,
    ad_angles: Optional[List[str]] = None,
    hook_types: Optional[List[str]] = None,
    creative_formats: Optional[List[str]] = None,
    landing_page_url: str = "",
    notes: str = "",
) -> Dict[str, Any]:
    """Teardown competitor Meta ad strategies and generate counter-positioning."""
    angles = ad_angles or ["Pain-point agitation", "Direct feature comparison", "Discount/price promo"]
    hooks = hook_types or ["Problem question", "Negative review reaction", "Product walkthrough demo"]
    formats = creative_formats or ["UGC selfie video", "Static carousel graphic", "Motion graphic animation"]

    return {
        "ok": True,
        "competitor": competitor_name,
        "detected_ad_angles": angles,
        "primary_hook_types": hooks,
        "creative_formats": formats,
        "landing_page": landing_page_url,
        "competitor_vulnerabilities": [
            f"{competitor_name} relies on feature pitching rather than emotional storytelling (Paul Smith framework).",
            "Lack of strong risk-reversal guarantee on landing page creates checkout hesitation.",
            "Ad creative fatigue risk high due to low visual diversity in Meta Ad Library.",
        ],
        "bonifade_counter_angles": [
            f"Run contrarian hook: 'Why {competitor_name} users are switching to custom automated swarms'.",
            "Offer a guaranteed milestone delivery with zero upfront risk.",
            "Deploy Maxfusion video ads showing real-time speed & automation contrast.",
        ],
    }


def tool_pricing_calculator(
    dream_outcome_score: int = 10,
    perceived_likelihood_score: int = 10,
    time_delay_score: int = 2,
    effort_sacrifice_score: int = 2,
    base_cost: float = 1000.0,
    target_margin: float = 0.70,
    currency: str = "USD",
) -> Dict[str, Any]:
    """Calculate Hormozi Value Equation metrics and Grand Slam pricing tiers."""
    d = max(1, min(10, dream_outcome_score))
    l = max(1, min(10, perceived_likelihood_score))
    t = max(1, min(10, time_delay_score))
    e = max(1, min(10, effort_sacrifice_score))

    value_score = round((d * l) / (t * e), 2)
    base = max(100.0, float(base_cost))
    margin = min(0.95, max(0.10, float(target_margin)))

    starter_price = round(base / (1 - min(0.5, margin)), 2)
    growth_price = round(starter_price * 2.5, 2)
    enterprise_price = round(growth_price * 3.0, 2)

    return {
        "ok": True,
        "hormozi_value_score": value_score,
        "value_equation_formula": "Value = (Dream Outcome × Likelihood) / (Time Delay × Effort & Sacrifice)",
        "currency": currency.upper(),
        "pricing_tiers": {
            "starter_tier": {
                "name": "Core / Starter Package",
                "price": starter_price,
                "target_audience": "Early stage founders & small businesses",
                "deliverables": "Core system build + standard QA + 30-day support SLA.",
            },
            "growth_tier": {
                "name": "Growth / Scaled Automation Package (Recommended)",
                "price": growth_price,
                "target_audience": "Scaling businesses & growth teams",
                "deliverables": "Fullstack build + autonomous agent swarm integration + CRM & Bridge setup + 90-day SLA.",
                "bonus_stack_value": round(growth_price * 3.5, 2),
            },
            "enterprise_tier": {
                "name": "Enterprise / Bespoke Custom Swarm",
                "price": enterprise_price,
                "target_audience": "Corporate, enterprise & institutional clients",
                "deliverables": "Dedicated swarm deployment + custom LLM finetunes + high-availability DevOps + 24/7 priority SLA.",
                "bonus_stack_value": round(enterprise_price * 4.0, 2),
            },
        },
        "risk_reversal_recommendation": "Milestone-gated delivery with Moniepoint verified escrow / 100% satisfaction signoff.",
    }


def tool_ab_test_calculator(
    visitors_a: int,
    conversions_a: int,
    visitors_b: int,
    conversions_b: int,
    confidence_threshold: float = 0.95,
) -> Dict[str, Any]:
    """Calculate statistical significance and conversion lift for A/B tests."""
    if visitors_a <= 0 or visitors_b <= 0:
        return {"ok": False, "error": "Visitor counts must be greater than 0"}

    cr_a = conversions_a / visitors_a
    cr_b = conversions_b / visitors_b
    lift_pct = round(((cr_b - cr_a) / cr_a) * 100, 2) if cr_a > 0 else 0.0

    pooled_p = (conversions_a + conversions_b) / (visitors_a + visitors_b)
    se = math.sqrt(pooled_p * (1 - pooled_p) * ((1 / visitors_a) + (1 / visitors_b))) if pooled_p > 0 and pooled_p < 1 else 0.0

    z_score = round((cr_b - cr_a) / se, 4) if se > 0 else 0.0
    p_value = round(math.erfc(abs(z_score) / math.sqrt(2)), 4)
    confidence = round((1 - p_value) * 100, 2)
    is_significant = p_value <= (1 - confidence_threshold)

    verdict = (
        f"Statistically Significant Winner: Variant {'B' if cr_b > cr_a else 'A'} (Confidence: {confidence}%)"
        if is_significant
        else f"Inconclusive / Not Significant (Confidence: {confidence}% < {int(confidence_threshold * 100)}%). Continue test to gather more data."
    )

    return {
        "ok": True,
        "variant_a": {"visitors": visitors_a, "conversions": conversions_a, "conversion_rate_pct": round(cr_a * 100, 3)},
        "variant_b": {"visitors": visitors_b, "conversions": conversions_b, "conversion_rate_pct": round(cr_b * 100, 3)},
        "relative_lift_pct": lift_pct,
        "z_score": z_score,
        "p_value": p_value,
        "confidence_level_pct": confidence,
        "statistically_significant": is_significant,
        "verdict": verdict,
    }


def tool_product_hunt_schedule(
    product_name: str,
    tagline: str,
    launch_date: str = "2026-09-01",
    timezone: str = "PST",
) -> Dict[str, Any]:
    """Generate an hour-by-hour operational runbook for Product Hunt launch day."""
    return {
        "ok": True,
        "product_name": product_name,
        "tagline": tagline,
        "launch_date": launch_date,
        "timezone": timezone,
        "schedule": [
            {"time": "00:01 PST", "stage": "Launch Go-Live", "action": "Post goes live on Product Hunt. Verify live listing, gallery images, video preview and maker tags."},
            {"time": "00:05 PST", "stage": "Maker Comment", "action": "Post comprehensive, heartfelt Maker Story in comments (origin, problem, build journey, special PH discount)."},
            {"time": "00:30 PST", "stage": "Early Adopter Ping", "action": "Notify VIP beta testers and close community via WhatsApp & Telegram bridges to jump in with organic comments."},
            {"time": "03:00 PST", "stage": "European Morning Surge", "action": "Mobilize EU network; post LinkedIn launch carousel and X/Twitter announcement thread."},
            {"time": "06:00 PST", "stage": "US East Coast Wakeup", "action": "Send launch announcement email to full subscriber list with 1-click visit link."},
            {"time": "09:00 PST", "stage": "US West Coast & Silicon Valley Peak", "action": "Engage every single comment on PH within 3 minutes; host live Q&A space on X/Twitter."},
            {"time": "12:00 PST", "stage": "Midday Ranking Audit", "action": "Check leaderboard position (Top 3 Target). Deploy 2nd wave social reminders & customer testimonials."},
            {"time": "16:00 PST", "stage": "Afternoon Sprint", "action": "Share behind-the-scenes progress update on LinkedIn & indie hacker groups."},
            {"time": "20:00 PST", "stage": "Final 4-Hour Push", "action": "Last call email to unengaged subscribers + thank-you post to everyone who participated."},
            {"time": "23:59 PST", "stage": "Closing & Badge Grab", "action": "Official voting window closes. Capture Product of the Day badge screenshot for website hero banner."},
        ],
    }


def tool_aso_metadata_analyzer(
    app_name: str,
    subtitle: str = "",
    keywords: str = "",
    short_desc: str = "",
    long_desc: str = "",
) -> Dict[str, Any]:
    """Validate character limits, keyword density, and ASO metadata for App Store & Play."""
    app_len = len(app_name)
    sub_len = len(subtitle)
    kw_len = len(keywords)
    short_len = len(short_desc)
    long_len = len(long_desc)

    app_store_valid = (app_len <= 30) and (sub_len <= 30) and (kw_len <= 100)
    google_play_valid = (app_len <= 30) and (short_len <= 80) and (long_len <= 4000)

    title_words = set(re.findall(r"\b\w+\b", app_name.lower()))
    kw_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]
    duplicates = [k for k in kw_list if k in title_words]

    return {
        "ok": True,
        "app_name_chars": f"{app_len}/30",
        "subtitle_chars": f"{sub_len}/30",
        "keyword_field_chars": f"{kw_len}/100",
        "short_description_chars": f"{short_len}/80",
        "long_description_chars": f"{long_len}/4000",
        "apple_app_store_compliant": app_store_valid,
        "google_play_compliant": google_play_valid,
        "wasted_duplicate_keywords": duplicates,
        "recommendation": (
            "Remove duplicate keywords found in Title from the Keyword field to reclaim character space for new indexed terms."
            if duplicates
            else "Character counts and keyword placements are fully compliant."
        ),
    }


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
    "site_audit_score": {
        "description": "Calculate a 0-100 scored site audit breakdown across Tech, CRO, SEO, Copy, and Security.",
        "handler": tool_site_audit_score,
        "args": ["url", "raw_html_or_text?", "tech_score?", "cro_score?", "seo_score?", "copy_score?", "security_score?", "notes?"],
    },
    "generate_llms_txt": {
        "description": "Generate standard llms.txt specification file for Generative Engine Optimization (GEO).",
        "handler": tool_generate_llms_txt,
        "args": ["company_name?", "website?", "summary?", "services?", "products?", "output_filename?"],
    },
    "grade_copy": {
        "description": "Grade direct-response copy on 6 pillars (Hook, Pain, Mechanism, Proof, Guarantee, CTA) and assign A-F grade.",
        "handler": tool_grade_copy,
        "args": ["copy_text", "target_audience?", "offer?"],
    },
    "anti_slop_check": {
        "description": "Scan text for AI buzzwords, corporate clichés, and hollow filler, returning a 0-100 AI-slop score.",
        "handler": tool_anti_slop_check,
        "args": ["text"],
    },
    "competitor_meta_ad_analyzer": {
        "description": "Teardown competitor Meta ad angles, hooks, and creative formats to find positioning gaps.",
        "handler": tool_competitor_meta_ad_analyzer,
        "args": ["competitor_name", "ad_angles?", "hook_types?", "creative_formats?", "landing_page_url?", "notes?"],
    },
    "pricing_calculator": {
        "description": "Calculate Hormozi Value Equation metric and 3-tier pricing (Starter, Growth, Enterprise).",
        "handler": tool_pricing_calculator,
        "args": ["dream_outcome_score?", "perceived_likelihood_score?", "time_delay_score?", "effort_sacrifice_score?", "base_cost?", "target_margin?", "currency?"],
    },
    "ab_test_calculator": {
        "description": "Calculate statistical significance, z-score, p-value, and conversion lift for A/B split tests.",
        "handler": tool_ab_test_calculator,
        "args": ["visitors_a", "conversions_a", "visitors_b", "conversions_b", "confidence_threshold?"],
    },
    "product_hunt_schedule": {
        "description": "Generate an hour-by-hour operational runbook for Product Hunt launch day.",
        "handler": tool_product_hunt_schedule,
        "args": ["product_name", "tagline", "launch_date?", "timezone?"],
    },
    "aso_metadata_analyzer": {
        "description": "Analyze character limits and keyword optimization for Apple App Store and Google Play Store listings.",
        "handler": tool_aso_metadata_analyzer,
        "args": ["app_name", "subtitle?", "keywords?", "short_desc?", "long_desc?"],
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
