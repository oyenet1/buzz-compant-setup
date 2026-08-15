#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# 🐝 BONIFADE TECHNOLOGIES — BUZZ COMPANY SWARM AUTOMATED INSTALLER
# ═══════════════════════════════════════════════════════════════════════════════
# Fully automated and interactive VPS deployment for Block's Buzz Hive Mind
# with multi-channel integration (Telegram, WhatsApp, SMTP, and AI Swarm).
#
# Usage:
#   chmod +x install.sh
#   ./install.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Terminal Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

clear || true

echo -e "${CYAN}${BOLD}"
echo "  ██████╗ ██╗   ██╗███████╗███████╗    ███████╗██╗    ██╗ █████╗ ██████╗ ███╗   ███╗"
echo "  ██╔══██╗██║   ██║╚══███╔╝╚══███╔╝    ██╔════╝██║    ██║██╔══██╗██╔══██╗████╗ ████║"
echo "  ██████╔╝██║   ██║  ███╔╝   ███╔╝     ███████╗██║ █╗ ██║███████║██████╔╝██╔████╔██║"
echo "  ██╔══██╗██║   ██║ ███╔╝   ███╔╝      ╚════██║██║███╗██║██╔══██║██╔══██╗██║╚██╔╝██║"
echo "  ██████╔╝╚██████╔╝███████╗███████╗    ███████║╚███╔███╔╝██║  ██║██║  ██║██║ ╚═╝ ██║"
echo "  ╚═════╝  ╚═════╝ ╚══════╝╚══════╝    ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝"
echo -e "${NC}"
echo -e "${BOLD}  Bonifade Technologies — Autonomous Company Swarm & Hive Mind Setup${NC}"
echo -e "${BLUE}  Powered by Block Buzz (Nostr Relay, ACP Agents & Multi-Channel Bridges)${NC}"
echo -e "  ═══════════════════════════════════════════════════════════════════════════════\n"

# ─────────────────────────────────────────────────────────────────────────────
# 1. System & Dependency Check
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}${BOLD}[1/7] Checking system environment and required dependencies...${NC}"

# Detect OS
OS_TYPE="unknown"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_TYPE=$ID
elif [ "$(uname)" = "Darwin" ]; then
    OS_TYPE="macos"
fi
echo -e "  ✓ Detected Operating System: ${GREEN}${OS_TYPE}${NC}"

# Helper for installing packages
install_pkg() {
    local pkgs=("$@")
    echo -e "  ⚙ Installing system packages: ${pkgs[*]}..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq && sudo apt-get install -y -qq "${pkgs[@]}"
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y -q "${pkgs[@]}"
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y -q "${pkgs[@]}"
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm "${pkgs[@]}"
    elif command -v apk >/dev/null 2>&1; then
        sudo apk add --no-cache "${pkgs[@]}"
    elif [ "$OS_TYPE" = "macos" ] && command -v brew >/dev/null 2>&1; then
        brew install "${pkgs[@]}"
    else
        echo -e "${RED}  ✗ Package manager not recognized. Please install: ${pkgs[*]}${NC}"
    fi
}

# Check essential CLI tools
MISSING_TOOLS=()
for tool in curl git openssl jq python3; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        MISSING_TOOLS+=("$tool")
    fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo -e "  ! Missing required tools: ${MISSING_TOOLS[*]}"
    install_pkg "${MISSING_TOOLS[@]}"
fi
echo -e "  ✓ Core CLI utilities verified (curl, git, openssl, jq, python3)"

# Check Docker
if ! command -v docker >/dev/null 2>&1; then
    echo -e "  ! Docker is not installed. Installing Docker automatically..."
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    rm -f /tmp/get-docker.sh
    if command -v systemctl >/dev/null 2>&1; then
        sudo systemctl enable --now docker
    fi
    echo -e "  ✓ Docker installed successfully."
fi

