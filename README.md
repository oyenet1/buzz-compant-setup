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
5. **AI Swarm Orchestration**: 14 specialist AI marketing and operational department agents reporting to the CEO.
6. **Antigravity Skills & AI Video Engine**: Built-in SaaS demo ad generation, Maxfusion multi-model AI video production (Veo 3.1, Gemini Omni Flash, HeyGen), and direct-response psychological frameworks.

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
             │  @qa-tester       @devops-agent    @marketer-   │
             │  @billing-officer @legal-officer   head & 14    │
             │                                    specialists  │
             │  Backed by Google Gemini / Claude / GPT-4o      │
             └─────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start & Automated Installation

Deploy the complete stack to any Ubuntu, Debian, CentOS, Fedora, or Rocky Linux VPS in 2 minutes:

```bash
# 1. Clone the repository
git clone git@github.com:oyenet1/buzz-compant-setup.git
cd buzz-compant-setup

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

### Executive, Engineering & Operations Core
| Agent Handle | Department / Role | System Persona & Responsibilities |
|---|---|---|
| **`@ceo`** | **Fade_networker** | Strategic direction, delegation, cross-department oversight, and final approvals. |
| **`@cto`** | **Technical Architecture** | Stack selection, architecture design, performance benchmarks, and RFC reviews. |
| **`@fullstack-dev`** | **Engineering** | Fullstack web apps, REST/GraphQL APIs, database models, frontend interfaces. |
| **`@qa-tester`** | **Quality Assurance** | Test plan automation, unit/integration testing, regression audits, delivery sign-off. |
| **`@devops-agent`** | **Infrastructure & SRE** | VPS orchestration, Docker, SSL/TLS, Caddy proxies, CI/CD, backup verification. |
| **`@billing-officer`** | **Finance & Invoicing** | Quotations, milestone invoices, Moniepoint account reconciliation. |
| **`@legal-officer`** | **Legal & Compliance** | MSAs, SOWs, NDAs, terms of service, IP assignment clauses, privacy policies. |
| **`@support-agent`** | **Client Success** | Customer ticketing, onboarding walkthroughs, maintenance coordination. |
| **`@site-monitor`** | **Diagnostics & Alerts** | Endpoint uptime, latency tracking, SSL expiry warnings, automated error alerts. |

### The 14-Specialist Marketing Swarm Hierarchy
| Badge | Agent Handle | Role Title | Core Specialization & Tools |
|---|---|---|---|
| 🖤 | **`@marketer-head`** (`@cmo`) | **Head of Marketing** | Swarm mastermind, cross-channel strategy, CAC/LTV economics, orchestrating campaigns. |
| 🟢 | **`@marketer-site-auditor`** | **Site Auditor & Analyst** | Full-funnel technical, UX, and CRO diagnostic audits scored 0–100 (`site_audit_score`). |
| 🟪 | **`@marketer-seo`** | **SEO & GEO Lead** | Search rankings, Generative Engine Optimization, standard `llms.txt` (`generate_llms_txt`). |
| 🔷 | **`@marketer-copywriter`** | **Direct-Response Copywriter** | Sales letters, VSLs, hero headlines; copy graded on 6 pillars (`grade_copy`). |
| ⚪️ | **`@marketer-creative`** | **Creative Strategist** | AI visual ads & demo videos via Maxfusion, Gemini Omni, Veo 3.1, and HeyGen. |
| 🔺 | **`@marketer-media-buyer`** | **Media Buyer** | Paid acquisition (Meta/Google/TikTok/X), ad fatigue diagnostics, decisive kill calls. |
| 🔵 | **`@marketer-email`** | **Email Marketer** | Full lifecycle sequences written in full, subject lines, send-time schedules. |
| 🟡 | **`@marketer-social`** | **Social Manager** | Organic platform-native posts that survive the algorithmic feed (X, LinkedIn, IG). |
| 🟥 | **`@marketer-launch`** | **Launch Manager** | Product Hunt, Hacker News, AppSumo, and GTM launches planned hour by hour (`product_hunt_schedule`). |
| 🟤 | **`@marketer-pricing`** | **Pricing Strategist** | Tiers, Grand Slam offers, Hormozi Value Equation math (`pricing_calculator`). |
| 🟩 | **`@marketer-competitor`** | **Competitor Analyst** | Meta Ad Library reverse-engineering, competitor angle extraction (`competitor_meta_ad_analyzer`). |
| 🟣 | **`@marketer-aso`** | **ASO Specialist** | iOS App Store & Google Play metadata, keyword density (`aso_metadata_analyzer`). |
| 🟦 | **`@marketer-data`** | **Marketing Data Analyst** | Growth dashboards, A/B test statistical math (`ab_test_calculator`), cohort retention. |
| 🔶 | **`@marketer-editor`** | **Chief Content Editor** | Anti-AI-slop firewall; cuts clichés and fluff before anything ships (`anti_slop_check`). |

---

## 🎬 SaaS Demo Video Ads Skill & Framework

The repository includes a battle-tested **Antigravity Skill** and **Playbook** for producing high-converting SaaS product demo videos and paid video ads.

* **Skill Location**: [`.agents/skills/ads-video-generation/SKILL.md`](.agents/skills/ads-video-generation/SKILL.md)
* **Dedicated Playbook**: [`marketing/playbooks/15-saas-demo-video-ads-framework.md`](marketing/playbooks/15-saas-demo-video-ads-framework.md)
* **Masterclass Video Reference**: [YouTube — High-Converting SaaS Demo Video Framework](https://www.youtube.com/watch?v=gHZNctEhCA0)

```
┌─────────────────────────┐     ┌─────────────────────────┐
│ 1. Define Your ONE      │ ──> │ 2. 90-Second Story Arc  │
│ • 1 Specific Audience   │     │ • The Hook (0-10s)      │
│ • 1 Specific Problem    │     │ • The Solution (10-25s) │
└─────────────────────────┘     │ • 2-3 Step Demo (25-75s)│
                                │ • Benefit Recap (75-90s)│
                                └────────────┬────────────┘
                                             │
