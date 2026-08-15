#!/usr/bin/env python3
"""
Bonifade Technologies Swarm — SMTP & IMAP Email Bridge for Buzz Relay.
Handles:
1. Outbound transactional emails with anti-spam rate limits.
2. Inbound IMAP checking for Gmail and custom mailboxes: reads unread emails,
   parses sender/subject/body, bridges into Buzz #support / #leads channels,
   and triggers instant Telegram/WhatsApp notifications to the CEO & team.
"""

import asyncio
from datetime import datetime
from email.header import decode_header, make_header
import email.message
import email.utils
import imaplib
import json
import logging
import os
import smtplib
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    import websockets
except ImportError:
    websockets = None

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../agents")))
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
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

SMTP_ENABLED = os.getenv("SMTP_ENABLED", "true").lower() in ["true", "1", "yes"]
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "bonifadetechnologies@gmail.com")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Bonifade Technologies Swarm")

EMAIL_DAILY_LIMIT = int(os.getenv("EMAIL_DAILY_LIMIT", "500"))
EMAIL_HOURLY_LIMIT = int(os.getenv("EMAIL_HOURLY_LIMIT", "200"))
EMAIL_SEND_INTERVAL_SECONDS = int(os.getenv("EMAIL_SEND_INTERVAL_SECONDS", "20"))

IMAP_ENABLED = os.getenv("IMAP_ENABLED", "true").lower() in ["true", "1", "yes"]
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER", SMTP_USER)
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", SMTP_APP_PASSWORD)

RELAY_URL = os.getenv("BUZZ_RELAY_URL", "ws://relay:8080")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Bonifade Technologies")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
if not os.path.exists(DATA_DIR) and os.path.exists("data"):
    DATA_DIR = "data"


def decode_mime_header(header_value: Optional[str]) -> str:
    """Decodes MIME encoded-words header into clean Unicode text."""
    if not header_value:
        return ""
    try:
        decoded = decode_header(header_value)
        return str(make_header(decoded))
    except Exception:
        return str(header_value)


