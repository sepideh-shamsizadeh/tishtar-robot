# TISHTAR — ICM-20948 Hardware Validation

## Hardware
- Raspberry Pi 4B
- SparkFun ICM-20948 9-DoF IMU
- Interface: I2C
- Bus: 1
- Address: 0x69

## Installation

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

## Run

python test_imu.py

## Measurement units
- Accelerometer: g
- Gyroscope: degrees/s
- Magnetometer: microtesla
- Nominal sampling interval: 0.2 seconds

## Validation results
- I2C device detection successful.
- WHO_AM_I returned 0xEA.
- Accelerometer, gyroscope and magnetometer readings acquired.
- Rotation and robot movement tests successful.
- Continuous operation for several minutes successful.

## Known limitations
- Intermittent I2C errors were previously observed.
- Exact root cause has not been confirmed.
- Formal endurance testing remains pending.
- Sensor calibration and axis validation remain pending.

## Related issues
- #33: Connect IMU and validate I2C
- #34: Standalone hardware test
- #35: Measurement and axis validation
- #36: Sampling, noise and calibration
