# TISHTAR — TFmini LiDAR UART Integration

**Project:** TISHTAR Autonomous Mobile Robot  
**Parent issue:** [#12 — SEN-03 — Integrate TFmini LiDAR](https://github.com/sepideh-shamsizadeh/tishtar-robot/issues/12)  
**Related issues:** [#26 — TF-01](https://github.com/sepideh-shamsizadeh/tishtar-robot/issues/26), [#27 — TF-02](https://github.com/sepideh-shamsizadeh/tishtar-robot/issues/27), [#28 — TF-03](https://github.com/sepideh-shamsizadeh/tishtar-robot/issues/28)  
**Status:** UART communication verified. Wiring is **provisional** until physically confirmed.

## 1. Overview

The Benewake TFmini is a single-point time-of-flight distance sensor. On TISHTAR it is mounted on the camera pan-tilt mechanism (PCA9685 + MG90S servos). The long-term goal is an experimental 180° 2D scanner (TF-05 to TF-07).

| Item | Value |
|---|---|
| Sensor | Benewake TFmini (exact variant/firmware **not yet confirmed**) |
| Host | Raspberry Pi 4B, Ubuntu 24.04.3 LTS |
| Interface | UART, receive-only |
| Linux device | `/dev/ttyS0` |
| Serial settings | 115200 baud, 8N1, no hardware flow control |
| Frame | 9 bytes, header `0x59 0x59` |
| Observed frame rate | ~100 Hz (host-side receive rate, 25 Nov 2026) |

## 2. Wiring (provisional)

> ⚠️ UART communication works with the current wiring, but the exact physical pins, wire-colour mapping, sensor variant and any HAT pass-through mapping have **not** been independently confirmed. Logic-voltage compatibility has also not been verified. The Raspberry Pi GPIO is **3.3 V only**. Confirm the TFmini variant's TX logic level before relying on this wiring.

| TFmini wire | Function | Raspberry Pi | Status |
|---|---|---|---|
| Red | 5 V supply | Physical pin 4 (5 V) | Provisional |
| Black | Ground | Physical pin 6 (GND) | Provisional |
| Green | Sensor TX | Physical pin 10 (GPIO15, RXD) | Provisional |
| Blue | Sensor RX | Not connected (receive-only) | Provisional |

Receive-only operation means the Pi cannot send configuration commands (frame rate, output format, etc.) to the sensor. The sensor runs with its factory or previously stored settings.

### Physical wiring verification checklist

Complete this before closing #26:

- [ ] Identify the exact sensor model from its label or packaging (TFmini / TFmini Plus / TFmini-S) and record the firmware version if available.
- [ ] Confirm the wire colours against that model's datasheet (colour conventions differ between variants and cables).
- [ ] Confirm the TX logic level is 3.3 V–compatible for this variant.
- [ ] Trace each wire to its physical header pin with the Pi powered off, and photograph the connection.
- [ ] If a HAT or breakout is between the sensor and the Pi, confirm how it passes pins 4, 6 and 10 through.
- [ ] Measure the supply voltage at the sensor connector with a multimeter.
- [ ] Update the table above, remove "provisional", and add a photo under `docs/images/`.

## 3. UART configuration

`/boot/firmware/config.txt` already contains:

```ini
enable_uart=1
```

Checked and confirmed on the Pi:

- No serial console in `/boot/firmware/cmdline.txt`, so the kernel is not using the UART.
- The user is in the `dialout` group. `/dev/ttyS0` is `root:dialout`, mode `crw-rw----`.
- `sudo lsof /dev/ttyS0` returned no processes.

No further boot configuration changes are needed. Do not modify boot files for this sensor.

> On the Pi 4, `/dev/ttyS0` is the mini-UART. Its baud clock is derived from the VPU core clock. It works reliably at 115200 here, but if the core clock changes (e.g. due to certain overlays or frequency scaling settings), the mini-UART baud rate can drift. Keep that in mind when diagnosing intermittent checksum errors.

**Note on the pinmux diagnostic:** `sudo sh -c 'cat /sys/kernel/debug/pinctrl/*/pinmux-pins' | grep -E 'pin (14|15) '` reported GPIO14/15 as unclaimed, even though UART reception demonstrably works. Do not rely on this diagnostic alone to judge UART availability.

## 4. Diagnostic commands

```bash
# Device and permissions
ls -l /dev/ttyS0
groups | grep dialout

# Is anything else holding the port?
sudo lsof /dev/ttyS0

# Kernel serial console must not be on ttyS0 / serial0
cat /boot/firmware/cmdline.txt

# Raw byte dump (expect repeating "59 59 ..." groups)
stty -F /dev/ttyS0 115200 raw -echo -crtscts
timeout 5s cat /dev/ttyS0 | hexdump -C

# Decoded output
python3 tests/hardware/tfmini/test_tfmini.py
```

## 5. Binary protocol

Each frame is 9 bytes, little-endian:

| Byte | Field | Notes |
|---|---|---|
| 0 | `0x59` | Header |
| 1 | `0x59` | Header |
| 2 | Distance low | `uint16`, centimetres |
| 3 | Distance high | |
| 4 | Strength low | `uint16`, unitless signal strength |
| 5 | Strength high | |
| 6 | Extra byte | Variant-specific, **not interpreted** |
| 7 | Extra byte | Variant-specific, **not interpreted** |
| 8 | Checksum | `sum(bytes[0:8]) & 0xFF` |

Depending on the variant, bytes 6–7 may encode the mode, temperature or something else. They are deliberately left uninterpreted until the exact model and protocol version are confirmed. They are not constant: `78 09` was observed on one day and `90 09` on another.

### Verified example frames

Received on `/dev/ttyS0` with `hexdump`:

```text
59 59 2f 00 41 0a 78 09 ad
59 59 2f 00 44 0a 78 09 b0
59 59 2f 00 3c 0a 78 09 a8
```

Decoding the first frame:

- Distance: `0x002F` = 47 cm
- Strength: `0x0A41` = 2625
- Extra: `78 09` (uninterpreted)
- Checksum: `(0x59+0x59+0x2F+0x00+0x41+0x0A+0x78+0x09) & 0xFF = 0xAD` ✔

These frames are used as fixtures in `tests/hardware/tfmini/test_tfmini_protocol.py`.

## 6. Troubleshooting

| Symptom | Likely causes / checks |
|---|---|
| `Permission denied` on `/dev/ttyS0` | User not in `dialout`: `sudo usermod -aG dialout $USER`, then log out and back in |
| `could not open port` / no such file | UART not enabled, or using the wrong device. Check `ls -l /dev/serial*` |
| Port opens but no bytes | Power, ground, or TX→RX wiring. Wrong pin (TX must go to GPIO15 / pin 10). Sensor not powered |
| Bytes arrive but no `59 59` pattern | Wrong baud rate, or the sensor is in a non-default output mode |
| Frequent checksum errors | Loose wiring, electrical noise, mini-UART clock drift, another process reading the port |
| Garbage mixed with kernel messages | Serial console still enabled on that UART (check `cmdline.txt`) |
| Port busy | Another process (e.g. `getty`, ModemManager, a second script). Check with `sudo lsof /dev/ttyS0` |

## 7. Current limitations

- Wiring, sensor variant and logic-level compatibility are not yet physically confirmed (see §2).
- Measurement accuracy, minimum reliable range, maximum range and behaviour on different materials are **not** characterized. See [TF-03 characterization](tfmini_characterization.md).
- Observed results (stable 46–47 cm on a static scene, dynamic response down to a reported 2 cm when an obstacle approached) show that communication and decoding work. They do not establish measurement validity at short range.
- Receive-only wiring: the sensor cannot be configured from the Pi.
- No ROS 2 driver yet (TF-04, #29).
