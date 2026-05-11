# Alpha Omega Arcade Python Architecture

Alpha Omega Arcade is a **button-first** Discord gaming ecosystem built with Python 3.12+, discord.py 2.x persistent views, async SQLAlchemy, PostgreSQL, Redis, and clean architecture. Gameplay and administration are intentionally driven by embeds, buttons, select menus, and modals; slash commands are reserved for optional bootstrap/deployment entry points.

## Runtime layers

- **app/**: configuration, logging, dependency wiring, Discord client startup, persistent view registration.
- **ui/**: premium embeds, cards, buttons, selects, modals, pagination, persistent views, confirmation screens, and loading states.
- **core/**: async services for profiles, inventory, economy, leaderboards, sessions, notifications, matchmaking, analytics, anti-cheat, quests, moderation, and admin permissions.
- **database/**: SQLAlchemy models and repositories. PostgreSQL is the source of truth for player progression, admin state, audit logs, punishments, analytics, sessions, and economy history.
- **redis/**: shared async primitives for cache, queues, cooldowns, active sessions, rate limits, notification queues, and anti-spam.
- **engines/**: reusable game engines. New games inherit from an engine and provide configuration/content, enabling 1000+ games without isolated rewrites.
- **games/**: polished game modules powered by engines, starting with Dungeon Raid, Blackjack, Mafia, Boss Battle, and Empire Conquest.
- **admin/**: owner-only and delegated admin panels, dashboards, audit tools, analytics views, moderation tools, and global controls.

## Owner and security model

The platform owner is Discord user `1417262684990083142` (`ntmhaha`). The owner is the highest permission level and bypasses cooldowns, anti-spam, economy limits, admin hierarchy, matchmaking restrictions, and dangerous-action throttles. Every admin action still creates an immutable audit record with actor, target, action type, reason, timestamp, and rollback metadata.

## Button-first UX

The persistent home panel acts like a console launcher with buttons for Games, Profile, Leaderboards, Inventory, Clans, Shop, Quests, Ranked, Events, Settings, About, and Admin. Every feature opens another interactive Discord view rather than asking users to type commands repeatedly.

## Migration workflow

1. Copy `.env.example` to `.env` and fill `DISCORD_TOKEN`.
2. Start services: `docker compose up -d postgres redis`.
3. Install dependencies: `python -m pip install -e .[dev]`.
4. Apply migrations once Alembic revisions are generated: `alembic upgrade head`.
5. Run the bot: `python -m app.bot`.

## Gameplay systems added in this phase

- **Distributed sessions**: `DistributedSessionManager` uses Redis session indexes, per-user active-session keys, reconnect tokens, stale cleanup, and short-lived interaction locks to prevent duplicate/concurrent game actions across workers.
- **Premium UI kit**: reusable card, pagination, and button builders provide rarity colors, reward screens, match-found screens, event announcements, profile cards, inventory cards, and mobile-friendly navigation patterns.
- **Dungeon Raid depth**: Dungeon Raid now has a procedural director with daily rotations, tier scaling, elite enemies, boss rooms, hero classes, abilities, status effects, revives, combat logs, loot tables, and damage tracking.
- **Retention systems**: progression includes XP curves, daily rewards, streak scaling, milestone titles, and reward scaling hooks for seasons/world events.
- **Platform loops**: matchmaking, leaderboards, world events, clan contribution, economy balancing, and analytics signal builders integrate with Redis/PostgreSQL services without duplicating game logic.

## Engagement systems added in this phase

- **Daily retention**: login streaks, weekly/monthly streak milestones, rotating daily/weekly/seasonal quests, battle pass XP multipliers, boosters, and claim visuals are centralized in `RetentionService`.
- **Premium identity**: profile themes, rarity palettes, badges, banners, cosmetics, and compact mobile stat formatting now share a single visual branding system.
- **Social competition**: parties, friend/challenge/game invites, spectating payloads, global feed events, leaderboard dethrone moments, tournament brackets, and world boss rankings create reasons to return and share wins.
- **Live events and shop**: world boss schedules, HP bars, damage reward tiers, rotating shop offers, cosmetic previews, and event-exclusive rewards connect daily play to visible progression.
- **Safety/performance**: reward validation, idempotency checks, session desync detection, and cache policy helpers protect the economy and keep high-traffic panels lightweight.
