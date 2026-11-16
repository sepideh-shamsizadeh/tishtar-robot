
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Vector3
from sensor_msgs.msg import JointState
from std_srvs.srv import SetBool

from tishtar_pan_tilt.servo_driver import PanTiltDriver


class PanTiltNode(Node):

    def __init__(self):
        super().__init__("pan_tilt_controller")

        # Configuration
        self.declare_parameter("pan_channel", 1)
        self.declare_parameter("tilt_channel", 0)

        self.declare_parameter("pan_home", 90.0)
        self.declare_parameter("tilt_home", 90.0)

        # Temporary defaults, NOT calibrated limits.
        self.declare_parameter("pan_min", 45.0)
        self.declare_parameter("pan_max", 180.0)
        self.declare_parameter("tilt_min", 45.0)
        self.declare_parameter("tilt_max", 180.0)

        self.declare_parameter("max_step_deg", 1.0)

        def param(name):
            return self.get_parameter(name).value

        self.pan_min = float(param("pan_min"))
        self.pan_max = float(param("pan_max"))
        self.tilt_min = float(param("tilt_min"))
        self.tilt_max = float(param("tilt_max"))

        if not (
            0 <= self.pan_min <= self.pan_max <= 180
            and 0 <= self.tilt_min <= self.tilt_max <= 180
        ):
            raise ValueError("Invalid servo angle limits")

        self.pan = float(param("pan_home"))
        self.tilt = float(param("tilt_home"))

        if not (
            self.pan_min <= self.pan <= self.pan_max
            and self.tilt_min <= self.tilt <= self.tilt_max
        ):
            raise ValueError("Home angles outside configured limits")

        self.target_pan = self.pan
        self.target_tilt = self.tilt
        self.max_step = float(param("max_step_deg"))

        if not 0 < self.max_step <= 5:
            raise ValueError("max_step_deg must be in (0, 5]")

        self.driver = PanTiltDriver(
            address=0x40,
            pan_channel=int(param("pan_channel")),
            tilt_channel=int(param("tilt_channel")),
        )

        self.armed = False

        self.jog_sub = self.create_subscription(
            Vector3,
            "/camera/pan_tilt/jog",
            self.on_jog,
            10,
        )

        self.state_pub = self.create_publisher(
            JointState,
            "/camera/pan_tilt/commanded_state",
            10,
        )

        self.arm_service = self.create_service(
            SetBool,
            "/camera/pan_tilt/arm",
            self.on_arm,
        )

        self.timer = self.create_timer(
            0.05,
            self.update,
        )

        self.get_logger().info(
            "Pan-tilt controller initialized DISARMED"
        )

    @staticmethod
    def clamp(value, low, high):
        return max(low, min(high, value))

    def on_arm(self, request, response):
        if request.data:
            self.armed = True
            self.get_logger().warning(
                "ARMED: First servo command may cause "
                "a position jump. Ensure mechanical clearance."
            )
            response.message = "Pan-tilt armed"
        else:
            self.armed = False
            self.target_pan = self.pan
            self.target_tilt = self.tilt
            self.driver.release()
            response.message = "Pan-tilt disarmed"

        response.success = True
        return response

    def on_jog(self, msg):
        if not self.armed:
            self.get_logger().warning(
                "Ignoring jog command: controller disarmed"
            )
            return

        self.target_pan = self.clamp(
            self.target_pan + msg.x,
            self.pan_min,
            self.pan_max,
        )

        self.target_tilt = self.clamp(
            self.target_tilt + msg.y,
            self.tilt_min,
            self.tilt_max,
        )

    def update(self):
        if not self.armed:
            return

        next_pan = self.pan + self.clamp(
            self.target_pan - self.pan,
            -self.max_step,
            self.max_step,
        )

        next_tilt = self.tilt + self.clamp(
            self.target_tilt - self.tilt,
            -self.max_step,
            self.max_step,
        )

        try:
            if abs(next_pan - self.pan) > 1e-6:
                self.driver.set_pan(next_pan)
                self.pan = next_pan

            if abs(next_tilt - self.tilt) > 1e-6:
                self.driver.set_tilt(next_tilt)
                self.tilt = next_tilt

        except Exception as exc:
            self.armed = False
            self.target_pan = self.pan
            self.target_tilt = self.tilt
            try:
                self.driver.release()
            except Exception:
                pass
            self.get_logger().error(
                f"Servo communication error; disarmed: {exc}"
            )
            return

        state = JointState()
        state.header.stamp = self.get_clock().now().to_msg()
        state.name = ["camera_pan_joint", "camera_tilt_joint"]

        # JointState uses radians.
        # These are COMMAND ESTIMATES, not measurements.
        from math import radians
        state.position = [
            radians(self.pan),
            radians(self.tilt),
        ]

        self.state_pub.publish(state)

    def shutdown_hardware(self):
        self.armed = False
        self.driver.release()


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = PanTiltNode()
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        if node is not None:
            try:
                node.shutdown_hardware()
            finally:
                node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