class EmailBridge:
    def __init__(self):
        self.privkey, self.pubkey = self._load_or_create_keys()
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.daily_sent = 0
        self.hourly_sent = 0
        self.last_day = datetime.now().day
        self.last_hour = datetime.now().hour
        self.last_send_time = 0.0
        self.processed_msg_ids = set()

    def _load_or_create_keys(self):
        key_file = os.path.join(DATA_DIR, "smtp_bridge_keys.json")
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

    def _check_rate_limits(self) -> bool:
        now = datetime.now()
        if now.day != self.last_day:
            self.daily_sent = 0
            self.last_day = now.day
        if now.hour != self.last_hour:
            self.hourly_sent = 0
            self.last_hour = now.hour

        if self.daily_sent >= EMAIL_DAILY_LIMIT:
            logger.warning(f"Daily email limit ({EMAIL_DAILY_LIMIT}) reached. Throttling outbound.")
            return False
        if self.hourly_sent >= EMAIL_HOURLY_LIMIT:
            logger.warning(f"Hourly email limit ({EMAIL_HOURLY_LIMIT}) reached. Throttling outbound.")
            return False
        return True

    def send_email_sync(self, to_email: str, subject: str, body_text: str, html_body: Optional[str] = None) -> bool:
        if not SMTP_APP_PASSWORD:
            logger.warning("SMTP_APP_PASSWORD not set. Outbound email skipped.")
            return False

        if not self._check_rate_limits():
            return False

        elapsed = time.time() - self.last_send_time
        if elapsed < EMAIL_SEND_INTERVAL_SECONDS:
            time.sleep(EMAIL_SEND_INTERVAL_SECONDS - elapsed)

        try:
            msg = email.message.EmailMessage()
            msg["Subject"] = subject
            msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
            msg["To"] = to_email
            msg["Date"] = email.utils.formatdate(localtime=True)
            msg.set_content(body_text)

            if html_body:
                msg.add_alternative(html_body, subtype="html")

            if SMTP_PORT == 465:
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                    server.login(SMTP_USER, SMTP_APP_PASSWORD)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_APP_PASSWORD)
                    server.send_message(msg)

            self.daily_sent += 1
            self.hourly_sent += 1
            self.last_send_time = time.time()
            logger.info(f"✓ Sent email to {to_email} with subject '{subject}' (Sent today: {self.daily_sent}/{EMAIL_DAILY_LIMIT})")
            return True
        except Exception as e:
            logger.error(f"Error sending SMTP email to {to_email}: {e}")
            return False

    def fetch_unread_emails_sync(self) -> List[Dict[str, Any]]:
        """Connects to IMAP (Gmail or custom server) and fetches unread messages."""
        if not IMAP_PASSWORD:
            return []

        results = []
        try:
            mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=20)
            mail.login(IMAP_USER, IMAP_PASSWORD)
            mail.select("INBOX")

            # Search for unread / unseen emails
            status, messages = mail.search(None, "UNSEEN")
            if status == "OK" and messages[0]:
                for num in messages[0].split():
                    try:
                        _, data = mail.fetch(num, "(RFC822)")
                        raw_email = data[0][1]
                        msg = email.message_from_bytes(raw_email)

                        message_id = msg.get("Message-ID", str(num))
                        if message_id in self.processed_msg_ids:
                            continue
                        self.processed_msg_ids.add(message_id)

                        subject = decode_mime_header(msg.get("Subject", "(No Subject)"))
                        from_addr = decode_mime_header(msg.get("From", "Unknown Sender"))
                        date_str = msg.get("Date", "")

                        # Extract text payload
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                ctype = part.get_content_type()
                                cdisp = str(part.get("Content-Disposition"))
                                if ctype == "text/plain" and "attachment" not in cdisp:
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        body = payload.decode(errors="ignore")
                                        break
                        else:
                            payload = msg.get_payload(decode=True)
                            if payload:
                                body = payload.decode(errors="ignore")

                        body_snippet = body.strip()[:1500] if body else "(No plain text content)"

                        results.append({
                            "message_id": message_id,
                            "from": from_addr,
                            "subject": subject,
                            "date": date_str,
                            "body": body_snippet,
                        })
                    except Exception as parse_err:
                        logger.error(f"Error parsing email message {num}: {parse_err}")

            mail.close()
            mail.logout()
        except Exception as e:
            logger.error(f"IMAP fetch error: {e}")

        return results

    async def poll_inbound_imap(self):
        """Background worker that checks IMAP every 60 seconds and publishes to Buzz."""
        if not IMAP_ENABLED or not IMAP_PASSWORD:
            logger.info("IMAP reading is idle. Set SMTP_APP_PASSWORD in .env to activate Gmail/IMAP reading.")
            while True:
                await asyncio.sleep(3600)

        logger.info(f"Starting IMAP email polling worker on {IMAP_HOST}:{IMAP_PORT} ({IMAP_USER})...")
        while True:
            try:
                unread = await asyncio.to_thread(self.fetch_unread_emails_sync)
                if unread:
                    logger.info(f"Found {len(unread)} new unread email(s) in {IMAP_USER}.")
                    for mail_item in unread:
                        from_sender = mail_item["from"]
                        subj = mail_item["subject"]
                        body = mail_item["body"]

                        content = (
                            f"📨 **Incoming Email Received**\n\n"
                            f"• **From:** `{from_sender}`\n"
                            f"• **Subject:** *{subj}*\n"
                            f"• **Date:** {mail_item['date']}\n\n"
                            f"**Message Body:**\n```\n{body}\n```\n\n"
                            f"_(Forwarded automatically to Telegram & Buzz #support by Email Bridge)_"
                        )

                        # Tag to trigger Telegram & Buzz support channel
                        tags = [
                            ["channel", "support"],
                            ["telegram_notify", "true"],
                            ["email_from", from_sender],
                            ["email_subject", subj],
                        ]

                        event = create_event(
                            priv_hex=self.privkey,
                            kind=KIND_STREAM_MESSAGE,
                            content=content,
                            tags=tags,
                        )

                        if self.ws:
                            await self.ws.send(json.dumps(["EVENT", event]))
                            logger.info(f"Published email event to Buzz: '{subj}'")

            except Exception as e:
                logger.error(f"IMAP polling loop error: {e}")

            await asyncio.sleep(60)

    async def buzz_relay_listener(self):
        """Listens for Buzz events requesting email dispatch."""
        while True:
            try:
                logger.info(f"Connecting to Buzz Relay at {RELAY_URL}...")
                async with websockets.connect(RELAY_URL, max_size=10 * 1024 * 1024) as ws:
                    self.ws = ws
                    logger.info("Email Bridge connected to Buzz Relay.")

                    await ws.send(json.dumps(["REQ", "smtp-sub-01", {"kinds": [KIND_STREAM_MESSAGE]}]))

                    async for message in ws:
                        try:
                            msg_json = json.loads(message)
                            if msg_json[0] == "AUTH":
                                auth_event = create_auth_event(self.privkey, msg_json[1], RELAY_URL)
                                await ws.send(json.dumps(["AUTH", auth_event]))
                            elif msg_json[0] == "EVENT":
                                event = msg_json[2]
                                if event.get("pubkey") == self.pubkey:
                                    continue

                                tags = {t[0]: t[1] for t in event.get("tags", []) if len(t) >= 2}
                                to_email = tags.get("send_email") or tags.get("email_to")
                                if to_email:
                                    subject = tags.get("subject", f"Update from {COMPANY_NAME}")
                                    content = event.get("content", "")
                                    await asyncio.to_thread(self.send_email_sync, to_email, subject, content)
                        except Exception as e:
                            logger.error(f"Error handling event in email bridge: {e}")

            except Exception as e:
                logger.warning(f"Email relay listener error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    async def run(self):
        if not SMTP_ENABLED and not IMAP_ENABLED:
            logger.info("Email Bridge is disabled.")
            while True:
                await asyncio.sleep(3600)

        await asyncio.gather(
            self.buzz_relay_listener(),
            self.poll_inbound_imap(),
        )


def check_inbox_cli():
    """Standalone CLI command to check and print unread emails immediately."""
    print(f"\n{CYAN}{BOLD}══ Checking Inbox for {IMAP_USER} ({IMAP_HOST}) ══════════════════════{NC}")
    bridge = EmailBridge()
    unread = bridge.fetch_unread_emails_sync()
    if not unread:
        print(f"  {GREEN}✓ No unread emails in inbox.{NC}")
    else:
        print(f"  {YELLOW}Found {len(unread)} unread email(s):{NC}\n")
        for i, m in enumerate(unread, 1):
            print(f"  {BOLD}[{i}] From:{NC}    {m['from']}")
            print(f"      {BOLD}Subject:{NC} {m['subject']}")
            print(f"      {BOLD}Date:{NC}    {m['date']}")
            print(f"      {BOLD}Preview:{NC} {m['body'][:120]}...\n")
    print(f"{CYAN}{BOLD}═════════════════════════════════════════════════════════════════════════{NC}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["check", "read", "inbox"]:
        check_inbox_cli()
    else:
        bridge = EmailBridge()
        try:
            asyncio.run(bridge.run())
        except KeyboardInterrupt:
            logger.info("Stopping Email bridge...")
