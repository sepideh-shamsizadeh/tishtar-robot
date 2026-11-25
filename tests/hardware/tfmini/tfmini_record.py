"""TISHTAR - TFmini distance characterization recorder (TF-03, issue #28).

Records every received frame (valid and checksum-invalid) for ONE reference
distance and appends it to a CSV file. Run once per reference distance.

Example:
    python tfmini_record.py --experiment-id 2026-11-26_A --reference-cm 50 \\
        --material "white matte cardboard"

Requires the physical sensor. Not collected by pytest.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from tfmini_protocol import TFminiStreamParser

CSV_FIELDS = [
    "experiment_id",
    "timestamp_utc",
    "elapsed_s",
    "reference_distance_cm",
    "target_material",
    "frame_valid",
    "distance_cm",
    "strength",
    "raw_frame_hex",
]

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "results" / "tfmini_characterization.csv"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Record TFmini frames for one reference distance")
    p.add_argument("--experiment-id", required=True, help="identifier shared by one experiment session")
    p.add_argument("--reference-cm", type=float, required=True, help="tape-measured reference distance in cm")
    p.add_argument("--material", required=True, help="target material/colour, e.g. 'white matte cardboard'")
    p.add_argument("--samples", type=int, default=500, help="frames to record (default: %(default)s)")
    p.add_argument("--max-duration", type=float, default=30.0, help="stop after N seconds (default: %(default)s)")
    p.add_argument("--settle", type=float, default=1.0,
                   help="seconds of data discarded after start-up (default: %(default)s)")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="CSV file to append to")
    p.add_argument("--port", default="/dev/ttyS0")
    p.add_argument("--baud", type=int, default=115200)
    args = p.parse_args(argv)
    if args.samples <= 0 or args.max_duration <= 0 or args.settle < 0 or args.reference_cm <= 0:
        p.error("--samples, --max-duration and --reference-cm must be positive; --settle >= 0")
    return args


def record(args: argparse.Namespace) -> int:
    import serial

    args.output.parent.mkdir(parents=True, exist_ok=True)
    new_file = not args.output.exists() or args.output.stat().st_size == 0
    parser = TFminiStreamParser()
    written = 0

    try:
        with serial.Serial(args.port, args.baud, timeout=0.5) as ser, \
                args.output.open("a", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            if new_file:
                writer.writeheader()

            # Settle: let the target/operator stop moving, then drop stale bytes.
            time.sleep(args.settle)
            ser.reset_input_buffer()
            parser.reset()

            start = time.monotonic()
            while written < args.samples and time.monotonic() - start < args.max_duration:
                chunk = ser.read(ser.in_waiting or 1)
                now = time.monotonic()
                for frame in parser.feed(chunk):
                    writer.writerow({
                        "experiment_id": args.experiment_id,
                        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                        "elapsed_s": f"{now - start:.4f}",
                        "reference_distance_cm": args.reference_cm,
                        "target_material": args.material,
                        "frame_valid": int(frame.checksum_ok),
                        # Values from a checksum-invalid frame are meaningless: leave blank.
                        "distance_cm": frame.distance_cm if frame.checksum_ok else "",
                        "strength": frame.strength if frame.checksum_ok else "",
                        "raw_frame_hex": frame.raw.hex(),
                    })
                    written += 1
                    if written >= args.samples:
                        break
    except KeyboardInterrupt:
        print("\nRecording interrupted.", file=sys.stderr)
    except serial.SerialException as error:
        print(f"Serial error: {error}", file=sys.stderr)
        return 1

    s = parser.stats
    print(f"Recorded {written} frames at reference {args.reference_cm} cm -> {args.output}")
    print(f"valid={s.valid_frames} checksum_errors={s.checksum_errors} discarded_bytes={s.discarded_bytes}")
    if written < args.samples:
        print(f"Warning: only {written}/{args.samples} frames before timeout/interrupt.", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    return record(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
