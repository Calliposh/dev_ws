from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    package_share = get_package_share_directory(
        'my_robot_description'
    )

    slam_config = os.path.join(
        package_share,
        'config',
        'slam_toolbox.yaml'
    )

    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_config]
    )

    return LaunchDescription([
        slam_node
    ])