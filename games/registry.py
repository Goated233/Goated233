from games.blackjack.definition import BLACKJACK
from games.boss_battle.definition import BOSS_BATTLE
from games.dungeon_raid.definition import DUNGEON_RAID
from games.empire_conquest.definition import EMPIRE_CONQUEST
from games.mafia.definition import MAFIA
from games.expanded_registry import EXPANDED_GAMES
from games.content_expansion import MMO_EXPANSION_GAMES

STARTER_GAMES = [DUNGEON_RAID, BLACKJACK, MAFIA, BOSS_BATTLE, EMPIRE_CONQUEST]
ALL_GAMES = [*STARTER_GAMES, *EXPANDED_GAMES, *MMO_EXPANSION_GAMES]
