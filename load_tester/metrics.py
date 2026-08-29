import csv
import os
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class RequestMetric:
    timestamp: str
    player_id: int
    endpoint: str
    latency_ms: float
    status_code: int
    success: bool
    error: str = ""


class MetricsCollector:

    def __init__(self):
        self.metrics: list[RequestMetric] = []

    def record(
        self,
        player_id: int,
        endpoint: str,
        latency_ms: float,
        status_code: int,
        success: bool,
        error: str = "",
    ):
        metric = RequestMetric(
            timestamp=datetime.now().isoformat(),
            player_id=player_id,
            endpoint=endpoint,
            latency_ms=latency_ms,
            status_code=status_code,
            success=success,
            error=error,
        )

        self.metrics.append(metric)

    def save_csv(self, filepath: str):
        directory = os.path.dirname(filepath)

        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(filepath, "w", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=RequestMetric.__dataclass_fields__.keys(),
            )

            writer.writeheader()

            for metric in self.metrics:
                writer.writerow(asdict(metric))

        print(f"Saved {len(self.metrics)} metrics to {filepath}")

    def get_metrics(self):
        return self.metrics