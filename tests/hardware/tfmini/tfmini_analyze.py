"""TISHTAR - TFmini distance characterization analysis (TF-03, issue #28).

Reads the CSV written by ``tfmini_record.py`` and reports, per
(experiment, reference distance, material) group:

    frames, checksum-invalid, excluded, invalid-reading rate,
    mean, median, std, bias, MAE, RMSE, min, max, mean strength,
    suspect sentinel values (0 / 65535), host-side receive rate.

Terminology:
    raw frame          any 9-byte frame aligned on 0x59 0x59
    valid frame        raw frame whose checksum matches
    valid measurement  valid frame not excluded by --exclude-distance /
                       --min-strength. By default nothing beyond the checksum
                       is excluded, because the sensor's invalid-reading
                       convention for this exact variant is not yet verified.

Example:
    python tfmini_analyze.py results/tfmini_characterization.csv
    python tfmini_analyze.py data.csv --exclude-distance 0 65535 --min-strength 100
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

SENTINEL_CANDIDATES = (0, 65535)

SUMMARY_FIELDS = [
    "experiment_id", "reference_distance_cm", "target_material",
    "frames", "checksum_invalid", "excluded", "valid_measurements", "invalid_rate",
    "mean_cm", "median_cm", "std_cm", "bias_cm", "mae_cm", "rmse_cm",
    "min_cm", "max_cm", "mean_strength", "suspect_zero", "suspect_65535", "rate_hz",
]


@dataclass
class GroupSummary:
    experiment_id: str
    reference_distance_cm: float
    target_material: str
    frames: int
    checksum_invalid: int
    excluded: int
    valid_measurements: int
    invalid_rate: float
    mean_cm: float | None
    median_cm: float | None
    std_cm: float | None
    bias_cm: float | None
    mae_cm: float | None
    rmse_cm: float | None
    min_cm: int | None
    max_cm: int | None
    mean_strength: float | None
    suspect_zero: int
    suspect_65535: int
    rate_hz: float | None


def summarize_group(
    key: tuple[str, float, str],
    rows: list[dict[str, str]],
    exclude_distances: frozenset[int] = frozenset(),
    min_strength: int | None = None,
) -> GroupSummary:
    experiment_id, reference, material = key
    checksum_invalid = 0
    excluded = 0
    distances: list[int] = []
    strengths: list[int] = []
    times: list[float] = []
    suspect = {value: 0 for value in SENTINEL_CANDIDATES}

    for row in rows:
        if row["frame_valid"] != "1":
            checksum_invalid += 1
            continue
        distance = int(row["distance_cm"])
        strength = int(row["strength"])
        if distance in suspect:
            suspect[distance] += 1
        if distance in exclude_distances or (min_strength is not None and strength < min_strength):
            excluded += 1
            continue
        distances.append(distance)
        strengths.append(strength)
        times.append(float(row["elapsed_s"]))

    n = len(distances)
    frames = len(rows)
    summary = GroupSummary(
        experiment_id=experiment_id, reference_distance_cm=reference, target_material=material,
        frames=frames, checksum_invalid=checksum_invalid, excluded=excluded,
        valid_measurements=n,
        invalid_rate=(checksum_invalid + excluded) / frames if frames else 0.0,
        mean_cm=None, median_cm=None, std_cm=None, bias_cm=None, mae_cm=None, rmse_cm=None,
        min_cm=None, max_cm=None, mean_strength=None,
        suspect_zero=suspect[0], suspect_65535=suspect[65535], rate_hz=None,
    )
    if n == 0:
        return summary

    errors = [d - reference for d in distances]
    summary.mean_cm = statistics.fmean(distances)
    summary.median_cm = statistics.median(distances)
    summary.std_cm = statistics.stdev(distances) if n > 1 else 0.0
    summary.bias_cm = statistics.fmean(errors)
    summary.mae_cm = statistics.fmean(abs(e) for e in errors)
    summary.rmse_cm = math.sqrt(statistics.fmean(e * e for e in errors))
    summary.min_cm = min(distances)
    summary.max_cm = max(distances)
    summary.mean_strength = statistics.fmean(strengths)
    span = max(times) - min(times)
    summary.rate_hz = (n - 1) / span if n > 1 and span > 0 else None
    return summary


def group_rows(rows: Iterable[dict[str, str]]) -> dict[tuple[str, float, str], list[dict[str, str]]]:
    groups: dict[tuple[str, float, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (row["experiment_id"], float(row["reference_distance_cm"]), row["target_material"])
        groups[key].append(row)
    return dict(sorted(groups.items(), key=lambda item: (item[0][0], item[0][1], item[0][2])))


def analyze(
    rows: Iterable[dict[str, str]],
    exclude_distances: Iterable[int] = (),
    min_strength: int | None = None,
) -> list[GroupSummary]:
    excluded = frozenset(exclude_distances)
    return [summarize_group(k, v, excluded, min_strength) for k, v in group_rows(rows).items()]


def _fmt(value: object, digits: int = 2) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def print_table(summaries: list[GroupSummary]) -> None:
    columns = [
        ("ref", "reference_distance_cm"), ("frames", "frames"), ("crc_bad", "checksum_invalid"),
        ("excl", "excluded"), ("inv%", "invalid_rate"), ("mean", "mean_cm"), ("median", "median_cm"),
        ("std", "std_cm"), ("bias", "bias_cm"), ("MAE", "mae_cm"), ("RMSE", "rmse_cm"),
        ("min", "min_cm"), ("max", "max_cm"), ("strength", "mean_strength"), ("Hz", "rate_hz"),
    ]
    current = None
    for s in summaries:
        if (s.experiment_id, s.target_material) != current:
            current = (s.experiment_id, s.target_material)
            print(f"\nExperiment {s.experiment_id} | material: {s.target_material}  (distances in cm)")
            print(" ".join(f"{h:>8}" for h, _ in columns))
        values = asdict(s)
        values["invalid_rate"] = 100.0 * s.invalid_rate
        print(" ".join(f"{_fmt(values[f], 1):>8}" for _, f in columns))
        if s.suspect_zero or s.suspect_65535:
            print(f"{'':>8} note: {s.suspect_zero} frames at 0 cm, {s.suspect_65535} at 65535 "
                  "(possible no-target sentinels; verify against the datasheet)")
    print("\nHz = host-side receive rate of valid measurements; includes OS/USB buffering jitter.")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Analyze TFmini characterization CSV")
    p.add_argument("csv", type=Path, help="CSV produced by tfmini_record.py")
    p.add_argument("--exclude-distance", type=int, nargs="*", default=[],
                   help="distance values treated as invalid readings, e.g. 0 65535")
    p.add_argument("--min-strength", type=int, default=None,
                   help="treat frames below this strength as invalid readings")
    p.add_argument("--summary-csv", type=Path, help="also write the summary table to this CSV")
    args = p.parse_args(argv)

    with args.csv.open(newline="") as handle:
        summaries = analyze(csv.DictReader(handle), args.exclude_distance, args.min_strength)
    if not summaries:
        print("No rows found.", file=sys.stderr)
        return 1

    print_table(summaries)
    if args.summary_csv:
        with args.summary_csv.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
            writer.writeheader()
            for s in summaries:
                writer.writerow(asdict(s))
        print(f"Summary written to {args.summary_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
