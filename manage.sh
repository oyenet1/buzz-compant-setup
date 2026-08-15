#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# 🐝 BONIFADE TECHNOLOGIES — BUZZ SWARM MANAGEMENT CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════
# Unified management script for controlling, monitoring, and updating
# the Buzz Company Swarm stack.
#
# Usage:
#   ./manage.sh [command] [options]
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
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f .env ]; then
    # shellcheck disable=SC1091
    source .env
fi

# Detect Docker Compose command
DOCKER_COMPOSE="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    if command -v docker-compose >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker-compose"
    fi
fi

show_help() {
    echo -e "${CYAN}${BOLD}"
    echo "  🐝 Bonifade Technologies — Buzz Swarm Management CLI"
    echo -e "${NC}"
    echo -e "  ${BOLD}USAGE:${NC}"
    echo -e "    ./manage.sh <command> [arguments]\n"
    echo -e "  ${BOLD}COMMANDS:${NC}"
    echo -e "    ${GREEN}start${NC}                  Start the complete Buzz swarm in the background"
    echo -e "    ${GREEN}stop${NC}                   Stop all running swarm containers"
    echo -e "    ${GREEN}restart${NC} [service]      Restart all containers or a specific service"
    echo -e "    ${GREEN}status${NC}                 Show live container health, ports, and resource usage"
    echo -e "    ${GREEN}logs${NC} [service]         View live streaming logs (e.g. ./manage.sh logs relay)"
    echo -e "    ${GREEN}update${NC}                 Pull latest images, rebuild bridges & restart seamlessly"
    echo -e "    ${GREEN}backup${NC}                 Create a complete compressed backup of DB, Redis & config"
    echo -e "    ${GREEN}restore${NC} <file.tar.gz>  Restore database and state from a backup archive"
    echo -e "    ${GREEN}r2-status${NC}              Check Cloudflare R2 bucket connection, files & size"
    echo -e "    ${GREEN}r2-backup${NC}              Create a snapshot and upload immediately to Cloudflare R2"
    echo -e "    ${GREEN}r2-sync-marketing${NC}      Sync all marketing books and playbooks to Cloudflare R2"
    echo -e "    ${GREEN}seed${NC}                   Re-seed company channels, baseline goals & department agents"
    echo -e "    ${GREEN}chat${NC}                   Open interactive terminal chat with the CEO / Swarm"
    echo -e "    ${GREEN}test-all${NC}               Run diagnostic connectivity tests on all AI & messaging APIs"
    echo -e "    ${GREEN}check-emails${NC}           Check unread emails in Gmail/IMAP inbox immediately"
    echo -e "    ${GREEN}send${NC} <channel> <msg>   Post a direct message into a Buzz channel"
    echo -e "    ${GREEN}psql${NC}                   Open an interactive PostgreSQL database shell"
    echo -e "    ${GREEN}redis-cli${NC}              Open an interactive Redis CLI session"
    echo -e "    ${GREEN}help${NC}                   Show this help message\n"
}

get_active_services() {
    local services="relay agent-orchestrator bridge-telegram bridge-whatsapp bridge-smtp"

    # Dynamic PostgreSQL detection
    if [ -z "$DATABASE_URL" ] || [[ "$DATABASE_URL" == *"@postgres:"* ]] || [[ "$DATABASE_URL" == *"@127.0.0.1:"* ]] || [[ "$DATABASE_URL" == *"@localhost:"* ]] || [ "${USE_EXTERNAL_POSTGRES}" = "false" ]; then
        services="postgres $services"
    else
        local db_host=$(echo "$DATABASE_URL" | sed -E 's/.*@([^:\/]+).*/\1/')
        echo -e "  ${CYAN}ℹ External PostgreSQL detected (${db_host}) — skipping local postgres container.${NC}"
    fi

    # Dynamic Redis detection
    if [ -z "$REDIS_URL" ] || [[ "$REDIS_URL" == *"@redis:"* ]] || [[ "$REDIS_URL" == *"@127.0.0.1:"* ]] || [[ "$REDIS_URL" == *"@localhost:"* ]]; then
        services="redis $services"
    else
        local redis_host=$(echo "$REDIS_URL" | sed -E 's/.*@([^:\/]+).*/\1/')
        echo -e "  ${CYAN}ℹ External Redis detected (${redis_host}) — skipping local redis container.${NC}"
    fi

    echo "$services"
}

