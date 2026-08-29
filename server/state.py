import random
import string


players = {}
matches = {}


def generate_match_id() -> str:
    return "match_" + "".join(
        random.choices(string.ascii_lowercase + string.digits, k=8)
    )


def create_player(player_id: int):
    players[player_id] = {
        "player_id": player_id,
        "status": "LOBBY",
        "match_id": None,
    }


def get_player(player_id: int):
    return players.get(player_id)


def create_match(player_id: int):
    match_id = generate_match_id()

    matches[match_id] = {
        "match_id": match_id,
        "players": [player_id],
        "status": "WAITING",
    }

    return match_id