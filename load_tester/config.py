from dataclasses import dataclass


@dataclass
class LoadTestConfig:
    server_url: str = "http://127.0.0.1:8000"

    # How long the test runs. Players keep starting new games until this
    # deadline; a game already in progress is allowed to finish.
    duration_seconds: int = 30

    # Players are started evenly over this window instead of all at once.
    ramp_up_seconds: int = 10

    player_count: int = 10

    min_action_delay_ms: int = 50
    max_action_delay_ms: int = 500

    min_actions: int = 5
    max_actions: int = 15
