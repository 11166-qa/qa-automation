import csv
import re
from pathlib import Path


RESULTS_DIR = Path(__file__).resolve().parent / "results"

SCENARIO_NAMES = {
    "A": "Authenticated GET Items",
    "B": "Create + Get Item",
    "C": "Mixed CRUD 5:2:2:1",
}


def get_value(row, *possible_names):
    """
    兼容不同 Locust 版本的 CSV 列名。
    """
    for name in possible_names:
        if name in row:
            return row[name]
    return ""


def to_float(value):
    if value is None:
        return 0.0

    value = str(value).strip()

    if not value:
        return 0.0

    try:
        return float(value)
    except ValueError:
        return 0.0


def load_csv(path):
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def parse_result_file(path):
    """
    从文件名提取：
    A_10_stats.csv
       ↓
    scenario = A
    concurrency = 10
    """

    match = re.fullmatch(
        r"([ABC])_(\d+)_stats\.csv",
        path.name,
    )

    if not match:
        return None

    scenario_code = match.group(1)
    concurrency = int(match.group(2))

    rows = load_csv(path)

    if not rows:
        raise RuntimeError(
            f"CSV file is empty: {path}"
        )

    aggregate_row = None

    for row in rows:
        if row.get("Name", "").strip() == "Aggregated":
            aggregate_row = row
            break

    if aggregate_row is None:
        raise RuntimeError(
            f"Aggregated row not found: {path}"
        )

    request_count = int(
        to_float(
            get_value(
                aggregate_row,
                "Request Count",
                "# Requests",
            )
        )
    )

    failure_count = int(
        to_float(
            get_value(
                aggregate_row,
                "Failure Count",
                "# Fails",
            )
        )
    )

    if request_count > 0:
        failure_rate = (
            failure_count
            / request_count
            * 100
        )
    else:
        failure_rate = 0.0

    summary = {
        "scenario_code": scenario_code,
        "scenario": SCENARIO_NAMES[
            scenario_code
        ],
        "concurrency": concurrency,
        "request_count": request_count,
        "failure_count": failure_count,
        "failure_rate_pct": round(
            failure_rate,
            4,
        ),
        "rps": round(
            to_float(
                get_value(
                    aggregate_row,
                    "Requests/s",
                    "Current RPS",
                )
            ),
            2,
        ),
        "average_ms": round(
            to_float(
                get_value(
                    aggregate_row,
                    "Average Response Time",
                    "Average (ms)",
                )
            ),
            2,
        ),
        "median_ms": round(
            to_float(
                get_value(
                    aggregate_row,
                    "Median Response Time",
                    "Median (ms)",
                )
            ),
            2,
        ),
        "p95_ms": round(
            to_float(
                get_value(
                    aggregate_row,
                    "95%",
                    "95%ile (ms)",
                )
            ),
            2,
        ),
        "p99_ms": round(
            to_float(
                get_value(
                    aggregate_row,
                    "99%",
                    "99%ile (ms)",
                )
            ),
            2,
        ),
        "max_ms": round(
            to_float(
                get_value(
                    aggregate_row,
                    "Max Response Time",
                    "Max (ms)",
                )
            ),
            2,
        ),
    }

    endpoint_rows = []

    for row in rows:
        name = row.get(
            "Name",
            "",
        ).strip()

        if not name:
            continue

        if name == "Aggregated":
            continue

        requests = int(
            to_float(
                get_value(
                    row,
                    "Request Count",
                    "# Requests",
                )
            )
        )

        failures = int(
            to_float(
                get_value(
                    row,
                    "Failure Count",
                    "# Fails",
                )
            )
        )

        if requests > 0:
            endpoint_failure_rate = (
                failures
                / requests
                * 100
            )
        else:
            endpoint_failure_rate = 0.0

        endpoint_rows.append(
            {
                "scenario_code": scenario_code,
                "scenario": SCENARIO_NAMES[
                    scenario_code
                ],
                "concurrency": concurrency,
                "method": row.get(
                    "Type",
                    "",
                ),
                "name": name,
                "request_count": requests,
                "failure_count": failures,
                "failure_rate_pct": round(
                    endpoint_failure_rate,
                    4,
                ),
                "rps": round(
                    to_float(
                        get_value(
                            row,
                            "Requests/s",
                            "Current RPS",
                        )
                    ),
                    2,
                ),
                "average_ms": round(
                    to_float(
                        get_value(
                            row,
                            "Average Response Time",
                            "Average (ms)",
                        )
                    ),
                    2,
                ),
                "median_ms": round(
                    to_float(
                        get_value(
                            row,
                            "Median Response Time",
                            "Median (ms)",
                        )
                    ),
                    2,
                ),
                "p95_ms": round(
                    to_float(
                        get_value(
                            row,
                            "95%",
                            "95%ile (ms)",
                        )
                    ),
                    2,
                ),
                "p99_ms": round(
                    to_float(
                        get_value(
                            row,
                            "99%",
                            "99%ile (ms)",
                        )
                    ),
                    2,
                ),
                "max_ms": round(
                    to_float(
                        get_value(
                            row,
                            "Max Response Time",
                            "Max (ms)",
                        )
                    ),
                    2,
                ),
            }
        )

    return summary, endpoint_rows


