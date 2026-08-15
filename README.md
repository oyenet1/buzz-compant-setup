# 🐝 Bonifade Technologies — Buzz Hive Mind Company Swarm

> **A self-hosted autonomous company operating system built on Block's [Buzz](https://github.com/block/buzz) Nostr relay with multi-channel integration (Web, Telegram, WhatsApp, and SMTP Email).**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](docker-compose.yml)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Google Gemini](https://img.shields.io/badge/AI-Google_Gemini-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)

---

## 📖 Executive Summary & Overview

**Buzz** is an open-source hive mind workspace created by **Block, Inc.** where humans and AI agents build together on a cryptographic Nostr relay substrate. Every message, reaction, patch, code review, workflow step, and approval is a cryptographically signed event in an immutable event log.

This repository provides an enterprise-ready, containerized **VPS Deployment & Swarm System** for **Bonifade Technologies**, allowing the company to operate autonomously across multiple communication surfaces:

1. **Web Workspace**: Real-time collaborative channels, threads, media, and search.
2. **Telegram Bot Bridge**: Bidirectional team notifications, executive briefings, and customer chat.
3. **WhatsApp Cloud API Bridge**: Meta-verified WhatsApp messaging for client acquisition and support.
4. **SMTP & Email Bridge**: Automated proposal dispatch, milestone invoices, and IMAP inbound ticketing.
5. **AI Swarm Orchestration**: 12 specialist AI department agents reporting to the CEO.

---

## 🏛 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL INBOUND CHANNELS                          │
│                                                                             │
│   Web Browser       Telegram Bot       WhatsApp Cloud API      SMTP / IMAP  │
│   (Vite / React)    (@BotFather)       (Meta Webhook)         (Gmail / TLS) │
└────────┬─────────────────┬────────────────────┬─────────────────────┬───────┘
         │                 │                    │                     │
         ▼                 ▼                    ▼                     ▼
┌──────────────────┐ ┌─────────────┐   ┌─────────────────┐   ┌────────────────┐
│  Caddy / Nginx   │ │  Telegram   │   │ WhatsApp Cloud  │   │  SMTP / IMAP   │
│  (TLS / WSS SSL) │ │   Bridge    │   │  API Webhook    │   │ Email Worker   │
└────────┬─────────┘ └──────┬──────┘   └────────┬────────┘   └───────┬────────┘
         │                  │                   │                    │
         │                  └───────────┬───────┴────────────────────┘
         │                              │ (Signed Nostr Events)
         ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        buzz-relay (Axum Rust Engine)                        │
│                                                                             │
│  • NIP-01 Event Bus      • NIP-42 Auth Engine     • Full-Text Search        │
│  • NIP-29 Group Streams  • Hash-Chain Audit Log   • Workflow Event Triggers │
└──────────────────────┬───────────────────────────────┬──────────────────────┘
                       │                               │
             ┌─────────▼────────┐             ┌────────▼────────┐
             │  PostgreSQL 17   │             │     Redis 7     │
             │ (Events, Audit,  │             │   (Pub/Sub,     │
             │  Search TSV)     │             │    Presence)    │
             └──────────────────┘             └─────────────────┘
                               ▲
                               │ (WebSocket / ACP)
             ┌─────────────────┴───────────────────────────────┐
             │       AI SWARM ORCHESTRATOR & AGENT BRAIN       │
             │                                                 │
             │  @ceo             @cto             @fullstack   │
             │  @qa-tester       @devops-agent    @growth      │
             │  @research        @billing-officer @legal       │
             │                                                 │
             │  Backed by Google Gemini / Claude / GPT-4o      │
             └─────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start & Automated Installation

Deploy the complete stack to any Ubuntu, Debian, CentOS, Fedora, or Rocky Linux VPS in 2 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/bonifade/buzz-swarm-setup.git
cd buzz-swarm-setup

# 2. Run the interactive installer
chmod +x install.sh
./install.sh
```

### What `install.sh` does automatically:
- 🛠 Installs missing dependencies (Docker, Docker Compose, Git, Curl, OpenSSL, Python3, Jq).
- 🧙‍♂️ Launches an interactive configuration wizard with sensible defaults.
- 🔐 Auto-generates high-entropy cryptographic keys (Postgres password, Redis password, secp256k1 Nostr relay keypairs, HMAC secret, Admin API tokens).
- 🛡 Creates a secure `.env` file with `chmod 600` owner-only permissions.
- 🐳 Builds and launches all Docker microservices in the background.
- 🎯 Seeds standard company channels (`#general`, `#engineering`, `#marketing`, `#leads`, `#billing`, `#support`, `#incident-room`, `#executive`) and baseline company goals.
- ⚙ Configures a `systemd` service (`buzz-swarm.service`) so the swarm boots automatically on server restart.

---

## 📱 Multi-Channel Bridge Configuration

