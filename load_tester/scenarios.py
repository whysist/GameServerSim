import random


class NormalPlayerScenario:

    def __init__(self, min_actions=5, max_actions=15):
        self.min_actions = min_actions
        self.max_actions = max_actions

    def get_actions(self):
        action_count = random.randint(
            self.min_actions,
            self.max_actions,
        )

        possible_actions = [
            "move",
            "shoot",
            "jump",
            "reload",
            "interact",
        ]

        return [
            random.choice(possible_actions)
            for _ in range(action_count)
        ]


class CompetitivePlayerScenario:

    def __init__(self):
        pass

    def get_actions(self):
        action_count = random.randint(15, 30)

        possible_actions = [
            "move",
            "shoot",
            "shoot",
            "reload",
            "interact",
        ]

        return [
            random.choice(possible_actions)
            for _ in range(action_count)
        ]


class ReconnectingPlayerScenario:

    def __init__(self):
        pass

    def get_actions(self):
        action_count = random.randint(5, 10)

        possible_actions = [
            "move",
            "shoot",
            "jump",
        ]

        return [
            random.choice(possible_actions)
            for _ in range(action_count)
        ]

    def should_reconnect(self):
        return random.random() < 0.3