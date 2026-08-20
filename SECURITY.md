# ═══════════════════════════════════════════════════════════════
# Bonifade Technologies — Security & Secret Hygiene Policy
# ═══════════════════════════════════════════════════════════════

## 🔒 Threat Model & Security Posture

The Buzz Hive Mind platform operates on a cryptographic Nostr substrate where all events, chat messages, workflow executions, and agent decisions are signed using secp256k1 keypairs (BIP-340 Schnorr signatures).

### 1. Environment & Secret Management
- **Never commit `.env`**: The `.env` file must never be tracked in git. `.gitignore` is configured to prevent accidental staging.
- **Strict File Permissions**: The `install.sh` script automatically sets `chmod 600 .env` so that only the local system user has read/write privileges.
- **Key Derivation**: All secrets (Postgres passwords, Redis auth, Nostr keys, JWT secrets, Webhook tokens) are generated using cryptographic pseudo-random number generators (`openssl rand -base64 24` or `secrets.randbits(256)`).

### 2. Network Isolation & Firewall
- **Internal Services**: PostgreSQL may be bound to `127.0.0.1` for local admin; Redis is **not** published to the host by default — swarm containers reach it as `redis:6379` on `buzz-network` only. They must never be exposed to the public internet.
- **Reverse Proxy**: Public access is routed strictly through Caddy or Nginx with TLS encryption (HTTPS/WSS) and HTTP-to-HTTPS redirection.

### 3. Anti-Spam & Rate Limiting Guardrails
- **Outbound Email**:
  - Daily cap: 500 emails / day (Gmail sending threshold).
  - Hourly cap: 200 emails / hour.
  - Spacing: 20-second pause between consecutive outbound transmissions.
- **Relay Ingestion**: Buzz Relay enforces token limits and max WebSocket frame sizes (512 KB) to prevent denial-of-service attempts.

### 4. Audit Trail & Hash-Chain Verification
- All stored events in the Buzz Relay are indexed in PostgreSQL with full-text search and signed SHA-256 event IDs.
- Sensitive moderator or administrative actions are permanently recorded in the immutable audit log.