# Ensure current user can run docker without sudo if possible
if ! groups "$USER" 2>/dev/null | grep -q docker; then
    sudo usermod -aG docker "$USER" 2>/dev/null || true
fi

# Check Docker Compose (plugin or standalone)
DOCKER_COMPOSE_CMD=""
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo -e "  ! Docker Compose is not installed. Installing Docker Compose plugin..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq && sudo apt-get install -y -qq docker-compose-plugin
        DOCKER_COMPOSE_CMD="docker compose"
    else
        sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        DOCKER_COMPOSE_CMD="docker-compose"
    fi
fi
echo -e "  ✓ Docker & Docker Compose available (${DOCKER_COMPOSE_CMD})"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 2. Directory Setup & Permissions
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}${BOLD}[2/7] Initializing project directories...${NC}"
mkdir -p data data/postgres data/redis data/media data/git departments workflows scripts docker bridges/telegram bridges/whatsapp bridges/smtp
chmod 750 data
echo -e "  ✓ Directories verified and permissions secured."
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 3. Interactive Configuration & Registration Wizard
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}${BOLD}[3/7] Configuration & Registration Wizard${NC}"
echo -e "${CYAN}  Press [Enter] on any prompt to accept the sensible default value.${NC}"
echo -e "${CYAN}  You can also edit or add any variable later in the generated .env file.${NC}\n"

# Helper for interactive prompt
prompt_var() {
    local prompt_text="$1"
    local default_val="$2"
    local var_name="$3"
    local is_secret="${4:-false}"

    local user_val=""
    if [ "$is_secret" = "true" ]; then
        echo -ne "  ${BOLD}${prompt_text}${NC} "
        if [ -n "$default_val" ]; then
            echo -ne "[default: ********]: "
        else
            echo -ne "[optional - press Enter to skip]: "
        fi
        read -r user_val
    else
        echo -ne "  ${BOLD}${prompt_text}${NC} "
        if [ -n "$default_val" ]; then
            echo -ne "[default: ${CYAN}${default_val}${NC}]: "
        else
            echo -ne "[optional - press Enter to skip]: "
        fi
        read -r user_val
    fi

    if [ -z "$user_val" ]; then
        user_val="$default_val"
    fi
    eval "$var_name=\"\$user_val\""
}

# Read existing .env values if already present
if [ -f .env ]; then
    echo -e "  ${YELLOW}ℹ Found existing .env file. Loading current values as defaults...${NC}\n"
    # shellcheck disable=SC1091
    source .env 2>/dev/null || true
fi

