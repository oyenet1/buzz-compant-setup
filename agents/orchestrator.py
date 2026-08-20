#!/usr/bin/env python3
"""
Bonifade Technologies Swarm — Multi-Agent AI Orchestrator for Buzz Hive Mind Relay.
Coordinates AI department agents (CEO, CTO, Dev, QA, Marketing, Support, Billing, Legal, DevOps),
listens to Buzz events & channels, executes LLM completions, and signs/publishes responses.
"""

import asyncio
import glob
import http.server
import json
import logging
import os
import re
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
import websockets

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _AGENT_DIR not in sys.path:
    sys.path.insert(0, _AGENT_DIR)

# Import our pure-python Nostr utilities
from nostr_util import (
    KIND_AUTH,
    KIND_JOB_REQUEST,
    KIND_JOB_RESULT,
    KIND_METADATA,
    KIND_STREAM_MESSAGE,
    KIND_TEXT_NOTE,
    create_auth_event,
    create_event,
    generate_keypair,
    get_pubkey_from_privkey,
)

from tools import ENABLE_AGENT_TOOLS, execute_tool, tool_catalog_for_prompt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Swarm-Orchestrator] %(message)s",
)
logger = logging.getLogger("orchestrator")

# Configuration from Environment
RELAY_URL = os.getenv("BUZZ_RELAY_URL", "ws://relay:8080")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
DEFAULT_GEMINI_MODEL = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.5-flash").strip()
PRO_GEMINI_MODEL = os.getenv("PRO_GEMINI_MODEL", "gemini-3.7-flash").strip()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
XAI_API_KEY = (os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY") or "").strip()
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "").strip()
GLM_API_KEY = (os.getenv("GLM_API_KEY") or os.getenv("ZHIPU_API_KEY") or "").strip()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
META_AI_API_KEY = (os.getenv("META_AI_API_KEY") or os.getenv("LLAMA_API_KEY") or os.getenv("GROQ_API_KEY") or "").strip()

DEFAULT_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "gemini")
DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "gemini-3.5-flash")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Bonifade Technologies")
DEPARTMENTS_DIR = os.getenv("DEPARTMENTS_DIR", "/app/departments")
MARKETING_DIR = os.getenv("MARKETING_DIR", "/app/marketing")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")

# Fallback local paths
if not os.path.exists(DEPARTMENTS_DIR) and os.path.exists("departments"):
    DEPARTMENTS_DIR = "departments"
if not os.path.exists(MARKETING_DIR) and os.path.exists("marketing"):
    MARKETING_DIR = "marketing"
if not os.path.exists(DATA_DIR) and os.path.exists("data"):
    DATA_DIR = "data"

