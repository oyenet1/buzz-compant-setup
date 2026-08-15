# 🚚 Buzz Swarm VPS Migration Guide (Zero Data Loss)

This guide walks you through migrating your entire **Bonifade Technologies Buzz Swarm** (including 3+ years of historical Nostr events, PostgreSQL databases, agent cryptographic identities, media assets, chat threads, and configuration) to a new VPS or hosting provider with **zero data loss** and **minimal downtime**.

---

## 🧭 The 3-Step Migration Architecture

Because Buzz uses **PostgreSQL 17** for event storage and **secp256k1 Nostr keypairs** for identity, your swarm's identity and history are 100% portable. You do not need to reconfigure agents, re-invite bots, or recreate channels.

```
┌───────────────────────────┐                      ┌───────────────────────────┐
│     EXISTING OLD VPS      │                      │        NEW TARGET VPS     │
│                           │                      │                           │
│  1. Run ./manage.sh backup│                      │  3. Run ./install.sh      │
│  2. Export Snapshot Tarball ──(rsync / scp / R2)──▶ 4. Run ./manage.sh restore│
│     (buzz_backup_*.tar.gz)│                      │  5. Switch Domain DNS     │
└───────────────────────────┘                      └───────────────────────────┘
```

---

## 📋 Step-by-Step Migration Execution

### Step 1: Create Full Snapshot on the Old Server

On your existing server where the swarm is running:

```bash
cd /path/to/buzz-swarm-setup

# 1. Trigger full snapshot (dumps PostgreSQL, Redis, keys, and configs)
./manage.sh backup
```

This generates a compressed archive in `backups/`, for example:
`backups/buzz_backup_20290815_143000.tar.gz`

---

### Step 2: Transfer Files to the New Server

You can transfer directly using `rsync` (fastest & preserves permissions) or `scp`:

```bash
# Option A: rsync entire project directory to the new server (Recommended)
rsync -avzP /path/to/buzz-swarm-setup user@NEW_VPS_IP:/home/user/buzz-swarm-setup

# Option B: Or copy just the backup archive
scp backups/buzz_backup_20290815_143000.tar.gz user@NEW_VPS_IP:/home/user/
```

> **Tip with Cloudflare R2 / S3**: If you configured `R2_ACCESS_KEY_ID` in `.env`, `./manage.sh backup` automatically uploads the snapshot to your Cloudflare R2 bucket. On the new server, you can simply pull it down from R2!

---

### Step 3: Restore on the New Server

SSH into your **New VPS**:

```bash
# 1. Enter the project folder
cd /home/user/buzz-swarm-setup

# 2. Run the automated installer (installs Docker/Compose if missing)
chmod +x install.sh manage.sh scripts/*.sh
./install.sh

# 3. Restore the 3-year historical snapshot
./manage.sh restore backups/buzz_backup_20290815_143000.tar.gz

# 4. Restart services with restored state
./manage.sh restart
```

---

### Step 4: Update Domain DNS & Verify

1. **Update DNS `A` Record**: Point `buzz.bonifadetechnologies.com` to your **New VPS IP address**.
2. **Run Diagnostics**:
   ```bash
   ./manage.sh test-all
   ```
3. **Verify Everything is Intact**:
   * Open the Web UI on port `4005` (or HTTPS via domain).
   * All historical channels (`#general`, `#executive`, `#leads`, `#billing`, etc.) and 3-year message histories will appear instantly.
   * Send a test message from Telegram, WhatsApp, or CLI (`./manage.sh chat`).
   * Department agents (`@ceo`, `@cto`, `@dev`, `@billing`) will continue seamlessly with their existing cryptographic identities!

---

## 🔒 Why This Migration is Bulletproof

1. **Identity Preservation**: Agent public keys (`pubkeys`) and Relay keys are stored in `data/` and preserved in the backup. To the Nostr protocol, the agents are identical, so all historical Schnorr signatures remain valid.
2. **PostgreSQL Relational Integrity**: Full-text search indices, audit logs, and workflow events are dumped with `pg_dump` and restored with exact foreign-key relations.
3. **Zero Configuration Drift**: The `.env` file containing all API keys (Gemini, Telegram bot tokens, WhatsApp Cloud API keys, SMTP credentials) is restored with `chmod 600` permissions.