# Detect VPS IP
DETECTED_IP=$(curl -s -m 3 https://api.ipify.org || curl -s -m 3 https://ifconfig.me || echo "127.0.0.1")

# Deployment Settings
prompt_var "Company Name" "${COMPANY_NAME:-Bonifade Technologies}" CFG_COMPANY_NAME
prompt_var "Domain Name or VPS Host (e.g. buzz.yourdomain.com or IP)" "${DOMAIN_NAME:-$DETECTED_IP}" CFG_DOMAIN_NAME
prompt_var "HTTP Scheme (http or https)" "${HTTP_SCHEME:-http}" CFG_HTTP_SCHEME
prompt_var "Public Web Port" "${APP_PORT:-3000}" CFG_APP_PORT
prompt_var "Buzz Relay WebSocket Port" "${RELAY_PORT:-8080}" CFG_RELAY_PORT

# Executive Contacts
prompt_var "CEO / Executive Name" "${CEO_NAME:-Hermes CEO}" CFG_CEO_NAME
prompt_var "CEO Email (for executive reports)" "${CEO_EMAIL:-bowofadeoyerinde@gmail.com}" CFG_CEO_EMAIL
prompt_var "CEO WhatsApp Number (e.g. +234...)" "${CEO_WHATSAPP_NUMBER:-+2347081353229}" CFG_CEO_WHATSAPP

echo ""
echo -e "${PURPLE}${BOLD}── AI Neural Engine Keys (Swarm Brain) ──────────────────────────${NC}"
prompt_var "Google Gemini API Key (Primary Recommended Model)" "${GOOGLE_API_KEY:-}" CFG_GOOGLE_API_KEY "true"
prompt_var "OpenAI API Key (Optional GPT-4o)" "${OPENAI_API_KEY:-}" CFG_OPENAI_API_KEY "true"
prompt_var "OpenRouter API Key (Optional Unified Gateway)" "${OPENROUTER_API_KEY:-}" CFG_OPENROUTER_API_KEY "true"
prompt_var "Firecrawl API Key (Web Scraping & Lead Discovery)" "${FIRECRAWL_API_KEY:-}" CFG_FIRECRAWL_API_KEY "true"

echo ""
echo -e "${PURPLE}${BOLD}── Communication Channels & Messaging Bridges ──────────────────${NC}"

# Telegram Setup
echo -ne "  ${BOLD}Enable Telegram Messaging Bridge?${NC} [Y/n]: "
read -r ENABLE_TG_ANS
ENABLE_TG_ANS="${ENABLE_TG_ANS:-Y}"
if [[ "$ENABLE_TG_ANS" =~ ^[Yy] ]]; then
    CFG_TELEGRAM_ENABLED="true"
    prompt_var "Telegram Bot Token (from @BotFather)" "${TELEGRAM_BOT_TOKEN:-}" CFG_TELEGRAM_BOT_TOKEN "true"
    prompt_var "Telegram Group Chat ID (for company alerts)" "${TELEGRAM_GROUP_CHAT_ID:-}" CFG_TELEGRAM_GROUP_CHAT_ID
    prompt_var "CEO Personal Telegram Chat ID (for direct escalation)" "${CEO_TELEGRAM_CHAT_ID:-}" CFG_CEO_TELEGRAM_CHAT_ID
else
    CFG_TELEGRAM_ENABLED="false"
    CFG_TELEGRAM_BOT_TOKEN=""
    CFG_TELEGRAM_GROUP_CHAT_ID=""
    CFG_CEO_TELEGRAM_CHAT_ID=""
fi

# WhatsApp Setup
echo ""
echo -ne "  ${BOLD}Enable Meta WhatsApp Cloud API Bridge?${NC} [y/N]: "
read -r ENABLE_WA_ANS
ENABLE_WA_ANS="${ENABLE_WA_ANS:-N}"
if [[ "$ENABLE_WA_ANS" =~ ^[Yy] ]]; then
    CFG_WHATSAPP_ENABLED="true"
    prompt_var "WhatsApp Cloud API Access Token" "${WHATSAPP_ACCESS_TOKEN:-}" CFG_WHATSAPP_ACCESS_TOKEN "true"
    prompt_var "WhatsApp Phone Number ID" "${WHATSAPP_PHONE_NUMBER_ID:-}" CFG_WHATSAPP_PHONE_NUMBER_ID
    prompt_var "WhatsApp Business Account ID" "${WHATSAPP_BUSINESS_ACCOUNT_ID:-}" CFG_WHATSAPP_BUSINESS_ACCOUNT_ID
else
    CFG_WHATSAPP_ENABLED="false"
    CFG_WHATSAPP_ACCESS_TOKEN="${WHATSAPP_ACCESS_TOKEN:-}"
    CFG_WHATSAPP_PHONE_NUMBER_ID="${WHATSAPP_PHONE_NUMBER_ID:-}"
    CFG_WHATSAPP_BUSINESS_ACCOUNT_ID="${WHATSAPP_BUSINESS_ACCOUNT_ID:-}"
fi

# SMTP Setup
echo ""
echo -ne "  ${BOLD}Enable SMTP Email Bridge (Invoices, Support & Outbound)?${NC} [Y/n]: "
read -r ENABLE_SMTP_ANS
ENABLE_SMTP_ANS="${ENABLE_SMTP_ANS:-Y}"
if [[ "$ENABLE_SMTP_ANS" =~ ^[Yy] ]]; then
    CFG_SMTP_ENABLED="true"
    prompt_var "SMTP Host (e.g. smtp.gmail.com)" "${SMTP_HOST:-smtp.gmail.com}" CFG_SMTP_HOST
    prompt_var "SMTP Port (587 for TLS, 465 for SSL)" "${SMTP_PORT:-587}" CFG_SMTP_PORT
    prompt_var "SMTP Username / Email" "${SMTP_USER:-bonifadetechnologies@gmail.com}" CFG_SMTP_USER
    prompt_var "SMTP App Password (Gmail 2FA App Password)" "${SMTP_APP_PASSWORD:-}" CFG_SMTP_APP_PASSWORD "true"
else
    CFG_SMTP_ENABLED="false"
    CFG_SMTP_HOST="${SMTP_HOST:-smtp.gmail.com}"
    CFG_SMTP_PORT="${SMTP_PORT:-587}"
    CFG_SMTP_USER="${SMTP_USER:-bonifadetechnologies@gmail.com}"
    CFG_SMTP_APP_PASSWORD="${SMTP_APP_PASSWORD:-}"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 4. Cryptographic Key Generation & Secrets
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}${BOLD}[4/7] Generating high-entropy cryptographic keys and credentials...${NC}"

