"""TISHTAR - TFmini LiDAR hardware validation (TF-02, issue #27).

Standalone script that reads TFmini frames over UART and prints distance and
signal strength. It is NOT a pytest test: it needs the physical sensor and is
excluded from test discovery by ``conftest.py``.

Usage:
    python test_tfmini.py                       # /dev/ttyS0 @ 115200
    python test_tfmini.py --port /dev/ttyAMA0 --baud 115200 --rate 5
"""

from __future__ import annotations

import argparse
import sys
import time

from tfmini_protocol import TFminiStreamParser

DEFAULT_PORT = "/dev/ttyS0"
DEFAULT_BAUD_RATE = 115200
DEFAULT_PRINT_RATE_HZ = 10.0
DEFAULT_TIMEOUT_S = 1.0
NO_DATA_WARNING_S = 3.0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TISHTAR TFmini hardware test")
    parser.add_argument("--port", default=DEFAULT_PORT, help="serial device (default: %(default)s)")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD_RATE, help="baud rate (default: %(default)s)")
    parser.add_argument(
        "--rate", type=float, default=DEFAULT_PRINT_RATE_HZ,
        help="maximum terminal print rate in Hz (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT_S,
        help="serial read timeout in seconds (default: %(default)s)",
    )
    args = parser.parse_args(argv)
    if args.rate <= 0:
        parser.error("--rate must be positive")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return args


def print_summary(parser: TFminiStreamParser, elapsed_s: float) -> None:
    stats = parser.stats
    rate = stats.valid_frames / elapsed_s if elapsed_s > 0 else 0.0
    print("-" * 40)
    print(f"Valid frames:     {stats.valid_frames}")
    print(f"Checksum errors:  {stats.checksum_errors}")
    print(f"Discarded bytes:  {stats.discarded_bytes}")
    print(f"Mean frame rate:  {rate:.1f} Hz over {elapsed_s:.1f} s")


def run(port: str, baud: int, print_rate_hz: float, timeout_s: float) -> int:
    """Read and display frames until Ctrl+C. Returns a process exit code."""
    try:
        import serial  # imported lazily so the parser can be tested without pyserial
    except ImportError:
        print("pyserial is not installed: python -m pip install -r requirements.txt", file=sys.stderr)
        return 2

    print("TISHTAR - TFmini Hardware Test")
    print(f"Port: {port}")
    print(f"Baud rate: {baud}")
    print("-" * 40)

    parser = TFminiStreamParser()
    print_period = 1.0 / print_rate_hz
    start = time.monotonic()
    last_print = 0.0
    last_frame = start
    warned_no_data = False
    exit_code = 0

    try:
        with serial.Serial(port, baud, timeout=timeout_s) as ser:
            ser.reset_input_buffer()  # discard stale bytes from before start-up
            while True:
                # Blocks for up to `timeout_s` when idle, so no busy loop.
                chunk = ser.read(ser.in_waiting or 1)
                now = time.monotonic()

                for frame in parser.feed(chunk):
                    if not frame.checksum_ok:
                        continue
                    last_frame = now
                    warned_no_data = False
                    if now - last_print >= print_period:
                        print(f"Distance: {frame.distance_cm:4d} cm | Strength: {frame.strength:5d}")
                        last_print = now

                if not warned_no_data and now - last_frame >= NO_DATA_WARNING_S:
                    print(
                        f"Warning: no valid frame for {NO_DATA_WARNING_S:.0f} s "
                        "- check wiring, power, port and baud rate.",
                        file=sys.stderr,
                    )
                    warned_no_data = True

    except KeyboardInterrupt:
        print("\nTest stopped.")
    except serial.SerialException as error:
        # Raised both when the port cannot be opened and on disconnection.
        print(f"Serial error: {error}", file=sys.stderr)
        exit_code = 1

    print_summary(parser, time.monotonic() - start)
    return exit_code


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return run(args.port, args.baud, args.rate, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