┌─────────────────────────┐     ┌────────────▼────────────┐
│ 4. Crystal Clear CTA    │ <── │ 3. Show, Don't Tell     │
│ • Single Frictionless   │     │ • Human Face (+38% Conv)│
│   Next Action           │     │ • Visual Zooms & Badges │
└─────────────────────────┘     │ • Studio Audio Quality  │
                                └─────────────────────────┘
```

### The 4-Part Framework Rules:
1. **Define Your ONE (6:45–7:00)**: Focus on 1 target persona and 1 acute pain point. Avoid generic multi-audience pitches.
2. **The 90-Second Story Arc (7:00–8:45)**: Keep the video between **60 and 120 seconds**.
   - *Hook*: Show the raw pain point immediately (messy spreadsheet, broken build, chaotic dashboard). Never start with a logo splash.
   - *Solution*: Position the product as the hero fixing that pain.
   - *Workflow Demo*: Show exactly **2 to 3 steps** focusing on outcomes, not technical settings.
   - *Benefit Recap*: Summarize quantifiable time or money saved.
3. **Show, Don't Tell (8:45–10:20)**:
   - *Human Face (+38% Lift)*: Use a presenter or HeyGen avatar to establish immediate trust.
   - *Visual Guidance*: Dynamic zooms and kinetic spotlight badges so viewers never search for buttons.
   - *Studio Audio*: Crisp voiceover audio.
4. **Crystal Clear CTA (10:20–11:10)**: Conclude with a single, frictionless action.
5. **Advanced Strategies**:
   - *Modular "Lego" Approach (11:10–12:15)*: 60-second atomic clips combined dynamically per buyer persona.
   - *Interactive Demos (12:15–13:20)*: Clickable self-guided tours paired with video.

---

## ⚡ Step-by-Step Guide: How to Use This Setup Effectively

Here are the 4 standard operational workflows to run your company and marketing swarm like a world-class growth machine.

### Recipe 1: End-to-End Autonomous Marketing Campaign
Run an entire campaign from research to copy, video, and email sequences in Buzz chat or CLI:

```bash
# Step 1: Brief the Head of Marketing
./manage.sh send marketing "@marketer-head We are launching Buzz Swarm OS for Solo SaaS Founders. Orchestrate the campaign."

# Step 2: Extract Competitor Hooks & Audit Landing Page
./manage.sh send marketing "@marketer-competitor Teardown competitor automation SaaS ads in Meta Ad Library"
./manage.sh send marketing "@marketer-site-auditor Audit https://bonifadetechnologies.com and score 0-100"

# Step 3: Structure Grand Slam Offer & Pricing
./manage.sh send marketing "@marketer-pricing Design 3 pricing tiers using Hormozi's Value Equation"

