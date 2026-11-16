
import sys
import select
import termios
import tty

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Vector3


class KeyboardNode(Node):

    def __init__(self):
        super().__init__("pan_tilt_keyboard")

        self.declare_parameter("step_deg", 3.0)

        self.step = float(
            self.get_parameter("step_deg").value
        )

        if not 0 < self.step <= 5:
            raise ValueError("step_deg must be in (0, 5]")

        self.publisher = self.create_publisher(
            Vector3,
            "/camera/pan_tilt/jog",
            10,
        )

        self.get_logger().info(
            "Keyboard teleoperation initialized"
        )

    def send(self, pan_delta=0.0, tilt_delta=0.0):
        msg = Vector3()
        msg.x = float(pan_delta)
        msg.y = float(tilt_delta)
        msg.z = 0.0
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = KeyboardNode()

    if not sys.stdin.isatty():
        node.get_logger().error(
            "An interactive terminal is required."
        )
        node.destroy_node()
        rclpy.shutdown()
        return

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    print("""
    ======================================
           TISHTAR CAMERA CONTROL
    ======================================

           W       Tilt up
       A       D   Pan left/right
           S       Tilt down

           Q       Quit

    NOTE: Controller must be armed separately.
    """)

    try:
        tty.setcbreak(fd)

        while rclpy.ok():
            ready, _, _ = select.select(
                [sys.stdin], [], [], 0.1
            )

            if not ready:
                continue

            key = sys.stdin.read(1).lower()

            if key == "w":
                node.send(tilt_delta=-node.step)

            elif key == "s":
                node.send(tilt_delta=node.step)

            elif key == "a":
                node.send(pan_delta=-node.step)

            elif key == "d":
                node.send(pan_delta=node.step)

            elif key == "q":
                break

    except KeyboardInterrupt:
        pass

    finally:
        termios.tcsetattr(
            fd,
            termios.TCSADRAIN,
            old_settings,
        )

        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
