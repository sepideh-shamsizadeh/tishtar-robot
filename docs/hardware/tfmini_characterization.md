# TISHTAR — TFmini Distance Characterization (TF-03)

**Project:** TISHTAR Autonomous Mobile Robot  
**Issue:** [#28 — TF-03 — Characterize distance accuracy and valid range](https://github.com/sepideh-shamsizadeh/tishtar-robot/issues/28)  
**Status:** Protocol and tooling prepared. **No measurements collected yet. Results pending.**

## 1. Objective

Quantify the TFmini's accuracy, repeatability, signal strength and invalid-reading behaviour at known reference distances. These results define the usable range for the TF-04 ROS 2 driver (`min_range` / `max_range` in `sensor_msgs/Range`) and the TF-06 experimental scanner.

## 2. Definitions

| Term | Meaning |
|---|---|
| Raw frame | Any 9-byte sequence aligned on `0x59 0x59` |
| Valid frame | Raw frame whose checksum matches |
| Valid measurement | Valid frame that also passes the measurement rules (sentinel distances, minimum strength). The rules are chosen **after** checking the datasheet for the confirmed variant |
| Invalid-reading rate | (checksum-invalid + excluded) / raw frames |
| Bias | mean(measured − reference) |
| MAE / RMSE | mean absolute error / root-mean-square error against the reference |

A checksum-valid frame shows that the link is working. It does not show that the distance is physically correct.

## 3. Setup

- Fix the robot or sensor so it cannot move. Point the TFmini horizontally. **Disable or unpower the pan-tilt servos** so the sensor does not move.
- Target: a flat board, larger than the beam footprint at the farthest distance, perpendicular to the beam.
- Reference: tape measure from the TFmini's **front face** to the target, recorded to ±0.5 cm. Record which datum is used. The sensor's internal zero point may differ from the front face. Measuring that offset is part of the bias analysis.
- Environment: indoor, note the lighting (sunlight affects ToF sensors).
- Materials: start with one matte, light-coloured target. Repeat with dark and glossy targets if time allows.

## 4. Procedure

Reference distances (cm):

```text
5, 10, 20, 30, 50, 75, 100, 150, 200, 300
```

5–20 cm are **exploratory**. They are included to find where readings stop being trustworthy, not because they are assumed to be in range.

For each material and distance:

```bash
cd tests/hardware/tfmini
python tfmini_record.py --experiment-id 2026-11-26_A --reference-cm 50 \
    --material "white matte cardboard" --samples 500
```

Then analyze:

```bash
python tfmini_analyze.py results/tfmini_characterization.csv \
    --summary-csv results/tfmini_summary.csv
```

Run the analysis once with no exclusions (raw behaviour). Then, once the datasheet's invalid-reading convention is confirmed, run it again with e.g. `--exclude-distance 0 65535 --min-strength <N>`. Report both runs.

## 5. CSV format (`tfmini_record.py`)

| Column | Description |
|---|---|
| `experiment_id` | Session identifier, e.g. `2026-11-26_A` |
| `timestamp_utc` | Host wall-clock time (ISO 8601) when the frame was parsed |
| `elapsed_s` | Host monotonic seconds since the start of recording |
| `reference_distance_cm` | Tape-measured reference |
| `target_material` | Free text |
| `frame_valid` | `1` = checksum OK, `0` = checksum failed |
| `distance_cm` | Decoded distance (blank if `frame_valid=0`) |
| `strength` | Decoded strength (blank if `frame_valid=0`) |
| `raw_frame_hex` | All 9 bytes, for re-analysis |

## 6. Results

> **Pending.** No characterization data has been collected. Do not fill this table with estimates.

| Ref (cm) | Material | Frames | Invalid % | Mean | Median | Std | Bias | MAE | RMSE | Min | Max | Strength | Hz |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | — | | | | | | | | | | | | |
| 10 | — | | | | | | | | | | | | |
| 20 | — | | | | | | | | | | | | |
| 30 | — | | | | | | | | | | | | |
| 50 | — | | | | | | | | | | | | |
| 75 | — | | | | | | | | | | | | |
| 100 | — | | | | | | | | | | | | |
| 150 | — | | | | | | | | | | | | |
| 200 | — | | | | | | | | | | | | |
| 300 | — | | | | | | | | | | | | |

## 7. Known limitations of the method

- `elapsed_s` and the reported Hz are **host receive times**. They include kernel/UART buffering jitter and are not sensor timestamps.
- A tape-measure reference has its own ±0.5–1 cm uncertainty. At 5–10 cm this is a large relative error.
- Beam divergence means the spot grows with distance. At long range the target must be large enough, or the reading mixes target and background.
- Results apply only to the tested materials, angle of incidence and lighting.
