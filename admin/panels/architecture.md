# Owner/Admin Panel Architecture

The admin system is a persistent Discord View system, not a slash-command workflow. The home panel exposes an owner/admin button that checks permissions before rendering the admin console.

## Security flow

1. Resolve `PermissionContext` for the interacting user.
2. Owner `1417262684990083142` (`ntmhaha`) receives all permissions and bypasses cooldowns/restrictions.
3. Delegated admins are checked against persisted roles and permissions.
4. Dangerous actions open confirmation/reason modals.
5. Every submitted action creates `AuditLog` and `AdminActionHistory` rows with actor, target, reason, metadata, and rollback metadata.

## Dashboards

- Admin dashboard: live platform stats, DB/Redis health, owner badge, server/shard/session counts.
- User management: inspect users, bans, stat resets, inventory wipes, grants, cooldown resets, blacklists.
- Moderation: warnings, punishments, exploit flags, notes, shadow mutes, anti-cheat review.
- Game control: terminate sessions, spawn bosses, tune loot/XP/drop rates, tournaments, leaderboard resets.
- Economy: transaction inspection, freezes, rollbacks, exploit detection, item creation/deletion.
- Analytics: retention, activity, game popularity, inflation, abuse, live sessions, button usage.
- Global controls: broadcasts, maintenance mode, enable/disable games, notification campaigns.