# Step 4: Write Graded Direct-Response Copy
./manage.sh send marketing "@marketer-copywriter Write a high-converting hero headline and lead for Buzz Swarm OS and grade it"

# Step 5: Scrub Copy through Anti-AI Slop Firewall
./manage.sh send marketing "@marketer-editor Review and scrub the copy for AI clichés, buzzwords, and fluff"

# Step 6: Generate Multi-Model Video Ads
./manage.sh send marketing "@marketer-creative Generate a 90-second SaaS demo video ad script and storyboard following the 4-part framework"

# Step 7: Build Full-Lifecycle Email Sequences
./manage.sh send marketing "@marketer-email Write our 5-day onboarding and conversion email sequence in full"
```

---

### Recipe 2: Generating AI Video Ads (Maxfusion Workflow)
Leverage multi-model AI video tools for high-converting creatives:

```bash
# 1. HeyGen Avatar Presenter (Human face for +38% conversion boost)
./manage.sh send marketing "@marketer-creative Generate a HeyGen avatar pitch video with our founder persona"

# 2. Google Veo 3.1 Cinematic B-Roll (4K terminal & UI macro animations)
./manage.sh send marketing "@marketer-creative Generate a 6-second Veo video of dark-mode terminal swarm execution"

# 3. Gemini Omni Flash Conversational Social Cut (9:16 vertical reels/TikTok)
./manage.sh send marketing "@marketer-creative Generate an Omni Flash video for a 9:16 vertical TikTok ad"

# 4. View Generated Video Job Exports
./manage.sh exports
```

---

### Recipe 3: Automated Client Proposals & PDF Generation
Generate and export branded, production-ready PDF proposals directly into `./data/exports/`:

```bash
# Request proposal from content specialist
./manage.sh send executive "@marketer-content Generate a PDF proposal for Acme Enterprise — AI Swarm Migration, 3 milestones, $12,500 total"

# Inspect and download generated PDF
./manage.sh exports
```

---

### Recipe 4: Multi-Channel Customer Engagement (Telegram, WhatsApp, Email)
Monitor and communicate with customers and your team across all external surfaces:

```bash
# 1. Check incoming emails and ticketing queue
./manage.sh check-emails

# 2. Send an outbound WhatsApp customer notification
./manage.sh send-whatsapp +2347081353229 "Hello! Your Buzz Swarm OS deployment is complete."

