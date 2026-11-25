"""
TISHTAR - TFmini LiDAR Hardware Validation

Interface: UART
Device: /dev/ttyS0
Baud rate: 115200
"""

import serial
import time

PORT = "/dev/ttyS0"
BAUD_RATE = 115200
FRAME_SIZE = 9
HEADER = b"\x59\x59"


def read_frame(ser):
    """Read and validate a TFmini data frame."""

    if ser.read(1) != HEADER[:1]:
        return None

    if ser.read(1) != HEADER[1:]:
        return None

    payload = ser.read(FRAME_SIZE - 2)

    if len(payload) != FRAME_SIZE - 2:
        return None

    frame = HEADER + payload

    checksum = sum(frame[:8]) & 0xFF

    if checksum != frame[8]:
        return None

    distance = int.from_bytes(frame[2:4], "little")
    strength = int.from_bytes(frame[4:6], "little")

    return distance, strength


def main():
    print("TISHTAR - TFmini Hardware Test")
    print(f"Port: {PORT}")
    print(f"Baud rate: {BAUD_RATE}")
    print("-" * 40)

    try:
        with serial.Serial(
            PORT, BAUD_RATE, timeout=1
        ) as ser:

            last_print = 0.0

            while True:
                measurement = read_frame(ser)

                if measurement is None:
                    continue

                distance, strength = measurement

                now = time.monotonic()

                if now - last_print >= 0.1:
                    print(
                        f"Distance: {distance:4d} cm | "
                        f"Strength: {strength:5d}"
                    )
                    last_print = now

    except KeyboardInterrupt:
        print("\nTest stopped.")

    except serial.SerialException as error:
        print(f"Serial error: {error}")


if __name__ == "__main__":
    main()