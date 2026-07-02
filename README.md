# Relationship Bot

A production-grade Discord relationship assistant for couples, built with Python 3.12, discord.py 2.5+, Motor/MongoDB, OpenAI, Pillow, aiohttp, and Railway-friendly process files.

## Features

- Prefix-only command UX using `,`.
- Couple linking with pending acceptance and active relationship records.
- AI counselor and complaint mediation using the OpenAI API with a safety-focused counselor prompt.
- Memories, journals, mood tracking, goals, reminders, anniversaries, statistics, affection, fun commands, and image cards.
- MongoDB persistence with indexes for all relationship collections.
- Reminder background delivery, JSON logging, admin logging configuration, and owner backup export.
- Modular architecture: `bot.py`, `config.py`, `cogs/`, `services/`, `models/`, `database/`, `utils/`, `events/`, `views/`, `prompts/`, and `assets/`.

## Local setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
# edit .env with DISCORD_TOKEN, MONGO_URI, and OPENAI_API_KEY
python bot.py
```

## Railway

Railway can run the included `Procfile`:

```text
worker: python bot.py
```

Set the environment variables shown in `.env.example` and attach a MongoDB service or external MongoDB URI.

## Primary commands

- `,couple link @partner` — create a pending couple link.
- `,couple accept` — accept a pending link.
- `,couple stats` — view relationship statistics.
- `,couple card` — render a Pillow relationship card.
- `,counsel <message>` — ask the AI counselor for practical guidance.
- `,complaint <text>` — save and mediate a complaint.
- `,memory <text>` — save a shared memory.
- `,journal <title> <body>` — save a journal entry.
- `,mood <1-10> [note]` — track mood.
- `,goal <title>` — create a relationship goal.
- `,remind <30m|2h|7d> <message>` — schedule a DM reminder.
- `,anniversary <YYYY-MM-DD>` — save anniversary date.
- `,hug [member]` and `,dateidea` — affection and fun commands.
- `,backup` — owner/admin JSON export.
- `,rblog #channel` — owner/admin logging channel setting.
