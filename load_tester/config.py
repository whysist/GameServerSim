from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Optional

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def _default_scenario_weights() -> dict:
    return {
        "normal_player": 70,
        "competitive_player": 20,
        "reconnecting_player": 10,
    }


@dataclass
class LoadTestConfig:
    server_url: str = "http://127.0.0.1:8000"

    # How long the test runs. Players keep starting new games until this
    # deadline; a game already in progress is allowed to finish.
    duration_seconds: int = 30

    # Players are started evenly over this window instead of all at once.
    ramp_up_seconds: int = 10

    player_count: int = 10

    # Player counts for scripts that run several tests in a row.
    player_counts: list = field(default_factory=lambda: [10])

    min_action_delay_ms: int = 50
    max_action_delay_ms: int = 500

    min_actions: int = 5
    max_actions: int = 15

    # Relative weights for the player-type mix. Keys must match the
    # scenario names in load_tester/scenarios.py.
    scenario_weights: dict = field(
        default_factory=_default_scenario_weights
    )

    # Optional seed so the same config assigns the same player types to
    # the same player IDs. Action sequences and timings still vary,
    # because concurrent players interleave differently on every run.
    seed: Optional[int] = None

    results_dir: str = "results"
    raw_metrics_path: str = "results/metrics.csv"

    @classmethod
    def from_yaml(
        cls,
        path: Optional[str] = None,
        **overrides,
    ) -> "LoadTestConfig":
        """
        Build a config from config.yaml. Settings missing from the file
        keep their defaults; keyword arguments override both.
        """

        config_path = Path(path) if path else DEFAULT_CONFIG_PATH

        with open(config_path) as file:
            raw = yaml.safe_load(file) or {}

        values = {}

        server = raw.get("server", {})
        if "host" in server or "port" in server:
            host = server.get("host", "127.0.0.1")
            port = server.get("port", 8000)
            values["server_url"] = f"http://{host}:{port}"

        load_test = raw.get("load_test", {})
        for key in (
            "duration_seconds",
            "ramp_up_seconds",
            "player_counts",
            "seed",
        ):
            if key in load_test:
                values[key] = load_test[key]

        player = raw.get("player", {})
        action_count = player.get("action_count", {})
        if "min" in action_count:
            values["min_actions"] = action_count["min"]
        if "max" in action_count:
            values["max_actions"] = action_count["max"]

        action_delay = player.get("action_delay_ms", {})
        if "min" in action_delay:
            values["min_action_delay_ms"] = action_delay["min"]
        if "max" in action_delay:
            values["max_action_delay_ms"] = action_delay["max"]

        scenarios = raw.get("scenarios")
        if scenarios:
            values["scenario_weights"] = {
                name: settings.get("weight", 0)
                for name, settings in scenarios.items()
            }

        output = raw.get("output", {})
        if "directory" in output:
            values["results_dir"] = output["directory"]
        if "raw_metrics" in output:
            values["raw_metrics_path"] = output["raw_metrics"]

        known = {f.name for f in fields(cls)}
        unknown = set(overrides) - known
        if unknown:
            raise TypeError(
                f"Unknown config override(s): {sorted(unknown)}"
            )

        values.update(overrides)

        config = cls(**values)
        config.validate()

        return config

    def validate(self) -> None:

        # Imported here to avoid a circular import.
        from load_tester.scenarios import SCENARIOS

        unknown = set(self.scenario_weights) - set(SCENARIOS)
        if unknown:
            raise ValueError(
                f"Unknown scenario(s) in config: {sorted(unknown)}. "
                f"Known scenarios: {sorted(SCENARIOS)}"
            )

        if any(w < 0 for w in self.scenario_weights.values()):
            raise ValueError("Scenario weights cannot be negative.")

        if sum(self.scenario_weights.values()) <= 0:
            raise ValueError("At least one scenario needs a weight above 0.")

        if self.min_actions > self.max_actions:
            raise ValueError("player.action_count.min is above max.")

        if self.min_action_delay_ms > self.max_action_delay_ms:
            raise ValueError("player.action_delay_ms.min is above max.")
