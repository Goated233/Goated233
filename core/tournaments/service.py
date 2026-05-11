from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from math import ceil, log2

from core.limits import LimitReason, LimitResult, LimitViolation


class TournamentStatus(StrEnum):
    SIGNUPS = "signups"
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass
class TournamentState:
    id: str
    name: str
    game_id: str
    starts_at: datetime
    status: TournamentStatus = TournamentStatus.SIGNUPS
    participants: list[int] = field(default_factory=list)
    bracket: list[list[int | None]] = field(default_factory=list)
    rewards: dict = field(default_factory=dict)
    max_participants: int = 128
    signup_attempts: dict[int, datetime] = field(default_factory=dict)


class TournamentService:
    def create(self, tournament_id: str, name: str, game_id: str, starts_in_minutes: int = 60) -> TournamentState:
        return TournamentState(
            id=tournament_id,
            name=name,
            game_id=game_id,
            starts_at=datetime.now(UTC) + timedelta(minutes=starts_in_minutes),
            rewards={"winner": {"gems": 250, "title": "Tournament Champion"}, "participant": {"xp": 250}},
        )

    def signup(self, tournament: TournamentState, user_id: int) -> TournamentState:
        if tournament.status != TournamentStatus.SIGNUPS:
            raise ValueError("Tournament signups are closed")
        if user_id in tournament.participants:
            raise LimitViolation(LimitResult.block(LimitReason.DUPLICATE, "You are already signed up for this tournament."))
        if len(tournament.participants) >= tournament.max_participants:
            raise LimitViolation(LimitResult.block(LimitReason.CAPACITY, "This tournament bracket is full."))
        last_attempt = tournament.signup_attempts.get(user_id)
        now = datetime.now(UTC)
        if last_attempt and now - last_attempt < timedelta(seconds=10):
            raise LimitViolation(LimitResult.block(LimitReason.COOLDOWN, "Tournament signup is cooling down."))
        tournament.signup_attempts[user_id] = now
        tournament.participants.append(user_id)
        return tournament

    def generate_bracket(self, tournament: TournamentState) -> TournamentState:
        size = 2 ** ceil(log2(max(2, len(tournament.participants))))
        padded = [*tournament.participants, *([None] * (size - len(tournament.participants)))]
        tournament.bracket = [padded[index : index + 2] for index in range(0, size, 2)]
        tournament.status = TournamentStatus.ACTIVE
        return tournament

    def leaderboard(self, tournament: TournamentState) -> list[tuple[int, int]]:
        return [(index + 1, user_id) for index, user_id in enumerate(tournament.participants)]
