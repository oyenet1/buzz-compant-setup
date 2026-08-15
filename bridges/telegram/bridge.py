#!/usr/bin/env python3
"""
Bonifade Technologies Swarm — Telegram Bot Bridge for Buzz Hive Mind Relay.
Enables bidirectional communication between Telegram and Buzz channels/agents.
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, Optional

import httpx
import websockets

# Import Nostr utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../agents")))
from nostr_util import (
    KIND_AUTH,
    KIND_STREAM_MESSAGE,
    KIND_TEXT_NOTE,
    create_auth_event,
    create_event,
    generate_keypair,
    get_pubkey_from_privkey,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Telegram-Bridge] %(message)s",
)
logger = logging.getLogger("telegram_bridge")

TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "true").lower() in ["true", "1", "yes"]
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_GROUP_CHAT_ID = os.getenv("TELEGRAM_GROUP_CHAT_ID", "").strip()
CEO_TELEGRAM_CHAT_ID = os.getenv("CEO_TELEGRAM_CHAT_ID", "").strip()
RELAY_URL = os.getenv("BUZZ_RELAY_URL", "ws://relay:8080")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
if not os.path.exists(DATA_DIR) and os.path.exists("data"):
    DATA_DIR = "data"


class TelegramBridge:
    def __init__(self):
        self.privkey, self.pubkey = self._load_or_create_keys()
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.last_update_id = 0
        self.http_client = httpx.AsyncClient(timeout=30.0)

    def _load_or_create_keys(self):
        key_file = os.path.join(DATA_DIR, "telegram_bridge_keys.json")
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(key_file):
            try:
                with open(key_file, "r") as f:
                    data = json.load(f)
                    return data["privkey"], data["pubkey"]
            except Exception:
                pass
        priv, pub = generate_keypair()
        with open(key_file, "w") as f:
            json.dump({"privkey": priv, "pubkey": pub}, f, indent=2)
        return priv, pub

    async def send_telegram_message(self, chat_id: str, text: str, reply_to_message_id: Optional[int] = None):
        if not TELEGRAM_BOT_TOKEN or not chat_id:
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        try:
            resp = await self.http_client.post(url, json=payload)
            if resp.status_code != 200:
                # Try fallback without markdown if parsing failed
                payload.pop("parse_mode", None)
                await self.http_client.post(url, json=payload)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    async def handle_telegram_update(self, update: Dict[str, Any]):
        msg = update.get("message") or update.get("channel_post")
        if not msg or "text" not in msg:
            return

        chat = msg.get("chat", {})
        chat_id = str(chat.get("id"))
        sender = msg.get("from", {}).get("first_name", "Telegram User")
        text = msg.get("text", "").strip()
        msg_id = msg.get("message_id")

        logger.info(f"Received Telegram message from {sender} ({chat_id}): '{text[:50]}'")

        # Handle built-in Telegram commands
        if text == "/start" or text == "/help":
            help_text = (
                "🐝 *Bonifade Technologies — Buzz Swarm Bot*\n\n"
                "You are connected to the autonomous AI company swarm.\n\n"
                "• Ask any question or give instructions directly.\n"
                "• Tag a department agent to direct your request:\n"
                "  `@ceo` — Strategy & Orchestration\n"
                "  `@cto` — System Architecture & Standards\n"
                "  `@fullstack-dev` — Code & Engineering\n"
                "  `@qa-tester` — Testing & Validation\n"
                "  `@devops-agent` — Deployments & Servers\n"
                "  `@marketer-growth` — Campaigns & Outbound\n"
                "  `@billing-officer` — Quotes & Invoices\n"
                "  `@legal-officer` — Contracts & NDAs\n"
                "  `@support-agent` — Client Success\n"
                "  `@site-monitor` — Uptime & System Health\n\n"
                "All interactions are logged to the cryptographic Buzz Relay audit trail."
            )
            await self.send_telegram_message(chat_id, help_text, reply_to_message_id=msg_id)
            return

        # Bridge into Buzz Relay as a signed Kind 9 Stream message
        tags = [
            ["channel", "telegram"],
            ["telegram_chat_id", chat_id],
            ["telegram_msg_id", str(msg_id)],
            ["author_name", sender],
        ]
        event = create_event(
            priv_hex=self.privkey,
            kind=KIND_STREAM_MESSAGE,
            content=f"[Telegram from {sender}]: {text}",
            tags=tags,
        )

        if self.ws:
            try:
                await self.ws.send(json.dumps(["EVENT", event]))
                logger.info(f"Bridged Telegram message into Buzz Relay as event {event['id'][:8]}...")
            except Exception as e:
                logger.error(f"Failed to post Telegram event to Buzz relay: {e}")

    async def telegram_polling_loop(self):
        """Long polls the Telegram Bot API for incoming updates."""
        if not TELEGRAM_BOT_TOKEN:
            logger.info("TELEGRAM_BOT_TOKEN is not set. Telegram polling loop disabled.")
            return

        logger.info("Starting Telegram Bot API polling loop...")
        while True:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
                params = {"offset": self.last_update_id + 1, "timeout": 20}
                resp = await self.http_client.get(url, params=params, timeout=30.0)
                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get("result", []):
                        self.last_update_id = update["update_id"]
                        asyncio.create_task(self.handle_telegram_update(update))
                elif resp.status_code == 401:
                    logger.error("Invalid TELEGRAM_BOT_TOKEN. Please check your token with @BotFather.")
                    await asyncio.sleep(60)
                else:
                    logger.warning(f"Telegram getUpdates returned status {resp.status_code}")
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Telegram polling error: {e}")
                await asyncio.sleep(5)

    async def buzz_relay_listener(self):
        """Listens for Buzz responses and forwards them to Telegram."""
        while True:
            try:
                logger.info(f"Connecting to Buzz Relay at {RELAY_URL}...")
                async with websockets.connect(RELAY_URL, max_size=10 * 1024 * 1024) as ws:
                    self.ws = ws
                    logger.info("Telegram Bridge connected to Buzz Relay.")

                    # Subscribe to stream messages
                    sub_id = "tg-bridge-sub"
                    await ws.send(json.dumps(["REQ", sub_id, {"kinds": [KIND_STREAM_MESSAGE, KIND_TEXT_NOTE]}]))

                    async for message in ws:
                        try:
                            msg_json = json.loads(message)
                            msg_type = msg_json[0]

                            if msg_type == "AUTH":
                                challenge = msg_json[1]
                                auth_event = create_auth_event(self.privkey, challenge, RELAY_URL)
                                await ws.send(json.dumps(["AUTH", auth_event]))

                            elif msg_type == "EVENT":
                                event = msg_json[2]
                                pubkey = event.get("pubkey")
                                if pubkey == self.pubkey:
                                    continue  # Skip our own bridged messages

                                content = event.get("content", "")
                                tags = {t[0]: t[1] for t in event.get("tags", []) if len(t) >= 2}

                                tg_chat_id = tags.get("telegram_chat_id")
                                tg_msg_id = tags.get("telegram_msg_id")

                                # If it was a reply to a telegram thread or designated for telegram group
                                target_chat = tg_chat_id or TELEGRAM_GROUP_CHAT_ID or CEO_TELEGRAM_CHAT_ID
                                if target_chat and content:
                                    reply_id = int(tg_msg_id) if tg_msg_id and tg_msg_id.isdigit() else None
                                    await self.send_telegram_message(target_chat, content, reply_to_message_id=reply_id)

                        except Exception as e:
                            logger.error(f"Error handling relay message in tg bridge: {e}")

            except (websockets.exceptions.ConnectionClosed, OSError) as e:
                logger.warning(f"Relay connection disconnected: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error in tg relay listener: {e}")
                await asyncio.sleep(5)

    async def run(self):
        if not TELEGRAM_ENABLED:
            logger.info("TELEGRAM_ENABLED is false. Bridge is disabled.")
            while True:
                await asyncio.sleep(3600)

        await asyncio.gather(
            self.telegram_polling_loop(),
            self.buzz_relay_listener(),
        )


if __name__ == "__main__":
    bridge = TelegramBridge()
    try:
        asyncio.run(bridge.run())
    except KeyboardInterrupt:
        logger.info("Stopping Telegram bridge...")
