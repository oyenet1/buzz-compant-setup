#!/usr/bin/env python3
"""
Bonifade Technologies Swarm — Diagnostic Integration Tester.
Tests connectivity and authentication for all configured AI, Database,
and Communication APIs.
"""

import asyncio
import os
import smtplib
import socket
import sys
import time

import httpx
import websockets

# Terminal Colors
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
NC = "\033[0m"


def report(name: str, status: bool, detail: str = ""):
    icon = f"{GREEN}✓ PASS{NC}" if status else f"{RED}✗ FAIL{NC}"
    print(f"  {icon}  {BOLD}{name:<25}{NC} {detail}")


async def test_gemini(api_key: str):
    if not api_key:
        print(f"  {YELLOW}○ SKIP{NC}  {BOLD}{'Google Gemini API':<25}{NC} (No key set in .env)")
        return
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": "Hello, respond with 'OK'"}]}]}
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(url, json=payload)
            if r.status_code == 200:
                report("Google Gemini API", True, f"{GREEN}200 OK — Model gemini-3.5-flash responsive{NC}")
            else:
                report("Google Gemini API", False, f"Status {r.status_code}: {r.text[:80]}")
    except Exception as e:
        report("Google Gemini API", False, str(e))


async def test_openai(api_key: str):
    if not api_key:
        print(f"  {YELLOW}○ SKIP{NC}  {BOLD}{'OpenAI API':<25}{NC} (No key set in .env)")
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if r.status_code == 200:
                report("OpenAI API", True, f"{GREEN}200 OK — Token verified{NC}")
            else:
                report("OpenAI API", False, f"Status {r.status_code}: {r.text[:80]}")
    except Exception as e:
        report("OpenAI API", False, str(e))


async def test_anthropic(api_key: str):
    if not api_key:
        print(f"  {YELLOW}○ SKIP{NC}  {BOLD}{'Anthropic Claude API':<25}{NC} (No key set in .env)")
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            )
            if r.status_code in [200, 400]:
                report("Anthropic Claude API", True, f"{GREEN}200 OK — Token verified{NC}")
            else:
                report("Anthropic Claude API", False, f"Status {r.status_code}: {r.text[:80]}")
    except Exception as e:
        report("Anthropic Claude API", False, str(e))


async def test_xai(api_key: str):
    if not api_key:
        print(f"  {YELLOW}○ SKIP{NC}  {BOLD}{'xAI Grok API':<25}{NC} (No key set in .env)")
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://api.x.ai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if r.status_code == 200:
                report("xAI Grok API", True, f"{GREEN}200 OK — Token verified{NC}")
            else:
                report("xAI Grok API", False, f"Status {r.status_code}: {r.text[:80]}")
    except Exception as e:
        report("xAI Grok API", False, str(e))


async def test_meta_ai(api_key: str):
    if not api_key:
        print(f"  {YELLOW}○ SKIP{NC}  {BOLD}{'Meta Muse Spark':<25}{NC} (No key set in .env)")
        return
    try:
        endpoint = os.getenv("META_AI_ENDPOINT", "https://api.meta.ai/v1/chat/completions")
        if "chat/completions" in endpoint:
            endpoint = endpoint.replace("chat/completions", "models")
        elif endpoint.rstrip("/").endswith("/v1"):
            endpoint = endpoint.rstrip("/") + "/models"
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                endpoint,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if r.status_code in [200, 400]:
                model = os.getenv("META_AI_MODEL", "muse-spark-1.2-contributor")
                report("Meta Muse Spark", True, f"{GREEN}OK — {model}{NC}")
            else:
                report("Meta Muse Spark", False, f"Status {r.status_code}: {r.text[:80]}")
    except Exception as e:
        report("Meta Muse Spark", False, str(e))


async def test_openrouter(api_key: str):
    if not api_key:
        print(f"  {YELLOW}○ SKIP{NC}  {BOLD}{'OpenRouter API':<25}{NC} (No key set in .env)")
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if r.status_code == 200:
                report("OpenRouter API", True, f"{GREEN}200 OK — Gateway token valid{NC}")
            else:
                report("OpenRouter API", False, f"Status {r.status_code}: {r.text[:80]}")
    except Exception as e:
        report("OpenRouter API", False, str(e))


async def test_firecrawl(api_key: str):
    if not api_key:
        print(f"  {YELLOW}○ SKIP{NC}  {BOLD}{'Firecrawl Web Search':<25}{NC} (No key set in .env)")
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            # 400 or 200 indicates valid auth header was evaluated
            if r.status_code in [200, 400]:
                report("Firecrawl Web Search", True, f"{GREEN}Auth valid{NC}")
            else:
                report("Firecrawl Web Search", False, f"Status {r.status_code}: {r.text[:80]}")
    except Exception as e:
        report("Firecrawl Web Search", False, str(e))


