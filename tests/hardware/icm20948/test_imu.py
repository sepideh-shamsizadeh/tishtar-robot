"""
TISHTAR - ICM-20948 Hardware Validation

Interface: I2C
Bus: 1
Address: 0x69
"""

import time
from icm20948 import ICM20948


def main():
    imu = ICM20948(i2c_addr=0x69)

    print("TISHTAR - ICM-20948 Hardware Test")
    print("I2C address: 0x69")
    print("-" * 60)

    try:
        while True:
            ax, ay, az, gx, gy, gz = (
                imu.read_accelerometer_gyro_data()
            )

            mx, my, mz = imu.read_magnetometer_data()

            print(
                f"ACC [g]: "
                f"X={ax:+7.3f} "
                f"Y={ay:+7.3f} "
                f"Z={az:+7.3f}"
            )

            print(
                f"GYRO [deg/s]: "
                f"X={gx:+7.3f} "
                f"Y={gy:+7.3f} "
                f"Z={gz:+7.3f}"
            )

            print(
                f"MAG [uT]: "
                f"X={mx:+7.3f} "
                f"Y={my:+7.3f} "
                f"Z={mz:+7.3f}"
            )

            print("-" * 60)

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\nTest stopped.")


if __name__ == "__main__":
    main()