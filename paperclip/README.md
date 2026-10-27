# Bonifade Paperclip VPS setup

Prepared 27 October 2026 from this repository's dev branch. This adds a separate
Dockerized Paperclip server and PostgreSQL database, preserving the existing Buzz
deployment. It reuses company identity, department prompts, logos and marketing
knowledge. Buzz messaging bridges, PDF/video tools and Nostr history are not migrated.

## Install on your Linux VPS

Prerequisites: Git, Python 3 with SQLite FTS5, OpenSSL, Docker Engine and the Docker
Compose plugin. The installer downloads the official prebuilt image instead of compiling source;
runtime RAM and disk requirements depend on agent concurrency and image size. The models run through providers,
not as local model weights on your VPS.

Clone this repository on your VPS, or transfer this checkout.
Copy the checkout using your normal Git or SFTP workflow, excluding local secrets,
data, .git and paperclip/upstream. On the VPS:

```sh
cd /opt/buzz-compant-setup
bash paperclip/setup.sh
```

The installer creates paperclip/.env with independent persistent secrets, pins
the official Paperclip image to commit 50b932a142216331b8d476042b454bc123739c40, builds the
knowledge index, and pulls/starts the containers without a source build. Re-running preserves secrets.
Keep the project directory private: its data includes internal company information.
Do not run the old root install.sh to install Paperclip; that installs Buzz.

## Access and first administrator

The canonical URL is https://company.bonifadetechnologies.com. Configure your host
Nginx HTTPS reverse proxy to forward to http://127.0.0.1:13100, preserving the Host
header and forwarding X-Forwarded-Proto and X-Forwarded-For. Support WebSocket
upgrades. PostgreSQL has no published port. The host port defaults to 13100; set PAPERCLIP_PORT in paperclip/.env to override it. The container continues listening on port 3100.

The installer creates paperclip/.env automatically. Re-running upgrades the original
http://localhost:3100 URL to this domain while preserving secrets and custom URLs.
Authenticated/private mode remains enabled. Complete the first account sign-in and
Claim this instance yourself before making the site generally accessible.

All tracked company sources, department prompts, marketing Markdown and brand assets
are included when cloning this repository. The installer builds a lexical knowledge
index and mounts the checkout read-only at /company for local agents. These files
are not automatically imported as UI documents, companies or agents.

## Company, logos and agents

1. Create **Bonifade Technologies**, website https://bonifadetechnologies.com.
2. Upload assets/brand/logo-512.png as the company icon where supported; use
   logo-full.jpeg in proposals/brand work. The upstream UI itself is not rebranded.
3. Connect provider credentials in **Apps -> Connections**. Credentials for this
   desktop chat are not automatically available on the VPS.
4. Create agents using departments/*.json, preserving names, roles and prompts.
   CEO reports to the human owner; CTO reports to CEO; engineering, QA, DevOps and
   site monitor report to CTO; marketing, billing, legal and support report to CEO.
5. Set the local agent working directory to /paperclip/workspaces/<agent-id>;
   create writable directories in the container if the adapter does not create them.
   Set instructions file to /company/paperclip/AGENTS.md, and append the corresponding
   department system_prompt in the agent prompt field. /company is read-only.
6. Apply models.json: GPT-6.1 Sol via Codex for the core team; Gemini 3.8 Flash via
   Gemini CLI for research/growth; Muse Spark 1.3 Contributor for content.
   The upstream image includes Codex and Gemini CLI. Run each adapter environment
   check and a small task before enabling scheduled work. Model access is account-specific.
7. Muse is a deployment dependency still to resolve: these files do not install a
   Meta runtime or invent a native Paperclip adapter. Connect a validated Meta-capable
   runtime through a supported adapter before activating that agent. Keep it paused
   until the integration and training-data policy are verified. Contributor mode can
   use inputs/outputs for Meta training; send only approved public marketing material,
   not the private SOUL/company corpus. Use standard Muse for private retrieval if needed.
8. Set company/agent budgets, then assign a draft campaign for one real product.
   Marketing handoff: research -> growth -> content -> CEO/human review.

models.json is an operator configuration plan, not an automatic Paperclip import.
No companies, provider connections or agents have been created on a live server.

## Retrieval and maintenance

This is lexical RAG: overlapping text chunks ranked by SQLite FTS5 BM25. It is not
vector/semantic search. It indexes only SOUL.md, department JSON, marketing Markdown
and optional products/*.md. It never indexes .env. Logos remain image assets.

```sh
python3 paperclip/knowledge.py index
python3 paperclip/knowledge.py search 'WhatsApp Nigerian trust offer' --limit 5
cd paperclip
docker compose -f compose.yml exec server python3 /company/paperclip/knowledge.py search 'storytelling offer' --limit 3
docker compose -f compose.yml ps
docker compose -f compose.yml logs --tail=100 server
```

Rebuild the index on the host after knowledge changes. The read-only mount makes it
available to local agents immediately. Remote/cloud agents need their own mounted
knowledge or an authenticated retrieval integration; this path does not reach them.
Add approved product facts under products/ before requesting real campaigns: the
existing playbooks reference products and library paths missing from this checkout.
Search results preserve file:line citations; prompts require retrieval before drafts.

Back up the PostgreSQL database, paperclip-data volume, paperclip/.env and company
sources together. Store backups outside this VPS and test restores. Do not use
docker compose down -v on a deployment you want to retain. Review upstream changes
and back up before changing the image reference in compose.yml.

## Validation limits and sources

The local retrieval checks are runnable without provider keys. Docker and VPS
startup require a Linux host and have not been verified from this Windows workspace.

- Paperclip: https://github.com/paperclipai/paperclip/blob/50b932a142216331b8d476042b454bc123739c40/doc/DOCKER.md
- Sol: https://developers.openai.com/api/docs/models/gpt-6.1-sol
- Gemini: https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
- Muse and Contributor data policy: https://dev.meta.ai/docs/models
