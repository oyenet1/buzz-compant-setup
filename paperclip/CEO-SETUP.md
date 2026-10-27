# Set up the Bonifade CEO with GPT-6.1 Sol

These steps assume Paperclip is running using paperclip/compose.yml from this
repository. That configuration mounts the company files at /company.

## 1. Open Paperclip

From your computer, replace the SSH username and VPS address:

```sh
ssh -L 13100:127.0.0.1:13100 YOUR_USER@YOUR_VPS_IP
```

Keep the tunnel open. Visit https://company.bonifadetechnologies.com and sign in to your company.

## 2. Connect your OpenAI account

In Paperclip, open **Apps → Connections** and connect Codex using your ChatGPT
account or an OpenAI API key. Complete the connection in your browser.
The account connected to your desktop chat is not automatically connected on the VPS.

## 3. Create the CEO workspace

On your VPS:

```sh
cd ~/bonifade/paperclip
docker compose -f compose.yml exec --user node server \
  mkdir -p /paperclip/workspaces/ceo
```

If you installed the repository elsewhere, adjust the first command.

## 4. Create or edit the CEO agent

Use these settings; labels can vary by Paperclip version:

| Setting | Value |
|---|---|
| Name | Fade_networker |
| Role | CEO |
| Adapter | Codex (codex_local) |
| Provider connection | The OpenAI/Codex connection from step 2 |
| Model | gpt-6.1-sol |
| Reasoning effort | high |
| Working directory | /paperclip/workspaces/ceo |
| Instructions file | /company/paperclip/AGENTS.md |

Choose a spending budget appropriate to your account before enabling scheduled runs.

## 5. Add the CEO prompt

Paste this into the agent prompt field:

```text
You are Fade_networker, CEO of Bonifade Technologies.

Read /company/SOUL.md for company information and
/company/departments/ceo.json for your role.
Follow /company/paperclip/AGENTS.md.

Turn company goals into clear tasks, delegate to available
department agents, track progress, and review their work.
Use Paperclip's workflow instructions for task management.

Retrieve relevant marketing knowledge before planning campaigns:
python3 /company/paperclip/knowledge.py search "YOUR TOPIC" --limit 5
Replace YOUR TOPIC with the subject of the task.

Cite sources and identify missing product facts.
Obtain human approval before publishing, sending outreach,
spending money, or committing contracts.

Company files describe the former Buzz runtime in some places.
Do not claim Buzz tools or integrations are available in Paperclip
unless they have actually been connected.
```

## 6. Save and test the connection

Save the agent, then run its adapter Test/environment check. Confirm that the
provider connection works and the requested model is available to your account.

If the test reports an outdated Codex CLI, check its version:

```sh
cd ~/bonifade/paperclip
docker compose -f compose.yml exec server codex --version
```

The pinned Paperclip adapter identifies Codex 0.159.0 as the verified minimum for
GPT-6.1 Sol with ChatGPT sign-in. If necessary, rebuild the image with fresh tool
installation layers, then retry the test:

```sh
docker compose -f compose.yml build --no-cache server
docker compose -f compose.yml up -d server
```

## 7. Assign the first task

Create a task assigned to the CEO:

```text
Read our company identity and marketing playbooks.
Summarize Bonifade's services, propose a department structure,
and draft a 7-day marketing plan.
List missing product information and cite your sources.
Keep all outputs as drafts for my review.
```

Run the task and inspect the run output. Confirm the CEO reads the company files,
uses knowledge search, cites sources, and identifies missing information. Create
the other department agents before expecting the CEO to delegate work to them.

## Reference

- Paperclip Docker and account connections: https://github.com/paperclipai/paperclip/blob/50b932a142216331b8d476042b454bc123739c40/doc/DOCKER.md
- Paperclip Codex adapter and CLI minimum: https://github.com/paperclipai/paperclip/blob/50b932a142216331b8d476042b454bc123739c40/packages/adapters/codex-local/src/index.ts
- OpenAI model documentation: https://developers.openai.com/api/docs/models/gpt-6.1-sol
