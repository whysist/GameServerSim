import asyncio

from load_tester.config import LoadTestConfig
from load_tester.metrics import MetricsCollector
from load_tester.player import VirtualPlayer


class LoadTestRunner:

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.metrics = MetricsCollector()

    async def run(self):

        print(
            f"Starting load test with "
            f"{self.config.player_count} players"
        )

        players = [
            VirtualPlayer(
                player_id=player_id,
                server_url=self.config.server_url,
                metrics=self.metrics,
                min_action_delay_ms=(
                    self.config.min_action_delay_ms
                ),
                max_action_delay_ms=(
                    self.config.max_action_delay_ms
                ),
                min_actions=self.config.min_actions,
                max_actions=self.config.max_actions,
            )
            for player_id in range(
                1,
                self.config.player_count + 1
            )
        ]

        start_time = asyncio.get_event_loop().time()

        await asyncio.gather(
            *[
                player.play()
                for player in players
            ]
        )

        elapsed = (
            asyncio.get_event_loop().time()
            - start_time
        )

        total_requests = len(
            self.metrics.get_metrics()
        )

        print(
            f"Load test completed in "
            f"{elapsed:.2f} seconds"
        )

        print(
            f"Total requests: "
            f"{total_requests}"
        )

        print(
            f"Requests/sec: "
            f"{total_requests / elapsed:.2f}"
        )

        return self.metrics, elapsed