case "$1" in
    start)
        echo -e "${GREEN}Starting Buzz Company Swarm (Dynamic Discovery)...${NC}"
        TARGET_SERVICES=$(get_active_services)
        # shellcheck disable=SC2086
        $DOCKER_COMPOSE up -d $TARGET_SERVICES
        echo -e "${GREEN}✓ All active swarm services started successfully.${NC}"
        ;;

    stop)
        echo -e "${YELLOW}Stopping Buzz Company Swarm...${NC}"
        $DOCKER_COMPOSE down
        echo -e "${YELLOW}✓ All services stopped.${NC}"
        ;;

    restart)
        shift
        SERVICE="$1"
        if [ -n "$SERVICE" ]; then
            echo -e "${YELLOW}Restarting service: $SERVICE...${NC}"
            $DOCKER_COMPOSE restart "$SERVICE"
        else
            echo -e "${YELLOW}Restarting all active swarm services...${NC}"
            TARGET_SERVICES=$(get_active_services)
            # shellcheck disable=SC2086
            $DOCKER_COMPOSE restart $TARGET_SERVICES
        fi
        echo -e "${GREEN}✓ Restart complete.${NC}"
        ;;

    status)
        echo -e "\n${CYAN}${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${BOLD}  Buzz Swarm Service Status${NC}"
        echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════════════${NC}\n"
        $DOCKER_COMPOSE ps
        echo ""
        echo -e "${BOLD}Resource Usage (Memory & CPU):${NC}"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
            $(docker ps --filter "name=buzz-" -q) 2>/dev/null || true
        echo ""
        ;;

    logs)
        shift
        SERVICE="$1"
        if [ -n "$SERVICE" ]; then
            $DOCKER_COMPOSE logs -f "$SERVICE"
        else
            $DOCKER_COMPOSE logs -f --tail=100
        fi
        ;;

    update)
        echo -e "${YELLOW}${BOLD}Updating Buzz Swarm Deployment...${NC}"
        echo -e "  [1/4] Pulling latest base images..."
        $DOCKER_COMPOSE pull postgres redis || true

        echo -e "  [2/4] Rebuilding custom agent orchestrator and channel bridges..."
        $DOCKER_COMPOSE build --no-cache agent-orchestrator bridge-telegram bridge-whatsapp bridge-smtp

        echo -e "  [3/4] Restarting containers with zero downtime..."
        $DOCKER_COMPOSE up -d --remove-orphans

        echo -e "  [4/4] Verifying database and running seed checks..."
        sleep 3
        python3 scripts/seed-company.py 2>/dev/null || true

        echo -e "${GREEN}${BOLD}✓ Buzz Swarm successfully updated to latest version!${NC}"
        ;;

    backup)
        bash scripts/backup.sh
        ;;

    restore)
        shift
        bash scripts/restore.sh "$@"
        ;;

    r2-status)
        python3 scripts/r2_storage.py status
        ;;

    r2-backup)
        bash scripts/backup.sh
        ;;

    r2-sync-marketing)
        python3 scripts/r2_storage.py sync-marketing
        ;;

    seed)
        echo -e "${GREEN}Re-seeding company channels and baseline goals...${NC}"
        python3 scripts/seed-company.py
        ;;

    chat)
        python3 scripts/chat.py
        ;;

    test-all)
        python3 scripts/test_integrations.py
        ;;

    check-emails|read-emails)
        python3 bridges/smtp/bridge.py check
        ;;

    send)
        shift
        CHANNEL="${1:-general}"
        shift || true
        MSG="$*"
        if [ -z "$MSG" ]; then
            echo "Usage: ./manage.sh send <channel_name> <your message>"
            exit 1
        fi
        python3 -c "
import asyncio, json, os, sys
sys.path.insert(0, 'agents')
from nostr_util import generate_keypair, create_event, KIND_STREAM_MESSAGE
import websockets

async def send():
    priv, pub = generate_keypair()
    ev = create_event(priv, KIND_STREAM_MESSAGE, '$MSG', tags=[['channel', '$CHANNEL']])
    async with websockets.connect(os.getenv('BUZZ_RELAY_URL', 'ws://127.0.0.1:8080')) as ws:
        await ws.send(json.dumps(['EVENT', ev]))
        print('✓ Message posted to #${CHANNEL}')

asyncio.run(send())
"
        ;;

    psql)
        echo -e "${GREEN}Opening PostgreSQL shell for database 'buzz'...${NC}"
        docker exec -it buzz-postgres psql -U "${POSTGRES_USER:-buzz}" -d "${POSTGRES_DB:-buzz}"
        ;;

    redis-cli)
        echo -e "${GREEN}Opening Redis CLI...${NC}"
        if [ -n "$REDIS_PASSWORD" ]; then
            docker exec -it buzz-redis redis-cli -a "$REDIS_PASSWORD"
        else
            docker exec -it buzz-redis redis-cli
        fi
        ;;

    help|--help|-h|"")
        show_help
        ;;

    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
