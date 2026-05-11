from dataclasses import dataclass
from enum import StrEnum


class HelpCategory(StrEnum):
    START = "start"
    PROGRESSION = "progression"
    GAMES = "games"
    DUNGEON = "dungeon"
    CLANS = "clans"
    ECONOMY = "economy"
    EVENTS = "events"
    MATCHMAKING = "matchmaking"
    REWARDS = "rewards"
    RECOVERY = "recovery"
    FAQ = "faq"


@dataclass(frozen=True)
class HelpTopic:
    id: str
    category: HelpCategory
    title: str
    summary: str
    steps: tuple[str, ...]
    commands: tuple[str, ...]
    next_actions: tuple[str, ...]
    advanced_tip: str


@dataclass(frozen=True)
class HelpSearchResult:
    topic: HelpTopic
    score: int


class HelpCodexService:
    def __init__(self) -> None:
        self.topics = self._build_topics()

    def categories(self) -> list[HelpCategory]:
        return list(HelpCategory)

    def topic(self, topic_id: str) -> HelpTopic:
        for topic in self.topics:
            if topic.id == topic_id:
                return topic
        raise KeyError(topic_id)

    def category_topics(self, category: HelpCategory) -> list[HelpTopic]:
        return [topic for topic in self.topics if topic.category == category]

    def search(self, query: str, limit: int = 5) -> list[HelpSearchResult]:
        terms = {term.lower() for term in query.split() if term.strip()}
        if not terms:
            return [HelpSearchResult(topic, 1) for topic in self.topics[:limit]]
        results: list[HelpSearchResult] = []
        for topic in self.topics:
            haystack = " ".join([topic.title, topic.summary, *topic.steps, *topic.commands, topic.advanced_tip]).lower()
            score = sum(3 if term in topic.title.lower() else 1 for term in terms if term in haystack)
            if score:
                results.append(HelpSearchResult(topic, score))
        return sorted(results, key=lambda row: row.score, reverse=True)[:limit]

    def recommendations(self, level: int, has_clan: bool, active_session: bool) -> list[str]:
        actions = []
        if active_session:
            actions.append("Recover your active run before starting another activity.")
        if level < 5:
            actions.extend(["Run the Beginner Dungeon", "Claim your daily streak", "Open the Tutorial Codex"])
        else:
            actions.extend(["Queue for a co-op raid", "Push a seasonal quest", "Check the world boss timer"])
        if not has_clan:
            actions.append("Browse clans and apply to one global guild.")
        return actions[:5]

    def _build_topics(self) -> list[HelpTopic]:
        return [
            HelpTopic("welcome", HelpCategory.START, "Welcome to Alpha Omega", "A persistent MMO world that lives across Discord servers.", ("Press Start Adventure.", "Pick a class.", "Clear your beginner quest.", "Return to the Home Hub for the next recommendation."), ("!start", "/help"), ("Start Adventure", "Open Games", "Read Beginner Guide"), "Every button returns to persistent server-side state; you can recover interrupted sessions."),
            HelpTopic("progression", HelpCategory.PROGRESSION, "Progression + Battle Pass", "Earn XP, coins, gems, titles, cosmetics, and prestige through all activities.", ("Claim daily rewards.", "Complete quests.", "Play featured games.", "Spend cosmetics, not power, when possible."), ("!daily", "!quests", "!battlepass", "!profile"), ("Claim Daily", "View Quests", "Open Profile"), "Streaks and seasonal missions are the fastest early-game accelerators."),
            HelpTopic("games", HelpCategory.GAMES, "Game Browser", "The launcher recommends solo, co-op, PvP, seasonal, and clan activities.", ("Open Games.", "Filter by tag.", "Check queue sizes and difficulty.", "Favorite games you want to return to."), ("!games", "!play", "!raid"), ("Browse Trending", "Search Dungeon", "Queue Co-op"), "The browser is global; servers are gateways, not separate worlds."),
            HelpTopic("dungeon", HelpCategory.DUNGEON, "Dungeon Raid", "Button-first dungeon runs with rooms, boss encounters, loot reveals, and safe recovery.", ("Start Dungeon Raid.", "Use Strike/Shield/Revive.", "Claim rewards once.", "Recover if interrupted."), ("!raid", "!recover"), ("Beginner Dungeon", "Recover Run", "View Loot"), "Reward idempotency prevents dupes while protecting real progress."),
            HelpTopic("clans", HelpCategory.CLANS, "Global Clans", "Clans are cross-server MMO guilds with banners, officers, wars, banks, levels, and prestige.", ("Reach level 5.", "Create or join one clan.", "Contribute XP, dungeon clears, and world boss damage.", "Join wars and events."), ("!clan"), ("Browse Clans", "Apply", "View Clan Wars"), "Clan ownership is protected and officer powers follow hierarchy."),
            HelpTopic("economy", HelpCategory.ECONOMY, "Economy + Shop", "Coins and gems fuel cosmetics, boosts, clan upgrades, and rotating shop offers.", ("Earn rewards.", "Avoid duplicate claims.", "Preview shop items.", "Confirm purchases intentionally."), ("!shop", "!daily", "!inventory"), ("Open Shop", "View Inventory", "Claim Daily"), "All rewards are server-side validated and overflow protected."),
            HelpTopic("events", HelpCategory.EVENTS, "World Events", "Bosses, invasions, tournaments, clan wars, and region updates make the world feel alive.", ("Open Events.", "Check timers.", "Contribute once rewards are valid.", "Watch global broadcasts."), ("!events", "!boss", "!leaderboard"), ("Fight Boss", "Read Feed", "View Rankings"), "Region modifiers change the best activity each rotation."),
            HelpTopic("matchmaking", HelpCategory.MATCHMAKING, "Parties + Matchmaking", "Create one party, invite friends, challenge rivals, spectate, and queue globally.", ("Create or recover a party.", "Invite friends without spamming.", "Queue casual or ranked.", "Avoid AFK penalties."), ("!party", "!friends", "!rank"), ("Create Party", "Queue Ranked", "Invite Friend"), "Ranked queues have stricter cooldowns and abandonment penalties."),
            HelpTopic("rewards", HelpCategory.REWARDS, "Rewards + Rarity", "Loot reveals use rarity colors, showcase slots, badges, and prestige borders.", ("Watch reward reveals.", "Equip cosmetics.", "Showcase rare drops.", "Flex profile badges."), ("!inventory", "!profile"), ("Open Inventory", "Edit Showcase", "View Profile"), "Mythic cosmetics are designed as identity, not raw power."),
            HelpTopic("recovery", HelpCategory.RECOVERY, "Recovery + Safety", "Interrupted sessions can be restored through server-side recovery prompts.", ("Use !recover.", "Resume active session.", "Claim once.", "Return to Home Hub."), ("!recover"), ("Recover Run", "Open Home", "Contact Admin"), "Recovery never trusts stale client buttons; it reloads server state."),
            HelpTopic("faq", HelpCategory.FAQ, "FAQ", "Fast answers for common confusion.", ("Use !help search terms.", "Use !guide for next actions.", "Use !settings for preferences."), ("!help", "!guide", "!settings"), ("Search Codex", "What Next", "Open Settings"), "If in doubt, the Home Hub always shows the next best action."),
        ]