# Random Generators
gen_pass() { openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24; }
gen_hex32() { openssl rand -hex 32; }

POSTGRES_PWD="${POSTGRES_PASSWORD:-$(gen_pass)}"
REDIS_PWD="${REDIS_PASSWORD:-$(gen_pass)}"
BUZZ_HMAC="${BUZZ_GIT_HOOK_HMAC_SECRET:-$(gen_hex32)}"
JWT_SEC="${JWT_SECRET:-$(gen_hex32)}"
ADMIN_TOKEN="${ADMIN_API_TOKEN:-$(gen_hex32)}"
WA_VERIFY="${WHATSAPP_WEBHOOK_VERIFY_TOKEN:-$(gen_pass)}"

# Generate Nostr secp256k1 keypair for the Relay using python helper
RELAY_PRIV_KEY="${BUZZ_RELAY_PRIVATE_KEY:-}"
RELAY_PUB_KEY="${BUZZ_RELAY_OWNER_PUBKEY:-}"

if [ -z "$RELAY_PRIV_KEY" ]; then
    KEY_OUT=$(python3 -c "from agents.nostr_util import generate_keypair; priv, pub = generate_keypair(); print(f'{priv}:{pub}')" 2>/dev/null || echo "")
    if [ -n "$KEY_OUT" ]; then
        RELAY_PRIV_KEY=$(echo "$KEY_OUT" | cut -d: -f1)
        RELAY_PUB_KEY=$(echo "$KEY_OUT" | cut -d: -f2)
    else
        RELAY_PRIV_KEY=$(gen_hex32)
        RELAY_PUB_KEY=""
    fi
fi

echo -e "  ✓ PostgreSQL Credentials Generated"
echo -e "  ✓ Redis Pub/Sub Key Generated"
echo -e "  ✓ Nostr Relay Signing Keypair: ${GREEN}${RELAY_PUB_KEY:0:16}...${NC}"
echo -e "  ✓ Internal HMAC & JWT Secrets Generated"

# Construct Public URLs
if [ "$CFG_HTTP_SCHEME" = "https" ]; then
    PUBLIC_URL="https://${CFG_DOMAIN_NAME}"
    RELAY_PUBLIC_URL="wss://${CFG_DOMAIN_NAME}"
else
    PUBLIC_URL="http://${CFG_DOMAIN_NAME}:${CFG_APP_PORT}"
    RELAY_PUBLIC_URL="ws://${CFG_DOMAIN_NAME}:${CFG_RELAY_PORT}"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 5. Write .env Configuration File
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}${BOLD}[5/7] Writing .env configuration file...${NC}"

