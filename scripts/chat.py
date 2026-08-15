#!/usr/bin/env python3
"""
Bonifade Technologies Swarm — Interactive Terminal Chat with Buzz AI Swarm.
Allows direct terminal dialogue with the CEO and department agents.
"""

import asyncio
import json
import os
import sys

import websockets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../agents")))
from nostr_util import (
    KIND_STREAM_MESSAGE,
    create_auth_event,
    create_event,
    generate_keypair,
    get_pubkey_from_privkey,
)

# Terminal Colors
CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
PURPLE = "\033[0;35m"
BOLD = "\033[1m"
NC = "\033[0m"

RELAY_URL = os.getenv("BUZZ_RELAY_URL", "ws://127.0.0.1:8080")


async def chat_loop():
    priv, pub = generate_keypair()

    print(f"\n{CYAN}{BOLD}═══════════════════════════════════════════════════════════════════════{NC}")
    print(f"{BOLD}  🐝 Bonifade Technologies — Interactive Swarm CLI Chat{NC}")
    print(f"{CYAN}{BOLD}═══════════════════════════════════════════════════════════════════════{NC}")
    print(f"  {YELLOW}Type your message and press Enter. Mention @ceo, @cto, @dev, @billing, etc.{NC}")
    print(f"  {YELLOW}Type 'exit' or press Ctrl+C to quit.{NC}\n")

    try:
        async with websockets.connect(RELAY_URL, timeout=5) as ws:
            # Check Auth
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
                mjson = json.loads(msg)
                if mjson[0] == "AUTH":
                    a_ev = create_auth_event(priv, mjson[1], RELAY_URL)
                    await ws.send(json.dumps(["AUTH", a_ev]))
            except asyncio.TimeoutError:
                pass

            # Subscribe to responses
            sub_id = f"cli-chat-{pub[:6]}"
            await ws.send(json.dumps(["REQ", sub_id, {"kinds": [KIND_STREAM_MESSAGE], "limit": 0}]))

            async def listen_for_replies():
                async for incoming in ws:
                    try:
                        data = json.loads(incoming)
                        if data[0] == "EVENT":
                            event = data[2]
                            if event.get("pubkey") != pub:
                                content = event.get("content", "")
                                print(f"\n{GREEN}{BOLD}🐝 Swarm Response:{NC}\n{content}\n")
                                print(f"{BOLD}> {NC}", end="", flush=True)
                    except Exception:
                        pass

            asyncio.create_task(listen_for_replies())

            while True:
                user_msg = await asyncio.to_thread(input, f"{BOLD}> {NC}")
                user_msg = user_msg.strip()
                if not user_msg:
                    continue
                if user_msg.lower() in ["exit", "quit", "q"]:
                    break

                ev = create_event(
                    priv_hex=priv,
                    kind=KIND_STREAM_MESSAGE,
                    content=user_msg,
                    tags=[["channel", "general"]],
                )
                await ws.send(json.dumps(["EVENT", ev]))
                # Wait briefly for reply
                await asyncio.sleep(0.5)

    except Exception as e:
        print(f"\n{YELLOW}Could not connect to Buzz Relay ({e}). Ensure stack is running with ./manage.sh start{NC}\n")


if __name__ == "__main__":
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        print("\nGoodbye.")