def write_csv(path, rows, fieldnames):
    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def write_markdown(summary_rows):
    path = RESULTS_DIR / "performance_summary.md"

    lines = [
        "# Performance Test Summary",
        "",
        "| Scenario | Concurrency | Requests | Failures | Failure Rate | RPS | Avg (ms) | Median (ms) | P95 (ms) | P99 (ms) | Max (ms) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in summary_rows:
        lines.append(
            "| "
            f"{row['scenario_code']} - "
            f"{row['scenario']} | "
            f"{row['concurrency']} | "
            f"{row['request_count']} | "
            f"{row['failure_count']} | "
            f"{row['failure_rate_pct']:.2f}% | "
            f"{row['rps']:.2f} | "
            f"{row['average_ms']:.2f} | "
            f"{row['median_ms']:.2f} | "
            f"{row['p95_ms']:.2f} | "
            f"{row['p99_ms']:.2f} | "
            f"{row['max_ms']:.2f} |"
        )

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return path


def main():
    if not RESULTS_DIR.exists():
        raise RuntimeError(
            f"Results directory does not exist: "
            f"{RESULTS_DIR}"
        )

    expected_files = []

    for scenario in ["A", "B", "C"]:
        for concurrency in [10, 50, 100]:
            expected_files.append(
                RESULTS_DIR
                / (
                    f"{scenario}_"
                    f"{concurrency}_stats.csv"
                )
            )

    missing_files = [
        path
        for path in expected_files
        if not path.exists()
    ]

    if missing_files:
        print(
            "WARNING: Missing performance files:"
        )

        for path in missing_files:
            print(
                f"  - {path.name}"
            )

        print()

    summary_rows = []
    endpoint_rows = []

    for path in expected_files:
        if not path.exists():
            continue

        result = parse_result_file(path)

        if result is None:
            continue

        summary, endpoints = result

        summary_rows.append(summary)
        endpoint_rows.extend(endpoints)

    summary_rows.sort(
        key=lambda row: (
            row["scenario_code"],
            row["concurrency"],
        )
    )

    endpoint_rows.sort(
        key=lambda row: (
            row["scenario_code"],
            row["concurrency"],
            row["name"],
        )
    )

    summary_path = (
        RESULTS_DIR
        / "performance_summary.csv"
    )

    endpoint_path = (
        RESULTS_DIR
        / "performance_endpoints.csv"
    )

    write_csv(
        summary_path,
        summary_rows,
        [
            "scenario_code",
            "scenario",
            "concurrency",
            "request_count",
            "failure_count",
            "failure_rate_pct",
            "rps",
            "average_ms",
            "median_ms",
            "p95_ms",
            "p99_ms",
            "max_ms",
        ],
    )

    write_csv(
        endpoint_path,
        endpoint_rows,
        [
            "scenario_code",
            "scenario",
            "concurrency",
            "method",
            "name",
            "request_count",
            "failure_count",
            "failure_rate_pct",
            "rps",
            "average_ms",
            "median_ms",
            "p95_ms",
            "p99_ms",
            "max_ms",
        ],
    )

    markdown_path = write_markdown(
        summary_rows
    )

    print()
    print("=" * 90)
    print("PERFORMANCE TEST SUMMARY")
    print("=" * 90)

    header = (
        f"{'Scene':<7}"
        f"{'Users':>7}"
        f"{'RPS':>10}"
        f"{'Avg(ms)':>12}"
        f"{'P95(ms)':>12}"
        f"{'P99(ms)':>12}"
        f"{'Fail%':>10}"
    )

    print(header)
    print("-" * 90)

    for row in summary_rows:
        print(
            f"{row['scenario_code']:<7}"
            f"{row['concurrency']:>7}"
            f"{row['rps']:>10.2f}"
            f"{row['average_ms']:>12.2f}"
            f"{row['p95_ms']:>12.2f}"
            f"{row['p99_ms']:>12.2f}"
            f"{row['failure_rate_pct']:>10.2f}"
        )

    print("=" * 90)

    print()
    print(
        f"Summary CSV: {summary_path}"
    )

    print(
        f"Endpoint CSV: {endpoint_path}"
    )

    print(
        f"Markdown report: {markdown_path}"
    )

    failures_found = [
        row
        for row in summary_rows
        if row["failure_count"] > 0
    ]

    if failures_found:
        print()
        print(
            "WARNING: Some formal runs "
            "contain failures:"
        )

        for row in failures_found:
            print(
                f"  {row['scenario_code']}-"
                f"{row['concurrency']}: "
                f"{row['failure_count']} failures "
                f"({row['failure_rate_pct']:.2f}%)"
            )
    else:
        print()
        print(
            "All formal performance runs "
            "completed with 0 recorded failures."
        )


if __name__ == "__main__":
    main()