cat <<EOF > .env
# ═══════════════════════════════════════════════════════════════
# Bonifade Technologies — Buzz Company Swarm Environment Config
# Generated automatically by install.sh on $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# ═══════════════════════════════════════════════════════════════

# ── 1. General & VPS Deployment ───────────────────────────────
ENVIRONMENT=production
COMPANY_NAME="${CFG_COMPANY_NAME}"
DOMAIN_NAME="${CFG_DOMAIN_NAME}"
HTTP_SCHEME="${CFG_HTTP_SCHEME}"
APP_PORT=${CFG_APP_PORT}
RELAY_PORT=${CFG_RELAY_PORT}
ADMIN_PORT=8081
HEALTH_PORT=9090
METRICS_PORT=9091
PUBLIC_URL=${PUBLIC_URL}
RELAY_PUBLIC_URL=${RELAY_PUBLIC_URL}

# ── 2. Database (PostgreSQL 17) ───────────────────────────────
POSTGRES_USER=buzz
POSTGRES_PASSWORD=${POSTGRES_PWD}
POSTGRES_DB=buzz
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgres://buzz:${POSTGRES_PWD}@postgres:5432/buzz
DB_POOL_SIZE=25

# ── 3. Cache & PubSub (Redis 7) ───────────────────────────────
REDIS_PASSWORD=${REDIS_PWD}
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://:${REDIS_PWD}@redis:6379/0
REDIS_POOL_SIZE=16

# ── 4. Buzz Relay Configuration ───────────────────────────────
BUZZ_BIND_ADDR=0.0.0.0:8080
BUZZ_RELAY_URL=ws://relay:8080
BUZZ_RELAY_PRIVATE_KEY=${RELAY_PRIV_KEY}
BUZZ_RELAY_OWNER_PUBKEY=${RELAY_PUB_KEY}
BUZZ_GIT_HOOK_HMAC_SECRET=${BUZZ_HMAC}
BUZZ_REQUIRE_AUTH_TOKEN=false
BUZZ_REQUIRE_RELAY_MEMBERSHIP=false
BUZZ_AUDIT_ENABLED=true
BUZZ_HUDDLE_AUDIO_AVAILABLE=true
CORS_ORIGINS=*

# ── 5. AI LLM Providers ───────────────────────────────────────
GOOGLE_API_KEY=${CFG_GOOGLE_API_KEY}
DEFAULT_GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=${CFG_OPENAI_API_KEY}
OPENROUTER_API_KEY=${CFG_OPENROUTER_API_KEY}
ANTHROPIC_API_KEY=
MOONSHOT_API_KEY=
DEFAULT_AI_PROVIDER=gemini
DEFAULT_AI_MODEL=gemini-2.5-flash
FIRECRAWL_API_KEY=${CFG_FIRECRAWL_API_KEY}

# ── 6. Telegram Messaging Bridge ──────────────────────────────
TELEGRAM_ENABLED=${CFG_TELEGRAM_ENABLED}
TELEGRAM_BOT_TOKEN=${CFG_TELEGRAM_BOT_TOKEN}
TELEGRAM_GROUP_CHAT_ID=${CFG_TELEGRAM_GROUP_CHAT_ID}
CEO_TELEGRAM_CHAT_ID=${CFG_CEO_TELEGRAM_CHAT_ID}

# ── 7. WhatsApp Messaging Bridge ──────────────────────────────
WHATSAPP_ENABLED=${CFG_WHATSAPP_ENABLED}
WHATSAPP_ACCESS_TOKEN=${CFG_WHATSAPP_ACCESS_TOKEN}
WHATSAPP_PHONE_NUMBER_ID=${CFG_WHATSAPP_PHONE_NUMBER_ID}
WHATSAPP_BUSINESS_ACCOUNT_ID=${CFG_WHATSAPP_BUSINESS_ACCOUNT_ID}
WHATSAPP_WEBHOOK_VERIFY_TOKEN=${WA_VERIFY}
WHATSAPP_GROUP_ID=

