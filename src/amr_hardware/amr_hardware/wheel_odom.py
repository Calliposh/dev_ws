#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import Int32
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class WheelOdometry(Node):

    def __init__(self):
        super().__init__('wheel_odometry')

        self.declare_parameter('wheel_radius', 0.04)
        self.declare_parameter('wheel_separation', 0.199)
        self.declare_parameter('meters_per_count', 0.00012825)
        self.declare_parameter('left_encoder_sign', -1.0)
        self.declare_parameter('right_encoder_sign', 1.0)
        self.declare_parameter('publish_tf', True)

        self.wheel_radius = float(
            self.get_parameter('wheel_radius').value
        )
        self.wheel_separation = float(
            self.get_parameter('wheel_separation').value
        )
        self.meters_per_count = float(
            self.get_parameter('meters_per_count').value
        )
        self.left_sign = float(
            self.get_parameter('left_encoder_sign').value
        )
        self.right_sign = float(
            self.get_parameter('right_encoder_sign').value
        )
        self.publish_tf = bool(
            self.get_parameter('publish_tf').value
        )

        self.left_count = None
        self.right_count = None

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        self.odom_pub = self.create_publisher(
            Odometry, '/odom', 10
        )

        self.tf_broadcaster = TransformBroadcaster(self)

        self.left_sub = self.create_subscription(
            Int32,
            '/nano/left_encoder',
            self.left_callback,
            10
        )

        self.right_sub = self.create_subscription(
            Int32,
            '/nano/right_encoder',
            self.right_callback,
            10
        )

        self.last_time = self.get_clock().now()
        self.last_report_time = self.last_time

        self.timer = self.create_timer(0.05, self.update_odometry)

        self.get_logger().info(
            'Wheel odometry ready; waiting for encoder readings.'
        )

    def left_callback(self, msg):
        self.left_count = msg.data

    def right_callback(self, msg):
        self.right_count = msg.data

    def update_odometry(self):
        if self.left_count is None or self.right_count is None:
            return

        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9

        if dt <= 0.0:
            return

        current_left = self.left_sign * self.left_count
        current_right = self.right_sign * self.right_count

        if not hasattr(self, 'previous_left'):
            self.previous_left = current_left
            self.previous_right = current_right
            self.last_time = now
            return

        delta_left = (
            current_left - self.previous_left
        ) * self.meters_per_count

        delta_right = (
            current_right - self.previous_right
        ) * self.meters_per_count

        self.previous_left = current_left
        self.previous_right = current_right

        distance = (delta_left + delta_right) / 2.0

        delta_yaw = (
            delta_right - delta_left
        ) / self.wheel_separation

        midpoint_yaw = self.yaw + delta_yaw / 2.0

        self.x += distance * math.cos(midpoint_yaw)
        self.y += distance * math.sin(midpoint_yaw)
        self.yaw += delta_yaw

        linear_velocity = distance / dt
        angular_velocity = delta_yaw / dt

        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_footprint'

        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0

        odom.pose.pose.orientation.x = 0.0
        odom.pose.pose.orientation.y = 0.0
        odom.pose.pose.orientation.z = math.sin(self.yaw / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.yaw / 2.0)

        odom.twist.twist.linear.x = linear_velocity
        odom.twist.twist.angular.z = angular_velocity

        odom.pose.covariance[0] = 0.02
        odom.pose.covariance[7] = 0.02
        odom.pose.covariance[35] = 0.05

        odom.twist.covariance[0] = 0.02
        odom.twist.covariance[35] = 0.05

        self.odom_pub.publish(odom)

        if self.publish_tf:
            transform = TransformStamped()
            transform.header.stamp = now.to_msg()
            transform.header.frame_id = 'odom'
            transform.child_frame_id = 'base_footprint'

            transform.transform.translation.x = self.x
            transform.transform.translation.y = self.y
            transform.transform.translation.z = 0.0

            transform.transform.rotation.x = 0.0
            transform.transform.rotation.y = 0.0
            transform.transform.rotation.z = math.sin(
                self.yaw / 2.0
            )
            transform.transform.rotation.w = math.cos(
                self.yaw / 2.0
            )

            self.tf_broadcaster.sendTransform(transform)

        self.last_time = now

        if (now - self.last_report_time).nanoseconds >= 2_000_000_000:
            self.get_logger().info(
                f'x={self.x:.3f} m, y={self.y:.3f} m, '
                f'yaw={self.yaw:.3f} rad'
            )
            self.last_report_time = now


def main(args=None):
    rclpy.init(args=args)
    node = WheelOdometry()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()