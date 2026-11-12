import asyncio
import random
import time
from typing import Optional

import httpx

from load_tester.metrics import MetricsCollector
from load_tester.scenarios import (
    NormalPlayerScenario,
    Scenario,
)


class VirtualPlayer:

    def __init__(
        self,
        player_id: int,
        server_url: str,
        metrics: MetricsCollector,
        min_action_delay_ms: int = 50,
        max_action_delay_ms: int = 500,
        min_actions: int = 5,
        max_actions: int = 15,
        scenario: Optional[Scenario] = None,
    ):
        self.player_id = player_id
        self.server_url = server_url
        self.metrics = metrics

        self.min_action_delay_ms = min_action_delay_ms
        self.max_action_delay_ms = max_action_delay_ms

        self.scenario = scenario or NormalPlayerScenario(
            min_actions=min_actions,
            max_actions=max_actions,
        )

        self.match_id = None

    async def request(
        self,
        client: httpx.AsyncClient,
        method: str,
        endpoint: str,
        **kwargs,
    ):
        start = time.perf_counter()

        try:
            response = await client.request(
                method,
                f"{self.server_url}{endpoint}",
                **kwargs,
            )

            latency_ms = (
                time.perf_counter() - start
            ) * 1000

            self.metrics.record(
                player_id=self.player_id,
                scenario=self.scenario.name,
                endpoint=endpoint,
                latency_ms=latency_ms,
                status_code=response.status_code,
                success=response.is_success,
            )

            if not response.is_success:
                return None

            return response

        except Exception as error:

            latency_ms = (
                time.perf_counter() - start
            ) * 1000

            self.metrics.record(
                player_id=self.player_id,
                scenario=self.scenario.name,
                endpoint=endpoint,
                latency_ms=latency_ms,
                status_code=0,
                success=False,
                # Some exceptions (e.g. httpx timeouts) have an empty
                # message, so always record the exception type too.
                error=f"{type(error).__name__}: {error}".rstrip(": "),
            )

            return None

    async def login(self, client):
        return await self.request(
            client,
            "POST",
            "/login",
            json={
                "player_id": self.player_id
            },
        )

    async def get_profile(self, client):
        return await self.request(
            client,
            "GET",
            f"/profile/{self.player_id}",
        )

    async def matchmaking(self, client):

        response = await self.request(
            client,
            "POST",
            "/matchmaking",
            json={
                "player_id": self.player_id
            },
        )

        if response:
            data = response.json()
            self.match_id = data.get("match_id")

        return response

    async def start_game(self, client):

        if not self.match_id:
            return None

        return await self.request(
            client,
            "POST",
            "/game/start",
            json={
                "player_id": self.player_id,
                "match_id": self.match_id,
            },
        )

    async def player_action(
        self,
        client,
        action: str,
    ):
        return await self.request(
            client,
            "POST",
            "/game/action",
            json={
                "player_id": self.player_id,
                "action": action,
            },
        )

    async def end_game(self, client):

        if not self.match_id:
            return None

        return await self.request(
            client,
            "POST",
            "/game/end",
            json={
                "player_id": self.player_id,
                "match_id": self.match_id,
            },
        )

    async def reconnect(self, client):

        return await self.request(
            client,
            "POST",
            "/reconnect",
            json={
                "player_id": self.player_id
            },
        )

    async def play(
        self,
        start_delay: float = 0.0,
        deadline: Optional[float] = None,
    ):
        """
        Run this player's session.

        start_delay: seconds to wait before logging in (used for ramp-up).
        deadline:    event-loop time after which no new game is started.
                     None means play exactly one game.
        """

        if start_delay > 0:
            await asyncio.sleep(start_delay)

        loop = asyncio.get_running_loop()

        async with httpx.AsyncClient() as client:

            # 1. Login
            response = await self.login(client)

            if response is None:
                return

            # 2. Fetch profile
            response = await self.get_profile(client)

            if response is None:
                return

            # 3+. Play games until the deadline (or once if no deadline).
            while True:

                completed = await self.play_one_game(client)

                if deadline is None or loop.time() >= deadline:
                    break

                if not completed:
                    # Back off briefly so a failing server isn't hammered
                    # by a tight retry loop.
                    await asyncio.sleep(1.0)

    async def play_one_game(self, client) -> bool:
        """Play a single game. Returns True if it reached game end."""

        self.match_id = None

        # 3. Enter matchmaking
        response = await self.matchmaking(client)

        if response is None:
            return False

        # Small delay before game starts
        await asyncio.sleep(
            random.uniform(0.1, 0.5)
        )

        # 4. Start game
        response = await self.start_game(client)

        if response is None:
            return False

        # 5. Perform gameplay actions
        actions = self.scenario.get_actions()

        # Reconnecting players may drop mid-game: pick the point in the
        # game (after which action) where the reconnect happens.
        reconnect_after = None
        if actions and self.scenario.should_reconnect():
            reconnect_after = random.randrange(len(actions))

        for index, action in enumerate(actions):

            await self.player_action(
                client,
                action,
            )

            if index == reconnect_after:
                # 6. Simulated drop and reconnect mid-game
                await self.reconnect(client)

            delay = random.uniform(
                self.min_action_delay_ms,
                self.max_action_delay_ms,
            )

            await asyncio.sleep(
                delay / 1000
            )

        # 7. End game
        response = await self.end_game(client)

        return response is not None