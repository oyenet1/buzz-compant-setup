#!/usr/bin/env python3
"""
Bonifade Technologies Swarm — WhatsApp Cloud API & Webhook Bridge for Buzz Relay.
Receives inbound WhatsApp webhooks from Meta and forwards outbound agent replies.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query, Request, Response
import httpx
import uvicorn
import websockets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../agents")))
from nostr_util import (
    KIND_STREAM_MESSAGE,
    create_auth_event,
    create_event,
    generate_keypair,
    get_pubkey_from_privkey,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [WhatsApp-Bridge] %(message)s",
)
logger = logging.getLogger("whatsapp_bridge")

WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "false").lower() in ["true", "1", "yes"]
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "").strip()
CEO_WHATSAPP_NUMBER = os.getenv("CEO_WHATSAPP_NUMBER", "").strip()
WHATSAPP_GROUP_ID = os.getenv("WHATSAPP_GROUP_ID", "").strip()
RELAY_URL = os.getenv("BUZZ_RELAY_URL", "ws://relay:8080")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
if not os.path.exists(DATA_DIR) and os.path.exists("data"):
    DATA_DIR = "data"

app = FastAPI(title="Buzz WhatsApp Bridge")


class WhatsAppClient:
    def __init__(self):
        self.privkey, self.pubkey = self._load_or_create_keys()
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.http_client = httpx.AsyncClient(timeout=30.0)

    def _load_or_create_keys(self):
        key_file = os.path.join(DATA_DIR, "whatsapp_bridge_keys.json")
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

    async def send_whatsapp_message(self, to_phone: str, message_text: str):
        if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
            logger.warning("WhatsApp API credentials missing. Cannot send outbound message.")
            return False

        is_group = "@g.us" in to_phone
        clean_target = to_phone if is_group else "".join(filter(str.isdigit, to_phone))
        url = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "group" if is_group else "individual",
            "to": clean_target,
            "type": "text",
            "text": {"preview_url": False, "body": message_text},
        }

        try:
            resp = await self.http_client.post(url, headers=headers, json=payload)
            if resp.status_code in [200, 201]:
                logger.info(f"WhatsApp message sent successfully to {clean_phone}")
                return True
            else:
                logger.error(f"WhatsApp API send failure ({resp.status_code}): {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Error calling WhatsApp API: {e}")
            return False

    async def send_whatsapp_template(
        self,
        to_phone: str,
        template_name: str = "hello_world",
        language_code: str = "en_US",
        components: Optional[list] = None,
    ):
        """Sends an approved Meta WhatsApp template message for initiating conversations."""
        if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
            logger.warning("WhatsApp API credentials missing.")
            return False

        clean_phone = "".join(filter(str.isdigit, to_phone))
        url = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or [],
            },
        }

        try:
            resp = await self.http_client.post(url, headers=headers, json=payload)
            if resp.status_code in [200, 201]:
                logger.info(f"WhatsApp template '{template_name}' sent to {clean_phone}")
                return True
            else:
                logger.error(f"WhatsApp template send failure ({resp.status_code}): {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Error calling WhatsApp template API: {e}")
            return False


wa_client = WhatsAppClient()


@app.get("/webhook/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta Webhook Verification Challenge."""
    if hub_mode == "subscribe" and (not WHATSAPP_WEBHOOK_VERIFY_TOKEN or hub_token == WHATSAPP_WEBHOOK_VERIFY_TOKEN):
        logger.info("WhatsApp webhook verified successfully by Meta challenge.")
        return Response(content=hub_challenge, media_type="text/plain")
    logger.warning("WhatsApp webhook challenge verification failed.")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@app.post("/webhook/whatsapp")
async def receive_webhook(request: Request):
    """Handles incoming WhatsApp messages from Meta."""
    try:
        body = await request.json()
        entries = body.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts = {c.get("wa_id"): c.get("profile", {}).get("name") for c in value.get("contacts", [])}

                for msg in messages:
                    if msg.get("type") == "text":
                        sender_id = msg.get("from")
                        sender_name = contacts.get(sender_id, "WhatsApp User")
                        text_body = msg.get("text", {}).get("body", "")

                        logger.info(f"Received WhatsApp message from {sender_name} ({sender_id}): '{text_body}'")

                        # Bridge to Buzz Relay
                        event = create_event(
                            priv_hex=wa_client.privkey,
                            kind=KIND_STREAM_MESSAGE,
                            content=f"[WhatsApp from {sender_name} (+{sender_id})]: {text_body}",
                            tags=[
                                ["channel", "whatsapp"],
                                ["whatsapp_phone", sender_id],
                                ["author_name", sender_name],
                            ],
                        )

                        if wa_client.ws:
                            await wa_client.ws.send(json.dumps(["EVENT", event]))
                            logger.info(f"Forwarded WhatsApp message to Buzz Relay as event {event['id'][:8]}...")

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error handling WhatsApp webhook: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "buzz-bridge-whatsapp"}


async def relay_outbound_listener():
    """Listens for Buzz events destined for WhatsApp recipients."""
    while True:
        try:
            logger.info(f"Connecting to Buzz Relay at {RELAY_URL}...")
            async with websockets.connect(RELAY_URL, max_size=10 * 1024 * 1024) as ws:
                wa_client.ws = ws
                logger.info("WhatsApp Bridge connected to Buzz Relay.")

                await ws.send(json.dumps(["REQ", "wa-sub-01", {"kinds": [KIND_STREAM_MESSAGE]}]))

                async for message in ws:
                    try:
                        msg_json = json.loads(message)
                        if msg_json[0] == "AUTH":
                            auth_event = create_auth_event(wa_client.privkey, msg_json[1], RELAY_URL)
                            await ws.send(json.dumps(["AUTH", auth_event]))
                        elif msg_json[0] == "EVENT":
                            event = msg_json[2]
                            if event.get("pubkey") == wa_client.pubkey:
                                continue

                            tags = {t[0]: t[1] for t in event.get("tags", []) if len(t) >= 2}
                            phone = tags.get("whatsapp_phone")
                            is_notify = tags.get("whatsapp_notify") == "true" or tags.get("telegram_notify") == "true"

                            target = phone or (WHATSAPP_GROUP_ID if (is_notify or tags.get("channel") in ["support", "leads", "executive"]) else None)
                            if target:
                                content = event.get("content", "")
                                await wa_client.send_whatsapp_message(target, content)
                    except Exception as e:
                        logger.error(f"Error parsing event in wa relay listener: {e}")

        except Exception as e:
            logger.warning(f"WhatsApp relay listener error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(relay_outbound_listener())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8085)
