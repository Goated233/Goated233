from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class EconomyGrant:
    currency: str
    amount: int
    reason: str
    idempotency_key: str
    metadata: dict


class EconomyBalancer:
    def reward_cap(self, user_level: int, game_id: str, base_amount: int) -> int:
        multiplier = 1 + min(user_level, 100) * 0.025
        game_ceiling = 12_000 if game_id in {"boss_battle", "empire_conquest"} else 4_500
        return min(round(base_amount * multiplier), game_ceiling)

    def sink_price(self, base_price: int, rarity: str, inflation_index: float) -> int:
        rarity_multiplier = {"common": 1, "uncommon": 1.35, "rare": 2.1, "epic": 3.8, "legendary": 7.5, "mythic": 12}.get(rarity, 1)
        return round(base_price * rarity_multiplier * max(1.0, inflation_index))

    def idempotency_key(self, user_id: int, source: str, nonce: str) -> str:
        return sha256(f"{user_id}:{source}:{nonce}".encode()).hexdigest()

    def verify_grant(self, grant: EconomyGrant) -> bool:
        return grant.amount != 0 and len(grant.idempotency_key) >= 32 and grant.currency in {"coins", "gems", "xp"}
