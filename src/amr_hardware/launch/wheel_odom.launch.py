from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    wheel_odom_node = Node(
        package='amr_hardware',
        executable='wheel_odom',
        name='wheel_odometry',
        output='screen',
        parameters=[{
            'odom_topic': '/wheel/odom',
            'publish_tf': False,
        }],
    )

    return LaunchDescription([
        wheel_odom_node
    ])