MAX_TOOL_ROUNDS = int(os.getenv("MAX_TOOL_ROUNDS", "5"))
_TOOL_BLOCK_RE = re.compile(r"```tool\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


def parse_tool_call(text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    if not text:
        return None
    match = _TOOL_BLOCK_RE.search(text)
    raw = match.group(1) if match else None
    if not raw:
        bare = re.search(
            r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"args"\s*:\s*(\{.*?\})\s*\}',
            text,
            re.DOTALL,
        )
        if not bare:
            return None
        try:
            return bare.group(1), json.loads(bare.group(2))
        except json.JSONDecodeError:
            return None
    try:
        payload = json.loads(raw)
        name = payload.get("name")
        args = payload.get("args") or {}
        if not name or not isinstance(args, dict):
            return None
        return str(name), args
    except json.JSONDecodeError:
        return None


class SwarmAgent:
    def __init__(self, agent_id: str, name: str, role: str, system_prompt: str, privkey: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.privkey = privkey
        self.pubkey = get_pubkey_from_privkey(privkey)


class SwarmOrchestrator:
    def __init__(self):
        self.agents: Dict[str, SwarmAgent] = {}
        self.master_privkey, self.master_pubkey = self._load_or_create_keys()
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = True
        self._load_departments()

    def _load_or_create_keys(self):
        key_file = os.path.join(DATA_DIR, "orchestrator_keys.json")
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(key_file):
            try:
                with open(key_file, "r") as f:
                    data = json.load(f)
                    return data["privkey"], data["pubkey"]
            except Exception as e:
                logger.warning(f"Failed to read key file {key_file}: {e}")

        priv, pub = generate_keypair()
        with open(key_file, "w") as f:
            json.dump({"privkey": priv, "pubkey": pub}, f, indent=2)
        logger.info(f"Generated new Swarm Orchestrator keypair: pubkey={pub}")
        return priv, pub

    def _load_departments(self):
        dept_files = glob.glob(os.path.join(DEPARTMENTS_DIR, "*.json"))
        for file_path in dept_files:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    agent_id = data.get("id", os.path.splitext(os.path.basename(file_path))[0])
                    name = data.get("name", agent_id.capitalize())
                    role = data.get("role", "Department Specialist")
                    prompt = data.get("system_prompt", f"You are {name}, {role} at {COMPANY_NAME}.")
                    
                    # Agent specific key derivation or generation
                    agent_key_file = os.path.join(DATA_DIR, f"agent_{agent_id}_keys.json")
                    if os.path.exists(agent_key_file):
                        with open(agent_key_file, "r") as kf:
                            kdata = json.load(kf)
                            priv = kdata["privkey"]
                    else:
                        priv, pub = generate_keypair()
                        with open(agent_key_file, "w") as kf:
                            json.dump({"privkey": priv, "pubkey": pub}, kf, indent=2)

                    agent = SwarmAgent(agent_id, name, role, prompt, priv)
                    self.agents[agent_id] = agent
                    logger.info(f"Loaded department agent: @{agent_id} ({name} - {role}) [pubkey={agent.pubkey[:12]}...]")
            except Exception as e:
                logger.error(f"Error loading department config from {file_path}: {e}")

        # Fallback default CEO agent if none loaded
        if not self.agents:
            ceo = SwarmAgent(
                "ceo",
                "Fade_networker",
                "Executive Orchestrator",
                f"You are Fade_networker, the CEO and orchestrator of {COMPANY_NAME}. Lead the swarm, delegate tasks, and drive client success.",
                self.master_privkey,
            )
            self.agents["ceo"] = ceo
            logger.info("Loaded default fallback CEO agent (Fade_networker).")

    async def generate_llm_response(self, agent: SwarmAgent, prompt: str, context: Optional[str] = None) -> str:
        """Invokes the configured LLM provider for the agent."""
        full_system = f"{agent.system_prompt}\nCompany: {COMPANY_NAME}\nRole: {agent.role}\n"
        full_system += (
            "\nWhen the user asks for a proposal, quote, SOW, NDA draft, or report file, "
            "use the generate_pdf tool so a real PDF is saved under data/exports/.\n"
            "Do not claim payment collection — quotes/pricing only.\n"
        )
        if ENABLE_AGENT_TOOLS:
            full_system += "\n" + tool_catalog_for_prompt(agent.agent_id) + "\n"
        if context:
            full_system += f"\nConversation Context:\n{context}\n"

        # 1. Primary: Google Gemini (3.7 Flash for Advanced Roles, 3.6/3.5 Flash for Operational Roles)
        if GOOGLE_API_KEY:
            is_advanced_role = agent.agent_id in ["ceo", "cto", "legal-officer", "marketer-research"]
            gemini_candidates = [
                PRO_GEMINI_MODEL,
                "gemini-3.7-flash",
                "gemini-3.6-flash",
                "gemini-3.5-flash",
                "gemini-3.1-pro-preview",
            ] if is_advanced_role else [
                DEFAULT_GEMINI_MODEL,
                "gemini-3.6-flash",
                "gemini-3.5-flash",
                "gemini-3.7-flash",
            ]

            for model_candidate in gemini_candidates:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_candidate}:generateContent?key={GOOGLE_API_KEY}"
                    payload = {
                        "contents": [{"parts": [{"text": f"System Context: {full_system}\n\nUser Request: {prompt}"}]}],
                        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096},
                    }
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            res_json = resp.json()
                            text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                            return text
                        else:
                            logger.warning(f"Google Gemini ({model_candidate}) returned status {resp.status_code}: {resp.text[:100]}")
                except Exception as e:
                    logger.warning(f"Google Gemini ({model_candidate}) failed: {e}")

        # 2. Fallback: Anthropic Claude Direct (Claude Opus 4.8 / Claude 3.7 Sonnet / 3.5 Sonnet)
        if ANTHROPIC_API_KEY:
            for claude_model in ["claude-4-8-opus", "claude-4-opus", "claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022"]:
                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        resp = await client.post(
                            "https://api.anthropic.com/v1/messages",
                            headers={
                                "x-api-key": ANTHROPIC_API_KEY,
                                "anthropic-version": "2023-06-01",
                                "content-type": "application/json",
                            },
                            json={
                                "model": claude_model,
                                "max_tokens": 4096,
                                "system": full_system,
                                "messages": [{"role": "user", "content": prompt}],
                            },
                        )
                        if resp.status_code == 200:
                            res_json = resp.json()
                            return res_json["content"][0]["text"]
                except Exception as e:
                    logger.warning(f"Anthropic Claude ({claude_model}) failed: {e}")

        # 3. Fallback: OpenAI Direct (GPT-5.3 / GPT-5 / o3-mini Reasoning / GPT-4.5 / GPT-4o)
        if OPENAI_API_KEY:
            for openai_model in ["gpt-5.3", "gpt-5", "o3-mini", "gpt-4.5-preview", "gpt-4o", "gpt-4o-mini"]:
                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        payload_oa = {
                            "model": openai_model,
                            "messages": [
                                {"role": "system", "content": full_system},
                                {"role": "user", "content": prompt},
                            ],
                        }
                        if openai_model.startswith("o"):
                            payload_oa["max_completion_tokens"] = 4096
                        resp = await client.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                            json=payload_oa,
                        )
                        if resp.status_code == 200:
                            res_json = resp.json()
                            return res_json["choices"][0]["message"]["content"]
                except Exception as e:
                    logger.warning(f"OpenAI ({openai_model}) failed: {e}")

        # 4. Fallback: xAI Grok Direct (Grok-4.5 / Grok-4 / Grok-3 / Grok-2)
        if XAI_API_KEY:
            for grok_model in ["grok-4.5", "grok-4", "grok-3", "grok-3-beta", "grok-2-latest"]:
                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        resp = await client.post(
                            "https://api.x.ai/v1/chat/completions",
                            headers={"Authorization": f"Bearer {XAI_API_KEY}"},
                            json={
                                "model": grok_model,
                                "messages": [
                                    {"role": "system", "content": full_system},
                                    {"role": "user", "content": prompt},
                                ],
                            },
                        )
                        if resp.status_code == 200:
                            res_json = resp.json()
                            return res_json["choices"][0]["message"]["content"]
                except Exception as e:
                    logger.warning(f"xAI Grok ({grok_model}) failed: {e}")

        # 5. Fallback: DeepSeek Direct (DeepSeek V4 Flash / R1 Reasoner / V3)
        if DEEPSEEK_API_KEY:
            for ds_model in ["deepseek-v4-flash", "deepseek-v4", "deepseek-reasoner", "deepseek-chat"]:
                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        resp = await client.post(
                            "https://api.deepseek.com/chat/completions",
                            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                            json={
                                "model": ds_model,
                                "messages": [
                                    {"role": "system", "content": full_system},
                                    {"role": "user", "content": prompt},
                                ],
                            },
                        )
                        if resp.status_code == 200:
                            res_json = resp.json()
                            return res_json["choices"][0]["message"]["content"]
                except Exception as e:
                    logger.warning(f"DeepSeek ({ds_model}) failed: {e}")

        # 6. Fallback: GLM / Zhipu Direct (GLM-5.2 / GLM-5 / GLM-4-Plus)
        if GLM_API_KEY:
            for glm_model in ["glm-5.2", "glm-5", "glm-4-plus", "glm-4-flash"]:
                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        resp = await client.post(
                            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                            headers={"Authorization": f"Bearer {GLM_API_KEY}"},
                            json={
                                "model": glm_model,
                                "messages": [
                                    {"role": "system", "content": full_system},
                                    {"role": "user", "content": prompt},
                                ],
                            },
                        )
                        if resp.status_code == 200:
                            res_json = resp.json()
                            return res_json["choices"][0]["message"]["content"]
                except Exception as e:
                    logger.warning(f"GLM ({glm_model}) failed: {e}")

        # 7. Fallback: MiniMax Direct (MiniMax 3 / MiniMax-Text-01)
        if MINIMAX_API_KEY:
            for mm_model in ["minimax-3", "MiniMax-Text-03", "MiniMax-Text-01"]:
                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        resp = await client.post(
                            "https://api.minimax.chat/v1/text/chatcompletion_v2",
                            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
                            json={
                                "model": mm_model,
                                "messages": [
                                    {"role": "system", "content": full_system},
                                    {"role": "user", "content": prompt},
                                ],
                            },
                        )
                        if resp.status_code == 200:
                            res_json = resp.json()
                            return res_json["choices"][0]["message"]["content"]
                except Exception as e:
                    logger.warning(f"MiniMax ({mm_model}) failed: {e}")

        # 8. Fallback: Meta AI / Llama / Muse Direct (Llama 3.3 70B / Meta Muse)
        if META_AI_API_KEY:
            try:
                endpoint = os.getenv("META_AI_ENDPOINT", "https://api.groq.com/openai/v1/chat/completions")
                model_name = os.getenv("META_AI_MODEL", "llama-3.3-70b-versatile")
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        endpoint,
                        headers={"Authorization": f"Bearer {META_AI_API_KEY}"},
                        json={
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": full_system},
                                {"role": "user", "content": prompt},
                            ],
                        },
                    )
                    if resp.status_code == 200:
                        res_json = resp.json()
                        return res_json["choices"][0]["message"]["content"]
            except Exception as e:
                logger.warning(f"Meta AI / Llama invocation failed: {e}")

        # 9. Fallback: OpenRouter Universal Gateway (Access to Claude Opus 4.8, Grok 4.5, DeepSeek V4, GLM 5.2, MiniMax 3)
        if OPENROUTER_API_KEY:
            openrouter_models = [
                "anthropic/claude-4-8-opus",
                "x-ai/grok-4.5",
                "deepseek/deepseek-v4-flash",
                "zhipu/glm-5.2",
                "minimax/minimax-3",
                "openai/gpt-5.3",
                "openai/gpt-5",
                "google/gemini-3.7-flash",
                "anthropic/claude-3.7-sonnet",
                "x-ai/grok-3",
                "deepseek/deepseek-r1",
                "meta-llama/llama-3.3-70b-instruct",
                "x-ai/grok-2",
                "deepseek/deepseek-chat",
                "minimax/minimax-01",
                "zhipu/glm-4-plus",
                "openai/gpt-4.5-preview",
                "openai/o3-mini",
                "meta-llama/llama-3.1-405b-instruct",
            ]
            for or_model in openrouter_models:
                try:
                    async with httpx.AsyncClient(timeout=45.0) as client:
                        resp = await client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                            json={
                                "model": or_model,
                                "messages": [
                                    {"role": "system", "content": full_system},
                                    {"role": "user", "content": prompt},
                                ],
                            },
                        )
                        if resp.status_code == 200:
                            res_json = resp.json()
                            return res_json["choices"][0]["message"]["content"]
                except Exception:
                    continue

        # Fallback offline simulation response
        return f"[{agent.name} - {agent.role}]\nReceived: {prompt}\n\n(AI providers currently unreachable. Set valid API keys in .env.)"

    async def run_agent_with_tools(self, agent: SwarmAgent, user_prompt: str) -> Tuple[str, List[Dict[str, Any]]]:
        """LLM ↔ tool loop (PDF generation, Firecrawl, etc.)."""
        tool_trace: List[Dict[str, Any]] = []
        context: Optional[str] = None
        prompt = user_prompt

        if not ENABLE_AGENT_TOOLS:
            return await self.generate_llm_response(agent, prompt), tool_trace

        for round_i in range(MAX_TOOL_ROUNDS):
            text = await self.generate_llm_response(agent, prompt, context=context)
            parsed = parse_tool_call(text)
            if not parsed:
                return text.strip(), tool_trace

            tool_name, tool_args = parsed
            logger.info(
                "Tool call round=%s agent=@%s tool=%s",
                round_i + 1,
                agent.agent_id,
                tool_name,
            )
            result = await asyncio.to_thread(execute_tool, tool_name, tool_args, agent.agent_id)
            tool_trace.append({"name": tool_name, "args": tool_args, "result": result})
            context = (context or "") + (
                f"\n\nTool result [{tool_name}]:\n{json.dumps(result, ensure_ascii=False)[:8000]}\n"
                "Continue with another tool if needed, otherwise give the final user-facing reply "
                "including any generated file path/filename."
            )
            prompt = (
                f"Original user request:\n{user_prompt}\n\n"
                f"Tool `{tool_name}` returned. Call another tool or produce the final answer."
            )

        final = await self.generate_llm_response(
            agent,
            f"Original request:\n{user_prompt}\n\nProduce the final answer now. Do not call more tools.",
            context=context,
        )
        return final.strip(), tool_trace

    async def handle_event(self, event: Dict[str, Any]):
        """Processes incoming events from Buzz Relay."""
        kind = event.get("kind")
        content = event.get("content", "").strip()
        pubkey = event.get("pubkey", "")
        event_id = event.get("id", "")
        tags = event.get("tags", [])

        # Prevent responding to our own agent messages
        all_agent_pubkeys = {a.pubkey for a in self.agents.values()}
        if pubkey in all_agent_pubkeys or pubkey == self.master_pubkey:
            return

        logger.info(f"Incoming Buzz Event kind={kind} id={event_id[:8]}... content='{content[:60]}...'")

        # Determine which agent should answer
        target_agent = self.agents.get("ceo")
        lower_content = content.lower()

        for agent_id, agent in self.agents.items():
            if f"@{agent_id}" in lower_content or f"@{agent.name.lower()}" in lower_content:
                target_agent = agent
                break
        else:
            # Department keyword routing
            if any(k in lower_content for k in ["code", "bug", "build", "api", "database", "backend", "frontend"]):
                target_agent = self.agents.get("fullstack-dev", target_agent)
            elif any(k in lower_content for k in ["architecture", "tech stack", "rfc"]):
                target_agent = self.agents.get("cto", target_agent)
            elif any(k in lower_content for k in ["test", "qa", "verify", "regression"]):
                target_agent = self.agents.get("qa-tester", target_agent)
            elif any(k in lower_content for k in ["pdf", "proposal", "quote", "document", "sow"]):
                if any(k in lower_content for k in ["quote", "pricing", "naira", "estimate"]):
                    target_agent = self.agents.get("billing-officer", target_agent)
                elif any(k in lower_content for k in ["nda", "contract", "legal"]):
                    target_agent = self.agents.get("legal-officer", target_agent)
                else:
                    target_agent = self.agents.get("marketer-content", target_agent)
            elif any(k in lower_content for k in ["marketing", "lead", "seo", "campaign", "growth"]):
                target_agent = self.agents.get("marketer-growth", target_agent)
            elif any(k in lower_content for k in ["invoice", "billing", "payment", "naira", "pricing"]):
                target_agent = self.agents.get("billing-officer", target_agent)
            elif any(k in lower_content for k in ["contract", "nda", "terms", "legal", "procurement"]):
                target_agent = self.agents.get("legal-officer", target_agent)
            elif any(k in lower_content for k in ["deploy", "docker", "vps", "server", "k8s", "caddy", "nginx"]):
                target_agent = self.agents.get("devops-agent", target_agent)

        if target_agent and content:
            response_text, tool_trace = await self.run_agent_with_tools(target_agent, content)

            for step in tool_trace:
                if step.get("name") == "generate_pdf":
                    res = step.get("result") or {}
                    if res.get("ok"):
                        response_text += (
                            f"\n\n---\n📄 PDF ready: `{res.get('filename')}` "
                            f"→ `{res.get('path')}` ({res.get('bytes')} bytes)"
                        )

            # Prepare reply tags
            reply_tags = [
                ["e", event_id, "", "reply"],
                ["p", pubkey],
            ]

            # Preserve channel and bridge routing metadata tags
            tag_dict = {t[0]: t[1] for t in tags if len(t) >= 2}
            for t in tags:
                if t and len(t) >= 2 and t[0] in ["h", "channel", "telegram_chat_id", "telegram_msg_id", "whatsapp_phone", "author_name"]:
                    reply_tags.append(t)

            # If this was an inbound client email, automatically prepare outbound SMTP dispatch
            if "email_from" in tag_dict:
                from_email = tag_dict["email_from"]
                subj = tag_dict.get("email_subject", "Bonifade Inquiry")
                clean_subj = subj if subj.startswith("Re:") else f"Re: {subj}"
                reply_tags.append(["send_email", from_email])
                reply_tags.append(["subject", clean_subj])

            response_event = create_event(
                priv_hex=target_agent.privkey,
                kind=kind if kind in [KIND_STREAM_MESSAGE, KIND_TEXT_NOTE] else KIND_STREAM_MESSAGE,
                content=response_text,
                tags=reply_tags,
            )

            # Send back to Buzz Relay (which bridges automatically dispatch to Telegram, WhatsApp & SMTP)
            if self.ws:
                await self.ws.send(json.dumps(["EVENT", response_event]))
                logger.info(
                    f"✓ Autonomous response published from @{target_agent.agent_id} "
                    f"(ID={response_event['id'][:8]}..., tools={len(tool_trace)})"
                )

    async def autonomous_scheduler(self):
        """Background autonomous scheduler: Site monitor health checks & CEO briefings."""
        logger.info("Starting autonomous background scheduler...")
        while self.running:
            try:
                # 1. Autonomous Site Monitor Check (Every 5 minutes)
                monitor_agent = self.agents.get("site-monitor")
                if monitor_agent and self.ws:
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            resp = await client.get("https://bonifadetechnologies.com")
                            if resp.status_code != 200:
                                alert_ev = create_event(
                                    priv_hex=monitor_agent.privkey,
                                    kind=KIND_STREAM_MESSAGE,
                                    content=f"⚠️ **Site Monitor Alert**: bonifadetechnologies.com returned status {resp.status_code}",
                                    tags=[["channel", "incident-room"], ["telegram_notify", "true"], ["whatsapp_notify", "true"]],
                                )
                                await self.ws.send(json.dumps(["EVENT", alert_ev]))
                    except Exception:
                        pass  # Silent if network unreachable in isolated dev
            except Exception as e:
                logger.error(f"Error in autonomous scheduler: {e}")

            await asyncio.sleep(300)

    async def run(self):
        """Main WebSocket listener and reconnection loop."""
        while self.running:
            try:
                logger.info(f"Connecting to Buzz Relay at {RELAY_URL}...")
                async with websockets.connect(RELAY_URL, max_size=10 * 1024 * 1024) as ws:
                    self.ws = ws
                    logger.info("Connected to Buzz Relay.")
                    asyncio.create_task(self.autonomous_scheduler())

                    # Subscribe to Chat Messages & Job Requests
                    sub_id = "swarm-sub-01"
                    req_msg = [
                        "REQ",
                        sub_id,
                        {"kinds": [KIND_TEXT_NOTE, KIND_STREAM_MESSAGE, KIND_JOB_REQUEST], "limit": 10},
                    ]
                    await ws.send(json.dumps(req_msg))
                    logger.info(f"Subscribed to Buzz events with sub_id={sub_id}")

                    async for message in ws:
                        try:
                            msg_json = json.loads(message)
                            msg_type = msg_json[0]

                            if msg_type == "AUTH":
                                # NIP-42 Challenge received
                                challenge = msg_json[1]
                                logger.info(f"Relay sent AUTH challenge: {challenge}")
                                auth_event = create_auth_event(self.master_privkey, challenge, RELAY_URL)
                                await ws.send(json.dumps(["AUTH", auth_event]))
                                logger.info("Submitted signed NIP-42 AUTH response.")

                            elif msg_type == "EVENT":
                                sub = msg_json[1]
                                event = msg_json[2]
                                asyncio.create_task(self.handle_event(event))

                            elif msg_type == "OK":
                                logger.debug(f"Relay OK: {msg_json}")

                            elif msg_type == "NOTICE":
                                logger.info(f"Relay NOTICE: {msg_json[1]}")

                        except Exception as e:
                            logger.error(f"Error parsing relay message: {e}")

            except (websockets.exceptions.ConnectionClosed, OSError) as e:
                logger.warning(f"Relay connection lost ({e}). Reconnecting in 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error in relay loop: {e}. Retrying in 5s...")
                await asyncio.sleep(5)


# Lightweight HTTP Health Server for Docker container healthcheck
class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ["/health", "/_liveness", "/_readiness"]:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"healthy","service":"buzz-agent-orchestrator"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Quiet logging


def start_health_server(port=8888):
    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    logger.info(f"Health check server running on port {port}")


if __name__ == "__main__":
    start_health_server(8888)
    orchestrator = SwarmOrchestrator()
    try:
        asyncio.run(orchestrator.run())
    except KeyboardInterrupt:
        logger.info("Stopping Swarm Orchestrator...")
