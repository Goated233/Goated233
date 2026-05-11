from dataclasses import dataclass
from enum import StrEnum


class StarterClass(StrEnum):
    VANGUARD = "vanguard"
    RIFTWALKER = "riftwalker"
    STARWEAVER = "starweaver"


@dataclass(frozen=True)
class OnboardingStep:
    id: str
    title: str
    body: str
    action_label: str
    reward_preview: str


@dataclass(frozen=True)
class StarterLoadout:
    player_class: StarterClass
    title: str
    rewards: dict
    cosmetics: tuple[str, ...]
    beginner_quests: tuple[str, ...]


class OnboardingService:
    STEPS = (
        OnboardingStep("wake", "Wake in the Omega Gate", "You are entering a global arcade universe where every server connects to the same world.", "Start Adventure", "+500 coins • Founder Spark"),
        OnboardingStep("class", "Choose Your First Class", "Pick a combat identity. Classes guide recommendations and profile flavor without locking you out.", "Choose Class", "Starter class title"),
        OnboardingStep("quest", "Accept Beginner Quest", "Clear a short dungeon, claim a daily reward, and open your profile showcase.", "Accept Quest", "+180 XP • Beginner Cache"),
        OnboardingStep("social", "Join the Living World", "Discover clans, parties, world bosses, and global broadcasts when you are ready.", "Open Home Hub", "Global Feed unlocked"),
    )

    def cinematic_flow(self) -> tuple[OnboardingStep, ...]:
        return self.STEPS

    def loadout(self, player_class: StarterClass) -> StarterLoadout:
        names = {
            StarterClass.VANGUARD: ("Vanguard", "🛡️ Gatebreaker Mantle"),
            StarterClass.RIFTWALKER: ("Riftwalker", "⚡ Riftstep Cloak"),
            StarterClass.STARWEAVER: ("Starweaver", "✨ Astral Thread"),
        }
        title, cosmetic = names[player_class]
        return StarterLoadout(
            player_class,
            title,
            {"coins": 500, "gems": 25, "xp": 120, "item": "beginner_cache"},
            (cosmetic, "🌌 Omega Initiate Banner"),
            ("Clear the Beginner Dungeon", "Claim your first Daily", "Open your Profile Showcase"),
        )

    def next_actions(self, completed_step_ids: set[str], active_session_id: str | None = None) -> list[str]:
        if active_session_id:
            return [f"Recover session {active_session_id}", "Claim protected rewards", "Return to Home Hub"]
        for step in self.STEPS:
            if step.id not in completed_step_ids:
                return [step.action_label, step.reward_preview, "Open Help Codex"]
        return ["Run Dungeon Raid", "Join a Clan", "Fight the World Boss"]
