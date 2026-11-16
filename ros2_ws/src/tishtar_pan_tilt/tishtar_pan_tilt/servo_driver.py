
from adafruit_servokit import ServoKit


class PanTiltDriver:
    """PCA9685 hardware interface for two positional servos."""

    def __init__(
        self,
        address=0x40,
        pan_channel=1,
        tilt_channel=0,
    ):
        self.kit = ServoKit(
            channels=16,
            address=address,
        )
        self.pan_channel = pan_channel
        self.tilt_channel = tilt_channel

    def set_pan(self, angle):
        self.kit.servo[self.pan_channel].angle = float(angle)

    def set_tilt(self, angle):
        self.kit.servo[self.tilt_channel].angle = float(angle)

    def release(self):
        self.kit.servo[self.pan_channel].angle = None
        self.kit.servo[self.tilt_channel].angle = None
