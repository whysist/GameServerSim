import sys
from pathlib import Path

# Add project root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import asyncio

from load_tester.config import LoadTestConfig
from load_tester.runner import LoadTestRunner


async def main():

    # Settings come from config.yaml.
    config = LoadTestConfig.from_yaml(
        player_count=10,
    )

    runner = LoadTestRunner(config)

    metrics = await runner.run()

    metrics.save_csv(
        "results/metrics.csv"
    )


if __name__ == "__main__":
    asyncio.run(main())