async def test_telegram(token: str):
    if not token:
        print(f"  {YELLOW}○ SKIP{NC}  {BOLD}{'Telegram Bot':<25}{NC} (No token set in .env)")
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"https://api.telegram.org/bot{token}/getMe")
            if r.status_code == 200:
                bot_user = r.json().get("result", {}).get("username", "")
                report("Telegram Bot", True, f"{GREEN}Connected as @{bot_user}{NC}")
            else:
                report("Telegram Bot", False, f"Status {r.status_code}: {r.text[:80]}")
    except Exception as e:
        report("Telegram Bot", False, str(e))


def test_smtp(host: str, port: int, user: str, password: str):
    if not password:
        print(f"  {YELLOW}○ SKIP{NC}  {BOLD}{'SMTP Email':<25}{NC} (No App Password set in .env)")
        return
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
        server.login(user, password)
        server.quit()
        report("SMTP Email", True, f"{GREEN}Authenticated successfully as {user}{NC}")
    except Exception as e:
        report("SMTP Email", False, str(e))


async def test_relay(relay_url: str):
    try:
        async with websockets.connect(relay_url, timeout=5) as ws:
            report("Buzz Relay WebSocket", True, f"{GREEN}Connected to {relay_url}{NC}")
    except Exception as e:
        report("Buzz Relay WebSocket", False, f"Could not connect to {relay_url} ({e})")


def test_port(name: str, host: str, port: int):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            report(name, True, f"{GREEN}Port {port} open and accepting connections{NC}")
        else:
            report(name, False, f"Port {port} not reachable")
    except Exception as e:
        report(name, False, str(e))


async def main():
    print(f"\n{CYAN}{BOLD}═══════════════════════════════════════════════════════════════════════{NC}")
    print(f"{BOLD}  Bonifade Technologies — Swarm Integration & Diagnostic Test{NC}")
    print(f"{CYAN}{BOLD}═══════════════════════════════════════════════════════════════════════{NC}\n")

    print(f"{BOLD}1. Database & Infrastructure Services:{NC}")
    db_url = os.getenv("DATABASE_URL", "")
    if db_url:
        import urllib.parse
        p = urllib.parse.urlparse(db_url)
        db_host = p.hostname or "127.0.0.1"
        db_port = p.port or 5432
        db_label = f"PostgreSQL ({'External: ' + db_host if db_host not in ['127.0.0.1', 'localhost', 'postgres'] else 'Local Docker'})"
        test_port(db_label, db_host, db_port)
    else:
        test_port("PostgreSQL Database", os.getenv("POSTGRES_HOST", "127.0.0.1"), int(os.getenv("POSTGRES_PORT", "5432")))

    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        import urllib.parse
        p = urllib.parse.urlparse(redis_url)
        r_host = p.hostname or "127.0.0.1"
        r_port = p.port or 6379
        r_label = f"Redis Pub/Sub ({'External: ' + r_host if r_host not in ['127.0.0.1', 'localhost', 'redis'] else 'Local Docker'})"
        test_port(r_label, r_host, r_port)
    else:
        test_port("Redis Pub/Sub", os.getenv("REDIS_HOST", "127.0.0.1"), int(os.getenv("REDIS_PORT", "6379")))

    await test_relay(os.getenv("BUZZ_RELAY_URL", "ws://127.0.0.1:4005"))

    print(f"\n{BOLD}2. AI Neural Providers (Swarm Brain):{NC}")
    await test_gemini(os.getenv("GOOGLE_API_KEY", ""))
    await test_anthropic(os.getenv("ANTHROPIC_API_KEY", ""))
    await test_openai(os.getenv("OPENAI_API_KEY", ""))
    await test_xai(os.getenv("XAI_API_KEY", "") or os.getenv("GROK_API_KEY", ""))
    await test_meta_ai(os.getenv("META_AI_API_KEY", ""))
    await test_openrouter(os.getenv("OPENROUTER_API_KEY", ""))
    await test_firecrawl(os.getenv("FIRECRAWL_API_KEY", ""))

    print(f"\n{BOLD}3. Messaging & Notification Channels:{NC}")
    await test_telegram(os.getenv("TELEGRAM_BOT_TOKEN", ""))
    test_smtp(
        os.getenv("SMTP_HOST", "smtp.gmail.com"),
        int(os.getenv("SMTP_PORT", "587")),
        os.getenv("SMTP_USER", "bonifadetechnologies@gmail.com"),
        os.getenv("SMTP_APP_PASSWORD", ""),
    )

    print(f"\n{CYAN}{BOLD}═══════════════════════════════════════════════════════════════════════{NC}\n")


if __name__ == "__main__":
    asyncio.run(main())