# 3. Start interactive terminal chat with your swarm
./manage.sh chat
```

---

## 🧰 Built-in Agent Tools Summary

| Tool Function | Category | Description |
|---|---|---|
| `generate_pdf` | Client Documents | Generates client-ready branded proposal/contract PDFs to `./data/exports/` |
| `site_audit_score` | CRO & Audits | Diagnostics scored 0–100 across Tech, CRO, SEO, Copy, and Security |
| `generate_llms_txt` | Search & GEO | Builds standard `llms.txt` and `llms-full.txt` for AI search engine indexing |
| `grade_copy` | Copywriting | Pre-grades direct-response copy on 6 pillars (Hook, Pain, Mechanism, Proof, Guarantee, CTA) |
| `anti_slop_check` | Content Quality | Scans and scrubs AI buzzwords, corporate clichés, and robotic phrasing |
| `competitor_meta_ad_analyzer` | Intelligence | Reverse-engineers competitor Meta Ad Library hooks, angles, and gaps |
| `pricing_calculator` | Monetization | Computes Hormozi Value Equation scores and 3-tier pricing models |
| `ab_test_calculator` | Growth Analytics | Calculates statistical significance (z-score, p-value) and conversion lift |
| `product_hunt_schedule` | Launch Ops | Produces hour-by-hour operational runbooks for launch day |
| `aso_metadata_analyzer` | App Growth | Analyzes App Store and Google Play metadata against algorithmic limits |
| `generate_video_omni` | Creative AI | Fast conversational Gemini Omni Flash video generation |
| `generate_video_veo` | Creative AI | High-fidelity Google Veo 3.1 cinematic video generation |
| `generate_video_heygen` | Creative AI | HeyGen presenter avatars / Video Agents |
| `firecrawl_scrape` / `firecrawl_search` | Intelligence | Live web extraction and competitive scraping |

---

## 📚 Complete Marketing Swarm Playbooks Library

The marketing swarm is backed by 15 operational playbooks in [`marketing/playbooks/`](marketing/playbooks/) and foundational knowledge in [`marketing/knowledge/`](marketing/knowledge/):

1. [`01-head-of-marketing-mastermind.md`](marketing/playbooks/01-head-of-marketing-mastermind.md) — Mastermind strategy & cross-channel CAC/LTV.
2. [`02-site-audit-and-cro.md`](marketing/playbooks/02-site-audit-and-cro.md) — Full-funnel technical and conversion audits.
3. [`03-geo-and-seo-rankings.md`](marketing/playbooks/03-geo-and-seo-rankings.md) — Generative Engine Optimization and `llms.txt`.
4. [`04-copywriting-and-grading-rubric.md`](marketing/playbooks/04-copywriting-and-grading-rubric.md) — Graded direct-response copy matrix.
5. [`05-creative-strategist-maxfusion-ads.md`](marketing/playbooks/05-creative-strategist-maxfusion-ads.md) — Multi-model AI visual ad workflows.
6. [`06-media-buying-and-kill-calls.md`](marketing/playbooks/06-media-buying-and-kill-calls.md) — Paid acquisition, fatigue alerts, kill calls.
7. [`07-email-sequences-and-schedules.md`](marketing/playbooks/07-email-sequences-and-schedules.md) — Full lifecycle email sequences and schedules.
8. [`08-social-feed-survival.md`](marketing/playbooks/08-social-feed-survival.md) — Algorithmic social dominance (X, LinkedIn, IG).
9. [`09-product-hunt-hour-by-hour.md`](marketing/playbooks/09-product-hunt-hour-by-hour.md) — Launch day runbook and hour-by-hour playbook.
10. [`10-pricing-tiers-and-offers.md`](marketing/playbooks/10-pricing-tiers-and-offers.md) — Hormozi Value Equation and pricing tiers.
11. [`11-competitor-meta-ad-teardown.md`](marketing/playbooks/11-competitor-meta-ad-teardown.md) — Meta Ad Library competitor reverse engineering.
12. [`12-aso-app-store-and-play.md`](marketing/playbooks/12-aso-app-store-and-play.md) — App Store and Google Play metadata optimization.
13. [`13-data-analytics-and-ab-testing.md`](marketing/playbooks/13-data-analytics-and-ab-testing.md) — Statistical A/B testing and growth dashboards.
14. [`14-anti-ai-slop-editor-guide.md`](marketing/playbooks/14-anti-ai-slop-editor-guide.md) — Anti-slop content firewall and brand voice guide.
15. [`15-saas-demo-video-ads-framework.md`](marketing/playbooks/15-saas-demo-video-ads-framework.md) — High-converting SaaS demo video & 4-part ad framework.

---

## 🧪 Diagnostics & Test Suites

Validate all AI models, tools, and bridges with a single command:

```bash
# 1. Run the comprehensive marketing swarm test suite
python3 scripts/test_marketing_swarm.py

# 2. Run end-to-end integration tests (Telegram, Nostr, Video APIs, DB)
./manage.sh test-all
```

---

## 🛠 Management CLI Cheat Sheet

The `./manage.sh` controller script manages all operations:

```bash
# View real-time service status, ports, and memory
./manage.sh status

# View live streaming logs
./manage.sh logs
./manage.sh logs agent-orchestrator

# Interactive chat with the swarm
./manage.sh chat

# Post message to a specific Buzz channel
./manage.sh send marketing "@marketer-head Review our weekly growth metrics"

# Check generated files (PDFs, Videos, Audits)
./manage.sh exports

# Full database and media backup
./manage.sh backup

# Seamless codebase update with zero downtime
./manage.sh update
```

---

## 🔒 Security & Data Hygiene

- **Owner-Only Config**: `.env` is locked to mode `600` to prevent unauthorized reading.
- **Port Isolation**: PostgreSQL is bound to `127.0.0.1`. Redis is accessible only over the internal Docker network.
- **Cryptographic Auditability**: Every event is signed with BIP-340 Schnorr signatures on secp256k1 keys.
- **Encrypted In-Transit**: All WebSocket and HTTP traffic is secured via modern TLS (HTTPS / WSS).

---

## 📄 License & Attribution

- **Buzz**: Developed by **Block, Inc.** under the **Apache 2.0 License**.
- **Bonifade Swarm Architecture**: Maintained by **Bonifade Technologies** ([bonifadetechnologies.com](https://bonifadetechnologies.com)).
