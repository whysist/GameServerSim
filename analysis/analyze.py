import pandas as pd


def load_metrics(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)

    if df.empty:
        raise ValueError("Metrics file is empty.")

    return df
def calculate_throughput(df):
    if df.empty:
        return 0.0

    start = pd.to_datetime(df["timestamp"]).min()
    end = pd.to_datetime(df["timestamp"]).max()

    duration_seconds = (
        end - start
    ).total_seconds()

    if duration_seconds <= 0:
        return float(len(df))

    return len(df) / duration_seconds

def calculate_summary(df: pd.DataFrame) -> dict:

    total_requests = len(df)

    successful_requests = df["success"].sum()

    failed_requests = total_requests - successful_requests

    success_rate = (
        successful_requests / total_requests
    ) * 100

    error_rate = (
        failed_requests / total_requests
    ) * 100

    latency = df["latency_ms"]

    return {
        "total_requests": total_requests,
        "successful_requests": int(successful_requests),
        "failed_requests": int(failed_requests),
        "success_rate": success_rate,
        "error_rate": error_rate,
        "mean_latency_ms": latency.mean(),
        "p50_latency_ms": latency.quantile(0.50),
        "p95_latency_ms": latency.quantile(0.95),
        "p99_latency_ms": latency.quantile(0.99),
    }


def calculate_endpoint_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

    summary = (
        df.groupby("endpoint")
        .agg(
            requests=("endpoint", "count"),
            mean_latency_ms=("latency_ms", "mean"),
            p50_latency_ms=(
                "latency_ms",
                lambda x: x.quantile(0.50),
            ),
            p95_latency_ms=(
                "latency_ms",
                lambda x: x.quantile(0.95),
            ),
            p99_latency_ms=(
                "latency_ms",
                lambda x: x.quantile(0.99),
            ),
            errors=("success", lambda x: (~x).sum()),
        )
        .reset_index()
    )

    summary["error_rate"] = (
        summary["errors"]
        / summary["requests"]
        * 100
    )

    return summary


def print_summary(summary: dict):

    print("\n========== LOAD TEST SUMMARY ==========\n")

    print(
        f"Total requests:      "
        f"{summary['total_requests']}"
    )

    print(
        f"Successful requests: "
        f"{summary['successful_requests']}"
    )

    print(
        f"Failed requests:     "
        f"{summary['failed_requests']}"
    )

    print(
        f"Success rate:        "
        f"{summary['success_rate']:.2f}%"
    )

    print(
        f"Error rate:          "
        f"{summary['error_rate']:.2f}%"
    )

    print(
        f"Mean latency:        "
        f"{summary['mean_latency_ms']:.2f} ms"
    )

    print(
        f"P50 latency:         "
        f"{summary['p50_latency_ms']:.2f} ms"
    )

    print(
        f"P95 latency:         "
        f"{summary['p95_latency_ms']:.2f} ms"
    )

    print(
        f"P99 latency:         "
        f"{summary['p99_latency_ms']:.2f} ms"
    )
    throughput = calculate_throughput(df)

    print(
        f"Requests/sec:       "
        f"{throughput:.2f}"
    )

    print("\n========================================\n")


if __name__ == "__main__":

    filepath = "results/metrics.csv"

    df = load_metrics(filepath)

    summary = calculate_summary(df)

    print_summary(summary)

    endpoint_summary = calculate_endpoint_summary(df)

    print("Endpoint performance:\n")

    print(
        endpoint_summary.to_string(
            index=False
        )
    )

    endpoint_summary.to_csv(
        "results/endpoint_summary.csv",
        index=False,
    )