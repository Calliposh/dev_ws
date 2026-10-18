#!/usr/bin/env python3

import time

import rclpy
import serial

from rclpy.node import Node
from std_msgs.msg import Int32, Float32


class NanoBridge(Node):
    """Read encoder and ultrasonic measurements from the Arduino."""

    def __init__(self):
        super().__init__('nano_bridge')

        self.declare_parameter('serial_port', '/dev/ttyUSB1')
        self.declare_parameter('baud_rate', 115200)

        self.serial_port = (
            self.get_parameter('serial_port')
            .get_parameter_value()
            .string_value
        )

        self.baud_rate = (
            self.get_parameter('baud_rate')
            .get_parameter_value()
            .integer_value
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

        # Keep serial reads bounded so the ROS node can recover
        # instead of blocking indefinitely.
        self.timer = self.create_timer(0.01, self.read_serial)

        self.connect_serial()

    def connect_serial(self):
        """Open or reopen the Arduino serial connection."""
        if self.ser is not None:
            try:
                self.ser.close()
            except serial.SerialException:
                pass

            self.ser = None

        try:
            self.ser = serial.Serial(
                self.serial_port,
                self.baud_rate,
                timeout=0.01
            )

            # Allow the serial connection to settle.
            time.sleep(0.2)

            self.ser.reset_input_buffer()

            self.get_logger().info(
                f'Connected to Arduino on {self.serial_port} '
                f'at {self.baud_rate} baud'
            )

        except (serial.SerialException, OSError) as exc:
            self.ser = None
            self.log_error(
                f'Cannot open {self.serial_port}: {exc}'
            )

    def log_error(self, message):
        """Avoid flooding the terminal with repeated errors."""
        now = time.monotonic()

        if now - self.last_error_time >= 5.0:
            self.get_logger().warning(message)
            self.last_error_time = now

    def read_serial(self):
        """Read and publish one five-field CSV packet."""
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

            # Expected format:
            # leftCount,rightCount,leftDistance,
            # frontDistance,rightDistance
            if len(fields) != 5:
                return

            try:
                left_count = int(fields[0].strip())
                right_count = int(fields[1].strip())

                left_distance = float(fields[2].strip())
                front_distance = float(fields[3].strip())
                right_distance = float(fields[4].strip())

            except ValueError:
                # Ignore startup messages or malformed packets.
                return

            values = [
                left_count,
                right_count,
                left_distance,
                front_distance,
                right_distance
            ]

            # Reject non-finite sensor readings.
            import math

            if not all(math.isfinite(value) for value in values):
                return

            left_encoder_msg = Int32()
            left_encoder_msg.data = left_count
            self.left_encoder_pub.publish(left_encoder_msg)

            right_encoder_msg = Int32()
            right_encoder_msg.data = right_count
            self.right_encoder_pub.publish(right_encoder_msg)

            left_msg = Float32()
            left_msg.data = left_distance
            self.left_ultrasonic_pub.publish(left_msg)

            front_msg = Float32()
            front_msg.data = front_distance
            self.front_ultrasonic_pub.publish(front_msg)

            right_msg = Float32()
            right_msg.data = right_distance
            self.right_ultrasonic_pub.publish(right_msg)

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