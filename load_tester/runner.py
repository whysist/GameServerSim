import asyncio
from collections import Counter

from load_tester.config import LoadTestConfig
from load_tester.limits import ensure_fd_limit
from load_tester.metrics import MetricsCollector
from load_tester.player import VirtualPlayer


class LoadTestRunner:

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.metrics = MetricsCollector()

    async def run(self):

        ensure_fd_limit(self.config.player_count)

        print(
            f"Starting load test with "
            f"{self.config.player_count} players "
            f"(ramp-up {self.config.ramp_up_seconds}s, "
            f"duration {self.config.duration_seconds}s)"
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

        loop = asyncio.get_running_loop()

        start_time = loop.time()

        # Players stop starting new games after this point.
        deadline = start_time + self.config.duration_seconds

        # Spread player start times evenly across the ramp-up window.
        ramp_step = (
            self.config.ramp_up_seconds / self.config.player_count
            if self.config.player_count > 0
            else 0
        )

        # return_exceptions=True: one player crashing (e.g. running out of
        # file descriptors) must not abort every other player's session.
        outcomes = await asyncio.gather(
            *[
                player.play(
                    start_delay=index * ramp_step,
                    deadline=deadline,
                )
                for index, player in enumerate(players)
            ],
            return_exceptions=True,
        )

        crashed = [
            outcome
            for outcome in outcomes
            if isinstance(outcome, BaseException)
        ]

        if crashed:
            reasons = Counter(
                f"{type(error).__name__}: {error}"
                for error in crashed
            )
            print(
                f"WARNING: {len(crashed)} of {len(players)} players "
                f"crashed inside the load generator:"
            )
            for reason, count in reasons.most_common(5):
                print(f"  {count} x {reason}")

        elapsed = loop.time() - start_time

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
