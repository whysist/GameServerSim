import asyncio
import random
import time

import httpx

from load_tester.metrics import MetricsCollector
from load_tester.scenarios import (
    NormalPlayerScenario,
    CompetitivePlayerScenario,
    ReconnectingPlayerScenario,
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
    ):
        self.player_id = player_id
        self.server_url = server_url
        self.metrics = metrics

        self.min_action_delay_ms = min_action_delay_ms
        self.max_action_delay_ms = max_action_delay_ms

        self.scenario = NormalPlayerScenario(
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
                endpoint=endpoint,
                latency_ms=latency_ms,
                status_code=0,
                success=False,
                error=str(error),
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

    async def play(self):

        async with httpx.AsyncClient() as client:

            # 1. Login
            response = await self.login(client)

            if response is None:
                return

            # 2. Fetch profile
            response = await self.get_profile(client)

            if response is None:
                return

            # 3. Enter matchmaking
            response = await self.matchmaking(client)

            if response is None:
                return

            # Small delay before game starts
            await asyncio.sleep(
                random.uniform(0.1, 0.5)
            )

            # 4. Start game
            response = await self.start_game(client)

            if response is None:
                return

            # 5. Perform gameplay actions
            actions = self.scenario.get_actions()

            for action in actions:

                await self.player_action(
                    client,
                    action,
                )

                delay = random.uniform(
                    self.min_action_delay_ms,
                    self.max_action_delay_ms,
                )

                await asyncio.sleep(
                    delay / 1000
                )

            # 6. Occasionally simulate reconnect
            if isinstance(
                self.scenario,
                ReconnectingPlayerScenario,
            ):
                if self.scenario.should_reconnect():
                    await self.reconnect(client)

            # 7. End game
            await self.end_game(client)