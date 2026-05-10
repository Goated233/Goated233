# Alpha Omega Arcade

Alpha Omega Arcade is a Python 3.12+, `discord.py` 2.x, button-first Discord gaming platform. It is designed as a premium MMO-style arcade with persistent views, PostgreSQL progression, Redis-backed sessions, owner/admin panels, reusable game engines, and playable Dungeon Raid.

## Requirements

- Python 3.12+
- Docker Desktop or Docker Engine
- PostgreSQL and Redis via `docker compose`
- A Discord bot token
- Required Discord bot scopes: `bot applications.commands`
- Required bot permissions: Send Messages, Embed Links, Use Application Commands, Read Message History
- Required intents: Guilds. Member intent is not required for the current launch flow.

## Local setup — Linux/macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
cp .env.example .env
# edit .env and set DISCORD_TOKEN
docker compose up -d postgres redis
alembic upgrade head
python scripts/seed_database.py
python scripts/bootstrap_owner.py
python -m app.bot
```

## Local setup — Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
Copy-Item .env.example .env
# edit .env and set DISCORD_TOKEN
docker compose up -d postgres redis
alembic upgrade head
python scripts\seed_database.py
python scripts\bootstrap_owner.py
python -m app.bot
```

## Deploy the persistent home panel

1. Invite the bot with `bot` and `applications.commands` scopes.
2. Start the bot.
3. As owner `ntmhaha` (`1417262684990083142`), run `/arcade setup-panel` in the target channel.
4. The posted Discord View uses stable custom IDs and is re-registered on restart.

## Health check

The owner can run `/arcade health` to verify:

- Discord token shape
- Owner ID/display configuration
- PostgreSQL connection
- Redis connection
- Panel readiness

## Playable flow

`Home → Games → Dungeon Raid → Start Tier 1 → Strike/Shield/Revive → Claim Rewards`

Dungeon Raid uses Redis-backed sessions, interaction locks, reconnect-ready state, procedural rooms, elite enemies, boss rooms, combat logs, and loot rewards.

## Database and migrations

```bash
alembic upgrade head
python scripts/seed_database.py
python scripts/bootstrap_owner.py
```

For local reset only:

```bash
python scripts/reset_dev_db.py
python scripts/seed_database.py
python scripts/bootstrap_owner.py
```

## Bot invite link

Replace `YOUR_CLIENT_ID` with your Discord application client ID:

```text
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot%20applications.commands&permissions=2147485696
```

## Package index / proxy errors

Some hosted coding environments block PyPI with errors like `Tunnel connection failed: 403 Forbidden` or fail while fetching `setuptools`. This is environment-specific, not an Alpha Omega Arcade code issue.

Local fixes:

```bash
python -m pip install -e .[dev]
# or
python -m pip install -r requirements.txt
```

If your network uses a private mirror:

```bash
python -m pip install -e .[dev] --index-url https://pypi.org/simple
python -m pip config set global.index-url https://pypi.org/simple
```

Corporate networks may require `HTTPS_PROXY` / `HTTP_PROXY` environment variables or an internal package index URL.

## Common errors

- `DISCORD_TOKEN is required`: copy `.env.example` to `.env` and set a real token.
- `PostgreSQL check failed`: run `docker compose up -d postgres` and verify `DATABASE_URL`.
- `Redis check failed`: run `docker compose up -d redis` and verify `REDIS_URL`.
- Slash command missing: restart the bot and check startup logs for command sync errors.
- Panel buttons expired after code changes: rerun `/arcade setup-panel`.
