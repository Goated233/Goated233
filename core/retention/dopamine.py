from dataclasses import dataclass
from enum import StrEnum

from ui.branding.identity import RARITY_PALETTE


class CelebrationIntensity(StrEnum):
    SPARK = "spark"
    SURGE = "surge"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"


@dataclass(frozen=True)
class RewardReveal:
    title: str
    lines: tuple[str, ...]
    intensity: CelebrationIntensity
    color: int
    share_text: str
    next_hook: str


class DopamineService:
    def streak_reveal(self, streak_day: int, xp: int, coins: int, gems: int) -> RewardReveal:
        if streak_day % 30 == 0:
            intensity = CelebrationIntensity.MYTHIC
            title = "Monthly Streak Ascended"
        elif streak_day % 7 == 0:
            intensity = CelebrationIntensity.LEGENDARY
            title = "Weekly Streak Ignited"
        elif streak_day % 5 == 0:
            intensity = CelebrationIntensity.SURGE
            title = "Booster Spark Online"
        else:
            intensity = CelebrationIntensity.SPARK
            title = "Daily Flame Claimed"
        rarity = "mythic" if intensity == CelebrationIntensity.MYTHIC else "legendary" if intensity == CelebrationIntensity.LEGENDARY else "epic" if intensity == CelebrationIntensity.SURGE else "rare"
        lines = (
            f"🔥 Streak Day **{streak_day}** secured.",
            f"`+{xp:,} XP` · `+{coins:,} coins` · `+{gems:,} gems`",
            "Momentum preserved. The next login upgrades your reward track.",
        )
        return RewardReveal(title, lines, intensity, RARITY_PALETTE[rarity]["color"], f"I hit Streak Day {streak_day} in Alpha Omega Arcade.", "Open Quest Hub")

    def loot_reveal(self, item_name: str, rarity: str, source: str) -> RewardReveal:
        meta = RARITY_PALETTE.get(rarity, RARITY_PALETTE["rare"])
        intensity = CelebrationIntensity.MYTHIC if rarity == "mythic" else CelebrationIntensity.LEGENDARY if rarity == "legendary" else CelebrationIntensity.SURGE
        lines = (
            f"{meta['emoji']} **{item_name}** emerged from **{source}**.",
            f"Rarity: `{meta['label']}` · Showcase-ready collectible.",
            "Flex it from your profile or share the drop with your clan.",
        )
        return RewardReveal(f"{meta['label']} Loot Reveal", lines, intensity, meta["color"], f"{item_name} dropped for me in Alpha Omega Arcade.", "Open Inventory")

    def milestone_reveal(self, level: int, title: str) -> RewardReveal:
        rarity = "legendary" if level % 25 == 0 else "epic"
        meta = RARITY_PALETTE[rarity]
        return RewardReveal(
            "Progression Milestone",
            (f"Level **{level}** reached.", f"Title unlocked: **{title}**", "Your profile border pulses brighter across the Omega network."),
            CelebrationIntensity.LEGENDARY if rarity == "legendary" else CelebrationIntensity.SURGE,
            meta["color"],
            f"I reached Level {level} in Alpha Omega Arcade.",
            "Open Profile",
        )