# ── 8. SMTP & Email Messaging Bridge ──────────────────────────
SMTP_ENABLED=${CFG_SMTP_ENABLED}
SMTP_HOST=${CFG_SMTP_HOST}
SMTP_PORT=${CFG_SMTP_PORT}
SMTP_USER=${CFG_SMTP_USER}
SMTP_APP_PASSWORD=${CFG_SMTP_APP_PASSWORD}
SMTP_FROM_EMAIL=${CFG_SMTP_USER}
SMTP_FROM_NAME="${CFG_COMPANY_NAME} Swarm"
EMAIL_DAILY_LIMIT=500
EMAIL_HOURLY_LIMIT=200
EMAIL_SEND_INTERVAL_SECONDS=20
IMAP_ENABLED=false
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=${CFG_SMTP_USER}
IMAP_PASSWORD=${CFG_SMTP_APP_PASSWORD}

# ── 9. Executive & Company Contact ────────────────────────────
CEO_NAME="${CFG_CEO_NAME}"
CEO_EMAIL=${CFG_CEO_EMAIL}
CEO_WHATSAPP_NUMBER=${CFG_CEO_WHATSAPP}
COMPANY_PHONE=+2347065720177
COMPANY_OFFICIAL_EMAIL=bonifadetechnologies@gmail.com
COMPANY_WEBSITE=https://bonifadetechnologies.com
COMPANY_BANK_NAME="Moniepoint MFB"
COMPANY_BANK_ACCOUNT=7065720177
COMPANY_BANK_ACCOUNT_NAME="Bonifade Technologies"

# ── 10. Security & Admin ──────────────────────────────────────
ADMIN_EMAIL=bonifadetechnologies@gmail.com
ADMIN_API_TOKEN=${ADMIN_TOKEN}
JWT_SECRET=${JWT_SEC}
LETSENCRYPT_EMAIL=bonifadetechnologies@gmail.com
EOF

chmod 600 .env
echo -e "  ✓ .env created with permissions set to 600 (owner-only access)"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 6. Docker Build & Startup
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}${BOLD}[6/7] Building and launching Buzz swarm containers...${NC}"

# Stop any running old containers
$DOCKER_COMPOSE_CMD down --remove-orphans 2>/dev/null || true

# Pull images and build custom bridges
echo -e "  ⚙ Pulling base images..."
$DOCKER_COMPOSE_CMD pull postgres redis || true

echo -e "  ⚙ Building AI Orchestrator & Channel Bridges..."
$DOCKER_COMPOSE_CMD build --no-cache agent-orchestrator bridge-telegram bridge-whatsapp bridge-smtp

echo -e "  ⚙ Starting Buzz Swarm stack in background..."
$DOCKER_COMPOSE_CMD up -d

echo -e "  ⚙ Waiting for database & relay to initialize..."
sleep 5

# Run database seed
echo -e "  ⚙ Seeding company channels, departments & baseline goals..."
python3 scripts/seed-company.py || echo -e "  ! Seed warning (relay will initialize on first connection)"

# Setup Systemd Service (Optional automatic start on reboot)
if [ -d /etc/systemd/system ] && command -v systemctl >/dev/null 2>&1; then
    echo -e "  ⚙ Configuring systemd unit for automatic VPS boot startup..."
    sudo bash -c "cat <<UNIT > /etc/systemd/system/buzz-swarm.service
[Unit]
Description=Buzz Hive Mind Swarm Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${SCRIPT_DIR}
ExecStart=$(command -v docker) compose up -d
ExecStop=$(command -v docker) compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
UNIT"
    sudo systemctl daemon-reload || true
    sudo systemctl enable buzz-swarm.service 2>/dev/null || true
    echo -e "  ✓ systemd service 'buzz-swarm.service' enabled."
fi

