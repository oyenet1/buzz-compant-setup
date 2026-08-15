#!/usr/bin/env python3
"""
Bonifade Technologies Swarm — Company Seed & Initialization Script for Buzz.
Creates standard company channels, registers department profiles, and seeds baseline goals.
"""

import asyncio
import json
import logging
import os
import sys
import time

import websockets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../agents")))
from nostr_util import (
    KIND_METADATA,
    KIND_STREAM_MESSAGE,
    KIND_TEXT_NOTE,
    create_auth_event,
    create_event,
    generate_keypair,
    get_pubkey_from_privkey,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")

RELAY_URL = os.getenv("BUZZ_RELAY_URL", "ws://127.0.0.1:8080")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Bonifade Technologies")
DATA_DIR = os.getenv("DATA_DIR", "data")

CHANNELS = [
    {"id": "general", "name": "general", "about": "Company-wide announcements, discussions, and updates"},
    {"id": "executive", "name": "executive", "about": "CEO briefings, strategic decisions, and department escalations"},
    {"id": "engineering", "name": "engineering", "about": "Technical architecture, fullstack code, reviews, and CI/CD"},
    {"id": "marketing", "name": "marketing", "about": "Market intelligence, SEO, copy, campaigns, and growth"},
    {"id": "leads", "name": "leads", "about": "Qualified client leads pipeline, consultation requests & CRM"},
    {"id": "billing", "name": "billing", "about": "Quotations, milestone invoices, payment confirmations (Moniepoint: 7065720177)"},
    {"id": "support", "name": "support", "about": "Customer tickets, onboarding requests, and client success"},
    {"id": "incident-room", "name": "incident-room", "about": "Uptime monitoring, server health, and error alerts"},
]

BASELINE_GOALS = [
    {"title": "First paying client", "target": "1 signed contract", "owner": "CEO", "deadline": "2026-09-30"},
    {"title": "Qualified leads pipeline", "target": "100 leads in leads DB", "owner": "Marketer Research", "deadline": "2026-09-30"},
    {"title": "Outreach launched", "target": "First 500-email campaign sent", "owner": "Marketer Growth", "deadline": "2026-08-31"},
    {"title": "Company website live", "target": "bonifadetechnologies.com current + lead capture", "owner": "Fullstack Dev", "deadline": "2026-08-15"},
    {"title": "Proposal & contract templates", "target": "MSA, SOW, NDA approved", "owner": "Legal Officer", "deadline": "2026-08-31"},
]


async def seed_buzz():
    os.makedirs(DATA_DIR, exist_ok=True)
    seed_key_file = os.path.join(DATA_DIR, "seed_keys.json")
    if os.path.exists(seed_key_file):
        with open(seed_key_file, "r") as f:
            data = json.load(f)
            priv = data["privkey"]
    else:
        priv, pub = generate_keypair()
        with open(seed_key_file, "w") as f:
            json.dump({"privkey": priv, "pubkey": pub}, f, indent=2)

    logger.info(f"Connecting to Buzz Relay at {RELAY_URL}...")
    try:
        async with websockets.connect(RELAY_URL, timeout=10) as ws:
            logger.info("Connected to Buzz Relay.")

            # Check if AUTH challenge is received
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                msg_json = json.loads(msg)
                if msg_json[0] == "AUTH":
                    auth_ev = create_auth_event(priv, msg_json[1], RELAY_URL)
                    await ws.send(json.dumps(["AUTH", auth_ev]))
                    logger.info("Sent NIP-42 Auth event.")
            except asyncio.TimeoutError:
                pass

            # 1. Create Channel Announcements
            for ch in CHANNELS:
                content = (
                    f"🐝 **#{ch['name']} Channel Initialized**\n\n"
                    f"{ch['about']}\n\n"
                    f"_Operated by the {COMPANY_NAME} Autonomous AI Swarm._"
                )
                tags = [
                    ["channel", ch["id"]],
                    ["name", ch["name"]],
                ]
                ev = create_event(priv, KIND_STREAM_MESSAGE, content, tags)
                await ws.send(json.dumps(["EVENT", ev]))
                logger.info(f"✓ Seeded channel: #{ch['name']}")
                await asyncio.sleep(0.1)

            # 2. Post Baseline Goals to #executive
            goals_text = f"🎯 **{COMPANY_NAME} — Baseline Strategic Goals**\n\n"
            for g in BASELINE_GOALS:
                goals_text += f"• **{g['title']}** — Target: `{g['target']}` | Owner: `{g['owner']}` | Deadline: `{g['deadline']}`\n"

            goals_ev = create_event(
                priv,
                KIND_STREAM_MESSAGE,
                goals_text,
                tags=[["channel", "executive"]],
            )
            await ws.send(json.dumps(["EVENT", goals_ev]))
            logger.info("✓ Seeded baseline company goals into #executive")

            logger.info("🎉 Company seed completed successfully!")
    except Exception as e:
        logger.warning(f"Could not connect to Buzz Relay ({e}). (Relay will be initialized automatically when started).")


if __name__ == "__main__":
    asyncio.run(seed_buzz())