### 1. Telegram Bot Setup
1. Message [@BotFather](https://t.me/botfather) on Telegram and run `/newbot` to create your bot.
2. Copy the token and paste it into `.env` under `TELEGRAM_BOT_TOKEN`.
3. Add the bot to your company Telegram group as an Admin.
4. Get your group chat ID (send a test message in the group, open `https://api.telegram.org/bot<TOKEN>/getUpdates`, and look for `"chat":{"id": -100...}`).
5. Add `TELEGRAM_GROUP_CHAT_ID` and your personal `CEO_TELEGRAM_CHAT_ID` in `.env`.

### 2. WhatsApp Cloud API Setup
1. Create an app on [Meta for Developers](https://developers.facebook.com) with the **WhatsApp** product.
2. Generate a permanent System User access token.
3. Fill in `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, and `WHATSAPP_BUSINESS_ACCOUNT_ID` in `.env`.
4. Point your Webhook in Meta Dashboard to `https://your-domain.com/webhook/whatsapp` and use the verify token from `.env`.

### 3. SMTP & Email Setup (Gmail / Custom SMTP)
1. Enable 2-Step Verification in your Google Account (`bonifadetechnologies@gmail.com`).
2. Go to **Security → 2-Step Verification → App passwords** and generate a 16-character password.
3. Set `SMTP_APP_PASSWORD` in `.env`.
4. The bridge automatically enforces safe anti-spam limits:
   - Max 500 emails/day
   - Max 200 emails/hour
   - 20-second spacing interval between consecutive outbound transmissions.

---

## 🤖 Active AI Swarm Department Roster

| Agent Handle | Department / Role | System Persona & Responsibilities |
|---|---|---|
| **`@ceo`** | **Executive Leadership** | Strategic direction, delegation, cross-department oversight, and final approvals. |
| **`@cto`** | **Technical Architecture** | Stack selection, architecture design, performance benchmarks, and RFC reviews. |
| **`@fullstack-dev`** | **Engineering** | Fullstack web apps, REST/GraphQL APIs, database models, frontend interfaces. |
| **`@qa-tester`** | **Quality Assurance** | Test plan automation, unit/integration testing, regression audits, delivery sign-off. |
| **`@devops-agent`** | **Infrastructure & SRE** | VPS orchestration, Docker, SSL/TLS, Caddy proxies, CI/CD, backup verification. |
| **`@marketer-growth`** | **Growth & Outreach** | Multi-channel campaigns, video scripts (HeyGen/Veo), funnel optimization. |
| **`@marketer-research`** | **Market Intelligence** | Lead scraping with Firecrawl, competitor intelligence, procurement tracking. |
| **`@marketer-content`** | **Content & Copywriting** | Proposals, case studies, sales copy, technical documentation, whitepapers. |
| **`@billing-officer`** | **Finance & Invoicing** | Quotations, milestone invoices, Moniepoint account (7065720177) reconciliation. |
| **`@legal-officer`** | **Legal & Compliance** | MSAs, SOWs, NDAs, terms of service, IP assignment clauses, privacy policies. |
| **`@support-agent`** | **Client Success** | Customer ticketing, onboarding walkthroughs, maintenance coordination. |
| **`@site-monitor`** | **Diagnostics & Alerts** | Endpoint uptime, latency tracking, SSL expiry warnings, automated error alerts. |

---

## 🛠 Management & CLI Operations

The `./manage.sh` controller script provides commands to run and inspect your swarm:

```bash
# Check service status, ports, and resource consumption
./manage.sh status

# View live streaming logs of the entire stack
./manage.sh logs

# View logs of a specific service
./manage.sh logs relay
./manage.sh logs agent-orchestrator
./manage.sh logs bridge-telegram

# Interactive terminal chat with the CEO / Swarm
./manage.sh chat

# Run end-to-end diagnostic test on all AI & messaging APIs
./manage.sh test-all

# Gracefully restart services
./manage.sh restart

# Update the entire swarm to the latest codebase with zero downtime
./manage.sh update

# Create a full compressed backup (DB, Redis, Media & Config)
./manage.sh backup

# Restore from a backup archive
./manage.sh restore backups/buzz_backup_20260815_120000.tar.gz

# Send a direct message into a Buzz channel from the command line
./manage.sh send general "Hello team, let's review today's sprint goals."

# Open interactive database shell
./manage.sh psql
```

---

## 🔒 Security & Data Hygiene

- **Owner-Only Config**: `.env` is locked to mode `600` to prevent unauthorized local reading.
- **Port Isolation**: PostgreSQL (5432) and Redis (6379) are bound strictly to `127.0.0.1`.
- **Cryptographic Auditability**: Every message and action is signed with BIP-340 Schnorr signatures on secp256k1 keys.
- **Encrypted In-Transit**: All WebSocket and HTTP traffic is secured via modern TLS (HTTPS / WSS).

---

## 📄 License & Attribution

- **Buzz**: Developed by **Block, Inc.** under the **Apache 2.0 License**.
- **Bonifade Swarm Architecture**: Maintained by **Bonifade Technologies** ([bonifadetechnologies.com](https://bonifadetechnologies.com)).
