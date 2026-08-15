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
import sys
import threading
import time
from typing import Any, Dict, List, Optional

import httpx
import websockets

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Swarm-Orchestrator] %(message)s",
)
logger = logging.getLogger("orchestrator")

# Configuration from Environment
RELAY_URL = os.getenv("BUZZ_RELAY_URL", "ws://relay:8080")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DEFAULT_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "gemini")
DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "gemini-2.5-flash")
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
                "Hermes CEO",
                "Executive Orchestrator",
                f"You are Hermes, the CEO and orchestrator of {COMPANY_NAME}. Lead the swarm, delegate tasks, and drive client success.",
                self.master_privkey,
            )
            self.agents["ceo"] = ceo
            logger.info("Loaded default fallback CEO agent.")

    async def generate_llm_response(self, agent: SwarmAgent, prompt: str, context: Optional[str] = None) -> str:
        """Invokes the configured LLM provider for the agent."""
        full_system = f"{agent.system_prompt}\nCompany: {COMPANY_NAME}\nRole: {agent.role}\n"
        if context:
            full_system += f"\nConversation Context:\n{context}\n"

        # 1. Try Google Gemini with optimal model per department
        if GOOGLE_API_KEY and DEFAULT_PROVIDER in ["gemini", "auto"]:
            # Route strategic, architectural and deep research tasks to Gemini 2.5 Pro, and operational tasks to Gemini 2.5 Flash
            if agent.agent_id in ["ceo", "cto", "legal-officer", "marketer-research"]:
                primary_model = os.getenv("PRO_GEMINI_MODEL", "gemini-2.5-pro")
            else:
                primary_model = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-2.5-flash")

            for model_candidate in [primary_model, "gemini-2.5-flash", "gemini-1.5-pro"]:
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
                            logger.warning(f"Gemini model {model_candidate} returned status {resp.status_code}: {resp.text[:100]}")
                except Exception as e:
                    logger.warning(f"Gemini invocation with {model_candidate} failed ({e}), trying fallback...")

        # 2. Try OpenRouter (Multi-model gateway)
        if OPENROUTER_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                        json={
                            "model": "anthropic/claude-3.5-sonnet" if "claude" in DEFAULT_MODEL else "google/gemini-2.5-flash",
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
                logger.error(f"OpenRouter invocation failed: {e}")

        # 3. Try OpenAI
        if OPENAI_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                        json={
                            "model": "gpt-4o",
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
                logger.error(f"OpenAI invocation failed: {e}")

        # Fallback offline simulation response
        return f"[{agent.name} - {agent.role}]\nReceived: {prompt}\n\n(AI API keys not configured or currently unreachable. Set GOOGLE_API_KEY or OPENROUTER_API_KEY in .env to activate live neural reasoning.)"

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

        if not target_agent:
            # Department keyword routing
            if any(k in lower_content for k in ["code", "bug", "build", "api", "database", "backend", "frontend"]):
                target_agent = self.agents.get("fullstack-dev", target_agent)
            elif any(k in lower_content for k in ["architecture", "tech stack", "rfc"]):
                target_agent = self.agents.get("cto", target_agent)
            elif any(k in lower_content for k in ["test", "qa", "verify", "regression"]):
                target_agent = self.agents.get("qa-tester", target_agent)
            elif any(k in lower_content for k in ["marketing", "lead", "seo", "campaign", "growth"]):
                target_agent = self.agents.get("marketer-growth", target_agent)
            elif any(k in lower_content for k in ["invoice", "quote", "billing", "payment", "naira", "pricing"]):
                target_agent = self.agents.get("billing-officer", target_agent)
            elif any(k in lower_content for k in ["contract", "nda", "terms", "legal", "procurement"]):
                target_agent = self.agents.get("legal-officer", target_agent)
            elif any(k in lower_content for k in ["deploy", "docker", "vps", "server", "k8s", "caddy", "nginx"]):
                target_agent = self.agents.get("devops-agent", target_agent)

        if target_agent and content:
            # Generate response
            response_text = await self.generate_llm_response(target_agent, content)
            
            # Prepare reply tags (replying to event_id)
            reply_tags = [
                ["e", event_id, "", "reply"],
                ["p", pubkey],
            ]
            # Preserve channel tags if present
            for t in tags:
                if t and t[0] in ["h", "channel"]:
                    reply_tags.append(t)

            response_event = create_event(
                priv_hex=target_agent.privkey,
                kind=kind if kind in [KIND_STREAM_MESSAGE, KIND_TEXT_NOTE] else KIND_STREAM_MESSAGE,
                content=response_text,
                tags=reply_tags,
            )

            # Send back to Buzz Relay
            if self.ws:
                await self.ws.send(json.dumps(["EVENT", response_event]))
                logger.info(f"Published response from @{target_agent.agent_id} (ID={response_event['id'][:8]}...)")

    async def run(self):
        """Main WebSocket listener and reconnection loop."""
        while self.running:
            try:
                logger.info(f"Connecting to Buzz Relay at {RELAY_URL}...")
                async with websockets.connect(RELAY_URL, max_size=10 * 1024 * 1024) as ws:
                    self.ws = ws
                    logger.info("Connected to Buzz Relay.")

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
