import asyncio
import os

import sys
from pathlib import Path

# Add project root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))


from load_tester.config import LoadTestConfig
from load_tester.runner import LoadTestRunner


RESULTS_DIR = "results"


EXPERIMENTS = {
    "baseline": [
        10,
        50,
        100,
    ],

    "peak": [
        100,
        250,
        500,
        1000,
    ],

    "stress": [
        1000,
        1500,
        2000,
        3000,
    ],
}


async def run_experiment(
    experiment_name: str,
    player_counts: list[int],
):

    print("\n")
    print("=" * 60)
    print(f"EXPERIMENT: {experiment_name.upper()}")
    print("=" * 60)

    experiment_dir = os.path.join(
        RESULTS_DIR,
        experiment_name,
    )

    os.makedirs(
        experiment_dir,
        exist_ok=True,
    )

    for player_count in player_counts:

        print("\n")
        print("-" * 60)
        print(
            f"{experiment_name.upper()} TEST: "
            f"{player_count} PLAYERS"
        )
        print("-" * 60)

        config = LoadTestConfig(
            server_url="http://127.0.0.1:8000",
            player_count=player_count,
        )

        runner = LoadTestRunner(config)

        metrics, elapsed = await runner.run()

        output_file = os.path.join(
            experiment_dir,
            f"load_{player_count}.csv",
        )

        metrics.save_csv(output_file)

        print(
            f"Results saved to: "
            f"{output_file}"
        )

        # Small pause between experiments.
        await asyncio.sleep(2)


async def main():

    for experiment_name, player_counts in EXPERIMENTS.items():

        await run_experiment(
            experiment_name,
            player_counts,
        )

        # Longer pause between experiment categories.
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())