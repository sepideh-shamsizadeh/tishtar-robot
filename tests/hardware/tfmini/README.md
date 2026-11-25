# TFmini Hardware Validation

Standalone scripts for validating the Benewake TFmini on the TISHTAR Raspberry Pi. They are independent of ROS 2 on purpose. The ROS 2 driver is a separate task (TF-04, #29).

Issues: [#26 TF-01](https://github.com/sepideh-shamsizadeh/tishtar-robot/issues/26) · [#27 TF-02](https://github.com/sepideh-shamsizadeh/tishtar-robot/issues/27) · [#28 TF-03](https://github.com/sepideh-shamsizadeh/tishtar-robot/issues/28)  
Wiring, UART setup and protocol: [docs/hardware/tfmini_lidar.md](../../../docs/hardware/tfmini_lidar.md)

## Files

| File | Purpose | Needs hardware |
|---|---|---|
| `tfmini_protocol.py` | Frame decoding + streaming parser with resynchronisation | No |
| `test_tfmini.py` | Live hardware test: prints distance and strength | **Yes** |
| `tfmini_record.py` | TF-03: record frames at a reference distance to CSV | **Yes** |
| `tfmini_analyze.py` | TF-03: statistics from the recorded CSV | No |
| `test_tfmini_protocol.py`, `test_tfmini_analysis.py` | Unit tests | No |
| `conftest.py` | Keeps `pytest` from collecting the hardware script | — |

`test_tfmini.py` keeps its original name and command. It matches pytest's default `test_*.py` pattern, so `conftest.py` excludes it from collection. The script also imports `pyserial` only inside `run()`, so importing the module never opens a port.

## Hardware requirements

- Raspberry Pi 4B with `enable_uart=1` and no serial console on the UART
- TFmini TX → GPIO15 (pin 10), 5 V and GND (see the provisional wiring table in the docs)
- User in the `dialout` group

## Installation

```bash
cd tests/hardware/tfmini

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt
```

`.venv/` and `__pycache__/` are ignored by Git. On the Pi, the system `/usr/bin/python3` with the apt package `python3-serial` also works.

## Usage

```bash
python test_tfmini.py                                 # defaults: /dev/ttyS0, 115200
python test_tfmini.py --port /dev/ttyS0 --baud 115200 --rate 10
python test_tfmini.py --help
```

Stop with `Ctrl+C`. The script prints a link-quality summary on exit. Exit codes: `0` = normal stop, `1` = serial error (cannot open port / disconnected), `2` = pyserial missing.

### Expected output

```text
TISHTAR - TFmini Hardware Test
Port: /dev/ttyS0
Baud rate: 115200
----------------------------------------
Distance:   46 cm | Strength:  2519
Distance:   46 cm | Strength:  2516
...
^C
Test stopped.
----------------------------------------
Valid frames:     381
Checksum errors:  0
Discarded bytes:  0
Mean frame rate:  100.0 Hz over 3.8 s
```

If no valid frame arrives for 3 s, a warning is printed to stderr.

## Unit tests (no hardware)

```bash
python -m pytest -q          # if pytest is installed
python -m unittest -v        # standard library only
```

The tests cover valid frames (the real recorded frames as fixtures), wrong checksums, incomplete and byte-by-byte input, misaligned starts, garbage between frames, recovery after corruption, a false `59 59` header inside a frame, little-endian decoding, and the characterization statistics.

## Frame structure

`59 59 | dist_L dist_H | str_L str_H | x x | checksum` where checksum = `sum(bytes[0:8]) & 0xFF`. Bytes 6–7 are not interpreted. Details: [docs/hardware/tfmini_lidar.md §5](../../../docs/hardware/tfmini_lidar.md#5-binary-protocol).

## Parser design

The serial port delivers arbitrary chunks, not whole frames. `TFminiStreamParser.feed()` buffers bytes, searches for the header, and waits for 9 bytes. After a checksum failure it drops **one** byte, not nine, so it re-locks even when the false header was inside a real frame (distance 89 cm = `0x59`). Frames with a bad checksum are returned with `checksum_ok=False` so they can be counted, never used.

## Distance characterization (TF-03)

```bash
python tfmini_record.py --experiment-id 2026-11-26_A --reference-cm 50 --material "white matte cardboard"
python tfmini_analyze.py results/tfmini_characterization.csv
```

Protocol, CSV format and results table: [docs/hardware/tfmini_characterization.md](../../../docs/hardware/tfmini_characterization.md).

## Verified results

Original script, on the Pi (`/dev/ttyS0`, 115200):

- Static scene: stable 46–47 cm, strength ≈ 2510–2530.
- Obstacle approaching: reported 10 → 9 → 5 → 2 cm with high strength. After removal: 47 cm.

Refactored script, on the Pi, 25 Nov 2026 (≈4 s run): 381 valid frames, 0 checksum errors, 0 discarded bytes, ≈100 Hz host receive rate, static scene at 78 cm.

These results show that communication and decoding work. They do **not** establish accuracy or minimum reliable range. Readings below roughly 10–30 cm in particular are unvalidated.

## Known limitations

- Wiring and the exact sensor variant are provisional (TF-01).
- Receive-only: the sensor cannot be configured.
- Timestamps are host receive times, not sensor times.
- Not a ROS 2 node: TF-04 will reuse `tfmini_protocol.py` logic in `tishtar_sensors`.
