# Sensor hardware integration — initial validation

Date: 2026-11-25. Platform: Raspberry Pi 4B, Ubuntu 24.04, ROS 2 Jazzy.

## TFmini (#26, #27)

UART device: /dev/ttyS0, 115200 baud. Frames were decoded, checksums validated, and distance and signal strength acquired. Initial stationary distance was approximately 46–47 cm; readings responded to moving targets.

Physical wiring is not independently confirmed. Record actual module variant, supply voltage, ground, TX/RX connections and logic levels before closing #26. Do not infer the pinout from the UART device name.

Local test command (on Pi):

```sh
cd ~/workspace/tishtar-robot
/usr/bin/python3 tests/hardware/tfmini/test_tfmini.py
```

The script was reported working locally but was not found on main during documentation review. Commit the actual tested script and dependency instructions before closing #27. Accuracy and valid range remain #28.

## ICM-20948 (#33, #34, #35)

SparkFun Qwiic 9DoF ICM-20948 breakout. Proposed wiring, to be checked against the installed harness:

| Pi physical pin | Signal | Breakout |
|---|---|---|
| 1 | 3.3 V | VIN |
| 3 | GPIO2 / SDA | DA |
| 5 | GPIO3 / SCL | CL |
| 9 | GND | GND |

Power off before changing wiring. Verify breakout voltage requirements and use a secure connector with strain relief. Do not use auxiliary ADA/ACL for the host bus.

I2C bus 1 detected address 0x69 alongside PCA9685 at 0x40. Bank 0 WHO_AM_I returned 0xEA.

```sh
sudo i2cdetect -y 1
sudo i2cset -y 1 0x69 0x7F 0x00
sudo i2cget -y 1 0x69 0x00
```

Run diagnostics with other IMU readers stopped. Expected identity: 0xea.

Local Python test uses the icm20948 package in a virtual environment. It reads acceleration (g), angular velocity (degrees/s), and magnetic field (microtesla).

```sh
cd ~/workspace/tishtar-robot/tests/hardware/icm20948
source .venv/bin/activate
python test_imu.py
```

Initial stationary acceleration approximately (0.073, -0.152, 0.967) g; norm approximately 0.982 g. Gyro Y approximately 1 degree/s. Magnetic magnitude initially approximately 144 microtesla and later approximately 47 microtesla. These are preliminary observations, not calibration results. Earlier movement caused I/O error 5 and device disappearance; wiring instability was reported. Subsequent functional operation was reported successful. Secure wiring and repeatability still require verification. Record installed package version and commit actual tested script; it was not found on main during review.

## Combined operation

The operator reported all sensors working after initial tests. Camera IMX219 was detected by libcamera; ultrasonic measurements were acquired through STM32. Earlier ultrasonic short-range limitations require characterization. No measured endurance duration, synchronized sampling, calibrated accuracy or ROS 2 sensor integration is claimed.

## Remaining acceptance checks

- [ ] Confirm and photograph installed TFmini and IMU wiring.
- [ ] Commit both actual hardware test scripts and reproducible dependencies.
- [ ] Run simultaneous acquisition for 10 minutes; record duration, errors and dropouts, including gentle movement.
- [ ] Record IMU axis orientation, noise and calibration separately (#35, #36).
- [ ] Characterize TFmini and ultrasonic distance accuracy and useful range.
- [ ] Review and merge documentation before closing applicable issues.
