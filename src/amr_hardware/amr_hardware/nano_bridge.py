#!/usr/bin/env python3

import math
import time

import rclpy
import serial

from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32, Float32


class NanoBridge(Node):

    def __init__(self):
        super().__init__('nano_bridge')

        self.declare_parameter('serial_port', '/dev/ttyUSB1')
        self.declare_parameter('baud_rate', 115200)

        self.serial_port = (
            self.get_parameter('serial_port').value
        )
        self.baud_rate = (
            self.get_parameter('baud_rate').value
        )

        self.ser = None
        self.packet_count = 0
        self.last_error_time = 0.0

        self.left_encoder_pub = self.create_publisher(
            Int32, '/nano/left_encoder', 10
        )
        self.right_encoder_pub = self.create_publisher(
            Int32, '/nano/right_encoder', 10
        )

        self.left_ultrasonic_pub = self.create_publisher(
            Float32, '/nano/ultrasonic_left', 10
        )
        self.front_ultrasonic_pub = self.create_publisher(
            Float32, '/nano/ultrasonic_front', 10
        )
        self.right_ultrasonic_pub = self.create_publisher(
            Float32, '/nano/ultrasonic_right', 10
        )

        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.timer = self.create_timer(0.01, self.read_serial)

        self.connect_serial()

    def connect_serial(self):
        if self.ser is not None:
            try:
                self.ser.close()
            except (serial.SerialException, OSError):
                pass

        self.ser = None

        try:
            self.ser = serial.Serial(
                self.serial_port,
                self.baud_rate,
                timeout=0.01
            )

            time.sleep(0.2)
            self.ser.reset_input_buffer()

            self.get_logger().info(
                f'Connected to Arduino on {self.serial_port} '
                f'at {self.baud_rate} baud'
            )

        except (serial.SerialException, OSError) as exc:
            self.log_error(f'Serial connection failed: {exc}')

    def log_error(self, message):
        now = time.monotonic()

        if now - self.last_error_time >= 5.0:
            self.get_logger().warning(message)
            self.last_error_time = now

    def cmd_vel_callback(self, msg):
        """Forward ROS velocity commands using the documented format."""
        if self.ser is None or not self.ser.is_open:
            return

        linear_velocity = msg.linear.x
        angular_velocity = msg.angular.z

        if not (
            math.isfinite(linear_velocity)
            and math.isfinite(angular_velocity)
        ):
            self.get_logger().warning(
                'Ignoring non-finite velocity command'
            )
            return

        # Previously documented command format: CMD,v,w
        command = (
            f'CMD,{linear_velocity:.4f},'
            f'{angular_velocity:.4f}\n'
        )

        try:
            self.ser.write(command.encode('ascii'))
        except (serial.SerialException, OSError) as exc:
            self.log_error(f'Failed to send motor command: {exc}')
            self.ser = None

    def read_serial(self):
        if self.ser is None or not self.ser.is_open:
            self.connect_serial()
            return

        try:
            line = self.ser.readline().decode(
                'ascii', errors='ignore'
            ).strip()

            if not line:
                return

            fields = line.split(',')

            # Expected Arduino sensor packet:
            # leftCount,rightCount,leftDistance,frontDistance,rightDistance
            if len(fields) != 5:
                return

            try:
                left_count = int(fields[0].strip())
                right_count = int(fields[1].strip())

                left_distance = float(fields[2].strip())
                front_distance = float(fields[3].strip())
                right_distance = float(fields[4].strip())

            except ValueError:
                return

            values = [
                left_distance,
                front_distance,
                right_distance
            ]

            if not all(math.isfinite(v) for v in values):
                return

            self.left_encoder_pub.publish(
                Int32(data=left_count)
            )
            self.right_encoder_pub.publish(
                Int32(data=right_count)
            )

            self.left_ultrasonic_pub.publish(
                Float32(data=left_distance)
            )
            self.front_ultrasonic_pub.publish(
                Float32(data=front_distance)
            )
            self.right_ultrasonic_pub.publish(
                Float32(data=right_distance)
            )

            self.packet_count += 1

            if self.packet_count % 100 == 0:
                self.get_logger().info(
                    f'Packets: {self.packet_count} | '
                    f'L:{left_count} R:{right_count} | '
                    f'US L:{left_distance:.1f} '
                    f'F:{front_distance:.1f} '
                    f'R:{right_distance:.1f}'
                )

        except (serial.SerialException, OSError) as exc:
            self.log_error(f'Serial communication failed: {exc}')
            self.ser = None

    def destroy_node(self):
        if self.ser is not None:
            try:
                self.ser.close()
            except (serial.SerialException, OSError):
                pass

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = NanoBridge()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()