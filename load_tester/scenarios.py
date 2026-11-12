import random


class Scenario:
    """
    A player type: which actions a player takes in a game, and whether
    it drops and reconnects mid-game.
    """

    name = "base"

    # Chance per game that the player reconnects mid-game.
    reconnect_probability = 0.0

    possible_actions = ["move"]

    def __init__(self, min_actions: int, max_actions: int):
        self.min_actions = min_actions
        self.max_actions = max_actions

    def get_actions(self):
        action_count = random.randint(
            self.min_actions,
            self.max_actions,
        )

        return [
            random.choice(self.possible_actions)
            for _ in range(action_count)
        ]

    def should_reconnect(self):
        return random.random() < self.reconnect_probability


class NormalPlayerScenario(Scenario):
    """Casual player. Action count comes from config.yaml."""

    name = "normal_player"

    possible_actions = [
        "move",
        "shoot",
        "jump",
        "reload",
        "interact",
    ]

    def __init__(self, min_actions=5, max_actions=15):
        super().__init__(min_actions, max_actions)


class CompetitivePlayerScenario(Scenario):
    """Plays longer, busier games with more shooting."""

    name = "competitive_player"

    possible_actions = [
        "move",
        "shoot",
        "shoot",
        "reload",
        "interact",
    ]

    def __init__(self, min_actions=15, max_actions=30):
        super().__init__(min_actions, max_actions)


class ReconnectingPlayerScenario(Scenario):
    """Short games on a flaky connection; sometimes reconnects mid-game."""

    name = "reconnecting_player"

    reconnect_probability = 0.3

    possible_actions = [
        "move",
        "shoot",
        "jump",
    ]

    def __init__(self, min_actions=5, max_actions=10):
        super().__init__(min_actions, max_actions)


SCENARIOS = {
    scenario.name: scenario
    for scenario in (
        NormalPlayerScenario,
        CompetitivePlayerScenario,
        ReconnectingPlayerScenario,
    )
}


def create_scenario(
    name: str,
    min_actions: int,
    max_actions: int,
) -> Scenario:
    """
    Build a scenario by name. Only the normal player takes its action
    count from config; the other types keep their own ranges, since a
    different action count is what defines them.
    """

    if name == NormalPlayerScenario.name:
        return NormalPlayerScenario(min_actions, max_actions)

    return SCENARIOS[name]()


def assign_scenarios(
    player_count: int,
    weights: dict,
    rng: random.Random,
) -> list:
    """
    Return one scenario name per player, matching the weights as
    closely as whole numbers allow (largest-remainder rounding), in a
    shuffled order. With weights 70/20/10 and 100 players this gives
    exactly 70/20/10, rather than a random draw that can drift.
    """

    active = {
        name: weight
        for name, weight in weights.items()
        if weight > 0
    }

    total = sum(active.values())

    exact = {
        name: player_count * weight / total
        for name, weight in active.items()
    }

    counts = {
        name: int(share)
        for name, share in exact.items()
    }

    leftover = player_count - sum(counts.values())

    by_remainder = sorted(
        exact,
        key=lambda name: exact[name] - counts[name],
        reverse=True,
    )

    for name in by_remainder[:leftover]:
        counts[name] += 1

    names = [
        name
        for name, count in counts.items()
        for _ in range(count)
    ]

    rng.shuffle(names)

    return names
