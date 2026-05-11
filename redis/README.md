# Redis adapters

The runnable Python package lives in `infra/redis` to avoid shadowing the third-party `redis` package. This directory documents the required Redis responsibilities from the architecture: cooldowns, queues, active sessions, leaderboard caching, notification queues, anti-spam, rate limits, and temporary game state.