# ─────────────────────────────────────────────────────────────────────────────
# 7. Summary & Next Steps
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD} 🎉 BONIFADE TECHNOLOGIES BUZZ SWARM IS INSTALLED & RUNNING!${NC}"
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "  ${BOLD}🌐 Platform Access Endpoints:${NC}"
echo -e "    • Web Workspace:       ${CYAN}${PUBLIC_URL}${NC}"
echo -e "    • Buzz WebSocket Relay: ${CYAN}${RELAY_PUBLIC_URL}${NC}"
echo -e "    • PostgreSQL Database: 127.0.0.1:5432 (User: buzz)"
echo -e "    • Redis Pub/Sub:       127.0.0.1:6379"
echo ""
echo -e "  ${BOLD}📱 Integrated Communication Channels:${NC}"
if [ "$CFG_TELEGRAM_ENABLED" = "true" ] && [ -n "$CFG_TELEGRAM_BOT_TOKEN" ]; then
    echo -e "    • Telegram Bot:        ${GREEN}ACTIVE${NC} (Group ID: ${CFG_TELEGRAM_GROUP_CHAT_ID:-None})"
else
    echo -e "    • Telegram Bot:        ${YELLOW}IDLE${NC} (Add token in .env anytime)"
fi

if [ "$CFG_WHATSAPP_ENABLED" = "true" ]; then
    echo -e "    • WhatsApp Bridge:     ${GREEN}ACTIVE${NC} (Webhook: ${PUBLIC_URL}/webhook/whatsapp)"
else
    echo -e "    • WhatsApp Bridge:     ${YELLOW}IDLE${NC} (Configure Meta API in .env)"
fi

if [ "$CFG_SMTP_ENABLED" = "true" ] && [ -n "$CFG_SMTP_APP_PASSWORD" ]; then
    echo -e "    • SMTP Email Bridge:   ${GREEN}ACTIVE${NC} (${CFG_SMTP_USER})"
else
    echo -e "    • SMTP Email Bridge:   ${YELLOW}IDLE${NC} (Set SMTP_APP_PASSWORD in .env)"
fi

echo ""
echo -e "  ${BOLD}🤖 Active Department Agents in Swarm:${NC}"
echo -e "    • @ceo                 (Hermes CEO — Strategy & Orchestration)"
echo -e "    • @cto                 (CTO — Technical Architecture & Stack)"
echo -e "    • @fullstack-dev       (Fullstack Dev — Engineering & APIs)"
echo -e "    • @qa-tester           (QA Tester — Automation & Validation)"
echo -e "    • @devops-agent        (DevOps — Infrastructure & CI/CD)"
echo -e "    • @marketer-growth     (Growth — Campaigns & Video Scripts)"
echo -e "    • @marketer-research   (Research — Market Scrapes & Leads)"
echo -e "    • @billing-officer     (Billing — Invoicing & Moniepoint Payments)"
echo -e "    • @legal-officer       (Legal — MSAs, SOWs & NDAs)"
echo -e "    • @support-agent       (Support — Customer Tickets & Onboarding)"
echo -e "    • @site-monitor        (Site Monitor — Uptime & System Health)"
echo ""
echo -e "  ${BOLD}🛠 Management CLI Commands:${NC}"
echo -e "    • ${CYAN}./manage.sh status${NC}      → Check container health & resource usage"
echo -e "    • ${CYAN}./manage.sh logs${NC}        → View real-time logs of the entire swarm"
echo -e "    • ${CYAN}./manage.sh restart${NC}     → Gracefully restart all services"
echo -e "    • ${CYAN}./manage.sh update${NC}      → Pull updates, apply migrations & reload"
echo -e "    • ${CYAN}./manage.sh backup${NC}      → Create complete DB, redis & env backup"
echo -e "    • ${CYAN}./manage.sh chat${NC}        → Interactive CLI chat with the CEO / Swarm"
echo -e "    • ${CYAN}./manage.sh test-all${NC}    → Diagnostic test of all APIs and bridges"
echo ""
echo -e "${GREEN}✓ Everything is ready for production.${NC}\n"
